/* ============================================================
   静屿 — 后台概览
   拉 /api/admin/stats 和 /api/admin/activity 渲染
   ============================================================ */

(function () {
  "use strict";

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));

  function formatTime(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleString("zh-CN", { hour12: false });
  }

  function renderStats(s) {
    $$("[data-stat]").forEach((el) => {
      const k = el.dataset.stat;
      if (s && typeof s[k] !== "undefined") el.textContent = s[k];
    });
  }

  function renderActivity(data) {
    const map = {
      diaries: "[data-list='diaries']",
      moods: "[data-list='moods']",
      users: "[data-list='users']",
    };
    Object.keys(map).forEach((key) => {
      const ul = $(map[key]);
      if (!ul) return;
      const items = data[key === "moods" ? "mood_checkins" : key] || [];
      if (!items.length) {
        ul.innerHTML = '<li class="admin-activity-empty">暂无</li>';
        return;
      }
      ul.innerHTML = items.map((it) => {
        if (key === "diaries") {
          return `<li>
            <span>${QI._escape(it.nickname)} <code>#${it.id}</code> ${it.mood_type || ''}</span>
            <span>${formatTime(it.created_at)}</span>
          </li>`;
        }
        if (key === "moods") {
          return `<li>
            <span>${QI._escape(it.nickname)} <code>${QI._escape(it.mood_emoji)}</code></span>
            <span>${it.check_date || ''}</span>
          </li>`;
        }
        // users
        return `<li>
          <span>${QI._escape(it.nickname)}${it.is_admin ? ' 🗝️' : ''}</span>
          <span>${formatTime(it.created_at)}</span>
        </li>`;
      }).join("");
    });
  }

  async function refresh() {
    try {
      const [stats, activity] = await Promise.all([
        QI.fetchJSON("/api/admin/stats"),
        QI.fetchJSON("/api/admin/activity?limit=8"),
      ]);
      renderStats(stats);
      renderActivity(activity);
    } catch (e) {
      QI.toast("刷新失败：" + e.message, "error");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    refresh();
    $$("[data-action='refresh-stats']").forEach((b) =>
      b.addEventListener("click", refresh)
    );
  });
})();
