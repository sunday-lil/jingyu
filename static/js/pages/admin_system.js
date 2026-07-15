/* ============================================================
   静屿 — 系统维护
   - 拉系统信息
   - 一键清 pycache
   ============================================================ */

(function () {
  "use strict";

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));

  function formatBytes(n) {
    if (n < 1024) return n + " B";
    if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
    return (n / 1024 / 1024).toFixed(2) + " MB";
  }

  async function loadInfo() {
    try {
      const data = await QI.fetchJSON("/api/admin/system/info");
      $("[data-info='python_version']").textContent = data.python_version;
      $("[data-info='platform']").textContent = data.platform;
      $("[data-info='base_dir']").textContent = data.base_dir;
      $("[data-info='db_path']").textContent = data.db_path;
      $("[data-info='db_size']").textContent = formatBytes(data.db_size_bytes);
      $("[data-info='log_path']").textContent = data.log_path;
      $("[data-info='log_size']").textContent = formatBytes(data.log_size_bytes);
      $("[data-info='pycache_dirs']").textContent = data.pycache_dirs;
      $("[data-info='pycache_size']").textContent = formatBytes(data.pycache_size_bytes);
    } catch (e) {
      QI.toast("加载系统信息失败：" + e.message, "error");
    }
  }

  async function clearPycaches() {
    const includeVenv = $("[data-include-venv]").checked;
    const resultEl = $("[data-pycaches-result]");
    resultEl.innerHTML = '<div class="admin-action-result__empty">清理中…</div>';
    try {
      const r = await QI.fetchJSON(
        "/api/admin/system/clear-pycaches?include_venv=" + (includeVenv ? "1" : "0"),
        { method: "POST" }
      );
      const paths = r.scanned_paths.length === r.dirs_removed
        ? r.scanned_paths
        : r.scanned_paths;  // 简化：直接显示前 30 条
      const list = paths.slice(0, 30).map((p) =>
        `<div class="admin-action-result__item">
           <span><code>${QI._escape(p)}</code></span>
         </div>`
      ).join("");
      resultEl.innerHTML = `
        <div class="admin-action-result__item" style="font-weight:500;color:var(--color-success);">
          ✓ 完成：${r.dirs_removed} 个目录、${r.files_removed} 个文件，释放 ${formatBytes(r.bytes_freed)}（耗时 ${r.duration_ms}ms）
        </div>
        ${list}
        ${paths.length > 30 ? `<div class="admin-action-result__empty" style="font-size:12px;">… 还有 ${paths.length - 30} 个未显示</div>` : ''}
      `;
      QI.toast("清理完成", "success");
      // 刷新信息卡
      setTimeout(loadInfo, 400);
    } catch (e) {
      resultEl.innerHTML = `<div class="admin-action-result__empty" style="color:var(--color-danger);">失败：${QI._escape(e.message)}</div>`;
      QI.toast(e.message, "error");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    loadInfo();
    $("[data-action='clear-pycaches']").addEventListener("click", clearPycaches);
  });
})();
