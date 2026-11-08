import threading

import numpy as np
import pandas as pd
import pytest

from ionopt.backends import make_backend
from ionopt.backends.mock import MockBackend, run_mock
from ionopt.backends.queue import QueueBackend
from ionopt.backends.transports import LocalFSTransport, SSHTransport
from ionopt.schemas import FILES, FINAL_COLUMNS, REQUIRED_RAW
from ionopt.worker.queue_worker import QueueWorker

from helpers import einzel_job


def test_mock_writes_all_raw_files(cfg_tmp):
    b = make_backend(cfg_tmp)
    assert isinstance(b, MockBackend)
    job = einzel_job(cfg_tmp)
    res = b.run(job)
    assert res.status == "success", res.error
    for key in REQUIRED_RAW + ("job", "config_snapshot"):
        assert key in res.files, key
    assert b.status(job.job_id) == "done"
    final = pd.read_csv(res.files["ions_final"])
    launch = pd.read_csv(res.files["ions_launch"])
    assert list(final.columns) == FINAL_COLUMNS
    assert sorted(final["ion_id"]) == sorted(launch["ion_id"])
    assert res.meta.params["v_e3"] == 85 and res.meta.n_ions == len(launch)


def test_mock_energy_conservation(cfg_tmp):
    res = MockBackend(cfg_tmp).run(einzel_job(cfg_tmp))
    f = pd.read_csv(res.files["ions_final"]).merge(pd.read_csv(res.files["ions_launch"]), on="ion_id")
    expect = f["KE0_eV"] + cfg_tmp.spec.launch.charge * (f["V_start_V"] - f["V_end_V"])
    np.testing.assert_allclose(f["KE_eV"], expect, rtol=1e-12)


def test_mock_field_free_case_r_equals_L_tan_theta(cfg_tmp):
    c = cfg_tmp.with_overrides(["backend.mock.f0=1.0", "backend.mock.chroma_min_m_per_eV=0",
                                "backend.mock.chroma_coeff_m_per_eV=0",
                                "spec.detector.mesh_opening_diameter_mm=1000",
                                "spec.detector.mcp_active_diameter_mm=1000"])
    res = MockBackend(c).run(einzel_job(c))
    launch = pd.read_csv(res.files["ions_launch"])[["ion_id", "theta_deg"]]
    f = pd.read_csv(res.files["ions_final"]).merge(launch, on="ion_id")
    r = np.hypot(f["x_m"], f["y_m"])
    np.testing.assert_allclose(r, 0.145 * np.tan(np.radians(f["theta_deg"])), rtol=1e-9, atol=1e-15)


def test_mock_3d_has_phi(cfg_tmp):
    res = MockBackend(cfg_tmp).run(einzel_job(cfg_tmp, fidelity="3d"))
    f = pd.read_csv(res.files["ions_final"])
    assert (f["y_m"].abs() > 0).any()


@pytest.mark.parametrize("inject, status, missing", [
    ("fail", "failed", None),
    ("timeout", "timeout", None),
    ("missing_file", "success", "ions_final"),
])
def test_failure_injection(cfg_tmp, inject, status, missing):
    res = MockBackend(cfg_tmp).run(einzel_job(cfg_tmp, tags={"mock_inject": inject}))
    assert res.status == status
    if missing:
        assert missing not in res.files
    if status != "success":
        assert res.error


def test_invalid_job_fails_cleanly(cfg_tmp):
    res = MockBackend(cfg_tmp).run(einzel_job(cfg_tmp, channels={"LV2": 5000.0}))
    assert res.status == "failed" and "JobValidationError" in res.error


def test_random_failure_rate(cfg_tmp):
    c = cfg_tmp.with_overrides(["backend.mock.failure_rate=0.5"])
    b = MockBackend(c)
    st = [b.run(einzel_job(c)).status for _ in range(30)]
    assert 5 < st.count("failed") < 25


def _start_worker(cfg, stop):
    w = QueueWorker(cfg.path("queue_dir"), run_mock, "mock-worker", root_dir=cfg.root_dir, poll_s=0.02)
    t = threading.Thread(target=w.run, kwargs={"should_stop": stop.is_set}, daemon=True)
    t.start()
    return w, t


def test_queue_backend_with_fake_worker(cfg_tmp):
    tr = LocalFSTransport(cfg_tmp.path("queue_dir"))
    b = QueueBackend(cfg_tmp, tr, poll_interval_s=0.02)
    stop = threading.Event()
    w, t = _start_worker(cfg_tmp, stop)
    try:
        ok = b.run(einzel_job(cfg_tmp), timeout_s=30)
        bad = b.run(einzel_job(cfg_tmp, tags={"mock_inject": "fail"}), timeout_s=30)
    finally:
        stop.set()
        t.join(5)
    assert ok.status == "success", ok.error
    assert all(k in ok.files for k in REQUIRED_RAW)
    assert bad.status == "failed" and "injected" in bad.error
    assert tr.state(ok.job_id) == "done" and tr.state(bad.job_id) == "failed"
    assert set(tr.list_done()) == {ok.job_id, bad.job_id}
    assert not any((cfg_tmp.path("queue_dir") / "running").iterdir())


def test_queue_backend_timeout_without_worker(cfg_tmp):
    b = QueueBackend(cfg_tmp, LocalFSTransport(cfg_tmp.path("queue_dir")), poll_interval_s=0.01)
    res = b.run(einzel_job(cfg_tmp), timeout_s=0.05)
    assert res.status == "timeout"
    assert b.status(res.job_id) == "pending"


def test_worker_never_leaves_job_running(cfg_tmp):
    def crashing_runner(job, cfg, out):
        raise KeyboardInterrupt          # not caught by execute(): simulates the worker being killed

    q = cfg_tmp.path("queue_dir")
    b = QueueBackend(cfg_tmp, LocalFSTransport(q))
    jid = b.submit(einzel_job(cfg_tmp))
    w = QueueWorker(q, crashing_runner, "crashy")
    with pytest.raises(KeyboardInterrupt):
        w.run(stop_when_empty=True)
    assert not any((q / "running").iterdir())
    assert (q / "failed" / jid / FILES["meta"]).is_file()


def test_ssh_transport_is_stub():
    t = SSHTransport("NOPE_HOST", "NOPE_DIR")
    with pytest.raises(NotImplementedError):
        t.list_done()
