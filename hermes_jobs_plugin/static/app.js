/*
 * jobs.ahfl.in board shell.
 *
 * The backend is the security boundary: every /api/jobs* route filters by the
 * signed-in person's vault aliases and rejects another user's job with 403.
 * This file only keeps the UI consistent with that rule. Everyone defaults to
 * "My jobs"; the extra "All jobs" control is rendered only when /api/whoami
 * reports is_admin=true. Toggling it resets every cached lane so a user can
 * never see an old row from the other scope while the new scope is loading.
 */
"use strict";

const STATUS_LABEL = {
  ready: "Queued",
  running: "Working",
  blocked: "Needs you",
  review: "Needs you",
  done: "Done",
  archived: "Dropped",
};

const ALL_LANES = ["needs_you", "working", "done", "dropped"];
const PAGE_SIZE = 50;

let currentLane = "needs_you";
// id -> job object. Holds both slim list rows and (once a job has been
// opened) the full detail object; see upsertJob for the merge rule.
const jobsById = new Map();
// Per-lane pagination state. ids are kept in server order (newest first)
// and only ever appended to, so scrolling never reshuffles what is
// already on screen.
const laneState = {};
function freshLaneState() {
  return { ids: [], cursor: null, done: false, loading: false, loaded: false };
}
ALL_LANES.forEach((l) => { laneState[l] = freshLaneState(); });

// Search + date filter, shared across lanes: searching for something and
// then flipping tabs should keep the search applied, with each lane's
// badge showing how many of ITS jobs match.
const filterState = { q: "", from: null, to: null, day: "all" };
let searchDebounce = null;

// Filled from /api/whoami during init. The flags are presentation-only; the
// server repeats every authorization check, so a tampered browser cannot gain
// access by flipping these values.
let me = { email: "", is_admin: false };
// False = "My jobs" (default for everyone). Only an admin can set this true.
let scopeAll = false;
// Raw tasks.tenant of the selected owner chip inside All jobs. Empty string
// means "All users". It is deliberately not persisted: a fresh login always
// starts on the normal owner-scoped board.
let ownerFilter = "";
// Cached owner-chip data from /api/jobs/owners, used only by the admin view.
let owners = [];

let activeJobId = null;
let sheetSignature = "";
let pollTimer = null;
let toastTimer = null;
let mediaRecorder = null;
let recordedChunks = [];
let discardRecording = false;
let composerMode = "new";
let composerJob = null;
// Unique id for the currently open composer. Dictation and pending submission
// items are tied to this id so a background transcription can tell whether the
// same form is still on screen, and a restored submission can finish after a
// reload without needing the modal to be open.
let composerDraftId = null;
// The mode-specific label for the submit button, restored after temporary
// "waiting for dictation" text.
let composerSubmitLabel = "Create job";
let fabOpen = false;

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function fmtTime(ts) {
  if (!ts) return "";
  const d = new Date(ts * 1000);
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function fmtSize(bytes) {
  if (bytes == null) return "";
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

// Matches a run of http(s):// or www. text with no whitespace/angle-bracket/
// quote in it, then peels off trailing punctuation that is almost certainly
// sentence punctuation rather than part of the URL (a closing paren/quote/
// period right after a link). Operates on the RAW string so an escaped "&"
// (-> "&amp;") never ends up inside an href; escaping happens per-segment
// as the string is rebuilt, never on the whole thing up front.
const URL_RE = /((?:https?:\/\/|www\.)[^\s<>"']+)/gi;

function linkify(raw) {
  const text = raw || "";
  let out = "";
  let last = 0;
  let m;
  URL_RE.lastIndex = 0;
  while ((m = URL_RE.exec(text))) {
    let url = m[0];
    let trail = "";
    while (url.length && /[.,;:!?)\]'"]$/.test(url)) {
      trail = url.slice(-1) + trail;
      url = url.slice(0, -1);
    }
    if (!url) continue;
    out += escapeHtml(text.slice(last, m.index));
    const href = url.startsWith("http") ? url : "https://" + url;
    out += `<a href="${escapeHtml(href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a>`;
    out += escapeHtml(trail);
    last = m.index + m[0].length;
  }
  out += escapeHtml(text.slice(last));
  return out;
}

function fileListHtml(jobId, files) {
  if (!files || !files.length) return "";
  return `<div class="file-list">${files.map((f) => `
    <a class="file-chip" href="/api/jobs/${jobId}/artifact?path=${encodeURIComponent(f.path)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(f.path)}">
      <span class="file-icon">&#128196;</span>
      <span class="file-name">${escapeHtml(f.name)}</span>
      ${f.size != null ? `<span class="file-size">${fmtSize(f.size)}</span>` : `<span class="file-size">missing</span>`}
    </a>`).join("")}</div>`;
}

function showToast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 2600);
}

// GET helper. The HTTP status is attached to the thrown Error so callers can
// distinguish "job no longer exists" (404) from "not your job" (403) without
// parsing the message text.
async function apiGet(path) {
  const r = await fetch(path, { credentials: "include" });
  if (!r.ok) {
    const err = new Error("GET " + path + " -> " + r.status);
    err.status = r.status;
    throw err;
  }
  return r.json();
}

async function apiPost(path, body) {
  const r = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || ("POST " + path + " -> " + r.status));
  return data;
}

// Used for every action that can carry an optional file attachment
// (create/answer/continue). Always multipart -- simpler than branching on
// whether files are present, and the backend accepts both forms anyway.
async function apiPostForm(path, fields, files) {
  const form = new FormData();
  Object.entries(fields || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null) form.append(k, v);
  });
  (files || []).forEach((f) => form.append("files", f, f.name));
  const r = await fetch(path, { method: "POST", credentials: "include", body: form });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.error || ("POST " + path + " -> " + r.status));
  return data;
}

function markUpdated() {
  const el = $("#lastUpdated");
  if (!el) return;
  const now = new Date();
  el.textContent = "Updated " + now.toLocaleTimeString(undefined, {
    hour: "2-digit", minute: "2-digit", second: "2-digit",
  });
}

function applyCounts(counts) {
  for (const lane of ALL_LANES) {
    const el = $("#badge-" + lane);
    if (el) el.textContent = (counts && counts[lane]) || 0;
  }
}

// A slim list row must never overwrite a full detail object already
// fetched for the same job -- otherwise reopening a job would blank its
// instruction/result until the detail call came back again.
function upsertJob(incoming) {
  const existing = jobsById.get(incoming.id);
  if (!existing) {
    jobsById.set(incoming.id, incoming);
    return;
  }
  const merged = { ...existing, ...incoming };
  if (existing.slim === false && incoming.slim) merged.slim = false;
  jobsById.set(incoming.id, merged);
}

// Build the query parameters shared by initial loads, polling and infinite
// scroll. The scope is included only while an admin has All jobs selected, so
// normal requests stay byte-identical to the original My-jobs traffic.
function filterParams() {
  const p = new URLSearchParams();
  if (filterState.q) p.set("q", filterState.q);
  if (filterState.from != null) p.set("from", String(filterState.from));
  if (filterState.to != null) p.set("to", String(filterState.to));
  if (scopeAll && me.is_admin) {
    p.set("scope", "all");
    if (ownerFilter) p.set("owner", ownerFilter);
  }
  return p;
}

function filterIsActive() {
  return !!filterState.q || filterState.day !== "all";
}

async function loadLane(lane, opts = {}) {
  const st = laneState[lane];
  if (st.loading) return;
  if (!opts.reset && st.done && st.loaded) return;
  st.loading = true;
  updateSentinel();
  try {
    const qs = filterParams();
    qs.set("lane", lane);
    qs.set("limit", String(PAGE_SIZE));
    const cursor = opts.reset ? null : st.cursor;
    if (cursor) qs.set("cursor", cursor);

    const data = await apiGet("/api/jobs?" + qs.toString());
    const incoming = data.jobs || [];
    incoming.forEach(upsertJob);

    if (opts.reset) {
      st.ids = incoming.map((j) => j.id);
    } else {
      const seen = new Set(st.ids);
      st.ids = st.ids.concat(incoming.map((j) => j.id).filter((id) => !seen.has(id)));
    }
    st.cursor = data.next_cursor || null;
    st.done = !data.next_cursor;
    st.loaded = true;

    applyCounts(data.counts);
    if (lane === currentLane) renderList();
    markUpdated();
  } catch (e) {
    console.error(e);
    showToast("Could not load jobs");
  } finally {
    st.loading = false;
    updateSentinel();
  }
}

// Throw away every page so each lane refetches on next view. Used after
// any action that can move a job between lanes (answer, continue, drop,
// create) -- the alternative is guessing which lanes changed.
function invalidateLanes() {
  ALL_LANES.forEach((l) => { laneState[l] = freshLaneState(); });
}

async function pollTick() {
  // Only re-fetch page 1 when the user is near the top. Deep-scrolled,
  // resetting to page 1 would yank rows out from under them, and a job
  // that moved lanes further down the list is not visible from page 1
  // anyway -- so counts stay live and the list reconciles on manual
  // refresh or a lane switch.
  const atTop = window.scrollY < 80;
  const st = laneState[currentLane];
  if (atTop && !st.loading) {
    await loadLane(currentLane, { reset: true });
  } else {
    try {
      const qs = filterParams();
      qs.set("lane", currentLane);
      qs.set("limit", "1");
      const data = await apiGet("/api/jobs?" + qs.toString());
      applyCounts(data.counts);
      markUpdated();
    } catch (e) {
      console.error(e);
    }
  }
  // The open modal refreshes itself rather than inferring state from the
  // list -- it needs full detail (events/artifacts) the list never carries.
  if (activeJobId && !$("#jobModal").classList.contains("hidden") && jobModalIsIdle()) {
    refreshOpenJob();
  }
}

// Wraps the lane reload with visible feedback for an explicit tap on the
// refresh button -- spins the icon, disables the button so a second tap
// can't pile up a duplicate request, and toasts a one-line confirmation.
// The silent 5s background poll (pollTick) refreshes quietly and only
// shows through the "Updated HH:MM:SS" label (markUpdated), which both
// paths share -- no visible refresh ever happens without that label
// moving.
async function manualRefresh() {
  const btn = $("#refreshBtn");
  const icon = $("#refreshIcon");
  if (btn.disabled) return;
  btn.disabled = true;
  icon.classList.add("spinning");
  try {
    invalidateLanes();
    if (scopeAll && me.is_admin) loadOwners();
    await loadLane(currentLane, { reset: true });
    showToast("Jobs updated");
  } finally {
    icon.classList.remove("spinning");
    btn.disabled = false;
  }
}

