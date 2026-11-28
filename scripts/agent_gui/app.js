'use strict';
/* Ion beam agent console front end. Talks to scripts/agent_gui.py (same origin). */

const TOKEN = document.body.dataset.token;
const NS = 'http://www.w3.org/2000/svg';
const STORE = 'agentConsole.v1';
const $ = (s, r = document) => r.querySelector(s);

let D = null;          // as-configured values and geometry from the server
let S = null;          // the settings shown on the page
let runs = [];         // known runs [{run_id, alive, mtime}]
let mon = null;        // monitor data of the watched run
let watched = null;
let tab = 'setup';

/* ------------------------------------------------------------------ helpers */

function h(tag, props = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'text') el.textContent = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const k of kids.flat()) if (k != null) el.append(k);
  return el;
}
const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
const fmt = v => String(Math.round(v * 1000) / 1000);
const cap1 = s => s.charAt(0).toUpperCase() + s.slice(1);

/* Custom drop-down. The native select stays hidden and keeps the value and the change event,
   so the rest of the code is unchanged. The list is drawn by the page, so it is always readable. */
const selValue = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value');
function enhanceSelect(sel) {
  if (sel.dataset.dd) return;
  sel.dataset.dd = '1';
  const small = sel.classList.contains('small');
  const wrap = h('div', { class: 'dd' + (small ? ' small' : '') });
  const btn = h('button', { type: 'button', class: 'select dd-btn' + (small ? ' small' : ''), 'aria-haspopup': 'listbox', 'aria-expanded': 'false' });
  if (sel.getAttribute('aria-label')) btn.setAttribute('aria-label', sel.getAttribute('aria-label'));
  const list = h('ul', { class: 'dd-list hidden', role: 'listbox', tabindex: '-1' });
  if (sel.parentNode) sel.replaceWith(wrap);
  wrap.append(sel, btn, list);
  sel.classList.add('dd-native');
  sel.tabIndex = -1;

  const label = () => {
    const o = sel.options[sel.selectedIndex];
    btn.textContent = o ? o.textContent : '';
  };
  Object.defineProperty(sel, 'value', {
    get() { return selValue.get.call(this); },
    set(v) { selValue.set.call(this, v); label(); },
  });
  new MutationObserver(label).observe(sel, { childList: true });
  label();

  let active = -1;
  const items = () => [...list.children];
  const mark = i => {
    active = i;
    items().forEach((li, k) => li.classList.toggle('active', k === i));
    const li = items()[i];
    if (li) li.scrollIntoView({ block: 'nearest' });
  };
  const close = () => { list.classList.add('hidden'); btn.setAttribute('aria-expanded', 'false'); document.removeEventListener('mousedown', away, true); };
  const away = e => { if (!wrap.contains(e.target)) close(); };
  const pick = i => {
    const o = sel.options[i];
    if (!o || o.disabled) return;
    close();
    if (sel.selectedIndex !== i) {
      selValue.set.call(sel, o.value);
      label();
      sel.dispatchEvent(new Event('change', { bubbles: true }));
    }
    btn.focus();
  };
  const open = () => {
    list.replaceChildren(...[...sel.options].map((o, i) => h('li', {
      role: 'option', class: 'dd-item' + (o.disabled ? ' off' : '') + (i === sel.selectedIndex ? ' on' : ''),
      'aria-selected': i === sel.selectedIndex ? 'true' : 'false', text: o.textContent,
      onmousedown: e => { e.preventDefault(); pick(i); },
    })));
    list.classList.remove('hidden');
    btn.setAttribute('aria-expanded', 'true');
    mark(sel.selectedIndex);
    document.addEventListener('mousedown', away, true);
  };
  btn.addEventListener('click', () => (list.classList.contains('hidden') ? open() : close()));
  btn.addEventListener('keydown', e => {
    const isOpen = !list.classList.contains('hidden');
    const step = d => {
      let i = active;
      for (let n = 0; n < sel.options.length; n++) { i = (i + d + sel.options.length) % sel.options.length; if (!sel.options[i].disabled) break; }
      mark(i);
    };
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); if (!isOpen) open(); step(e.key === 'ArrowDown' ? 1 : -1); }
    else if (e.key === 'Enter' || e.key === ' ') { if (isOpen) { e.preventDefault(); pick(active); } }
    else if (e.key === 'Escape' && isOpen) { e.preventDefault(); close(); }
    else if (e.key === 'Tab' && isOpen) close();
  });
  return wrap;
}

async function api(path, body) {
  const opt = body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Token': TOKEN }, body: JSON.stringify(body),
  };
  const r = await fetch(path, opt);
  const j = await r.json().catch(() => ({ error: 'The console server sent an unreadable reply' }));
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

let toastTimer = null;
function toast(msg, isErr = false) {
  const t = $('#toast');
  t.textContent = msg;
  t.classList.toggle('err', isErr);
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, isErr ? 7000 : 3500);
}

function confirmModal(title, rows, note, okText = 'Confirm', danger = false) {
  return new Promise(resolve => {
    $('#modal-title').textContent = title;
    const dl = h('dl');
    for (const [k, v] of rows) dl.append(h('dt', { text: k }), h('dd', { text: v }));
    const body = $('#modal-body');
    body.replaceChildren(dl);
    if (note) body.append(h('p', { text: note }));
    const ok = $('#modal-ok');
    ok.textContent = okText;
    ok.className = 'btn ' + (danger ? 'danger' : 'primary');
    const m = $('#modal');
    m.classList.remove('hidden');
    ok.focus();
    const done = v => {
      m.classList.add('hidden');
      ok.onclick = null; $('#modal-cancel').onclick = null; document.removeEventListener('keydown', key);
      resolve(v);
    };
    const key = e => { if (e.key === 'Escape') done(false); };
    document.addEventListener('keydown', key);
    ok.onclick = () => done(true);
    $('#modal-cancel').onclick = () => done(false);
  });
}

/* ------------------------------------------------------------------ settings */

