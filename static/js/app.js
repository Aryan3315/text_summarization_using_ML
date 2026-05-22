/**
 * Text Summarizer — frontend logic
 * Communicates with Flask backend at /api/summarize and /api/upload
 */

"use strict";

// ── Constants ────────────────────────────────────────────────────────────────
const MAX_CHARS    = 10_000;
const MAX_RETRIES  = 3;
const TIMEOUT_MS   = 120_000;  // 2 minutes — BART on CPU can be slow
const TOAST_MS     = 2_000;

// ── State ────────────────────────────────────────────────────────────────────
const state = {
  summary:     null,   // string | null
  isLoading:   false,
  retryCount:  0,
  lastRequest: null,   // { text, length } for retry
};

// ── DOM refs ─────────────────────────────────────────────────────────────────
const inputEl       = document.getElementById("input-text");
const charCountEl   = document.getElementById("char-count");
const inputErrorEl  = document.getElementById("input-error");
const lengthEl      = document.getElementById("length-select");
const summarizeBtn  = document.getElementById("summarize-btn");
const btnLabel      = document.getElementById("btn-label");
const btnSpinner    = document.getElementById("btn-spinner");
const clearBtn      = document.getElementById("clear-btn");
const outputArea    = document.getElementById("output-area");
const wordCountEl   = document.getElementById("word-count");
const copyBtn       = document.getElementById("copy-btn");
const downloadBtn   = document.getElementById("download-btn");
const copyToast     = document.getElementById("copy-toast");
const globalBanner  = document.getElementById("global-banner");
const fileUpload    = document.getElementById("file-upload");
const fileNameLabel = document.getElementById("file-name");

// ── Session storage: persist length selection ─────────────────────────────────
(function restoreLength() {
  const saved = sessionStorage.getItem("summaryLength");
  if (saved && ["short", "medium", "long"].includes(saved)) {
    lengthEl.value = saved;
  }
})();

lengthEl.addEventListener("change", () => {
  sessionStorage.setItem("summaryLength", lengthEl.value);
});

// ── Character counter ─────────────────────────────────────────────────────────
inputEl.addEventListener("input", () => {
  const len = inputEl.value.length;
  charCountEl.textContent = `${len.toLocaleString()} / ${MAX_CHARS.toLocaleString()}`;
  charCountEl.classList.toggle("over-limit", len > MAX_CHARS);
  if (len <= MAX_CHARS) clearFieldError();
});

// ── Summarize ─────────────────────────────────────────────────────────────────
summarizeBtn.addEventListener("click", () => {
  const text   = inputEl.value;
  const length = lengthEl.value;

  if (!validateInput(text)) return;

  state.lastRequest = { text, length };
  state.retryCount  = 0;
  doSummarize(text, length);
});

async function doSummarize(text, length) {
  setLoading(true);
  clearOutput();
  hideBanner();

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch("/api/summarize", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text, length }),
      signal:  controller.signal,
    });

    clearTimeout(timer);
    const data = await res.json();

    if (!res.ok) {
      handleApiError(data);
      return;
    }

    // Success
    state.summary    = data.summary;
    state.retryCount = 0;
    renderSummary(data.summary, data.word_count);

  } catch (err) {
    clearTimeout(timer);

    if (err.name === "AbortError") {
      showBanner("The request timed out. Please try again.", "error");
      logError(err);
    } else {
      // Network error — offer retry
      state.retryCount++;
      logError(err);

      if (state.retryCount < MAX_RETRIES) {
        showBanner(
          `Could not reach the server. ${MAX_RETRIES - state.retryCount} attempt(s) remaining.`,
          "error",
          true
        );
      } else {
        showBanner("Could not reach the server. Please try again later.", "error", false);
      }
    }
  } finally {
    setLoading(false);
  }
}

// ── Validation ────────────────────────────────────────────────────────────────
function validateInput(text) {
  if (!text || !text.trim()) {
    showFieldError("Text input is required.");
    return false;
  }
  if (text.length > MAX_CHARS) {
    showFieldError(`Text exceeds the ${MAX_CHARS.toLocaleString()} character limit.`);
    return false;
  }
  clearFieldError();
  return true;
}

function showFieldError(msg) {
  inputErrorEl.textContent = msg;
  inputEl.classList.add("error");
  inputEl.setAttribute("aria-invalid", "true");
}

function clearFieldError() {
  inputErrorEl.textContent = "";
  inputEl.classList.remove("error");
  inputEl.removeAttribute("aria-invalid");
}

// ── API error handler ─────────────────────────────────────────────────────────
function handleApiError(data) {
  const msg = data?.error || "An unexpected error occurred. Please try again.";
  const code = data?.code || "";
  logError(new Error(`API error [${code}]: ${msg}`));

  if (code === "MODEL_UNAVAILABLE") {
    showBanner(msg, "warning");
  } else {
    showBanner(msg, "error");
  }
}