function localMidnight(dateObj) {
  const x = new Date(dateObj);
  x.setHours(0, 0, 0, 0);
  return Math.floor(x.getTime() / 1000);
}

// Day boundaries are computed HERE, in the browser, and sent to the
// server as plain epoch seconds. The server never works out what a
// "day" is -- it does not know the viewer's timezone, and bucketing by
// UTC date would file an early-morning job under the day before.
function setDayFilter(key, dateStr) {
  const today = localMidnight(new Date());
  filterState.day = key;

  if (key === "today") {
    filterState.from = today;
    filterState.to = today + 86400;
  } else if (key === "yesterday") {
    filterState.from = today - 86400;
    filterState.to = today;
  } else if (key === "7d") {
    filterState.from = today - 6 * 86400;
    filterState.to = today + 86400;
  } else if (key === "date" && dateStr) {
    // "YYYY-MM-DD" parsed by hand: new Date("2026-10-28") is treated as
    // UTC midnight by spec, which lands on the wrong local day for any
    // timezone east or west of UTC.
    const [y, m, d] = dateStr.split("-").map(Number);
    const from = localMidnight(new Date(y, m - 1, d));
    filterState.from = from;
    filterState.to = from + 86400;
  } else {
    filterState.day = "all";
    filterState.from = null;
    filterState.to = null;
  }

  // Only date chips carry data-day. The admin scope chips also use the
  // day-chip pill styling, so a broad .day-chip selector here would strip
  // their active state every time a date filter changed.
  $$(".day-chip[data-day]").forEach((c) => c.classList.toggle("active", c.dataset.day === filterState.day));
  const picker = $("#datePick");
  picker.classList.toggle("active", filterState.day === "date");
  if (filterState.day !== "date") picker.value = "";

  applyFilters();
}

function dayFilterLabel() {
  if (filterState.day === "today") return "today";
  if (filterState.day === "yesterday") return "yesterday";
  if (filterState.day === "7d") return "last 7 days";
  if (filterState.day === "date" && filterState.from != null) {
    return new Date(filterState.from * 1000).toLocaleDateString(undefined, {
      day: "numeric", month: "short", year: "numeric",
    });
  }
  return "";
}

function updateFilterSummary() {
  const bits = [];
  if (filterState.q) bits.push('matching "' + filterState.q + '"');
  const day = dayFilterLabel();
  if (day) bits.push(day);
  const active = bits.length > 0;
  $("#filterSummary").classList.toggle("hidden", !active);
  $("#filterSummaryText").textContent = active ? "Showing jobs " + bits.join(" \u00b7 ") : "";
}

// Any filter change invalidates every cached page: the cursor space
// changes, so old pages cannot be extended.
function applyFilters() {
  invalidateLanes();
  updateFilterSummary();
  renderList();
  loadLane(currentLane, { reset: true });
}

function clearFilters() {
  filterState.q = "";
  $("#searchInput").value = "";
  $("#searchClear").classList.add("hidden");
  setDayFilter("all");
}

function setLane(lane) {
  currentLane = lane;
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.lane === lane));
  renderList();
  window.scrollTo({ top: 0 });
  if (!laneState[lane].loaded) loadLane(lane, { reset: true });
}

// Switch between the normal owner-scoped board and the admin-only All jobs
// board. Clearing jobsById is deliberate: without it, a stale detail object
// from the previous scope could still be opened while the new lane loads.
// The server independently rejects scope=all for non-admins, so this function
// is not a security boundary.
function setScope(all) {
  const next = Boolean(all && me.is_admin);
  if (next === scopeAll) return;
  scopeAll = next;

  closeJob();
  jobsById.clear();
  invalidateLanes();
  renderList();

  const mineBtn = $("#scopeMine");
  const allBtn = $("#scopeAll");
  if (mineBtn) mineBtn.classList.toggle("active", !scopeAll);
  if (allBtn) allBtn.classList.toggle("active", scopeAll);
  // The owner column is additive: Origin stays visible in both scopes, and the
  // extra "Created by" column appears only while All jobs is active.
  document.body.classList.toggle("scope-all", scopeAll);

  // The owner-chip row exists only inside All jobs. Leaving that scope clears
  // the selected owner so returning to My jobs cannot carry a stale filter.
  showOwnerFilterBar(scopeAll);
  loadLane(currentLane, { reset: true });
}

// Render the admin-only owner chips. The first chip is always "All users";
// each remaining chip is one raw tenant key from /api/jobs/owners. Counts are
// all-time job totals, not just the currently loaded lane.
function renderOwnerChips() {
  const wrap = $("#ownerChips");
  if (!wrap) return;
  const total = owners.reduce((sum, o) => sum + (o.count || 0), 0);
  const parts = [
    `<button type="button" class="owner-chip ${ownerFilter ? "" : "active"}" data-owner="">`
      + `All users <span class="owner-count">${total}</span></button>`,
  ];
  owners.forEach((o) => {
    const tenant = o.tenant || "";
    const label = o.display || tenant;
    parts.push(
      `<button type="button" class="owner-chip ${ownerFilter === tenant ? "active" : ""}"`
      + ` data-owner="${escapeHtml(tenant)}" title="${escapeHtml(label)}">`
      + `${escapeHtml(label)} <span class="owner-count">${o.count || 0}</span></button>`
    );
  });
  wrap.innerHTML = parts.join("");
  wrap.querySelectorAll(".owner-chip").forEach((btn) => {
    btn.onclick = () => setOwnerFilter(btn.dataset.owner || "");
  });
}

// Fetch the distinct owner list for the All jobs view. Admin-only on the
// server as well; this function is only called after whoami says is_admin.
async function loadOwners() {
  if (!me.is_admin) return;
  try {
    const data = await apiGet("/api/jobs/owners");
    owners = data.owners || [];
    // If the selected owner disappeared (or was renamed/merged), fall back to
    // All users instead of leaving the list permanently empty.
    if (ownerFilter && !owners.some((o) => o.tenant === ownerFilter)) {
      ownerFilter = "";
      invalidateLanes();
    }
    renderOwnerChips();
  } catch (e) {
    console.error(e);
    showToast("Could not load owners");
  }
}

// Select one owner chip (or "" for All users) and reload every lane with the
// new owner filter. Clearing jobsById prevents a stale detail modal from the
// previous owner remaining open while the new scope loads.
function setOwnerFilter(tenant) {
  const next = tenant || "";
  if (next === ownerFilter) return;
  ownerFilter = next;
  closeJob();
  jobsById.clear();
  invalidateLanes();
  renderList();
  renderOwnerChips();
  loadLane(currentLane, { reset: true });
}

// Show/hide the owner-chip row and reset its state when leaving All jobs.
// loadOwners is intentionally lazy: the first switch into All jobs fetches the
// list, and manual refresh can refresh it later.
function showOwnerFilterBar(visible) {
  const bar = $("#ownerFilterBar");
  if (bar) bar.classList.toggle("hidden", !visible);
  if (visible) {
    renderOwnerChips();
    loadOwners();
  } else {
    ownerFilter = "";
    owners = [];
    const chips = $("#ownerChips");
    if (chips) chips.innerHTML = "";
  }
}

// Desktop arrows scroll the owner row by most of a viewport; phones use normal
// finger scrolling because the row is a horizontal overflow container.
function scrollOwnerChips(direction) {
  const chips = $("#ownerChips");
  if (!chips) return;
  const distance = Math.max(180, Math.round(chips.clientWidth * 0.7));
  chips.scrollBy({ left: direction * distance, behavior: "smooth" });
}

function jobSignature(j) {
  return [
    j.status, j.pending_kind, j.result, j.question, j.question_context,
    j.last_failure_error, j.completed_at, j.dropped_at, j.resume_rounds,
    (j.tags || []).join(","),
  ].join("|");
}

function jobModalIsIdle() {
  const modal = $("#jobModal");
  const active = document.activeElement;
  if (active && modal.contains(active) && /^(TEXTAREA|INPUT)$/.test(active.tagName)) {
    return false;
  }
  return Array.from(modal.querySelectorAll("textarea")).every((t) => !t.value.trim());
}

function renderList() {
  const list = $("#list");
  const st = laneState[currentLane];
  const items = st.ids.map((id) => jobsById.get(id)).filter(Boolean);

  list.className = "jobs-list" + (items.length === 0 ? " solo" : "");
  $("#jobsHead").classList.toggle("hidden", items.length === 0);
  list.innerHTML = "";

  if (items.length === 0) {
    const p = document.createElement("p");
    p.className = "empty";
    p.textContent = !st.loaded
      ? "Loading\u2026"
      : filterIsActive()
      ? "No jobs in this tab match these filters."
      : currentLane === "needs_you"
      ? "Nothing needs you right now."
      : "No jobs here.";
    list.appendChild(p);
    updateSentinel();
    return;
  }

  // No client-side day-group headers -- the All/Today/Yesterday/7-days
  // chips + date picker in the filter bar already cover "jobs for a
  // particular day" without a second, buggier mechanism for the same
  // thing (the sticky header's hardcoded top offset didn't account for
  // the filter bar's real height, so it overlapped/hid the row right
  // under it -- simplest fix was removing the redundant feature).
  for (const j of items) list.appendChild(renderRow(j));
  updateSentinel();
}

// Footer under the list: drives infinite scroll and says whether more
// pages exist.
function updateSentinel() {
  const el = $("#scrollSentinel");
  if (!el) return;
  const st = laneState[currentLane];
  if (st.loading) {
    el.textContent = "Loading more\u2026";
  } else if (st.loaded && !st.done) {
    el.textContent = "Scroll for more";
  } else if (st.loaded && st.ids.length) {
    el.textContent = "All " + st.ids.length + " shown";
  } else {
    el.textContent = "";
  }
}

