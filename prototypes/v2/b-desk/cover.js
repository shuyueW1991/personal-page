/* 封面页交互：上海时间、跟随暖光、复制邮箱 */

(() => {
  const clock = document.querySelector("[data-clock]");

  if (clock) {
    const formatter = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Asia/Shanghai",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23",
    });

    const tick = () => {
      const now = new Date();
      clock.textContent = formatter.format(now);
      clock.dateTime = now.toISOString();
    };

    tick();
    window.setInterval(tick, 1000);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) tick();
    });
  }

  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  if (finePointer.matches && !reduceMotion.matches) {
    const root = document.documentElement;
    window.addEventListener(
      "pointermove",
      (event) => {
        root.style.setProperty("--mx", `${event.clientX}px`);
        root.style.setProperty("--my", `${event.clientY}px`);
      },
      { passive: true }
    );
  }

  const status = document.querySelector("[data-copy-status]");
  const buttons = document.querySelectorAll("[data-copy]");

  const fallbackCopy = (text) => {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.top = "-9999px";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    area.setSelectionRange(0, area.value.length);

    let copied = false;
    try {
      copied = document.execCommand("copy");
    } catch {
      copied = false;
    }
    area.remove();
    return copied;
  };

  const copyText = async (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch {
        // 继续走 execCommand 的兜底
      }
    }
    return fallbackCopy(text);
  };

  buttons.forEach((button) => {
    let timer = 0;
    const original = button.textContent.trim();
    button.dataset.original = original;

    button.addEventListener("click", async () => {
      const text = button.dataset.copy || "";
      const copied = await copyText(text);
      const value = button.parentElement.querySelector(".ch-value");

      window.clearTimeout(timer);
      button.classList.toggle("is-copied", copied);

      if (copied) {
        button.textContent = "copied";
        if (status) status.textContent = `已复制 ${text}`;
      } else {
        button.textContent = "select";
        if (value) {
          const range = document.createRange();
          range.selectNodeContents(value);
          const selection = window.getSelection();
          selection.removeAllRanges();
          selection.addRange(range);
        }
        if (status) status.textContent = `复制失败，已选中 ${text}`;
      }

      timer = window.setTimeout(() => {
        button.textContent = button.dataset.original;
        button.classList.remove("is-copied");
      }, 1800);
    });
  });
})();
