"use strict";
const $ = (id) => document.getElementById(id);
const el = (tag, props = {}, ...kids) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (v == null) continue;
    if (k === "class") e.className = v; else if (k === "text") e.textContent = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
  }
  e.append(...kids.filter((x) => x != null));
  return e;
};
const SVG = (tag, props = {}, ...kids) => {
  const e = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(props)) if (k === "text") e.textContent = v; else e.setAttribute(k, v);
  e.append(...kids); return e;
};
const fmt = (v, d = 1) => (v == null || Number.isNaN(Number(v))) ? "-" : Number(v).toFixed(d);
const pct = (a, b, d = 1) => b ? `${(100 * a / b).toFixed(d)}%` : "-";
const words = (s) => String(s ?? "").replace(/_/g, " ");
const RESULTS = ["FAIL", "REVIEW", "PASS_WITH_NOTE", "PASS"];
const ICON = { PASS: "✓", PASS_WITH_NOTE: "✓", REVIEW: "?", FAIL: "✕", ok: "✓", escape: "!", false_reject: "!" };
const RNAME = { PASS: "Pass", PASS_WITH_NOTE: "Pass with note", REVIEW: "Review", FAIL: "Fail" };
const ONAME = { ok: "Agrees with labels", escape: "Missed defect", false_reject: "False reject" };
const DNAME = { confirmed: "Confirmed", false_alarm: "False alarm", missed_defect: "Missed defect", rework: "Rework", scrap: "Scrap" };
const RCOL = { FAIL: "var(--s-bad)", REVIEW: "var(--s-warn)", PASS_WITH_NOTE: "var(--s-note)", PASS: "var(--s-good)" };
const tag = (key, text) => el("span", { class: `tag ${key}`, "data-i": ICON[key] }, text ?? words(key));
const kpi = (label, value, cls) => el("div", { class: `kpi ${cls || ""}` }, el("b", { text: value }), el("span", { text: label }));
const store = { get(k) { try { return localStorage.getItem(k) || ""; } catch { return ""; } }, set(k, v) { try { localStorage.setItem(k, v); } catch { /* private window */ } } };

