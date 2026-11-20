#!/usr/bin/env node
/**
 * 把 vitrine/ 下所有 markdown 原稿转成可离线浏览的预览 HTML。
 *
 * 思路与已上线的注记页一致：
 *   - 生成阶段就用 KaTeX 把 $...$ / $$...$$ / \(...\) / \[...\] 预渲染成 HTML+MathML，
 *     页面本身不加载任何公式脚本，离线、无 CDN 依赖；
 *   - 先用占位符把数学段从正文里摘出来，再交给 markdown-it，
 *     避免 $...$ 里的 _ * \ 等字符被 Markdown 引擎吃掉；
 *   - 输出按源目录结构镜像到 .preview/（已在 .gitignore 里，不会入库），
 *     文档里的 ./images/xxx.svg 相对路径照常可用；
 *   - 另生成一个 .preview/index.html 索引页，列出全部预览文档。
 *
 * 用法：
 *   cd tools/md_preview && npm install && node build.mjs
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import katex from "katex";
import MarkdownIt from "markdown-it";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..", "..");
const VITRINE = path.join(ROOT, "vitrine");
const OUT = path.join(ROOT, ".preview");
const KATEX_SRC = path.join(ROOT, "prototypes", "v2", "b-desk", "assets", "katex");

const md = new MarkdownIt({ html: true });

// 外链（http/https/锚点）保持原样；其余一律新标签打开，不在预览里跳走。
const defaultLinkOpen = md.renderer.rules.link_open || ((tokens, idx, options, env, self) => self.renderToken(tokens, idx, options));
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const href = tokens[idx].attrGet("href") || "";
  if (!/^(https?:|#|mailto:|\/\/)/.test(href)) {
    tokens[idx].attrSet("target", "_blank");
    tokens[idx].attrSet("rel", "noopener");
  }
  return defaultLinkOpen(tokens, idx, options, env, self);
};

/* ---------- 数学段抽取：原文 -> 占位符标记，同时预渲染成 KaTeX HTML ---------- */

let seq = 0;
const placeholders = new Map();

/** 查找下一个未转义的裸 $，要求不出现在同一行之外。 */
function findInlineDollar(text, from) {
  for (let j = from; j < text.length; j++) {
    if (text[j] === "$") {
      if (j > 0 && text[j - 1] === "\\") continue;
      return j;
    }
  }
  return -1;
}

function renderMath(tex, displayMode) {
  const html = katex.renderToString(tex, {
    displayMode,
    throwOnError: false,
    strict: false,
    trust: true,
  });
  const key = `@@KATEX${seq++}@@`;
  placeholders.set(key, html);
  return key;
}

/** 从头开始扫描，把数学段替换为占位符，返回处理后的中间 Markdown。 */
function extractMath(src) {
  let out = "";
  let i = 0;
  const n = src.length;

  while (i < n) {
    // $$ ... $$ 行间公式（可跨行、带 \tag）
    if (src.startsWith("$$", i)) {
      const close = src.indexOf("$$", i + 2);
      if (close !== -1) {
        out += renderMath(src.slice(i + 2, close), true);
        i = close + 2;
        continue;
      }
    }
    // \[ ... \] 行间公式
    if (src.startsWith("\\[", i)) {
      const close = src.indexOf("\\]", i + 2);
      if (close !== -1) {
        out += renderMath(src.slice(i + 2, close), true);
        i = close + 2;
        continue;
      }
    }
    // $ ... $ 行内公式（同一行内闭合）
    if (src[i] === "$" && src[i + 1] !== "$") {
      const close = findInlineDollar(src, i + 1);
      if (close !== -1 && !src.slice(i, close + 1).includes("\n")) {
        out += renderMath(src.slice(i + 1, close), false);
        i = close + 1;
        continue;
      }
    }
    // \( ... \) 行内公式
    if (src.startsWith("\\(", i)) {
      const close = src.indexOf("\\)", i + 2);
      if (close !== -1) {
        out += renderMath(src.slice(i + 2, close), false);
        i = close + 2;
        continue;
      }
    }

    out += src[i];
    i++;
  }
  return out;
}

