#!/usr/bin/env node
/**
 * 把 vitrine/instrumentality 下的 Markdown 注记排成站点页面。
 *
 * 设计目标和已上线的三篇注记一致：
 *   - KaTeX 在构建时预渲染成 HTML + MathML，页面不加载公式脚本；
 *   - 公式段先抽成占位符再交给 markdown-it，避免 $...$ 里的 _ * \ 被 Markdown 吃掉；
 *   - 图片不留在正文里，统一收进右侧阅读桌的 figure-store，由 post.js 生成图版 tabs；
 *   - 页面外壳、评论、统计、上下篇、canonical 都由 build.py 传入的站点地址生成。
 *
 * 目录约定：
 *   - vitrine/instrumentality/**\/*.md 都会发布（子目录可以自动当 slug）；
 *   - 以 _ 或 . 开头的文件/目录不发布，可用来放草稿和素材；
 *   - front matter 支持：title / heading / list_title / deck / date / slug /
 *     summary / lang / draft。
 *
 * 用法（一般由 build.py 调用）：
 *   node tools/posts/build.mjs \
 *     --src vitrine/instrumentality --out _site \
 *     --site-url https://example.github.io/repo/ \
 *     --manifest /tmp/posts.json
 */

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import katex from "katex";
import MarkdownIt from "markdown-it";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");

const DEFAULT_SRC = path.join(ROOT, "vitrine", "instrumentality");
const DEFAULT_OUT = path.join(ROOT, "_site");
const DEFAULT_TEMPLATE = path.join(HERE, "note-template.html");
const DEFAULT_SITE_URL = "https://shuyuew1991.github.io/personal-page/";

const IMAGE_EXTS = new Set([".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".apng", ".ico"]);

/** KaTeX 0.16.x 的内部类名和站点 CSS 的命名对齐：base → katex-base，等等。 */
const KATEX_CLASSES = new Set(["base", "strut", "sizing", "stretchy"]);

const md = new MarkdownIt({ html: true, linkify: false, typographer: false });

// 表格横向滚动容器：和现有注记页的 .table-wrap 完全一致。
md.renderer.rules.table_open = () => '<div class="table-wrap"><table>\n';
md.renderer.rules.table_close = () => "</table></div>\n";

const defaultImageRule =
  md.renderer.rules.image ||
  ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options));

md.renderer.rules.image = (tokens, idx, options, env, self) => {
  const token = tokens[idx];
  const src = token.attrGet("src") || "";
  const post = env && env.post;
  if (post && isRelativeAsset(src)) {
    const asset = copyAsset(post, src);
    token.attrSet("src", asset.url);
  }
  token.attrSet("loading", "lazy");
  token.attrSet("decoding", "async");
  return defaultImageRule(tokens, idx, options, env, self);
};

/* ---------- 参数 ---------- */

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const item = argv[i];
    if (!item.startsWith("--")) continue;
    const key = item.slice(2);
    const next = argv[i + 1];
    if (next !== undefined && !next.startsWith("--")) {
      args[key] = next;
      i += 1;
    } else {
      args[key] = true;
    }
  }
  return args;
}

const args = parseArgs(process.argv.slice(2));
const SRC = path.resolve(args.src || DEFAULT_SRC);
const OUT = path.resolve(args.out || DEFAULT_OUT);
const TEMPLATE = path.resolve(args.template || DEFAULT_TEMPLATE);
const MANIFEST = path.resolve(args.manifest || path.join(OUT, ".posts-manifest.json"));
const SITE_URL = `${String(args["site-url"] || DEFAULT_SITE_URL).replace(/\/+$/, "")}/`;

/* ---------- 通用小工具 ---------- */

