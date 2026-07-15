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
})();
