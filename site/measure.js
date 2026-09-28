// The paper's evaluation on the page: eleven milestones per session, keypresses
// to the world map, the chain of steps a playthrough passes, and the two
// routes. Every number comes from a session's `measure` block, which the
// service reads from the frames of the game with the paper's own code.

const MS = ["map", "item", "location", "hermit", "compass", "party",
            "battle", "ended", "exp", "level", "book"];
const STEPS = ["leave_house", "enter_location", "reach_hermit", "enter_battle",
               "win_battle", "hold_book"];
const HOME = "王居";                         // 王居, the starting house
const PLACE = {"南賢居": "house of the hermit", "河洛客棧": "Heluo Inn",
  "高昇客棧": "Gaosheng Inn", "王居": "starting house",
  "閻基居": "house of Yan Ji", "田伯光居": "house of Tian Boguang",
  "藥王莊": "Yaowang Manor", "福威鏢局": "Fuwei Escort Agency",
  "峨嵋派": "Emei Sect", "衡山派": "Hengshan Sect",
  "黑龍潭": "Black Dragon Pool", "無量山洞": "Wuliang Cave"};
const place = n => document.documentElement.lang === "en" ? (PLACE[n] || n) : n;
const modelName = n => ALIASES[n] || String(n || "?").replace(/-high$/, "");
const isBase = n => /random|baseline/i.test(n || "");

function msOf(r) {
  const m = r.measure;
  return m && Array.isArray(m.rungs) ? m.rungs : MS.map(() => null);
}
function msReached(r) { return msOf(r).filter(v => v === true).length; }

// the minute of play each milestone was first reached, where the reading has one
function msMinutes(r) {
  const m = r.measure || {}, f = m.first || {}, c = m.chain || [];
  const ended = [f.defeat, f.won].filter(v => v != null);
  return {map: c[0], item: f.obtained, location: c[1], hermit: f.hermit, compass: f.compass,
          party: m.recruited_minute, battle: f.battle,
          ended: ended.length ? Math.min(...ended) : null,
          exp: f.exp, level: f.level, book: c[5]};
}

// a step label on two lines, centred on x
const twoLines = (x, y, text) => {
  const w = String(text).split(" ");
  const a = w.length > 1 ? w.slice(0, Math.ceil(w.length / 2)).join(" ") : text;
  const b = w.length > 1 ? w.slice(Math.ceil(w.length / 2)).join(" ") : "";
  return `<text x="${x}" y="${y}" text-anchor="middle" class="lab">${a}`
    + (b ? `<tspan x="${x}" dy="12">${b}</tspan>` : "") + `</text>`;
};

const minute = v => v == null ? "" : (v < 10 ? v.toFixed(1) : Math.round(v)) + "m";

function msLadder(r, big) {
  const got = msOf(r), when = big ? msMinutes(r) : {};
  const cells = got.map((v, i) => {
    const cls = v === true ? "on" : v === null ? "unk" : "off";
    if (!big) return `<i class="${cls}" title="${T["ms_" + MS[i]]}"></i>`;
    return `<span class="mschip ${cls}"><i></i><b>${T["ms_" + MS[i]]}</b>`
      + `<u>${v === true ? minute(when[MS[i]]) : ""}</u></span>`;
  }).join("");
  const live = r.running ? ` data-live="${r.id}:ladder"` : "";
  return `<div class="ladder${big ? " big" : ""}"${live}>${cells}`
    + `<b class="n">${r.measure ? msReached(r) + "/" + MS.length : "-"}</b></div>`;
}

// keypresses, actions and minute of the first crossing onto the world map
function crossing(r) {
  const m = r.measure;
  if (!m || m.rungs == null) return "-";
  if (m.rungs[0] !== true) return "—";
  const k = m.crossing_keys, a = m.crossing_actions, t = (m.chain || [])[0];
  return [k != null ? k + " " + T.u_keys : null, a != null ? a + " " + T.u_acts : null,
          t != null ? minute(t) : null].filter(Boolean).join(" · ");
}

function places(r) {
  const s = ((r.measure || {}).scenes || []).map(e => e[1]).filter(n => n !== HOME);
  return [...new Set(s)];
}

function routeSrc(r, kind) {
  const m = r.measure || {};
  if (r.running) return r.routes_at ? `${STORE}/live/${r.id}-${kind}.png?v=${r.routes_at}` : null;
  return m[kind + "_url"] ? `${STORE}/${m[kind + "_url"]}` : null;
}

