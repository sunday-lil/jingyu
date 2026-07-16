/* ============================================================
   静屿 — 情绪日历 + 今日打卡 + 30 天趋势
   （2026-07-15 合并原 /mood 打卡页，甲方要求「每日手帐与日历合一」）
   ============================================================ */

(function () {
  "use strict";

  const calendarEl = document.getElementById("calendar");
  const trendEl = document.getElementById("trend-chart");
  const monthTitleEl = document.getElementById("month-title");
  const prevBtn = document.getElementById("prev-month");
  const nextBtn = document.getElementById("next-month");
  const streakEl = document.getElementById("streak");
  if (!calendarEl || !trendEl) return;

  // ── 今日打卡（合并自 mood.js） ──
  const moodItems = document.querySelectorAll(".mood-item");
  const saveBtn = document.getElementById("save-mood");
  const noteEl = document.getElementById("mood-note");
  let selectedMood = null;

  if (moodItems.length && saveBtn) {
    moodItems.forEach((el) => {
      el.addEventListener("click", () => {
        moodItems.forEach((m) => m.classList.remove("is-selected"));
        el.classList.add("is-selected");
        selectedMood = el.dataset.mood;
      });
    });
    // 预选已存在的今日记录
    const initial = document.querySelector(".mood-item.is-selected");
    if (initial) selectedMood = initial.dataset.mood;

    saveBtn.addEventListener("click", async () => {
      if (!selectedMood) {
        QI.toast("先选一个心情吧", "warn");
        return;
      }
      saveBtn.disabled = true;
      const origText = saveBtn.textContent;
      saveBtn.textContent = "收 好…";
      try {
        await QI.fetchJSON("/api/mood/checkin", {
          method: "POST",
          body: {
            mood_emoji: selectedMood,
            note: noteEl.value.trim() || null,
          },
        });
        QI.toast("+1 养分 🌱", "success");
        QI.floatEnergy("+1 养分", saveBtn);
        QI.confetti(saveBtn, { glyphs: ["🌱", "🌿", "🌸", "✨"] });
        // 更新能量显示
        document.querySelectorAll("[data-energy-display]").forEach((el) => {
          const m = (el.textContent || "0");
          el.textContent = String(parseInt(m) + 1);
        });
        saveBtn.textContent = "✓ 已收好";
        // 刷新日历今日格子 + 趋势 + 连胜
        loadCalendar();
        loadTrend();
      } catch (e) {
        QI.toast(e.message, "error");
        saveBtn.disabled = false;
        saveBtn.textContent = origText;
      }
    });
  }

  // ── 日历 + 趋势 ──
  let viewYear, viewMonth;
  const today = new Date();
  viewYear = today.getFullYear();
  viewMonth = today.getMonth() + 1;

  function moodColor(code) {
    const map = {
      ecstatic: "#FFD56B", happy: "#F6B26B", calm: "#A8D5BA",
      tired: "#B8B5C5", anxious: "#9BB5D5", angry: "#E89A9A", sad: "#A5A8C5",
    };
    return map[code] || null;
  }

  function moodEmoji(code) {
    const map = {
      ecstatic: "🤩", happy: "😊", calm: "😌",
      tired: "😪", anxious: "😰", angry: "😠", sad: "😢",
    };
    return map[code] || null;
  }

  async function loadCalendar() {
    monthTitleEl.textContent = `${viewYear} 年 ${viewMonth} 月`;
    const data = await QI.fetchJSON(`/api/mood/calendar?year=${viewYear}&month=${viewMonth}`);
    renderCalendar(data.items);
  }

  async function loadTrend() {
    const data = await QI.fetchJSON("/api/mood/trend?days=30");
    renderTrend(data.items);
    if (streakEl) {
      streakEl.textContent = `已连续 ${data.current_streak} 天`;
    }
  }

  function renderCalendar(items) {
    const byDate = Object.fromEntries(items.map((i) => [i.check_date, i]));
    const firstDay = new Date(viewYear, viewMonth - 1, 1);
    const lastDay = new Date(viewYear, viewMonth, 0);
    const startWeekday = firstDay.getDay();
    const daysInMonth = lastDay.getDate();

    const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
    let html = weekdays.map((w) => `<div class="calendar__weekday">${w}</div>`).join("");

    for (let i = 0; i < startWeekday; i++) {
      html += `<div class="calendar__day"></div>`;
    }

    const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${viewYear}-${String(viewMonth).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
      const record = byDate[dateStr];
      const isToday = dateStr === todayStr;
      const isFuture = new Date(dateStr) > today;
      const isChecked = record && !isFuture;

      const bgColor = isChecked ? moodColor(record.mood_emoji) : null;
      const emoji = isChecked ? moodEmoji(record.mood_emoji) : null;
      const title = record?.note ? ` title="${QI._escape ? QI._escape(record.note) : record.note}"` : "";

      const classes = [
        "calendar__day",
        isToday ? "is-today" : "",
        isFuture ? "is-future" : "",
        isChecked ? "is-checked" : "",
      ].filter(Boolean).join(" ");

      const style = bgColor ? ` style="background:${bgColor}"` : "";
      const emojiHtml = emoji ? `<span class="mood-emoji">${emoji}</span>` : "";

      html += `<div class="${classes}"${style}${title}>${d}${emojiHtml}</div>`;
    }
    calendarEl.innerHTML = html;
  }

  function renderTrend(items) {
    const moodToHeight = {
      ecstatic: 100, happy: 90, calm: 70,
      tired: 50, anxious: 40, angry: 30, sad: 20,
    };
    let html = "";
    items.forEach((it) => {
      const color = it.mood_emoji ? moodColor(it.mood_emoji) : null;
      const height = it.mood_emoji ? moodToHeight[it.mood_emoji] || 50 : 8;
      const classes = it.mood_emoji ? "trend-bar" : "trend-bar is-empty";
      const style = color ? ` style="height:${height}%;background:${color}"` : "";
      const title = it.mood_emoji ? `${it.date} · ${it.label}` : `${it.date} · 无`;
      html += `<div class="${classes}"${style} title="${title}"></div>`;
    });
    trendEl.innerHTML = html;
  }

  prevBtn.addEventListener("click", () => {
    viewMonth -= 1;
    if (viewMonth < 1) { viewMonth = 12; viewYear -= 1; }
    loadCalendar();
  });
  nextBtn.addEventListener("click", () => {
    viewMonth += 1;
    if (viewMonth > 12) { viewMonth = 1; viewYear += 1; }
    loadCalendar();
  });

  loadCalendar();
  loadTrend();
})();