function initSettings() {
  S = {
    chamber: '1', run_id: D.suggested_run_id, goal: '', page: 'voltages', test_mode: false, remove_mesh: false,
    lv: [...D.lv_range], mcp: [...D.mcp_front], mesh_v: [...D.mesh_v],
    ext_min: D.ext_min, ext_max: D.ext_max, ext_fixed: D.ext_fixed, pos: {},
    budget: D.budget, rounds: D.rounds, round_max: D.round_max, no_improve: D.no_improve, improve_tol: D.improve_tol,
    eta_min: D.eta_min, sigma_mcp: D.sigma_mcp, hwhm: D.hwhm, e0: D.e0, mass: D.mass, charge: D.charge, hints: {},
  };
  for (const [k, c] of Object.entries(D.chambers)) {
    if (c.usable) S.pos[k] = { lens_gap: [...c.lens_gap], mesh_gap: [...c.mesh_gap], z_mcp: [...c.z_mcp] };
  }
  try {
    const saved = JSON.parse(localStorage.getItem(STORE) || 'null');
    if (!saved || saved.v !== 1) return;
    const keep = ['goal', 'page', 'test_mode', 'remove_mesh', 'ext_min', 'ext_max', 'ext_fixed', 'budget', 'rounds',
      'round_max', 'no_improve', 'improve_tol', 'eta_min', 'sigma_mcp', 'hwhm', 'e0', 'mass', 'charge'];
    for (const k of keep) if (k in saved.s && (typeof saved.s[k] === typeof S[k] || saved.s[k] === null)) S[k] = saved.s[k];
    if (D.chambers[saved.s.chamber] && D.chambers[saved.s.chamber].usable) S.chamber = saved.s.chamber;
    const rng = (key, lo, hi) => {
      const v = saved.s[key];
      if (Array.isArray(v) && v.length === 2 && v.every(Number.isFinite)) {
        const a = clamp(v[0], lo, hi), b = clamp(v[1], lo, hi);
        return a <= b ? [a, b] : null;
      }
      return null;
    };
    S.lv = rng('lv', ...D.lv_range) || S.lv;
    S.mcp = rng('mcp', ...D.mcp_front) || S.mcp;
    S.mesh_v = rng('mesh_v', ...D.mesh_v) || S.mesh_v;
    for (const k of Object.keys(S.pos)) {
      const sp = saved.s.pos && saved.s.pos[k];
      if (!sp) continue;
      for (const key of ['lens_gap', 'mesh_gap', 'z_mcp']) {
        const v = sp[key], base = D.chambers[k][key];
        if (Array.isArray(v) && v.length === 2 && v.every(Number.isFinite)) {
          const a = clamp(v[0], base[0], base[1]), b = clamp(v[1], base[0], base[1]);
          if (a <= b) S.pos[k][key] = [a, b];
        }
      }
    }
    if (saved.s.hints && typeof saved.s.hints === 'object') S.hints = saved.s.hints;
  } catch (e) { /* storage unavailable or damaged: start from the defaults */ }
}

let saveTimer = null;
function save() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    try { localStorage.setItem(STORE, JSON.stringify({ v: 1, s: S })); } catch (e) { /* ignore */ }
  }, 300);
}

function payload() {
  const p = S.pos[S.chamber];
  const hints = Object.entries(S.hints)
    .filter(([, v]) => v && ((v.state && v.state !== 'auto') || v.lo !== '' && v.lo != null || v.hi !== '' && v.hi != null))
    .map(([el, v]) => ({ el, state: v.state || 'auto', lo: v.lo === '' ? null : v.lo, hi: v.hi === '' ? null : v.hi }));
  return {
    chamber: S.chamber, run_id: S.run_id.trim(), goal: S.goal, test_mode: S.test_mode, remove_mesh: S.remove_mesh,
    lv: S.lv, mcp: S.mcp, mesh_v: S.mesh_v, ext_min: S.ext_min, ext_max: S.ext_max, ext_fixed: S.ext_fixed,
    lens_gap: p.lens_gap, mesh_gap: p.mesh_gap, z_mcp: p.z_mcp,
    budget: S.budget, rounds: S.rounds, round_max: S.round_max, no_improve: S.no_improve, improve_tol: S.improve_tol,
    eta_min: S.eta_min, sigma_mcp: S.sigma_mcp, hwhm: S.hwhm, e0: S.e0, mass: S.mass, charge: S.charge, hints,
  };
}

/* ------------------------------------------------------------------ diagram */

const VB = { W: 1200, H: 366, cy: 180, x0: 84, x1: 1150, sy: 2.8 };
let rayEls = [];
let ions = [];
let animT = 0;
let beamSpeed = 0.35;

