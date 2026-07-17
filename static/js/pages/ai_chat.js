/* ============================================================
   静屿 — AI 树洞对话（NVIDIA NIM 接入）
   对话历史只在浏览器内存里，刷新即清空，保护隐私。
   ============================================================ */

(function () {
  "use strict";

  const messagesEl = document.getElementById("chat-messages");
  const inputEl = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");
  if (!messagesEl || !inputEl || !sendBtn) return;

  // 内存里的对话历史（OpenAI 格式），刷新即清空
  const history = [];
  let sending = false;

  function scrollBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function appendMsg(role, text) {
    const isUser = role === "user";
    const wrap = document.createElement("div");
    wrap.className = `chat-msg chat-msg--${isUser ? "user" : "ai"}`;
    const avatar = isUser ? "🪶" : "🌿";
    wrap.innerHTML = `
      <div class="chat-msg__avatar">${avatar}</div>
      <div class="chat-msg__bubble"></div>
    `;
    // 用 textContent 防注入
    wrap.querySelector(".chat-msg__bubble").textContent = text;
    messagesEl.appendChild(wrap);
    scrollBottom();
  }

  function appendLoading() {
    const wrap = document.createElement("div");
    wrap.className = "chat-msg chat-msg--ai chat-msg--loading";
    wrap.id = "chat-loading";
    wrap.innerHTML = `
      <div class="chat-msg__avatar">🌿</div>
      <div class="chat-msg__bubble"><span class="chat-typing"><span></span><span></span><span></span></span></div>
    `;
    messagesEl.appendChild(wrap);
    scrollBottom();
  }

  function removeLoading() {
    const el = document.getElementById("chat-loading");
    if (el) el.remove();
  }

  async function send() {
    if (sending) return;
    const text = inputEl.value.trim();
    if (!text) return;
    sending = true;
    sendBtn.disabled = true;
    inputEl.value = "";
    inputEl.style.height = "auto";

    appendMsg("user", text);
    history.push({ role: "user", content: text });

    appendLoading();
    try {
      const data = await QI.fetchJSON("/api/ai/chat", {
        method: "POST",
        body: { messages: history },
      });
      removeLoading();
      appendMsg("assistant", data.reply);
      history.push({ role: "assistant", content: data.reply });
      if (!data.available) {
        QI.toast("AI 暂时不在岛上，先把想说的话留着", "warn");
      }
    } catch (e) {
      removeLoading();
      appendMsg("assistant", "海风停了一下，稍后再来。");
      QI.toast(e.message, "error");
    } finally {
      sending = false;
      sendBtn.disabled = false;
      inputEl.focus();
    }
  }

  sendBtn.addEventListener("click", send);
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });
  // 自动撑高 textarea
  inputEl.addEventListener("input", () => {
    inputEl.style.height = "auto";
    inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + "px";
  });

  inputEl.focus();
})();
