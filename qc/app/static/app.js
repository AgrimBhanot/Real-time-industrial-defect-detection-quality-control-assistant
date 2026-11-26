"use strict";
const $ = (id) => document.getElementById(id);
const el = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null) continue;
    if (k === "class") e.className = v; else if (k === "text") e.textContent = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
  }
  e.append(...kids.filter((x) => x != null && x !== false));
  return e;
};
const NS = "http://www.w3.org/2000/svg";
const SVG = (tag, props = {}, ...kids) => {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(props)) if (k === "text") e.textContent = v; else e.setAttribute(k, v);
  e.append(...kids); return e;
};
const ICONS = {
  pause: '<rect x="6.5" y="5" width="3.5" height="14" rx="1"/><rect x="14" y="5" width="3.5" height="14" rx="1"/>',
  play: '<path d="M8 5.5v13l10.5-6.5z"/>',
  next: '<path d="M6 5.5v13l9.5-6.5z"/><path d="M19 5.5v13"/>',
  scan: '<path d="M4 8.5V6.5A2.5 2.5 0 0 1 6.5 4h2M15.5 4h2A2.5 2.5 0 0 1 20 6.5v2M20 15.5v2a2.5 2.5 0 0 1-2.5 2.5h-2M8.5 20h-2A2.5 2.5 0 0 1 4 17.5v-2"/><circle cx="12" cy="12" r="3.2"/>',
  x: '<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  ask: '<path d="M9.3 9.2a2.8 2.8 0 1 1 3.9 2.6c-.7.3-1.2 1-1.2 1.8v.6"/><path d="M12 17.6v.1"/>',
  download: '<path d="M12 4.5v10.5M7.5 10.5L12 15l4.5-4.5M5 19.5h14"/>',
  left: '<path d="M14.5 6l-6 6 6 6"/>', right: '<path d="M9.5 6l6 6-6 6"/>',
  doc: '<path d="M14 3.5H7.5a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2V8z"/><path d="M14 3.5V8h4.5M9 13h6M9 16.5h4"/>',
};
const icon = (name) => { const s = document.createElementNS(NS, "svg"); s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("class", "i"); s.setAttribute("aria-hidden", "true"); s.innerHTML = ICONS[name]; return s; };
const label = (node, name, text) => { node.replaceChildren(...(name ? [icon(name)] : []), el("span", { text })); return node; };

const fmt = (v, d = 1) => (v == null || Number.isNaN(Number(v))) ? "-" : Number(v).toFixed(d);
const pct = (a, b, d = 1) => b ? `${(100 * a / b).toFixed(d)}%` : "-";
const words = (s) => String(s ?? "").replace(/_/g, " ");
const cap = (s) => { s = words(s); return s.charAt(0).toUpperCase() + s.slice(1); };
const plural = (n, one, many = `${one}s`) => `${n} ${n === 1 ? one : many}`;
const tidy = (t) => String(t).replace(/\b(\d+) ([\w-]+ )?(defect|unit|part|finding)\(s\)/g, (m, n, mid, w) => `${n} ${mid || ""}${w}${n === "1" ? "" : "s"}`);
const RESULTS = ["FAIL", "REVIEW", "PASS_WITH_NOTE", "PASS"];
const RNAME = { PASS: "Pass", PASS_WITH_NOTE: "Pass with note", REVIEW: "Review", FAIL: "Fail" };
const RICON = { PASS: "check", PASS_WITH_NOTE: "check", REVIEW: "ask", FAIL: "x" };
const ONAME = { ok: "Agrees with labels", escape: "Missed defect", false_reject: "False reject" };
const DNAME = { confirmed: "Confirmed", false_alarm: "False alarm", missed_defect: "Missed defect", rework: "Rework", scrap: "Scrap" };
const RCOL = { FAIL: "var(--fail)", REVIEW: "var(--review)", PASS_WITH_NOTE: "var(--note)", PASS: "var(--pass)" };
const SCOL = { high: "var(--fail)", medium: "var(--review)", low: "var(--note)" };
const pill = (key, text, dot = true) => el("span", { class: `pill ${key || ""}` }, dot ? el("i") : null, text ?? words(key));
const passed = (c) => (c.PASS || 0) + (c.PASS_WITH_NOTE || 0);
const stat = (value, unit, text) => el("div", { class: "stat" }, el("b", {}, String(value), unit ? el("small", { text: unit }) : null), el("span", { text }));
const big = (value, unit) => el("div", { class: "big" }, String(value), unit ? el("small", { text: unit }) : null);
const store = { get(k) { try { return localStorage.getItem(k) || ""; } catch { return ""; } }, set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window */ } } };

