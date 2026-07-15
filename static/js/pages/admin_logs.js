/* ============================================================
   静屿 — 运行日志
   - tail N 行，可按级别过滤
   - 可选 3s 自动刷新
   - 颜色按 level 标
   ============================================================ */

(function () {
  "use strict";

  const $ = (s) => document.querySelector(s);
  const logEl = $("[data-log]");
  const metaEl = $("[data-meta]");
  const levelEl = $("[data-level]");
  const linesEl = $("[data-lines]");
  const autoEl = $("[data-auto]");

  let timer = null;

  function colorize(line) {
    if (line.includes("[INFO]")) return `<span class="lvl-INFO">${QI._escape(line)}</span>`;
    if (line.includes("[WARNING]")) return `<span class="lvl-WARNING">${QI._escape(line)}</span>`;
    if (line.includes("[ERROR]")) return `<span class="lvl-ERROR">${QI._escape(line)}</span>`;
    if (line.includes("[DEBUG]")) return `<span class="lvl-DEBUG">${QI._escape(line)}</span>`;
    return QI._escape(line);
  }

  function formatBytes(n) {
    if (n < 1024) return n + " B";
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
    return (n / 1024 / 1024).toFixed(2) + " MB";
  }

  async function refresh() {
    try {
      const params = new URLSearchParams({
        level: levelEl.value,
        lines: linesEl.value,
      });
      const data = await QI.fetchJSON("/api/admin/logs?" + params);
      if (!data.exists) {
        logEl.textContent = `(日志文件不存在：${data.path})`;
        metaEl.textContent = "—";
        return;
      }
      logEl.innerHTML = data.lines.length
        ? data.lines.map(colorize).join("\n")
        : "(空)";
      metaEl.textContent = `${formatBytes(data.size_bytes)} · 共 ${data.total_lines} 行（过滤后）`;
      // 自动滚到底
      logEl.scrollTop = logEl.scrollHeight;
    } catch (e) {
      logEl.textContent = "加载失败：" + e.message;
    }
  }

  function startAuto() {
    stopAuto();
    timer = setInterval(refresh, 3000);
  }
  function stopAuto() {
    if (timer) { clearInterval(timer); timer = null; }
  }

  document.addEventListener("DOMContentLoaded", () => {
    refresh();
    $("[data-action='refresh']").addEventListener("click", refresh);
    levelEl.addEventListener("change", refresh);
    linesEl.addEventListener("change", refresh);
    autoEl.addEventListener("change", () => autoEl.checked ? startAuto() : stopAuto());
    $("[data-action='download']").addEventListener("click", () => {
      // 让浏览器直接下载日志文件（admin API 没暴露 /logs/download，
      // 但浏览器能直接 GET /api/admin/logs?lines=2000 复制粘贴）
      QI.toast("可右键日志区 → '另存为'，或直接 fetchJSON 后保存", "info", 3600);
    });
  });
})();