async function api(url, body) {
  const r = await fetch(url, body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json", "X-QC": "1" }, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error || `request failed (${r.status})`);
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
  for (const b of document.querySelectorAll("nav button")) b.setAttribute("aria-selected", b.dataset.page === name);
  for (const m of document.querySelectorAll("main.page")) m.hidden = m.id !== `page-${name}`;
  $("view").src = name === "inspect" ? "/stream.mjpg" : "";   // one open stream at a time
  if (name === "log") { loadFacets(); loadLog(); } else if (name === "analytics") { loadFacets().then(loadAnalytics); } else if (name === "system") loadSystem();
}
for (const b of document.querySelectorAll("nav button")) b.onclick = () => { location.hash = b.dataset.page; };
addEventListener("hashchange", () => route());
function route() {
  const [p, uid] = location.hash.slice(1).split("/");
  if (uid) { if (!page) show("log"); openUnit(uid); return; }
  closeUnit(false); if (p !== page) show(p || "inspect");
}

/* ---- inspect ---- */
const PACE = [0.1, 0.2, 0.5, 1, 2, 4, 10];
let S = null, stripKey = "", advKey = "", findKey = "";
function findingsList(dets) {
  if (!dets.length) return el("div", { class: "muted", text: "No defects found." });
  const groups = new Map();
  for (const d of dets) {
    const k = [d.part, d.defect, d.severity, d.needs_review].join("|");
    const g = groups.get(k) || { ...d, n: 0, zones: new Set(), best: 0 };
    g.n++; g.zones.add(d.zone); g.best = Math.max(g.best, d.confidence); g.size = Math.max(g.size, d.size); groups.set(k, g);
  }
  const rank = { high: 0, medium: 1, low: 2 };
  return el("div", {}, ...[...groups.values()].sort((a, b) => rank[a.severity] - rank[b.severity]).map((g) => el("div", { class: "finding" },
    el("b", { text: `${words(g.defect)}${g.n > 1 ? ` × ${g.n}` : ""}${g.part ? ` on ${g.part}` : ""}` }), tag(g.severity),
    el("small", { text: [g.size_unit === "part_frac" ? `${fmt(100 * g.size, 0)}% of the surface` : `confidence ${fmt(g.best, 2)}`, `zone ${[...g.zones].sort().join(", ")}`,
      g.size_unit === "mm2" ? `largest ${fmt(g.size, 2)} mm²` : "", g.needs_review ? "needs a person" : ""].filter(Boolean).join(" · ") }))));
}
function adviceBox(a) {
  const x = a.advice || {}, box = el("div", { class: "adv" });
  if (x.summary) box.append(el("p", { text: x.summary }));
  for (const [t, v] of [["Likely causes", x.likely_causes], ["What to do", x.recommended_actions], ["Then verify", x.verify]]) {
    if (!v) continue;
    box.append(el("h3", { text: t }), Array.isArray(v) ? el("ul", {}, ...v.map((i) => el("li", { text: i }))) : el("div", { text: v }));
  }
  const src = a.fallback ? "Procedure template (Llama's answer was rejected)" : a.backend === "executorch" ? `Llama 3.2 1B on the Arm CPU${a.repaired ? ", repaired by the validator" : ""}` : "Procedure template";
  box.append(el("div", { class: "meta", text: src + (a.total_ms && a.backend === "executorch" ? ` · ${fmt(a.total_ms / 1000)} s · first word ${fmt(a.ttft_ms / 1000)} s · ${fmt(a.tok_s)} tokens/s` : "") }));
  return box;
}
function drawInspect(s) {
  const c = s.counts, n = RESULTS.reduce((t, r) => t + (c[r] || 0), 0), t = s.telemetry || {}, g = s.gt_counts || {}, gn = (g.ok || 0) + (g.escape || 0) + (g.false_reject || 0);
  const r = s.record, pass = (c.PASS || 0) + (c.PASS_WITH_NOTE || 0);
  $("kpis").replaceChildren(kpi(s.trigger ? "Trays inspected" : "Units inspected", n), kpi("Passed", pct(pass, n), n ? "good" : ""), kpi("Review", c.REVIEW || 0, c.REVIEW ? "warn" : ""), kpi("Failed", c.FAIL || 0, c.FAIL ? "bad" : ""),
    ...(gn ? [kpi("Verdicts matching labels", pct(g.ok || 0, gn)), kpi("Missed defects", g.escape || 0, g.escape ? "bad" : "good"), kpi("False rejects", g.false_reject || 0, g.false_reject ? "warn" : "")] : []),
    kpi("Vision per frame", `${fmt(s.trigger ? s.live?.vision_ms : r?.timings_ms?.vision, 0)} ms`), kpi("Board power", t.power_mw ? `${fmt(t.power_mw / 1000)} W` : "-"), kpi("Waiting for advice", s.advice_pending));
  const cam = s.camera, v = $("view-msg"); let msg = "";
  if (s.switching) msg = `Switching to ${words(s.switching)} ...`; else if (cam && !cam.live) msg = `No camera signal. ${cam.error || "Connecting ..."}`; else if (!s.inspect) msg = ""; else if (!r && !s.live) msg = "Loading the model ...";
  v.hidden = !msg; v.textContent = msg;
  $("play").textContent = s.paused ? "Resume" : "Pause"; $("play").disabled = !s.inspect; $("step").hidden = s.trigger || !s.inspect; $("pace-wrap").hidden = s.trigger || !s.inspect; $("inspect-now").hidden = !s.trigger;
  if (document.activeElement !== $("pace")) { const i = PACE.reduce((b, p, k) => Math.abs(p - s.fps_limit) < Math.abs(PACE[b] - s.fps_limit) ? k : b, 0); $("pace").value = i; $("pace-val").textContent = paceText(s.fps_limit); }
  $("view-info").textContent = s.trigger ? `${fmt(s.fps, 0)} FPS · ${s.paused ? "automatic logging paused" : "logs a tray when parts lie still"}` : `${s.label} · ${s.vision_backend}`;
  const vd = $("verdict"); vd.className = `panel verdict ${r ? r.inspection_result : ""}`;
  $("v-word").textContent = r ? `${ICON[r.inspection_result]} ${RNAME[r.inspection_result]}` : s.inspect ? "Waiting" : "Camera only";
  $("v-why").textContent = r ? r.rule_trace[r.rule_trace.length - 1].replace(/^(FAIL|REVIEW|PASS)( with note| \(rework\))?: /i, "") : s.trigger ? "Place parts on the tray and keep them still." : "";
  $("v-unit").textContent = r ? `${r.unit_id} · ${r.timestamp.slice(11, 19)}` : "";
  const gt = r && r.gt_result ? (["PASS", "PASS_WITH_NOTE"].includes(r.gt_result) === ["PASS", "PASS_WITH_NOTE"].includes(r.inspection_result) ? "ok" : ["PASS", "PASS_WITH_NOTE"].includes(r.gt_result) ? "false_reject" : "escape") : null;
  $("v-label").replaceChildren(...(gt ? [tag(gt, ONAME[gt])] : []));
  const parts = s.trigger && s.live ? s.live.parts : {}; $("parts-panel").hidden = !s.trigger;
  $("parts").replaceChildren(...["nut", "bolt", "washer"].map((k) => el("div", {}, el("b", { text: parts[k] || 0 }), el("span", { text: (parts[k] || 0) === 1 ? k : `${k}s` }))));
  const fk = r ? r.unit_id : ""; if (fk !== findKey) { findKey = fk; $("findings").replaceChildren(r ? findingsList(r.detections) : el("div", { class: "muted", text: "Nothing inspected yet." })); }
  const adv = s.advice_current || s.advice_latest, stopped = r && r.detections.length && r.inspection_result !== "PASS";
  const ak = [adv?.unit_id, s.advice_writing, stopped && !s.advice_current, s.advisory_backend].join();
  if (ak !== advKey) {
    advKey = ak;
    $("adv-unit").textContent = adv ? (s.advice_current ? "for this unit" : `for an earlier unit, ${adv.unit_id}`) : "";
    const note = s.advisory_backend === "disabled" ? "Advice is off." : s.advice_writing ? `Writing about ${s.advice_writing} ...` : "";
    $("advice").replaceChildren(...(note ? [el("div", { class: "muted", text: note, style: adv ? "margin-bottom:9px" : "" })] : []), adv ? adviceBox(adv) : note ? "" : el("div", { class: "muted", text: "No advice yet. It is written for units that fail, need review or pass with a note." }));
  }
  const sk = s.session + s.recent.map((x) => x.unit_id).join();
  if (sk !== stripKey) {
    stripKey = sk;
    $("strip").replaceChildren(...(s.recent.length ? [...s.recent].reverse().map((u) => el("button", { class: `thumb ${u.result}`, title: `${u.unit_id}: ${RNAME[u.result]}`, onclick: () => { location.hash = `inspect/${u.unit_id}`; } },
      el("img", { src: `/api/unit/${u.unit_id}/image.jpg?w=200`, alt: "", loading: "lazy" }), `${ICON[u.result]} ${u.unit_id.slice(-5)}${u.gt_outcome && u.gt_outcome !== "ok" ? " !" : ""}`)) : [el("span", { class: "muted", text: "Inspected units appear here." })]));
  }
}
const paceText = (v) => v >= 1 ? `${fmt(v, v % 1 ? 1 : 0)} per second` : `one per ${fmt(1 / v, 0)} s`;
$("play").onclick = () => act(api("/api/control", { action: S?.paused ? "play" : "pause" }).then(tick));
$("step").onclick = () => act(api("/api/control", { action: "step" }).then(() => setTimeout(tick, 250)));
$("inspect-now").onclick = () => act(api("/api/control", { action: "inspect_now" }));
$("pace").oninput = () => { $("pace-val").textContent = paceText(PACE[$("pace").value]); };
$("pace").onchange = () => act(api("/api/control", { action: "pace", value: PACE[$("pace").value] }).then(() => $("pace").blur()));
$("line").onchange = () => act(api("/api/line", { name: $("line").value }).then(() => { stripKey = findKey = advKey = ""; tick(); }).catch((e) => { loadLines(); throw e; }));
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
  if (s.profile !== lastProfile) { lastProfile = s.profile; loadLines().catch(() => {}); }
  const net = s.network, on = !!net.default_route && !/^(l4tbr0|usb)/.test(net.default_route);
  $("net-pill").textContent = on ? "Network connected" : "Offline"; $("net-pill").className = `pill ${on ? "" : "ok"}`; $("net-pill").title = on ? `Default route via ${net.default_route}. Inspection does not use it.` : "No route to the internet. Everything runs on the board.";
  const ex = s.advisory_backend === "executorch"; $("llm-pill").textContent = ex ? (s.telemetry?.llm_rss_mb ? (s.advice_writing ? "Llama writing" : "Llama ready") : "Llama starting") : s.advisory_backend === "template" ? "Template advice" : "Advice off"; $("llm-pill").className = `pill ${ex && s.telemetry?.llm_rss_mb ? "ok" : ""}`;
  if (page === "inspect") drawInspect(s);
}