// ── Render summary ────────────────────────────────────────────────────────────
function renderSummary(text, wordCount) {
  outputArea.textContent = text;
  wordCountEl.textContent = `${wordCount} word${wordCount !== 1 ? "s" : ""}`;
  copyBtn.disabled     = false;
  downloadBtn.disabled = false;
}

function clearOutput() {
  outputArea.innerHTML = '<p class="placeholder-text">Your summary will appear here.</p>';
  wordCountEl.textContent = "";
  copyBtn.disabled     = true;
  downloadBtn.disabled = true;
  state.summary        = null;
}

// ── Loading state ─────────────────────────────────────────────────────────────
function setLoading(on) {
  state.isLoading        = on;
  summarizeBtn.disabled  = on;
  btnLabel.textContent   = on ? "Summarizing…" : "Summarize";
  btnSpinner.classList.toggle("hidden", !on);
}

// ── Banner ────────────────────────────────────────────────────────────────────
function showBanner(msg, type = "error", showRetry = false) {
  globalBanner.className = `banner ${type}`;
  globalBanner.innerHTML = "";

  const text = document.createTextNode(msg);
  globalBanner.appendChild(text);

  if (showRetry) {
    const retryBtn = document.createElement("button");
    retryBtn.className   = "banner-retry";
    retryBtn.textContent = "Retry";
    retryBtn.setAttribute("aria-label", "Retry summarization request");
    retryBtn.addEventListener("click", () => {
      if (state.lastRequest) {
        hideBanner();
        doSummarize(state.lastRequest.text, state.lastRequest.length);
      }
    });
    globalBanner.appendChild(retryBtn);
  }
}

function hideBanner() {
  globalBanner.className = "banner hidden";
  globalBanner.textContent = "";
}

// ── Clear button ──────────────────────────────────────────────────────────────
clearBtn.addEventListener("click", () => {
  inputEl.value = "";
  charCountEl.textContent = `0 / ${MAX_CHARS.toLocaleString()}`;
  charCountEl.classList.remove("over-limit");
  clearFieldError();
  clearOutput();
  hideBanner();
  fileNameLabel.textContent = "";
  fileUpload.value = "";
  state.lastRequest = null;
  state.retryCount  = 0;
});

// ── Copy button ───────────────────────────────────────────────────────────────
copyBtn.addEventListener("click", async () => {
  if (!state.summary) return;

  try {
    await navigator.clipboard.writeText(state.summary);
    copyToast.classList.remove("hidden");
    setTimeout(() => copyToast.classList.add("hidden"), TOAST_MS);
  } catch (err) {
    logError(err);
    showBanner("Copy failed. Please select the text and copy it manually.", "error");
  }
});

// ── Download button ───────────────────────────────────────────────────────────
downloadBtn.addEventListener("click", () => {
  if (!state.summary) return;

  const blob = new Blob([state.summary], { type: "text/plain;charset=utf-8" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href     = url;
  a.download = "summary.txt";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

// ── File upload ───────────────────────────────────────────────────────────────
fileUpload.addEventListener("change", async () => {
  const file = fileUpload.files[0];
  if (!file) return;

  fileNameLabel.textContent = file.name;

  // Client-side pre-validation
  const ext = file.name.split(".").pop().toLowerCase();
  if (!["txt", "pdf"].includes(ext)) {
    showBanner("Unsupported file format. Accepted formats: .txt, .pdf", "error");
    fileUpload.value = "";
    fileNameLabel.textContent = "";
    return;
  }
  if (file.size === 0) {
    showBanner("The uploaded file is empty.", "error");
    fileUpload.value = "";
    fileNameLabel.textContent = "";
    return;
  }
  if (file.size > 5 * 1024 * 1024) {
    showBanner("File size exceeds the 5 MB limit.", "error");
    fileUpload.value = "";
    fileNameLabel.textContent = "";
    return;
  }

  hideBanner();

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res  = await fetch("/api/upload", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      showBanner(data?.error || "File processing failed.", "error");
      fileUpload.value = "";
      fileNameLabel.textContent = "";
      return;
    }

    inputEl.value = data.text;
    const len = data.text.length;
    charCountEl.textContent = `${len.toLocaleString()} / ${MAX_CHARS.toLocaleString()}`;
    charCountEl.classList.toggle("over-limit", len > MAX_CHARS);
    clearFieldError();

  } catch (err) {
    logError(err);
    showBanner("Could not upload the file. Please try again.", "error");
    fileUpload.value = "";
    fileNameLabel.textContent = "";
  }
});

// ── Global error boundary ─────────────────────────────────────────────────────
window.addEventListener("error", (event) => {
  logError(event.error || new Error(event.message));
  showBanner("An unexpected error occurred. You can continue using the app.", "error");
});

window.addEventListener("unhandledrejection", (event) => {
  logError(event.reason instanceof Error ? event.reason : new Error(String(event.reason)));
  showBanner("An unexpected error occurred. You can continue using the app.", "error");
});

// ── Logging ───────────────────────────────────────────────────────────────────
function logError(err) {
  console.error(`[TextSummarizer] ${new Date().toISOString()}`, err);
}