function routesHtml(r, big) {
  const figs = ["house", "world"].map(k => {
    const src = routeSrc(r, k);
    return src ? `<figure class="route ${k}"><img src="${src}" alt="${T["r_" + k]}" loading="lazy">`
      + (big ? `<figcaption>${T["r_" + k]}</figcaption>` : "") + `</figure>` : "";
  }).join("");
  return figs ? `<div class="routes${big ? " big" : ""}">${figs}</div>` : "";
}

// what happened when, in minutes of play, newest last
function eventRows(r) {
  const m = r.measure;
  if (!m) return [];
  const f = m.first || {}, c = m.chain || [], out = [];
  if (c[0] != null) out.push([c[0], T.ev_cross]);
  for (const [t, n] of m.scenes || []) if (n !== HOME) out.push([t, T.ev_enter + " " + place(n)]);
  for (const k of ["hermit", "compass", "battle", "defeat", "won", "exp", "level"])
    if (f[k] != null) out.push([f[k], T["ev_" + k]]);
  if (f.obtained != null) out.push([f.obtained, T.ev_obtained]);
  if (m.recruited_minute != null) out.push([m.recruited_minute, T.ev_recruit]);
  if (c[5] != null) out.push([c[5], T.ev_book]);
  return out.sort((a, b) => a[0] - b[0]);
}

function eventsHtml(r) {
  const rows = eventRows(r);
  if (!rows.length) return `<p class="msg">${r.measure ? T.ev_none : T.ev_unread}</p>`;
  return `<div class="evlist">` + rows.map(([t, what]) =>
    `<div class="ev" data-min="${t}"><span class="t">${minute(t)}</span><span>${what}</span></div>`).join("")
    + `</div>`;
}

// ---------------------------------------------------------------- the board

let bbudget = ["3600", "14400", "all"].includes(Q.get("budget")) ? Q.get("budget") : "3600";

function boardRuns() {
  return runs.filter(r => !r.running && r.measure && r.measure.rungs
    && (showShort || !isShort(r))
    && !/^probe-/.test(r.agent || "")
    && (bbudget === "all" || String(r.budget) === bbudget));
}