/* ---- log ---- */
const L = { offset: 0, limit: 50, results: new Set(), key: "" };
$("f-results").append(...RESULTS.map((r) => el("button", { type: "button", "aria-pressed": "false", text: RNAME[r], onclick: (e) => { const on = !L.results.has(r); on ? L.results.add(r) : L.results.delete(r); e.target.setAttribute("aria-pressed", on); L.offset = 0; loadLog(); } })));
function fill(sel, items, name = (x) => x, any = "any") { const v = sel.value; sel.replaceChildren(el("option", { value: "", text: any }), ...items.map((x) => el("option", { value: x, text: name(x) }))); if (items.includes(v)) sel.value = v; }
async function loadFacets() {
  const f = await api("/api/facets").catch(() => null); if (!f) return;
  const F = $("filters"), A = $("a-filters");
  for (const q of [F, A]) { fill(q.profile, f.profiles, words, "all lines"); fill(q.session, f.sessions, (x) => x === S?.session ? `${x} (now)` : x, "all sessions"); }
  if (!A.dataset.init && S) { A.dataset.init = 1; A.profile.value = S.profile; A.session.value = S.session; }  // analytics opens on what is running now
  fill(F.defect, f.defects, words); fill(F.decision, ["open", ...f.decisions], (x) => x === "open" ? "to be decided" : DNAME[x]);
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
  $("log-total").textContent = `${j.total} unit${j.total === 1 ? "" : "s"}`;
  $("log-mix").replaceChildren(...RESULTS.filter((r) => j.by_result[r]).map((r) => el("span", { style: "margin-right:8px" }, tag(r, `${j.by_result[r]} ${RNAME[r].toLowerCase()}`))));
  $("log-rows").replaceChildren(...(j.rows.length ? j.rows.map((r) => {
    const go = () => { location.hash = `log/${r.unit_id}`; }, n = {}; for (const d of (r.defects || "").split(" ").filter(Boolean)) { const k = d.split(":")[0]; n[k] = (n[k] || 0) + 1; }
    return el("tr", { tabindex: "0", onclick: go, onkeydown: (e) => { if (e.key === "Enter") go(); } },
      el("td", {}, el("img", { src: `/api/unit/${r.unit_id}/image.jpg?w=200`, alt: "", loading: "lazy" })),
      el("td", {}, el("b", { text: r.unit_id }), el("small", { text: `${(r.ts || "").slice(0, 10)} ${(r.ts || "").slice(11, 19)}` })), el("td", { text: words(r.profile) }), el("td", {}, tag(r.result, RNAME[r.result])),
      el("td", { text: Object.entries(n).map(([k, v]) => words(k) + (v > 1 ? ` × ${v}` : "")).join(", ") || "none" }), el("td", {}, r.gt_outcome ? tag(r.gt_outcome, ONAME[r.gt_outcome]) : el("span", { class: "muted", text: "-" })),
      el("td", {}, el("div", { class: "clip", text: r.advice_summary || "-" })), el("td", {}, r.decision ? el("span", { class: "tag", text: DNAME[r.decision] }) : ["FAIL", "REVIEW"].includes(r.result) ? el("span", { class: "muted", text: "to be decided" }) : ""), el("td", { class: "num", text: `${fmt(r.vision_ms, 0)} ms` }));
  }) : [el("tr", {}, el("td", { colspan: "9", class: "empty", text: "No units match these filters." }))]));
  $("p-new").disabled = L.offset === 0; $("p-old").disabled = L.offset + L.limit >= j.total;
  $("p-pos").textContent = j.total ? `${L.offset + 1} to ${Math.min(L.offset + L.limit, j.total)} of ${j.total}` : "";
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
  const r = u.record, D = $("drawer"), base = `/api/unit/${u.unit_id}/image.jpg`; let boxes = true;
  const img = el("img", { src: base, alt: `inspected image of ${u.unit_id}`, onerror: (e) => { e.target.parentNode.replaceChildren(el("div", { class: "empty", text: "The image of this unit was not kept." })); } });
  const nav = (id, t) => { const b = el("button", { class: "btn", text: t, onclick: () => { location.hash = `${page}/${id}`; } }); b.disabled = !id; return b; };
  const op = el("input", { type: "text", placeholder: "your name or initials", "aria-label": "operator", value: store.get("qc-operator"), maxlength: "60" }), note = el("input", { type: "text", placeholder: "note (optional)", "aria-label": "note", maxlength: "500" });
  const choose = (d) => act(api(`/api/unit/${u.unit_id}/decision`, { decision: d, operator: op.value, note: note.value }).then(() => { store.set("qc-operator", op.value); L.key = ""; openUnit(u.unit_id); if (page === "log") loadLog(); }));
  const choices = ["FAIL", "REVIEW"].includes(u.result) ? ["confirmed", "false_alarm", "rework", "scrap"] : ["confirmed", "missed_defect"];
  const t = r.timings_ms || {}, a = u.advice;
  D.replaceChildren(
    el("div", { class: "d-head" }, el("h1", { id: "d-title", text: u.unit_id }), tag(u.result, RNAME[u.result]), u.gt_outcome ? tag(u.gt_outcome, ONAME[u.gt_outcome]) : null, el("span", { class: "grow" }), nav(u.newer, "Newer"), nav(u.older, "Older"), el("button", { class: "btn", id: "d-close", text: "Close", onclick: () => closeUnit(true) })),
    el("div", { class: "d-img" }, img),
    el("label", { class: "muted" }, (() => { const c = el("input", { type: "checkbox", onchange: (e) => { boxes = e.target.checked; img.src = `${base}?boxes=${boxes ? 1 : 0}`; } }); c.checked = true; return c; })(), " show findings on the image"),
    el("div", { class: "decide" }, el("h2", { text: "Operator decision" }), el("div", { class: "row" }, op, note), el("div", { class: "row" }, ...choices.map((d) => el("button", { class: "btn", text: DNAME[d], onclick: () => choose(d) }))),
      u.decisions.length ? el("ul", { class: "hist" }, ...u.decisions.map((x) => el("li", { text: `${DNAME[x.decision]}${x.operator ? ` by ${x.operator}` : ""}, ${x.ts.slice(0, 16).replace("T", " ")}${x.note ? `: ${x.note}` : ""}` }))) : null),
    el("div", { class: "d-cols" },
      el("div", {}, el("h2", { text: "Findings" }), findingsList(r.detections || []), el("h2", { text: "How the rules decided", style: "margin-top:18px" }), el("ul", { class: "trace" }, ...(r.rule_trace || []).map((x) => el("li", { text: x })))),
      el("div", {}, el("h2", { text: "Advice" }), a ? adviceBox(a) : el("div", { class: "muted", text: "No advice was written for this unit." }), a && a.errors.length ? el("ul", { class: "trace muted" }, ...a.errors.map((x) => el("li", { text: x }))) : null)),
    el("h2", { text: "Record", style: "margin-top:20px" }),
    el("dl", { class: "kv" }, ...[["Line", words(u.profile)], ["Time", u.ts], ["Session", u.session], ["Source", u.image_ref], ["Labelled verdict", r.gt_result ? `${RNAME[r.gt_result]}${r.gt_defects?.length ? ` (${[...new Set(r.gt_defects)].map(words).join(", ")})` : ""}` : null], ["Parts", r.parts?.length ? Object.entries(r.parts.reduce((m, p) => ({ ...m, [p.type]: (m[p.type] || 0) + 1 }), {})).map(([k, v]) => `${v} ${k}`).join(", ") : null],
      ["Vision", `${fmt(t.vision)} ms (pre ${fmt(t.pre)}, inference ${fmt(t.infer)}, post ${fmt(t.post)}${t.anomaly ? `, anomaly ${fmt(t.anomaly)}` : ""}${t.checks ? `, part checks ${fmt(t.checks)}` : ""})`], ["Frame to verdict", `${fmt(t.e2e)} ms`]].filter(([, v]) => v).flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])));
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
function hint(node, text) { node.addEventListener("pointermove", (e) => { const t = $("tip"); t.textContent = text; t.hidden = false; t.style.left = `${Math.min(e.clientX + 14, innerWidth - t.offsetWidth - 8)}px`; t.style.top = `${e.clientY + 14}px`; }); node.addEventListener("pointerleave", () => { $("tip").hidden = true; }); return node; }
const legend = (items) => el("div", { class: "legend" }, ...items.map(([n, c]) => el("span", {}, el("i", { style: `background:${c}` }), n)));
const none = (t) => el("div", { class: "empty", text: t });
function trendChart(trend) {
  if (!trend.length) return none("No units yet.");
  const W = 620, H = 190, l = 34, b = 22, max = Math.max(...trend.map((x) => x.n)), w = (W - l) / trend.length, g = SVG("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "results over time, oldest first" });
  for (const f of [0, 0.5, 1]) { const y = (H - b) * (1 - f) + 6 * f; g.append(SVG("line", { x1: l, x2: W, y1: y, y2: y, class: "gl" }), SVG("text", { x: l - 6, y: y + 4, "text-anchor": "end", text: Math.round(max * f) })); }
  trend.forEach((t, i) => { let y = H - b; const bw = Math.min(26, w - 3), grp = SVG("g"); for (const r of ["PASS", "PASS_WITH_NOTE", "REVIEW", "FAIL"]) { const h = (H - b - 6) * t[r] / max; if (h <= 0) continue; grp.append(SVG("rect", { x: l + i * w + (w - bw) / 2, y: y - h, width: bw, height: Math.max(1, h - 2), fill: RCOL[r] })); y -= h; } grp.append(SVG("rect", { x: l + i * w, y: 0, width: w, height: H - b, fill: "transparent" })); g.append(hint(grp, `${t.from.slice(5, 16).replace("T", " ")} to ${t.to.slice(11, 16)}\n${t.n} units: ${RESULTS.filter((r) => t[r]).map((r) => `${t[r]} ${RNAME[r].toLowerCase()}`).join(", ")}`)); });
  g.append(SVG("text", { x: l, y: H - 4, text: trend[0].from.slice(5, 16).replace("T", " ") }), SVG("text", { x: W, y: H - 4, "text-anchor": "end", text: trend.at(-1).to.slice(5, 16).replace("T", " ") }));
  return el("div", {}, legend(RESULTS.map((r) => [RNAME[r], RCOL[r]])), g);
}
function bars(rows, total) { const m = Math.max(1, ...rows.map((r) => r.total)); return el("div", { class: "hb" }, ...rows.flatMap((r) => [el("span", { text: r.name }), hint(el("div", { class: "bar" }, ...r.segs.filter((s) => s.n).map((s) => el("i", { style: `width:${100 * s.n / m}%;background:${s.c}` }))), `${r.name}: ${r.segs.filter((s) => s.n).map((s) => `${s.n} ${s.t}`).join(", ")}${total ? `\n${pct(r.total, total)} of all` : ""}`), el("span", { class: "num", text: r.total })])); }
function lineChart(rows, key, title, unit, scale = 1, d = 1) {
  const pts = rows.map((r, i) => [i, r[key] == null ? null : r[key] * scale, r.ts]).filter((p) => p[1] != null), box = el("section", { class: "panel" }, el("h2", {}, title, " ", el("span", { class: "muted", text: pts.length ? `now ${fmt(pts.at(-1)[1], d)} ${unit}` : "" })));
  if (pts.length < 2) { box.append(none("Not enough readings yet.")); return box; }
  const W = 560, H = 130, l = 38, max = Math.max(...pts.map((p) => p[1])) * 1.1 || 1, X = (i) => l + (W - l - 6) * i / (rows.length - 1), Y = (v) => H - 18 - (H - 26) * v / max;
  const g = SVG("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title }); for (const f of [0, 0.5, 1]) { const v = max * f; g.append(SVG("line", { x1: l, x2: W, y1: Y(v), y2: Y(v), class: "gl" }), SVG("text", { x: l - 6, y: Y(v) + 4, "text-anchor": "end", text: fmt(v, max < 10 ? 1 : 0) })); }
  g.append(SVG("polyline", { points: pts.map((p) => `${X(p[0])},${Y(p[1])}`).join(" "), fill: "none", stroke: "var(--series)", "stroke-width": 2 }));
  const dot = SVG("circle", { r: 4, fill: "var(--series)", stroke: "var(--panel)", "stroke-width": 2, visibility: "hidden" }), area = SVG("rect", { x: l, y: 0, width: W - l, height: H, fill: "transparent" }); g.append(dot, area);
  area.addEventListener("pointermove", (e) => { const q = g.getBoundingClientRect(), i = ((e.clientX - q.left) / q.width * W - l) / (W - l - 6) * (rows.length - 1), p = pts.reduce((a, b) => Math.abs(b[0] - i) < Math.abs(a[0] - i) ? b : a); dot.setAttribute("cx", X(p[0])); dot.setAttribute("cy", Y(p[1])); dot.setAttribute("visibility", "visible"); const t = $("tip"); t.textContent = `${p[2].slice(11, 19)}\n${fmt(p[1], d)} ${unit}`; t.hidden = false; t.style.left = `${Math.min(e.clientX + 14, innerWidth - 120)}px`; t.style.top = `${e.clientY + 14}px`; });
  area.addEventListener("pointerleave", () => { dot.setAttribute("visibility", "hidden"); $("tip").hidden = true; });
  box.append(g); return box;
}

/* ---- analytics ---- */
async function loadAnalytics() {
  const F = $("a-filters"), p = new URLSearchParams(); for (const k of ["profile", "session"]) if (F[k].value) p.set(k, F[k].value);
  let a; try { a = await api(`/api/analytics?${p}`); } catch (e) { say(e.message); return; }
  const R = a.results, L_ = a.labels, A = a.advice, O = L_.outcomes;
  $("a-kpis").replaceChildren(kpi("Units", a.units), kpi("Passed", pct((R.PASS || 0) + (R.PASS_WITH_NOTE || 0), a.units)), kpi("Failed", R.FAIL || 0), kpi("Review", R.REVIEW || 0), kpi("Vision mean", `${fmt(a.latency.vision_mean)} ms`), kpi("Vision p95", `${fmt(a.latency.vision_p95)} ms`), kpi("To be decided", a.open, a.open ? "warn" : ""));
  $("a-trend").replaceChildren(trendChart(a.trend));
  const total = Object.values(a.defects).reduce((s, d) => s + d.total, 0), sev = [["high", "var(--s-bad)"], ["medium", "var(--s-warn)"], ["low", "var(--s-good)"]];
  $("a-defects").replaceChildren(total ? el("div", {}, legend(sev.map(([n, c]) => [`${n} severity`, c])), bars(Object.entries(a.defects).sort((x, y) => y[1].total - x[1].total).slice(0, 12).map(([k, d]) => ({ name: words(k), total: d.total, segs: sev.map(([n, c]) => ({ n: d[n], c, t: n })) })), total)) : none("No defects recorded."));
  $("a-labels").replaceChildren(L_.n ? el("dl", { class: "kv" }, ...[["Labelled units", L_.n], ["Verdict agrees", `${O.ok || 0} (${pct(O.ok || 0, L_.n)})`], ["Defective units missed", `${O.escape || 0} of ${L_.defective} (${pct(O.escape || 0, L_.defective)})`], ["Good units rejected", `${O.false_reject || 0} of ${L_.acceptable} (${pct(O.false_reject || 0, L_.acceptable)})`]].flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])) : none("These units have no dataset labels."));
  const zs = Object.keys(a.zones).filter((z) => /^[A-Z]\d$/.test(z)), zm = Math.max(1, ...Object.values(a.zones)), rows = Math.max(3, ...zs.map((z) => z.charCodeAt(0) - 64)), cols = Math.max(3, ...zs.map((z) => +z[1]));
  $("a-zones").replaceChildren(zs.length ? el("div", { class: "zones", style: `grid-template-columns:repeat(${cols},1fr)` }, ...Array.from({ length: rows * cols }, (_, i) => { const z = String.fromCharCode(65 + Math.floor(i / cols)) + (i % cols + 1), n = a.zones[z] || 0, f = n / zm; return el("div", { style: `background:color-mix(in srgb, var(--series) ${Math.round(8 + 62 * f)}%, var(--panel))` }, el("b", { text: n }), z); })) : none("No defects recorded."));
  $("a-advice").replaceChildren(A.n + A.template ? el("dl", { class: "kv" }, ...[["Units with advice", A.n + A.template], ["Written by Llama", A.n ? `${A.n - A.fallback} of ${A.n} (${pct(A.n - A.fallback, A.n)})` : "none"], ["of which repaired by the validator", A.repaired], ["Rejected, template used", A.fallback], ["Time per answer", `${fmt(A.total_mean_ms / 1000)} s`], ["First word after", `${fmt(A.ttft_mean_ms / 1000)} s`], ["Speed", `${fmt(A.tok_s_mean)} tokens/s`]].flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])) : none("No advice yet."));
  const d = Object.entries(a.decisions); $("a-decisions").replaceChildren(d.length ? bars(d.map(([k, n]) => ({ name: DNAME[k], total: n, segs: [{ n, c: "var(--series)", t: "units" }] }))) : none("No decisions yet. Open a unit in the log to record one."));
}
$("a-filters").addEventListener("input", loadAnalytics);
$("summary-btn").onclick = async () => {
  const b = $("summary"); b.hidden = false; $("summary-btn").disabled = true; b.replaceChildren(el("div", { class: "muted", text: "Llama is reading the log of this line. This can take half a minute ..." }));
  try { const s = await api("/api/shift_summary", {}); b.replaceChildren(el("div", { class: "adv" }, el("p", { text: s.trend }), el("div", { text: s.likely_process_issue }), el("h3", { text: "What to do" }), el("ul", {}, ...(s.actions || []).map((x) => el("li", { text: x }))), el("div", { class: "meta", text: `${s.backend === "executorch" ? "Llama 3.2 1B on the Arm CPU" : "Procedure template"}, last ${s.stats.units} units of this line` }))); } catch (e) { b.replaceChildren(el("div", { text: e.message })); }
  $("summary-btn").disabled = false;
};

