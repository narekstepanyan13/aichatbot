const chat = document.getElementById("chat");
const input = document.getElementById("user-input");
const form = document.getElementById("chat-form");
const historyList = document.getElementById("history");
const newChatBtn = document.getElementById("new-chat");
const deleteChatBtn = document.getElementById("delete-chat");
const fileInput = document.getElementById("file-input");
const micButton = document.getElementById("mic-button");

let conversations = {};
let currentChatId = null;

/* ------------------ Helpers ------------------ */
function generateId() {
  return crypto.randomUUID();
}

/* ------------------ Rendering ------------------ */
function renderChat() {
  chat.innerHTML = "";
  if (!currentChatId) return;

  conversations[currentChatId].messages.forEach(m => {
    const div = document.createElement("div");
    div.className = `message ${m.role}`;
    div.innerText = m.text;
    chat.appendChild(div);
  });

  chat.scrollTop = chat.scrollHeight;
}

function renderSidebar() {
  historyList.innerHTML = "";

  Object.entries(conversations).forEach(([id, conv]) => {
    const li = document.createElement("li");
    li.textContent = conv.title;

    li.onclick = () => {
      currentChatId = id;
      renderChat();
    };

    historyList.appendChild(li);
  });
}

/* ------------------ New Chat ------------------ */
function startNewChat() {
  const id = generateId();

  conversations[id] = {
    title: "New Chat",
    messages: []
  };

  currentChatId = id;
  renderSidebar();
  renderChat();
}

/* ------------------ Send Message ------------------ */
async function sendMessage(text) {
  if (!text.trim()) return;

  // If user types without clicking "New Chat"
  if (!currentChatId) {
    startNewChat();
  }

  const conv = conversations[currentChatId];

  // User message
  conv.messages.push({ role: "user", text });
  input.value = "";
  renderChat();

  // Generate title on FIRST message ONLY
  if (conv.messages.length === 1) {
    conv.title = text.slice(0, 30) + (text.length > 30 ? "…" : "");
    renderSidebar();
  }

  try {
    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    const data = await res.json();
    conv.messages.push({ role: "bot", text: data.reply });
    renderChat();
  } catch {
    conv.messages.push({ role: "bot", text: "⚠️ Error contacting AI" });
    renderChat();
  }
}

/* ------------------ Form ------------------ */
form.addEventListener("submit", e => {
  e.preventDefault();
  sendMessage(input.value);
});

/* ------------------ Delete Chat ------------------ */
deleteChatBtn.addEventListener("click", () => {
  if (!currentChatId) return;

  delete conversations[currentChatId];
  currentChatId = null;

  renderSidebar();
  chat.innerHTML = "";
});

/* ------------------ File Upload ------------------ */
document.getElementById("file-button").onclick = () => fileInput.click();
fileInput.onchange = () => {
  Array.from(fileInput.files).forEach(file => {
    input.value += (input.value ? " " : "") + file.name;
  });
};

/* ------------------ Voice Input ------------------ */
let recognition;
if ("webkitSpeechRecognition" in window) {
  recognition = new webkitSpeechRecognition();
  recognition.lang = "en-US";

  recognition.onresult = e => {
    input.value += (input.value ? " " : "") + e.results[0][0].transcript;
  };
}

micButton.onclick = () => {
  if (recognition) recognition.start();
  else alert("Speech recognition not supported");
};

/* ------------------ Buttons ------------------ */
newChatBtn.onclick = startNewChat;
