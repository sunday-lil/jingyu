/* ============================================================
   静屿 — 登录 / 注册
   ============================================================ */

(function () {
  "use strict";

  const form = document.querySelector("form.auth-form");
  if (!form) return;

  const submitBtn = form.querySelector("button[type=submit]");
  const errorEl = form.querySelector(".form-error");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.textContent = "";

    const data = new FormData(form);
    const payload = {
      nickname: data.get("nickname").trim(),
      password: data.get("password"),
    };

    if (payload.nickname.length < 2) {
      errorEl.textContent = "昵称至少 2 个字";
      return;
    }
    if (payload.password.length < 6) {
      errorEl.textContent = "密码至少 6 位";
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "稍等…";

    const action = form.dataset.action;
    const url = action === "register" ? "/api/auth/register" : "/api/auth/login";
    const nextUrl = new URLSearchParams(location.search).get("next") || "/";

    try {
      await QI.fetchJSON(url, { method: "POST", body: payload });
      QI.toast(action === "register" ? "欢迎你 ✨" : "回来了 ☀️", "success");
      setTimeout(() => location.href = nextUrl, 600);
    } catch (err) {
      errorEl.textContent = err.message;
      submitBtn.disabled = false;
      submitBtn.textContent = action === "register" ? "启 程" : "入 境";
    }
  });
})();
