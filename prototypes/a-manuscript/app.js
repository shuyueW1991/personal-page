(() => {
  const buttons = Array.from(document.querySelectorAll("[data-filter]"));
  const entries = Array.from(document.querySelectorAll(".entry"));
  const groups = Array.from(document.querySelectorAll(".year-group"));
  const count = document.querySelector("[data-count]");
  if (!buttons.length || !entries.length) return;

  function apply(category) {
    let visible = 0;

    entries.forEach((entry) => {
      const show = category === "all" || entry.dataset.cat === category;
      entry.hidden = !show;
      if (show) visible += 1;
    });

    groups.forEach((group) => {
      const hasVisible = Array.from(group.querySelectorAll(".entry")).some(
        (entry) => !entry.hidden
      );
      group.hidden = !hasVisible;
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