/* ---------- 页面模板 ---------- */

function katexCssHref(fromHtml) {
  return path.relative(path.dirname(fromHtml), path.join(OUT, "katex", "katex.min.css")).replaceAll("\\", "/");
}

function pageHtml(title, lang, bodyHtml, fromHtml) {
  const katexRel = katexCssHref(fromHtml);
  const indexRel = path.relative(path.dirname(fromHtml), path.join(OUT, "index.html")).replaceAll("\\", "/");
  return `<!doctype html>
<html lang="${lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} · vitrine 预览</title>
<link rel="stylesheet" href="${katexRel}">
<style>
  :root { --w: 44rem; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #f6f4ee; color: #23201b; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Georgia, serif; line-height: 1.75; }
  .page { max-width: var(--w); margin: 0 auto; padding: 3rem 1.5rem 6rem; background: transparent; }
  .toolbar { position: sticky; top: 0; z-index: 10; background: rgba(246,244,238,.94); border-bottom: 1px solid #e2ddd2; padding: .5rem 0; margin-bottom: 2rem; backdrop-filter: blur(4px); }
  .toolbar a { color: #6b5b45; text-decoration: none; font-size: .9rem; }
  .toolbar a:hover { text-decoration: underline; }
  h1 { font-size: 1.7rem; line-height: 1.4; margin: 0 0 1.5rem; }
  h2 { font-size: 1.25rem; margin: 2.4rem 0 .8rem; border-bottom: 1px solid #e2ddd2; padding-bottom: .35rem; }
  h3 { font-size: 1.05rem; margin: 1.8rem 0 .6rem; }
  p { margin: .9rem 0; }
  ul, ol { padding-left: 1.4rem; }
  blockquote { margin: 1.1rem 0; padding: .2rem 1.1rem; border-left: 3px solid #cfc6b4; color: #55503f; background: rgba(230,225,213,.5); }
  table { border-collapse: collapse; margin: 1.2rem 0; font-size: .95rem; width: 100%; }
  th, td { border: 1px solid #d8d2c4; padding: .45rem .7rem; text-align: left; vertical-align: top; }
  th { background: #ece7da; font-weight: 600; }
  img { max-width: 100%; height: auto; margin: .8rem 0; }
  strong { font-weight: 650; }
  .katex-display { overflow-x: auto; overflow-y: hidden; padding: .2rem 0; }
  .katex-display > .katex { max-width: 100%; overflow-x: auto; overflow-y: hidden; }
  hr { border: none; border-top: 1px solid #e2ddd2; margin: 2rem 0; }
  .foot { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #e2ddd2; color: #8a8371; font-size: .85rem; }
</style>
</head>
<body>
<div class="page">
  <div class="toolbar"><a href="${indexRel}">← vitrine 全部预览</a></div>
  ${bodyHtml}
  <div class="foot">${title}</div>
</div>
</body>
</html>
`;
}

/* ---------- 构建 ---------- */

function collectMdFiles(dir) {
  const found = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      found.push(...collectMdFiles(full));
    } else if (entry.name.toLowerCase().endsWith(".md")) {
      found.push(full);
    }
  }
  return found;
}

function firstHeading(src) {
  for (const line of src.split("\n")) {
    const m = /^#\s+(.*)$/.exec(line.trim());
    if (m) return m[1].replace(/\$\$\$|\$+/g, "").trim();
  }
  return path.basename(src).replace(/\.md$/i, "");
}

function detectLang(src) {
  return /[\u4e00-\u9fff]/.test(src) ? "zh-Hans" : "en";
}

