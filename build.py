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

import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "prototypes" / "v2" / "b-desk"
OUT = ROOT / "_site"

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
]

# 页面引用、但既不是页面也不是样式表的小文件。
EXTRAS = [
    "cover.js",
    "favicon.svg",
]

ASSETS_DIR = "assets"

# 万一百名单写错，这一层会拦住：稿件和脚本永远不进 _site。
FORBIDDEN = re.compile(
    r"\.(docx?|pdf|xlsx?|pages|key|epub|indd|rtf|py|pyc|doc)$", re.IGNORECASE
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

    # 每页引用的本地资源都得真实存在，否则线上就是 404。
    for page in PAGES:
        parser = Refs()
        parser.feed((SRC / page).read_text(encoding="utf-8"))
        for ref in sorted(parser.local):
            if ref in PAGES or ref in STYLES:
                continue
            if not (SRC / ref).is_file():
                problems.append(f"{page} 引用了不存在的 {ref}")

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
