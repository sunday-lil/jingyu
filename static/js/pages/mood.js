/* ============================================================
   静屿 — 今日心情手帐
   ============================================================ */

(function () {
  "use strict";

  const moodItems = document.querySelectorAll(".mood-item");
  const saveBtn = document.getElementById("save-mood");
  const noteEl = document.getElementById("mood-note");
  if (!moodItems.length || !saveBtn) return;

  let selectedMood = null;

  moodItems.forEach((el) => {
    el.addEventListener("click", () => {
      moodItems.forEach((m) => m.classList.remove("is-selected"));
      el.classList.add("is-selected");
      selectedMood = el.dataset.mood;
    });
  });

  // 预选已存在
  const initial = document.querySelector(".mood-item.is-selected");
  if (initial) selectedMood = initial.dataset.mood;

  saveBtn.addEventListener("click", async () => {
    if (!selectedMood) {
      QI.toast("先选一个心情吧", "warn");
      return;
    }
    saveBtn.disabled = true;
    saveBtn.textContent = "收 好…";
    try {
      const resp = await QI.fetchJSON("/api/mood/checkin", {
        method: "POST",
        body: {
          mood_emoji: selectedMood,
          note: noteEl.value.trim() || null,
        },
      });
      QI.toast("+1 养分 🌱", "success");
      QI.floatEnergy("+1 养分", saveBtn);
      // 更新能量显示
      document.querySelectorAll("[data-energy-display]").forEach((el) => {
        const m = (el.textContent || "0");
        el.textContent = String(parseInt(m) + 1);
      });
      saveBtn.textContent = "✓ 已收好";
    } catch (e) {
      QI.toast(e.message, "error");
      saveBtn.disabled = false;
      saveBtn.textContent = "收 好";
    }
  });
})();