function renderRow(j) {
  const row = document.createElement("div");
  row.className = "job-row";
  row.setAttribute("role", "button");
  row.setAttribute("tabindex", "0");
  row.setAttribute("aria-label", `${STATUS_LABEL[j.status] || j.status}: ${j.title || j.id}`);
  row.onclick = () => openJob(j.id);
  row.onkeydown = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      openJob(j.id);
    }
  };
  row.innerHTML = `
    <div class="job-status">
      <span class="pill status-${j.status}">${escapeHtml(STATUS_LABEL[j.status] || j.status)}</span>
    </div>
    <div class="job-main">
      <div class="job-title">${escapeHtml(j.title || "Untitled job")}</div>
      <div class="job-id">${escapeHtml(j.id)}${j.resume_rounds ? ` &middot; ${j.resume_rounds} round(s)` : ""}${j.parent_job_id ? ` &middot; chained` : ""}</div>
      ${listTagsHtml(j)}
    </div>
    <div class="job-detail">
      <div class="job-detail-text">${escapeHtml(j.snippet || "")}</div>
    </div>
    <div class="job-owner owner-col">${escapeHtml(j.owner_display || j.owner || "")}</div>
    <div class="job-origin">${escapeHtml(j.origin_display || "")}</div>
    <div class="job-time">${fmtTime(j.created_at)}</div>
    <div class="job-actions"><span class="row-open">Open &rsaquo;</span></div>
  `;
  wireRowTagEditor(row, j);
  return row;
}

// Tags are stored as flat "type:Label" strings (see hermes_jobs_plugin/
// tagging.py) -- "contacts:Raghu Iyer", "projects:Ranka Amber",
// "work:follow_up". Only the label is shown; the type just picks the
// chip style (work: gets the accent chip, everything else is neutral --
// the label itself already says what kind of thing it is).
// Split a stored "type:Label" tag into its display pieces. The type only
// chooses a colour; the label is what people actually read.
function tagParts(tag) {
  const text = String(tag || "");
  const sep = text.indexOf(":");
  const type = sep === -1 ? "" : text.slice(0, sep);
  const label = sep === -1 ? text : text.slice(sep + 1);
  // Stored classification values are snake_case (research_lookup); show the
  // same friendly label the add-tag selector uses while keeping the raw value
  // in the stored tag and remove-button data attribute.
  const classification = type === "work"
    ? TAG_CLASSIFICATIONS.find(([value]) => value === label)
    : null;
  return { type, label, display: classification ? classification[1] : label };
}

// The seven classification buckets tagging.py already uses for the blue
// work: chips. Exposing them in the add-tag control lets a human add a missing
// classification (e.g. work:communication) instead of being forced into a
// free-text noun tag.
const TAG_CLASSIFICATIONS = [
  ["communication", "Communication"],
  ["follow_up", "Follow-up"],
  ["scheduling", "Scheduling"],
  ["drafting_creative", "Drafting / creative"],
  ["research_lookup", "Research / lookup"],
  ["compliance_finance", "Compliance / finance"],
  ["engineering", "Engineering"],
];

function tagTypeOptionsHtml() {
  return `<option value="manual">Noun / custom text</option>`
    + TAG_CLASSIFICATIONS.map(([value, label]) =>
      `<option value="work:${value}">${label} (classification)</option>`
    ).join("");
}

// A list row is itself clickable, so every tag control below stops propagation
// before it runs. Without that, tapping a delete button would also open the job.
function listTagsHtml(job) {
  const tags = Array.isArray(job.tags) ? job.tags : [];
  const jobId = escapeHtml(job.id);
  const chips = tags.map((t) => {
    const { type, display } = tagParts(t);
    const cls = type === "work" ? "tag-chip tag-chip-work tag-chip-editable" : "tag-chip tag-chip-editable";
    return `<span class="${cls}">${escapeHtml(display)}`
      + `<button type="button" class="tag-remove" data-row-remove-tag="${escapeHtml(t)}"`
      + ` data-row-job-id="${jobId}" aria-label="Remove tag ${escapeHtml(display)}" title="Remove tag">&times;</button></span>`;
  }).join("");
  return `<div class="job-tags list-tags" data-row-tags="${jobId}">${chips}`
    + `<button type="button" class="tag-add" data-row-add-tag="${jobId}" aria-label="Add tag" title="Add tag">+</button>`
    + `<span class="tag-add-wrap hidden" data-row-tag-wrap="${jobId}">`
    + `<select class="tag-add-type" data-row-tag-type="${jobId}">${tagTypeOptionsHtml()}</select>`
    + `<input type="text" class="tag-add-input" data-row-tag-input="${jobId}" maxlength="80" placeholder="tag or type:Label" autocomplete="off">`
    + `<button type="button" class="btn btn-primary tag-add-save" data-row-tag-save="${jobId}">Add</button>`
    + `<button type="button" class="tag-add-cancel" data-row-tag-cancel="${jobId}" aria-label="Cancel">&times;</button>`
    + `</span></div>`;
}

// Editable chips for the detail modal. Each chip gets a remove button that
// appears on hover/focus (and is always visible on touch devices), followed by
// a + button that reveals a classification selector plus a small inline input.
function editableTagsHtml(job) {
  const tags = Array.isArray(job.tags) ? job.tags : [];
  const chips = tags.map((t) => {
    const { type, display } = tagParts(t);
    const cls = type === "work" ? "tag-chip tag-chip-work tag-chip-editable" : "tag-chip tag-chip-editable";
    return `<span class="${cls}">${escapeHtml(display)}`
      + `<button type="button" class="tag-remove" data-remove-tag="${escapeHtml(t)}"`
      + ` aria-label="Remove tag ${escapeHtml(display)}" title="Remove tag">&times;</button></span>`;
  }).join("");
  return `<div class="job-tags editable-tags" id="jobTags">${chips}`
    + `<button type="button" class="tag-add" id="addTagBtn" aria-label="Add tag" title="Add tag">+</button>`
    + `<span class="tag-add-wrap hidden" id="tagAddWrap">`
    + `<select id="tagAddType" class="tag-add-type">${tagTypeOptionsHtml()}</select>`
    + `<input type="text" id="tagAddInput" class="tag-add-input" maxlength="80" placeholder="tag or type:Label" autocomplete="off">`
    + `<button type="button" class="btn btn-primary tag-add-save" id="tagAddSave">Add</button>`
    + `<button type="button" class="tag-add-cancel" id="tagAddCancel" aria-label="Cancel">&times;</button>`
    + `</span></div>`;
}

// Selecting a classification disables the text input: the category itself is
// the complete tag. Selecting Noun/custom re-enables free-text entry.
function syncTagInputForType(select, input) {
  if (!select || !input) return;
  const isClassification = select.value.startsWith("work:");
  input.disabled = isClassification;
  input.placeholder = isClassification ? "Classification tag selected" : "tag or type:Label";
  if (isClassification) input.value = "";
}

function metaItem(k, v) {
  if (!v) return "";
  return `<div class="meta-item"><span class="k">${escapeHtml(k)}</span><span class="v">${escapeHtml(v)}</span></div>`;
}

function openJob(jobId) {
  const j = jobsById.get(jobId);
  if (!j) return;
  activeJobId = jobId;
  sheetSignature = "";
  clearPendingFiles("jobFilesInput");
  // Render the cheap list-cache version immediately (no blank modal while
  // the detail call is in flight), then replace it with the full detail
  // fetch -- the list endpoint deliberately omits events/artifacts/input
  // attachments to stay light, so a job only ever shows those once this
  // resolves.
  renderJob(j);
  $("#jobModal").classList.remove("hidden");
  updateBodyLock();
  refreshOpenJob();
}

async function refreshOpenJob() {
  if (!activeJobId) return;
  const jobId = activeJobId;
  try {
    const detail = await apiGet(`/api/jobs/${jobId}`);
    if (activeJobId !== jobId) return; // closed/switched while in flight
    detail.slim = false;
    upsertJob(detail);
    if (jobModalIsIdle() && jobSignature(detail) !== sheetSignature) {
      renderJob(jobsById.get(jobId));
    }
  } catch (e) {
    console.error(e);
    // The detail endpoint is the direct-URL surface. A 403 here means the job
    // exists but belongs to someone else (or the session's aliases changed).
    // Close the stale modal rather than leaving a partially rendered job open.
    if (e && e.status === 403) {
      closeJob();
      showToast("You do not have access to this job");
    }
  }
}

function closeJob() {
  stopRecording(true);
  activeJobId = null;
  sheetSignature = "";
  $("#jobModal").classList.add("hidden");
  updateBodyLock();
}

function attachRowHtml(inputId, label) {
  return `
      <label class="field-label">${escapeHtml(label || "Attach files (optional)")}</label>
      <div class="attach-row">
        <input type="file" id="${inputId}" class="file-input-hidden" multiple>
        <button type="button" class="btn btn-secondary attach-btn" data-attach-for="${inputId}">&#128206; Attach files</button>
        <div class="attach-chips" data-attach-chips-for="${inputId}"></div>
      </div>`;
}

