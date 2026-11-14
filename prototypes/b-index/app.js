(() => {
  const buttons = Array.from(document.querySelectorAll("[data-filter]"));
  const cards = Array.from(document.querySelectorAll(".card"));
  const count = document.querySelector("[data-count]");
  if (!buttons.length || !cards.length) return;

  function apply(category) {
    let visible = 0;

    cards.forEach((card) => {
      const show = category === "all" || card.dataset.cat === category;
      card.hidden = !show;
      if (show) visible += 1;
    });

    buttons.forEach((button) => {
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.filter === category)
      );
    });

    if (count) count.textContent = `${visible} 篇`;
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => apply(button.dataset.filter));
  });
})();
