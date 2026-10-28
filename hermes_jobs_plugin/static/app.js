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

let activeJobId = null;
let sheetSignature = "";
let pollTimer = null;
let toastTimer = null;
let mediaRecorder = null;
let recordedChunks = [];
let discardRecording = false;
let composerMode = "new";
let composerJob = null;
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

async function apiGet(path) {
  const r = await fetch(path, { credentials: "include" });
  if (!r.ok) throw new Error("GET " + path + " -> " + r.status);
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

async function loadLane(lane, opts = {}) {
  const st = laneState[lane];
  if (st.loading) return;
  if (!opts.reset && st.done && st.loaded) return;
  st.loading = true;
  updateSentinel();
  try {
    const qs = new URLSearchParams({ lane, limit: String(PAGE_SIZE) });
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
      const data = await apiGet("/api/jobs?lane=" + currentLane + "&limit=1");
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
    await loadLane(currentLane, { reset: true });
    showToast("Jobs updated");
  } finally {
    icon.classList.remove("spinning");
    btn.disabled = false;
  }
}

function setLane(lane) {
  currentLane = lane;
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.lane === lane));
  renderList();
  window.scrollTo({ top: 0 });
  if (!laneState[lane].loaded) loadLane(lane, { reset: true });
}

function jobSignature(j) {
  return [
    j.status, j.pending_kind, j.result, j.question, j.question_context,
    j.last_failure_error, j.completed_at, j.dropped_at, j.resume_rounds,
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
      : currentLane === "needs_you"
      ? "Nothing needs you right now."
      : "No jobs here.";
    list.appendChild(p);
    updateSentinel();
    return;
  }
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
    </div>
    <div class="job-detail">
      <div class="job-detail-text">${escapeHtml(j.snippet || "")}</div>
    </div>
    <div class="job-origin">${escapeHtml(j.origin_display || "")}</div>
    <div class="job-time">${fmtTime(j.created_at)}</div>
    <div class="job-actions"><span class="row-open">Open &rsaquo;</span></div>
  `;
  return row;
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
    ${metaItem("Created", fmtTime(j.created_at))}
    ${metaItem("Completed", j.completed_at ? fmtTime(j.completed_at) : "")}
    ${metaItem("Rounds", j.resume_rounds ? String(j.resume_rounds) : "")}
  </div>`;

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
  wireJobActions(j);
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
      const files = Array.from(($("#jobFilesInput") || {}).files || []);
      answerBtn.disabled = true;
      try {
        await apiPostForm(`/api/jobs/${j.id}/answer`, { text }, files);
        closeJob();
        showToast("Clarification sent — job continuing");
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
      const files = Array.from(($("#jobFilesInput") || {}).files || []);
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
      btn.disabled = true;
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

// File inputs are read directly from the DOM at submit time (FileList is
// live), so this only needs to wire the "attach" button -> hidden input
// click, and show a plain filename preview on change. No per-file removal
// UI -- re-picking replaces the browser's own selection, which is enough
// for a happy-path attach flow.
function wireAttachControls(root) {
  root.querySelectorAll("[data-attach-for]").forEach((btn) => {
    const input = document.getElementById(btn.dataset.attachFor);
    if (!input) return;
    btn.onclick = () => input.click();
    input.onchange = () => {
      const chips = root.querySelector(`[data-attach-chips-for="${input.id}"]`);
      if (!chips) return;
      const names = Array.from(input.files || []).map((f) => f.name);
      chips.textContent = names.length ? names.join(", ") : "";
    };
  });
}

function openComposer(mode = "new", job = null) {
  if (!$("#jobModal").classList.contains("hidden")) closeJob();
  composerMode = mode;
  composerJob = job;
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
  const chips = document.querySelector('[data-attach-chips-for="composerFilesInput"]');
  if (chips) chips.textContent = "";

  $("#composerSubmit").textContent = chain ? "Create next job"
    : resubmit ? "Resubmit as new job"
    : "Create job";
  $("#composerHint").textContent = chain
    ? "Creates a new linked job. The previous job and its history stay untouched."
    : resubmit
    ? "This creates a fresh job. The original job and its history stay untouched."
    : "Runs in the background. Open the job later to read the final reply.";

  $("#composerModal").classList.remove("hidden");
  updateBodyLock();
  setTimeout(() => $("#composerInstruction").focus(), 60);
}

function closeComposer() {
  stopRecording(true);
  composerMode = "new";
  composerJob = null;
  $("#composerModal").classList.add("hidden");
  updateBodyLock();
}

async function submitComposer() {
  const instruction = ($("#composerInstruction").value || "").trim();
  const feedback = ($("#composerFeedback").value || "").trim();
  const btn = $("#composerSubmit");
  if (!instruction) {
    showToast(composerMode === "chain" ? "Describe what's next first" : "Describe the job first");
    return;
  }

  const wasResubmit = composerMode === "resubmit";
  const wasChain = composerMode === "chain";
  let body = instruction;
  if (wasResubmit && feedback) {
    body += "\n\nAdditional feedback / changes requested:\n" + feedback;
  }

  const fields = { instruction: body };
  if (wasChain && composerJob) fields.parent_job_id = composerJob.id;
  const files = Array.from(($("#composerFilesInput") || {}).files || []);

  btn.disabled = true;
  try {
    await apiPostForm("/api/jobs", fields, files);
    closeComposer();
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
    || !$("#voiceOverlay").classList.contains("hidden");
  document.body.classList.toggle("modal-open", open);
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
  status.textContent = "Listening… tap stop when done.";
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

  stopBtn.onclick = async () => {
    stopBtn.disabled = true;
    cancelBtn.disabled = true;
    $("#voicePulse").classList.add("thinking");
    status.textContent = "Transcribing…";
    recorder.stop();
    await stopped;
    if (cancelled) return;

    if (!chunks.length) {
      overlay.classList.add("hidden");
      updateBodyLock();
      showToast("No audio captured");
      return;
    }
    try {
      const blob = new Blob(chunks, { type: "audio/webm" });
      const form = new FormData();
      form.append("audio", blob, "audio.webm");
      const r = await fetch("/api/transcribe", { method: "POST", credentials: "include", body: form });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.error || ("transcribe -> " + r.status));
      const text = (data.text || "").trim();
      if (!text) {
        overlay.classList.add("hidden");
        updateBodyLock();
        showToast("No speech detected");
        return;
      }
      status.textContent = "Creating job…";
      await apiPost("/api/jobs", { instruction: text });
      overlay.classList.add("hidden");
      updateBodyLock();
      showToast("Job queued from dictation");
      invalidateLanes();
      setLane("working");
    } catch (e) {
      overlay.classList.add("hidden");
      updateBodyLock();
      showToast("Failed: " + e.message);
    }
  };

  recorder.start();
}

function init() {
  $$(".tab").forEach((tab) => {
    tab.onclick = () => setLane(tab.dataset.lane);
  });

  $("#refreshBtn").onclick = manualRefresh;
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
      else closeComposer();
    };
  });

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
    if (!$("#composerModal").classList.contains("hidden")) {
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
