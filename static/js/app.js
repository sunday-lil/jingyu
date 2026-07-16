/* ============================================================
   静屿 — 全局工具
   暴露 window.QI 命名空间。
   ============================================================ */

(function () {
  "use strict";

  const QI = {
    // ── Toast 提示 ──
    toast(message, type = "info", duration = 2400) {
      let container = document.querySelector(".toast-container");
      if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
      }

      const el = document.createElement("div");
      el.className = `toast toast--${type}`;
      el.textContent = message;
      container.appendChild(el);

      setTimeout(() => {
        el.classList.add("is-leaving");
        setTimeout(() => el.remove(), 320);
      }, duration);
    },

    // ── fetch JSON 封装（自动处理 JSON 和错误） ──
    async fetchJSON(url, options = {}) {
      const opts = {
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        ...options,
      };
      if (opts.body && typeof opts.body !== "string") {
        opts.body = JSON.stringify(opts.body);
      }
      const resp = await fetch(url, opts);
      const isJSON = (resp.headers.get("content-type") || "").includes("application/json");
      if (!resp.ok) {
        if (isJSON) {
          const err = await resp.json();
          throw new Error(err.error || err.detail || `请求失败 (${resp.status})`);
        }
        throw new Error(`请求失败 (${resp.status})`);
      }
      if (resp.status === 204) return null;
      return isJSON ? await resp.json() : await resp.text();
    },

    // ── 确认弹窗（温柔风格） ──
    confirmThen(message, onConfirm) {
      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.innerHTML = `
        <div class="modal" role="dialog" aria-modal="true">
          <p style="font-size:17px;line-height:1.7;margin-bottom:24px;">${this._escape(message)}</p>
          <div style="display:flex;justify-content:flex-end;gap:8px;">
            <button class="btn btn--ghost" data-action="cancel">再想想</button>
            <button class="btn btn--primary" data-action="ok">好</button>
          </div>
        </div>`;
      document.body.appendChild(overlay);
      const close = () => overlay.remove();
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) close();
        const action = e.target.dataset.action;
        if (action === "cancel") close();
        if (action === "ok") {
          close();
          onConfirm && onConfirm();
        }
      });
    },

    // ── 能量飞升动效 ──
    floatEnergy(text, fromEl) {
      if (!fromEl) return;
      const rect = fromEl.getBoundingClientRect();
      const el = document.createElement("div");
      el.className = "energy-float";
      el.textContent = text;
      el.style.left = `${rect.left + rect.width / 2 - 10}px`;
      el.style.top = `${rect.top + window.scrollY}px`;
      document.body.appendChild(el);
      setTimeout(() => el.remove(), 1600);
    },

    // ── 是否偏好减少动效（无障碍）──
    prefersReducedMotion() {
      return window.matchMedia &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    },

    // ── 滚动渐显：给 .reveal 元素在进入视口时加 .is-visible ──
    initReveal() {
      const els = document.querySelectorAll(".reveal");
      if (!els.length) return;
      if (this.prefersReducedMotion() || !("IntersectionObserver" in window)) {
        els.forEach((el) => el.classList.add("is-visible"));
        return;
      }
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((en) => {
            if (en.isIntersecting) {
              en.target.classList.add("is-visible");
              io.unobserve(en.target);
            }
          });
        },
        { rootMargin: "0px 0px -8% 0px", threshold: 0.08 }
      );
      els.forEach((el) => io.observe(el));
    },

    // ── 按钮涟漪：事件委托 .btn 的点击，插入 .ripple-ink（支持动态插入的按钮）──
    initRipple() {
      if (this._rippleBound) return;
      this._rippleBound = true;
      document.addEventListener("click", (e) => {
        const btn = e.target.closest && e.target.closest(".btn");
        if (!btn) return;
        if (this.prefersReducedMotion()) return;
        if (btn.disabled) return;
        const rect = btn.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const ink = document.createElement("span");
        ink.className = "ripple-ink";
        ink.style.width = ink.style.height = `${size}px`;
        ink.style.left = `${e.clientX - rect.left}px`;
        ink.style.top = `${e.clientY - rect.top}px`;
        btn.appendChild(ink);
        setTimeout(() => ink.remove(), 620);
      });
    },

    // ── 密码可见性切换：事件委托 .password-toggle 的点击（支持动态生成的 modal）──
    initPasswordToggle() {
      if (this._pwdToggleBound) return;
      this._pwdToggleBound = true;
      document.addEventListener("click", (e) => {
        const btn = e.target.closest && e.target.closest(".password-toggle");
        if (!btn) return;
        const wrap = btn.parentElement;
        if (!wrap || !wrap.classList.contains("password-input-wrap")) return;
        const input = wrap.querySelector("input");
        if (!input) return;
        if (input.type === "password") {
          input.type = "text";
          btn.textContent = "🙈";
          btn.setAttribute("aria-label", "隐藏密码");
        } else {
          input.type = "password";
          btn.textContent = "👁";
          btn.setAttribute("aria-label", "显示密码");
        }
      });
    },

    // ── 数字计数：[data-countup] 元素在进入视口时从 0 缓动到目标值 ──
    initCountUp() {
      const els = document.querySelectorAll("[data-countup]");
      if (!els.length) return;
      const run = (el) => {
        const target = parseFloat(el.dataset.countup);
        if (isNaN(target)) return;
        this.countUp(el, target);
      };
      if (this.prefersReducedMotion() || !("IntersectionObserver" in window)) {
        els.forEach((el) => { el.textContent = el.dataset.countup; });
        return;
      }
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((en) => {
            if (en.isIntersecting) {
              run(en.target);
              io.unobserve(en.target);
            }
          });
        },
        { threshold: 0.4 }
      );
      els.forEach((el) => io.observe(el));
    },

    // ── 数字缓动到目标（立即执行）──
    countUp(el, target, opts = {}) {
      if (!el) return;
      const duration = opts.duration || 1200;
      const decimals = opts.decimals || 0;
      const start = performance.now();
      const from = 0;
      const ease = (t) => 1 - Math.pow(1 - t, 3); // easeOutCubic
      const tick = (now) => {
        const p = Math.min(1, (now - start) / duration);
        const v = from + (target - from) * ease(p);
        el.textContent = v.toFixed(decimals);
        if (p < 1) requestAnimationFrame(tick);
        else el.textContent = target.toFixed(decimals);
      };
      requestAnimationFrame(tick);
    },

    // ── 环境花瓣：在 .petal-layer 内周期性生成 .petal ──
    initPetals() {
      const layer = document.querySelector(".petal-layer");
      if (!layer) return;
      if (this.prefersReducedMotion()) return;
      // 仅在含 .hero 的页面（首页）生成，避免打扰写作 / 打卡等专注页
      if (!document.querySelector(".hero")) return;
      const glyphs = ["🌸", "🍂", "🌿", "🌼"];
      const MAX = 8;
      let alive = 0;
      const spawn = () => {
        if (alive >= MAX) return;
        const p = document.createElement("span");
        p.className = "petal";
        p.textContent = glyphs[Math.floor(Math.random() * glyphs.length)];
        const dur = 9000 + Math.random() * 6000;
        const drift = (Math.random() * 160 - 80).toFixed(0) + "px";
        p.style.left = `${Math.random() * 100}%`;
        p.style.animationDuration = `${dur}ms`;
        p.style.setProperty("--drift", drift);
        p.style.fontSize = `${14 + Math.random() * 10}px`;
        layer.appendChild(p);
        alive++;
        setTimeout(() => { p.remove(); alive--; }, dur);
      };
      // 初始散落几片
      for (let i = 0; i < 3; i++) setTimeout(spawn, i * 800);
      setInterval(spawn, 2400);
    },

    // ── 花瓣撒落（成功反馈，可由页面 JS 调用）──
    confetti(fromEl, opts = {}) {
      if (!fromEl || this.prefersReducedMotion()) return;
      const rect = fromEl.getBoundingClientRect();
      const cx0 = rect.left + rect.width / 2;
      const cy0 = rect.top + rect.height / 2;
      const glyphs = opts.glyphs || ["🌸", "🌿", "🌼", "✨"];
      const count = opts.count || 12;
      for (let i = 0; i < count; i++) {
        const p = document.createElement("span");
        p.className = "confetti-petal";
        p.textContent = glyphs[i % glyphs.length];
        const angle = (Math.PI * 2 * i) / count + Math.random() * 0.4;
        const dist = 60 + Math.random() * 70;
        p.style.left = `${cx0}px`;
        p.style.top = `${cy0}px`;
        p.style.setProperty("--cx", `${(Math.cos(angle) * dist).toFixed(0)}px`);
        p.style.setProperty("--cy", `${(Math.sin(angle) * dist - 40).toFixed(0)}px`);
        p.style.setProperty("--cr", `${(Math.random() * 720 - 360).toFixed(0)}deg`);
        document.body.appendChild(p);
        setTimeout(() => p.remove(), 1300);
      }
    },

    // ── 页面进入过渡：<main> 加 .is-ready ──
    initPageTransition() {
      const main = document.querySelector(".page-transition");
      if (!main) return;
      requestAnimationFrame(() => {
        requestAnimationFrame(() => main.classList.add("is-ready"));
      });
    },

    // ── 一次性自动初始化所有增强效果（DOMContentLoaded 时调用）──
    initAll() {
      this.initPageTransition();
      this.initReveal();
      this.initRipple();
      this.initPasswordToggle();
      this.initCountUp();
      this.initPetals();
    },

    // ── HTML escape ──
    _escape(s) {
      return String(s).replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
      }[c]));
    },

    // ── 格式化日期 ──
    formatDate(d) {
      const dt = d instanceof Date ? d : new Date(d);
      const y = dt.getFullYear();
      const m = String(dt.getMonth() + 1).padStart(2, "0");
      const day = String(dt.getDate()).padStart(2, "0");
      return `${y}年${m}月${day}日`;
    },

    formatTime(d) {
      const dt = d instanceof Date ? d : new Date(d);
      const h = String(dt.getHours()).padStart(2, "0");
      const m = String(dt.getMinutes()).padStart(2, "0");
      return `${h}:${m}`;
    },

    // ── 时间格式化为「x 分钟前」 ──
    timeAgo(d) {
      const dt = d instanceof Date ? d : new Date(d);
      const seconds = Math.floor((Date.now() - dt.getTime()) / 1000);
      if (seconds < 60) return "刚刚";
      const minutes = Math.floor(seconds / 60);
      if (minutes < 60) return `${minutes} 分钟前`;
      const hours = Math.floor(minutes / 60);
      if (hours < 24) return `${hours} 小时前`;
      const days = Math.floor(hours / 24);
      if (days < 30) return `${days} 天前`;
      return this.formatDate(dt);
    },

    // ── 日记加解密（Web Crypto API） ──
    async deriveKey(password, saltB64) {
      const enc = new TextEncoder();
      const salt = Uint8Array.from(atob(saltB64), (c) => c.charCodeAt(0));
      const keyMaterial = await crypto.subtle.importKey(
        "raw", enc.encode(password), { name: "PBKDF2" }, false, ["deriveKey"]
      );
      return crypto.subtle.deriveKey(
        { name: "PBKDF2", salt, iterations: 200000, hash: "SHA-256" },
        keyMaterial,
        { name: "AES-GCM", length: 256 },
        false,
        ["encrypt", "decrypt"]
      );
    },

    async encryptDiary(content, password, saltB64) {
      const key = await this.deriveKey(password, saltB64);
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const ct = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv },
        key,
        new TextEncoder().encode(content)
      );
      // 拼接 iv + ciphertext，base64 编码
      const merged = new Uint8Array(iv.length + ct.byteLength);
      merged.set(iv, 0);
      merged.set(new Uint8Array(ct), iv.length);
      return btoa(String.fromCharCode(...merged));
    },

    async decryptDiary(tokenB64, password, saltB64) {
      try {
        const key = await this.deriveKey(password, saltB64);
        const data = Uint8Array.from(atob(tokenB64), (c) => c.charCodeAt(0));
        const iv = data.slice(0, 12);
        const ct = data.slice(12);
        const pt = await crypto.subtle.decrypt(
          { name: "AES-GCM", iv },
          key,
          ct
        );
        return new TextDecoder().decode(pt);
      } catch (e) {
        return null;
      }
    },
  };

  window.QI = QI;

  // ── 自动初始化全局增强效果（页面进入过渡 / 滚动渐显 / 按钮涟漪 / 数字计数 / 环境花瓣）──
  // app.js 在 base.html 末尾以非 defer 方式加载，此时 DOM 已解析完成；
  // 但仍兼容 readyState=loading 的极端情况。
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => QI.initAll());
  } else {
    QI.initAll();
  }
})();