/* ---- system ---- */
async function loadSystem() {
  const rows = await api("/api/metrics?limit=240").catch(() => []), t = S?.telemetry || {};
  $("s-kpis").replaceChildren(kpi("Board power", t.power_mw ? `${fmt(t.power_mw / 1000)} W` : "-"), kpi("Temperature", t.temp_c ? `${fmt(t.temp_c, 0)} °C` : "-"), kpi("GPU load", t.gpu_pct == null ? "-" : `${fmt(t.gpu_pct, 0)}%`), kpi("CPU load", `${fmt(t.cpu_pct, 0)}%`), kpi("Memory", `${fmt(t.ram_used_mb / 1024)} of ${fmt(t.ram_total_mb / 1024)} GB`), kpi("Vision and app", `${fmt(t.proc_rss_mb / 1024, 2)} GB`), kpi("Llama", t.llm_rss_mb ? `${fmt(t.llm_rss_mb / 1024, 2)} GB` : "-"));
  $("s-charts").replaceChildren(lineChart(rows, "power_mw", "Board power", "W", 0.001), lineChart(rows, "temp_c", "Temperature", "°C"), lineChart(rows, "gpu_pct", "GPU load", "%", 1, 0), lineChart(rows, "ram_used_mb", "Memory in use", "GB", 1 / 1024, 2));
  if (S) $("s-info").replaceChildren(el("dl", { class: "kv" }, ...[["Line", `${S.label} (${S.station || "-"})`], ["Vision runtime A", S.vision_backend], ["Advisory runtime B", S.advisory_backend === "executorch" ? "Llama 3.2 1B Instruct, ExecuTorch + XNNPACK, Arm CPU" : S.advisory_backend], ["Advice queue", `${S.advice_pending} waiting, ${S.advice_dropped} skipped this session`], ["Session", S.session], ["Camera", S.camera ? `${S.camera.name}, ${S.camera.live ? "live" : S.camera.error || "connecting"}` : "not used by this line"], ["Network", S.network.default_route ? `default route via ${S.network.default_route}; Wi-Fi ${S.network.wifi || "-"}` : `no route to the internet; Wi-Fi ${S.network.wifi || "-"}`]].flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])));
}

async function openCount() { if (!S) return; try { const j = await api(`/api/log?decision=open&limit=1&session=${S.session}`); $("open-count").hidden = !j.total; $("open-count").textContent = j.total > 999 ? "999+" : j.total; $("open-count").title = `${j.total} stopped units of this session still to be decided`; } catch { /* shown by tick */ } }
setInterval(tick, 500); setInterval(openCount, 5000);
setInterval(() => { if (page === "log" && $("log-auto").checked && L.offset === 0 && $("drawer").hidden) loadLog(); if (page === "system") loadSystem(); if (page === "analytics" && $("summary").hidden) loadAnalytics(); }, 4000);
tick().then(route); openCount();
