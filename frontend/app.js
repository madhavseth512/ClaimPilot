const API = "";  // same origin — FastAPI serves this file
let token = sessionStorage.getItem("cp_token");
let currentCaseId = null;

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  if (token) showChat();
  setupDragDrop();
});

// ── Auth ──────────────────────────────────────────────────────────────────────

function switchTab(tab) {
  document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".auth-form").forEach(f => f.classList.add("hidden"));
  document.querySelector(`#${tab}-form`).classList.remove("hidden");
  event.currentTarget.classList.add("active");
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;
  try {
    const res = await fetch(`${API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    const data = await res.json();
    token = data.token;
    sessionStorage.setItem("cp_token", token);
    showChat();
  } catch (err) {
    showAuthError(err.message);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById("reg-name").value;
  const email = document.getElementById("reg-email").value;
  const password = document.getElementById("reg-password").value;
  try {
    const res = await fetch(`${API}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    const data = await res.json();
    token = data.token;
    sessionStorage.setItem("cp_token", token);
    showChat();
  } catch (err) {
    showAuthError(err.message);
  }
}

function showAuthError(msg) {
  const el = document.getElementById("auth-error");
  el.textContent = msg;
  el.classList.remove("hidden");
}

function logout() {
  token = null;
  currentCaseId = null;
  sessionStorage.removeItem("cp_token");
  document.getElementById("messages").innerHTML = "";
  document.getElementById("auth-screen").classList.remove("hidden");
  document.getElementById("chat-screen").classList.add("hidden");
}

// ── Screen transitions ────────────────────────────────────────────────────────

function showChat() {
  document.getElementById("auth-screen").classList.add("hidden");
  document.getElementById("chat-screen").classList.remove("hidden");
  loadActiveCases();
}

async function loadActiveCases() {
  try {
    const res = await fetch(`${API}/cases/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return;
    const cases = await res.json();
    if (cases.length > 0) {
      currentCaseId = cases[0].case_id;
      updateCaseBadge(cases[0].intent);
    }
  } catch (_) {}
}

function updateCaseBadge(intent) {
  const badge = document.getElementById("case-badge");
  const labels = {
    motor_claim: "Motor Claim",
    health_claim: "Health Claim",
    life_insurance: "Life Insurance",
    travel_insurance: "Travel Insurance",
    home_property: "Home/Property",
    personal_accident: "Personal Accident",
  };
  badge.textContent = labels[intent] || intent;
  badge.classList.remove("hidden");
}

// ── Messaging ─────────────────────────────────────────────────────────────────

async function sendMessage() {
  const input = document.getElementById("message-input");
  const text = input.value.trim();
  if (!text) return;

  appendMessage("user", text);
  input.value = "";
  showTyping(true);

  try {
    const res = await fetch(`${API}/chat/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message: text, case_id: currentCaseId }),
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    const data = await res.json();
    currentCaseId = data.case_id;
    showTyping(false);
    appendMessage("agent", data.response);
    if (data.pending_docs?.length > 0) showUploadArea();
  } catch (err) {
    showTyping(false);
    appendMessage("agent", `Something went wrong: ${err.message}`);
  }
}

function handleKeyDown(e) {
  if (e.key === "Enter" && !e.shiftKey) sendMessage();
}

function appendMessage(role, text) {
  const container = document.getElementById("messages");
  const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.innerHTML = `
    <div class="avatar">${role === "agent" ? "🛡️" : "👤"}</div>
    <div>
      <div class="bubble">${escapeHtml(text)}</div>
      <div class="message-time">${time}</div>
    </div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function showTyping(show) {
  document.getElementById("typing-indicator").classList.toggle("hidden", !show);
  const container = document.getElementById("messages");
  container.scrollTop = container.scrollHeight;
}

// ── File upload ───────────────────────────────────────────────────────────────

function toggleUpload() {
  document.getElementById("upload-area").classList.toggle("hidden");
}

function showUploadArea() {
  document.getElementById("upload-area").classList.remove("hidden");
}

async function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  await uploadFile(file);
  e.target.value = "";
}

async function uploadFile(file) {
  if (!file.name.endsWith(".pdf")) {
    appendMessage("agent", "I currently only accept PDF files. Please upload your document in PDF format.");
    return;
  }

  const label = document.getElementById("upload-text");
  label.textContent = `Uploading ${file.name}…`;

  const formData = new FormData();
  formData.append("file", file);
  if (currentCaseId) formData.append("case_id", currentCaseId);

  try {
    const res = await fetch(`${API}/upload/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
    if (!res.ok) throw new Error((await res.json()).detail);
    const data = await res.json();
    appendMessage("agent", data.message);
    if (data.pending_docs?.length === 0) {
      document.getElementById("upload-area").classList.add("hidden");
    }
  } catch (err) {
    appendMessage("agent", `Upload failed: ${err.message}`);
  } finally {
    label.textContent = "Drag & drop PDF or click to browse";
  }
}

// ── Drag & drop ───────────────────────────────────────────────────────────────

function setupDragDrop() {
  const area = document.getElementById("upload-area");
  area.addEventListener("dragover", e => { e.preventDefault(); area.classList.add("dragover"); });
  area.addEventListener("dragleave", () => area.classList.remove("dragover"));
  area.addEventListener("drop", e => {
    e.preventDefault();
    area.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}