function smoothPath(pts) {
  let d = `M${pts[0][0].toFixed(1)},${pts[0][1].toFixed(1)}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[i - 1] || pts[i], p1 = pts[i], p2 = pts[i + 1], p3 = pts[i + 2] || p2;
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    d += ` C${c1[0].toFixed(1)},${c1[1].toFixed(1)} ${c2[0].toFixed(1)},${c2[1].toFixed(1)} ${p2[0].toFixed(1)},${p2[1].toFixed(1)}`;
  }
  return d;
}

function drawDiagram() {
  const st = $('#stage');
  VB.W = Math.max(900, Math.round(st.clientWidth * VB.H / Math.max(1, st.clientHeight)));
  VB.x1 = VB.W - 56;
  $('#diagram').setAttribute('viewBox', `0 0 ${VB.W} ${VB.H}`);
  const ch = S.chamber, c = D.chambers[ch], pos = S.pos[ch];
  const j3 = ch === '3';
  const zmax = j3 ? 450 : 205;
  const sx = (VB.x1 - 28) / (zmax + 26), cy = VB.cy, sy = VB.sy;
  VB.x0 = 28 + 26 * sx;                 // the chamber wall (z = -26 mm) starts 28 px from the left edge
  const X = z => VB.x0 + z * sx, Y = r => cy - r * sy;
  const lg = clamp(13.48, pos.lens_gap[0], pos.lens_gap[1]);
  const zm = clamp(j3 ? c.z_mcp[0] : 160, pos.z_mcp[0], pos.z_mcp[1]);
  const flange = 193.7;
  const meshOn = !S.remove_mesh;
  const zMesh = zm - pos.mesh_gap[0];
  const lastPlate = D.stack[D.stack.length - 1];
  let stackEnd = lg + lastPlate.front + lastPlate.plate;
  if (j3) { const d = D.deflectors[D.deflectors.length - 1]; stackEnd = lg + d.front + d.length; }

  let g = `<defs><filter id="blur" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3.5"/></filter></defs>`;
  g += `<line class="axis" x1="${X(-30)}" y1="${cy}" x2="${X(zmax - 8)}" y2="${cy}"/>`;

  // chamber outline
  const tx0 = X(-26), tx1 = X(flange), th = 126;   // clears the E labels, which sit about 112 px from the axis
  g += `<rect class="chamber" x="${tx0}" y="${cy - th}" width="${tx1 - tx0}" height="${2 * th}" rx="16"/>`;
  if (j3) {
    const sxc = X(c.z_mcp[0]), rs = 115, neck = 34;
    const lx = sxc - Math.sqrt(rs * rs - neck * neck);
    g += `<circle class="chamber" cx="${sxc}" cy="${cy}" r="${rs}"/>`;
    g += `<line class="chamber" x1="${tx1}" y1="${cy - neck}" x2="${lx}" y2="${cy - neck}"/>`;
    g += `<line class="chamber" x1="${tx1}" y1="${cy + neck}" x2="${lx}" y2="${cy + neck}"/>`;
  }

  // tie rods (cfg 1: the MCP rides on them)
  if (c.mcp_on_rods) {
    for (const s of [-1, 1]) {
      g += `<line x1="${X(lg)}" y1="${Y(s * 27)}" x2="${X(lg + 140.7)}" y2="${Y(s * 27)}" stroke="#2a3846" stroke-width="2"/>`;
    }
  }

  // tip
  const tx = X(0);
  g += `<path class="tipbody" d="M${tx},${cy} L${tx - 16},${cy - 7} L${tx - 46},${cy - 7} L${tx - 46},${cy + 7} L${tx - 16},${cy + 7} Z"/>`;
  g += `<text class="lab" x="${tx - 30}" y="${cy - 18}" text-anchor="middle">Tip</text>`;

  // beam (drawn before the plates so the plates sit on top)
  const ctrl = [[0, 0], [lg * 0.5, 1.7], [lg, 2.7], [(lg + stackEnd) / 2, 3.5], [stackEnd, 3.1]];
  const L = zm - stackEnd;
  if (L > 8) ctrl.push([stackEnd + L * 0.3, 5.2], [stackEnd + L * 0.65, 9.5]);
  ctrl.push([zm - 1, L > 8 ? 16 : 5]);
  let beam = '<g class="beam">';
  const fs = [-1, -0.66, -0.33, 0, 0.33, 0.66, 1];
  for (const f of fs) {
    const d = smoothPath(ctrl.map(([z, R]) => [X(z), cy - f * R * sy]));
    beam += `<path class="ray-glow" d="${d}"/><path class="ray-base" d="${d}"/><path class="ray-core" d="${d}"/>`;
  }
  beam += '</g><g id="ions"></g>';
  g += beam;

  // lens plates
  const nLab = j3 ? 14 : 15;
  D.stack.forEach((p, i) => {
    const el = 'E' + (i + 1);
    const hint = S.hints[el] || {};
    const x = X(lg + p.front), w = Math.max(p.plate * sx, 6);
    const cls = 'plate' + (hint.state === 'keep' ? ' keep' : '') + (hint.state === 'drop' ? ' drop' : '');
    g += `<g class="${cls}" data-el="${el}">` +
      `<rect x="${x}" y="${Y(p.r_out)}" width="${w}" height="${(p.r_out - p.r_in) * sy}" rx="2"/>` +
      `<rect x="${x}" y="${Y(-p.r_in)}" width="${w}" height="${(p.r_out - p.r_in) * sy}" rx="2"/>` +
      `<rect x="${x - 3}" y="${Y(p.r_out)}" width="${w + 6}" height="${2 * p.r_out * sy}" style="fill:transparent;stroke:none"/>` +
      `<text class="lab" style="font-size:${nLab}px" x="${x + w / 2}" y="${Y(p.r_out) - 9}" text-anchor="middle">${el}</text></g>`;
  });

  // deflectors (cfg 3 only)
  if (j3) {
    for (const d of D.deflectors) {
      const x = X(lg + d.front), w = d.length * sx;
      g += `<g class="defl"><rect x="${x}" y="${Y(d.r_out)}" width="${w}" height="${(d.r_out - d.r_in) * sy}"/>` +
        `<rect x="${x}" y="${Y(-d.r_in)}" width="${w}" height="${(d.r_out - d.r_in) * sy}"/>` +
        `<text class="lab-muted" x="${x + w / 2}" y="${Y(d.r_out) - 9}" text-anchor="middle">${d.name.toUpperCase()}</text></g>`;
    }
  }

  // screen mesh
  g += `<g class="mesh${meshOn ? '' : ' off'}" data-mesh="1" style="cursor:pointer">` +
    `<line class="mesh-line" x1="${X(zMesh)}" y1="${Y(19)}" x2="${X(zMesh)}" y2="${Y(-19)}"/>` +
    `<rect x="${X(zMesh) - 8}" y="${Y(19)}" width="16" height="${38 * sy}" style="fill:transparent;stroke:none"/>` +
    `<text class="lab-muted" x="${X(zMesh)}" y="${Y(-19) + 19}" text-anchor="middle">${meshOn ? 'Mesh' : 'No mesh'}</text></g>`;

  // MCP
  const mr = D.mcp_diameter / 2;
  g += `<g class="mcp"><rect x="${X(zm)}" y="${Y(mr)}" width="9" height="${2 * mr * sy}" rx="2"/>` +
    `<text class="lab" x="${X(zm) + 4}" y="${Y(mr) - 9}" text-anchor="middle">MCP</text></g>`;

  // position ranges (only where a range exists)
  const bracket = (a, b, y, label) => {
    if (b - a < 0.5) return '';
    const x1 = X(a), x2 = X(b);
    const right = x2 + 12 + label.length * 7.5 < VB.W - 8;
    return `<path class="bracket" d="M${x1},${y - 5} V${y + 5} M${x1},${y} H${x2} M${x2},${y - 5} V${y + 5}"/>` +
      `<text class="lab-green" x="${right ? x2 + 10 : x1 - 10}" y="${y + 5}" text-anchor="${right ? 'start' : 'end'}">${label}</text>`;
  };
  g += bracket(pos.lens_gap[0], pos.lens_gap[1], cy + th + 22, 'Stack position range');
  if (c.mcp_on_rods) g += bracket(pos.z_mcp[0], pos.z_mcp[1], cy + th + 44, 'MCP position range');

  $('#diagram').innerHTML = g;
  rayEls = [...document.querySelectorAll('#diagram .ray-base')];
  buildIons();

  $('#cap-title').textContent = cap1(c.name);
  $('#cap-sub').textContent = j3
    ? 'Tube joined to the sphere. The MCP is fixed at the sphere centre.'
    : 'The MCP rides on the tie rods behind the lens stack.';
  wirePlates();
}