const escapeHtml = (value) => md.utils.escapeHtml(String(value == null ? "" : value));

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function isRelativeAsset(src) {
  return Boolean(src) && !/^(?:[a-z]+:|\/\/|\/|#)/i.test(src);
}

function pad2(value) {
  return String(value).padStart(2, "0");
}

function todayFromDate(date) {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(date.getDate())}`;
}

/* ---------- front matter ---------- */

function parseFrontMatter(source) {
  const text = String(source).replace(/^\uFEFF/, "");
  if (!text.startsWith("---")) return { meta: {}, body: text };

  const lines = text.split(/\r?\n/);
  if (lines[0].trim() !== "---") return { meta: {}, body: text };

  let end = -1;
  for (let i = 1; i < lines.length; i += 1) {
    if (lines[i].trim() === "---") {
      end = i;
      break;
    }
  }
  if (end === -1) throw new Error("front matter 没有结束的 ---");

  const meta = {};
  for (const rawLine of lines.slice(1, end)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    const colon = line.indexOf(":");
    if (colon === -1) continue;
    const key = line.slice(0, colon).trim().toLowerCase();
    let value = line.slice(colon + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (value === "true") value = true;
    else if (value === "false") value = false;
    meta[key] = value;
  }

  return { meta, body: lines.slice(end + 1).join("\n").replace(/^\n+/, "") };
}

/* ---------- 代码保护：先摘掉 fenced code 和行内 code，数学段只扫描普通正文 ---------- */

function protectCode(source) {
  const nonce = `CXP${crypto.randomBytes(4).toString("hex").toUpperCase()}`;
  let seq = 0;
  const store = new Map();
  const placeholder = () => `${nonce}${seq++}Z`;

  const lines = source.split("\n");
  const kept = [];
  let i = 0;
  while (i < lines.length) {
    const open = /^[ \t]*(`{3,}|~{3,})/.exec(lines[i]);
    if (open) {
      const marker = open[1];
      const closeRe = new RegExp(`^[ \\t]*${marker[0]}{${marker.length},}[ \\t]*$`);
      let j = i + 1;
      while (j < lines.length && !closeRe.test(lines[j])) j += 1;
      if (j < lines.length) {
        const key = placeholder();
        store.set(key, lines.slice(i, j + 1).join("\n"));
        kept.push(key);
        i = j + 1;
        continue;
      }
    }
    kept.push(lines[i]);
    i += 1;
  }

  let text = kept.join("\n");
  text = text.replace(/(`+)([^`\n]*?)\1/g, (span) => {
    const key = placeholder();
    store.set(key, span);
    return key;
  });

  return {
    text,
    restore(value) {
      let out = value;
      for (const [key, original] of store) out = out.split(key).join(original);
      return out;
    },
  };
}

/* ---------- 数学段抽取 + KaTeX 预渲染 ---------- */

function prefixKatex(html) {
  return html.replace(/class="([^"]*)"/g, (whole, value) => {
    const classes = value
      .split(/\s+/)
      .filter(Boolean)
      .map((name) => (KATEX_CLASSES.has(name) ? `katex-${name}` : name));
    return `class="${classes.join(" ")}"`;
  });
}

function createMath() {
  const nonce = `KXM${crypto.randomBytes(4).toString("hex").toUpperCase()}`;
  let seq = 0;
  const map = new Map();

  function add(tex, display) {
    const html = prefixKatex(
      katex.renderToString(tex, {
        displayMode: display,
        throwOnError: false,
        strict: false,
        trust: true,
      })
    );
    const key = `${nonce}${seq++}Z`;
    map.set(key, { tex, display, html });
    return key;
  }

  function extract(source) {
    let out = "";
    let i = 0;
    const n = source.length;
    if (source.includes(nonce)) throw new Error("正文里出现了和公式占位符相同的字符串");

    while (i < n) {
      // 转义的美元符号原样保留，交给 Markdown 处理。
      if (source[i] === "\\" && source[i + 1] === "$") {
        out += "\\$";
        i += 2;
        continue;
      }

      if (source.startsWith("$$", i)) {
        const close = source.indexOf("$$", i + 2);
        if (close !== -1) {
          out += add(source.slice(i + 2, close), true);
          i = close + 2;
          continue;
        }
      }

      if (source.startsWith("\\[", i) && source[i - 1] !== "\\") {
        const close = source.indexOf("\\]", i + 2);
        if (close !== -1) {
          out += add(source.slice(i + 2, close), true);
          i = close + 2;
          continue;
        }
      }

      if (source[i] === "$" && source[i + 1] !== "$" && source[i - 1] !== "\\") {
        let close = i + 1;
        while ((close = source.indexOf("$", close)) !== -1) {
          if (source[close - 1] === "\\") {
            close += 1;
            continue;
          }
          break;
        }
        if (close !== -1) {
          const tex = source.slice(i + 1, close);
          if (!tex.includes("\n")) {
            out += add(tex, false);
            i = close + 1;
            continue;
          }
        }
      }

      if (source.startsWith("\\(", i) && source[i - 1] !== "\\") {
        const close = source.indexOf("\\)", i + 2);
        if (close !== -1) {
          const tex = source.slice(i + 2, close);
          if (!tex.includes("\n")) {
            out += add(tex, false);
            i = close + 2;
            continue;
          }
        }
      }

      out += source[i];
      i += 1;
    }

    return out;
  }

  return { add, extract, map };
}