const median = xs => {
  const v = xs.filter(x => x != null && isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return null;
  const k = v.length >> 1;
  return v.length % 2 ? v[k] : (v[k - 1] + v[k]) / 2;
};

function modelRows() {
  const by = new Map();
  for (const r of boardRuns()) {
    const k = modelName(r.agent);
    if (!by.has(k)) by.set(k, []);
    by.get(k).push(r);
  }
  const out = [];
  for (const [agent, rs] of by) {
    const cols = MS.map((_, i) => rs.map(r => msOf(r)[i]));
    const counts = cols.map(c => [c.filter(v => v === true).length, c.filter(v => v !== null).length, c.length]);
    out.push({agent, runs: rs, sessions: rs.length, counts,
      reached: counts.filter(c => c[0] > 0).length,
      share: counts.reduce((a, c) => a + (c[2] ? c[0] / c[2] : 0), 0),
      cross: rs.map(r => r.measure.rungs[0] === true ? r.measure.crossing_keys : null)
               .filter(v => v != null).sort((a, b) => a - b),
      base: isBase(agent)});
  }
  return out.sort((a, b) => (a.base - b.base) || (b.reached - a.reached) || (b.share - a.share)
                             || a.agent.localeCompare(b.agent));
}

function disc(k, known, n) {
  const R = 7;
  if (!known) return `<svg class="disc" viewBox="-8 -8 16 16"><circle r="${R}" class="unk"/></svg>`;
  const f = k / n;
  if (f >= 1) return `<svg class="disc" viewBox="-8 -8 16 16"><circle r="${R}" class="full"/></svg>`;
  const a = f * 2 * Math.PI, x = R * Math.sin(a), y = -R * Math.cos(a);
  const wedge = f > 0 ? `<path d="M0 0 L0 ${-R} A${R} ${R} 0 ${f > .5 ? 1 : 0} 1 ${x.toFixed(2)} ${y.toFixed(2)} Z"/>` : "";
  return `<svg class="disc" viewBox="-8 -8 16 16"><circle r="${R}" class="ring"/>${wedge}</svg>`;
}

function drawMilestones(el) {
  const rows = modelRows();
  const humans = bbudget === "14400" ? [] : HUMAN;
  const head = `<div class="mrow hd"><span></span>` + MS.map(k =>
    `<span class="mh">${T["ms_" + k]}</span>`).join("") + `<span class="mh">${T.b_runs}</span></div>`;
  const line = (label, sub, counts, n, open, tag) =>
    `<div class="mrow"${open ? ` data-open="${open}"` : ""}>`
    + `<span class="mm">${label}${sub ? `<u>${sub}</u>` : ""}${tag || ""}</span>`
    + counts.map(c => `<span title="${c[0]}/${c[2]}">${disc(c[0], c[1], c[2])}</span>`).join("")
    + `<span class="mn">${n}</span></div>`;
  el.innerHTML = `<div class="mtable">` + head
    + humans.map(h => line(T["h_" + h.cls], T.h_sub, h.counts.map(k => [k, h.sessions, h.sessions]), h.sessions))
      .join("")
    + rows.map(m => line(mark(m.agent) + `<b>${m.agent}</b>`, "", m.counts, m.sessions,
        m.sessions === 1 ? m.runs[0].id : "", m.base ? `<span class="btag">${T.b_base}</span>` : ""))
      .join("")
    + `</div>`;
  wireOpen(el);
  $("bnote").textContent = T.b_n_ms;
}

function drawCrossing(el) {
  const rows = modelRows().filter(m => m.cross.length && !m.base);
  rows.sort((a, b) => (a.cross.reduce((x, y) => x + y, 0) / a.cross.length)
                    - (b.cross.reduce((x, y) => x + y, 0) / b.cross.length));
  if (!rows.length) { el.innerHTML = `<p class="msg">${T.empty}</p>`; return; }
  const W = 940, L = 170, R = 20, P = 22, TP = 8, H = TP + rows.length * P + 34;
  const lo = 10, hi = Math.max(1000, ...rows.flatMap(m => m.cross)) * 1.2;
  const x = v => L + (Math.log10(Math.max(lo, v)) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo)) * (W - L - R);
  const ticks = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000].filter(v => v <= hi);
  let svg = ticks.map(v => `<line x1="${x(v)}" y1="${TP}" x2="${x(v)}" y2="${H - 30}" class="gl"/>`
    + `<text x="${x(v)}" y="${H - 16}" text-anchor="middle" class="ax">${v}</text>`).join("");
  rows.forEach((m, i) => {
    const y = TP + i * P + P / 2, mean = m.cross.reduce((a, b) => a + b, 0) / m.cross.length;
    svg += `<text x="${L - 10}" y="${y + 4}" text-anchor="end" class="lab">${m.agent}</text>`
      + `<line x1="${x(Math.min(...m.cross))}" y1="${y}" x2="${x(Math.max(...m.cross))}" y2="${y}" class="rng"/>`
      + m.cross.map(v => `<circle cx="${x(v)}" cy="${y}" r="3.2" class="one"><title>${v}</title></circle>`).join("")
      + `<circle cx="${x(mean)}" cy="${y}" r="4.2" class="mean"><title>${Math.round(mean)}</title></circle>`;
  });
  svg += `<text x="${L}" y="${H - 2}" class="ax">${T.b_axis_keys}</text>`;
  el.innerHTML = `<div class="plotwrap"><svg viewBox="0 0 ${W} ${H}" class="plot">${svg}</svg></div>`;
  $("bnote").textContent = T.b_n_cross;
}

// the chain of steps: of the sessions that passed the step before, who passed
// this one, and the minutes it took them, or until their last action
function chainOf(rs) {
  let prev = rs.map(r => [r, 0]);
  return STEPS.map((s, i) => {
    const passed = [], stuck = [];
    for (const [r, t0] of prev) {
      const t = (r.measure.chain || [])[i];
      if (t != null) passed.push([r, t, t - t0]);
      else stuck.push([r, Math.max(0, (r.played || 0) / 60 - t0)]);
    }
    const out = {step: s, atRisk: prev.length, passed, stuck};
    prev = passed.map(([r, t]) => [r, t]);
    return out;
  });
}