/** 只把真正会被页面引用的图片类文件镜像过去，脚本源文件不进入预览目录。 */
const IMAGE_EXTS = new Set([".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".apng", ".avif", ".ico"]);

function copyImagesDir(srcDir, outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  for (const entry of fs.readdirSync(srcDir, { withFileTypes: true })) {
    const src = path.join(srcDir, entry.name);
    if (entry.isDirectory()) {
      copyImagesDir(src, path.join(outDir, entry.name));
    } else if (IMAGE_EXTS.has(path.extname(entry.name).toLowerCase())) {
      fs.copyFileSync(src, path.join(outDir, entry.name));
    }
  }
}

async function main() {
  // 清空输出目录，保证每次生成的是同一份（与 build.py 对 _site 的做法一致）。
  fs.rmSync(OUT, { recursive: true, force: true });
  fs.mkdirSync(OUT, { recursive: true });

  // 复制离线 KaTeX 资源（CSS + 字体）。
  fs.cpSync(KATEX_SRC, path.join(OUT, "katex"), { recursive: true });

  const mdFiles = collectMdFiles(VITRINE).sort();
  const entries = [];
  const copiedImagesDirs = new Set();

  for (const srcPath of mdFiles) {
    const rel = path.relative(VITRINE, srcPath);
    // 镜像源目录结构：<name>.md -> <name>.html
    const relHtml = rel.replace(/\.md$/i, ".html");
    const outHtml = path.join(OUT, relHtml);
    fs.mkdirSync(path.dirname(outHtml), { recursive: true });

    // 把 md 旁边的 images/ 目录一并镜像过去，文档里 ./images/... 才不会 404。
    const mdDirImages = path.join(path.dirname(srcPath), "images");
    if (fs.existsSync(mdDirImages) && !copiedImagesDirs.has(mdDirImages)) {
      copiedImagesDirs.add(mdDirImages);
      const outImages = path.join(OUT, path.relative(VITRINE, mdDirImages));
      copyImagesDir(mdDirImages, outImages);
    }

    const src = fs.readFileSync(srcPath, "utf8");
    const mid = extractMath(src);
    let body = md.render(mid);
    for (const [key, html] of placeholders) {
      body = body.split(key).join(html);
    }
    placeholders.clear();

    const title = firstHeading(src);
    const lang = detectLang(src);
    fs.writeFileSync(outHtml, pageHtml(title, lang, body, outHtml), "utf8");
    entries.push({ rel, relHtml, outHtml, title, size: fs.statSync(outHtml).size });
    console.log(`  · ${rel}`);
  }

  // 索引页
  const rows = entries
    .map((e) => {
      const href = e.relHtml.split("/").map(encodeURIComponent).join("/");
      return `    <li><a href="${href}">${e.title}</a> <span class="meta">${e.rel}</span></li>`;
    })
    .join("\n");
  const indexHtml = `<!doctype html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>vitrine · Markdown 预览</title>
<style>
  body { margin: 0; background: #f6f4ee; color: #23201b; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", Georgia, serif; line-height: 1.7; }
  .page { max-width: 44rem; margin: 0 auto; padding: 3rem 1.5rem 6rem; }
  h1 { font-size: 1.5rem; border-bottom: 1px solid #e2ddd2; padding-bottom: .6rem; }
  ul { list-style: none; padding: 0; }
  li { padding: .55rem 0; border-bottom: 1px dashed #e2ddd2; }
  a { color: #6b5b45; text-decoration: none; font-size: 1.05rem; }
  a:hover { text-decoration: underline; }
  .meta { color: #9a927e; font-size: .82rem; margin-left: .6rem; }
  .note { color: #8a8371; font-size: .9rem; }
</style>
</head>
<body>
<div class="page">
  <h1>vitrine · Markdown 预览（${entries.length} 篇）</h1>
  <p class="note">公式已在生成时用本地 KaTeX 预渲染，可离线打开；图片沿用源目录的相对路径。</p>
  <ul>
${rows}
  </ul>
</div>
</body>
</html>
`;
  fs.writeFileSync(path.join(OUT, "index.html"), indexHtml, "utf8");

  const total = entries.reduce((a, e) => a + e.size, 0) + fs.statSync(path.join(OUT, "index.html")).size;
  console.log(`\n✓ 生成 ${entries.length} 篇预览：${path.relative(ROOT, OUT)}/（${(total / 1024).toFixed(0)} KB）`);
  console.log(`  打开 ${path.relative(ROOT, path.join(OUT, "index.html"))} 即可浏览全部。`);
}

main().catch((err) => {
  console.error(err);
  process.exitCode = 1;
});