function renderJob(j) {
  activeJobId = j.id;
  sheetSignature = jobSignature(j);

  $("#jobModalStatus").innerHTML =
    `<span class="pill status-${j.status}">${escapeHtml(STATUS_LABEL[j.status] || j.status)}</span>`;
  $("#jobModalTitle").textContent = j.title || j.id;

  let html = "";

  if (j.parent_job_id) {
    html += `<div class="chain-banner">Continues job <button type="button" class="link-btn" id="openParentBtn">${escapeHtml(j.parent_job_id)}</button></div>`;
  }

  html += `<div class="meta-grid">
    ${metaItem("Job ID", j.id)}
    ${metaItem("Origin", j.origin_display || "")}
    ${scopeAll && me.is_admin ? metaItem("Owner", j.owner_display || j.owner || "") : ""}
    ${metaItem("Created", fmtTime(j.created_at))}
    ${metaItem("Completed", j.completed_at ? fmtTime(j.completed_at) : "")}
    ${metaItem("Rounds", j.resume_rounds ? String(j.resume_rounds) : "")}
  </div>`;

  // Tags are always shown in detail (even when empty) because this is where
  // the human can remove noisy auto-tags and add the vocabulary they want.
  html += `<div class="section-label">Tags</div>${editableTagsHtml(j)}`;

  const pending = j.slim ? "Loading\u2026" : "";
  html += `<div class="section-label">Instruction</div>
    <div class="section-body">${linkify(j.instruction || pending)}</div>`;

  if (j.input_attachments && j.input_attachments.length) {
    html += `<div class="section-label">Files you attached</div>`
      + fileListHtml(j.id, j.input_attachments);
  }

  if (j.pending_kind === "clarification") {
    const context = j.question_context
      ? `\n\n${escapeHtml(j.question_context)}`
      : "";
    html += `<div class="section-label">Waiting on you</div>
      <div class="question-box">${linkify(j.question || pending)}${context}</div>
      ${j.suggested_options && j.suggested_options.length ? `
        <div class="options-row">
          ${j.suggested_options.map((o) => `<button class="option-chip" data-opt="${escapeHtml(o)}">${escapeHtml(o)}</button>`).join("")}
        </div>` : ""}
      <label class="field-label" for="answerInput">Your clarification</label>
      <div class="compose-row">
        <textarea id="answerInput" class="input textarea" placeholder="Type or dictate your answer..."></textarea>
        <button class="mic-btn" data-mic-for="answerInput" title="Dictate" aria-label="Dictate clarification">&#127908;</button>
      </div>
      ${attachRowHtml("jobFilesInput")}
      <p class="hint">Sending this continues the same job. Drop job ends it and ignores this text.</p>
      <div class="action-row">
        <button class="btn btn-primary" id="answerBtn">Send clarification &amp; continue</button>
        <button class="btn btn-secondary" id="resubmitBtn">Resubmit as new job</button>
        <button class="btn btn-danger" id="dropBtn">Drop job</button>
      </div>`;
  } else if (j.pending_kind === "failure") {
    html += `<div class="section-label">What went wrong</div>
      <div class="section-body">${escapeHtml(j.last_failure_error || pending)}</div>
      <label class="field-label" for="answerInput">Optional extra input before retrying</label>
      <div class="compose-row">
        <textarea id="answerInput" class="input textarea" placeholder="Anything to add before retrying (optional)..."></textarea>
        <button class="mic-btn" data-mic-for="answerInput" title="Dictate" aria-label="Dictate extra input">&#127908;</button>
      </div>
      ${attachRowHtml("jobFilesInput")}
      <div class="action-row">
        <button class="btn btn-primary" id="continueBtn">Continue job</button>
        <button class="btn btn-secondary" id="resubmitBtn">Resubmit as new job</button>
        <button class="btn btn-danger" id="dropBtn">Drop job</button>
      </div>`;
  } else if (j.status === "done") {
    html += `<div class="section-label">Final reply</div>
      <div class="reply-box">${linkify(j.result || pending || "No final reply was recorded for this job.")}</div>`;
    if (j.artifacts && j.artifacts.length) {
      html += `<div class="section-label">Files produced</div>` + fileListHtml(j.id, j.artifacts);
    }
    html += `<div class="action-row">
        <button class="btn btn-primary" id="nextJobBtn">Next job</button>
      </div>`;
  } else if (j.status === "archived") {
    html += `<div class="section-label">Dropped</div>
      <div class="section-body">${fmtTime(j.dropped_at)}${j.drop_reason ? "\n" + escapeHtml(j.drop_reason) : ""}</div>
      <div class="action-row">
        <button class="btn btn-primary" id="startAgainBtn">Start again as new job</button>
      </div>`;
  } else {
    html += `<div class="section-label">Status</div>
      <div class="section-body">Still ${escapeHtml(STATUS_LABEL[j.status] || j.status)}. Refreshing every few seconds.</div>
      <div class="action-row">
        <button class="btn btn-secondary" id="resubmitBtn">Resubmit as new job</button>
        <button class="btn btn-danger" id="dropBtn">Drop job</button>
      </div>`;
  }

  if (j.events && j.events.length) {
    html += `<div class="section-label">History</div><div class="section-body">`
      + j.events.map((e) => `${fmtTime(e.created_at)} &mdash; ${escapeHtml(e.kind)}`).join("<br>")
      + `</div>`;
  }

  $("#jobModalBody").innerHTML = html;
  wireMicButtons($("#jobModal"));
  wireAttachControls($("#jobModal"));
  wireTagEditor(j);
  wireJobActions(j);
}

// Replace the cached job's tag list. Re-render the detail modal only when that
// exact job is the one currently open; list rows call renderList themselves.
function applyTagsUpdate(jobId, tags) {
  const current = jobsById.get(jobId);
  if (!current) return;
  upsertJob({ ...current, tags: Array.isArray(tags) ? tags : [] });
  if (activeJobId === jobId && !$("#jobModal").classList.contains("hidden")) {
    renderJob(jobsById.get(jobId));
  }
}

// Single tag-write path shared by the detail modal and list rows. The server
// returns the authoritative resulting tag list.
async function updateJobTag(jobId, action, tag) {
  const data = await apiPost(`/api/jobs/${jobId}/tags`, { action, tag });
  applyTagsUpdate(jobId, data.tags);
  return data;
}

// Wire the detail modal's tag editor: per-chip remove buttons, a classification
// selector, and the +/inline custom-text form.
function wireTagEditor(job) {
  const root = $("#jobModal");
  const addBtn = $("#addTagBtn");
  const wrap = $("#tagAddWrap");
  const typeSel = $("#tagAddType");
  const input = $("#tagAddInput");
  const saveBtn = $("#tagAddSave");
  const cancelBtn = $("#tagAddCancel");

  function showInput() {
    if (!wrap || !input) return;
    if (addBtn) addBtn.classList.add("hidden");
    wrap.classList.remove("hidden");
    if (typeSel) typeSel.value = "manual";
    syncTagInputForType(typeSel, input);
    input.value = "";
    input.focus();
  }

  function hideInput() {
    if (!wrap || !input) return;
    wrap.classList.add("hidden");
    input.value = "";
    if (addBtn) addBtn.classList.remove("hidden");
  }

  async function addTag() {
    const selected = typeSel ? typeSel.value : "manual";
    const raw = selected.startsWith("work:")
      ? selected
      : ((input && input.value) || "").trim();
    if (!raw) {
      showToast("Choose a classification or enter a tag");
      return;
    }
    if (saveBtn) saveBtn.disabled = true;
    try {
      await updateJobTag(job.id, "add", raw);
      showToast("Tag added");
    } catch (e) {
      showToast("Failed: " + e.message);
      if (saveBtn) saveBtn.disabled = false;
    }
  }

  if (addBtn) addBtn.onclick = showInput;
  if (saveBtn) saveBtn.onclick = addTag;
  if (cancelBtn) cancelBtn.onclick = hideInput;
  if (typeSel) typeSel.onchange = () => syncTagInputForType(typeSel, input);
  if (input) {
    input.onkeydown = (e) => {
      e.stopPropagation();
      if (e.key === "Enter") {
        e.preventDefault();
        addTag();
      } else if (e.key === "Escape") {
        e.preventDefault();
        hideInput();
      }
    };
  }

  root.querySelectorAll("[data-remove-tag]").forEach((btn) => {
    btn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const tag = btn.dataset.removeTag || "";
      if (!tag) return;
      btn.disabled = true;
      try {
        await updateJobTag(job.id, "remove", tag);
        showToast("Tag removed");
      } catch (err) {
        showToast("Failed: " + err.message);
        btn.disabled = false;
      }
    };
  });
}

// Wire the inline tag editor that lives inside a clickable list row. Every
// control stops click/key propagation so using tags never opens the job.
function wireRowTagEditor(row, job) {
  row.querySelectorAll(".list-tags button, .list-tags select, .list-tags input")
    .forEach((el) => el.addEventListener("click", (e) => e.stopPropagation()));

  const addBtn = row.querySelector("[data-row-add-tag]");
  const wrap = row.querySelector("[data-row-tag-wrap]");
  const typeSel = row.querySelector("[data-row-tag-type]");
  const input = row.querySelector("[data-row-tag-input]");
  const saveBtn = row.querySelector("[data-row-tag-save]");
  const cancelBtn = row.querySelector("[data-row-tag-cancel]");

  function showInput() {
    if (!wrap || !input) return;
    if (addBtn) addBtn.classList.add("hidden");
    wrap.classList.remove("hidden");
    if (typeSel) typeSel.value = "manual";
    syncTagInputForType(typeSel, input);
    input.value = "";
    input.focus();
  }

  function hideInput() {
    if (!wrap || !input) return;
    wrap.classList.add("hidden");
    input.value = "";
    if (addBtn) addBtn.classList.remove("hidden");
  }

  async function addTag() {
    const selected = typeSel ? typeSel.value : "manual";
    const raw = selected.startsWith("work:")
      ? selected
      : ((input && input.value) || "").trim();
    if (!raw) {
      showToast("Choose a classification or enter a tag");
      return;
    }
    if (saveBtn) saveBtn.disabled = true;
    try {
      await updateJobTag(job.id, "add", raw);
      renderList();
      showToast("Tag added");
    } catch (e) {
      showToast("Failed: " + e.message);
      if (saveBtn) saveBtn.disabled = false;
    }
  }

  if (addBtn) addBtn.onclick = (e) => { e.stopPropagation(); showInput(); };
  if (saveBtn) saveBtn.onclick = (e) => { e.stopPropagation(); addTag(); };
  if (cancelBtn) cancelBtn.onclick = (e) => { e.stopPropagation(); hideInput(); };
  if (typeSel) typeSel.onchange = () => syncTagInputForType(typeSel, input);
  if (input) {
    input.onkeydown = (e) => {
      e.stopPropagation();
      if (e.key === "Enter") {
        e.preventDefault();
        addTag();
      } else if (e.key === "Escape") {
        e.preventDefault();
        hideInput();
      }
    };
  }

  row.querySelectorAll("[data-row-remove-tag]").forEach((btn) => {
    btn.onclick = async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const tag = btn.dataset.rowRemoveTag || "";
      if (!tag) return;
      btn.disabled = true;
      try {
        await updateJobTag(job.id, "remove", tag);
        renderList();
        showToast("Tag removed");
      } catch (err) {
        showToast("Failed: " + err.message);
        btn.disabled = false;
      }
    };
  });
}

