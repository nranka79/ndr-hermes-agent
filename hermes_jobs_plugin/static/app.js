// Hermes Jobs PWA -- vanilla JS, no build step, no framework.
"use strict";

const STATUS_LABEL = {
  ready: "Queued", running: "Working", blocked: "Needs you",
  review: "Needs you", done: "Done", archived: "Dropped",
};

let currentLane = "needs_you";
let jobsCache = [];
let activeJobId = null;
let pollTimer = null;
let mediaRecorder = null;
let recordedChunks = [];

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function fmtTime(ts) {
  if (!ts) return "";
  const d = new Date(ts * 1000);
  return d.toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function escapeHtml(s) {
  return (s || "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function showToast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 2200);
}

// ---------------------------------------------------------------------------
// data
// ---------------------------------------------------------------------------

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
    // If the open sheet's job changed state, refresh it in place.
    if (activeJobId) {
      const j = jobsCache.find((x) => x.id === activeJobId);
      if (j) renderSheet(j);
    }
  } catch (e) {
    console.error(e);
    showToast("Could not load jobs");
  }
}

// ---------------------------------------------------------------------------
// list rendering
// ---------------------------------------------------------------------------

function renderList() {
  const list = $("#list");
  const items = jobsCache.filter((j) => j.lane === currentLane);
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
  items.sort((a, b) => (b.created_at || 0) - (a.created_at || 0));
  for (const j of items) {
    list.appendChild(renderCard(j));
  }
}

function renderCard(j) {
  const card = document.createElement("div");
  card.className = "card";
  card.onclick = () => openSheet(j.id);
  const sub = j.pending_kind === "clarification" ? j.question
    : j.pending_kind === "failure" ? j.last_failure_error
    : j.status === "done" ? (j.result || "")
    : j.instruction;
  card.innerHTML = `
    <div class="card-top">
      <span class="card-id">${escapeHtml(j.id)}</span>
      <span class="card-status status-${j.status}">${STATUS_LABEL[j.status] || j.status}</span>
    </div>
    <div class="card-title">${escapeHtml(j.title)}</div>
    <div class="card-sub">${escapeHtml(sub || "")}</div>
    <div class="card-meta">
      <span>${escapeHtml(j.origin_display)}</span>
      <span>${fmtTime(j.created_at)}</span>
      ${j.resume_rounds ? `<span>${j.resume_rounds} round(s)</span>` : ""}
    </div>
  `;
  return card;
}

// ---------------------------------------------------------------------------
// detail sheet
// ---------------------------------------------------------------------------

function openSheet(jobId) {
  activeJobId = jobId;
  const j = jobsCache.find((x) => x.id === jobId);
  if (!j) return;
  renderSheet(j);
  $("#sheetBackdrop").classList.remove("hidden");
  $("#sheet").classList.remove("hidden");
}

function closeSheet() {
  activeJobId = null;
  $("#sheetBackdrop").classList.add("hidden");
  $("#sheet").classList.add("hidden");
  stopRecording();
}

function renderSheet(j) {
  $("#sheetTitle").textContent = j.id;
  const body = $("#sheetBody");

  let html = `
    <div class="card-status status-${j.status}" style="display:inline-block;margin-bottom:6px;">
      ${STATUS_LABEL[j.status] || j.status}
    </div>
    <div class="section-label">Origin</div>
    <div class="section-body">${escapeHtml(j.origin_display)} &middot; ${fmtTime(j.created_at)}</div>
    <div class="section-label">Instruction</div>
    <div class="section-body">${escapeHtml(j.instruction)}</div>
  `;

  if (j.pending_kind === "clarification") {
    html += `
      <div class="section-label">Waiting on you</div>
      <div class="section-body">${escapeHtml(j.question)}${j.question_context ? "\n\n" + escapeHtml(j.question_context) : ""}</div>
      ${j.suggested_options && j.suggested_options.length ? `
        <div class="options-row">
          ${j.suggested_options.map((o) => `<button class="option-chip" data-opt="${escapeHtml(o)}">${escapeHtml(o)}</button>`).join("")}
        </div>` : ""}
      <div class="answer-row">
        <textarea class="answer-input" id="answerInput" placeholder="Type or dictate your answer..."></textarea>
        <button class="mic-btn" id="micBtn" title="Dictate">&#127908;</button>
      </div>
      <div class="action-row">
        <button class="btn btn-primary" id="submitAnswerBtn">Answer</button>
        <button class="btn btn-danger" id="dropBtn">Drop job</button>
      </div>
    `;
  } else if (j.pending_kind === "failure") {
    html += `
      <div class="section-label">What went wrong</div>
      <div class="section-body">${escapeHtml(j.last_failure_error || "")}</div>
      <div class="section-label">Optional extra input before retrying</div>
      <div class="answer-row">
        <textarea class="answer-input" id="answerInput" placeholder="Anything to add before retrying (optional)..."></textarea>
        <button class="mic-btn" id="micBtn" title="Dictate">&#127908;</button>
      </div>
      <div class="action-row">
        <button class="btn btn-primary" id="continueBtn">Continue</button>
        <button class="btn btn-danger" id="dropBtn">Drop job</button>
      </div>
    `;
  } else if (j.status === "done") {
    html += `
      <div class="section-label">Result</div>
      <div class="section-body">${escapeHtml(j.result || "")}</div>
    `;
  } else if (j.status === "archived") {
    html += `
      <div class="section-label">Dropped</div>
      <div class="section-body">${fmtTime(j.dropped_at)}${j.drop_reason ? "\n" + escapeHtml(j.drop_reason) : ""}</div>
    `;
  } else {
    html += `
      <div class="section-label">Status</div>
      <div class="section-body">Still ${STATUS_LABEL[j.status] || j.status}. Checking every few seconds.</div>
      <div class="action-row">
        <button class="btn btn-danger" id="dropBtn">Drop job</button>
      </div>
    `;
  }

  if (j.events && j.events.length) {
    html += `<div class="section-label">History</div><div class="section-body">`
      + j.events.map((e) => `${fmtTime(e.created_at)} &mdash; ${escapeHtml(e.kind)}`).join("<br>")
      + `</div>`;
  }

  body.innerHTML = html;
  wireSheetActions(j);
}

