/* 注记页 · 3 栏阅读
 *
 * 左：读者图板（正文图版 / 草图）。右：贴着段落的页边批注。
 * 批注存进 GitHub Issues，标题格式 [margin] <page>#<anchor>，
 * 正文开头带一段 base64 元数据（页码、锚点、引文）。
 * 这样静态页面不用后端，也能让任何人用 GitHub 账号留言，
 * 并让 /inbox.html 把新留言列成待看项。
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
  const stage = document.querySelector("[data-margin-stage]");
  const loadButtons = Array.from(document.querySelectorAll("[data-margin-load]"));
  const boardToggleButtons = Array.from(document.querySelectorAll("[data-board-toggle]"));
  const boardCloseButtons = Array.from(document.querySelectorAll("[data-board-close]"));

  if (!body || !article || !stage) return;

  const state = {
    blocks: [],
    byAnchor: new Map(),
    pins: new Map(),
    cards: new Map(),
    issues: [],
    loaded: false,
    loading: false,
    failed: false,
    fetchPromise: null,
    targetAnchor: null,
    targetIssue: null,
    targetTimer: 0,
    composer: null,
    composerHiddenCard: null,
    mobile: matchMedia("(max-width: 760px)").matches,
    board: null,
  };

  const mobileQuery = matchMedia("(max-width: 760px)");
  const overlayQuery = matchMedia("(max-width: 1240px)");

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

  /* ---------- 收集可批注的块 ---------- */

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

  function collectBlocks() {
    const used = new Set();

    Array.from(body.children).forEach((element) => {
      if (!(element instanceof HTMLElement)) return;
      if (!element.matches("p,h2,h3,figure,blockquote,ul,ol,.table-wrap")) return;

      const text = blockText(element).replace(/\s+/g, " ").trim();
      if (!text) return;

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

      const block = { node: element, anchor, text, top: 0 };
      state.blocks.push(block);
      state.byAnchor.set(anchor, block);

      const pin = node("button", "margin-pin");
      pin.type = "button";
      pin.dataset.anchor = anchor;
      pin.title = "Add a margin note";
      pin.setAttribute("aria-label", `Add a margin note on “${shorten(text, 70)}”`);
      const line = node("span", "margin-pin-line");
      const plus = node("span", "margin-pin-plus", "+");
      plus.setAttribute("aria-hidden", "true");
      pin.append(line, plus);
      pin.addEventListener("click", () => {
        ensureCommentsLoaded();
        const existing = state.issues.some((issue) => issue.anchor === anchor);
        if (existing) {
          focusMargin(anchor);
        } else {
          openComposer(anchor, text, false);
        }
      });
      element.addEventListener("mouseenter", () => pin.classList.add("is-active"));
      element.addEventListener("mouseleave", () => pin.classList.remove("is-active"));
      pin.addEventListener("mouseenter", () => pin.classList.add("is-active"));
      pin.addEventListener("mouseleave", () => pin.classList.remove("is-active"));

      state.pins.set(anchor, pin);
      stage.append(pin);
    });
  }

  /* ---------- GitHub Issues 读取 ---------- */

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

  function updateLoadButtons() {
    const label = state.failed
      ? "margin notes · retry"
      : state.loading
        ? "margin notes · loading"
        : state.loaded
          ? `margin notes · ${state.issues.length}`
          : "margin notes";

    loadButtons.forEach((button) => {
      button.textContent = label;
      button.classList.toggle("is-error", state.failed);
      button.title = state.loaded
        ? `${state.issues.length} margin note${state.issues.length === 1 ? "" : "s"} on this page`
        : "Load margin notes from GitHub Issues (only when you ask)";
    });
  }

  function showMarginStatus(message) {
    document.querySelectorAll(".margin-status").forEach((item) => item.remove());
    const status = node("p", "margin-status");
    status.append(document.createTextNode(message));
    const link = node("a", "", "GitHub Issues");
    link.href = `https://github.com/${CONFIG.repo}/issues`;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    status.append(document.createTextNode(" "), link);
    if (state.mobile) {
      const first = state.blocks[0] && state.blocks[0].node;
      if (first) first.after(status);
      else stage.append(status);
    } else {
      stage.append(status);
    }
    layoutMargins();
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
    updateLoadButtons();

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
          renderCards();
          showMarginStatus("Margin notes could not be loaded.");
        }
      } finally {
        state.loading = false;
        state.fetchPromise = null;
        updateLoadButtons();
        layoutMargins();
        applyTarget();
      }
    })();

    return state.fetchPromise;
  }

  function applyIssues(issues) {
    document.querySelectorAll(".margin-status").forEach((item) => item.remove());
    state.issues = issues
      .filter((issue) => issue && issue.anchor && state.byAnchor.has(issue.anchor))
      .sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
    state.loaded = true;
    state.failed = false;
    renderCards();
    updateLoadButtons();
    layoutMargins();
    applyTarget();
  }

  function ensureCommentsLoaded() {
    if (state.loaded || state.loading) return state.fetchPromise || Promise.resolve();
    return loadComments(false);
  }

  /* ---------- 页边卡片 ---------- */

  function buildIssueElement(issue) {
    const item = node("div", "margin-comment");
    item.dataset.issue = String(issue.number);

    if (issue.text) {
      const text = node("p", "margin-comment-text");
      text.append(linkify(issue.text));
      item.append(text);
    } else {
      const text = node("p", "margin-comment-text", "This note lives on GitHub.");
      item.append(text);
    }

    const meta = node("p", "margin-comment-meta");
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
    return item;
  }

  function buildCard(group) {
    const issue = group[0];
    const block = state.byAnchor.get(issue.anchor);
    const card = document.createElement("article");
    card.className = "margin-card";
    card.dataset.anchor = issue.anchor;
    card.dataset.issues = group.map((item) => item.number).join(" ");
    card.setAttribute("aria-label", "Margin notes");
    card.tabIndex = -1;

    const head = node("header", "margin-card-head");
    const label = node("span", "margin-card-label", "margin note");
    label.setAttribute("aria-hidden", "true");
    head.append(label);
    card.append(head);

    const quoteText = issue.quote || (block ? block.text : "");
    if (quoteText) {
      const quote = node("blockquote", "margin-quote");
      quote.textContent = `“${shorten(quoteText, 240)}”`;
      card.append(quote);
    }

    const comments = node("div", "margin-comments");
    group.forEach((item) => comments.append(buildIssueElement(item)));
    card.append(comments);

    const reply = node("button", "margin-reply", "add a note");
    reply.type = "button";
    reply.addEventListener("click", () => {
      openComposer(issue.anchor, quoteText, true);
    });
    card.append(reply);
    return card;
  }

  function renderCards() {
    state.cards.forEach((card) => card.remove());
    state.cards.clear();

    const groups = new Map();
    state.issues.forEach((issue) => {
      if (!groups.has(issue.anchor)) groups.set(issue.anchor, []);
      groups.get(issue.anchor).push(issue);
    });

    groups.forEach((group, anchor) => {
      const block = state.byAnchor.get(anchor);
      if (!block) return;
      const card = buildCard(group);
      state.cards.set(anchor, card);
      if (state.mobile) {
        card.classList.add("is-inline");
        block.node.after(card);
      } else {
        stage.append(card);
      }
    });

    if (state.composer && !state.mobile) {
      const existing = state.cards.get(state.composer.anchor);
      if (existing) {
        existing.hidden = true;
        state.composerHiddenCard = existing;
      }
    }

    state.pins.forEach((pin, anchor) => {
      pin.hidden = state.mobile || state.cards.has(anchor);
    });
    layoutMargins();
  }

  function clearTargetHighlights() {
    document
      .querySelectorAll(".is-target, .is-target-comment")
      .forEach((element) => element.classList.remove("is-target", "is-target-comment"));
  }

  function applyTarget() {
    if (!state.targetAnchor) return;
    const block = state.byAnchor.get(state.targetAnchor);
    if (!block) return;

    clearTargetHighlights();
    block.node.classList.add("is-target");

    let card = state.cards.get(state.targetAnchor);
    if (state.targetIssue) {
      const found = Array.from(state.cards.values()).find((item) =>
        (item.dataset.issues || "").split(" ").includes(String(state.targetIssue))
      );
      if (found) card = found;
    }
    if (card) card.classList.add("is-target");

    if (state.targetIssue) {
      const comment = document.querySelector(
        `.margin-comment[data-issue="${String(state.targetIssue)}"]`
      );
      if (comment) comment.classList.add("is-target-comment");
    }

    const target = card || block.node;
    window.setTimeout(() => {
      target.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 60);

    window.clearTimeout(state.targetTimer);
    state.targetTimer = window.setTimeout(() => {
      clearTargetHighlights();
    }, 6000);
  }

  /* ---------- 批注编辑器 ---------- */

  function closeComposer() {
    if (!state.composer) return;
    const { card, block } = state.composer;
    card.remove();
    if (block) block.classList.remove("is-comment-target");
    if (state.composerHiddenCard && state.composerHiddenCard.isConnected) {
      state.composerHiddenCard.hidden = false;
    }
    state.composerHiddenCard = null;
    state.composer = null;
    layoutMargins();
  }

  function openComposer(anchor, quoteText, fromExisting) {
    const block = state.byAnchor.get(anchor);
    if (!block) return;
    closeComposer();

    const card = document.createElement("article");
    card.className = "margin-card is-composer";
    card.dataset.anchor = anchor;
    card.setAttribute("aria-label", "Write a margin note");
    if (state.mobile) card.classList.add("is-inline");

    const head = node("header", "margin-card-head");
    const label = node("span", "margin-card-label", fromExisting ? "reply" : "margin note");
    const close = node("button", "margin-card-close", "×");
    close.type = "button";
    close.setAttribute("aria-label", "Close margin note editor");
    close.addEventListener("click", closeComposer);
    head.append(label, close);
    card.append(head);

    if (quoteText) {
      const quote = node("blockquote", "margin-quote");
      quote.textContent = `“${shorten(quoteText, 240)}”`;
      card.append(quote);
    }

    const form = document.createElement("form");
    form.className = "margin-form";
    const field = document.createElement("textarea");
    field.required = true;
    field.maxLength = 3000;
    field.rows = 5;
    field.placeholder = "Write a note for this passage…";
    field.setAttribute("aria-label", "Your margin note");
    form.append(field);

    const hint = node(
      "p",
      "margin-form-hint",
      "Posts to GitHub Issues. Your GitHub account is the byline; the note appears here after a refresh."
    );
    form.append(hint);

    const actions = node("div", "margin-form-actions");
    const submit = node("button", "margin-submit", "Post on GitHub ↗");
    submit.type = "submit";
    const cancel = node("button", "margin-cancel", "cancel");
    cancel.type = "button";
    cancel.addEventListener("click", closeComposer);
    actions.append(submit, cancel);
    form.append(actions);

    const status = node("p", "margin-form-status");
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
        quote: shorten(quoteText, 260),
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

    card.append(form);
    state.composer = { card, block: block.node, anchor };
    block.node.classList.add("is-comment-target");

    if (state.mobile) {
      block.node.after(card);
    } else {
      const existing = state.cards.get(anchor);
      if (existing) {
        existing.hidden = true;
        state.composerHiddenCard = existing;
      }
      stage.append(card);
    }

    layoutMargins();
    window.setTimeout(() => {
      card.scrollIntoView({ behavior: "smooth", block: "nearest" });
      field.focus({ preventScroll: true });
    }, 40);
  }

  /* ---------- 定位 ---------- */

  function layoutMargins() {
    if (state.mobile) {
      stage.style.height = "";
      state.pins.forEach((pin) => {
        pin.style.top = "";
      });
      Array.from(state.cards.values()).forEach((card) => {
        card.style.top = "";
      });
      if (state.composer) state.composer.card.style.top = "";
      return;
    }

    const stageTop = stage.getBoundingClientRect().top;
    state.blocks.forEach((block) => {
      block.top = Math.max(0, block.node.getBoundingClientRect().top - stageTop);
      const pin = state.pins.get(block.anchor);
      if (pin) pin.style.top = `${block.top}px`;
    });

    const items = Array.from(state.cards.values())
      .filter((card) => !card.hidden)
      .map((card) => ({
        card,
        top: (state.byAnchor.get(card.dataset.anchor) || {}).top || 0,
      }));

    if (state.composer) {
      const block = state.byAnchor.get(state.composer.anchor);
      items.push({ card: state.composer.card, top: block ? block.top : 0 });
    }

    items.sort((a, b) => a.top - b.top);

    let cursor = 0;
    items.forEach((item) => {
      const top = Math.max(item.top, cursor);
      item.card.style.top = `${top}px`;
      cursor = top + item.card.offsetHeight + 20;
    });

    stage.style.height = `${Math.max(article.offsetHeight, cursor + 16)}px`;
  }

  function focusMargin(anchor) {
    state.targetAnchor = anchor;
    state.targetIssue = null;
    applyTarget();
  }

  /* ---------- 选中文字 ---------- */

  function handleSelectionEnd() {
    window.setTimeout(() => {
      const selection = window.getSelection();
      if (!selection || selection.isCollapsed || selection.rangeCount === 0) return;
      let text = selection.toString().replace(/\s+/g, " ").trim();
      if (text.length < 6) return;

      const range = selection.getRangeAt(0);
      const wrapper = document.createElement("div");
      wrapper.append(range.cloneContents());
      text = cleanText(wrapper);
      if (text.length < 6) return;

      let selected = range.startContainer;
      if (selected.nodeType === Node.TEXT_NODE) selected = selected.parentElement;
      if (!selected || !body.contains(selected)) return;
      if (selected.closest(".margin-card, .board, .comments")) return;

      const block = selected.closest("[data-margin-id]");
      if (!block || !body.contains(block)) return;
      ensureCommentsLoaded();
      openComposer(block.dataset.marginId, text, false);
    }, 0);
  }

  document.addEventListener("mouseup", handleSelectionEnd);
  document.addEventListener("keyup", (event) => {
    if (event.shiftKey || event.key === "Shift") handleSelectionEnd();
  });

  /* ---------- 图版放大 ---------- */

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

  /* ---------- 图板 ---------- */

  function setupBoard() {
    const board = document.querySelector("[data-board]");
    const tabs = document.querySelector("[data-board-tabs]");
    const figurePanel = document.querySelector('[data-board-panel="figure"]');
    const doodlePanel = document.querySelector('[data-board-panel="doodle"]');
    if (!board || !tabs || !figurePanel || !doodlePanel) return;

    const figures = Array.from(body.querySelectorAll("figure.post-figure")).map((figure, index) => {
      const image = figure.querySelector("img");
      const caption = figure.querySelector("figcaption");
      return {
        index,
        src: image ? image.getAttribute("src") : "",
        alt: image ? image.getAttribute("alt") || "" : "",
        caption: caption ? cleanText(caption) : "",
      };
    });

    const doodleTab = tabs.querySelector('[data-board-tab="doodle"]');
    if (!doodleTab) return;

    const note = board.querySelector(".board-note");
    if (note) {
      note.textContent = figures.length
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
      wrapper.className = "board-figure";
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

    figures.forEach((figure) => {
      const element = body.querySelectorAll("figure.post-figure")[figure.index];
      if (!element) return;
      const button = node("button", "pin-figure", "pin to board");
      button.type = "button";
      button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        selectBoardTab(`figure-${figure.index}`);
        openBoard();
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

    state.board = { selectBoardTab, open: openBoard, close: closeBoard };
    selectBoardTab(figures.length ? "figure-0" : "doodle");
  }

  function openBoard() {
    document.body.classList.add("board-open");
    boardToggleButtons.forEach((button) => button.setAttribute("aria-expanded", "true"));
    if (state.board && overlayQuery.matches) {
      const board = document.querySelector("[data-board]");
      if (board) board.scrollTop = 0;
    }
  }

  function closeBoard() {
    document.body.classList.remove("board-open");
    boardToggleButtons.forEach((button) => button.setAttribute("aria-expanded", "false"));
  }

  boardToggleButtons.forEach((button) => {
    button.addEventListener("click", () => {
      if (document.body.classList.contains("board-open")) closeBoard();
      else openBoard();
    });
  });
  boardCloseButtons.forEach((button) => button.addEventListener("click", closeBoard));

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.body.classList.contains("board-open")) closeBoard();
  });

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
    let resizeTimer = 0;

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
                (point) => Array.isArray(point) && point.length === 2 && Number.isFinite(point[0]) && Number.isFinite(point[1])
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
    if ("ResizeObserver" in window) {
      new ResizeObserver(resize).observe(canvas);
    }
    // 字体/布局稳定后再定一次尺寸。
    window.setTimeout(redraw, 80);
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(redraw).catch(() => {});
    }
  }

  /* ---------- 初始化 ---------- */

  const params = new URLSearchParams(location.search);
  state.targetAnchor = params.get("margin") || params.get("anchor") || null;
  state.targetIssue = params.get("issue");

  collectBlocks();
  setupBoard();
  setupDoodle();

  loadButtons.forEach((button) => {
    button.addEventListener("click", () => loadComments(true));
  });

  if (state.targetAnchor) {
    loadComments(true);
  } else {
    updateLoadButtons();
  }

  if (state.mobile) {
    state.pins.forEach((pin) => {
      pin.hidden = true;
    });
  }

  const relayout = debounce(() => {
    const wasMobile = state.mobile;
    state.mobile = mobileQuery.matches;
    if (wasMobile !== state.mobile) {
      renderCards();
      if (state.composer) {
        const { card, block } = state.composer;
        if (state.mobile) {
          card.classList.add("is-inline");
          block.after(card);
        } else {
          card.classList.remove("is-inline");
          stage.append(card);
        }
      }
    }
    layoutMargins();
  }, 140);

  window.addEventListener("resize", relayout);
  window.addEventListener("load", layoutMargins);
  if (document.fonts?.ready) document.fonts.ready.then(layoutMargins).catch(() => {});
  if ("ResizeObserver" in window) {
    new ResizeObserver(debounce(layoutMargins, 120)).observe(article);
  }
  Array.from(body.querySelectorAll("img")).forEach((image) => {
    if (!image.complete) image.addEventListener("load", layoutMargins, { once: true });
  });

  if (state.mobile) {
    state.pins.forEach((pin) => {
      pin.hidden = true;
    });
  }
})();