async function api(url, body) {
  const r = await fetch(url, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json", "X-QC": "1" }, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `Request failed (${r.status})`);
  return j;
}
let alertTimer;
function say(msg, ms = 6000) { $("alert").textContent = msg; $("alert").hidden = !msg; clearTimeout(alertTimer); if (msg && ms) alertTimer = setTimeout(() => { $("alert").hidden = true; }, ms); }
const act = (p) => p.catch((e) => say(e.message));

/* ---- pages ---- */
let page = "";
function show(name) {
  if (!["inspect", "log", "analytics", "system"].includes(name)) name = "inspect";
  page = name;
  for (const b of document.querySelectorAll(".tabs button")) b.setAttribute("aria-selected", b.dataset.page === name);
  for (const m of document.querySelectorAll("main.page")) m.hidden = m.id !== `page-${name}`;
  $("view").src = name === "inspect" ? "/stream.mjpg" : "";   // one open stream at a time
  if (name === "log") { loadFacets(); loadLog(); } else if (name === "analytics") { loadFacets().then(loadAnalytics); } else if (name === "system") loadSystem();
  else if (S) drawInspect(S, true);
}
for (const b of document.querySelectorAll(".tabs button")) b.onclick = () => { location.hash = b.dataset.page; };
addEventListener("hashchange", () => route());
function route() {
  const [p, uid] = location.hash.slice(1).split("/");
  if (uid) { if (!page) show("log"); openUnit(uid); return; }
  closeUnit(false); if (p !== page) show(p || "inspect");
}

/* ---- shared pieces ---- */
function groupFindings(dets) {
  const groups = new Map();
  for (const d of dets) {
    const k = [d.part, d.defect, d.severity, d.needs_review].join("|");
    const g = groups.get(k) || { ...d, n: 0, zones: new Set(), best: 0 };
    g.n++; g.zones.add(d.zone); g.best = Math.max(g.best, d.confidence); g.size = Math.max(g.size, d.size); groups.set(k, g);
  }
  const rank = { high: 0, medium: 1, low: 2 };
  return [...groups.values()].sort((a, b) => rank[a.severity] - rank[b.severity] || b.size - a.size);
}
function findingsList(dets, max = 99) {
  if (!dets.length) return el("div", { class: "empty", text: "No defects found." });
  const g = groupFindings(dets), shown = g.slice(0, max);
  return el("div", {}, ...shown.map((f) => el("div", { class: "finding" },
    el("i", { style: `background:${SCOL[f.severity]}` }),
    el("b", { text: `${f.part ? `${cap(f.part)} · ` : ""}${words(f.defect)}${f.n > 1 ? ` × ${f.n}` : ""}` }),
    el("span", { class: "val", text: f.size_unit === "part_frac" ? `${fmt(100 * f.size, 0)}%` : fmt(f.best, 2) }),
    el("small", { text: [`${f.severity} severity`, `zone ${[...f.zones].sort().join(", ")}`, f.size_unit === "part_frac" ? "share of the part" : "confidence",
      f.size_unit === "mm2" ? `largest ${fmt(f.size, 2)} mm²` : "", f.needs_review ? "needs a person" : ""].filter(Boolean).join(" · ") }))),
    g.length > max ? el("div", { class: "more", text: `${g.length - max} more in the log` }) : null);
}
function adviceBox(a) {
  const x = a.advice || {}, box = el("div");
  if (x.summary) box.append(el("p", { class: "adv-sum", text: tidy(x.summary.replace(/^(PASS_WITH_NOTE|PASS|REVIEW|FAIL):/, (m, k) => `${RNAME[k]}:`)) }));
  const cols = [["Likely causes", x.likely_causes], ["What to do", x.recommended_actions], ["Then verify", x.verify]].filter(([, v]) => v && v.length);
  if (cols.length) box.append(el("div", { class: "adv-cols" }, ...cols.map(([t, v]) => el("div", {}, el("h3", { text: t }), Array.isArray(v) ? el("ul", {}, ...v.map((i) => el("li", { text: i }))) : el("div", { text: v })))));
  const llm = a.backend === "executorch" && !a.fallback;
  const meta = el("div", { class: "adv-meta" }, el("span", { text: a.fallback ? "Procedure template: Llama's answer was rejected by the validator" : llm ? `Llama 3.2 1B on the Arm CPU${a.repaired ? ", checked and repaired by the validator" : ", checked by the validator"}` : "Procedure template" }));
  if (llm && a.total_ms) meta.append(el("span", {}, el("b", { text: `${fmt(a.total_ms / 1000)} s` }), " to answer"), el("span", {}, el("b", { text: `${fmt(a.ttft_ms / 1000)} s` }), " to first word"), el("span", {}, el("b", { text: fmt(a.tok_s) }), " tokens/s"));
  box.append(meta);
  return box;
}
function gauge(segs, centre, sub) {
  const W = 220, H = 128, cx = 110, cy = 112, r = 84, sw = 18, total = segs.reduce((t, s) => t + s.n, 0);
  const pt = (t, rr) => [cx + rr * Math.cos(Math.PI * (1 - t)), cy - rr * Math.sin(Math.PI * (1 - t))];
  const arc = (a, b) => { const [x1, y1] = pt(a, r), [x2, y2] = pt(b, r); return `M${x1.toFixed(2)},${y1.toFixed(2)} A${r},${r} 0 0 1 ${x2.toFixed(2)},${y2.toFixed(2)}`; };
  const g = SVG("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": `${centre} ${sub}` });
  for (let i = 0; i <= 48; i++) { const t = i / 48, [x1, y1] = pt(t, r + sw / 2 + 5), [x2, y2] = pt(t, r + sw / 2 + (i % 6 ? 9 : 12)); g.append(SVG("line", { x1, y1, x2, y2, stroke: "var(--line)", "stroke-width": 1.4, "stroke-linecap": "round" })); }
  g.append(SVG("path", { d: arc(0, 1), stroke: "var(--card-2)", "stroke-width": sw, fill: "none", "stroke-linecap": "round" }));
  let t0 = 0; const gap = 0.012;
  for (const s of segs) {
    if (!s.n || !total) continue;
    const t1 = t0 + s.n / total, p = SVG("path", { d: arc(t0 === 0 ? 0 : t0 + gap / 2, t1 >= 1 ? 1 : t1 - gap / 2), stroke: s.c, "stroke-width": sw, fill: "none", "stroke-linecap": "butt" });
    g.append(hint(p, `${s.t}: ${s.n} (${pct(s.n, total)})`)); t0 = t1;
  }
  g.append(SVG("text", { x: cx, y: cy - 14, "text-anchor": "middle", class: "gauge-num", text: centre }), SVG("text", { x: cx, y: cy + 8, "text-anchor": "middle", class: "gauge-lbl", text: sub }));
  return g;
}

