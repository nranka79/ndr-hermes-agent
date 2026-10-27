"use strict";

const STATUS_LABEL = {
  ready: "Queued",
  running: "Working",
  blocked: "Needs you",
  review: "Needs you",
  done: "Done",
  archived: "Dropped",
};

let currentLane = "needs_you";
let jobsCache = [];
let activeJobId = null;
let sheetSignature = "";
let pollTimer = null;
let toastTimer = null;
let mediaRecorder = null;
let recordedChunks = [];
let discardRecording = false;
let composerMode = "new";
let composerJob = null;

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

async function loadJobs() {
  try {
    const data = await apiGet("/api/jobs");
    jobsCache = data.jobs || [];
    for (const lane of ["needs_you", "working", "done", "dropped"]) {
      const el = $("#badge-" + lane);
      if (el) el.textContent = data.counts[lane] || 0;
    }
    renderList();
    if (activeJobId && !$("#jobModal").classList.contains("hidden")) {
      const j = jobsCache.find((x) => x.id === activeJobId);
      if (j && jobSignature(j) !== sheetSignature && jobModalIsIdle()) {
        refreshOpenJob();
      }
    }
  } catch (e) {
    console.error(e);
    showToast("Could not load jobs");
  }
}

function setLane(lane) {
  currentLane = lane;
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.lane === lane));
  renderList();
}

