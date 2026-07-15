/* ============================================================
   静屿 — 我的瓶子（时间线解密）
   ============================================================ */

(function () {
  "use strict";

  const list = document.getElementById("bottles-list");
  if (!list) return;

  const items = list.querySelectorAll(".timeline-item");
  const saltEl = document.getElementById("encryption-salt");
  const nicknameEl = document.getElementById("user-nickname");
  const salt = saltEl?.value;

  let password = null;  // 会话级缓存

  async function ensurePassword() {
    if (password) return password;
    password = await askPassword();
    return password;
  }

  items.forEach((item) => {
    const previewEl = item.querySelector(".timeline-item__preview");
    const token = item.dataset.encrypted;
    const mood = item.dataset.mood;

    item.addEventListener("click", async () => {
      const pwd = await ensurePassword();
      if (!pwd) return;

      // 验证密码
      try {
        await QI.fetchJSON("/api/auth/login", {
          method: "POST",
          body: { nickname: nicknameEl.value, password: pwd },
        });
      } catch {
        QI.toast("密码不对", "error");
        password = null;
        return;
      }

      // 跳转详情页（详情页会再次解密）
      location.href = `/my-bottles/${item.dataset.id}`;
    });
  });

  function askPassword() {
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.innerHTML = `
        <div class="modal">
          <h3 style="font-family:var(--font-serif);font-weight:400;margin-bottom:8px;">第一次打开，需要你的钥匙</h3>
          <p style="color:var(--color-text-secondary);font-size:14px;margin-bottom:16px;">输入密码，解锁属于你的瓶子们。<br>会话期间只需输入一次。</p>
          <input type="password" class="form-input" id="pwd-input" autofocus>
          <div id="pwd-error" class="form-error" style="min-height:18px;"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
            <button class="btn btn--ghost" data-act="cancel">暂 不</button>
            <button class="btn btn--primary" data-act="ok">解 锁</button>
          </div>
        </div>`;
      document.body.appendChild(overlay);
      const input = overlay.querySelector("#pwd-input");
      input.focus();
      const close = (v) => { overlay.remove(); resolve(v); };
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) close(null);
        if (e.target.dataset.act === "cancel") close(null);
        if (e.target.dataset.act === "ok") {
          if (input.value.length < 6) {
            overlay.querySelector("#pwd-error").textContent = "密码至少 6 位";
            return;
          }
          close(input.value);
        }
      });
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") overlay.querySelector('[data-act="ok"]').click();
        if (e.key === "Escape") close(null);
      });
    });
  }
})();
