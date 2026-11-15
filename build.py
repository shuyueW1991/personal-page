#!/usr/bin/env python3
"""把 prototypes/v2/b-desk 里真正上线的页面装配成 _site/。

白名单复制：站点里永远不出现稿件、生成脚本、设计截图。
本地的 `python3 build.py` 和 GitHub Actions 走的是同一个函数，
所以"我本机看到的"和"线上看到的"是同一份东西。

用法：
    python3 build.py            # 生成 _site/
    python3 build.py --check    # 只检查，不写文件（构建流程里也用它）
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "prototypes" / "v2" / "b-desk"
OUT = ROOT / "_site"

# 站点公开地址。换域名或改仓库名时只改这一行：
# canonical 标签、sitemap.xml、robots.txt 都从这里推出来。
SITE_URL = "https://shuyuew1991.github.io/personal-page/"

# 上线页面。新增页面时只改这里，别把草稿页一起带上去。
PAGES = [
    "index.html",
    "contact.html",
    "instrumentality.html",
    "illusion.html",
    "initiatives.html",
    "novel.html",
    "qixia.html",
    "papers.html",
    "exegesis.html",
    "essay.html",
    "quiet-tool.html",
    "notes.html",
    "stats.html",
]

STYLES = [
    "cover.css",
    "index.css",
    "contact.css",
    "initiatives.css",
    "personal.css",
    "novel.css",
    "qixia.css",
    "papers.css",
    "section.css",
    "exegesis.css",
    "style.css",
    "notes.css",
    "stats.css",
]

# 页面引用、但既不是页面也不是样式表的小文件。
EXTRAS = [
    "cover.js",
    "stats.js",
    "favicon.svg",
    # Google Search Console 的所有权验证文件：文件名和内容都不能改。
    "googlefa66aa447ffb8c98.html",
]

ASSETS_DIR = "assets"

# 统计脚本靠它把访问发给 GoatCounter；它随 assets/ 一起复制，但漏了不会报错，
# 所以单独点名检查。
REQUIRED_ASSETS = [
    "assets/goatcounter-count.js",
]

# 统计页是给访客看的，不放进 sitemap，也不让搜索引擎收录。
NOINDEX = {"stats.html"}

# 统计快照由 tools/stats_snapshot.py 在 CI 里生成；本地没有时用这个占位，
# 前端读到 enabled: false 就把统计入口安静地藏起来。
STATS_PLACEHOLDER = {
    "schema": 1,
    "enabled": False,
    "reason": "no-snapshot",
    "generated": None,
}

# 万一百名单写错，这一层会拦住：稿件和脚本永远不进 _site。
FORBIDDEN = re.compile(
    r"\.(docx?|pdf|xlsx?|pages|key|epub|indd|rtf|py|pyc|doc)$", re.IGNORECASE
)

# 每页都应声明同一套地址，否则同一个页面会被收录成好几份。
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"')


def page_url(name: str) -> str:
    """首页统一用目录地址，避免 / 与 /index.html 各被收录一次。"""
    return SITE_URL if name == "index.html" else f"{SITE_URL}{name}"


def write_generated(out: Path) -> None:
    """sitemap.xml 和 robots.txt 都由 PAGES / SITE_URL 现算，加页面不用手工维护。"""
    urls = "".join(
        f"  <url><loc>{page_url(name)}</loc></url>\n"
        for name in PAGES
        if name not in NOINDEX
    )
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n",
        encoding="utf-8",
    )
    (out / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {SITE_URL}sitemap.xml\n",
        encoding="utf-8",
    )
    # CI 的 stats_snapshot.py 会覆盖这一份；本地预览则用它把统计入口藏起来。
    (out / "stats.json").write_text(
        json.dumps(STATS_PLACEHOLDER, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class Refs(HTMLParser):
    """收集页面里所有本地 href / src。"""

    def __init__(self) -> None:
        super().__init__()
        self.local: set[str] = set()

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name not in ("href", "src") or not value:
                continue
            if value.startswith(("#", "http://", "https://", "mailto:", "//")):
                continue
            self.local.add(value.split("#", 1)[0].split("?", 1)[0])


def build(check_only: bool = False) -> int:
    problems: list[str] = []

    for name in PAGES + STYLES:
        if not (SRC / name).is_file():
            problems.append(f"缺文件：{name}")

    for name in EXTRAS:
        if not (SRC / name).is_file():
            problems.append(f"缺文件：{name}")

    for name in REQUIRED_ASSETS:
        if not (SRC / name).is_file():
            problems.append(f"缺文件：{name}")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    if not check_only:
        if OUT.exists():
            shutil.rmtree(OUT)
        OUT.mkdir(parents=True)

        for name in PAGES + STYLES + EXTRAS:
            shutil.copy2(SRC / name, OUT / name)

        shutil.copytree(SRC / ASSETS_DIR, OUT / ASSETS_DIR)
        (OUT / ".nojekyll").write_text("", encoding="utf-8")
        write_generated(OUT)

    # 每页引用的本地资源都得真实存在，否则线上就是 404。
    for page in PAGES:
        text = (SRC / page).read_text(encoding="utf-8")
        parser = Refs()
        parser.feed(text)
        for ref in sorted(parser.local):
            if ref in PAGES or ref in STYLES:
                continue
            if not (SRC / ref).is_file():
                problems.append(f"{page} 引用了不存在的 {ref}")

        found = CANONICAL.search(text)
        if not found:
            problems.append(f"{page} 缺 canonical")
        elif found.group(1) != page_url(page):
            problems.append(f"{page} 的 canonical 指向 {found.group(1)}，应为 {page_url(page)}")

        # 统计要覆盖每一页：新加页面时忘了挂脚本，这里会拦下来。
        if "stats.css" not in text:
            problems.append(f"{page} 没有引用 stats.css")
        if "stats.js" not in text:
            problems.append(f"{page} 没有引用 stats.js")
        if "data-stats" not in text:
            problems.append(f"{page} 没有统计挂载点（data-stats）")

        if page in NOINDEX and 'name="robots"' not in text:
            problems.append(f"{page} 在 NOINDEX 里，但没写 robots 标签")

    # 兜底：生成结果里不允许出现稿件或脚本。
    if not check_only and OUT.exists():
        for path in OUT.rglob("*"):
            if path.is_file() and FORBIDDEN.search(path.name):
                problems.append(f"_site 里出现了不该上线的文件：{path.relative_to(OUT)}")

    if problems:
        print("\n".join(f"✗ {p}" for p in problems), file=sys.stderr)
        return 1

    if not check_only:
        total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
        count = sum(1 for p in OUT.rglob("*") if p.is_file())
        print(f"✓ _site/  {count} 个文件，{total / 1024:.0f} KB")
        for name in PAGES:
            print(f"  · {name}")
    else:
        print("✓ 检查通过")

    return 0


if __name__ == "__main__":
    raise SystemExit(build(check_only="--check" in sys.argv))
