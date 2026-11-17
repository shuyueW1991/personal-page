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

  document.querySelectorAll("[data-comments]").forEach((mount) => {
    const button = mount.querySelector("[data-comments-load]");
    if (!button) return;

    const isEnglish = Boolean(mount.closest('[lang="en"]'));
    let started = false;

    const showError = () => {
      button.hidden = true;
      if (mount.querySelector(".comments-error")) return;
      const note = document.createElement("p");
      note.className = "comments-error";
      note.textContent = isEnglish
        ? "Comments could not be loaded. Please write in GitHub Issues instead."
        : "评论暂时没能加载，请直接到 GitHub Issues 留言。";
      mount.appendChild(note);
    };

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
      script.addEventListener("error", showError);
      mount.appendChild(script);

      // 连不上时 iframe 会一直停在 0 高度。等到 12 秒还没有内容才提示；
      // 不删 iframe —— 网络慢的话，它稍后仍然可以出现。
      const startedAt = Date.now();
      const timer = window.setInterval(() => {
        const frame = mount.querySelector("iframe");
        if (frame && frame.getBoundingClientRect().height > 24) {
          window.clearInterval(timer);
          button.hidden = true;
          const note = mount.querySelector(".comments-error");
          if (note) note.remove();
        } else if (Date.now() - startedAt > 12000) {
          window.clearInterval(timer);
          showError();
        }
      }, 400);
    });
  });
})();