function wireJobActions(j) {
  const root = $("#jobModal");
  const answerInput = $("#answerInput");

  const openParentBtn = $("#openParentBtn");
  if (openParentBtn) openParentBtn.onclick = () => openJob(j.parent_job_id);

  root.querySelectorAll(".option-chip").forEach((btn) => {
    btn.onclick = () => {
      if (answerInput) {
        answerInput.value = btn.dataset.opt;
        answerInput.focus();
      }
    };
  });

  const answerBtn = $("#answerBtn");
  if (answerBtn) {
    answerBtn.onclick = async () => {
      const text = (answerInput.value || "").trim();
      if (!text) { showToast("Add your clarification first"); return; }
      const files = getPendingFiles("jobFilesInput");
      answerBtn.disabled = true;
      try {
        await apiPostForm(`/api/jobs/${j.id}/answer`, { text }, files);
        closeJob();
        showToast("Clarification sent â€” job continuing");
        invalidateLanes();
        setLane("working");
      } catch (e) {
        showToast("Failed: " + e.message);
      } finally {
        answerBtn.disabled = false;
      }
    };
  }

  const continueBtn = $("#continueBtn");
  if (continueBtn) {
    continueBtn.onclick = async () => {
      const files = getPendingFiles("jobFilesInput");
      continueBtn.disabled = true;
      try {
        await apiPostForm(`/api/jobs/${j.id}/continue`, {
          extra: (answerInput.value || "").trim(),
        }, files);
        closeJob();
        showToast("Job retrying");
        invalidateLanes();
        setLane("working");
      } catch (e) {
        showToast("Failed: " + e.message);
      } finally {
        continueBtn.disabled = false;
      }
    };
  }

  const resubmitBtn = $("#resubmitBtn");
  if (resubmitBtn) resubmitBtn.onclick = () => openComposer("resubmit", j);

  const nextJobBtn = $("#nextJobBtn");
  if (nextJobBtn) nextJobBtn.onclick = () => openComposer("chain", j);

  const startAgainBtn = $("#startAgainBtn");
  if (startAgainBtn) startAgainBtn.onclick = () => openComposer("resubmit", j);

  const dropBtn = $("#dropBtn");
  if (dropBtn) {
    dropBtn.onclick = async () => {
      if (!confirm("Drop this job? It will not run again.")) return;
      dropBtn.disabled = true;
      try {
        await apiPost(`/api/jobs/${j.id}/drop`, { reason: "dropped from board" });
        closeJob();
        showToast("Job dropped");
        invalidateLanes();
        loadLane(currentLane, { reset: true });
      } catch (e) {
        showToast("Failed: " + e.message);
      } finally {
        dropBtn.disabled = false;
      }
    };
  }
}

async function toggleRecording(btn, targetInput) {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    stopRecording();
    return;
  }
  if (!targetInput) return;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks = [];
    discardRecording = false;
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) recordedChunks.push(e.data);
    };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      btn.classList.remove("recording");
      if (discardRecording) {
        discardRecording = false;
        recordedChunks = [];
        return;
      }
      if (recordedChunks.length === 0) return;
      const blob = new Blob(recordedChunks, { type: "audio/webm" });

      // Composer fields use the durable background queue: persist the clip,
      // release the mic immediately, and let the worker transcribe it. This is
      // what lets the user hit Create while the transcript is still in flight.
      if (targetInput.id === "composerInstruction"
          || targetInput.id === "composerFeedback") {
        if (!composerDraftId) {
          showToast("Open the job form again to dictate");
          return;
        }
        await enqueueFormDictation(blob, targetInput.id, composerDraftId);
        showToast("Dictation queued \u2014 transcribing in background");
        return;
      }

      // Non-composer fields (job detail answer/retry) keep the original inline
      // behavior, but now show an explicit busy state while the request runs.
      btn.disabled = true;
      setButtonBusy(btn, true);
      showToast("Transcribing...");
      try {
        const form = new FormData();
        form.append("audio", blob, "audio.webm");
        const r = await fetch("/api/transcribe", {
          method: "POST",
          credentials: "include",
          body: form,
        });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(data.error || ("transcribe -> " + r.status));
        if (data.text) {
          targetInput.value = (targetInput.value ? targetInput.value + " " : "") + data.text;
        }
        showToast(data.text ? "Dictation added" : "No speech detected");
      } catch (e) {
        console.error(e);
        showToast("Transcription failed: " + e.message);
      } finally {
        setButtonBusy(btn, false);
        btn.disabled = false;
      }
    };
    mediaRecorder.start();
    btn.classList.add("recording");
  } catch (e) {
    showToast("Microphone access denied");
  }
}

function stopRecording(discard = false) {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    discardRecording = discard;
    mediaRecorder.stop();
  }
}

function wireMicButtons(root) {
  root.querySelectorAll("[data-mic-for]").forEach((btn) => {
    btn.onclick = () => toggleRecording(btn, document.getElementById(btn.dataset.micFor));
  });
}

// A native <input type="file"> only ever holds the files picked in its
// MOST RECENT dialog session -- clicking "Attach files" a second time to
// add one more file silently replaces the first selection, not adds to
// it. That is the exact bug reported live: attach two files across two
// clicks, submit, only the last one survives. Fixed by keeping our own
// running list per input id, keyed by id (not by element) since the job
// detail modal rebuilds its #jobFilesInput element on every re-render.
const pendingAttachments = new Map(); // inputId -> File[]

function getPendingFiles(inputId) {
  return pendingAttachments.get(inputId) || [];
}

function clearPendingFiles(inputId) {
  pendingAttachments.delete(inputId);
  renderAttachChips(inputId);
}

function renderAttachChips(inputId) {
  const chips = document.querySelector(`[data-attach-chips-for="${inputId}"]`);
  if (!chips) return;
  const files = getPendingFiles(inputId);
  if (!files.length) {
    chips.innerHTML = "";
    return;
  }
  chips.innerHTML = files.map((f, i) => `
    <span class="attach-chip">
      <span class="attach-chip-name">${escapeHtml(f.name)}</span>
      <button type="button" class="attach-chip-remove" data-remove-idx="${i}" aria-label="Remove ${escapeHtml(f.name)}">&times;</button>
    </span>`).join("");
  chips.querySelectorAll("[data-remove-idx]").forEach((btn) => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.removeIdx, 10);
      const list = getPendingFiles(inputId).slice();
      list.splice(idx, 1);
      pendingAttachments.set(inputId, list);
      renderAttachChips(inputId);
    };
  });
}

function wireAttachControls(root) {
  root.querySelectorAll("[data-attach-for]").forEach((btn) => {
    const input = document.getElementById(btn.dataset.attachFor);
    if (!input) return;
    const inputId = input.id;
    btn.onclick = () => input.click();
    input.onchange = () => {
      const picked = Array.from(input.files || []);
      if (picked.length) {
        const merged = getPendingFiles(inputId).slice();
        for (const f of picked) {
          // Same name+size picked twice (user re-opened the dialog and
          // selected the same file again) -- skip, don't double-attach.
          if (!merged.some((e) => e.name === f.name && e.size === f.size)) {
            merged.push(f);
          }
        }
        pendingAttachments.set(inputId, merged);
      }
      input.value = ""; // reset so picking the same file again still fires change
      renderAttachChips(inputId);
    };
    renderAttachChips(inputId); // show files already pending across a re-render
  });
}

function openComposer(mode = "new", job = null) {
  if (!$("#jobModal").classList.contains("hidden")) closeJob();
  composerMode = mode;
  composerJob = job;
  // A fresh draft id per opening. Any dictation recorded for an older draft is
  // ignored by this form even if its background transcription finishes later.
  composerDraftId = newDictationId();
  const resubmit = mode === "resubmit" && job;
  const chain = mode === "chain" && job;

  $("#composerKicker").textContent = chain ? `Next job, continuing ${job.id}`
    : resubmit ? `Resubmit ${job.id} as a new job`
    : "New job";
  $("#composerTitle").textContent = chain ? "What should Hermes do next?"
    : resubmit ? "Update the job and resubmit"
    : "What should Hermes do?";
  $("#composerInstruction").value = resubmit ? (job.instruction || "") : "";
  $("#composerInstruction").placeholder = chain
    ? "What's next, given the result below?"
    : "Describe the job, or tap the mic and dictate...";
  $("#composerFeedback").value = "";
  $("#composerFeedbackWrap").classList.toggle("hidden", !resubmit);

  $("#composerContextWrap").classList.toggle("hidden", !chain);
  if (chain) {
    $("#composerContextInstruction").innerHTML = linkify(job.instruction || "");
    $("#composerContextResult").innerHTML = linkify(job.result || "(no result recorded)");
  }

  $("#composerFilesInput").value = "";
  clearPendingFiles("composerFilesInput");
  refreshMicBusyForDraft(composerDraftId);

  composerSubmitLabel = chain ? "Create next job"
    : resubmit ? "Resubmit as new job"
    : "Create job";
  $("#composerSubmit").textContent = composerSubmitLabel;
  $("#composerHint").textContent = chain
    ? "Creates a new linked job. The previous job and its history stay untouched."
    : resubmit
    ? "This creates a fresh job. The original job and its history stay untouched."
    : "Runs in the background. Open the job later to read the final reply.";

  $("#composerModal").classList.remove("hidden");
  updateBodyLock();
  setTimeout(() => $("#composerInstruction").focus(), 60);
}

function closeComposer(options = {}) {
  const draftId = composerDraftId;
  stopRecording(true);
  composerMode = "new";
  composerJob = null;
  composerDraftId = null;
  composerSubmitLabel = "Create job";
  $("#composerSubmit").textContent = composerSubmitLabel;
  $("#composerModal").classList.add("hidden");
  updateBodyLock();
  // Explicit cancel/dismiss discards that draft's unfinished dictations. A
  // submission that is still waiting on transcription passes keepDictations
  // so the background worker can finish the job after the modal is gone.
  if (draftId && !options.keepDictations) {
    discardDraftDictations(draftId);
  }
  clearMicBusy();
}

async function submitComposer() {
  const instruction = ($("#composerInstruction").value || "").trim();
  const feedback = ($("#composerFeedback").value || "").trim();
  const btn = $("#composerSubmit");

  const wasResubmit = composerMode === "resubmit";
  const wasChain = composerMode === "chain";
  const draftId = composerDraftId;
  const files = getPendingFiles("composerFilesInput");
  const draftDictations = draftId ? formDictationsForDraft(draftId) : [];
  const failed = draftDictations.filter((i) => i.status === "failed");
  const pending = draftDictations.filter(
    (i) => i.status === "queued" || i.status === "transcribing"
  );

  // A failed clip needs a human decision (retry or discard) before we can know
  // what text belongs in the job. Do not silently submit without it.
  if (failed.length) {
    openDictationQueue();
    showToast("A dictation failed \u2014 retry or discard it before submitting");
    return;
  }

  // The instruction may be empty because the user dictated it and the
  // transcript is still in flight. That is valid: the queued submission will
  // fill it in when transcription completes. Only block when there is neither
  // manual text nor a pending dictation targeting the instruction field.
  const hasPendingInstruction = pending.some(
    (item) => item.targetField === "composerInstruction"
  );
  if (!instruction && !hasPendingInstruction) {
    showToast(composerMode === "chain" ? "Describe what's next first" : "Describe the job first");
    return;
  }

  // Submit while a clip is still transcribing: persist the whole submission
  // (fields + attachments + which dictations to wait for) and close the form
  // immediately. The background worker appends the transcript(s) and creates
  // the job as soon as they are ready.
  if (pending.length) {
    // Freeze these clips for the submission. If a transcript arrives in the
    // tiny window before the modal closes, it must not be appended to the live
    // textarea (the submission already captured an earlier fields snapshot);
    // the background submission worker will append it to its own copy instead.
    pending.forEach((item) => {
      item.submissionQueued = true;
      dictPut(item).catch(() => {});
    });
    await enqueueFormSubmission({
      draftId,
      fields: {
        instruction,
        feedback,
        mode: composerMode,
        parent_job_id: wasChain && composerJob ? composerJob.id : null,
      },
      files,
      dictationIds: pending.map((i) => i.id),
    });
    closeComposer({ keepDictations: true });
    showToast("Job queued \u2014 will submit when dictation is ready");
    return;
  }

  let body = instruction;
  if (wasResubmit && feedback) {
    body += "\n\nAdditional feedback / changes requested:\n" + feedback;
  }

  const fields = { instruction: body };
  if (wasChain && composerJob) fields.parent_job_id = composerJob.id;

  btn.disabled = true;
  try {
    await apiPostForm("/api/jobs", fields, files);
    if (draftId) clearDraftDictations(draftId);
    closeComposer({ keepDictations: true });
    showToast(wasChain ? "Next job queued" : wasResubmit ? "New job created from your changes" : "Job queued");
    invalidateLanes();
    setLane("working");
  } catch (e) {
    showToast("Failed: " + e.message);
  } finally {
    btn.disabled = false;
  }
}

