/* ============================================================
   静屿 — 首页（AI 帮我选音）
   ============================================================ */

(function () {
  "use strict";

  const btn = document.getElementById("ai-mood-btn");
  const input = document.getElementById("ai-mood-input");
  if (!btn || !input) return; // 未登录页不渲染该卡

  const reasonEl = document.getElementById("ai-mood-reason");
  const goEl = document.getElementById("ai-mood-go");
  const resultBox = document.getElementById("ai-mood-result");
  if (!reasonEl || !goEl || !resultBox) return;

  const YIN_NAMES = {
    gong: "宫", shang: "商", jue: "角", zhi: "徵", yu: "羽",
  };

  async function recommend() {
    const state = input.value.trim();
    btn.disabled = true;
    const origText = btn.textContent;
    btn.textContent = "海在听…";
    try {
      const resp = await QI.fetchJSON("/api/ai/recommend-music", {
        method: "POST",
        body: { user_state: state || null },
      });
      if (!resp || !resp.yin) {
        QI.toast("AI 暂时不在岛上", "info");
        return;
      }
      const yin = resp.yin;
      const yinName = YIN_NAMES[yin] || yin;
      reasonEl.textContent = `${yinName}音 — ${resp.reason}`;
      goEl.href = `/music/${yin}`;
      resultBox.style.display = "block";
      // 平滑滚动到结果
      setTimeout(() => resultBox.scrollIntoView({ behavior: "smooth", block: "nearest" }), 100);
    } catch (e) {
      QI.toast(e.message || "AI 暂时不在岛上", "error");
    } finally {
      btn.disabled = false;
      btn.textContent = origText;
    }
  }

  btn.addEventListener("click", recommend);
  // Enter 触发
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      recommend();
    }
  });
})();
