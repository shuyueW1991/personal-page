/* 评论 · 点开才加载 utterances
 *
 * 默认不连接任何第三方：页面加载时只显示一个按钮。
 * 点开后把 utterances 的 client.js 注入 [data-comments]，由它生成 iframe；
 * 之后每个页面按 pathname 对应一个 GitHub Issue。
 *
 * 仓库里第一次启用：给 shuyueW1991/personal-page 安装 utterances App
 * （https://github.com/apps/utterances），并确认 Issues 已开启。
 */
(() => {
  const CONFIG = {
    repo: "shuyueW1991/personal-page",
    "issue-term": "pathname",
    label: "comment",
    theme: "github-light",
    crossorigin: "anonymous",
  };

  const showError = (mount, isEnglish) => {
    const note = document.createElement("p");
    note.className = "comments-error";
    note.textContent = isEnglish
      ? "Comments could not be loaded. Please write in GitHub Issues instead."
      : "评论暂时没能加载，请直接到 GitHub Issues 留言。";
    mount.appendChild(note);
  };

  document.querySelectorAll("[data-comments]").forEach((mount) => {
    const button = mount.querySelector("[data-comments-load]");
    if (!button) return;

    const isEnglish = Boolean(mount.closest('[lang="en"]'));
    let started = false;

    button.addEventListener("click", () => {
      if (started) return;
      started = true;
      button.disabled = true;
      button.textContent = isEnglish ? "Loading…" : "加载中…";

      const script = document.createElement("script");
      script.src = "https://utteranc.es/client.js";
      script.async = true;
      script.crossOrigin = "anonymous";
      Object.keys(CONFIG).forEach((key) => {
        script.setAttribute(key, CONFIG[key]);
      });

      script.addEventListener("error", () => {
        button.hidden = true;
        showError(mount, isEnglish);
      });

      mount.appendChild(script);

      // utterances 连不上仓库时，iframe 会一直停在 0 高度：等一会儿再收掉。
      const startedAt = Date.now();
      const timer = window.setInterval(() => {
        const frame = mount.querySelector("iframe");
        if (frame && frame.getBoundingClientRect().height > 24) {
          button.hidden = true;
          window.clearInterval(timer);
        } else if (Date.now() - startedAt > 8000) {
          window.clearInterval(timer);
          button.hidden = true;
          if (frame) frame.remove();
          showError(mount, isEnglish);
        }
      }, 400);
    });
  });
})();