function updateBodyLock() {
  const open = !$("#jobModal").classList.contains("hidden")
    || !$("#composerModal").classList.contains("hidden")
    || !$("#voiceOverlay").classList.contains("hidden")
    || !$("#dictationQueueModal").classList.contains("hidden");
  document.body.classList.toggle("modal-open", open);
}

// ---------------------------------------------------------------------------
// Dictation queue: durable (IndexedDB) so a recorded clip survives a
// reload/backgrounded-tab kill, and processed in the background so
// "New job by voice" never makes the next recording wait on a network
// round trip. See runDictationItem for the actual upload.
// ---------------------------------------------------------------------------

const DICT_DB_NAME = "hermes-jobs-dictation";
const DICT_DB_VERSION = 1;
const DICT_STORE = "queue";
const DICTATION_CONCURRENCY = 2;

let dictDbPromise = null;
function dictDb() {
  if (dictDbPromise) return dictDbPromise;
  dictDbPromise = new Promise((resolve, reject) => {
    if (!("indexedDB" in window)) { reject(new Error("IndexedDB unavailable")); return; }
    const req = indexedDB.open(DICT_DB_NAME, DICT_DB_VERSION);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(DICT_STORE)) {
        req.result.createObjectStore(DICT_STORE, { keyPath: "id" });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dictDbPromise;
}

function dictPut(item) {
  return dictDb().then((db) => new Promise((resolve, reject) => {
    const tx = db.transaction(DICT_STORE, "readwrite");
    tx.objectStore(DICT_STORE).put(item);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  }));
}

function dictDelete(id) {
  return dictDb().then((db) => new Promise((resolve, reject) => {
    const tx = db.transaction(DICT_STORE, "readwrite");
    tx.objectStore(DICT_STORE).delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  }));
}

function dictGetAll() {
  return dictDb().then((db) => new Promise((resolve, reject) => {
    const tx = db.transaction(DICT_STORE, "readonly");
    const req = tx.objectStore(DICT_STORE).getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  }));
}

// One durable queue now carries three item kinds:
//   voice          -- the original "New job by voice" clip
//   form_dictation -- one clip recorded into a composer field
//   form_submit    -- a composer submission waiting on one or more dictations
//
// id -> item. Common fields: id, kind, createdAt, status, error, jobId.
// Voice items also carry blob. Form dictation items carry blob, draftId,
// targetField, text, appliedToDraft. Form submit items carry draftId, fields,
// files, dictationIds, idempotencyKey. "done" items are deleted from
// IndexedDB as soon as their job exists, then kept in this map briefly so the
// panel can show a confirmation.
const dictationQueue = new Map();
let dictationRunning = 0;

// Join two pieces of dictated/manual text with exactly one separating space.
function dictationTextJoin(left, right) {
  const a = String(left || "").trim();
  const b = String(right || "").trim();
  if (!a) return b;
  if (!b) return a;
  return a + " " + b;
}

// All form dictation clips recorded for one composer session.
function formDictationsForDraft(draftId) {
  if (!draftId) return [];
  return Array.from(dictationQueue.values()).filter(
    (item) => item.kind === "form_dictation" && item.draftId === draftId
  );
}

// A clip is "pending" while the user may still submit before its transcript
// arrives. Transcribed clips already applied to the textarea are not pending.
function formDictationIsPending(item) {
  return item.status === "queued" || item.status === "transcribing";
}

// A waiting form submission can start only after every referenced clip has a
// transcript. Missing ids mean the user discarded that clip; failed clips make
// the submission runnable so it can surface the failure instead of hanging.
function formSubmissionIsReady(item) {
  const ids = item.dictationIds || [];
  for (const id of ids) {
    const dict = dictationQueue.get(id);
    if (!dict) continue;
    if (dict.status === "failed") return true;
    if (dict.status !== "transcribed") return false;
  }
  return true;
}

// Queue-panel visibility. A transcribed clip already appended to the open
// composer is part of the draft and does not need a queue row; it stays in
// IndexedDB until the job is submitted or the draft is cancelled.
function visibleDictationItems() {
  return Array.from(dictationQueue.values()).filter(
    (item) => !(item.kind === "form_dictation"
      && item.status === "transcribed"
      && item.appliedToDraft)
  );
}

function updateDictationBadge() {
  const badge = $("#dictationQueueBadge");
  if (!badge) return;
  const items = visibleDictationItems();
  badge.textContent = String(items.length);
  badge.classList.toggle("hidden", items.length === 0);
  badge.classList.toggle("dictation-badge-failed", items.some((i) => i.status === "failed"));
}

// Put a visible "Transcribing..." status next to one mic button and pulse the
// button itself. The status span is created on demand so the same helper works
// for static composer fields and dynamically rebuilt job-detail fields.
function setButtonBusy(btn, busy) {
  if (!btn) return;
  btn.classList.toggle("transcribing", busy);
  btn.setAttribute("aria-busy", busy ? "true" : "false");
  const row = btn.closest(".compose-row") || btn.parentElement;
  if (!row) return;
  let status = row.querySelector(".mic-status");
  if (!status) {
    status = document.createElement("span");
    status.className = "mic-status";
    row.appendChild(status);
  }
  status.textContent = busy ? "Transcribing\u2026" : "";
}

// Toggle busy state for every mic targeting one input id.
function setMicBusyForField(targetField, busy) {
  document.querySelectorAll(`[data-mic-for="${targetField}"]`).forEach((btn) => {
    setButtonBusy(btn, busy);
  });
}

// Recompute composer mic busy states from the durable queue. This is called
// after enqueue, transcription success/failure, restore and form close, so the
// indicator always reflects the real background work rather than a timer.
function refreshMicBusyForDraft(draftId) {
  const pendingFields = new Set();
  if (draftId && isComposerDraftOpen(draftId)) {
    for (const item of formDictationsForDraft(draftId)) {
      if (formDictationIsPending(item)) pendingFields.add(item.targetField);
    }
  }
  setMicBusyForField("composerInstruction", pendingFields.has("composerInstruction"));
  setMicBusyForField("composerFeedback", pendingFields.has("composerFeedback"));
}

function clearMicBusy() {
  setMicBusyForField("composerInstruction", false);
  setMicBusyForField("composerFeedback", false);
}

function isComposerDraftOpen(draftId) {
  return Boolean(
    draftId
    && composerDraftId === draftId
    && !$("#composerModal").classList.contains("hidden")
  );
}

// Append a finished transcript to its original composer field. Returns false
// when that field is no longer on screen (form closed/replaced), in which case
// a pending submission worker will use the stored text instead.
function appendTextToComposerField(targetField, text) {
  const input = document.getElementById(targetField);
  if (!input || !text) return false;
  input.value = dictationTextJoin(input.value, text);
  return true;
}

// Remove all form-dictation records for a draft. Used after a successful
// normal submit and when the user explicitly cancels the composer.
function clearDraftDictations(draftId) {
  for (const item of formDictationsForDraft(draftId)) {
    dictationQueue.delete(item.id);
    dictDelete(item.id).catch(() => {});
  }
  renderDictationQueue();
  refreshMicBusyForDraft(draftId);
}

// Cancel a draft's clips, but never delete one that a queued form submission
// still references (that submission is already committed to running).
function discardDraftDictations(draftId) {
  const referenced = new Set();
  for (const item of dictationQueue.values()) {
    if (item.kind === "form_submit" && item.draftId === draftId) {
      (item.dictationIds || []).forEach((id) => referenced.add(id));
    }
  }
  for (const item of formDictationsForDraft(draftId)) {
    if (referenced.has(item.id)) continue;
    dictationQueue.delete(item.id);
    dictDelete(item.id).catch(() => {});
  }
  renderDictationQueue();
  refreshMicBusyForDraft(draftId);
}

const DICT_STATUS_META = {
  queued: { label: "Queued", pill: "status-ready" },
  transcribing: { label: "Transcribing\u2026", pill: "status-running" },
  transcribed: { label: "Dictation ready", pill: "status-done" },
  uploading: { label: "Processing\u2026", pill: "status-running" },
  waiting: { label: "Waiting for dictation\u2026", pill: "status-ready" },
  submitting: { label: "Creating job\u2026", pill: "status-running" },
  done: { label: "Done", pill: "status-done" },
  failed: { label: "Failed", pill: "status-review" },
};

function dictationItemHtml(item) {
  const meta = DICT_STATUS_META[item.status] || { label: item.status, pill: "" };
  const kindLabel = item.kind === "form_submit" ? "Form job"
    : item.kind === "form_dictation" ? "Form dictation"
    : "Voice job";
  let extra = "";
  if (item.status === "done" && item.jobId) {
    extra = `<button class="link-btn dict-open-job" data-open-job="${item.jobId}">Open job &rsaquo;</button>`;
  } else if (item.status === "failed") {
    extra = `<div class="section-body dict-error">${escapeHtml(item.error || "Unknown error")}</div>
      <div class="action-row">
        <button class="btn btn-primary" data-retry-dict="${item.id}">Retry</button>
        <button class="btn btn-secondary" data-discard-dict="${item.id}">Discard</button>
      </div>`;
  } else if (item.kind === "form_dictation" && item.status === "transcribed"
             && !item.appliedToDraft) {
    // A recovered/orphaned clip: show what was transcribed and let the user
    // discard it if the original form is no longer open.
    extra = `<div class="section-body dict-error">${escapeHtml(item.text || "")}</div>
      <div class="action-row">
        <button class="btn btn-secondary" data-discard-dict="${item.id}">Discard</button>
      </div>`;
  } else if (item.kind === "form_submit" && item.status === "waiting") {
    extra = `<div class="section-body">Waiting for the dictation transcript before creating the job.</div>`;
  } else if (item.kind === "form_dictation" && item.status === "transcribing") {
    extra = `<div class="section-body">Transcribing your clip\u2026</div>`;
  }
  return `<div class="dict-item">
    <div class="dict-item-head">
      <span class="pill ${meta.pill}">${meta.label}</span>
      <span class="dict-item-time">${kindLabel} &middot; ${fmtTime(Math.floor((item.createdAt || 0) / 1000))}</span>
    </div>
    ${extra}
  </div>`;
}

function renderDictationQueue() {
  updateDictationBadge();
  const modal = $("#dictationQueueModal");
  if (modal.classList.contains("hidden")) return;
  const body = $("#dictationQueueBody");
  const items = visibleDictationItems().sort((a, b) => b.createdAt - a.createdAt);
  if (!items.length) {
    body.innerHTML = `<p class="empty">No dictated jobs in the queue.</p>`;
    return;
  }
  body.innerHTML = items.map(dictationItemHtml).join("");
  body.querySelectorAll("[data-retry-dict]").forEach((btn) => {
    btn.onclick = () => retryDictationItem(btn.dataset.retryDict);
  });
  body.querySelectorAll("[data-discard-dict]").forEach((btn) => {
    btn.onclick = () => discardDictationItem(btn.dataset.discardDict);
  });
  body.querySelectorAll("[data-open-job]").forEach((btn) => {
    btn.onclick = () => { closeDictationQueue(); openJob(btn.dataset.openJob); };
  });
}

function openDictationQueue() {
  toggleFab(false);
  $("#dictationQueueModal").classList.remove("hidden");
  updateBodyLock();
  renderDictationQueue();
}

function closeDictationQueue() {
  $("#dictationQueueModal").classList.add("hidden");
  updateBodyLock();
}

function newDictationId() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  return "dict-" + Date.now() + "-" + Math.random().toString(36).slice(2);
}

// Writes the blob to IndexedDB FIRST, then returns -- the caller (Stop
// button) releases the UI the instant this resolves, which is the whole
// point: the next recording can start before this one has even begun
// uploading.
async function enqueueDictation(blob) {
  const item = {
    kind: "voice",
    id: newDictationId(), createdAt: Date.now(), status: "queued",
    error: null, jobId: null, blob,
  };
  dictationQueue.set(item.id, item);
  // Await the IndexedDB write before the caller releases the UI. That closes
  // the race where a user backgrounds the tab immediately after Stop and the
  // only copy of the clip was still in memory.
  try {
    await dictPut(item);
  } catch (e) {
    console.error("dictation queue: persist failed", e);
    showToast("Could not save the clip locally \u2014 keep this tab open");
  }
  renderDictationQueue();
  pumpDictationQueue();
}

// Persist one form-field recording before any network call. The blob, draft id
// and target field are all in IndexedDB, so a reload or disconnect cannot lose
// the clip. The background worker transcribes it and appends the text to the
// same textarea if that draft is still open.
async function enqueueFormDictation(blob, targetField, draftId) {
  const item = {
    kind: "form_dictation",
    id: newDictationId(),
    draftId,
    targetField,
    createdAt: Date.now(),
    status: "queued",
    error: null,
    text: "",
    appliedToDraft: false,
    blob,
  };
  dictationQueue.set(item.id, item);
  try {
    await dictPut(item);
  } catch (e) {
    console.error("form dictation: persist failed", e);
    showToast("Could not save the dictation locally \u2014 keep this tab open");
  }
  renderDictationQueue();
  refreshMicBusyForDraft(draftId);
  pumpDictationQueue();
}

// Persist a complete form submission while its dictation is still in flight.
// The fields/files snapshot is everything needed to create the job later; the
// dictationIds list is what the worker waits on before appending transcripts.
async function enqueueFormSubmission({ draftId, fields, files, dictationIds }) {
  const id = newDictationId();
  const item = {
    kind: "form_submit",
    id,
    draftId,
    createdAt: Date.now(),
    status: "waiting",
    error: null,
    jobId: null,
    fields,
    files: files || [],
    dictationIds: dictationIds || [],
    idempotencyKey: "form-" + id,
  };
  dictationQueue.set(item.id, item);
  try {
    await dictPut(item);
  } catch (e) {
    console.error("form submission: persist failed", e);
    showToast("Could not save the pending job locally \u2014 keep this tab open");
  }
  renderDictationQueue();
  pumpDictationQueue();
}

// The pump can start three kinds of work. A waiting form submission is only
// runnable once every referenced clip has a transcript (or has been discarded),
// which is what makes "submit while transcribing" non-blocking but ordered.
function isRunnableDictationItem(item) {
  if (item.kind === "form_submit") {
    return item.status === "waiting" && formSubmissionIsReady(item);
  }
  return item.status === "queued";
}

function pumpDictationQueue() {
  while (dictationRunning < DICTATION_CONCURRENCY) {
    const next = Array.from(dictationQueue.values())
      .filter(isRunnableDictationItem)
      .sort((a, b) => a.createdAt - b.createdAt)[0];
    if (!next) break;

    if (next.kind === "form_submit") next.status = "submitting";
    else if (next.kind === "form_dictation") next.status = "transcribing";
    else next.status = "uploading";

    dictPut(next).catch(() => {});
    dictationRunning++;
    renderDictationQueue();
    if (next.kind === "form_dictation") refreshMicBusyForDraft(next.draftId);

    const runner = next.kind === "form_submit" ? runFormSubmissionItem
      : next.kind === "form_dictation" ? runFormDictationItem
      : runDictationItem;
    runner(next).finally(() => {
      dictationRunning--;
      pumpDictationQueue();
    });
  }
}

async function runDictationItem(item) {
  try {
    const form = new FormData();
    form.append("audio", item.blob, "audio.webm");
    const r = await fetch(
      "/api/jobs/from-dictation?idempotency_key=" + encodeURIComponent(item.id),
      { method: "POST", credentials: "include", body: form },
    );
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || ("from-dictation -> " + r.status));
    // The user may have discarded this row while the request was in flight.
    // Do not resurrect a deleted item by writing it back to IndexedDB.
    if (dictationQueue.get(item.id) !== item) return;
    item.status = "done";
    item.jobId = data.job.id;
    item.error = null;
    await dictDelete(item.id).catch(() => {});
    renderDictationQueue();
    invalidateLanes();
    if (currentLane === "working") loadLane("working", { reset: true });
    showToast("Voice job created");
    setTimeout(() => {
      dictationQueue.delete(item.id);
      renderDictationQueue();
    }, 4000);
  } catch (e) {
    if (dictationQueue.get(item.id) !== item) return;
    item.status = "failed";
    item.error = e.message || String(e);
    dictPut(item).catch(() => {});
    renderDictationQueue();
    showToast("A dictated job failed \u2014 check the queue");
  }
}