function drawFilters(el) {
  const rs = boardRuns().filter(r => !isBase(r.agent));
  if (!rs.length) { el.innerHTML = `<p class="msg">${T.empty}</p>`; return; }
  const ch = chainOf(rs), n = rs.length;
  const W = 940, H = 250, gap = 40, pw = (W - gap) / 2, TP = 16, BT = 40, L = 44;
  const cx = (i, w, l) => l + (i + 0.5) * (w - l) / STEPS.length;
  const yb = v => TP + (1 - v) * (H - TP - BT);
  let left = [0, .25, .5, .75, 1].map(v => `<line x1="${L}" y1="${yb(v)}" x2="${pw}" y2="${yb(v)}" class="gl"/>`
    + `<text x="${L - 6}" y="${yb(v) + 3.5}" text-anchor="end" class="ax">${Math.round(v * 100)}%</text>`).join("");
  ch.forEach((c, i) => {
    const v = c.passed.length / n, bw = (pw - L) / STEPS.length * 0.6, x0 = cx(i, pw, L) - bw / 2;
    left += `<rect x="${x0}" y="${yb(v)}" width="${bw}" height="${yb(0) - yb(v)}" class="bar"/>`
      + `<text x="${cx(i, pw, L)}" y="${yb(v) - 5}" text-anchor="middle" class="ax">${c.passed.length}/${n}</text>`
      + twoLines(cx(i, pw, L), H - BT + 16, T["st_" + c.step]);
  });
  const lo = 0.5, hi = 300, X0 = pw + gap;
  const ym = v => TP + (1 - (Math.log10(Math.min(hi, Math.max(lo, v))) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo))) * (H - TP - BT);
  let right = [1, 3, 10, 30, 100].map(v => `<line x1="${X0 + L}" y1="${ym(v)}" x2="${W}" y2="${ym(v)}" class="${v === 30 ? "wait" : "gl"}"/>`
    + `<text x="${X0 + L - 6}" y="${ym(v) + 3.5}" text-anchor="end" class="ax">${v}</text>`).join("");
  ch.forEach((c, i) => {
    const x = X0 + cx(i, pw, L), jitter = k => ((k * 37) % 11 - 5) * 1.3;
    right += c.passed.map(([r, , d], k) => `<circle cx="${x - 7 + jitter(k)}" cy="${ym(d)}" r="3" class="pass" data-open="${r.id}"><title>${modelName(r.agent)} ${minute(d)}</title></circle>`).join("")
      + c.stuck.map(([r, d], k) => `<circle cx="${x + 7 + jitter(k)}" cy="${ym(d)}" r="3" class="open" data-open="${r.id}"><title>${modelName(r.agent)} ${minute(d)}</title></circle>`).join("")
      + twoLines(x, H - BT + 16, T["st_" + c.step]);
  });
  right += `<text x="${X0 + L}" y="${TP - 4}" class="ax">${T.b_axis_min}</text>`;
  el.innerHTML = `<div class="plotwrap"><svg viewBox="0 0 ${W} ${H}" class="plot filters">${left}${right}</svg></div>`;
  wireOpen(el);
  $("bnote").textContent = T.b_n_filters;
}

function drawEffort(el) {
  const rows = modelRows();
  const f1 = v => v == null ? "-" : v.toFixed(1), f0 = v => v == null ? "-" : Math.round(v);
  el.innerHTML = `<div class="etable"><div class="erow hd"><span>${T.b_model}</span><span>${T.b_runs}</span>`
    + `<span>${T.e_actions}</span><span>${T.e_keys}</span><span>${T.e_think}</span><span>${T.e_reads}</span></div>`
    + rows.map(m => `<div class="erow"><span class="mm">${mark(m.agent)}<b>${m.agent}</b>`
      + (m.base ? `<span class="btag">${T.b_base}</span>` : "") + `</span>`
      + `<span>${m.sessions}</span>`
      + `<span>${f0(median(m.runs.map(r => r.actions)))}</span>`
      + `<span>${f1(median(m.runs.map(r => r.actions ? (r.key_events ?? r.actions) / r.actions : null)))}</span>`
      + `<span>${f1(median(m.runs.map(r => r.gap_p50)))}s</span>`
      + `<span>${f1(median(m.runs.map(r => r.actions && r.reads != null ? r.reads / r.actions : null)))}</span></div>`)
      .join("") + `</div>`;
  $("bnote").textContent = T.b_n_effort;
}

const BOARD = {milestones: drawMilestones, crossing: drawCrossing, filters: drawFilters, effort: drawEffort};
let bview = BOARD[Q.get("board")] ? Q.get("board") : "milestones";

function drawBoard() {
  const el = $("btable");
  if (!el) return;
  if (!boardRuns().length) { el.innerHTML = `<p class="msg">${T.empty}</p>`; $("bnote").textContent = ""; return; }
  BOARD[bview](el);
}

function wireBoard() {
  for (const [id, key, set] of [["bviews", "b", v => { bview = v; }], ["bbudget", "bb", v => { bbudget = v; }]]) {
    const seg = $(id);
    if (!seg) continue;
    const cur = id === "bviews" ? bview : bbudget;
    seg.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", String(x.dataset[key] === cur)));
    seg.addEventListener("click", e => {
      const b = e.target.closest(`button[data-${key}]`);
      if (!b) return;
      set(b.dataset[key]);
      seg.querySelectorAll("button").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      drawBoard();
    });
  }
}

function provenance() {
  const done = runs.filter(r => !r.running);
  const last = Math.max(0, ...done.map(r => r.started || 0));
  const ed = document.querySelector('meta[name="build"]');
  $("pved").textContent = ed ? ed.content.slice(0, 8) : "-";
  $("pvruns").textContent = done.length;
  $("pvup").textContent = last ? new Date(last * 1000).toISOString().slice(0, 10) : "-";
}
