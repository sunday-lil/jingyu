/* ============================================================
   静屿 — 用户详情
   - 重置密码 / 切换管理员 / 删除 / 调整能量
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

  function applyLocalTimes() {
    $$("[data-iso]").forEach((el) => {
      const iso = el.dataset.iso;
      if (iso) el.textContent = formatTime(iso);
    });
  }

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
          <div class="form-field"><label class="form-label">新密码</label>
            <input type="password" name="new_password" minlength="6" required class="form-input"></div>
          <div class="form-field"><label class="form-label">再次输入</label>
            <input type="password" name="confirm" minlength="6" required class="form-input"></div>
          <div class="form-error" data-err style="min-height:18px;margin-bottom:8px;color:var(--color-danger);font-size:13px;"></div>
          <div style="display:flex;justify-content:flex-end;gap:8px;">
            <button type="button" class="btn btn--ghost" data-cancel>取消</button>
            <button type="submit" class="btn btn--primary">确认</button>
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
          method: "POST", body: { new_password: p1 },
        });
        QI.toast(`已重置 ${nickname} 的密码`, "success");
        close();
        if (r.warning) setTimeout(() => QI.toast(r.warning, "info", 4800), 200);
      } catch (err) { errEl.textContent = err.message; }
    });
  }

  async function toggleAdmin(userId, nickname, current) {
    const verb = current === "1" ? "降为普通用户" : "升为管理员";
    QI.confirmThen(`确认将「${nickname}」${verb}？`, async () => {
      try {
        await QI.fetchJSON(`/api/admin/users/${userId}/toggle-admin`, { method: "POST" });
        QI.toast("已切换", "success");
        setTimeout(() => location.reload(), 600);
      } catch (e) { QI.toast(e.message, "error"); }
    });
  }

  async function deleteUser(userId, nickname) {
    QI.confirmThen(
      `⚠️ 确认删除「${nickname}」？\n该用户的所有日记、打卡、能量、花园记录会被一并删除，不可恢复。`,
      async () => {
        try {
          await QI.fetchJSON(`/api/admin/users/${userId}`, { method: "DELETE" });
          QI.toast("已删除", "success");
          setTimeout(() => location.href = "/admin/users", 600);
        } catch (e) { QI.toast(e.message, "error"); }
      }
    );
  }

  async function adjustEnergy(userId) {
    const form = $("[data-action='adjust-energy']");
    if (!form) return;
    const fd = new FormData(form);
    const op = fd.get("op");
    const amount = parseInt(fd.get("amount") || "0", 10);
    const note = (fd.get("note") || "").toString().trim();
    if (!amount || amount <= 0) { QI.toast("请输入正整数", "warn"); return; }
    const delta = op === "-" ? -amount : amount;
    try {
      const r = await QI.fetchJSON(`/api/admin/users/${userId}/adjust-energy`, {
        method: "POST",
        body: { delta, note },
      });
      QI.toast(`已调整 ${delta > 0 ? '+' : ''}${delta} → 当前 ${r.new_total_energy} 🍃`, "success");
      const el = $("[data-energy]");
      if (el) el.textContent = r.new_total_energy + " 🍃";
    } catch (e) { QI.toast(e.message, "error"); }
  }

  document.addEventListener("DOMContentLoaded", () => {
    applyLocalTimes();
    $$("[data-action='reset-password']").forEach((b) =>
      b.addEventListener("click", () => openResetPassword(b.dataset.userId, b.dataset.nickname)));
    $$("[data-action='toggle-admin']").forEach((b) =>
      b.addEventListener("click", () => toggleAdmin(b.dataset.userId, b.dataset.nickname, b.dataset.current)));
    $$("[data-action='delete-user']").forEach((b) =>
      b.addEventListener("click", () => deleteUser(b.dataset.userId, b.dataset.nickname)));
    const adjForm = $("[data-action='adjust-energy']");
    if (adjForm) {
      adjForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const userId = parseInt(location.pathname.split("/").pop(), 10);
        adjustEnergy(userId);
      });
    }
  });
})();