// Transcribe one form clip in the background. On success the text is appended
// to the live composer if the same draft is still open; otherwise it remains in
// the queue for a waiting form submission to consume. No job is created here.
async function runFormDictationItem(item) {
  try {
    const form = new FormData();
    form.append("audio", item.blob, "audio/webm");
    const r = await fetch("/api/transcribe", {
      method: "POST",
      credentials: "include",
      body: form,
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || ("transcribe -> " + r.status));
    const text = (data.text || "").trim();
    if (!text) throw new Error("No speech detected");
    if (dictationQueue.get(item.id) !== item) return;

    item.text = text;
    item.status = "transcribed";
    item.error = null;
    if (isComposerDraftOpen(item.draftId) && !item.submissionQueued) {
      item.appliedToDraft = appendTextToComposerField(item.targetField, text);
    }
    dictPut(item).catch(() => {});
    renderDictationQueue();
    refreshMicBusyForDraft(item.draftId);
    pumpDictationQueue(); // release any submission waiting on this clip
    showToast(item.appliedToDraft ? "Dictation added" : "Dictation ready");
  } catch (e) {
    if (dictationQueue.get(item.id) !== item) return;
    item.status = "failed";
    item.error = e.message || String(e);
    dictPut(item).catch(() => {});
    renderDictationQueue();
    refreshMicBusyForDraft(item.draftId);
    showToast("Dictation failed \u2014 check the queue");
  }
}

// Create the job for a form submission after its transcript(s) are available.
// Transcripts already applied to the textarea are skipped because the captured
// fields snapshot already contains them; pending clips are appended now.
async function runFormSubmissionItem(item) {
  try {
    const dictations = (item.dictationIds || [])
      .map((id) => dictationQueue.get(id))
      .filter(Boolean);
    const failed = dictations.find((d) => d.status === "failed");
    if (failed) {
      throw new Error("A dictation failed: " + (failed.error || "unknown error"));
    }

    let instruction = (item.fields && item.fields.instruction) || "";
    let feedback = (item.fields && item.fields.feedback) || "";
    for (const dict of dictations) {
      if (dict.appliedToDraft) continue;
      const text = (dict.text || "").trim();
      if (!text) continue;
      if (dict.targetField === "composerFeedback") {
        feedback = dictationTextJoin(feedback, text);
      } else {
        instruction = dictationTextJoin(instruction, text);
      }
    }
    if (!instruction) throw new Error("No job instruction after dictation");

    let body = instruction;
    if (item.fields && item.fields.mode === "resubmit" && feedback) {
      body += "\n\nAdditional feedback / changes requested:\n" + feedback;
    }
    const payload = {
      instruction: body,
      idempotency_key: item.idempotencyKey,
    };
    if (item.fields && item.fields.mode === "chain" && item.fields.parent_job_id) {
      payload.parent_job_id = item.fields.parent_job_id;
    }

    const data = await apiPostForm("/api/jobs", payload, item.files || []);
    // If the user discarded this submission while the request was in flight,
    // still delete the persisted row but do not resurrect/announce it.
    if (dictationQueue.get(item.id) !== item) return;
    item.status = "done";
    item.jobId = data.job.id;
    item.error = null;

    // The submission and its source clips have become a real job; nothing is
    // left worth persisting. Keep the done row in memory briefly for the panel.
    for (const dict of dictations) {
      dictationQueue.delete(dict.id);
      dictDelete(dict.id).catch(() => {});
    }
    dictDelete(item.id).catch(() => {});
    renderDictationQueue();
    invalidateLanes();
    if (currentLane === "working") loadLane("working", { reset: true });
    showToast("Dictated job created");
    setTimeout(() => {
      dictationQueue.delete(item.id);
      renderDictationQueue();
    }, 4000);
  } catch (e) {
    if (dictationQueue.get(item.id) !== item) return;
    item.status = "failed";
    item.error = e.message || String(e);
    dictPut(item).catch(() => {});
    renderDictationQueue();
    showToast("A dictated form job failed \u2014 check the queue");
  }
}

function retryDictationItem(id) {
  const item = dictationQueue.get(id);
  if (!item) return;
  if (item.kind === "form_submit") {
    item.status = "waiting";
    // Retrying a failed submission also retries any clip that caused it to
    // fail; otherwise the pump would immediately fail the submission again.
    for (const dictId of item.dictationIds || []) {
      const dict = dictationQueue.get(dictId);
      if (dict && dict.status === "failed") {
        dict.status = "queued";
        dict.error = null;
        dict.text = "";
        dictPut(dict).catch(() => {});
      }
    }
  } else {
    item.status = "queued";
    if (item.kind === "form_dictation") item.text = "";
  }
  item.error = null;
  dictPut(item).catch(() => {});
  renderDictationQueue();
  refreshMicBusyForDraft(item.draftId);
  pumpDictationQueue();
}

function discardDictationItem(id) {
  const item = dictationQueue.get(id);
  if (!item) return;
  dictationQueue.delete(id);
  dictDelete(id).catch(() => {});

  if (item.kind === "form_submit") {
    // Discarding a whole submission also discards the clips it was waiting on.
    for (const dictId of item.dictationIds || []) {
      dictationQueue.delete(dictId);
      dictDelete(dictId).catch(() => {});
    }
  } else if (item.kind === "form_dictation") {
    // A waiting submission should proceed without a clip the user discarded.
    for (const other of dictationQueue.values()) {
      if (other.kind === "form_submit" && (other.dictationIds || []).includes(id)) {
        other.dictationIds = other.dictationIds.filter((x) => x !== id);
        dictPut(other).catch(() => {});
      }
    }
  }
  renderDictationQueue();
  refreshMicBusyForDraft(item.draftId);
  pumpDictationQueue();
}

async function restoreDictationQueue() {
  try {
    const rows = await dictGetAll();
    for (const item of rows) {
      if (!item.kind) item.kind = "voice";
      // In-flight states are never trustworthy after a reload: the request
      // that set them died with the old page. Put them back in a runnable state.
      if (item.status === "uploading") item.status = "queued";
      if (item.status === "transcribing") item.status = "queued";
      if (item.status === "submitting") item.status = "waiting";
      // The composer DOM is gone after a reload, so no transcript can still be
      // considered "already applied"; a waiting submission must consume it.
      if (item.kind === "form_dictation") item.appliedToDraft = false;
      dictationQueue.set(item.id, item);
    }
    renderDictationQueue();
    pumpDictationQueue();
  } catch (e) {
    console.warn("dictation queue: restore failed (IndexedDB unavailable?)", e);
  }
}

// ---------------------------------------------------------------------------
// FAB: "+ New job" speed-dial (form, or voice-only instant submit)
// ---------------------------------------------------------------------------

function toggleFab(open) {
  fabOpen = open === undefined ? !fabOpen : open;
  $("#fabMenu").classList.toggle("hidden", !fabOpen);
  $("#fabMainBtn").setAttribute("aria-expanded", String(fabOpen));
  $("#fabMainBtn").classList.toggle("fab-main-open", fabOpen);
}

// Voice-only job: tap, dictate, stop -- creates the job immediately from
// the (cleaned-up) transcript with no form and no review step. "New job by
// form" below is the deliberate, editable alternative for when the words
// need checking before they go in.
async function startVoiceOnlyJob() {
  const overlay = $("#voiceOverlay");
  const status = $("#voiceOverlayStatus");
  const stopBtn = $("#voiceStopBtn");
  const cancelBtn = $("#voiceCancelBtn");

  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (e) {
    showToast("Microphone access denied");
    return;
  }

  overlay.classList.remove("hidden");
  updateBodyLock();
  status.textContent = "Listeningâ€¦ tap stop when done.";
  $("#voicePulse").classList.remove("thinking");
  stopBtn.disabled = false;
  cancelBtn.disabled = false;

  const chunks = [];
  let cancelled = false;
  const recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
  const stopped = new Promise((resolve) => {
    recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      resolve();
    };
  });

  cancelBtn.onclick = async () => {
    cancelled = true;
    cancelBtn.disabled = true;
    stopBtn.disabled = true;
    recorder.stop();
    await stopped;
    overlay.classList.add("hidden");
    updateBodyLock();
  };

  // Stop hands the clip to the durable queue and releases the UI
  // IMMEDIATELY -- nothing here waits on a network round trip, so the
  // next recording can start before this one has even begun uploading.
  // Transcription, cleanup, and job creation all happen in the
  // background (runDictationItem); failures surface in the queue panel
  // with a Retry button that resubmits this SAME blob, no re-dictating.
  stopBtn.onclick = async () => {
    stopBtn.disabled = true;
    cancelBtn.disabled = true;
    recorder.stop();
    await stopped;
    overlay.classList.add("hidden");
    updateBodyLock();
    if (cancelled) return;
    if (!chunks.length) {
      showToast("No audio captured");
      return;
    }
    await enqueueDictation(new Blob(chunks, { type: "audio/webm" }));
    showToast("Added to queue \u2014 processing in background");
  };

  recorder.start();
}

