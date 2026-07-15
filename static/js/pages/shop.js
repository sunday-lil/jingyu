/* ============================================================
   静屿 — 商店兑换
   ============================================================ */

(function () {
  "use strict";

  document.querySelectorAll("[data-exchange]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const itemId = parseInt(btn.dataset.exchange, 10);
      const card = btn.closest(".shop-item");
      const name = card?.querySelector(".shop-item__name")?.textContent || "这件";

      QI.confirmThen(`确定要兑换「${name}」吗？`, async () => {
        btn.disabled = true;
        btn.textContent = "兑换中…";
        try {
          const resp = await QI.fetchJSON("/api/energy/exchange", {
            method: "POST",
            body: { item_id: itemId },
          });
          QI.toast(`已领到「${name}」`, "success");
          card.classList.add("is-bought");
          // 替换为「已收入」
          const newBtn = document.createElement("button");
          newBtn.className = "btn btn--soft btn--sm";
          newBtn.disabled = true;
          newBtn.textContent = "已收好";
          btn.replaceWith(newBtn);

          // 更新能量显示
          document.querySelectorAll("[data-energy-display]").forEach((el) => {
            el.textContent = resp.new_total_energy;
          });
        } catch (e) {
          QI.toast(e.message, "error");
          btn.disabled = false;
          btn.textContent = "兑 换";
        }
      });
    });
  });
})();
