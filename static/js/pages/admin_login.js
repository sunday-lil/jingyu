/* ============================================================
   静屿 — 后台登录
   直接复用 /api/auth/login，成功后跳到 /admin
   ============================================================ */

(function () {
  "use strict";

  const form = document.querySelector("[data-action='admin-login']");
  if (!form) return;

  const errEl = form.querySelector("[data-error]");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errEl.textContent = "";
    const fd = new FormData(form);
    const nickname = (fd.get("nickname") || "").toString().trim();
    const password = (fd.get("password") || "").toString();
    if (!nickname || !password) return;

    const btn = form.querySelector("button[type=submit]");
    btn.disabled = true;
    btn.textContent = "验证中…";
    try {
      const data = await QI.fetchJSON("/api/auth/login", {
        method: "POST",
        body: { nickname, password },
      });
      if (!data.is_admin) {
        errEl.textContent = "此账号没有后台权限";
        btn.disabled = false;
        btn.textContent = "入 内 院";
        return;
      }
      QI.toast("欢迎回来，" + data.nickname, "success");
      setTimeout(() => location.href = "/admin/", 320);
    } catch (err) {
      errEl.textContent = err.message || "登录失败";
      btn.disabled = false;
      btn.textContent = "入 内 院";
    }
  });

  // 退出登录表单（侧栏）
  const logoutForm = document.getElementById("admin-logout-form");
  if (logoutForm) {
    logoutForm.addEventListener("submit", (e) => {
      e.preventDefault();
      QI.fetchJSON("/api/auth/logout", { method: "POST" })
        .then(() => location.href = "/admin/login")
        .catch(() => location.href = "/admin/login");
    });
  }
})();
