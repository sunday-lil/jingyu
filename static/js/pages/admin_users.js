/* ============================================================
   静屿 — 用户列表
   - 搜索 / 仅管理员筛选（前端本地过滤；如有需要再走后端）
   - 分页
   - 重置密码 / 代建用户
   ============================================================ */

(function () {
  "use strict";

  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));

  const state = { page: 1, pageSize: 20, q: "", adminOnly: false };
  const tbody = $("[data-tbody]");
  const countEl = $("[data-count]");
  const pagerInfo = $("[data-pager-info]");

  function formatTime(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleString("zh-CN", { hour12: false });
  }

  function applyLocalTimes() {
    $$("[data-iso]").forEach((el) => {
      const iso = el.dataset.iso;
      if (iso) el.textContent = formatTime(iso);
    });
  }

  function rowHTML(u) {
    return `<tr data-row data-user-id="${u.id}" data-nickname="${QI._escape(u.nickname)}">
      <td><code>#${u.id}</code></td>
      <td><a href="/admin/users/${u.id}" class="admin-table__name">${QI._escape(u.nickname)}</a></td>
      <td>${u.is_admin ? '<span class="admin-tag admin-tag--admin">管理员</span>' : '<span class="admin-tag">用户</span>'}</td>
      <td>${u.total_energy}</td>
      <td>${u.diary_count} <span style="color:var(--color-text-muted);font-size:12px;">(公${u.public_diary_count})</span></td>
      <td>${u.mood_count}</td>
      <td><span data-iso="${u.created_at || ''}"></span></td>
      <td>
        <a class="btn btn--ghost btn--sm" href="/admin/users/${u.id}">查看</a>
        <button class="btn btn--ghost btn--sm" data-action="reset-password" data-user-id="${u.id}" data-nickname="${QI._escape(u.nickname)}">重置密码</button>
      </td>
    </tr>`;
  }

  async function fetchPage() {
    try {
      const params = new URLSearchParams({
        page: state.page,
        page_size: state.pageSize,
        q: state.q,
      });
      if (state.adminOnly) params.set("admin_only", "1");
      const data = await QI.fetchJSON("/api/admin/users?" + params);
      tbody.innerHTML = data.items.length
        ? data.items.map(rowHTML).join("")
        : '<tr><td colspan="8" class="admin-empty">无匹配用户</td></tr>';
      countEl.textContent = `共 ${data.total} 人`;
      const totalPages = Math.max(1, Math.ceil(data.total / data.page_size));
      pagerInfo.textContent = `第 ${data.page} / ${totalPages} 页`;
      applyLocalTimes();
    } catch (e) {
      QI.toast("加载失败：" + e.message, "error");
    }
  }

  // ── 重置密码弹窗 ──
  function openResetPassword(userId, nickname) {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true">
        <h3 style="margin:0 0 8px;">重置「${QI._escape(nickname)}」的密码</h3>
        <p style="color:var(--color-text-secondary);font-size:13px;margin:0 0 16px;">
          ⚠️ 重置后旧密码派生的加密日记将无法在该用户本机解密（除非他们记得旧密码）。
        </p>
        <form data-form>
          <div class="form-field">
            <label class="form-label">新密码（至少 6 位）</label>
            <input type="password" name="new_password" minlength="6" required class="form-input">
          </div>
          <div class="form-field">
            <label class="form-label">再次输入</label>
            <input type="password" name="confirm" minlength="6" required class="form-input">
          </div>
          <div class="form-error" data-err style="min-height:18px;margin-bottom:8px;color:var(--color-danger);font-size:13px;"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;">
            <button type="button" class="btn btn--ghost" data-cancel>取消</button>
            <button type="submit" class="btn btn--primary">确认重置</button>
          </div>
        </form>
      </div>`;
    document.body.appendChild(overlay);
    const close = () => overlay.remove();
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
      if (e.target.dataset.cancel !== undefined) close();
    });
    const form = overlay.querySelector("[data-form]");
    const errEl = overlay.querySelector("[data-err]");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      const p1 = fd.get("new_password");
      const p2 = fd.get("confirm");
      if (p1 !== p2) { errEl.textContent = "两次输入不一致"; return; }
      try {
        const r = await QI.fetchJSON(`/api/admin/users/${userId}/reset-password`, {
          method: "POST",
          body: { new_password: p1 },
        });
        QI.toast(`已重置 ${nickname} 的密码`, "success");
        close();
        if (r.warning) setTimeout(() => QI.toast(r.warning, "info", 4800), 200);
      } catch (err) {
        errEl.textContent = err.message;
      }
    });
    overlay.querySelector('input[name="new_password"]').focus();
  }

  // ── 代建用户弹窗 ──
  function openCreateUser() {
    const overlay = document.createElement("div");
    overlay.className = "modal-overlay";
    overlay.innerHTML = `
      <div class="modal" role="dialog" aria-modal="true">
        <h3 style="margin:0 0 8px;">+ 代建用户</h3>
        <p style="color:var(--color-text-secondary);font-size:13px;margin:0 0 16px;">
          管理员代为创建一个普通用户（用于不擅长自注册的家人朋友）。
        </p>
        <form data-form>
          <div class="form-field">
            <label class="form-label">昵称（2-20 字）</label>
            <input type="text" name="nickname" minlength="2" maxlength="20" required class="form-input">
          </div>
          <div class="form-field">
            <label class="form-label">初始密码（至少 6 位）</label>
            <input type="password" name="password" minlength="6" required class="form-input">
          </div>
          <div class="form-field">
            <label class="admin-checkbox">
              <input type="checkbox" name="is_admin"> 创建为管理员
            </label>
          </div>
          <div class="form-error" data-err style="min-height:18px;margin-bottom:8px;color:var(--color-danger);font-size:13px;"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;">
            <button type="button" class="btn btn--ghost" data-cancel>取消</button>
            <button type="submit" class="btn btn--primary">创建</button>
          </div>
        </form>
      </div>`;
    document.body.appendChild(overlay);
    const close = () => overlay.remove();
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) close();
      if (e.target.dataset.cancel !== undefined) close();
    });
    const form = overlay.querySelector("[data-form]");
    const errEl = overlay.querySelector("[data-err]");
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        const r = await QI.fetchJSON("/api/admin/users", {
          method: "POST",
          body: {
            nickname: fd.get("nickname"),
            password: fd.get("password"),
            is_admin: fd.get("is_admin") === "on",
          },
        });
        QI.toast("已创建用户：" + r.nickname, "success");
        close();
        fetchPage();
      } catch (err) { errEl.textContent = err.message; }
    });
    overlay.querySelector('input[name="nickname"]').focus();
  }

  // ── 事件绑定 ──
  document.addEventListener("DOMContentLoaded", () => {
    applyLocalTimes();
    fetchPage();

    // 搜索（防抖）
    const search = $("[data-search]");
    let t = null;
    search && search.addEventListener("input", () => {
      clearTimeout(t);
      t = setTimeout(() => {
        state.q = search.value.trim();
        state.page = 1;
        fetchPage();
      }, 300);
    });

    $("[data-admin-only]") && $("[data-admin-only]").addEventListener("change", (e) => {
      state.adminOnly = e.target.checked;
      state.page = 1;
      fetchPage();
    });

    $("[data-pager='prev']") && $("[data-pager='prev']").addEventListener("click", () => {
      if (state.page > 1) { state.page--; fetchPage(); }
    });
    $("[data-pager='next']") && $("[data-pager='next']").addEventListener("click", () => {
      state.page++; fetchPage();
    });

    // 表格事件代理
    tbody.addEventListener("click", (e) => {
      const t = e.target.closest("[data-action='reset-password']");
      if (t) openResetPassword(t.dataset.userId, t.dataset.nickname);
    });

    $$("[data-action='open-create-user']").forEach((b) =>
      b.addEventListener("click", openCreateUser)
    );
  });
})();
