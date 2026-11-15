#!/usr/bin/env python3
"""把 GoatCounter 的汇总数据写成 _site/stats.json。

站点是纯静态的，浏览器里不能放 API token；所以由 CI 定期跑一次这个脚本，
把「总浏览 / 各页 / 国家地区 / 近 30 天」汇总成一个公开的小 JSON。
token 只放在 GitHub Actions secret 里，永远不进仓库。

用法：
    GOATCOUNTER_TOKEN=... python3 tools/stats_snapshot.py --out _site/stats.json

    # 本地用假数据试跑（不需要真 token）：
    python3 tools/stats_snapshot.py --site demo --token test \
        --api-base http://127.0.0.1:8765/api/v0 --out /tmp/stats.json

站点代号从 prototypes/v2/b-desk/stats.js 的 GOATCOUNTER_SITE 读，
所以浏览器脚本与 CI 永远用同一个值。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
STATS_JS = ROOT / "prototypes" / "v2" / "b-desk" / "stats.js"

TZ = ZoneInfo("Asia/Shanghai")
# 统计起点：站点上线远晚于这个日期，取一个足够早的值即可。
# 这个值只影响 API 查询范围，不会显示在页面上；页面上显示的是「第一条真实记录」。
SINCE = date(2026, 1, 1)
SCHEMA = 1
WINDOW_DAYS = 30


def now_iso() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def read_site_from_js() -> str:
    """从 stats.js 读站点代号，保持前后端同一个配置。"""
    try:
        text = STATS_JS.read_text(encoding="utf-8")
    except OSError:
        return ""
    found = re.search(r'GOATCOUNTER_SITE\s*=\s*["\']([^"\']*)["\']', text)
    return found.group(1).strip() if found else ""


def write_json(out: Path, data: dict[str, Any]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_disabled(out: Path, reason: str) -> None:
    """没配置时也写一个合法文件，前端据此安静地隐藏统计入口。"""
    write_json(
        out,
        {
            "schema": SCHEMA,
            "enabled": False,
            "reason": reason,
            "generated": now_iso(),
        },
    )


def api_get(
    base: str, token: str, endpoint: str, params: dict[str, Any], timeout: float
) -> dict[str, Any]:
    url = f"{base}{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "personal-page-stats-snapshot/1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read(400).decode("utf-8", "replace").strip()
        raise RuntimeError(
            f"GoatCounter API {error.code}：{endpoint} {detail or error.reason}"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"连不上 GoatCounter：{error.reason}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"GoatCounter 返回的不是 JSON：{endpoint}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"GoatCounter 返回了意外的数据结构：{endpoint}")
    return payload


def as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def build(
    site: str,
    token: str,
    api_base: str,
    timeout: float,
    since: date,
    today: date,
) -> dict[str, Any]:
    # end 传「明天」：GoatCounter 对 date-only 的 end 按上界处理，
    # 传今天有可能把今天的数据挡在区间外（不同版本的边界略有差异）。
    # 多给一天只是把还没有数据的明天算进来，today 的窗口仍然只到 today。
    span = {
        "start": since.isoformat(),
        "end": (today + timedelta(days=1)).isoformat(),
    }

    hits = api_get(
        api_base,
        token,
        "/stats/hits",
        {**span, "limit": 100},
        timeout,
    )
    totals = api_get(api_base, token, "/stats/total", span, timeout)
    locations = api_get(
        api_base,
        token,
        "/stats/locations",
        {**span, "limit": 100},
        timeout,
    )

    # ---- 各页浏览 -----------------------------------------------------
    pages: dict[str, dict[str, Any]] = {}
    for hit in hits.get("hits") or []:
        if hit.get("event"):
            continue
        path = str(hit.get("path") or "").split("?", 1)[0]
        if not path:
            continue
        entry = pages.setdefault(
            path, {"path": path, "title": str(hit.get("title") or ""), "views": 0}
        )
        entry["views"] += as_int(hit.get("count"))
        if not entry["title"] and hit.get("title"):
            entry["title"] = str(hit["title"])
    page_list = sorted(
        (p for p in pages.values() if p["views"] > 0),
        key=lambda p: (-p["views"], p["path"]),
    )[:100]

    # ---- 国家 / 地区 --------------------------------------------------
    countries: list[dict[str, Any]] = []
    for item in locations.get("stats") or []:
        views = as_int(item.get("count"))
        if views <= 0:
            continue
        code = str(item.get("id") or "").strip().upper()
        countries.append(
            {
                "code": code,
                "name": str(item.get("name") or code),
                "views": views,
            }
        )
    countries.sort(key=lambda c: (-c["views"], c["code"]))
    # 「Unknown」之类不是国家，算地区数时排除，但保留在列表里让人看到。
    region_count = sum(
        1 for c in countries if len(c["code"]) == 2 and c["code"].isalpha()
    )

    # ---- 每日曲线与总量 -----------------------------------------------
    by_day: dict[str, int] = defaultdict(int)
    for stat in totals.get("stats") or []:
        day = str(stat.get("day") or "")[:10]
        if not day:
            continue
        hourly = stat.get("hourly")
        if isinstance(hourly, list) and hourly:
            by_day[day] += sum(as_int(v) for v in hourly)
        else:
            by_day[day] += as_int(stat.get("daily"))

    views = as_int(totals.get("total")) - as_int(totals.get("total_events"))
    views = max(views, 0)
    if views == 0 and page_list:  # 防御：total 缺失时退回到各页合计
        views = sum(p["views"] for p in page_list)
    today_day = today.isoformat()
    today_views = by_day.get(today_day, 0)

    window: list[dict[str, Any]] = []
    for offset in range(WINDOW_DAYS - 1, -1, -1):
        day = (today - timedelta(days=offset)).isoformat()
        window.append({"day": day, "views": by_day.get(day, 0)})

    seen = [day for day, count in by_day.items() if count > 0]
    since = min(seen) if seen else None

    if hits.get("more"):
        print("! 路径超过 100 条，只统计了前 100 条", file=sys.stderr)

    return {
        "schema": SCHEMA,
        "enabled": True,
        "generated": now_iso(),
        "site": {
            "views": views,
            "today": today_views,
            "countries": region_count,
            "pages": len(page_list),
            "since": since,
        },
        "pages": page_list,
        "countries": countries[:60],
        "daily": window,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="生成公开的 GoatCounter 汇总 stats.json")
    parser.add_argument("--out", default="_site/stats.json", help="输出文件")
    parser.add_argument("--site", default="", help="GoatCounter 站点代号；默认从 stats.js 读")
    parser.add_argument(
        "--token",
        default=os.environ.get("GOATCOUNTER_TOKEN", ""),
        help="API token；默认取 GOATCOUNTER_TOKEN 环境变量",
    )
    parser.add_argument(
        "--api-base",
        default="",
        help="API 根地址；默认 https://<site>.goatcounter.com/api/v0（测试时可指向本地）",
    )
    parser.add_argument("--since", default=SINCE.isoformat(), help="统计起点（默认 2026-01-01）")
    parser.add_argument("--timeout", type=float, default=25.0, help="单次请求超时秒数")
    args = parser.parse_args(argv)

    out = Path(args.out)
    today = datetime.now(TZ).date()

    try:
        since = date.fromisoformat(args.since)
    except ValueError:
        print(f"✗ --since 不是日期：{args.since}", file=sys.stderr)
        return 2

    site = (args.site or read_site_from_js()).strip()
    if not site:
        write_disabled(out, "no-site")
        print("· stats.js 里还没填 GOATCOUNTER_SITE，统计入口保持隐藏")
        return 0
    if not re.fullmatch(r"[A-Za-z0-9-]+", site):
        print(f"✗ 站点代号只能包含字母、数字和连字符：{site}", file=sys.stderr)
        return 2

    token = args.token.strip()
    if not token:
        write_disabled(out, "no-token")
        print("· 没有 GOATCOUNTER_TOKEN，统计入口保持隐藏（站点仍在计数）")
        return 0

    api_base = (args.api_base or f"https://{site}.goatcounter.com/api/v0").rstrip("/")

    try:
        data = build(site, token, api_base, args.timeout, since, today)
    except RuntimeError as error:
        # 不要写半成品：直接失败，CI 就不会部署，线上继续用上一份数字。
        print(f"✗ {error}", file=sys.stderr)
        return 1

    write_json(out, data)
    print(
        f"✓ {out}：{data['site']['views']:,} 次浏览，"
        f"{data['site']['pages']} 个页面，{data['site']['countries']} 个地区"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
