/* ============================================================
   静屿 — 漂流瓶日记写作页
   流程：输入 → 加密 → 投瓶动效 → 上传
   ============================================================ */

(function () {
  "use strict";

  const editor = document.getElementById("diary-editor");
  const counter = document.getElementById("char-counter");
  const throwBtn = document.getElementById("throw-bottle");
  const isPublicEl = document.getElementById("is-public");
  const moodItems = document.querySelectorAll(".mood-item");
  const bottle = document.querySelector(".bottle");
  const splash = document.querySelector(".splash");
  const water = document.querySelector(".water-surface");
  const stage = document.querySelector(".bottle-stage");
  const stageWrap = document.getElementById("bottle-wrap");
  const resultWrap = document.getElementById("throw-result");
  const saltEl = document.getElementById("encryption-salt");
  const nicknameEl = document.getElementById("user-nickname");

  if (!editor || !throwBtn) return;

  let selectedMood = null;
  const maxLen = 5000;

  // 字符计数
  editor.addEventListener("input", () => {
    const len = editor.value.length;
    counter.textContent = `${len} / ${maxLen}`;
    counter.style.color = len > maxLen * 0.9 ? "var(--color-warn)" : "var(--color-text-muted)";
  });

  // 心情选择
  moodItems.forEach((el) => {
    el.addEventListener("click", () => {
      moodItems.forEach((m) => m.classList.remove("is-selected"));
      el.classList.add("is-selected");
      selectedMood = el.dataset.mood;
    });
  });

  // 投瓶
  throwBtn.addEventListener("click", async () => {
    const content = editor.value.trim();
    if (!content) {
      QI.toast("纸上还没有字呢", "warn");
      editor.focus();
      return;
    }
    if (content.length > maxLen) {
      QI.toast("字数超了", "error");
      return;
    }

    const nickname = nicknameEl.value;
    const salt = saltEl.value;

    // 询问密码用于加密
    const pwd = await askPassword();
    if (!pwd) return;

    // 验证密码：调一次 login
    try {
      await QI.fetchJSON("/api/auth/login", {
        method: "POST",
        body: { nickname, password: pwd },
      });
    } catch (e) {
      QI.toast("密码不对，无法收好", "error");
      return;
    }

    // 加密
    let encrypted;
    try {
      encrypted = await QI.encryptDiary(content, pwd, salt);
    } catch (e) {
      QI.toast("加密失败：" + e.message, "error");
      return;
    }

    // 投瓶动效
    bottle.classList.add("is-throwing");
    setTimeout(() => splash.classList.add("is-active"), 1000);
    setTimeout(() => water.classList.add("is-active"), 800);
    throwBtn.disabled = true;

    // 上传
    try {
      const resp = await QI.fetchJSON("/api/diary", {
        method: "POST",
        body: {
          content_encrypted: encrypted,
          mood_type: selectedMood,
          is_public: isPublicEl.checked,
        },
      });
      // 动效结束后显示结果
      setTimeout(() => {
        stageWrap.style.display = "none";
        resultWrap.style.display = "block";
        resultWrap.innerHTML = `
          <div class="card fade-in" style="text-align:center;max-width:420px;margin:0 auto;">
            <div style="font-size:64px;margin-bottom:16px;">🌊</div>
            <h2 style="font-family:var(--font-serif);font-weight:400;margin-bottom:8px;">已收好</h2>
            <p style="color:var(--color-text-secondary);margin-bottom:24px;">${resp.granted_energy ? "+2 阳光 ☀️ 已悄悄洒下" : ""}</p>
            <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
              <a href="/my-bottles" class="btn btn--primary">回到我的瓶子</a>
              <a href="/diary" class="btn btn--ghost">再写一封</a>
            </div>
          </div>`;
        // 更新导航能量
        document.querySelectorAll("[data-energy-display]").forEach((el) => {
          el.textContent = resp.new_total_energy;
        });
        QI.toast("瓶子已漂向大海 🌊", "success");
      }, 2000);
    } catch (err) {
      QI.toast(err.message, "error");
      bottle.classList.remove("is-throwing");
      splash.classList.remove("is-active");
      water.classList.remove("is-active");
      throwBtn.disabled = false;
    }
  });

  // ── 温柔版密码询问 ──
  function askPassword() {
    return new Promise((resolve) => {
      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.innerHTML = `
        <div class="modal" role="dialog">
          <h3 style="font-family:var(--font-serif);font-weight:400;margin-bottom:8px;letter-spacing:0.05em;">确认是你的</h3>
          <p style="color:var(--color-text-secondary);font-size:14px;margin-bottom:16px;">请输入密码以加密这封日记。<br>密码不会发送到服务器。</p>
          <input type="password" class="form-input" id="pwd-input" placeholder="密码" autofocus>
          <div id="pwd-error" class="form-error" style="min-height:18px;"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:16px;">
            <button class="btn btn--ghost" data-act="cancel">回 去</button>
            <button class="btn btn--primary" data-act="ok">收 好</button>
          </div>
        </div>`;
      document.body.appendChild(overlay);
      const input = overlay.querySelector("#pwd-input");
      const errEl = overlay.querySelector("#pwd-error");
      input.focus();

      const close = (val) => {
        overlay.remove();
        resolve(val);
      };
      const submit = () => {
        const v = input.value;
        if (v.length < 6) {
          errEl.textContent = "密码至少 6 位";
          return;
        }
        close(v);
      };
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) close(null);
        if (e.target.dataset.act === "cancel") close(null);
        if (e.target.dataset.act === "ok") submit();
      });
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") submit();
        if (e.key === "Escape") close(null);
      });
    });
  }
})();
