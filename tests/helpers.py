"""Shared test helpers."""
from ionopt.jobs import build_job

MM = 1e-3


def einzel_job(cfg, fidelity="2d", **kw):
    """Valid job for the example_einzel configuration under dev_overrides."""
    conf = cfg.b0_configs.get("example_einzel")
    channels = {"LV1": 100.0, "LV2": 85.0, "HV1": -5000.0, "HV4": -200.0}
    positions = {"lens_gap": 13.482 * MM, "z_mcp": 145 * MM, "mesh_gap": 12.7 * MM}
    channels.update(kw.pop("channels", {}))
    positions.update(kw.pop("positions", {}))
    for k in kw.pop("drop_positions", []):
        positions.pop(k)
    return build_job(cfg, conf, channels, positions, fidelity=fidelity, **kw)
