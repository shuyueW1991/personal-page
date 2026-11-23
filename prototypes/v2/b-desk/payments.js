/* 书的 Stripe Payment Links。
 *
 * 在 Stripe Dashboard → Payment links 建好一次性付款链接后，把 URL 粘到下面。
 * 这里只放公开的 Payment Link，不放 sk_ / whsec_；付款、发票、退款、
 * Alipay/卡 的选择都由 Stripe 托管页完成。
 *
 * 链接为空时，页面上的购买按钮会隐藏，并显示“payment link coming soon”
 * 的占位文案——所以可以先上线页面，再补链接。
 */
window.BOOK_PAYMENT_LINKS = {
  // PDF / EPUB（一次性）
  pdf: "https://buy.stripe.com/8x2fZh0GL4G7a0k4dPbZe00",
  // PDF + code + updates（一次性）
  bundle: "https://buy.stripe.com/fZubJ1cptc8z8WgcKlbZe01",
};

(() => {
  const links = window.BOOK_PAYMENT_LINKS || {};

  document.querySelectorAll("[data-book-buy]").forEach((button) => {
    const key = button.getAttribute("data-book-buy");
    const url = String(links[key] || "").trim();
    const pending = document.querySelector(`[data-book-pending="${key}"]`);

    if (!url) {
      button.hidden = true;
      if (pending) pending.hidden = false;
      return;
    }

    button.href = url;
    button.target = "_blank";
    button.rel = "noopener";
    button.hidden = false;
    if (pending) pending.hidden = true;
  });
})();
