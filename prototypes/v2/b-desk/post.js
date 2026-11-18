/* 注记页 · 阅读桌
 *
 * 正文占 2/3，右侧是一张随滚动固定的阅读桌：
 * 上半是图版/草图，下半是页边批注。
 * 正文右侧的 34px 刻度栏把段落和批注对应起来；
 * 选中文字、点刻度，或从 inbox 进来，都会在阅读桌里打开对应批注。
 *
 * 批注存进 GitHub Issues，标题 [margin] <page>#<anchor>，
 * 正文开头带一段 base64 元数据（页码、锚点、引文）。
 */
(() => {
  "use strict";

  if (!document.body.classList.contains("post-page")) return;

  const CONFIG = {
    repo: "shuyueW1991/personal-page",
    api: "https://api.github.com/repos/shuyueW1991/personal-page/issues",
    prefix: "[margin]",
    cacheTtl: 5 * 60 * 1000,
    page: decodeURIComponent(location.pathname.split("/").pop() || "index.html"),
  };

  const body = document.querySelector(".article-main .body");
  const article = document.querySelector(".article-main");
  const gutter = document.querySelector("[data-annotation-gutter]");
  const desk = document.querySelector(".reader-desk");
  const plate = document.querySelector(".desk-plate");
  const deskMargin = document.querySelector(".desk-margin");
  const notesBody = document.querySelector("[data-desk-notes]");
  const deskCount = document.querySelector("[data-margin-count]");
  const deskLoad = document.querySelector("[data-margin-load]");
  const deskOpenButtons = Array.from(document.querySelectorAll("[data-desk-open]"));
  const deskCloseButton = document.querySelector("[data-desk-close]");

  if (!body || !article || !gutter || !desk || !notesBody) return;

  const state = {
    blocks: [],
    byAnchor: new Map(),
    ticks: new Map(),
    issues: [],
    loaded: false,
    loading: false,
    failed: false,
    fetchPromise: null,
    selectedAnchor: null,
    targetAnchor: null,
    targetIssue: null,
    composer: null,
    mobile: matchMedia("(max-width: 900px)").matches,
    board: null,
  };

  const mobileQuery = matchMedia("(max-width: 900px)");

  /* ---------- 小工具 ---------- */

  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

  function node(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function debounce(fn, wait) {
    let timer = 0;
    return (...args) => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => fn(...args), wait);
    };
  }

  function shorten(value, length) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return text.length > length ? `${text.slice(0, length - 1)}…` : text;
  }

  function hashText(value) {
    let hash = 0x811c9dc5;
    const text = String(value || "");
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 0x01000193);
    }
    return (hash >>> 0).toString(36);
  }

  function formatDate(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, "0")}.${String(
      date.getDate()
    ).padStart(2, "0")}`;
  }

  function encodeMeta(value) {
    const bytes = new TextEncoder().encode(JSON.stringify(value));
    let binary = "";
    for (const byte of bytes) binary += String.fromCharCode(byte);
    return btoa(binary);
  }

  function decodeMeta(value) {
    const binary = atob(value);
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    return JSON.parse(new TextDecoder().decode(bytes));
  }

  function linkify(text) {
    const fragment = document.createDocumentFragment();
    const pattern = /(https?:\/\/[^\s<]+[^\s<.,;:!?)\]}'"])/g;
    let cursor = 0;
    let match;
    while ((match = pattern.exec(text)) !== null) {
      if (match.index > cursor) fragment.append(document.createTextNode(text.slice(cursor, match.index)));
      const anchor = node("a", "", match[0]);
      anchor.href = match[0];
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      fragment.append(anchor);
      cursor = match.index + match[0].length;
    }
    if (cursor < text.length) fragment.append(document.createTextNode(text.slice(cursor)));
    return fragment;
  }

  function cleanText(element) {
    const clone = element.cloneNode(true);
    clone.querySelectorAll(".katex-mathml, .sr-only, script, style").forEach((item) => item.remove());
    return (clone.textContent || "").replace(/\s+/g, " ").trim();
  }

  function blockText(element) {
    if (element.matches("figure")) {
      const image = element.querySelector("img");
      const caption = element.querySelector("figcaption");
      return `${image ? image.alt : ""} ${caption ? cleanText(caption) : ""}`;
    }
    return cleanText(element);
  }

  /* ---------- 正文块 + 刻度 ---------- */

  function collectBlocks() {
    const used = new Set();
    let order = 0;

    Array.from(body.children).forEach((element) => {
      if (!(element instanceof HTMLElement)) return;
      if (!element.matches("p,h2,h3,figure,blockquote,ul,ol,.table-wrap")) return;

      const text = blockText(element).replace(/\s+/g, " ").trim();
      if (!text) return;

      order += 1;
      const tag = element.matches(".table-wrap") ? "tbl" : element.tagName.toLowerCase();
      const base = `${tag}-${hashText(text.slice(0, 900))}`;
      let anchor = base;
      let suffix = 2;
      while (used.has(anchor)) {
        anchor = `${base}-${suffix}`;
        suffix += 1;
      }
      used.add(anchor);

      element.dataset.marginId = anchor;
      if (!element.id) element.id = `m-${anchor}`;

      const block = { node: element, anchor, text, order, top: 0 };
      state.blocks.push(block);
      state.byAnchor.set(anchor, block);

      const tick = node("button", "margin-tick");
      tick.type = "button";
      tick.dataset.anchor = anchor;
      tick.title = "Margin notes";
      const line = node("span", "margin-tick-line");
      const mark = node("span", "margin-tick-mark", "+");
      tick.append(line, mark);
      tick.addEventListener("click", () => onTickClick(block));
      tick.setAttribute("aria-label", `Add a margin note on “${shorten(text, 60)}”`);

      element.addEventListener("mouseenter", () => tick.classList.add("is-active"));
      element.addEventListener("mouseleave", () => tick.classList.remove("is-active"));

      state.ticks.set(anchor, tick);
      gutter.append(tick);
    });

  }

  function layoutTicks() {
    if (state.mobile || !gutter.offsetParent) return;
    const gutterTop = gutter.getBoundingClientRect().top;
    state.blocks.forEach((block) => {
      const tick = state.ticks.get(block.anchor);
      if (!tick) return;
      const top = block.node.getBoundingClientRect().top - gutterTop;
      tick.style.top = `${Math.max(0, top - 10)}px`;
    });
  }

  function updateTicks() {
    const counts = new Map();
    state.issues.forEach((issue) => {
      counts.set(issue.anchor, (counts.get(issue.anchor) || 0) + 1);
    });

    state.blocks.forEach((block) => {
      const tick = state.ticks.get(block.anchor);
      if (!tick) return;
      const count = counts.get(block.anchor) || 0;
      tick.classList.toggle("has-notes", count > 0);
      const mark = tick.querySelector(".margin-tick-mark");
      if (mark) mark.textContent = count > 0 ? String(count) : "+";
      tick.setAttribute(
        "aria-label",
        count > 0
          ? `${count} margin note${count === 1 ? "" : "s"} on “${shorten(block.text, 60)}”`
          : `Add a margin note on “${shorten(block.text, 60)}”`
      );
    });
  }

  /* ---------- GitHub Issues ---------- */

  function cacheKey() {
    return `margin-cache:${CONFIG.page}`;
  }

  function readCache() {
    try {
      const raw = sessionStorage.getItem(cacheKey());
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.issues)) return null;
      return parsed;
    } catch (error) {
      return null;
    }
  }

  function writeCache(issues) {
    try {
      sessionStorage.setItem(cacheKey(), JSON.stringify({ at: Date.now(), issues }));
    } catch (error) {
      /* 隐私模式下写不了缓存也不影响页面。 */
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
    if (page !== CONFIG.page || !anchor) return null;

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
      title,
      htmlUrl: issue.html_url,
      user: issue.user && issue.user.login ? issue.user.login : "someone",
      createdAt: issue.created_at,
      updatedAt: issue.updated_at,
      replies: Number(issue.comments) || 0,
      anchor,
      quote: typeof meta.quote === "string" ? meta.quote : "",
      text,
    };
  }

  function updateDeskHeader() {
    if (deskCount) {
      deskCount.textContent = state.loading && !state.loaded
        ? "loading"
        : state.failed && !state.loaded
          ? "offline"
          : state.loaded
            ? `${state.issues.length} note${state.issues.length === 1 ? "" : "s"}`
            : "—";
    }
    if (deskLoad) {
      deskLoad.disabled = state.loading;
      deskLoad.textContent = state.loading
        ? "loading…"
        : state.loaded
          ? "refresh"
          : state.failed
            ? "retry"
            : "load";
    }
  }

  async function loadComments(force = false) {
    if (state.fetchPromise) return state.fetchPromise;
    if (state.loaded && !force) return;

    const cache = readCache();
    if (!force && cache && Date.now() - cache.at < CONFIG.cacheTtl) {
      applyIssues(cache.issues);
      return;
    }
    if (cache) applyIssues(cache.issues);

    state.loading = true;
    state.failed = false;
    updateDeskHeader();
    renderDesk();

    state.fetchPromise = (async () => {
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
        const issues = data.map(parseIssue).filter(Boolean);
        writeCache(issues);
        state.failed = false;
        applyIssues(issues);
      } catch (error) {
        state.failed = true;
        state.loaded = Boolean(cache);
        if (cache) {
          applyIssues(cache.issues);
          state.failed = true;
        } else {
          state.issues = [];
          updateTicks();
          renderDesk();
        }
      } finally {
        state.loading = false;
        state.fetchPromise = null;
        updateDeskHeader();
        updateTicks();
        renderDesk();
        applyTarget();
      }
    })();

    return state.fetchPromise;
  }

  function applyIssues(issues) {
    state.issues = issues
      .filter((issue) => issue && issue.anchor && state.byAnchor.has(issue.anchor))
      .sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
    state.loaded = true;
    state.failed = false;
    updateTicks();
    updateDeskHeader();
    renderDesk();
    applyTarget();
  }

  function ensureCommentsLoaded() {
    if (state.loaded || state.loading) return state.fetchPromise || Promise.resolve();
    return loadComments(false);
  }

  /* ---------- 阅读桌：索引 / 线程 / 编辑器 ---------- */

  function clearHighlights() {
    document.querySelectorAll(".is-target, .is-target-comment").forEach((element) => {
      element.classList.remove("is-target", "is-target-comment");
    });
    state.ticks.forEach((tick) => tick.classList.remove("is-active"));
  }

  function emptyState(message, withLink = false) {
    const paragraph = node("p", "desk-empty");
    paragraph.append(document.createTextNode(message));
    if (withLink) {
      const link = node("a", "", "GitHub Issues");
      link.href = `https://github.com/${CONFIG.repo}/issues`;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      paragraph.append(document.createTextNode(" "), link);
    }
    notesBody.replaceChildren(paragraph);
    notesBody.scrollTop = 0;
  }

  function renderDesk() {
    if (state.composer) {
      if (state.composer.keepOpen && notesBody.querySelector(".desk-form")) return;
      renderComposer();
      state.composer.keepOpen = true;
      return;
    }
    if (state.selectedAnchor) {
      renderThread(state.selectedAnchor);
      return;
    }
    if (state.loading && !state.loaded) {
      emptyState("Loading margin notes…");
      return;
    }
    if (state.failed && !state.loaded) {
      emptyState("Margin notes could not be loaded.", true);
      return;
    }
    if (state.loaded && state.issues.length > 0) {
      renderIndex();
      return;
    }
    if (state.loaded) {
      emptyState("No margin notes yet. Select a passage, or click a tick in the margin.");
    } else {
      emptyState("Margin notes load from GitHub only when you ask. Select a passage, or click a tick in the margin, to write one.");
    }
  }

  function renderIndex() {
    const groups = new Map();
    state.issues.forEach((issue) => {
      if (!groups.has(issue.anchor)) groups.set(issue.anchor, []);
      groups.get(issue.anchor).push(issue);
    });

    const entries = Array.from(groups.entries())
      .map(([anchor, issues]) => ({ anchor, issues, block: state.byAnchor.get(anchor) }))
      .filter((entry) => entry.block)
      .sort((a, b) => a.block.order - b.block.order);

    if (!entries.length) {
      emptyState("No margin notes yet. Select a passage, or click a tick in the margin.");
      return;
    }

    const list = node("ul", "desk-index");
    entries.forEach((entry) => {
      const item = document.createElement("li");
      const button = node("button", "desk-index-row");
      button.type = "button";
      button.dataset.anchor = entry.anchor;
      const no = node("span", "desk-index-no", String(entry.block.order).padStart(2, "0"));
      const quote = node("span", "desk-index-quote");
      quote.textContent = `“${shorten(entry.issues[0].quote || entry.block.text, 120)}”`;
      const meta = node(
        "span",
        "desk-index-meta",
        `@${entry.issues[0].user} · ${entry.issues.length} note${entry.issues.length === 1 ? "" : "s"}`
      );
      button.append(no, quote, meta);
      button.addEventListener("click", () => selectAnchor(entry.anchor, { scroll: true }));
      item.append(button);
      list.append(item);
    });
    notesBody.replaceChildren(list);
    notesBody.scrollTop = 0;
  }

  function renderThread(anchor) {
    const block = state.byAnchor.get(anchor);
    if (!block) return;
    const issues = state.issues.filter((issue) => issue.anchor === anchor);

    const back = node("button", "desk-back", "← all notes");
    back.type = "button";
    back.addEventListener("click", () => {
      state.selectedAnchor = null;
      state.composer = null;
      state.targetIssue = null;
      clearHighlights();
      renderDesk();
    });

    const quote = node("blockquote", "desk-quote");
    quote.textContent = `“${shorten(issues[0] ? issues[0].quote || block.text : block.text, 220)}”`;

    const wrap = node("div");
    wrap.append(back, quote);

    if (!issues.length) {
      if (state.loading) {
        emptyState("Loading margin notes…");
        return;
      }
      const empty = node("p", "desk-empty", "No notes on this passage yet.");
      wrap.append(empty);
      if (!state.loading) {
        const add = node("button", "desk-reply", "add a note");
        add.type = "button";
        add.addEventListener("click", () => openComposer(anchor, block.text, false));
        wrap.append(add);
      }
      notesBody.replaceChildren(wrap);
      notesBody.scrollTop = 0;
      return;
    }

    const comments = node("div", "desk-comments");
    issues.forEach((issue) => {
      const item = node("div", "desk-comment");
      item.dataset.issue = String(issue.number);
      if (String(issue.number) === String(state.targetIssue)) item.classList.add("is-target-comment");

      if (issue.text) {
        const text = node("p", "desk-comment-text");
        text.append(linkify(issue.text));
        item.append(text);
      } else {
        item.append(node("p", "desk-comment-text", "This note lives on GitHub."));
      }

      const meta = node("p", "desk-comment-meta");
      meta.append(document.createTextNode(`@${issue.user} · ${formatDate(issue.createdAt)}`));
      if (issue.replies > 0) {
        meta.append(document.createTextNode(` · ${issue.replies} repl${issue.replies === 1 ? "y" : "ies"}`));
      }
      const link = node("a", "", " GitHub ↗");
      link.href = issue.htmlUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      meta.append(link);
      item.append(meta);
      comments.append(item);
    });
    wrap.append(comments);

    const add = node("button", "desk-reply", "add a note");
    add.type = "button";
    add.addEventListener("click", () => openComposer(anchor, issues[0].quote || block.text, true));
    wrap.append(add);

    notesBody.replaceChildren(wrap);
    notesBody.scrollTop = 0;
  }

  function renderComposer() {
    const { anchor, quote: quoteText } = state.composer;
    const block = state.byAnchor.get(anchor);
    if (!block) {
      state.composer = null;
      renderDesk();
      return;
    }

    const wrap = node("div");
    const back = node("button", "desk-back", "← cancel");
    back.type = "button";
    back.addEventListener("click", () => {
      state.composer = null;
      renderDesk();
    });
    wrap.append(back);

    const quote = node("blockquote", "desk-quote");
    quote.textContent = `“${shorten(quoteText || block.text, 220)}”`;
    wrap.append(quote);

    const form = document.createElement("form");
    form.className = "desk-form";

    const field = document.createElement("textarea");
    field.required = true;
    field.maxLength = 3000;
    field.rows = 5;
    field.placeholder = "Write a note for this passage…";
    field.setAttribute("aria-label", "Your margin note");
    form.append(field);

    form.append(
      node(
        "p",
        "desk-form-hint",
        "Posts to GitHub Issues. Your GitHub account is the byline; the note appears here after a refresh."
      )
    );

    const actions = node("div", "desk-form-actions");
    const submit = node("button", "desk-submit", "Post on GitHub ↗");
    submit.type = "submit";
    const cancel = node("button", "desk-cancel", "cancel");
    cancel.type = "button";
    cancel.addEventListener("click", () => {
      state.composer = null;
      renderDesk();
    });
    actions.append(submit, cancel);
    form.append(actions);

    const status = node("p", "desk-form-status");
    status.hidden = true;
    form.append(status);

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const text = field.value.trim();
      if (text.length < 2) {
        status.hidden = false;
        status.textContent = "Write a note first.";
        field.focus();
        return;
      }

      const title = `${CONFIG.prefix} ${CONFIG.page}#${anchor}`;
      const bodyText = `<!-- margin-meta: ${encodeMeta({
        page: CONFIG.page,
        anchor,
        quote: shorten(quoteText || block.text, 260),
      })} -->\n\n${text}`;
      const params = new URLSearchParams({ title, body: bodyText });
      const url = `https://github.com/${CONFIG.repo}/issues/new?${params.toString()}`;

      const opened = window.open(url, "_blank");
      if (opened) opened.opener = null;

      status.hidden = false;
      status.replaceChildren(
        document.createTextNode("Finish the issue on GitHub, then come back. "),
        (() => {
          const link = node("a", "", "Open the issue composer");
          link.href = url;
          link.target = "_blank";
          link.rel = "noopener noreferrer";
          return link;
        })()
      );

      let refreshed = false;
      const refresh = () => {
        if (refreshed) return;
        refreshed = true;
        window.setTimeout(() => {
          loadComments(true);
        }, 700);
      };
      window.addEventListener("focus", refresh, { once: true });
      window.setTimeout(refresh, 120000);
    });

    wrap.append(form);
    notesBody.replaceChildren(wrap);
    notesBody.scrollTop = 0;
    window.setTimeout(() => field.focus({ preventScroll: true }), 30);
  }

  function setSelected(anchor, keepTargetIssue = false) {
    const block = state.byAnchor.get(anchor);
    if (!block) return;
    clearHighlights();
    if (!keepTargetIssue) state.targetIssue = null;
    state.selectedAnchor = anchor;
    block.node.classList.add("is-target");
    const tick = state.ticks.get(anchor);
    if (tick) tick.classList.add("is-active");
  }

  function selectAnchor(anchor, options = {}) {
    const block = state.byAnchor.get(anchor);
    if (!block) return;
    setSelected(anchor, false);
    state.composer = null;
    renderDesk();
    if (options.scroll) {
      block.node.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    if (options.compose) {
      openComposer(anchor, options.quote || block.text, false);
    }
    ensureCommentsLoaded();
  }

  function openComposer(anchor, quoteText, fromExisting) {
    const block = state.byAnchor.get(anchor);
    if (!block) return;
    setSelected(anchor, false);
    state.composer = {
      anchor,
      quote: quoteText || block.text,
      fromExisting: Boolean(fromExisting),
      keepOpen: false,
    };
    renderDesk();
    if (state.mobile) openDesk("notes");
  }

  function onTickClick(block) {
    setSelected(block.anchor, false);
    state.composer = null;
    renderDesk();
    ensureCommentsLoaded().then(() => {
      const has = state.issues.some((issue) => issue.anchor === block.anchor);
      if (has) {
        state.selectedAnchor = block.anchor;
        renderDesk();
      } else {
        openComposer(block.anchor, block.text, false);
      }
    });
  }

  /* ---------- 选中文字 ---------- */

  function handleSelectionEnd() {
    window.setTimeout(() => {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || selection.rangeCount === 0) return;
      const range = selection.getRangeAt(0);
      let selected = range.startContainer;
      if (selected.nodeType === Node.TEXT_NODE) selected = selected.parentElement;
      if (!selected || !body.contains(selected)) return;
      if (selected.closest(".reader-desk, .comments")) return;

      const block = selected.closest("[data-margin-id]");
      if (!block || !body.contains(block)) return;

      const wrapper = document.createElement("div");
      wrapper.append(range.cloneContents());
      const text = cleanText(wrapper);
      if (text.length < 6) return;

      openComposer(block.dataset.marginId, text, false);
      ensureCommentsLoaded();
    }, 0);
  }

  document.addEventListener("mouseup", handleSelectionEnd);
  document.addEventListener("keyup", (event) => {
    if (event.shiftKey || event.key === "Shift") handleSelectionEnd();
  });

  /* ---------- 阅读桌开合 ---------- */

  function openDesk(section = "notes") {
    if (state.mobile) {
      document.body.classList.add("desk-open");
      deskOpenButtons.forEach((button) => button.setAttribute("aria-expanded", "true"));
      window.requestAnimationFrame(() => {
        const target = section === "plate" ? plate : deskMargin;
        if (!target) return;
        const deskTop = desk.getBoundingClientRect().top;
        const targetTop = target.getBoundingClientRect().top - deskTop + desk.scrollTop - 10;
        desk.scrollTo({ top: Math.max(0, targetTop), behavior: "smooth" });
        window.dispatchEvent(new CustomEvent("doodle:resize"));
      });
    } else if (section === "notes") {
      notesBody.scrollTop = 0;
    }
  }

  function closeDesk() {
    document.body.classList.remove("desk-open");
    deskOpenButtons.forEach((button) => button.setAttribute("aria-expanded", "false"));
  }

  deskOpenButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.deskOpen === "plate") {
        openDesk("plate");
        return;
      }
      if (!state.composer) {
        state.selectedAnchor = null;
        state.targetIssue = null;
        clearHighlights();
        renderDesk();
      }
      if (!state.loaded) loadComments(true);
      openDesk("notes");
    });
  });

  if (deskCloseButton) deskCloseButton.addEventListener("click", closeDesk);
  if (deskLoad) deskLoad.addEventListener("click", () => loadComments(true));

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.body.classList.contains("desk-open")) closeDesk();
  });

  /* ---------- 图版 ---------- */

  let lightbox = null;

  function closeLightbox() {
    if (!lightbox) return;
    lightbox.hidden = true;
    document.body.classList.remove("lightbox-open");
  }

  function openLightbox(src, alt) {
    if (!src) return;
    if (!lightbox) {
      lightbox = document.createElement("div");
      lightbox.className = "figure-lightbox";
      lightbox.hidden = true;
      lightbox.setAttribute("role", "dialog");
      lightbox.setAttribute("aria-modal", "true");
      lightbox.setAttribute("aria-label", "Figure preview");
      const image = document.createElement("img");
      image.alt = "";
      const close = node("button", "figure-lightbox-close", "×");
      close.type = "button";
      close.setAttribute("aria-label", "Close figure preview");
      close.addEventListener("click", closeLightbox);
      lightbox.addEventListener("click", (event) => {
        if (event.target === lightbox) closeLightbox();
      });
      lightbox.append(image, close);
      document.body.append(lightbox);
    }
    const image = lightbox.querySelector("img");
    image.src = src;
    image.alt = alt || "";
    lightbox.hidden = false;
    document.body.classList.add("lightbox-open");
    lightbox.querySelector(".figure-lightbox-close").focus({ preventScroll: true });
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && lightbox && !lightbox.hidden) closeLightbox();
  });

  function setupBoard() {
    const board = document.querySelector("[data-board]");
    const tabs = document.querySelector("[data-board-tabs]");
    const figurePanel = document.querySelector('[data-board-panel="figure"]');
    const doodlePanel = document.querySelector('[data-board-panel="doodle"]');
    if (!board || !tabs || !figurePanel || !doodlePanel) return;

    const figures = Array.from(body.querySelectorAll("figure.post-figure")).map((figure) => {
      const image = figure.querySelector("img");
      const caption = figure.querySelector("figcaption");
      return {
        src: image ? image.getAttribute("src") : "",
        alt: image ? image.getAttribute("alt") || "" : "",
        caption: caption ? cleanText(caption) : "",
      };
    });

    const doodleTab = tabs.querySelector('[data-board-tab="doodle"]');
    if (!doodleTab) return;

    const hint = board.querySelector(".desk-hint");
    if (hint) {
      hint.textContent = figures.length
        ? "Pin a figure, click it to enlarge, or sketch."
        : "Sketch a comparison while you read.";
    }

    const tabElements = new Map();
    figures.forEach((figure, index) => {
      const tab = node("button", "board-tab", `fig ${index + 1}`);
      tab.type = "button";
      tab.setAttribute("role", "tab");
      tab.setAttribute("aria-selected", "false");
      tab.setAttribute("aria-controls", "board-figure-panel");
      tab.dataset.boardTab = `figure-${index}`;
      tabs.insertBefore(tab, doodleTab);
      tabElements.set(`figure-${index}`, tab);
      tab.addEventListener("click", () => selectBoardTab(`figure-${index}`));
    });

    doodleTab.setAttribute("aria-selected", figures.length === 0 ? "true" : "false");
    doodleTab.setAttribute("aria-controls", "board-doodle-panel");
    doodleTab.dataset.boardTab = "doodle";
    tabElements.set("doodle", doodleTab);
    doodleTab.addEventListener("click", () => selectBoardTab("doodle"));

    function renderFigure(index) {
      const figure = figures[index];
      if (!figure) return;
      const wrapper = document.createElement("figure");
      wrapper.className = "desk-figure";
      const image = document.createElement("img");
      image.src = figure.src;
      image.alt = figure.alt;
      image.loading = "eager";
      image.decoding = "async";
      image.title = "Open full size";
      image.tabIndex = 0;
      image.setAttribute("role", "button");
      image.setAttribute("aria-label", `Open ${figure.alt || "figure"} full size`);
      image.addEventListener("click", () => openLightbox(figure.src, figure.alt));
      image.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openLightbox(figure.src, figure.alt);
        }
      });
      const caption = document.createElement("figcaption");
      caption.textContent = figure.caption;
      wrapper.append(image, caption);
      figurePanel.replaceChildren(wrapper);
    }

    function selectBoardTab(key) {
      tabElements.forEach((tab, name) => {
        tab.setAttribute("aria-selected", String(name === key));
      });
      const isFigure = key.startsWith("figure-");
      figurePanel.hidden = !isFigure;
      doodlePanel.hidden = isFigure;
      if (isFigure) {
        renderFigure(Number(key.slice("figure-".length)));
      } else {
        window.dispatchEvent(new CustomEvent("doodle:resize"));
      }
    }

    figures.forEach((figure, index) => {
      const element = body.querySelectorAll("figure.post-figure")[index];
      if (!element) return;
      const button = node("button", "pin-figure", "pin to desk");
      button.type = "button";
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        selectBoardTab(`figure-${index}`);
        openDesk("plate");
      });
      element.append(button);
    });

    tabs.addEventListener("keydown", (event) => {
      if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
      const list = Array.from(tabElements.values());
      const current = list.findIndex((tab) => tab.getAttribute("aria-selected") === "true");
      if (current < 0) return;
      event.preventDefault();
      const next = (current + (event.key === "ArrowRight" ? 1 : -1) + list.length) % list.length;
      list[next].focus();
      list[next].click();
    });

    state.board = { selectBoardTab };
    selectBoardTab(figures.length ? "figure-0" : "doodle");
  }

  /* ---------- 草图 ---------- */

  function setupDoodle() {
    const canvas = document.querySelector("[data-doodle-canvas]");
    if (!canvas) return;
    const context = canvas.getContext("2d");
    if (!context) return;

    const storageKey = `doodle:${CONFIG.page}`;
    let strokes = [];
    let current = null;
    let color = "#181715";

    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          strokes = parsed
            .filter((stroke) => stroke && Array.isArray(stroke.points))
            .map((stroke) => ({
              color: typeof stroke.color === "string" ? stroke.color : "#181715",
              width: Number(stroke.width) || 0.006,
              points: stroke.points.filter(
                (point) =>
                  Array.isArray(point) &&
                  point.length === 2 &&
                  Number.isFinite(point[0]) &&
                  Number.isFinite(point[1])
              ),
            }))
            .filter((stroke) => stroke.points.length > 0);
        }
      }
    } catch (error) {
      strokes = [];
    }

    function save() {
      while (strokes.reduce((total, stroke) => total + stroke.points.length, 0) > 6000) {
        strokes.shift();
      }
      try {
        localStorage.setItem(storageKey, JSON.stringify(strokes));
      } catch (error) {
        /* 草图丢掉也不影响阅读。 */
      }
    }

    function size() {
      return { width: Math.max(1, canvas.clientWidth), height: Math.max(1, canvas.clientHeight) };
    }

    function redraw() {
      const { width, height } = size();
      const ratio = window.devicePixelRatio || 1;
      if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
        canvas.width = Math.round(width * ratio);
        canvas.height = Math.round(height * ratio);
      }
      context.setTransform(ratio, 0, 0, ratio, 0, 0);
      context.clearRect(0, 0, width, height);
      context.fillStyle = "#fff";
      context.fillRect(0, 0, width, height);
      context.lineCap = "round";
      context.lineJoin = "round";
      strokes.forEach((stroke) => drawStroke(stroke, width, height));
    }

    function drawStroke(stroke, width, height) {
      if (stroke.points.length === 0) return;
      context.strokeStyle = stroke.color;
      context.lineWidth = Math.max(1, stroke.width * width);
      context.beginPath();
      stroke.points.forEach((point, index) => {
        const x = point[0] * width;
        const y = point[1] * height;
        if (index === 0) context.moveTo(x, y);
        else context.lineTo(x, y);
      });
      context.stroke();
    }

    function pointFromEvent(event) {
      const rect = canvas.getBoundingClientRect();
      return [
        clamp((event.clientX - rect.left) / rect.width, 0, 1),
        clamp((event.clientY - rect.top) / rect.height, 0, 1),
      ];
    }

    canvas.addEventListener("pointerdown", (event) => {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      event.preventDefault();
      canvas.setPointerCapture(event.pointerId);
      current = { color, width: 0.006, points: [pointFromEvent(event)] };
      strokes.push(current);
      redraw();
    });

    canvas.addEventListener("pointermove", (event) => {
      if (!current) return;
      event.preventDefault();
      const point = pointFromEvent(event);
      const previous = current.points[current.points.length - 1];
      if (Math.abs(point[0] - previous[0]) + Math.abs(point[1] - previous[1]) < 0.0015) return;
      current.points.push(point);
      const { width, height } = size();
      context.strokeStyle = current.color;
      context.lineWidth = Math.max(1, current.width * width);
      context.beginPath();
      context.moveTo(previous[0] * width, previous[1] * height);
      context.lineTo(point[0] * width, point[1] * height);
      context.stroke();
    });

    const finish = () => {
      if (!current) return;
      current = null;
      save();
    };
    canvas.addEventListener("pointerup", finish);
    canvas.addEventListener("pointercancel", finish);
    window.addEventListener("pagehide", save);

    document.querySelectorAll("[data-doodle-color]").forEach((button) => {
      button.addEventListener("click", () => {
        color = button.dataset.doodleColor || "#181715";
        document.querySelectorAll("[data-doodle-color]").forEach((item) => {
          item.setAttribute("aria-pressed", String(item === button));
        });
      });
    });

    const undo = document.querySelector("[data-doodle-undo]");
    if (undo) {
      undo.addEventListener("click", () => {
        strokes.pop();
        redraw();
        save();
      });
    }

    const clear = document.querySelector("[data-doodle-clear]");
    if (clear) {
      clear.addEventListener("click", () => {
        strokes = [];
        redraw();
        save();
      });
    }

    const saveSvg = document.querySelector("[data-doodle-save]");
    if (saveSvg) {
      saveSvg.addEventListener("click", () => {
        const { width, height } = size();
        const svgWidth = 1000;
        const svgHeight = Math.round((height / width) * svgWidth);
        const parts = [
          `<svg xmlns="http://www.w3.org/2000/svg" width="${svgWidth}" height="${svgHeight}" viewBox="0 0 ${svgWidth} ${svgHeight}">`,
          `<rect width="100%" height="100%" fill="#fff"/>`,
        ];
        strokes.forEach((stroke) => {
          if (!stroke.points.length) return;
          const path = stroke.points
            .map((point, index) => {
              const x = (point[0] * svgWidth).toFixed(1);
              const y = (point[1] * svgHeight).toFixed(1);
              return `${index === 0 ? "M" : "L"}${x} ${y}`;
            })
            .join(" ");
          parts.push(
            `<path d="${path}" fill="none" stroke="${stroke.color}" stroke-width="${(
              stroke.width * svgWidth
            ).toFixed(1)}" stroke-linecap="round" stroke-linejoin="round"/>`
          );
        });
        parts.push("</svg>");
        const blob = new Blob([parts.join("")], { type: "image/svg+xml" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `${CONFIG.page.replace(/\.html$/, "")}-doodle.svg`;
        document.body.append(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(url), 2000);
      });
    }

    const resize = debounce(redraw, 120);
    window.addEventListener("resize", resize);
    window.addEventListener("doodle:resize", resize);
    if ("ResizeObserver" in window) new ResizeObserver(resize).observe(canvas);
    window.setTimeout(redraw, 80);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(redraw).catch(() => {});
    }
  }

  /* ---------- 目标定位 ---------- */

  function applyTarget() {
    if (!state.targetAnchor || !state.loaded) return;
    const block = state.byAnchor.get(state.targetAnchor);
    if (!block) {
      state.targetAnchor = null;
      return;
    }
    setSelected(block.anchor, true);
    state.composer = null;
    renderDesk();
    if (state.targetIssue) {
      const item = notesBody.querySelector(
        `.desk-comment[data-issue="${String(state.targetIssue)}"]`
      );
      if (item) {
        window.setTimeout(() => item.scrollIntoView({ block: "nearest" }), 50);
      }
    }
    if (state.mobile) openDesk("notes");
    window.setTimeout(() => {
      block.node.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 80);
    state.targetAnchor = null;
  }

  /* ---------- 初始化 ---------- */

  const params = new URLSearchParams(location.search);
  state.targetAnchor = params.get("margin") || params.get("anchor") || null;
  state.targetIssue = params.get("issue");

  collectBlocks();
  setupBoard();
  setupDoodle();
  updateDeskHeader();
  updateTicks();
  renderDesk();
  layoutTicks();
  if (!state.mobile) {
    deskOpenButtons.forEach((button) => button.setAttribute("aria-expanded", "true"));
  }

  if (state.targetAnchor) {
    loadComments(true);
  }

  const relayout = debounce(() => {
    const wasMobile = state.mobile;
    state.mobile = mobileQuery.matches;
    if (wasMobile !== state.mobile) {
      if (!state.mobile) {
        closeDesk();
        deskOpenButtons.forEach((button) => button.setAttribute("aria-expanded", "true"));
      } else {
        deskOpenButtons.forEach((button) => button.setAttribute("aria-expanded", "false"));
      }
      layoutTicks();
    } else {
      layoutTicks();
    }
  }, 120);

  window.addEventListener("resize", relayout);
  window.addEventListener("load", layoutTicks);
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(layoutTicks).catch(() => {});
  }
  if ("ResizeObserver" in window) {
    new ResizeObserver(debounce(layoutTicks, 120)).observe(article);
  }
  Array.from(body.querySelectorAll("img")).forEach((image) => {
    if (!image.complete) image.addEventListener("load", layoutTicks, { once: true });
  });

})();