/* ---- inspect ---- */
const PACE = [0.1, 0.2, 0.5, 1, 2, 4, 10];
const paceText = (v) => v >= 1 ? `${fmt(v, v % 1 ? 1 : 0)} per second` : `one every ${fmt(1 / v, 0)} s`;
const TICKS = 48;
let S = null, keys = {};
const changed = (k, v) => { if (keys[k] === v) return false; keys[k] = v; return true; };
function lineText(s) {
  const what = cap(s.title || s.label || "");
  if (s.trigger) return `${what}. A tray is logged once its parts lie still; the board finds each part and measures rust on it.`;
  if (!s.inspect) return `${what}. Camera view only.`;
  return `${what}, played at ${paceText(s.fps_limit)}. Each verdict is checked against the dataset's own labels.`;
}
function drawInspect(s, force = false) {
  if (force) keys = {};
  const c = s.counts, n = RESULTS.reduce((t, r) => t + (c[r] || 0), 0), t = s.telemetry || {}, g = s.gt_counts || {}, gn = (g.ok || 0) + (g.escape || 0) + (g.false_reject || 0);
  const r = s.record;
  if (changed("title", s.label + s.title + s.fps_limit + s.trigger)) { $("line-title").textContent = s.label || "QC Inspector"; $("line-desc").textContent = lineText(s); }
  // stage messages and controls
  const cam = s.camera, v = $("view-msg"); let msg = "";
  if (s.switching) msg = `Switching to ${words(s.switching)} ...`; else if (cam && !cam.live) msg = `No camera signal. ${cam.error || "Connecting ..."}`; else if (s.inspect && !r && !s.live) msg = "Loading the model ...";
  v.hidden = !msg; v.textContent = msg;
  const lc = $("live-chip");
  lc.className = `live ${s.paused ? "paused" : "on"}`;
  lc.lastChild.textContent = s.paused ? (s.trigger ? "Logging paused" : "Paused") : s.trigger ? `Live · ${fmt(s.fps, 0)} FPS` : s.inspect ? "Dataset replay" : "Camera";
  if (changed("ctl", [s.paused, s.trigger, s.inspect].join())) {
    label($("play"), s.paused ? "play" : "pause", s.paused ? "Resume" : "Pause"); $("play").disabled = !s.inspect;
    label($("step"), "next", "Next unit"); $("step").hidden = s.trigger || !s.inspect;
    label($("inspect-now"), "scan", "Inspect now"); $("inspect-now").hidden = !s.trigger;
    $("pace-wrap").hidden = s.trigger || !s.inspect;
  }
  if (document.activeElement !== $("pace")) { const i = PACE.reduce((b, p, k) => Math.abs(p - s.fps_limit) < Math.abs(PACE[b] - s.fps_limit) ? k : b, 0); $("pace").value = i; $("pace-val").textContent = paceText(s.fps_limit); }
  // session strip: ticks, thumbnails, stats
  const sk = s.session + s.recent.map((x) => x.unit_id + x.result).join();
  if (changed("recent", sk)) {
    const rec = s.recent.slice(-TICKS), last = rec.at(-1)?.unit_id;
    $("ticks").replaceChildren(...Array.from({ length: TICKS }, (_, i) => {
      const u = rec[i]; if (!u) return el("i");
      const tk = el("i", { "data-u": u.unit_id, class: u.unit_id === last ? "now" : null, style: `background:${RCOL[u.result]}` });
      tk.onclick = () => { location.hash = `inspect/${u.unit_id}`; };
      return hint(tk, `${u.unit_id}\n${RNAME[u.result]}${u.gt_outcome && u.gt_outcome !== "ok" ? ` · ${ONAME[u.gt_outcome]}` : ""}`);
    }));
    $("ticks").setAttribute("aria-label", `Latest ${rec.length} units of this session, oldest first`);
    const six = [...s.recent].slice(-6).reverse();
    $("recent").replaceChildren(...six.map((u) => el("button", { type: "button", title: `Open ${u.unit_id}`, style: `--c:${RCOL[u.result]}`, onclick: () => { location.hash = `inspect/${u.unit_id}`; } },
      el("img", { src: `/api/unit/${u.unit_id}/image.jpg?w=360`, alt: `${u.unit_id}, ${RNAME[u.result]}`, loading: "lazy" }), el("span", {}, el("i"), el("b", { text: RNAME[u.result] }), `· ${u.unit_id.slice(-5)}`))),
      ...Array.from({ length: 6 - six.length }, () => el("div", { class: "slot" })));
  }
  const visionMs = s.trigger ? s.live?.vision_ms : r?.timings_ms?.vision;
  $("stage-stats").replaceChildren(stat(n, null, s.trigger ? "Trays inspected" : "Units inspected"), stat(fmt(visionMs, 0), "ms", "Vision per frame"),
    s.trigger || !gn ? stat(t.power_mw ? fmt(t.power_mw / 1000) : "-", "W", "Board power") : stat(pct(g.ok || 0, gn, 0), null, "Verdicts matching labels"));
  // verdict
  const vd = $("verdict"), res = r ? r.inspection_result : "";
  vd.className = `card verdict ${res}`;
  $("v-ico").replaceChildren(icon(r ? RICON[res] : s.trigger ? "scan" : "next"));
  $("v-unit").textContent = r ? `${r.unit_id} · ${r.timestamp.slice(11, 19)}` : "No unit yet";
  $("v-word").textContent = r ? RNAME[res] : s.inspect ? "Waiting" : "Camera only";
  $("v-why").textContent = r ? tidy(cap(r.rule_trace[r.rule_trace.length - 1].replace(/^(FAIL|REVIEW|PASS)( with note| \(rework\))?: /i, ""))) : s.trigger ? "Place parts on the tray and keep them still." : "";
  const gt = r && r.gt_result ? (["PASS", "PASS_WITH_NOTE"].includes(r.gt_result) === ["PASS", "PASS_WITH_NOTE"].includes(res) ? "ok" : ["PASS", "PASS_WITH_NOTE"].includes(r.gt_result) ? "false_reject" : "escape") : null;
  if (changed("vfoot", [r?.unit_id, gt].join())) $("v-foot").replaceChildren(...(r ? [el("span", { class: "pill", text: r.detections.length ? plural(r.detections.length, "finding") : "No findings" }),
    r.parts?.length ? el("span", { class: "pill", text: plural(r.parts.length, "part") }) : null, gt ? el("span", { class: "pill" }, el("i"), ONAME[gt]) : null].filter(Boolean) : []));
  // side card: parts on the tray, or the dataset's labels
  if (s.trigger) {
    $("side-title").textContent = "Parts in view";
    const parts = s.live ? s.live.parts : {};
    if (changed("side", JSON.stringify(parts))) $("side-body").replaceChildren(el("div", { class: "trio" }, ...["nut", "bolt", "washer"].map((k) => el("div", {}, big(parts[k] || 0), el("span", { class: "lbl", text: (parts[k] || 0) === 1 ? cap(k) : `${cap(k)}s` })))));
  } else {
    $("side-title").textContent = "Against the labels";
    if (changed("side", JSON.stringify([r?.gt_result, r?.gt_defects, g]))) $("side-body").replaceChildren(
      el("div", { class: "kv-mini" },
        el("div", {}, "This unit is labelled", el("b", { text: r?.gt_result ? RNAME[r.gt_result] : "-" })),
        el("div", {}, "Labelled defects", el("b", { text: r?.gt_defects?.length ? [...new Set(r.gt_defects)].map(words).join(", ") : "none" })),
        el("div", {}, "Missed defects this session", el("b", { text: g.escape || 0 })),
        el("div", {}, "False rejects this session", el("b", { text: g.false_reject || 0 }))));
  }
  // yield
  if (changed("yield", JSON.stringify(c))) $("yield").replaceChildren(gauge(RESULTS.slice().reverse().map((k) => ({ n: c[k] || 0, c: RCOL[k], t: RNAME[k] })), n ? pct(passed(c), n, 0) : "-", "passed"),
    el("div", { class: "legend-rows" }, ...RESULTS.slice().reverse().map((k) => el("div", {}, el("i", { style: `background:${RCOL[k]}` }), RNAME[k], el("b", { text: c[k] || 0 })))));
  // findings
  if (changed("find", r ? r.unit_id : "")) { $("findings").replaceChildren(!r ? el("div", { class: "empty", text: "Nothing inspected yet." }) : r.detections.length ? findingsList(r.detections, 5) : el("div", { class: "ok-empty" }, el("span", {}, icon("check")), "No defects on this unit"));
    $("findings").className = r && !r.detections.length ? "ok-empty-wrap" : ""; $("find-count").textContent = r && r.detections.length ? String(r.detections.length) : ""; }
  // board
  const tc = t.temps_c || {}, soc = ["soc0", "soc1", "soc2"].map((k) => tc[k]).filter((x) => x != null);
  const temps = [["CPU", tc.cpu], ["GPU", tc.gpu], ["SoC", soc.length ? soc.reduce((a, b) => a + b) / soc.length : null], ["Junction", tc.tj ?? t.temp_c]];
  $("board").replaceChildren(el("div", { class: "temps" }, ...temps.map(([k, v]) => el("div", { class: `temp ${v > 80 ? "hot" : ""}` }, el("em", { text: v == null ? "-" : `${fmt(v, 0)} °C` }), el("div", { class: "tube" }, el("span", { style: `height:${Math.max(4, Math.min(100, v || 0))}%` })), k))),
    el("div", { class: "kv-mini" }, el("div", {}, "Board power", el("b", { text: t.power_mw ? `${fmt(t.power_mw / 1000)} W` : "-" })), el("div", {}, "GPU load", el("b", { text: t.gpu_pct == null ? "-" : `${fmt(t.gpu_pct, 0)}%` })),
      el("div", {}, "CPU load", el("b", { text: t.cpu_pct == null ? "-" : `${fmt(t.cpu_pct, 0)}%` })), el("div", {}, "Memory", el("b", { text: t.ram_used_mb ? `${fmt(t.ram_used_mb / 1024)} / ${fmt(t.ram_total_mb / 1024)} GB` : "-" }))));
  fitView();
  // advice
  const adv = s.advice_current || s.advice_latest, b = $("adv-badge");
  const ex = s.advisory_backend === "executorch";
  b.className = `badge ${s.advice_writing ? "writing" : ex && t.llm_rss_mb ? "ready" : ""}`;
  b.textContent = s.advice_writing ? "Writing" : s.advisory_backend === "disabled" ? "Off" : !ex ? "Template" : t.llm_rss_mb ? "Ready" : "Starting";
  if (changed("adv", [adv?.unit_id, s.advice_writing, s.advisory_backend].join())) {
    $("adv-unit").textContent = adv ? (s.advice_current ? "for this unit" : `for ${adv.unit_id}`) : "";
    const note = s.advisory_backend === "disabled" ? "Advice is off." : s.advice_writing ? `Writing about ${s.advice_writing} ...` : "";
    $("advice").replaceChildren(...(note ? [el("div", { class: "adv-note", text: note })] : []), adv ? adviceBox(adv) : note ? "" : el("div", { class: "empty", text: "Advice is written for units that fail, need review or pass with a note." }));
  }
}
function fitView() {   // the frame takes the image's own shape, so findings are never cropped and no bars are drawn
  const img = $("view"), w = $("view-wrap"), f = $("view-frame"), a = img.naturalWidth && img.naturalHeight ? img.naturalWidth / img.naturalHeight : 16 / 9;
  if (w.clientWidth < 10) return;
  if (getComputedStyle(w).display !== "grid") { f.style.cssText = `aspect-ratio:${a}`; return; }
  let W = w.clientWidth, H = W / a; if (H > w.clientHeight) { H = w.clientHeight; W = H * a; }
  f.style.cssText = `width:${Math.floor(W)}px;height:${Math.floor(H)}px;aspect-ratio:auto;max-height:none`;
}
addEventListener("resize", fitView); $("view").addEventListener("load", fitView);
$("play").onclick = () => act(api("/api/control", { action: S?.paused ? "play" : "pause" }).then(tick));
$("step").onclick = () => act(api("/api/control", { action: "step" }).then(() => setTimeout(tick, 250)));
$("inspect-now").onclick = () => act(api("/api/control", { action: "inspect_now" }));
$("pace").oninput = () => { $("pace-val").textContent = paceText(PACE[$("pace").value]); };
$("pace").onchange = () => act(api("/api/control", { action: "pace", value: PACE[$("pace").value] }).then(() => $("pace").blur()));
$("line").onchange = () => act(api("/api/line", { name: $("line").value }).then(() => { keys = {}; tick(); }).catch((e) => { loadLines(); throw e; }));
async function loadLines() {
  const j = await api("/api/lines");
  $("line").replaceChildren(...j.lines.map((x) => { const o = el("option", { value: x.name, text: x.label + (x.ready ? "" : ` (${x.why})`) }); o.disabled = !x.ready; return o; }));
  $("line").value = j.current;
}
let lastProfile = "", stickyErr = "";
async function tick() {
  let s; try { s = await api("/api/state"); } catch { say("The inspection service is not answering. Retrying ...", 0); stickyErr = "down"; return; }
  if (stickyErr === "down") { say(""); stickyErr = ""; if (page === "inspect") $("view").src = `/stream.mjpg?${Date.now()}`; }
  if (s.error && s.error !== stickyErr) { stickyErr = s.error; say(s.error, 0); } else if (!s.error && stickyErr) { stickyErr = ""; say(""); }
  S = s;
  if (s.profile !== lastProfile) { lastProfile = s.profile; keys = {}; loadLines().catch(() => {}); }
  const ex = s.advisory_backend === "executorch", up = ex && s.telemetry?.llm_rss_mb, ch = $("llm-chip");
  ch.className = `chip ${s.advice_writing ? "busy" : up ? "on" : ""}`;
  ch.lastChild.textContent = ex ? (up ? (s.advice_writing ? "Llama writing" : "Llama ready") : "Llama starting") : s.advisory_backend === "template" ? "Template advice" : "Advice off";
  if (page === "inspect") drawInspect(s);
}