function restoreMath(html, mathMap, { wrap }) {
  let out = html;
  for (const [key, info] of mathMap) {
    const rendered = wrap
      ? info.display
        ? `<span class="math-display">${info.html}</span>`
        : `<span class="math-inline">${info.html}</span>`
      : info.html;
    out = out.split(key).join(rendered);
  }
  return out;
}

function demoteMath(text, mathMap) {
  let out = text;
  for (const [key, info] of mathMap) out = out.split(key).join(info.tex);
  return out;
}

/** 把一段 Markdown 内联源码渲染成 HTML；用于 front matter 里的 heading / deck。 */
function renderInlineSource(source) {
  const math = createMath();
  const text = normalizeStrong(math.extract(source));
  return restoreMath(md.renderInline(text), math.map, { wrap: false });
}

/** 纯文本标题/摘要：去掉 Markdown 标记和公式定界符，不保留 HTML。 */
function plainInline(source, mathMap) {
  let text = String(source == null ? "" : source)
    .replace(/<[^>]+>/g, "")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1");
  if (mathMap) text = demoteMath(text, mathMap);
  return text.replace(/[*_~`]/g, "").replace(/\s+/g, " ").trim();
}

/**
 * 中文全角标点紧贴 ** 时，CommonMark 的 flanking 规则会把 `**A**与**B**`
 * 解析成 `**A<strong>与</strong>B**`。中文写作里这种写法很常见，
 * 所以先把成对的 ** 直接换成 <strong>，再交给 markdown-it；代码和公式已经
 * 被占位符保护，不会被误伤。
 */
function normalizeStrong(text) {
  return text.replace(/\*\*([^\n]+?)\*\*/g, (whole, inner) =>
    inner.trim() ? `<strong>${inner}</strong>` : whole
  );
}

/* ---------- 图片 ---------- */

function copyAsset(post, rawSrc) {
  const cleaned = decodeURIComponent(String(rawSrc).split("#")[0].split("?")[0]);
  const absolute = path.resolve(path.dirname(post.file), cleaned);
  const rel = path.relative(post.srcRoot, absolute);
  if (!rel || rel.startsWith("..") || path.isAbsolute(rel)) {
    throw new Error(`${path.basename(post.file)} 引用了注记目录之外的图片：${rawSrc}`);
  }
  if (!fs.existsSync(absolute) || !fs.statSync(absolute).isFile()) {
    throw new Error(`${path.basename(post.file)} 引用了不存在的图片：${rawSrc}`);
  }
  const ext = path.extname(absolute).toLowerCase();
  if (!IMAGE_EXTS.has(ext)) {
    throw new Error(`${path.basename(post.file)} 引用了非图片文件：${rawSrc}`);
  }

  const base = path.basename(absolute);
  const key = `${post.slug}/${base}`;
  const previous = post.assets.get(key);
  if (previous && previous !== absolute) {
    throw new Error(`${post.slug} 里有两张同名图片：${base}`);
  }
  post.assets.set(key, absolute);

  const destDir = path.join(post.out, "assets", "posts", post.slug);
  ensureDir(destDir);
  fs.copyFileSync(absolute, path.join(destDir, base));

  return { url: `assets/posts/${post.slug}/${base}`, file: absolute, base };
}

/* ---------- 标题 / 日期 / slug ---------- */

function slugify(value) {
  return String(value)
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[\s_]+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

function resolveSlug(file, meta, srcRoot, date) {
  if (meta.slug) {
    const slug = slugify(meta.slug);
    if (!slug) throw new Error(`front matter 里的 slug 不是合法英文短名：${meta.slug}`);
    return { slug, source: "front matter" };
  }

  const rel = path.relative(srcRoot, file);
  const parts = rel.split(path.sep);
  const parent = parts.length > 1 ? parts[parts.length - 2] : "";
  if (parent) {
    const fromParent = slugify(parent);
    // 只接受至少带一个字母的 slug；中文目录名常会留下 "13" 这种纯数字前缀。
    if (fromParent && /[a-z]/.test(fromParent)) return { slug: fromParent, source: "子目录名" };
  }

  const fromFile = slugify(path.basename(file, path.extname(file)));
  if (fromFile && /[a-z]/.test(fromFile)) return { slug: fromFile, source: "文件名" };

  // 中文标题也能直接发布：用相对路径哈希出一个稳定短名。想改 URL 时补 slug:。
  const normalized = rel.split(path.sep).join("/");
  const hash = crypto.createHash("sha1").update(normalized).digest("hex").slice(0, 8);
  return {
    slug: `note-${date.replace(/-/g, "")}-${hash}`,
    source: "自动生成",
  };
}

function resolveDate(file, meta) {
  if (meta.date !== undefined) {
    if (typeof meta.date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(meta.date)) {
      throw new Error(`${path.relative(ROOT, file)} 的 date 不是 YYYY-MM-DD：${meta.date}`);
    }
    return { date: meta.date, source: "front matter" };
  }

  for (const candidate of [path.basename(file), path.basename(path.dirname(file))]) {
    const found = /^(\d{4}-\d{2}-\d{2})/.exec(candidate);
    if (found) return { date: found[1], source: "文件名" };
  }

  try {
    const output = execFileSync(
      "git",
      ["log", "--follow", "--format=%cs", "--date=short", "--", path.relative(ROOT, file)],
      { cwd: ROOT, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }
    ).trim();
    const lines = output.split("\n").filter(Boolean);
    if (lines.length) return { date: lines[lines.length - 1], source: "git 首次提交" };
  } catch {
    // 不是 git 仓库或文件还没提交：继续用 mtime。
  }

  return { date: todayFromDate(new Date(fs.statSync(file).mtime)), source: "文件修改时间" };
}

/* ---------- 正文 token 处理 ---------- */

function takeFirstH1(tokens) {
  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].type === "heading_open" && tokens[i].tag === "h1") {
      const inline = tokens[i + 1];
      const content = inline && inline.type === "inline" ? inline.content : "";
      const close = tokens[i + 2] && tokens[i + 2].type === "heading_close" ? i + 3 : i + 2;
      return { content, tokens: [...tokens.slice(0, i), ...tokens.slice(close)] };
    }
  }
  return { content: "", tokens };
}

const CAPTION_BOLD =
  /^\s*(?:\*\*|<strong>)\s*((?:Figure|图)\s*\d+[A-Za-z]?\s*[.．。]?)\s*(?:\*\*|<\/strong>)\s*/;
const CAPTION_PLAIN = /^\s*((?:Figure|图)\s*\d+[A-Za-z]?\s*[.．。]?)\s+/;

function figureHtml(img, captionSource, index, post, math) {
  const rawSrc = img.attrGet("src") || "";
  if (!rawSrc) return null;

  const asset = isRelativeAsset(rawSrc) ? copyAsset(post, rawSrc) : { url: rawSrc };
  const alt = plainInline(img.content || "", math.map);
  const imageTitle = plainInline(img.attrGet("title") || "", math.map);

  let figNo = "";
  let caption = "";
  let captionIsMarkdown = false;

  if (captionSource) {
    let match = CAPTION_BOLD.exec(captionSource);
    if (!match) match = CAPTION_PLAIN.exec(captionSource);
    if (match) {
      figNo = match[1].trim();
      caption = captionSource.slice(match[0].length).trim();
    } else {
      caption = captionSource.trim();
    }
    captionIsMarkdown = true;
  } else if (imageTitle) {
    caption = imageTitle;
  } else if (alt) {
    caption = alt;
  }

  if (!figNo) figNo = `Figure ${index + 1}.`;
  if (!/[.．。]$/.test(figNo)) figNo += ".";

  const captionBody = caption
    ? captionIsMarkdown
      ? restoreMath(md.renderInline(caption), math.map, { wrap: true })
      : escapeHtml(caption)
    : "";
  const figcaption = captionBody
    ? `<figcaption><span class="fig-no">${escapeHtml(figNo)}</span> ${captionBody}</figcaption>`
    : "";

  return `<figure class="post-figure"><img src="${escapeHtml(asset.url)}" alt="${escapeHtml(alt)}" loading="lazy" decoding="async">${figcaption}</figure>`;
}

function extractFigures(tokens, post, math) {
  const kept = [];
  const figures = [];

  for (let i = 0; i < tokens.length; i += 1) {
    const open = tokens[i];
    if (open.type !== "paragraph_open" || !tokens[i + 1] || tokens[i + 1].type !== "inline") {
      kept.push(open);
      continue;
    }

    const inline = tokens[i + 1];
    const children = inline.children || [];
    const images = children.filter((child) => child.type === "image");
    const onlyImages = images.length > 0 && children.every(
      (child) =>
        child.type === "image" ||
        child.type === "softbreak" ||
        child.type === "hardbreak" ||
        (child.type === "text" && !child.content.trim())
    );

    if (!onlyImages) {
      kept.push(open);
      continue;
    }

    let end = i + 2; // paragraph_close
    let captionSource = "";
    if (
      images.length === 1 &&
      tokens[i + 3] &&
      tokens[i + 3].type === "paragraph_open" &&
      tokens[i + 4] &&
      tokens[i + 4].type === "inline"
    ) {
      const candidate = tokens[i + 4].content.trim();
      if (CAPTION_BOLD.test(candidate) || CAPTION_PLAIN.test(candidate)) {
        captionSource = tokens[i + 4].content.trim();
        end = i + 5;
      }
    }

    images.forEach((img, order) => {
      const html = figureHtml(img, captionSource, figures.length + order, post, math);
      if (html) figures.push({ html });
    });

    i = end;
  }

  return { tokens: kept, figures };
}

function firstParagraph(tokens) {
  for (let i = 0; i < tokens.length; i += 1) {
    if (tokens[i].type === "paragraph_open" && tokens[i + 1] && tokens[i + 1].type === "inline") {
      return tokens[i + 1].content || "";
    }
  }
  return "";
}

/* ---------- 单篇渲染 ---------- */

const template = fs.readFileSync(TEMPLATE, "utf8");
if (!fs.existsSync(SRC)) throw new Error(`注记目录不存在：${SRC}`);
ensureDir(OUT);

function collectMarkdown(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    if (entry.name.startsWith("_") || entry.name.startsWith(".")) continue;
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      files.push(...collectMarkdown(full));
    } else if (entry.name.toLowerCase().endsWith(".md") && entry.name.toLowerCase() !== "readme.md") {
      files.push(full);
    }
  }
  return files;
}

function buildPost(file) {
  const raw = fs.readFileSync(file, "utf8");
  const { meta, body } = parseFrontMatter(raw);
  if (meta.draft === true) return null;

  const { date, source: dateSource } = resolveDate(file, meta);
  const { slug, source: slugSource } = resolveSlug(file, meta, SRC, date);
  if (slugSource === "自动生成") {
    console.warn(`  ! ${path.relative(ROOT, file)} 没写 slug，自动用 ${slug}（想固定 URL 时补 slug:）`);
  }
  const post = {
    file,
    slug,
    date,
    dateSource,
    out: OUT,
    srcRoot: SRC,
    assets: new Map(),
    figures: [],
    hasMath: false,
  };

  const code = protectCode(body);
  const math = createMath();
  const text = code.restore(normalizeStrong(math.extract(code.text)));

  let tokens = md.parse(text, {});
  const h1 = takeFirstH1(tokens);
  tokens = h1.tokens;
  const figureResult = extractFigures(tokens, post, math);
  tokens = figureResult.tokens;
  post.figures = figureResult.figures;

  const bodyHtml = restoreMath(md.renderer.render(tokens, md.options, { post }), math.map, {
    wrap: true,
  });

  const headingSource = meta.heading || h1.content || meta.title || path.basename(file, ".md");
  const headingHtml = meta.heading
    ? renderInlineSource(String(meta.heading))
    : restoreMath(md.renderInline(h1.content || String(meta.title || path.basename(file, ".md"))), math.map, {
        wrap: false,
      });

  const title = String(
    meta.title ||
      plainInline(meta.heading || h1.content || "", math.map) ||
      path.basename(file, ".md")
  );
  const listTitle = String(meta.list_title || title);
  const deckHtml = meta.deck ? renderInlineSource(String(meta.deck)) : "";
  const lang = String(meta.lang || (/[\u3400-\u9fff]/.test(body) ? "zh-Hans" : "en"));

  let summary = meta.summary ? String(meta.summary) : "";
  if (!summary) {
    summary = plainInline(firstParagraph(tokens), math.map);
    if (summary.length > 160) summary = `${summary.slice(0, 157)}…`;
  }

  const searchable = `${headingHtml}\n${deckHtml}\n${bodyHtml}\n${post.figures.map((f) => f.html).join("\n")}`;
  post.hasMath = math.map.size > 0 || headingSource.includes("$") || /class="katex/.test(searchable);

  return {
    ...post,
    title,
    listTitle,
    summary,
    lang,
    headingHtml,
    deckHtml,
    bodyHtml,
  };
}

/* ---------- 页面拼装 ---------- */

function navBlock(label, post, isNext) {
  const className = isNext ? ' class="next"' : "";
  if (!post) {
    return `            <div${className}>\n              <div class="label">${label}</div>\n              <span>—</span>\n            </div>`;
  }
  return `            <div${className}>\n              <div class="label">${label}</div>\n              <a href="${escapeHtml(post.slug)}.html">${escapeHtml(post.title)}</a>\n            </div>`;
}

function fillTemplate(values) {
  let out = template;
  for (const [key, value] of Object.entries(values)) {
    out = out.split(`{{${key}}}`).join(value);
  }
  return out;
}

function renderPost(post, previous, next) {
  const canonical = `${SITE_URL}${post.slug}.html`;
  const figureStore = post.figures.length
    ? `        <div class="figure-store" data-figure-store hidden>\n${post.figures
        .map((figure) => `          ${figure.html}`)
        .join("\n")}\n        </div>`
    : "";

  const html = fillTemplate({
    LANG: escapeHtml(post.lang),
    TITLE: escapeHtml(post.title),
    CANONICAL: escapeHtml(canonical),
    DESCRIPTION: escapeHtml(post.summary),
    HEADING: post.headingHtml,
    DECK: post.deckHtml ? `          <p class="deck" lang="${escapeHtml(post.lang)}">${post.deckHtml}</p>` : "",
    KATEX: post.hasMath ? '  <link rel="stylesheet" href="assets/katex/katex.min.css">' : "",
    BODY: post.bodyHtml,
    PREV: navBlock("Previous", previous, false),
    NEXT: navBlock("Next", next, true),
    FIGURE_STORE: figureStore,
  });

  if (/\{\{(?:LANG|TITLE|CANONICAL|DESCRIPTION|HEADING|DECK|KATEX|BODY|PREV|NEXT|FIGURE_STORE)\}\}/.test(html)) {
    throw new Error(`${post.slug}.html 里还有未替换的模板占位符`);
  }

  fs.writeFileSync(path.join(OUT, `${post.slug}.html`), html, "utf8");
  return canonical;
}

/* ---------- 主流程 ---------- */

function main() {
  const files = collectMarkdown(SRC).sort();
  const posts = [];
  const seen = new Map();

  for (const file of files) {
    const post = buildPost(file);
    if (!post) {
      console.log(`  · 跳过草稿 ${path.relative(ROOT, file)}`);
      continue;
    }
    if (seen.has(post.slug)) {
      throw new Error(
        `slug 重复：${post.slug}\n  ${path.relative(ROOT, seen.get(post.slug))}\n  ${path.relative(ROOT, file)}`
      );
    }
    seen.set(post.slug, file);
    posts.push(post);
    if (post.dateSource !== "front matter") {
      console.warn(`  ! ${post.slug} 没写 date，按${post.dateSource}取 ${post.date}`);
    }
  }

  posts.sort((a, b) => a.date.localeCompare(b.date) || a.slug.localeCompare(b.slug));

  posts.forEach((post, index) => {
    const previous = index > 0 ? posts[index - 1] : null;
    const next = index < posts.length - 1 ? posts[index + 1] : null;
    renderPost(post, previous, next);
    console.log(`  · ${post.slug}.html  ${post.date}  ${post.title}`);
  });

  const manifest = {
    schema: 1,
    generated: new Date().toISOString(),
    site_url: SITE_URL,
    posts: posts.map((post) => ({
      slug: post.slug,
      title: post.title,
      list_title: post.listTitle,
      date: post.date,
      lang: post.lang,
      summary: post.summary,
      file: path.relative(ROOT, post.file),
      figures: post.figures.length,
    })),
  };
  ensureDir(path.dirname(MANIFEST));
  fs.writeFileSync(MANIFEST, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");

  const figureCount = posts.reduce((sum, post) => sum + post.figures.length, 0);
  console.log(`\n✓ 生成 ${posts.length} 篇注记、${figureCount} 张图版`);
}

try {
  main();
} catch (error) {
  console.error(`\n✗ ${error.message}`);
  process.exitCode = 1;
}