function jobSummary(j) {
  if (j.pending_kind === "clarification") return j.question || "Waiting on your answer.";
  if (j.pending_kind === "failure") return j.last_failure_error || "The run failed.";
  if (j.status === "done") return j.result || "No final reply recorded.";
  return j.instruction || "";
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
  const items = jobsCache
    .filter((j) => j.lane === currentLane)
    .sort((a, b) => (b.created_at || 0) - (a.created_at || 0));

  list.className = "jobs-list" + (items.length === 0 ? " solo" : "");
  $("#jobsHead").classList.toggle("hidden", items.length === 0);
  list.innerHTML = "";

  if (items.length === 0) {
    const p = document.createElement("p");
    p.className = "empty";
    p.textContent = currentLane === "needs_you"
      ? "Nothing needs you right now."
      : "No jobs here.";
    list.appendChild(p);
    return;
  }
  for (const j of items) list.appendChild(renderRow(j));
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
      <div class="job-id">${escapeHtml(j.id)}${j.resume_rounds ? ` &middot; ${j.resume_rounds} round(s)` : ""}</div>
    </div>
    <div class="job-detail">
      <div class="job-detail-text">${escapeHtml(jobSummary(j))}</div>
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
  const j = jobsCache.find((x) => x.id === jobId);
  if (!j) return;
  activeJobId = jobId;
  sheetSignature = "";
  // Render the cheap list-cache version immediately (no blank modal while
  // the detail call is in flight), then replace it with the full detail
  // fetch -- the list endpoint deliberately omits events/artifacts to stay
  // light, so a job only ever shows files/history once this resolves.
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
    const idx = jobsCache.findIndex((x) => x.id === jobId);
    if (idx >= 0) jobsCache[idx] = { ...jobsCache[idx], ...detail };
    if (jobModalIsIdle()) renderJob(detail);
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

function renderJob(j) {
  activeJobId = j.id;
  sheetSignature = jobSignature(j);

  $("#jobModalStatus").innerHTML =
    `<span class="pill status-${j.status}">${escapeHtml(STATUS_LABEL[j.status] || j.status)}</span>`;
  $("#jobModalTitle").textContent = j.title || j.id;

  let html = `<div class="meta-grid">
    ${metaItem("Job ID", j.id)}
    ${metaItem("Origin", j.origin_display || "")}
    ${metaItem("Created", fmtTime(j.created_at))}
    ${metaItem("Completed", j.completed_at ? fmtTime(j.completed_at) : "")}
    ${metaItem("Rounds", j.resume_rounds ? String(j.resume_rounds) : "")}
  </div>`;

  html += `<div class="section-label">Instruction</div>
    <div class="section-body">${linkify(j.instruction || "")}</div>`;

  if (j.pending_kind === "clarification") {
    const context = j.question_context
      ? `\n\n${escapeHtml(j.question_context)}`
      : "";
    html += `<div class="section-label">Waiting on you</div>
      <div class="question-box">${linkify(j.question || "")}${context}</div>
      ${j.suggested_options && j.suggested_options.length ? `
        <div class="options-row">
          ${j.suggested_options.map((o) => `<button class="option-chip" data-opt="${escapeHtml(o)}">${escapeHtml(o)}</button>`).join("")}
        </div>` : ""}
      <label class="field-label" for="answerInput">Your clarification</label>
      <div class="compose-row">
        <textarea id="answerInput" class="input textarea" placeholder="Type or dictate your answer..."></textarea>
        <button class="mic-btn" data-mic-for="answerInput" title="Dictate" aria-label="Dictate clarification">&#127908;</button>
      </div>
      <p class="hint">Sending this continues the same job. Drop job ends it and ignores this text.</p>
      <div class="action-row">
        <button class="btn btn-primary" id="answerBtn">Send clarification &amp; continue</button>
        <button class="btn btn-secondary" id="resubmitBtn">Resubmit as new job</button>
        <button class="btn btn-danger" id="dropBtn">Drop job</button>
      </div>`;
  } else if (j.pending_kind === "failure") {
    html += `<div class="section-label">What went wrong</div>
      <div class="section-body">${escapeHtml(j.last_failure_error || "")}</div>
      <label class="field-label" for="answerInput">Optional extra input before retrying</label>
      <div class="compose-row">
        <textarea id="answerInput" class="input textarea" placeholder="Anything to add before retrying (optional)..."></textarea>
        <button class="mic-btn" data-mic-for="answerInput" title="Dictate" aria-label="Dictate extra input">&#127908;</button>
      </div>
      <div class="action-row">
        <button class="btn btn-primary" id="continueBtn">Continue job</button>
        <button class="btn btn-secondary" id="resubmitBtn">Resubmit as new job</button>
        <button class="btn btn-danger" id="dropBtn">Drop job</button>
      </div>`;
  } else if (j.status === "done") {
    html += `<div class="section-label">Final reply</div>
      <div class="reply-box">${linkify(j.result || "No final reply was recorded for this job.")}</div>`;
    const files = j.artifacts || [];
    if (files.length) {
      html += `<div class="section-label">Files produced</div>
        <div class="file-list">${files.map((f) => `
          <a class="file-chip" href="/api/jobs/${j.id}/artifact?path=${encodeURIComponent(f.path)}" target="_blank" rel="noopener noreferrer" title="${escapeHtml(f.path)}">
            <span class="file-icon">&#128196;</span>
            <span class="file-name">${escapeHtml(f.name)}</span>
            ${f.size != null ? `<span class="file-size">${fmtSize(f.size)}</span>` : `<span class="file-size">missing</span>`}
          </a>`).join("")}</div>`;
    }
    html += `<div class="action-row">
        <button class="btn btn-primary" id="resubmitBtn">Resubmit with changes</button>
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
  wireJobActions(j);
}

function wireJobActions(j) {
  const root = $("#jobModal");
  const answerInput = $("#answerInput");

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
      answerBtn.disabled = true;
      try {
        await apiPost(`/api/jobs/${j.id}/answer`, { text });
        closeJob();
        showToast("Clarification sent — job continuing");
        setLane("working");
        loadJobs();
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
      continueBtn.disabled = true;
      try {
        await apiPost(`/api/jobs/${j.id}/continue`, {
          extra: (answerInput.value || "").trim(),
        });
        closeJob();
        showToast("Job retrying");
        setLane("working");
        loadJobs();
      } catch (e) {
        showToast("Failed: " + e.message);
      } finally {
        continueBtn.disabled = false;
      }
    };
  }

  const resubmitBtn = $("#resubmitBtn");
  if (resubmitBtn) resubmitBtn.onclick = () => openComposer("resubmit", j);

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
        loadJobs();
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

function openComposer(mode = "new", job = null) {
  if (!$("#jobModal").classList.contains("hidden")) closeJob();
  composerMode = mode;
  composerJob = job;
  const resubmit = mode === "resubmit" && job;

  $("#composerKicker").textContent = resubmit
    ? `Resubmit ${job.id} as a new job`
    : "New job";
  $("#composerTitle").textContent = resubmit
    ? "Update the job and resubmit"
    : "What should Hermes do?";
  $("#composerInstruction").value = resubmit ? (job.instruction || "") : "";
  $("#composerFeedback").value = "";
  $("#composerFeedbackWrap").classList.toggle("hidden", !resubmit);
  $("#composerSubmit").textContent = resubmit ? "Resubmit as new job" : "Create job";
  $("#composerHint").textContent = resubmit
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
    showToast("Describe the job first");
    return;
  }

  const wasResubmit = composerMode === "resubmit";
  let body = instruction;
  if (wasResubmit && feedback) {
    body += "\n\nAdditional feedback / changes requested:\n" + feedback;
  }

  btn.disabled = true;
  try {
    await apiPost("/api/jobs", { instruction: body });
    closeComposer();
    showToast(wasResubmit ? "New job created from your changes" : "Job queued");
    setLane("working");
    loadJobs();
  } catch (e) {
    showToast("Failed: " + e.message);
  } finally {
    btn.disabled = false;
  }
}

function updateBodyLock() {
  const open = !$("#jobModal").classList.contains("hidden")
    || !$("#composerModal").classList.contains("hidden");
  document.body.classList.toggle("modal-open", open);
}

function init() {
  $$(".tab").forEach((tab) => {
    tab.onclick = () => setLane(tab.dataset.lane);
  });

  $("#refreshBtn").onclick = loadJobs;
  $("#newJobBtn").onclick = () => openComposer("new");
  $("#composerCancel").onclick = closeComposer;
  $("#composerSubmit").onclick = submitComposer;

  $$("[data-close-modal]").forEach((el) => {
    el.onclick = () => {
      const modal = el.closest(".modal");
      if (!modal) return;
      if (modal.id === "jobModal") closeJob();
      else closeComposer();
    };
  });

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
    if (!$("#composerModal").classList.contains("hidden")) {
      closeComposer();
    } else if (!$("#jobModal").classList.contains("hidden")) {
      closeJob();
    }
  });

  wireMicButtons(document);
  loadJobs();
  pollTimer = setInterval(loadJobs, 5000);

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js", { updateViaCache: "none" }).catch(() => {});
  }
}

document.addEventListener("DOMContentLoaded", init);