function buildIons() {
  const layer = $('#ions');
  ions = [];
  if (!layer || !rayEls.length) return;
  for (let i = 0; i < 44; i++) {
    const el = rayEls[i % rayEls.length];
    const c = document.createElementNS(NS, 'circle');
    c.setAttribute('class', 'ion');
    c.setAttribute('r', '2.4');
    c.setAttribute('opacity', '0');
    layer.append(c);
    ions.push({ c, el, len: el.getTotalLength(), phase: Math.random(), speed: 0.06 + Math.random() * 0.07 });
  }
}

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
let lastFrame = performance.now();
function frame(now) {
  const dt = Math.min(0.1, (now - lastFrame) / 1000);
  lastFrame = now;
  if (!document.hidden && !reduceMotion) {
    animT += dt * beamSpeed;
    for (const p of ions) {
      const u = (p.phase + animT * p.speed * 6) % 1;
      const pt = p.el.getPointAtLength(p.len * Math.pow(u, 1.35));
      p.c.setAttribute('cx', pt.x.toFixed(1));
      p.c.setAttribute('cy', pt.y.toFixed(1));
      p.c.setAttribute('opacity', (Math.min(1, u * 10, (1 - u) * 8) * (beamSpeed > 0.5 ? 0.95 : 0.55)).toFixed(2));
    }
  }
  requestAnimationFrame(frame);
}

function wirePlates() {
  const tip = $('#tip'), stage = $('#stage');
  const show = (e, text) => {
    const r = stage.getBoundingClientRect();
    tip.textContent = text;
    tip.hidden = false;
    tip.style.left = Math.min(r.width - 330, e.clientX - r.left + 14) + 'px';
    tip.style.top = (e.clientY - r.top + 16) + 'px';
  };
  document.querySelectorAll('#diagram .plate').forEach(el => {
    const name = el.dataset.el;
    const kind = Number(name.slice(1)) <= 4 ? 'lens plate' : 'accelerator plate';
    el.addEventListener('mousemove', e => show(e, `${name}, ${kind}. Click to set hints for it.`));
    el.addEventListener('mouseleave', () => { tip.hidden = true; });
    el.addEventListener('click', () => openHint(name));
  });
  const mesh = document.querySelector('#diagram .mesh');
  if (mesh) {
    mesh.addEventListener('mousemove', e => show(e, S.remove_mesh ? 'Screen mesh removed. Click to allow it again.' : 'Screen mesh. Click to require its removal.'));
    mesh.addEventListener('mouseleave', () => { tip.hidden = true; });
    mesh.addEventListener('click', () => { S.remove_mesh = !S.remove_mesh; save(); drawDiagram(); renderPage(); });
  }
}

/* ------------------------------------------------------------------ parameter rows */

function rowShell(o) {
  return h('div', { class: 'prow' + (o.off ? ' off' : '') });
}

