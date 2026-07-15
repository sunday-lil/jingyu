/* ============================================================
   静屿 — 拾取陌生人漂流瓶
   ============================================================ */

(function () {
  "use strict";

  const pickBtn = document.getElementById("pick-btn");
  if (!pickBtn) return;

  const salt = document.getElementById("user-salt")?.value;
  const empty = document.getElementById("pick-empty");
  const result = document.getElementById("pick-result");
  const contentEl = document.getElementById("bottle-content");
  const moodEl = document.getElementById("bottle-mood");
  const dateEl = document.getElementById("bottle-date");
  const encourageBtn = document.getElementById("encourage-btn");
  const encourageInput = document.getElementById("encourage-input");
  const encouragementsEl = document.getElementById("bottle-encouragements");

  let currentDiary = null;
  let password = null;

  async function askPassword() {
    if (password) return password;
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.innerHTML = `
        <div class="modal">
          <h3 style="font-family:var(--font-serif);font-weight:400;margin-bottom:8px;">输入你的密码</h3>
          <p style="color:var(--color-text-secondary);font-size:14px;margin-bottom:16px;">用来打开漂来的瓶子。<br>密码只在本机使用。</p>
          <input type="password" class="form-input" id="pwd-input" autofocus>
          <div id="pwd-error" class="form-error" style="min-height:18px;"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
            <button class="btn btn--ghost" data-act="cancel">离 开</button>
            <button class="btn btn--primary" data-act="ok">拾 起</button>
          </div>
        </div>`;
      document.body.appendChild(overlay);
      const input = overlay.querySelector("#pwd-input");
      input.focus();
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) { overlay.remove(); resolve(null); }
        if (e.target.dataset.act === "cancel") { overlay.remove(); resolve(null); }
        if (e.target.dataset.act === "ok") {
          const v = input.value;
          if (v.length < 6) {
            overlay.querySelector("#pwd-error").textContent = "密码至少 6 位";
            return;
          }
          overlay.remove();
          resolve(v);
        }
      });
    });
  }

  pickBtn.addEventListener("click", async () => {
    pickBtn.disabled = true;
    pickBtn.textContent = "海面上寻找…";
    try {
      const data = await QI.fetchJSON("/api/diary/pick/random");
      if (!data) {
        empty.style.display = "block";
        result.style.display = "none";
        return;
      }
      currentDiary = data;

      // 询问密码
      const pwd = await askPassword();
      if (!pwd) {
        pickBtn.disabled = false;
        pickBtn.textContent = "再拾一个";
        return;
      }
      password = pwd;

      // 解密（用日记所有者的 salt + 当前用户密码）
      const text = await QI.decryptDiary(data.content_encrypted, pwd, data.salt);
      if (text === null) {
        QI.toast("这个瓶子被海浪打湿了，开不了", "error");
        pickBtn.disabled = false;
        pickBtn.textContent = "再拾一个";
        return;
      }
      // 显示内容
      empty.style.display = "none";
      result.style.display = "block";
      contentEl.textContent = text;
      const moodInfo = JSON.parse(contentEl.dataset.moodInfo || "{}");
      const info = moodInfo[data.mood_type];
      moodEl.textContent = info ? `${info.emoji} ${info.label}` : "无署名";
      dateEl.textContent = QI.formatDate(data.created_at);
    } catch (e) {
      QI.toast(e.message, "error");
    } finally {
      pickBtn.disabled = false;
      pickBtn.textContent = "再拾一个";
    }
  });

  encourageBtn?.addEventListener("click", async () => {
    if (!currentDiary) return;
    const text = encourageInput.value.trim();
    if (!text) {
      QI.toast("写一句话再寄出", "warn");
      return;
    }
    try {
      await QI.fetchJSON(`/api/diary/${currentDiary.id}/encourage`, {
        method: "POST",
        body: { content: text },
      });
      encourageInput.value = "";
      QI.toast("已悄悄送达 🌿", "success");
    } catch (e) {
      QI.toast(e.message, "error");
    }
  });
})();