/* ---- log ---- */
const L = { offset: 0, limit: 50, results: new Set(), key: "" };
$("f-results").append(...RESULTS.map((r) => el("button", { type: "button", "aria-pressed": "false", onclick: (e) => { const on = !L.results.has(r); on ? L.results.add(r) : L.results.delete(r); e.currentTarget.setAttribute("aria-pressed", on); L.offset = 0; loadLog(); } }, el("i", { style: `background:${RCOL[r]}` }), RNAME[r])));
label($("f-csv"), "download", "Export CSV"); label($("p-new"), "left", "Newer"); label($("p-old"), "right", "Older"); label($("summary-btn"), "doc", "Ask Llama for a shift summary");
function fill(sel, items, name = (x) => x, any = "any") { const v = sel.value; sel.replaceChildren(el("option", { value: "", text: any }), ...items.map((x) => el("option", { value: x, text: name(x) }))); if (items.includes(v)) sel.value = v; }
async function loadFacets() {
  const f = await api("/api/facets").catch(() => null); if (!f) return;
  const F = $("filters"), A = $("a-filters");
  for (const q of [F, A]) { fill(q.profile, f.profiles, cap, "All lines"); fill(q.session, f.sessions, (x) => x === S?.session ? `${x} (now)` : x, "All sessions"); }
  if (!A.dataset.init && S) { A.dataset.init = 1; A.profile.value = S.profile; A.session.value = S.session; }  // analytics opens on what is running now
  fill(F.defect, f.defects, cap); fill(F.decision, ["open", ...f.decisions], (x) => x === "open" ? "To be decided" : DNAME[x]);
}
function query(extra = {}) {
  const F = $("filters"), p = new URLSearchParams();
  for (const k of ["profile", "defect", "decision", "gt_outcome", "session", "q"]) if (F[k].value) p.set(k, F[k].value);
  if (L.results.size) p.set("results", [...L.results].join(","));
  if (F.from.value) p.set("since", F.from.value);
  if (F.to.value) { const d = new Date(`${F.to.value}T12:00`); d.setDate(d.getDate() + 1); p.set("until", `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`); }
  for (const [k, v] of Object.entries(extra)) p.set(k, v);
  return p;
}
async function loadLog() {
  $("f-csv").href = `/api/export.csv?${query()}`;
  let j; try { j = await api(`/api/log?${query({ limit: L.limit, offset: L.offset })}`); } catch (e) { say(e.message); return; }
  const key = JSON.stringify([j.total, j.rows.map((r) => [r.unit_id, r.advice_summary, r.decision])]); if (key === L.key) return; L.key = key;
  $("log-total").textContent = `${j.total.toLocaleString("en")} unit${j.total === 1 ? "" : "s"} match these filters`;
  $("log-mix").replaceChildren(...RESULTS.filter((r) => j.by_result[r]).map((r) => pill(r, `${j.by_result[r].toLocaleString("en")} ${RNAME[r].toLowerCase()}`)));
  $("log-rows").replaceChildren(...(j.rows.length ? j.rows.map((r) => {
    const go = () => { location.hash = `log/${r.unit_id}`; }, n = {}; for (const d of (r.defects || "").split(" ").filter(Boolean)) { const k = d.split(":")[0]; n[k] = (n[k] || 0) + 1; }
    const f = Object.entries(n).map(([k, v]) => words(k) + (v > 1 ? ` × ${v}` : "")).join(", ");
    return el("tr", { tabindex: "0", onclick: go, onkeydown: (e) => { if (e.key === "Enter") go(); } },
      el("td", {}, el("img", { src: `/api/unit/${r.unit_id}/image.jpg?w=200`, alt: "", loading: "lazy" })),
      el("td", {}, el("b", { text: r.unit_id }), el("small", { text: `${(r.ts || "").slice(0, 10)} · ${(r.ts || "").slice(11, 19)}` })), el("td", { text: cap(r.profile) }), el("td", {}, pill(r.result, RNAME[r.result])),
      el("td", { class: f ? "" : "none", text: f || "none" }), el("td", {}, r.gt_outcome ? pill(r.gt_outcome, ONAME[r.gt_outcome]) : el("span", { class: "none", text: "-" })),
      el("td", {}, el("div", { class: "clip", text: r.advice_summary || "-" })), el("td", {}, r.decision ? pill("", DNAME[r.decision], false) : ["FAIL", "REVIEW"].includes(r.result) ? el("span", { class: "none", text: "To be decided" }) : ""), el("td", { class: "num", text: `${fmt(r.vision_ms, 0)} ms` }));
  }) : [el("tr", {}, el("td", { colspan: "9", class: "empty", text: "No units match these filters." }))]));
  $("p-new").disabled = L.offset === 0; $("p-old").disabled = L.offset + L.limit >= j.total;
  $("p-pos").textContent = j.total ? `${(L.offset + 1).toLocaleString("en")} to ${Math.min(L.offset + L.limit, j.total).toLocaleString("en")} of ${j.total.toLocaleString("en")}` : "";
}
let typing; $("filters").addEventListener("input", (e) => { clearTimeout(typing); typing = setTimeout(() => { L.offset = 0; loadLog(); }, e.target.name === "q" ? 300 : 0); });
$("filters").addEventListener("submit", (e) => e.preventDefault());
$("f-clear").onclick = () => { $("filters").reset(); L.results.clear(); for (const b of $("f-results").children) b.setAttribute("aria-pressed", "false"); L.offset = 0; loadLog(); };
$("p-new").onclick = () => { L.offset = Math.max(0, L.offset - L.limit); loadLog(); }; $("p-old").onclick = () => { L.offset += L.limit; loadLog(); };