function dualRow(o) {
  const row = rowShell(o);
  const lo = h('input', { class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': o.label + ' minimum' });
  const hi = h('input', { class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': o.label + ' maximum' });
  const rl = h('input', { type: 'range', min: o.min, max: o.max, step: o.step, 'aria-label': o.label + ' minimum slider' });
  const rh = h('input', { type: 'range', min: o.min, max: o.max, step: o.step, 'aria-label': o.label + ' maximum slider' });
  const fill = h('div', { class: 'fill' });
  const changed = () => { save(); if (o.onChange) o.onChange(); };
  const sync = () => {
    const [a, b] = o.get(), span = o.max - o.min;
    rl.value = a; rh.value = b;
    fill.style.left = ((a - o.min) / span * 100) + '%';
    fill.style.right = (100 - (b - o.min) / span * 100) + '%';
    lo.value = fmt(a);
    hi.value = (o.openHigh != null && b >= o.openHigh) ? 'none' : fmt(b);
    rl.style.zIndex = a > (o.min + o.max) / 2 ? 3 : 1;
    rh.style.zIndex = 2;
  };
  const commit = (a, b) => {
    a = clamp(a, o.min, o.max); b = clamp(b, o.min, o.max);
    if (a > b) [a, b] = [b, a];
    o.set([a, b]); sync(); changed();
  };
  rl.addEventListener('input', () => commit(Math.min(+rl.value, +rh.value), +rh.value));
  rh.addEventListener('input', () => commit(+rl.value, Math.max(+rh.value, +rl.value)));
  lo.addEventListener('change', () => { const v = parseFloat(lo.value); if (Number.isFinite(v)) commit(v, o.get()[1]); else sync(); });
  hi.addEventListener('change', () => {
    const t = hi.value.trim().toLowerCase();
    if (o.openHigh != null && /^(none|off|no limit)?$/.test(t)) return commit(o.get()[0], o.max);
    const v = parseFloat(t);
    if (Number.isFinite(v)) commit(o.get()[0], v); else sync();
  });
  row.append(
    h('div', { class: 'prow-head' },
      h('div', { class: 'prow-label', text: o.label }),
      h('div', { class: 'prow-inputs' }, lo, 'to', hi, o.unit || '')),
    ...(o.sub ? [h('div', { class: 'prow-sub', text: o.sub })] : []),
    h('div', { class: 'dual' }, h('div', { class: 'track' }), fill, rl, rh));
  sync();
  return row;
}

function singleRow(o) {
  const row = rowShell(o);
  const box = h('input', { class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': o.label });
  const r = h('input', { type: 'range', min: o.min, max: o.max, step: o.step, 'aria-label': o.label + ' slider' });
  const fill = h('div', { class: 'fill' });
  const sync = () => {
    const v = o.get();
    r.value = v; box.value = fmt(v);
    fill.style.left = '0%'; fill.style.right = (100 - (clamp(v, o.min, o.max) - o.min) / (o.max - o.min) * 100) + '%';
  };
  const commit = v => { o.set(o.int ? Math.round(v) : v); sync(); save(); if (o.onChange) o.onChange(); };
  r.addEventListener('input', () => commit(+r.value));
  box.addEventListener('change', () => { const v = parseFloat(box.value); if (Number.isFinite(v)) commit(clamp(v, o.softMin ?? o.min, o.softMax ?? o.max)); else sync(); });
  row.append(
    h('div', { class: 'prow-head' },
      h('div', { class: 'prow-label', text: o.label }),
      h('div', { class: 'prow-inputs' }, box, o.unit || '')),
    ...(o.sub ? [h('div', { class: 'prow-sub', text: o.sub })] : []),
    h('div', { class: 'single' }, h('div', { class: 'track' }), fill, r));
  sync();
  return row;
}

function switchRow(o) {
  const cb = h('input', { type: 'checkbox' });
  cb.checked = !!o.get();
  cb.addEventListener('change', () => { o.set(cb.checked); save(); if (o.onChange) o.onChange(); });
  return h('div', { class: 'prow' },
    h('label', { class: 'switch' }, cb, h('span', { class: 'knob' }), h('span', {}, o.label)),
    o.sub ? h('p', { class: 'note', text: o.sub }) : null);
}

/* ------------------------------------------------------------------ pages */

const PAGES = [
  { id: 'voltages', title: 'Voltage ranges' },
  { id: 'positions', title: 'Positions' },
  { id: 'limits', title: 'Run limits' },
  { id: 'beam', title: 'Beam and detector' },
  { id: 'hints', title: 'Lens hints' },
];

function pageVoltages() {
  const fixedOn = S.ext_fixed !== null && S.ext_fixed !== undefined;
  const fixedBox = h('input', { class: 'num', type: 'text', inputmode: 'decimal', 'aria-label': 'Fixed extraction voltage' });
  fixedBox.value = fixedOn ? fmt(S.ext_fixed) : '';
  fixedBox.disabled = !fixedOn;
  fixedBox.addEventListener('change', () => {
    const v = parseFloat(fixedBox.value);
    if (Number.isFinite(v)) { S.ext_fixed = clamp(v, 0, 2000); save(); }
    fixedBox.value = fmt(S.ext_fixed);
  });
  const cb = h('input', { type: 'checkbox' });
  cb.checked = fixedOn;
  cb.addEventListener('change', () => {
    S.ext_fixed = cb.checked ? 120 : null;
    save(); renderPage();
  });
  return h('div', { class: 'grid2' },
    dualRow({ label: 'Lens channels', sub: 'LV1 to LV4, one shared range', unit: 'V', min: D.lv_range[0], max: D.lv_range[1], step: 5,
      get: () => S.lv, set: v => { S.lv = v; } }),
    dualRow({ label: 'MCP front', sub: 'detector entrance voltage', unit: 'V', min: D.mcp_front[0], max: D.mcp_front[1], step: 50,
      get: () => S.mcp, set: v => { S.mcp = v; } }),
    dualRow({ label: 'Screen mesh', sub: S.remove_mesh ? 'not used, the mesh is removed' : 'voltage on the mesh', unit: 'V',
      min: D.mesh_v[0], max: D.mesh_v[1], step: 50, off: S.remove_mesh, get: () => S.mesh_v, set: v => { S.mesh_v = v; } }),
    dualRow({ label: 'Extraction, tip to E1', sub: 'the upper end "none" means no limit', unit: 'V', min: 0, max: 600, step: 5, openHigh: 600,
      off: fixedOn,
      get: () => [S.ext_min, S.ext_max == null ? 600 : S.ext_max],
      set: ([a, b]) => { S.ext_min = a; S.ext_max = b >= 600 ? null : b; } }),
    h('div', { class: 'prow' },
      h('div', { class: 'prow-head' },
        h('label', { class: 'switch' }, cb, h('span', { class: 'knob' }), h('span', {}, 'Fix the extraction voltage')),
        h('div', { class: 'prow-inputs' }, fixedBox, 'V')),
      h('p', { class: 'note', text: 'Holds the tip to E1 difference constant, as in run 1.' })));
}

function pagePositions() {
  const ch = S.chamber, c = D.chambers[ch], pos = S.pos[ch];
  const mcpFixed = c.z_mcp[0] === c.z_mcp[1];
  return h('div', { class: 'grid2' },
    dualRow({ label: 'Stack position', sub: 'tip to the E1 front face', unit: 'mm', min: c.lens_gap[0], max: c.lens_gap[1], step: 0.5,
      get: () => pos.lens_gap, set: v => { pos.lens_gap = v; }, onChange: drawDiagram }),
    mcpFixed
      ? h('div', { class: 'prow' }, h('div', { class: 'prow-label', text: 'MCP position' }), h('div', { class: 'prow-sub', text: `Fixed at ${fmt(c.z_mcp[0])} mm (sphere centre)` }))
      : dualRow({ label: 'MCP position', sub: 'front face, from the tip', unit: 'mm', min: c.z_mcp[0], max: c.z_mcp[1], step: 0.5,
        get: () => pos.z_mcp, set: v => { pos.z_mcp = v; }, onChange: drawDiagram }),
    dualRow({ label: 'Mesh gap', sub: 'mesh distance in front of the MCP', unit: 'mm', min: c.mesh_gap[0], max: c.mesh_gap[1], step: 0.5,
      off: S.remove_mesh, get: () => pos.mesh_gap, set: v => { pos.mesh_gap = v; }, onChange: drawDiagram }),
    switchRow({ label: 'Remove the screen mesh', sub: 'Every layout must run without it. You can also click the mesh in the diagram.',
      get: () => S.remove_mesh, set: v => { S.remove_mesh = v; }, onChange: () => { drawDiagram(); renderPage(); } }));
}

function pageLimits() {
  return h('div', { class: 'grid2' },
    singleRow({ label: 'Solve budget', sub: 'total simulations for the run', min: 50, max: 1500, step: 10, int: true, softMin: 10, softMax: 5000,
      get: () => S.budget, set: v => { S.budget = v; } }),
    singleRow({ label: 'Round cap', sub: 'most planner rounds', min: 2, max: 100, step: 1, int: true, softMin: 1, softMax: 200,
      get: () => S.rounds, set: v => { S.rounds = v; } }),
    singleRow({ label: 'Largest study per round', sub: 'simulations in one optimizer study', min: 10, max: 200, step: 5, int: true, softMin: 5, softMax: 500,
      get: () => S.round_max, set: v => { S.round_max = v; } }),
    singleRow({ label: 'Rounds without gain before stopping', min: 1, max: 30, step: 1, int: true, softMin: 1, softMax: 100,
      get: () => S.no_improve, set: v => { S.no_improve = v; } }),
    singleRow({ label: 'Smallest gain that counts', sub: 'in degrees of resolution', unit: 'deg', min: 0, max: 0.05, step: 0.001, softMin: 0, softMax: 1,
      get: () => S.improve_tol, set: v => { S.improve_tol = v; } }),
    switchRow({ label: 'Test mode (mock backend)', sub: 'Toy optics, no COMSOL. The planner still calls Claude.',
      get: () => S.test_mode, set: v => { S.test_mode = v; } }));
}

function pageBeam() {
  const species = [['Na+ (22.99 Da)', 22.99, 1], ['Protonated arginine (175.1 Da)', 175.1, 1], ['Cl- (35.45 Da)', 35.45, -1]];
  const sel = h('select', { class: 'select small', 'aria-label': 'Ion species', style: 'min-width:0;width:100%' },
    h('option', { value: '', text: 'Choose a species to fill mass and charge' }),
    ...species.map(([n], i) => h('option', { value: i, text: n })));
  const massRow = singleRow({ label: 'Ion mass', unit: 'Da', min: 1, max: 250, step: 0.1, softMin: 0.5, softMax: 2000,
    get: () => S.mass, set: v => { S.mass = v; } });
  sel.addEventListener('change', () => {
    if (sel.value === '') return;
    const [, m, q] = species[+sel.value];
    S.mass = m; S.charge = q; save(); renderPage();
  });
  return h('div', { class: 'grid2' },
    singleRow({ label: 'Minimum collection', sub: 'share of ions that must reach the MCP', min: 0.1, max: 0.95, step: 0.01, softMin: 0.01, softMax: 1,
      get: () => S.eta_min, set: v => { S.eta_min = v; } }),
    singleRow({ label: 'MCP resolution (1 sigma)', unit: 'um', min: 20, max: 150, step: 1, softMin: 1, softMax: 1000,
      get: () => S.sigma_mcp, set: v => { S.sigma_mcp = v; } }),
    singleRow({ label: 'Emission half width', sub: 'HWHM of the angular spread', unit: 'deg', min: 5, max: 40, step: 0.5, softMin: 0.5, softMax: 60,
      get: () => S.hwhm, set: v => { S.hwhm = v; } }),
    singleRow({ label: 'Launch energy', unit: 'eV', min: 0.5, max: 10, step: 0.1, softMin: 0.01, softMax: 100,
      get: () => S.e0, set: v => { S.e0 = v; } }),
    h('div', { class: 'prow' }, sel,
      h('p', { class: 'note', text: `Current charge number: ${S.charge > 0 ? '+' : ''}${S.charge}` })),
    massRow);
}

function pageHints() {
  const els = ['tip', ...Array.from({ length: 9 }, (_, i) => 'E' + (i + 1))];
  const mk = el => {
    const v = S.hints[el] || (S.hints[el] = { state: 'auto', lo: '', hi: '' });
    const fixed = el === 'tip' || el === 'E1';
    const sel = h('select', { class: 'select', 'aria-label': el + ' use' },
      h('option', { value: 'auto', text: 'Auto' }), h('option', { value: 'keep', text: 'Keep' }), h('option', { value: 'drop', text: 'Leave out' }));
    sel.value = v.state || 'auto';
    sel.addEventListener('change', () => { v.state = sel.value; save(); drawDiagram(); });
    const num = (key, label) => {
      const i = h('input', { class: 'num', type: 'text', inputmode: 'decimal', placeholder: 'any', 'aria-label': `${el} ${label} voltage` });
      i.value = v[key] === '' || v[key] == null ? '' : fmt(v[key]);
      i.addEventListener('change', () => {
        const t = parseFloat(i.value);
        v[key] = Number.isFinite(t) ? clamp(t, -10000, 10000) : '';
        i.value = v[key] === '' ? '' : fmt(v[key]);
        save();
      });
      return i;
    };
    return h('div', { class: 'hint-row', 'data-el': el },
      h('span', { class: 'name', text: el === 'tip' ? 'Tip' : el }),
      fixed ? h('span', { class: 'muted', text: 'always in' }) : sel,
      num('lo', 'minimum'), num('hi', 'maximum'));
  };
  const head = () => h('div', { class: 'hint-head' }, h('span'), h('span', { text: 'Use' }), h('span', { text: 'Min V' }), h('span', { text: 'Max V' }));
  return h('div', {},
    h('p', { class: 'note', text: 'Optional soft guidance, added to the goal text. Auto lets the planner decide. Keep or Leave out asks it to use or skip a plate. The planner follows a hint unless the numbers argue against it. Voltage boxes apply only if the plate is used.' }),
    h('div', { class: 'grid2', style: 'margin-top:12px' },
      h('div', {}, head(), ...els.slice(0, 5).map(mk).map(r => h('div', { style: 'margin-bottom:8px' }, r))),
      h('div', {}, head(), ...els.slice(5).map(mk).map(r => h('div', { style: 'margin-bottom:8px' }, r)))));
}

function renderPage() {
  const fn = { voltages: pageVoltages, positions: pagePositions, limits: pageLimits, beam: pageBeam, hints: pageHints }[S.page] || pageVoltages;
  $('#page').value = S.page;
  $('#page-body').replaceChildren(fn());
  $('#page-body').querySelectorAll('select').forEach(enhanceSelect);
}

function openHint(el) {
  S.page = 'hints'; save();
  setTab('setup');
  renderPage();
  const row = document.querySelector(`.hint-row[data-el="${el}"]`);
  if (row) { row.scrollIntoView({ block: 'nearest' }); row.classList.add('flash'); setTimeout(() => row.classList.remove('flash'), 1500); }
}

/* ------------------------------------------------------------------ tabs, footer */

function setTab(t) {
  tab = t;
  $('#view-setup').classList.toggle('hidden', t !== 'setup');
  $('#view-monitor').classList.toggle('hidden', t !== 'monitor');
  $('#bar-setup').classList.toggle('hidden', t !== 'setup');
  $('#bar-monitor').classList.toggle('hidden', t !== 'monitor');
  $('#btn-check').classList.toggle('hidden', t !== 'setup');
  $('#tab-setup').classList.toggle('on', t === 'setup');
  $('#tab-monitor').classList.toggle('on', t === 'monitor');
  updateFooter();
}

function nameState() {
  const id = S.run_id.trim();
  const r = runs.find(x => x.run_id === id);
  return r ? (r.alive ? 'alive' : 'exists') : 'new';
}

function setBarMsg(text, cls = '') {
  const m = $('#bar-msg');
  m.textContent = text;
  m.className = 'bar-msg ' + cls;
}

function updateFooter() {
  const btn = $('#btn-main');
  btn.disabled = false;
  if (tab === 'setup') {
    const st = nameState();
    if (st === 'alive') { btn.textContent = 'Stop this run'; btn.className = 'btn danger'; setBarMsg('This run is running now.'); }
    else if (st === 'exists') { btn.textContent = 'Resume run'; btn.className = 'btn primary'; setBarMsg('A run with this name exists. It resumes with its stored settings. Pick a new name to start fresh.'); }
    else { btn.textContent = 'Start agent loop'; btn.className = 'btn primary'; if ($('#bar-msg').className.indexOf('err') < 0) setBarMsg(''); }
  } else {
    $('#bar-watch').textContent = watched ? `Watching ${watched}` : 'No run selected';
    if (mon && mon.alive) { btn.textContent = 'Stop run'; btn.className = 'btn danger'; }
    else if (mon && mon.exists) { btn.textContent = 'Resume run'; btn.className = 'btn primary'; }
    else { btn.textContent = 'Nothing to run'; btn.className = 'btn primary'; btn.disabled = true; }
  }
}

async function mainAction() {
  let id, state;
  if (tab === 'setup') { id = S.run_id.trim(); state = nameState(); }
  else { id = watched; state = mon && mon.alive ? 'alive' : (mon && mon.exists ? 'exists' : 'new'); }
  try {
    if (state === 'alive') {
      const ok = await confirmModal('Stop this run?', [['Run', id]],
        'The simulation in progress is lost. Resume continues from the last finished round.', 'Stop run', true);
      if (!ok) return;
      await api('/api/stop', { run_id: id });
      toast(`Stopped ${id}`);
    } else if (state === 'exists') {
      const ok = await confirmModal('Resume this run?', [['Run', id]],
        'It continues from its last checkpoint with the settings it was started with.', 'Resume run');
      if (!ok) return;
      await api('/api/resume', { run_id: id });
      toast(`Resumed ${id}`);
      watch(id); setTab('monitor');
    } else {
      if (!S.goal.trim()) { setBarMsg('Write a goal for the planner first.', 'err'); $('#goal').focus(); return; }
      const p = payload();
      await api('/api/check', p);       // fails early with the loader's own message
      const c = D.chambers[S.chamber];
      const cost = S.test_mode ? 'small' : `about $${Math.max(1, Math.round(S.budget * 0.011))} of Claude usage (rough, from run 3)`;
      const ok = await confirmModal('Start the agent loop?', [
        ['Run name', p.run_id], ['Chamber', cap1(c.name)],
        ['Solve budget', `${S.budget} solves, up to ${S.rounds} rounds`],
        ['Backend', S.test_mode ? 'Mock (toy optics)' : 'COMSOL'],
        ['Screen mesh', S.remove_mesh ? 'Must be removed' : 'Planner may keep it'],
        ['Lens voltages', `${fmt(S.lv[0])} to ${fmt(S.lv[1])} V`],
        ['MCP front', `${fmt(S.mcp[0])} to ${fmt(S.mcp[1])} V`],
        ['Estimated cost', cost],
        ['Goal', S.goal.trim().slice(0, 160) + (S.goal.trim().length > 160 ? ' ...' : '')],
      ], 'The run keeps going if you close this window. Use Monitor to watch, answer questions or stop it.', 'Start run');
      if (!ok) return;
      await api('/api/start', p);
      toast(`Started ${p.run_id}`);
      await refreshRuns();
      watch(p.run_id); setTab('monitor');
    }
    await tick();
  } catch (e) {
    setBarMsg(e.message, 'err');
    toast(e.message, true);
  }
}

async function checkOnly() {
  if (!S.goal.trim()) { setBarMsg('Write a goal for the planner first.', 'err'); $('#goal').focus(); return; }
  try {
    await api('/api/check', { ...payload(), run_id: S.run_id.trim() || 'check-only' });
    setBarMsg('Settings are valid.', 'ok');
  } catch (e) { setBarMsg(e.message, 'err'); }
}

/* ------------------------------------------------------------------ monitor */

const STATE_UI = {
  RUNNING: ['Running', 'running'], RESTARTING: ['Restarting', 'warn'], QUESTION: ['Needs you', 'warn'],
  DONE: ['Done', 'done'], STOPPED: ['Stopped', 'idle'], CRITICAL: ['Critical error', 'bad'], IDLE: ['Idle', 'idle'],
};

function watch(id) {
  watched = id;
  mon = null;
  const sel = $('#watch');
  if (sel.value !== id) sel.value = id;
  updateFooter();
}

function renderMonitor() {
  const m = mon;
  const ui = m ? (STATE_UI[m.state] || [m.state, 'idle']) : STATE_UI.IDLE;
  $('#pill').className = 'pill ' + ui[1];
  $('#pill-text').textContent = ui[0];
  const active = !!(m && m.alive && m.state === 'RUNNING');
  $('#stage').classList.toggle('idle', !active);
  beamSpeed = active ? 1 : 0.35;
  if (!m) {
    $('#headline').textContent = watched ? 'Loading run status.' : 'No run selected. Start one on the Setup tab, or pick an earlier run above.';
    return;
  }
  const last = m.last_round ? m.last_round.replace(/^\[[^\]]*\]\s*/, '') : '';
  const reason = m.status && (m.status.reason || '');
  const text = {
    RUNNING: last ? `Running. Latest: ${last}` : 'Running. Waiting for the first round to report.',
    RESTARTING: 'The run stopped unexpectedly and is restarting by itself.',
    QUESTION: 'The planner has a question that only you can answer.',
    DONE: `Finished. ${(m.status && m.status.summary && m.status.summary[0]) || ''}`,
    STOPPED: 'Not running. Resume continues from the last checkpoint.',
    CRITICAL: `Needs attention: ${reason || 'the run could not continue'}`,
    IDLE: 'No run with this name yet.',
  }[m.state] || m.state;
  $('#headline').textContent = text;

  const sv = m.solves == null ? 0 : m.solves;
  $('#t-solves').textContent = m.budget ? `${sv} / ${m.budget}` : String(sv);
  $('#t-bar').style.width = m.budget ? Math.min(100, sv / m.budget * 100) + '%' : '0%';
  $('#t-rounds').textContent = String(m.rounds || 0);
  $('#t-rounds-sub').textContent = m.rounds_cap ? `cap ${m.rounds_cap}` : '';
  if (m.best && m.best.score != null) {
    $('#t-best').textContent = `${Number(m.best.score).toFixed(3)} deg`;
    $('#t-best-sub').textContent = `round ${m.best.round}` + (m.best.eta != null ? `, collection ${Math.round(m.best.eta * 100)} percent` : '') +
      (m.best.final ? '' : ', best study so far');
  } else { $('#t-best').textContent = 'none yet'; $('#t-best-sub').textContent = ''; }

  const q = $('#question');
  q.classList.toggle('hidden', m.state !== 'QUESTION');
  if (m.state === 'QUESTION') $('#q-text').textContent = m.question || (m.status && m.status.text) || '';

  const rep = $('#link-report');
  rep.classList.toggle('hidden', !m.report);
  rep.href = `/results/runs/${encodeURIComponent(m.run_id)}/report/index.html`;
  $('#edits').textContent = m.approved_edits ? `${m.approved_edits} model edit${m.approved_edits === 1 ? '' : 's'} approved automatically` : '';

  const log = $('#log');
  const near = log.scrollHeight - log.scrollTop - log.clientHeight < 60;
  const lines = (m.log && m.log.length) ? m.log : (m.supervisor_log || []);
  log.textContent = lines.join('\n') || 'The log is empty so far.';
  if (near) log.scrollTop = log.scrollHeight;
  $('#log-time').textContent = `updated ${m.time.slice(11)}`;
}

async function refreshRuns() {
  try {
    runs = (await api('/api/runs')).runs;
  } catch (e) { return; }
  const sel = $('#watch');
  const cur = watched;
  sel.replaceChildren(h('option', { value: '', text: 'Pick a run' }),
    ...runs.map(r => h('option', { value: r.run_id, text: r.run_id + (r.alive ? '  (running)' : '') })));
  sel.value = cur || '';
  updateFooter();
}

async function tick() {
  if (!watched) { renderMonitor(); return; }
  try {
    mon = await api('/api/monitor?run=' + encodeURIComponent(watched));
  } catch (e) { mon = null; }
  renderMonitor();
  updateFooter();
}

/* ------------------------------------------------------------------ start up */

async function init() {
  D = await api('/api/defaults');
  initSettings();

  // chamber drop-down
  const cs = $('#chamber');
  for (const [k, c] of Object.entries(D.chambers)) {
    cs.append(h('option', { value: k, text: cap1(c.name) + (c.usable ? '' : ', not usable yet'), disabled: !c.usable }));
  }
  cs.value = S.chamber;
  cs.addEventListener('change', () => { S.chamber = cs.value; save(); drawDiagram(); renderPage(); });

  // parameter pages
  const ps = $('#page');
  for (const p of PAGES) ps.append(h('option', { value: p.id, text: p.title }));
  ps.addEventListener('change', () => { S.page = ps.value; save(); renderPage(); });

  // goal
  const goal = $('#goal');
  goal.value = S.goal;
  goal.addEventListener('input', () => { S.goal = goal.value; save(); if ($('#bar-msg').className.indexOf('err') >= 0) setBarMsg(''); });
  const gl = $('#goal-load');
  gl.append(h('option', { value: '', text: 'Start from an earlier goal' }), ...D.goals.map(g => h('option', { value: g.file, text: g.name })));
  gl.addEventListener('change', async () => {
    if (!gl.value) return;
    try {
      const j = await api('/api/goal?file=' + encodeURIComponent(gl.value));
      goal.value = j.text; S.goal = j.text; save();
      toast('Goal loaded. Edit it, then start.');
    } catch (e) { toast(e.message, true); }
    gl.value = '';
  });

  ['#chamber', '#page', '#goal-load', '#watch'].forEach(id => enhanceSelect($(id)));

  // run name, buttons, tabs
  const rid = $('#run-id');
  rid.value = S.run_id;
  rid.addEventListener('input', () => { S.run_id = rid.value; setBarMsg(''); updateFooter(); });
  $('#btn-main').addEventListener('click', mainAction);
  $('#btn-check').addEventListener('click', checkOnly);
  document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => setTab(b.dataset.tab)));
  $('#watch').addEventListener('change', e => { watch(e.target.value || null); tick(); });
  $('#q-send').addEventListener('click', async () => {
    try {
      await api('/api/answer', { run_id: watched, text: $('#q-answer').value });
      $('#q-answer').value = '';
      toast('Answer sent. The run continues.');
      await tick();
    } catch (e) { toast(e.message, true); }
  });

  // optional deep link: ?chamber=3&page=positions&tab=monitor&run=run-4-cfg1-nomesh
  const q = new URLSearchParams(location.search);
  if (D.chambers[q.get('chamber')] && D.chambers[q.get('chamber')].usable) { S.chamber = q.get('chamber'); cs.value = S.chamber; }
  if (PAGES.some(p => p.id === q.get('page'))) S.page = q.get('page');
  drawDiagram();
  let rz = null;
  window.addEventListener('resize', () => { clearTimeout(rz); rz = setTimeout(drawDiagram, 150); });
  renderPage();
  await refreshRuns();
  const live = runs.find(r => r.alive);
  if (live) { watch(live.run_id); }
  if (q.get('run')) watch(q.get('run'));
  setTab(q.get('tab') === 'monitor' ? 'monitor' : 'setup');
  await tick();
  requestAnimationFrame(frame);
  setInterval(tick, 2500);
  setInterval(refreshRuns, 8000);
}

init().catch(e => {
  document.body.insertAdjacentHTML('beforeend',
    `<div class="toast err" style="display:block">Could not start the console: ${String(e.message).replace(/</g, '&lt;')}</div>`);
});

