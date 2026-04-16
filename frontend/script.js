// AIRag – Frontend Logic

const API_BASE = window.location.origin;

// DOM elements
const fileInput = document.getElementById("file-input");
const fileName = document.getElementById("file-name");
const uploadBtn = document.getElementById("upload-btn");
const uploadForm = document.getElementById("upload-form");
const uploadStatus = document.getElementById("upload-status");
const chatForm = document.getElementById("chat-form");
const questionInput = document.getElementById("question-input");
const chatMessages = document.getElementById("chat-messages");
const docCount = document.getElementById("doc-count");
const clearBtn = document.getElementById("clear-btn");

// ------------------------------------------------------------------
// File upload
// ------------------------------------------------------------------

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        fileName.textContent = fileInput.files[0].name;
        uploadBtn.disabled = false;
    } else {
        fileName.textContent = "No file selected";
        uploadBtn.disabled = true;
    }
});

uploadForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!fileInput.files.length) return;

    uploadBtn.disabled = true;
    showStatus("Uploading and processing…", "loading");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const res = await fetch(`${API_BASE}/api/upload`, {
            method: "POST",
            body: formData,
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Upload failed");
        }
        showStatus(`${data.message} (${data.chunks} chunks)`, "success");
        refreshHealth();
    } catch (err) {
        showStatus(`Error: ${err.message}`, "error");
    } finally {
        uploadBtn.disabled = false;
    }
});

// ------------------------------------------------------------------
// Chat / Query
// ------------------------------------------------------------------

chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = questionInput.value.trim();
    if (!question) return;

    addMessage(question, "user");
    questionInput.value = "";

    try {
        const res = await fetch(`${API_BASE}/api/query`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question }),
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Query failed");
        }

        let answerHtml = `<p>${escapeHtml(data.answer)}</p>`;
        if (data.sources && data.sources.length > 0) {
            const sourceSnippets = data.sources
                .filter((s) => s.text)
                .slice(0, 3)
                .map((s) => escapeHtml(s.text.slice(0, 100)))
                .join(" | ");
            if (sourceSnippets) {
                answerHtml += `<div class="sources">Sources: ${sourceSnippets}…</div>`;
            }
        }
        addMessage(answerHtml, "assistant", true);
    } catch (err) {
        addMessage(`Error: ${err.message}`, "assistant");
    }
});

// ------------------------------------------------------------------
// Clear documents
// ------------------------------------------------------------------

clearBtn.addEventListener("click", async () => {
    if (!confirm("Clear all ingested documents?")) return;
    try {
        await fetch(`${API_BASE}/api/documents`, { method: "DELETE" });
        refreshHealth();
        showStatus("All documents cleared.", "success");
    } catch {
        showStatus("Failed to clear documents.", "error");
    }
});

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

function addMessage(content, role, isHtml = false) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    if (isHtml) {
        div.innerHTML = content;
    } else {
        div.textContent = content;
    }
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showStatus(text, type) {
    uploadStatus.textContent = text;
    uploadStatus.className = `status ${type}`;
    uploadStatus.hidden = false;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

async function refreshHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        const data = await res.json();
        docCount.textContent = `Documents: ${data.vector_store_size} chunks`;
    } catch {
        // Silently ignore health check failures
    }
}

// Initial health check
refreshHealth();
