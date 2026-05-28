const statusPill = document.querySelector("#statusPill");
const modelLine = document.querySelector("#modelLine");
const presetButtons = document.querySelector("#presetButtons");
const voiceButtons = document.querySelector("#voiceButtons");
const textInput = document.querySelector("#text");
const langInput = document.querySelector("#lang");
const totalStepInput = document.querySelector("#totalStep");
const speedInput = document.querySelector("#speed");
const seedInput = document.querySelector("#seed");
const silenceDurationInput = document.querySelector("#silenceDuration");
const generateButton = document.querySelector("#generateButton");
const surpriseButton = document.querySelector("#surpriseButton");
const clearButton = document.querySelector("#clearButton");
const audioPlayer = document.querySelector("#audioPlayer");
const emptyOutput = document.querySelector("#emptyOutput");
const logs = document.querySelector("#logs");
const metrics = document.querySelector("#metrics");
const recentList = document.querySelector("#recentList");
const parameterReference = document.querySelector("#parameterReference");

let templates = {};
let activePoll = null;
let selectedVoice = "M1";

function setStatus(text, kind = "") {
  statusPill.textContent = text;
  statusPill.className = `status-pill ${kind}`.trim();
}

async function getJSON(url, options = {}) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || response.statusText);
  }
  return data;
}

function applyDefaults() {
  const defaults = templates.generation_defaults || {};
  selectedVoice = defaults.voice || "M1";
  textInput.value = templates.text_presets?.[0]?.text || "";
  langInput.value = defaults.lang || "en";
  totalStepInput.value = defaults.total_step || 8;
  speedInput.value = defaults.speed || 1.05;
  seedInput.value = defaults.seed ?? -1;
  silenceDurationInput.value = defaults.silence_duration ?? 0.3;
}

function renderPresets() {
  presetButtons.innerHTML = "";
  for (const preset of templates.text_presets || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = preset.label;
    button.addEventListener("click", () => {
      textInput.value = preset.text;
      textInput.focus();
    });
    presetButtons.append(button);
  }
}

function renderLanguages() {
  langInput.innerHTML = "";
  for (const row of templates.languages || []) {
    const option = document.createElement("option");
    option.value = row.code;
    option.textContent = `${row.code} · ${row.name}`;
    langInput.append(option);
  }
}

function renderVoices() {
  voiceButtons.innerHTML = "";
  for (const voice of templates.voices || []) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = voice.id === selectedVoice ? "voice selected" : "voice";
    button.innerHTML = `<strong>${escapeHTML(voice.label)}</strong><small>${escapeHTML(voice.description)}</small>`;
    button.addEventListener("click", () => {
      selectedVoice = voice.id;
      renderVoices();
    });
    voiceButtons.append(button);
  }
}

function renderReference() {
  parameterReference.innerHTML = "";
  const refs = templates.parameter_reference || {};
  for (const [key, value] of Object.entries(refs)) {
    const dt = document.createElement("dt");
    const dd = document.createElement("dd");
    dt.textContent = key;
    dd.textContent = value;
    parameterReference.append(dt, dd);
  }
}

function payload() {
  return {
    text: textInput.value.trim(),
    lang: langInput.value,
    voice: selectedVoice,
    total_step: Number(totalStepInput.value),
    speed: Number(speedInput.value),
    seed: Number(seedInput.value),
    silence_duration: Number(silenceDurationInput.value),
  };
}

function renderAudio(url) {
  if (!url) return;
  audioPlayer.src = `${url}?t=${Date.now()}`;
  audioPlayer.style.display = "block";
  emptyOutput.style.display = "none";
}

function renderJob(job) {
  logs.textContent = (job.logs || []).join("\n");
  logs.scrollTop = logs.scrollHeight;

  if (job.audio_url) {
    renderAudio(job.audio_url);
  }

  if (job.result) {
    const parts = [];
    if (job.result.duration_seconds !== undefined) parts.push(`${job.result.duration_seconds}s audio`);
    if (job.result.total_step) parts.push(`${job.result.total_step} steps`);
    if (job.result.voice) parts.push(job.result.voice);
    if (job.result.lang) parts.push(job.result.lang);
    if (job.result.elapsed_seconds) parts.push(`${job.result.elapsed_seconds}s render`);
    metrics.textContent = parts.join(" · ");
  }

  if (job.status === "queued") setStatus("Queued", "working");
  if (job.status === "running") setStatus("Generating", "working");
  if (job.status === "done") setStatus("Done", "ok");
  if (job.status === "error") setStatus(job.error || "Error", "error");
}

function pollJob(id) {
  if (activePoll) window.clearInterval(activePoll);
  activePoll = window.setInterval(async () => {
    try {
      const job = await getJSON(`/api/job/${id}`);
      renderJob(job);
      if (job.status === "done" || job.status === "error") {
        window.clearInterval(activePoll);
        activePoll = null;
        generateButton.disabled = false;
        await loadRecent();
      }
    } catch (error) {
      window.clearInterval(activePoll);
      activePoll = null;
      generateButton.disabled = false;
      setStatus(error.message, "error");
    }
  }, 1200);
}

async function submitGeneration() {
  logs.textContent = "";
  metrics.textContent = "";
  generateButton.disabled = true;
  setStatus("Queued", "working");
  try {
    const job = await getJSON("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload()),
    });
    renderJob(job);
    pollJob(job.id);
  } catch (error) {
    generateButton.disabled = false;
    setStatus(error.message, "error");
  }
}

async function loadRecent() {
  const data = await getJSON("/api/recent");
  recentList.innerHTML = "";
  for (const item of data.items || []) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = "recent-item";
    row.innerHTML = `
      <span class="play-dot"></span>
      <span>
        <strong>${escapeHTML(item.text || item.filename)}</strong>
        <small>${escapeHTML(item.voice || "")} · ${escapeHTML(item.lang || "")} · ${escapeHTML(item.duration_seconds ?? "")}s</small>
      </span>
    `;
    row.addEventListener("click", () => {
      textInput.value = item.text || "";
      selectedVoice = item.voice || selectedVoice;
      langInput.value = item.lang || langInput.value;
      renderVoices();
      renderAudio(item.audio_url);
    });
    recentList.append(row);
  }
}

function escapeHTML(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function init() {
  try {
    templates = await getJSON("/api/templates");
    renderPresets();
    renderLanguages();
    applyDefaults();
    renderVoices();
    renderReference();
    const state = await getJSON("/api/state");
    modelLine.textContent = templates.model?.hf_repo || modelLine.textContent;
    setStatus(state.model_ready ? "Ready" : "Download model", state.model_ready ? "ok" : "working");
    await loadRecent();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

generateButton.addEventListener("click", submitGeneration);

surpriseButton.addEventListener("click", async () => {
  try {
    const data = await getJSON("/api/surprise");
    textInput.value = data.text;
    textInput.focus();
  } catch (error) {
    setStatus(error.message, "error");
  }
});

clearButton.addEventListener("click", () => {
  textInput.value = "";
  logs.textContent = "";
  metrics.textContent = "";
  audioPlayer.removeAttribute("src");
  audioPlayer.style.display = "none";
  emptyOutput.style.display = "grid";
  textInput.focus();
});

init();

