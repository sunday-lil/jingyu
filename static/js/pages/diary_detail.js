/* ============================================================
   静屿 — 单个瓶子详情页
   ============================================================ */

(function () {
  "use strict";

  const contentEl = document.getElementById("diary-content");
  if (!contentEl) return;

  const encrypted = contentEl.dataset.encrypted;
  const salt = document.getElementById("encryption-salt")?.value;
  const nickname = document.getElementById("user-nickname")?.value;
  const encryptedEl = document.getElementById("encrypted-state");
  const unlockBtn = document.getElementById("unlock-btn");

  unlockBtn?.addEventListener("click", async () => {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal">
        <h3 style="font-family:var(--font-serif);font-weight:400;margin-bottom:8px;">输入密码</h3>
        <input type="password" class="form-input" id="pwd-input" autofocus>
        <div id="pwd-error" class="form-error" style="min-height:18px;"></div>
        <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
          <button class="btn btn--ghost" data-act="cancel">取 消</button>
          <button class="btn btn--primary" data-act="ok">展 开</button>
        </div>
      </div>`;
    document.body.appendChild(overlay);
    const input = overlay.querySelector("#pwd-input");
    input.focus();
    overlay.addEventListener("click", async (e) => {
      if (e.target === overlay) overlay.remove();
      if (e.target.dataset.act === "cancel") overlay.remove();
      if (e.target.dataset.act === "ok") {
        const pwd = input.value;
        try {
          await QI.fetchJSON("/api/auth/login", {
            method: "POST",
            body: { nickname, password: pwd },
          });
        } catch {
          overlay.querySelector("#pwd-error").textContent = "密码不对";
          return;
        }
        const text = await QI.decryptDiary(encrypted, pwd, salt);
        overlay.remove();
        if (text === null) {
          QI.toast("解不开，可能密码换了", "error");
          return;
        }
        contentEl.textContent = text;
        encryptedEl.style.display = "none";
        QI.toast("已展开", "success", 1200);
      }
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") overlay.querySelector('[data-act="ok"]').click();
    });
  });
})();