/* ---- one unit ---- */
let back = null;
async function openUnit(uid) {
  let u; try { u = await api(`/api/unit/${encodeURIComponent(uid)}`); } catch { say(`Unit ${uid} was not found.`); location.hash = page || "log"; return; }
  if ($("drawer").hidden) back = document.activeElement;
  const r = u.record, D = $("drawer"), base = `/api/unit/${u.unit_id}/image.jpg`;
  const img = el("img", { src: base, alt: `Inspected image of ${u.unit_id}`, onerror: (e) => { e.target.parentNode.replaceChildren(el("div", { class: "empty", style: "padding:48px;text-align:center;color:var(--on-stage-2)", text: "The image of this unit was not kept." })); } });
  const nav = (id, ic, t) => { const b = label(el("button", { class: "btn ghost", type: "button", onclick: () => { location.hash = `${page}/${id}`; } }), ic, t); b.disabled = !id; return b; };
  const op = el("input", { type: "text", placeholder: "Your name or initials", "aria-label": "Operator", value: store.get("qc-operator"), maxlength: "60" }), note = el("input", { type: "text", placeholder: "Note (optional)", "aria-label": "Note", maxlength: "500" });
  const choose = (d) => act(api(`/api/unit/${u.unit_id}/decision`, { decision: d, operator: op.value, note: note.value }).then(() => { store.set("qc-operator", op.value); L.key = ""; openUnit(u.unit_id); if (page === "log") loadLog(); }));
  const choices = ["FAIL", "REVIEW"].includes(u.result) ? ["confirmed", "false_alarm", "rework", "scrap"] : ["confirmed", "missed_defect"];
  const t = r.timings_ms || {}, a = u.advice, box = el("input", { type: "checkbox", id: "d-boxes", onchange: (e) => { img.src = `${base}?boxes=${e.target.checked ? 1 : 0}`; } }); box.checked = true;
  D.replaceChildren(
    el("div", { class: "d-head" }, el("h1", { id: "d-title", text: u.unit_id }), pill(u.result, RNAME[u.result]), u.gt_outcome ? pill(u.gt_outcome, ONAME[u.gt_outcome]) : null, el("span", { class: "grow" }), nav(u.newer, "left", "Newer"), nav(u.older, "right", "Older"), label(el("button", { class: "btn dark", id: "d-close", type: "button", onclick: () => closeUnit(true) }), "x", "Close")),
    el("div", { class: "d-img" }, img),
    el("div", { class: "d-tools" }, box, el("label", { for: "d-boxes", text: "Show findings on the image" }), el("span", { class: "grow" }), el("span", { text: `${cap(u.profile)} · ${u.ts.slice(0, 19).replace("T", " ")}` })),
    el("div", { class: "d-grid" },
      el("section", { class: "card decide wide" }, el("h2", { text: "Operator decision" }), el("div", { class: "row" }, op, note), el("div", { class: "row" }, ...choices.map((d) => el("button", { class: d === "confirmed" ? "btn dark" : "btn ghost", type: "button", text: DNAME[d], onclick: () => choose(d) }))),
        u.decisions.length ? el("ul", { class: "hist" }, ...u.decisions.map((x) => el("li", { text: `${DNAME[x.decision]}${x.operator ? ` by ${x.operator}` : ""}, ${x.ts.slice(0, 16).replace("T", " ")}${x.note ? `: ${x.note}` : ""}` }))) : null),
      el("section", { class: "card" }, el("h2", { text: "Findings" }), findingsList(r.detections || []), el("h2", { text: "How the rules decided", style: "margin-top:18px" }), el("ul", { class: "trace" }, ...(r.rule_trace || []).map((x) => el("li", { text: x })))),
      el("section", { class: "card" }, el("h2", { text: "Llama advice" }), a ? adviceBox(a) : el("div", { class: "empty", text: "No advice was written for this unit." }), a && a.errors.length ? el("ul", { class: "trace", style: "margin-top:10px" }, ...a.errors.map((x) => el("li", { text: x }))) : null),
      el("section", { class: "card wide" }, el("h2", { text: "Record" }),
        el("dl", { class: "kv" }, ...[["Line", cap(u.profile)], ["Time", u.ts], ["Session", u.session], ["Source", u.image_ref], ["Labelled verdict", r.gt_result ? `${RNAME[r.gt_result]}${r.gt_defects?.length ? ` (${[...new Set(r.gt_defects)].map(words).join(", ")})` : ""}` : null], ["Parts", r.parts?.length ? Object.entries(r.parts.reduce((m, p) => ({ ...m, [p.type]: (m[p.type] || 0) + 1 }), {})).map(([k, v]) => `${v} ${k}`).join(", ") : null],
          ["Vision", `${fmt(t.vision)} ms (pre ${fmt(t.pre)}, inference ${fmt(t.infer)}, post ${fmt(t.post)}${t.anomaly ? `, anomaly ${fmt(t.anomaly)}` : ""}${t.checks ? `, part checks ${fmt(t.checks)}` : ""})`], ["Frame to verdict", `${fmt(t.e2e)} ms`]].filter(([, v]) => v).flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])))));
  D.hidden = $("scrim").hidden = false; D.scrollTop = 0; $("d-close").focus();
}
function closeUnit(nav) { if ($("drawer").hidden) return; $("drawer").hidden = $("scrim").hidden = true; if (nav) location.hash = page; if (back) back.focus?.(); }
$("scrim").onclick = () => closeUnit(true);
addEventListener("keydown", (e) => {
  if ($("drawer").hidden) return;
  if (e.key === "Escape") closeUnit(true);
  if (e.key === "Tab") { const f = [...$("drawer").querySelectorAll("button:not(:disabled),input,a")]; if (!f.length) return; if (e.shiftKey && document.activeElement === f[0]) { f.at(-1).focus(); e.preventDefault(); } else if (!e.shiftKey && document.activeElement === f.at(-1)) { f[0].focus(); e.preventDefault(); } }
});

