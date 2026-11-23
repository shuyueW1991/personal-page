#!/usr/bin/env python3
"""把 prototypes/v2/b-desk 里真正上线的页面装配成 _site/。

白名单复制：站点里不会出现完整书稿、生成脚本、设计截图；公开样章见 tools/book/sample.md。
本地的 `python3 build.py` 和 GitHub Actions 走的是同一个函数，
所以"我本机看到的"和"线上看到的"是同一份东西。

注记页不手工维护：`vitrine/instrumentality/` 下的每篇 Markdown 都由
`tools/posts/build.mjs` 在构建时排成整页（KaTeX 预渲染、图片进图版桌面），
`instrumentality.html` 里的 notes 列表也由同一份清单生成。

用法：
    python3 build.py            # 生成 _site/
    python3 build.py --check    # 只检查，不写 _site/（在临时目录里完整构建一遍）
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "prototypes" / "v2" / "b-desk"
OUT = ROOT / "_site"

# 站点公开地址。换域名或改仓库名时只改这一行：
# canonical 标签、sitemap.xml、robots.txt 都从这里推出来。
SITE_URL = "https://shuyuew1991.github.io/personal-page/"

# 手工维护的页面。注记页不在这里：它们由 vitrine/instrumentality/ 自动生成。
# 新增静态页面时只改这里，别把草稿页一起带上去。
STATIC_PAGES = [
    "index.html",
    "contact.html",
    "instrumentality.html",
    "inbox.html",
    "illusion.html",
    "initiatives.html",
    "novel.html",
    "qixia.html",
    "papers.html",
    "exegesis.html",
    "essay.html",
    "quiet-tool.html",
    "notes.html",
    "thanks.html",
    "stats.html",
]

STYLES = [
    "cover.css",
    "index.css",
    "contact.css",
    "initiatives.css",
    "instrumentality.css",
    "inbox.css",
    "personal.css",
    "novel.css",
    "qixia.css",
    "papers.css",
    "section.css",
    "exegesis.css",
    "book-sample.css",
    "style.css",
    "notes.css",
    "post.css",
    "comments.css",
    "stats.css",
]

# 页面引用、但既不是页面也不是样式表的小文件。
EXTRAS = [
    "cover.js",
    "stats.js",
    "comments.js",
    "post.js",
    "inbox.js",
    "payments.js",
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

# 统计页和待看评论页不放进 sitemap，也不让搜索引擎收录。
NOINDEX = {"stats.html", "inbox.html", "thanks.html"}

# 注记源目录与生成器。构建时由 build.py 调用 Node 生成整页。
POSTS_DIR = ROOT / "vitrine" / "instrumentality"
POSTS_TOOL = ROOT / "tools" / "posts" / "build.mjs"
POSTS_DEPS = ROOT / "tools" / "posts" / "node_modules" / "katex"

# 书的免费样章（序言 + 第一章）。源文件在 tools/book/sample.md，
# 和注记共用同一个 KaTeX 生成器，只是换一套 template。
BOOK_DIR = ROOT / "tools" / "book"
BOOK_TEMPLATE = BOOK_DIR / "sample-template.html"

# instrumentality.html 里由生成器填充的两段内容。
NOTES_COUNT_START = "<!-- notes:count:start -->"
NOTES_COUNT_END = "<!-- notes:count:end -->"
NOTES_LIST_START = "<!-- notes:list:start -->"
NOTES_LIST_END = "<!-- notes:list:end -->"

# 统计快照由 tools/stats_snapshot.py 在 CI 里生成；本地没有时用这个占位，
# 前端读到 enabled: false 就把统计入口安静地藏起来。
STATS_PLACEHOLDER = {
    "schema": 1,
    "enabled": False,
    "reason": "no-snapshot",
    "generated": None,
}

# 万一百名单写错，这一层会拦住：完整书稿和脚本永远不进 _site（公开样章是白名单内容）。
FORBIDDEN = re.compile(
    r"\.(docx?|pdf|xlsx?|pages|key|epub|indd|rtf|py|pyc|doc)$", re.IGNORECASE
)

# 每页都应声明同一套地址，否则同一个页面会被收录成好几份。
CANONICAL = re.compile(r'<link\s+rel="canonical"\s+href="([^"]+)"')


def page_url(name: str) -> str:
    """首页统一用目录地址，避免 / 与 /index.html 各被收录一次。"""
    return SITE_URL if name == "index.html" else f"{SITE_URL}{name}"


def write_generated(out: Path, pages: list[str]) -> None:
    """sitemap.xml 和 robots.txt 都由页面清单 / SITE_URL 现算，加页面不用手工维护。"""
    urls = "".join(
        f"  <url><loc>{page_url(name)}</loc></url>\n"
        for name in pages
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


def run_post_builder(out: Path, manifest: Path) -> list[dict]:
    """调用 tools/posts/build.mjs，返回按日期升序的注记清单。"""
    node = shutil.which("node")
    if not node:
        raise RuntimeError("找不到 node。注记生成需要 Node.js 18+，请先安装 Node。")
    if not POSTS_DEPS.is_dir():
        raise RuntimeError("缺少注记生成依赖。先在 tools/posts 下运行：npm ci")

    command = [
        node,
        str(POSTS_TOOL),
        "--src",
        str(POSTS_DIR),
        "--out",
        str(out),
        "--site-url",
        SITE_URL,
        "--manifest",
        str(manifest),
    ]
    print("注记：", flush=True)
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError("注记生成失败（见上面的报错），本次构建中止")
    return json.loads(manifest.read_text(encoding="utf-8")).get("posts", [])


def run_book_builder(out: Path, manifest: Path) -> list[dict]:
    """调用同一个 KaTeX 生成器，把 tools/book/ 下的样章排成整页。"""
    node = shutil.which("node")
    if not node:
        raise RuntimeError("找不到 node。样章生成需要 Node.js 18+，请先安装 Node。")
    if not POSTS_DEPS.is_dir():
        raise RuntimeError("缺少样章生成依赖。先在 tools/posts 下运行：npm ci")
    if not BOOK_TEMPLATE.is_file():
        raise RuntimeError(f"缺少样章模板：{BOOK_TEMPLATE.relative_to(ROOT)}")

    command = [
        node,
        str(POSTS_TOOL),
        "--src",
        str(BOOK_DIR),
        "--out",
        str(out),
        "--site-url",
        SITE_URL,
        "--template",
        str(BOOK_TEMPLATE),
        "--manifest",
        str(manifest),
    ]
    print("样章：", flush=True)
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        raise RuntimeError("样章生成失败（见上面的报错），本次构建中止")
    return json.loads(manifest.read_text(encoding="utf-8")).get("posts", [])


def replace_region(text: str, start: str, end: str, replacement: str, label: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise RuntimeError(f"instrumentality.html 缺少 {label} 标记：{start} … {end}")
    return pattern.sub(lambda _: f"{start}{replacement}{end}", text, count=1)


def notes_list_html(posts: list[dict]) -> str:
    """按年份倒序、年内按日期倒序生成 notes 列表；posts 来自生成器，日期升序。"""
    grouped: dict[str, list[dict]] = {}
    for post in reversed(posts):
        grouped.setdefault(post["date"][:4], []).append(post)

    sections = []
    for year in sorted(grouped, reverse=True):
        items = grouped[year]
        rows = []
        for post in items:
            month, day = post["date"][5:7], post["date"][8:10]
            lang_attr = ' lang="en"' if post.get("lang") == "en" else ""
            title = html.escape(post.get("list_title") or post["title"])
            rows.append(
                "            <li>\n"
                f'              <a class="note-entry" href="{html.escape(post["slug"])}.html">\n'
                f'                <time datetime="{post["date"]}">{month}.{day}</time>\n'
                f'                <span class="note-title"{lang_attr}>{title}</span>\n'
                '                <span class="note-arrow" aria-hidden="true">↗</span>\n'
                "              </a>\n"
                "            </li>"
            )
        sections.append(
            f'        <section class="note-year" aria-label="{year} 年的注记">\n'
            '          <header class="note-year-head">\n'
            f"            <span>{year}</span>\n"
            f"            <span>{len(items):02d}</span>\n"
            "          </header>\n"
            '          <ul class="note-list">\n'
            f"{chr(10).join(rows)}\n"
            "          </ul>\n"
            "        </section>"
        )

    return "\n".join(sections)


def inject_notes(page: Path, posts: list[dict]) -> None:
    """把 notes 数量和列表填进 instrumentality.html 的标记之间。"""
    text = page.read_text(encoding="utf-8")
    text = replace_region(
        text,
        NOTES_COUNT_START,
        NOTES_COUNT_END,
        f"{len(posts)} 篇",
        "notes 数量",
    )
    text = replace_region(
        text,
        NOTES_LIST_START,
        NOTES_LIST_END,
        "\n" + notes_list_html(posts) + "\n        ",
        "notes 列表",
    )
    page.write_text(text, encoding="utf-8")


def write_post_titles(out: Path, posts: list[dict]) -> None:
    """inbox 用它把 [margin] issue 的页码显示成标题；新帖子不用手改 inbox.js。"""
    titles = {
        f"{post['slug']}.html": post.get("list_title") or post["title"] for post in posts
    }
    (out / "post-titles.js").write_text(
        "window.POST_TITLES = "
        + json.dumps(titles, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )


def validate_site(out: Path, pages: list[str]) -> list[str]:
    problems: list[str] = []

    for page in pages:
        path = out / page
        if not path.is_file():
            problems.append(f"缺页面：{page}")
            continue
        text = path.read_text(encoding="utf-8")

        parser = Refs()
        parser.feed(text)
        for ref in sorted(parser.local):
            if ref in pages or ref in STYLES:
                continue
            if not (out / ref).is_file():
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

        # 挂了评论的页面必须带上评论区自己的样式和脚本，否则按钮点了没反应。
        if "data-comments" in text:
            if "comments.css" not in text:
                problems.append(f"{page} 有评论挂载点，但没引用 comments.css")
            if "comments.js" not in text:
                problems.append(f"{page} 有评论挂载点，但没引用 comments.js")

        # 注记页的阅读桌、图版和页边批注都靠 post.js / post.css。
        if 'class="post-page"' in text:
            if "post.css" not in text:
                problems.append(f"{page} 是注记页，但没引用 post.css")
            if "post.js" not in text:
                problems.append(f"{page} 是注记页，但没引用 post.js")

        if page in NOINDEX and 'name="robots"' not in text:
            problems.append(f"{page} 在 NOINDEX 里，但没写 robots 标签")

    return problems


def build_into(out: Path, check_only: bool) -> int:
    for name in STATIC_PAGES + STYLES + EXTRAS:
        shutil.copy2(SRC / name, out / name)
    shutil.copytree(SRC / ASSETS_DIR, out / ASSETS_DIR)

    with tempfile.TemporaryDirectory(prefix="personal-page-posts-") as manifest_dir:
        try:
            posts = run_post_builder(out, Path(manifest_dir) / "posts.json")
            book_posts = run_book_builder(out, Path(manifest_dir) / "book.json")
            inject_notes(out / "instrumentality.html", posts)
            write_post_titles(out, posts)
        except RuntimeError as error:
            print(f"✗ {error}", file=sys.stderr)
            return 1

    pages = (
        STATIC_PAGES
        + [f"{post['slug']}.html" for post in posts]
        + [f"{post['slug']}.html" for post in book_posts]
    )
    write_generated(out, pages)

    problems = validate_site(out, pages)

    # 兜底：生成结果里不允许出现完整书稿或脚本。
    for path in out.rglob("*"):
        if path.is_file() and FORBIDDEN.search(path.name):
            problems.append(f"_site 里出现了不该上线的文件：{path.relative_to(out)}")

    if problems:
        print("\n".join(f"✗ {p}" for p in problems), file=sys.stderr)
        return 1

    if check_only:
        print(f"✓ 检查通过（{len(posts)} 篇注记，{len(book_posts)} 篇样章）")
        return 0

    total = sum(p.stat().st_size for p in out.rglob("*") if p.is_file())
    count = sum(1 for p in out.rglob("*") if p.is_file())
    print(f"✓ _site/  {count} 个文件，{total / 1024:.0f} KB")
    for name in pages:
        print(f"  · {name}")
    print(f"  · 注记 {len(posts)} 篇由 vitrine/instrumentality/ 生成")
    print(f"  · 样章 {len(book_posts)} 篇由 tools/book/ 生成")
    return 0


def build(check_only: bool = False) -> int:
    problems: list[str] = []

    for name in STATIC_PAGES + STYLES:
        if not (SRC / name).is_file():
            problems.append(f"缺文件：{name}")

    for name in EXTRAS:
        if not (SRC / name).is_file():
            problems.append(f"缺文件：{name}")

    for name in REQUIRED_ASSETS:
        if not (SRC / name).is_file():
            problems.append(f"缺文件：{name}")

    if not POSTS_DIR.is_dir():
        problems.append(f"缺注记目录：{POSTS_DIR.relative_to(ROOT)}")
    if not POSTS_TOOL.is_file():
        problems.append(f"缺注记生成器：{POSTS_TOOL.relative_to(ROOT)}")
    if not BOOK_DIR.is_dir():
        problems.append(f"缺样章目录：{BOOK_DIR.relative_to(ROOT)}")
    if not BOOK_TEMPLATE.is_file():
        problems.append(f"缺样章模板：{BOOK_TEMPLATE.relative_to(ROOT)}")
    if not (BOOK_DIR / "sample.md").is_file():
        problems.append("缺样章源文件：tools/book/sample.md")
    if shutil.which("node") is None:
        problems.append("找不到 node：注记生成需要 Node.js 18+")
    elif not POSTS_DEPS.is_dir():
        problems.append("缺注记生成依赖：先在 tools/posts 下运行 npm ci")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1

    if check_only:
        with tempfile.TemporaryDirectory(prefix="personal-page-check-") as temp_dir:
            return build_into(Path(temp_dir), check_only=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    return build_into(OUT, check_only=False)


if __name__ == "__main__":
    raise SystemExit(build(check_only="--check" in sys.argv))