function wireSheetActions(j) {
  const answerInput = $("#answerInput");
  $$(".option-chip").forEach((btn) => {
    btn.onclick = () => { if (answerInput) answerInput.value = btn.dataset.opt; };
  });
  const micBtn = $("#micBtn");
  if (micBtn) micBtn.onclick = () => toggleRecording(micBtn, answerInput);

  const submitAnswerBtn = $("#submitAnswerBtn");
  if (submitAnswerBtn) {
    submitAnswerBtn.onclick = async () => {
      const text = (answerInput.value || "").trim();
      if (!text) { showToast("Enter an answer first"); return; }
      submitAnswerBtn.disabled = true;
      try {
        await apiPost(`/api/jobs/${j.id}/answer`, { text });
        showToast("Answered -- job resuming");
        closeSheet();
        loadJobs();
      } catch (e) {
        showToast("Failed: " + e.message);
      } finally {
        submitAnswerBtn.disabled = false;
      }
    };
  }

  const continueBtn = $("#continueBtn");
  if (continueBtn) {
    continueBtn.onclick = async () => {
      continueBtn.disabled = true;
      try {
        await apiPost(`/api/jobs/${j.id}/continue`, { extra: (answerInput.value || "").trim() });
        showToast("Retrying job");
        closeSheet();
        loadJobs();
      } catch (e) {
        showToast("Failed: " + e.message);
      } finally {
        continueBtn.disabled = false;
      }
    };
  }

  const dropBtn = $("#dropBtn");
  if (dropBtn) {
    dropBtn.onclick = async () => {
      if (!confirm("Drop this job? This cannot be undone.")) return;
      dropBtn.disabled = true;
      try {
        await apiPost(`/api/jobs/${j.id}/drop`, { reason: "dropped from board" });
        showToast("Job dropped");
        closeSheet();
        loadJobs();
      } catch (e) {
        showToast("Failed: " + e.message);
      } finally {
        dropBtn.disabled = false;
      }
    };
  }
}

// ---------------------------------------------------------------------------
// voice dictation
// ---------------------------------------------------------------------------

async function toggleRecording(btn, targetInput) {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    stopRecording();
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    recordedChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) recordedChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      btn.classList.remove("recording");
      if (recordedChunks.length === 0) return;
      const blob = new Blob(recordedChunks, { type: "audio/webm" });
      showToast("Transcribing...");
      try {
        const form = new FormData();
        form.append("audio", blob, "audio.webm");
        const r = await fetch("/api/transcribe", { method: "POST", credentials: "include", body: form });
        const data = await r.json();
        if (data.text && targetInput) {
          targetInput.value = (targetInput.value ? targetInput.value + " " : "") + data.text;
        }
        showToast(data.text ? "Dictation added" : "No speech detected");
      } catch (e) {
        showToast("Transcription failed");
      }
    };
    mediaRecorder.start();
    btn.classList.add("recording");
  } catch (e) {
    showToast("Microphone access denied");
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state === "recording") {
    mediaRecorder.stop();
  }
}

// ---------------------------------------------------------------------------
// wiring
// ---------------------------------------------------------------------------

function init() {
  $$(".tab").forEach((tab) => {
    tab.onclick = () => {
      $$(".tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      currentLane = tab.dataset.lane;
      renderList();
    };
  });
  $("#refreshBtn").onclick = loadJobs;
  $("#sheetClose").onclick = closeSheet;
  $("#sheetBackdrop").onclick = closeSheet;

  loadJobs();
  pollTimer = setInterval(loadJobs, 8000);

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
}

document.addEventListener("DOMContentLoaded", init);