/* ---- charts ---- */
function hint(node, text) {
  node.addEventListener("pointermove", (e) => { const t = $("tip"); t.textContent = typeof text === "function" ? text() : text; t.hidden = false; t.style.left = `${Math.min(e.clientX + 14, innerWidth - t.offsetWidth - 8)}px`; t.style.top = `${e.clientY + 16}px`; });
  node.addEventListener("pointerleave", () => { $("tip").hidden = true; }); return node;
}
const legend = (items) => el("div", { class: "legend" }, ...items.map(([n, c]) => el("span", {}, el("i", { style: `background:${c}` }), n)));
const none = (t) => el("div", { class: "empty", text: t });
const when = (ts) => ts.slice(5, 16).replace("T", " ");
function trendChart(trend, width = 760) {
  if (!trend.length) return none("No units yet.");
  const W = Math.max(360, Math.round(width)), H = 250, l = 40, rgt = 64, top = 10, b = 26, X = (i) => trend.length === 1 ? l + (W - l - rgt) / 2 : l + (W - l - rgt) * i / (trend.length - 1), Y = (v) => top + (H - top - b) * (1 - v / 100);
  const series = [{ k: "pass", t: "Passed", c: "var(--pass)", f: (x) => 100 * ((x.PASS || 0) + (x.PASS_WITH_NOTE || 0)) / x.n }, { k: "fail", t: "Failed", c: "var(--fail)", f: (x) => 100 * (x.FAIL || 0) / x.n }];
  const g = SVG("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart", role: "img", "aria-label": "Share of units passed and failed over time, oldest first; the rest went to review" });
  const defs = SVG("defs"); g.append(defs);
  for (const s of series) defs.append(SVG("linearGradient", { id: `g-${s.k}`, x1: 0, x2: 0, y1: 0, y2: 1 }, SVG("stop", { offset: "0", "stop-color": s.c, "stop-opacity": ".22" }), SVG("stop", { offset: "1", "stop-color": s.c, "stop-opacity": "0" })));
  for (const v of [0, 25, 50, 75, 100]) g.append(SVG("line", { x1: l, x2: W - rgt, y1: Y(v), y2: Y(v), class: "gl", "stroke-dasharray": v ? "2 4" : "" }), SVG("text", { x: l - 8, y: Y(v) + 4, "text-anchor": "end", text: `${v}%` }));
  for (const s of series) {
    const pts = trend.map((x, i) => [X(i), Y(s.f(x))]);
    g.append(SVG("path", { d: `M${pts[0][0]},${Y(0)} ` + pts.map((p) => `L${p[0]},${p[1]}`).join(" ") + ` L${pts.at(-1)[0]},${Y(0)} Z`, fill: `url(#g-${s.k})` }));
    g.append(SVG("polyline", { points: pts.map((p) => p.join(",")).join(" "), fill: "none", stroke: s.c, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
    if (pts.length === 1) g.append(SVG("circle", { cx: pts[0][0], cy: pts[0][1], r: 5, fill: s.c, stroke: "var(--card)", "stroke-width": 2 }));
    g.append(SVG("text", { x: pts.at(-1)[0] + 8, y: pts.at(-1)[1] + 4, class: "ink", style: "fill:var(--ink);font-weight:600", text: `${fmt(s.f(trend.at(-1)), 0)}%` }));
  }
  const xl = [[0, "start"], [Math.floor((trend.length - 1) / 2), "middle"], [trend.length - 1, "end"]].filter((v, i, a) => a.findIndex((w) => w[0] === v[0]) === i);
  for (const [i, an] of xl) g.append(SVG("text", { x: X(i), y: H - 6, "text-anchor": trend.length === 1 ? "middle" : an, text: when(trend[i].from) }));
  const cross = SVG("line", { y1: top, y2: H - b, stroke: "var(--ink-3)", "stroke-width": 1, visibility: "hidden" }), dots = series.map((s) => SVG("circle", { r: 5, fill: s.c, stroke: "var(--card)", "stroke-width": 2, visibility: "hidden" }));
  const area = SVG("rect", { x: l, y: 0, width: W - l - rgt, height: H - b, fill: "transparent" }); g.append(cross, ...dots, area);
  area.addEventListener("pointermove", (e) => {
    const q = g.getBoundingClientRect(), x = (e.clientX - q.left) / q.width * W, i = trend.length === 1 ? 0 : Math.max(0, Math.min(trend.length - 1, Math.round((x - l) / (W - l - rgt) * (trend.length - 1)))), d = trend[i];
    cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i)); cross.setAttribute("visibility", "visible");
    series.forEach((s, k) => { dots[k].setAttribute("cx", X(i)); dots[k].setAttribute("cy", Y(s.f(d))); dots[k].setAttribute("visibility", "visible"); });
    const t = $("tip"); t.textContent = `${when(d.from)} to ${d.to.slice(11, 16)}\n${d.n} units: ${RESULTS.filter((r) => d[r]).map((r) => `${d[r]} ${RNAME[r].toLowerCase()}`).join(", ")}`; t.hidden = false;
    t.style.left = `${Math.min(e.clientX + 14, innerWidth - t.offsetWidth - 8)}px`; t.style.top = `${e.clientY + 16}px`;
  });
  area.addEventListener("pointerleave", () => { cross.setAttribute("visibility", "hidden"); dots.forEach((d) => d.setAttribute("visibility", "hidden")); $("tip").hidden = true; });
  return el("div", {}, legend(series.map((s) => [s.t, s.c])), g);
}
function bars(rows, total) { const m = Math.max(1, ...rows.map((r) => r.total)); return el("div", { class: "hb" }, ...rows.flatMap((r) => [el("span", { text: r.name }), hint(el("div", { class: "bar" }, ...r.segs.filter((s) => s.n).map((s) => el("i", { style: `width:${100 * s.n / m}%;background:${s.c}` }))), `${r.name}: ${r.segs.filter((s) => s.n).map((s) => `${s.n} ${s.t}`).join(", ")}${total ? `\n${pct(r.total, total)} of all` : ""}`), el("span", { class: "num", text: r.total })])); }
function lineChart(rows, key, title, unit, scale = 1, d = 1, width = 560) {
  const pts = rows.map((r, i) => [i, r[key] == null ? null : r[key] * scale, r.ts]).filter((p) => p[1] != null), box = el("section", { class: "card" }, el("h2", {}, title, el("span", { class: "sub", text: pts.length ? `now ${fmt(pts.at(-1)[1], d)} ${unit}` : "" })));
  if (pts.length < 2) { box.append(none("Not enough readings yet.")); return box; }
  const W = Math.max(320, Math.round(width)), H = 170, l = 40, max = Math.max(...pts.map((p) => p[1])) * 1.1 || 1, X = (i) => l + (W - l - 6) * i / (rows.length - 1), Y = (v) => H - 18 - (H - 26) * v / max;
  const g = SVG("svg", { viewBox: `0 0 ${W} ${H}`, class: "chart", role: "img", "aria-label": title });
  for (const f of [0, 0.5, 1]) { const v = max * f; g.append(SVG("line", { x1: l, x2: W, y1: Y(v), y2: Y(v), class: "gl", "stroke-dasharray": f ? "2 4" : "" }), SVG("text", { x: l - 8, y: Y(v) + 4, "text-anchor": "end", text: fmt(v, max < 10 ? 1 : 0) })); }
  g.append(SVG("polyline", { points: pts.map((p) => `${X(p[0])},${Y(p[1])}`).join(" "), fill: "none", stroke: "var(--series)", "stroke-width": 2, "stroke-linejoin": "round" }));
  const dot = SVG("circle", { r: 5, fill: "var(--series)", stroke: "var(--card)", "stroke-width": 2, visibility: "hidden" }), area = SVG("rect", { x: l, y: 0, width: W - l, height: H, fill: "transparent" }); g.append(dot, area);
  area.addEventListener("pointermove", (e) => { const q = g.getBoundingClientRect(), i = ((e.clientX - q.left) / q.width * W - l) / (W - l - 6) * (rows.length - 1), p = pts.reduce((a, b) => Math.abs(b[0] - i) < Math.abs(a[0] - i) ? b : a); dot.setAttribute("cx", X(p[0])); dot.setAttribute("cy", Y(p[1])); dot.setAttribute("visibility", "visible"); const t = $("tip"); t.textContent = `${p[2].slice(11, 19)}\n${fmt(p[1], d)} ${unit}`; t.hidden = false; t.style.left = `${Math.min(e.clientX + 14, innerWidth - 120)}px`; t.style.top = `${e.clientY + 16}px`; });
  area.addEventListener("pointerleave", () => { dot.setAttribute("visibility", "hidden"); $("tip").hidden = true; });
  box.append(g); return box;
}
const statCard = (lbl, value, unit, cls) => el("div", { class: `card ${cls || ""}` }, el("span", { class: "lbl", text: lbl }), big(value, unit));