async function init() {
  // Resolve the signed-in identity before the first lane load. A failure here
  // is non-fatal: the list endpoint still applies the safe My-jobs default, and
  // the All-jobs control simply stays hidden.
  try {
    me = await apiGet("/api/whoami");
  } catch (e) {
    console.error("whoami failed", e);
  }
  const scopeBar = $("#scopeBar");
  if (me && me.is_admin && scopeBar) {
    scopeBar.classList.remove("hidden");
  }
  const scopeMine = $("#scopeMine");
  const scopeAllBtn = $("#scopeAll");
  if (scopeMine) scopeMine.onclick = () => setScope(false);
  if (scopeAllBtn) scopeAllBtn.onclick = () => setScope(true);
  const ownerLeft = $("#ownerScrollLeft");
  const ownerRight = $("#ownerScrollRight");
  if (ownerLeft) ownerLeft.onclick = () => scrollOwnerChips(-1);
  if (ownerRight) ownerRight.onclick = () => scrollOwnerChips(1);

  $$(".tab").forEach((tab) => {
    tab.onclick = () => setLane(tab.dataset.lane);
  });

  $("#refreshBtn").onclick = manualRefresh;

  // Search is debounced so a fast typist fires one query, not twelve.
  // It runs server-side across every job, not just the loaded pages.
  const searchInput = $("#searchInput");
  searchInput.addEventListener("input", () => {
    $("#searchClear").classList.toggle("hidden", !searchInput.value);
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
      const next = searchInput.value.trim();
      if (next === filterState.q) return;
      filterState.q = next;
      applyFilters();
    }, 300);
  });
  searchInput.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    e.stopPropagation();
    if (searchInput.value) {
      searchInput.value = "";
      $("#searchClear").classList.add("hidden");
      filterState.q = "";
      applyFilters();
    }
  });
  $("#searchClear").onclick = () => {
    searchInput.value = "";
    $("#searchClear").classList.add("hidden");
    filterState.q = "";
    applyFilters();
    searchInput.focus();
  };

  // Wire only the actual date chips. The scope chips (My jobs / All jobs) are
  // wired separately above; including them here used to overwrite their
  // handlers with setDayFilter(undefined), which made the scope switch appear
  // to do nothing and removed its active highlight.
  $$(".day-chip[data-day]").forEach((chip) => {
    chip.onclick = () => setDayFilter(chip.dataset.day);
  });
  $("#datePick").onchange = (e) => {
    if (e.target.value) setDayFilter("date", e.target.value);
    else setDayFilter("all");
  };
  $("#clearFilters").onclick = clearFilters;
  $("#composerCancel").onclick = closeComposer;
  $("#composerSubmit").onclick = submitComposer;

  $("#fabMainBtn").onclick = () => toggleFab();
  $("#fabFormBtn").onclick = () => { toggleFab(false); openComposer("new"); };
  $("#fabVoiceBtn").onclick = () => { toggleFab(false); startVoiceOnlyJob(); };

  $$("[data-close-modal]").forEach((el) => {
    el.onclick = () => {
      const modal = el.closest(".modal");
      if (!modal) return;
      if (modal.id === "jobModal") closeJob();
      else if (modal.id === "dictationQueueModal") closeDictationQueue();
      else closeComposer();
    };
  });

  $("#dictationQueueBadge").onclick = (e) => {
    e.stopPropagation();
    openDictationQueue();
  };

  wireAttachControls(document);

  ["composerInstruction", "composerFeedback"].forEach((id) => {
    document.getElementById(id).addEventListener("keydown", (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        submitComposer();
      }
    });
  });

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (fabOpen) { toggleFab(false); return; }
    if (!$("#dictationQueueModal").classList.contains("hidden")) {
      closeDictationQueue();
    } else if (!$("#composerModal").classList.contains("hidden")) {
      closeComposer();
    } else if (!$("#jobModal").classList.contains("hidden")) {
      closeJob();
    }
  });

  document.addEventListener("click", (e) => {
    if (!fabOpen) return;
    if ($("#fabWrap").contains(e.target)) return;
    toggleFab(false);
  });

  wireMicButtons(document);
  loadLane(currentLane, { reset: true });
  restoreDictationQueue();
  pollTimer = setInterval(pollTick, 5000);

  // Infinite scroll: the sentinel sits under the list, so it only comes
  // into view once the user has reached the bottom of the loaded pages.
  const sentinel = $("#scrollSentinel");
  if (sentinel && "IntersectionObserver" in window) {
    new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) loadLane(currentLane);
    }, { rootMargin: "400px" }).observe(sentinel);
  }

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js", { updateViaCache: "none" }).catch(() => {});
  }
}

document.addEventListener("DOMContentLoaded", init);


