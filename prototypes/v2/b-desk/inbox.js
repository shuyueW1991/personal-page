/* 待看评论 · GitHub Issues 里的 margin 批注
 *
 * 每条批注是一个 issue，标题 [margin] <page>#<anchor>。
 * 勾掉 = 在本机记下这个 issue 的 updated_at；之后同一 issue
 * 有新的回复（updated_at 变了）会重新出现。
 */
(() => {
  "use strict";

  if (!document.body.classList.contains("inbox-page")) return;

  const CONFIG = {
    repo: "shuyueW1991/personal-page",
    api: "https://api.github.com/repos/shuyueW1991/personal-page/issues",
    prefix: "[margin]",
    cacheKey: "margin-inbox-cache:v1",
    dismissedKey: "margin-inbox-dismissed:v1",
    cacheTtl: 5 * 60 * 1000,
  };

  // post-titles.js 由 build.py 按 vitrine/instrumentality/ 的清单生成；
  // 没加载到时退回 slug，至少链接还能点。
  const PAGE_TITLES = window.POST_TITLES || {};

  const list = document.querySelector("[data-inbox-list]");
  const count = document.querySelector("[data-inbox-count]");
  const empty = document.querySelector("[data-inbox-empty]");
  const errorBox = document.querySelector("[data-inbox-error]");
  const refresh = document.querySelector("[data-inbox-refresh]");
  const toast = document.querySelector("[data-inbox-toast]");
  const toastText = document.querySelector("[data-inbox-toast-text]");
  const undoButton = document.querySelector("[data-inbox-undo]");

  if (!list) return;

  const state = {
    issues: [],
    dismissed: readDismissed(),
    lastDismiss: null,
    loading: false,
    toastTimer: 0,
    error: false,
  };

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function shorten(value, length) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return text.length > length ? `${text.slice(0, length - 1)}…` : text;
  }

  function formatDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, "0")}.${String(
      date.getDate()
    ).padStart(2, "0")}`;
  }

  function decodeMeta(value) {
    const binary = atob(value);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  }

  function readDismissed() {
    try {
      const parsed = JSON.parse(localStorage.getItem(CONFIG.dismissedKey) || "{}");
      return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
    } catch (error) {
      return {};
    }
  }

  function writeDismissed() {
    try {
      localStorage.setItem(CONFIG.dismissedKey, JSON.stringify(state.dismissed));
    } catch (error) {
      /* 本地存不了也不影响本次会话。 */
    }
  }

  function readCache() {
    try {
      const parsed = JSON.parse(sessionStorage.getItem(CONFIG.cacheKey) || "null");
      if (!parsed || !Array.isArray(parsed.issues)) return null;
      return parsed;
    } catch (error) {
      return null;
    }
  }

  function writeCache() {
    try {
      sessionStorage.setItem(
        CONFIG.cacheKey,
        JSON.stringify({ at: Date.now(), issues: state.issues })
      );
    } catch (error) {
      /* 忽略缓存错误。 */
    }
  }

  function parseIssue(issue) {
    if (!issue || issue.pull_request) return null;
    const title = String(issue.title || "");
    if (!title.startsWith(`${CONFIG.prefix} `)) return null;
    const rest = title.slice(CONFIG.prefix.length + 1);
    const split = rest.lastIndexOf("#");
    if (split < 1) return null;
    const page = rest.slice(0, split);
    const anchor = rest.slice(split + 1);
    if (!/^[A-Za-z0-9._-]+\.html$/.test(page)) return null;
    if (!/^[A-Za-z0-9-]+$/.test(anchor)) return null;

    let meta = {};
    const metaMatch = /<!--\s*margin-meta:\s*([A-Za-z0-9+/=]+)\s*-->/.exec(issue.body || "");
    if (metaMatch) {
      try {
        meta = decodeMeta(metaMatch[1]);
      } catch (error) {
        meta = {};
      }
    }

    const text = String(issue.body || "")
      .replace(/<!--[\s\S]*?-->/g, "")
      .trim();

    return {
      number: issue.number,
      page,
      anchor,
      quote: typeof meta.quote === "string" ? meta.quote : "",
      text,
      user: issue.user && issue.user.login ? issue.user.login : "someone",
      createdAt: issue.created_at,
      updatedAt: issue.updated_at,
      replies: Number(issue.comments) || 0,
      htmlUrl: issue.html_url,
    };
  }

  function isDismissed(issue) {
    return state.dismissed[String(issue.number)] === issue.updatedAt;
  }

  function pending() {
    return state.issues.filter((issue) => !isDismissed(issue));
  }

  function updateCount() {
    const total = pending().length;
    count.textContent = total === 1 ? "1 pending" : `${total} pending`;
    document.title = `${total} pending — 王舒悦`;
    empty.hidden = total !== 0 || state.loading || state.error;
  }

  function buildRow(issue) {
    const row = node("li", "inbox-row");
    row.dataset.number = String(issue.number);

    const checkLabel = node("label", "inbox-check");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = true;
    checkbox.setAttribute("aria-label", `Mark “${shorten(issue.quote || issue.text, 60)}” reviewed`);
    checkLabel.append(checkbox);

    const link = node("a", "inbox-link");
    link.href = `${issue.page}?margin=${encodeURIComponent(issue.anchor)}&issue=${issue.number}#m-${issue.anchor}`;

    const pageName = node(
      "span",
      "inbox-page-name",
      `${PAGE_TITLES[issue.page] || issue.page.replace(/\.html$/, "")} · margin`
    );
    link.append(pageName);

    if (issue.quote) {
      const quote = node("span", "inbox-quote", `“${shorten(issue.quote, 220)}”`);
      link.append(quote);
    }

    link.append(node("span", "inbox-comment", shorten(issue.text || "Open on GitHub to read this note.", 280)));

    const meta = node(
      "span",
      "inbox-meta",
      `@${issue.user} · ${formatDate(issue.createdAt)}${
        issue.replies ? ` · ${issue.replies} repl${issue.replies === 1 ? "y" : "ies"}` : ""
      }`
    );
    link.append(meta);

    const arrow = node("span", "inbox-arrow", "↗");
    arrow.setAttribute("aria-hidden", "true");

    checkbox.addEventListener("change", () => {
      if (!checkbox.checked) dismiss(issue, row);
    });

    row.append(checkLabel, link, arrow);
    return row;
  }

  function render() {
    const visible = pending();
    list.replaceChildren();
    visible.forEach((issue) => list.append(buildRow(issue)));
    updateCount();
  }

  function dismiss(issue, row) {
    const key = String(issue.number);
    const previous = state.dismissed[key];
    state.lastDismiss = { issue, previous };
    state.dismissed[key] = issue.updatedAt;
    writeDismissed();

    row.classList.add("is-gone");
    window.setTimeout(() => {
      row.remove();
      updateCount();
    }, 240);

    showToast(`Removed “${shorten(issue.quote || issue.text, 42)}”.`);
    updateCount();
  }

  function undoDismiss() {
    if (!state.lastDismiss) return;
    const { issue, previous } = state.lastDismiss;
    const key = String(issue.number);
    if (previous === undefined) delete state.dismissed[key];
    else state.dismissed[key] = previous;
    writeDismissed();
    state.lastDismiss = null;
    hideToast();
    render();
    const restored = list.querySelector(`[data-number="${issue.number}"] input`);
    if (restored) restored.focus({ preventScroll: true });
  }

  function showToast(message) {
    if (!toast || !toastText) return;
    toastText.textContent = message;
    toast.hidden = false;
    window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(hideToast, 6000);
  }

  function hideToast() {
    if (!toast) return;
    toast.hidden = true;
    window.clearTimeout(state.toastTimer);
  }

  if (undoButton) undoButton.addEventListener("click", undoDismiss);

  function showError(message) {
    state.error = true;
    if (errorBox) {
      errorBox.hidden = false;
      errorBox.replaceChildren(document.createTextNode(message + " "));
      const link = node("a", "", "Open GitHub Issues");
      link.href = `https://github.com/${CONFIG.repo}/issues`;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      errorBox.append(link);
    }
    if (empty) empty.hidden = true;
    updateCount();
  }

  function clearError() {
    state.error = false;
    if (errorBox) {
      errorBox.hidden = true;
      errorBox.replaceChildren();
    }
  }

  async function fetchIssues(force) {
    if (state.loading) return;
    const cache = readCache();
    if (!force && cache && Date.now() - cache.at < CONFIG.cacheTtl) {
      state.issues = cache.issues;
      clearError();
      render();
      return;
    }

    state.loading = true;
    clearError();
    refresh.disabled = true;
    refresh.textContent = "refreshing…";
    count.textContent = "loading…";
    if (empty) empty.hidden = true;

    try {
      const url = new URL(CONFIG.api);
      url.searchParams.set("state", "open");
      url.searchParams.set("per_page", "100");
      url.searchParams.set("sort", "updated");
      url.searchParams.set("direction", "desc");
      const response = await fetch(url, {
        headers: { Accept: "application/vnd.github+json" },
        cache: "no-store",
      });
      if (!response.ok) throw new Error(`GitHub returned ${response.status}`);
      const data = await response.json();
      state.issues = data
        .map(parseIssue)
        .filter(Boolean)
        .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
      writeCache();
      render();
    } catch (error) {
      if (cache) {
        state.issues = cache.issues;
        render();
        showError("Could not refresh; showing the last cached copy.");
      } else {
        state.issues = [];
        render();
        showError("Could not load GitHub Issues.");
      }
    } finally {
      state.loading = false;
      refresh.disabled = false;
      refresh.textContent = "refresh";
      updateCount();
    }
  }

  refresh.addEventListener("click", () => fetchIssues(true));

  const cached = readCache();
  if (cached && Date.now() - cached.at < CONFIG.cacheTtl) {
    state.issues = cached.issues;
    render();
  } else {
    fetchIssues(false);
  }
})();