/* ---- analytics ---- */
async function loadAnalytics() {
  const F = $("a-filters"), p = new URLSearchParams(); for (const k of ["profile", "session"]) if (F[k].value) p.set(k, F[k].value);
  let a; try { a = await api(`/api/analytics?${p}`); } catch (e) { say(e.message); return; }
  const R = a.results, L_ = a.labels, A = a.advice, O = L_.outcomes, n = a.units;
  $("a-scope").textContent = `${F.profile.value ? cap(F.profile.value) : "All lines"} · ${F.session.value ? (F.session.value === S?.session ? "this session" : `session ${F.session.value}`) : "all sessions"} · ${plural(n, "unit").replace(String(n), n.toLocaleString("en"))}`;
  const pp = n ? 100 * passed(R) / n : null;
  $("a-kpis").replaceChildren(statCard("Units inspected", n.toLocaleString("en")), statCard("Passed", pp == null ? "-" : fmt(pp, 1), "%"), statCard("Failed", (R.FAIL || 0).toLocaleString("en")), statCard("Sent for review", (R.REVIEW || 0).toLocaleString("en")),
    statCard("Vision per frame", fmt(a.latency.vision_mean), "ms"), statCard("Vision, slowest 5%", fmt(a.latency.vision_p95), "ms"), statCard("To be decided", a.open.toLocaleString("en"), null, a.open ? "alertish" : ""));
  $("a-trend").replaceChildren(trendChart(a.trend, $("a-trend").clientWidth));
  const total = Object.values(a.defects).reduce((s, d) => s + d.total, 0), sev = [["high", "var(--fail)"], ["medium", "var(--review)"], ["low", "var(--note)"]];
  $("a-defects").replaceChildren(total ? el("div", {}, legend(sev.map(([k, c]) => [`${cap(k)} severity`, c])), bars(Object.entries(a.defects).sort((x, y) => y[1].total - x[1].total).slice(0, 10).map(([k, d]) => ({ name: cap(k), total: d.total, segs: sev.map(([s, c]) => ({ n: d[s], c, t: s })) })), total)) : none("No defects recorded."));
  $("a-labels").replaceChildren(L_.n ? el("div", {},
    el("div", { class: "agree" }, big(fmt(100 * (O.ok || 0) / L_.n, 1), "%"), el("span", { text: `of ${L_.n.toLocaleString("en")} labelled units agree` })),
    el("div", { class: "dual" },
      el("div", {}, gauge([{ n: O.escape || 0, c: "var(--fail)", t: "Missed" }, { n: Math.max(0, L_.defective - (O.escape || 0)), c: "var(--pass)", t: "Stopped" }], pct(O.escape || 0, L_.defective, 1), `missed, of ${L_.defective}`), el("span", { class: "lbl", text: "Defective units missed" })),
      el("div", {}, gauge([{ n: O.false_reject || 0, c: "var(--review)", t: "Rejected" }, { n: Math.max(0, L_.acceptable - (O.false_reject || 0)), c: "var(--pass)", t: "Passed" }], pct(O.false_reject || 0, L_.acceptable, 1), `rejected, of ${L_.acceptable}`), el("span", { class: "lbl", text: "Good units rejected" })))) : none("These units have no dataset labels. The live tray has none; the dataset lines do."));
  const zs = Object.keys(a.zones).filter((z) => /^[A-Z]\d$/.test(z)), zm = Math.max(1, ...Object.values(a.zones)), rows = Math.max(3, ...zs.map((z) => z.charCodeAt(0) - 64)), cols = Math.max(3, ...zs.map((z) => +z[1]));
  $("a-zones").replaceChildren(zs.length ? el("div", { class: "zones", style: `grid-template-columns:repeat(${cols},1fr)` }, ...Array.from({ length: rows * cols }, (_, i) => { const z = String.fromCharCode(65 + Math.floor(i / cols)) + (i % cols + 1), v = a.zones[z] || 0, f = v / zm, m = Math.round(6 + 80 * f); return hint(el("div", { class: m > 50 ? "hot" : "", style: `background:color-mix(in srgb, var(--fail) ${m}%, var(--card-2))` }, el("b", { text: v }), z), `Zone ${z}: ${v} defects`); })) : none("No defects recorded."));
  $("a-advice").replaceChildren(A.n + A.template ? el("dl", { class: "kv" }, ...[["Units with advice", A.n + A.template], ["Written by Llama", A.n ? `${A.n - A.fallback} of ${A.n} (${pct(A.n - A.fallback, A.n)})` : "none"], ["Repaired by the validator", A.repaired], ["Rejected, template used", A.fallback], ["Time per answer", `${fmt(A.total_mean_ms / 1000)} s`], ["First word after", `${fmt(A.ttft_mean_ms / 1000)} s`], ["Speed", `${fmt(A.tok_s_mean)} tokens/s`]].flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])) : none("No advice yet."));
  const d = Object.entries(a.decisions); $("a-decisions").replaceChildren(d.length ? bars(d.map(([k, v]) => ({ name: DNAME[k], total: v, segs: [{ n: v, c: "var(--ink-2)", t: "units" }] }))) : none("No decisions yet. Open a stopped unit in the log to record one."));
}
$("a-filters").addEventListener("input", loadAnalytics);
$("summary-btn").onclick = async () => {
  const b = $("summary"); b.hidden = false; $("summary-btn").disabled = true; b.replaceChildren(el("div", { class: "adv-note", text: "Llama is reading the log of this line. This can take half a minute ..." }));
  try { const s = await api("/api/shift_summary", {}); b.replaceChildren(el("div", { class: "adv-head" }, el("h2", { text: "Shift summary" }), el("span", { class: "sub", text: `last ${s.stats.units} units of this line` })), el("p", { class: "adv-sum", text: s.trend }), el("div", { class: "adv-cols" }, el("div", {}, el("h3", { text: "Likely process issue" }), el("div", { text: s.likely_process_issue })), el("div", { style: "grid-column:span 2" }, el("h3", { text: "What to do" }), el("ul", {}, ...(s.actions || []).map((x) => el("li", { text: x }))))), el("div", { class: "adv-meta", text: s.backend === "executorch" ? "Llama 3.2 1B on the Arm CPU" : "Procedure template" })); } catch (e) { b.replaceChildren(el("div", { text: e.message })); }
  $("summary-btn").disabled = false;
};

