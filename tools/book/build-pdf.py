#!/usr/bin/env python3
"""把 vitrine/exegesis_of_diffusion/ 的五章排成一份本地 PDF 草案。

这不是 CI 的一步：书稿目录被 .gitignore 排除，CI 上没有它。
用法：

    python3 tools/book/build-pdf.py

输出：dist/diffusion-exegesis-draft.pdf（*.pdf 已被 .gitignore 排除）。

依赖：
  - Node.js + tools/posts/node_modules（和注记共用 KaTeX/markdown-it）
  - 本机 Chrome（或用 CHROME 环境变量指定）
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "vitrine" / "exegesis_of_diffusion" / "DmExegesis"
TOOL = ROOT / "tools" / "posts" / "build.mjs"
TEMPLATE = ROOT / "tools" / "book" / "print-template.html"
DEPS = ROOT / "tools" / "posts" / "node_modules" / "katex"
ASSETS = ROOT / "prototypes" / "v2" / "b-desk" / "assets"
OUT = ROOT / "dist" / "diffusion-exegesis-draft.pdf"

CHAPTERS = [
    ("Chapter 0 - Preface.md", "Preface"),
    ("Chapter I  The High-Dimensional Structure of True Data.md", "Chapter I — The High-Dimensional Structure of True Data"),
    ("Chapter II  The ELBO Paradigm --- Proxy Objective for True Data Maximization.md", "Chapter II — The ELBO Paradigm"),
    ("Chapter III Dissecting the ELBO --- Diffusion Models as Distribution-Transitioned Dynamics..md", "Chapter III — Dissecting the ELBO"),
    ("Chapter IV Implementation on machine --- Training for Realistic Sampling..md", "Chapter IV — Implementation on Machine"),
]

SEPARATOR = re.compile(r"-{3,}")


def clean_chapter(path: Path) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and SEPARATOR.fullmatch(lines[0].strip()):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)

    subtitle = ""
    if lines and not SEPARATOR.fullmatch(lines[0].strip()):
        subtitle = lines.pop(0).strip().strip("_").strip()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and SEPARATOR.fullmatch(lines[0].strip()):
        lines.pop(0)
    while lines and not lines[0].strip():
        lines.pop(0)

    body = "\n".join(lines).rstrip() + "\n"
    body = body.replace("\u200b", "").replace("\u2061", "")
    return subtitle, body


def assemble(work: Path) -> Path:
    parts = []
    for filename, heading in CHAPTERS:
        subtitle, body = clean_chapter(SRC / filename)
        lead = f"*{subtitle}*\n\n" if subtitle else ""
        parts.append(f"## {heading}\n\n{lead}{body}")

    markdown = (
        "---\n"
        "title: A Preliminary Mathematical Exegesis of Diffusion Models\n"
        "heading: A Preliminary Mathematical Exegesis of Diffusion Models\n"
        "deck: Gaining Clarity From True Understanding\n"
        "date: 2026-11-23\n"
        "slug: book-full\n"
        "summary: A working draft on the mathematics of diffusion models.\n"
        "lang: en\n"
        "---\n\n"
        + "\n\n".join(parts)
    )
    source = work / "src"
    source.mkdir()
    (source / "full.md").write_text(markdown, encoding="utf-8")
    return source


def find_chrome() -> str:
    for candidate in [
        os.environ.get("CHROME"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
    ]:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError("找不到 Chrome。设置 CHROME=/path/to/chrome 后重试。")


def main() -> int:
    if not SRC.is_dir():
        print(f"缺书稿目录：{SRC}", file=sys.stderr)
        return 1
    if not DEPS.is_dir():
        print("缺 Node 依赖。先在 tools/posts 下运行：npm ci", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="book-pdf-") as temp:
        work = Path(temp)
        source = assemble(work)
        html_dir = work / "html"
        html_dir.mkdir()
        manifest = work / "manifest.json"

        command = [
            shutil.which("node") or "node",
            str(TOOL),
            "--src",
            str(source),
            "--out",
            str(html_dir),
            "--site-url",
            "https://shuyuew1991.github.io/personal-page/",
            "--template",
            str(TEMPLATE),
            "--manifest",
            str(manifest),
        ]
        print("排版：", flush=True)
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode != 0:
            print("排版失败", file=sys.stderr)
            return 1

        # 模板里用的本地资源：KaTeX CSS/字体 + 封面图。
        shutil.copytree(ASSETS / "katex", html_dir / "assets" / "katex")
        shutil.copy2(ASSETS / "plate-01.jpg", html_dir / "assets" / "plate-01.jpg")

        OUT.parent.mkdir(parents=True, exist_ok=True)
        chrome = find_chrome()
        print("打印：", OUT, flush=True)
        print_result = subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--no-first-run",
                f"--user-data-dir={work / 'chrome-profile'}",
                "--no-pdf-header-footer",
                "--run-all-compositor-stages-before-draw",
                "--virtual-time-budget=15000",
                f"--print-to-pdf={OUT}",
                (html_dir / "book-full.html").as_uri(),
            ],
            check=False,
        )
        if print_result.returncode != 0:
            print("Chrome 打印失败", file=sys.stderr)
            return 1

    print(f"✓ {OUT}  {OUT.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