/* ---- system ---- */
async function loadSystem() {
  const rows = await api("/api/metrics?limit=240").catch(() => []), t = S?.telemetry || {};
  $("s-kpis").replaceChildren(statCard("Board power", t.power_mw ? fmt(t.power_mw / 1000) : "-", "W"), statCard("Temperature", t.temp_c ? fmt(t.temp_c, 0) : "-", "°C"), statCard("GPU load", t.gpu_pct == null ? "-" : fmt(t.gpu_pct, 0), "%"), statCard("CPU load", fmt(t.cpu_pct, 0), "%"),
    statCard("Memory in use", fmt(t.ram_used_mb / 1024), `of ${fmt(t.ram_total_mb / 1024)} GB`), statCard("Vision and app", fmt(t.proc_rss_mb / 1024, 2), "GB"), statCard("Llama", t.llm_rss_mb ? fmt(t.llm_rss_mb / 1024, 2) : "-", "GB"));
  const cw = ($("s-charts").clientWidth - 14) / (innerWidth > 1180 ? 2 : 1) - 40;
  $("s-charts").replaceChildren(lineChart(rows, "power_mw", "Board power", "W", 0.001, 1, cw), lineChart(rows, "temp_c", "Temperature", "°C", 1, 1, cw), lineChart(rows, "gpu_pct", "GPU load", "%", 1, 0, cw), lineChart(rows, "ram_used_mb", "Memory in use", "GB", 1 / 1024, 2, cw));
  if (S) $("s-info").replaceChildren(el("dl", { class: "kv" }, ...[["Line", `${S.label} (${S.station || "-"})`], ["Vision, runtime A", S.vision_backend], ["Advice, runtime B", S.advisory_backend === "executorch" ? "Llama 3.2 1B Instruct, ExecuTorch + XNNPACK, Arm CPU" : S.advisory_backend], ["Advice queue", `${S.advice_pending} waiting, ${S.advice_dropped} skipped this session`], ["Session", S.session], ["Camera", S.camera ? `${S.camera.name}, ${S.camera.live ? "live" : S.camera.error || "connecting"}` : "not used by this line"]].flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])));
}

async function openCount() { if (!S) return; try { const j = await api(`/api/log?decision=open&limit=1&session=${S.session}`); $("open-count").hidden = !j.total; $("open-count").textContent = j.total > 999 ? "999+" : j.total; $("open-count").title = `${j.total} stopped units of this session still to be decided`; } catch { /* shown by tick */ } }
setInterval(tick, 500); setInterval(openCount, 5000);
setInterval(() => { if (page === "log" && $("log-auto").checked && L.offset === 0 && $("drawer").hidden) loadLog(); if (page === "system") loadSystem(); if (page === "analytics" && $("summary").hidden) loadAnalytics(); }, 4000);
tick().then(route); openCount();
