/* 访客统计：读 stats.json，渲染 stats.html 的完整记录；页脚不再显示计数。
   统计本身由 GoatCounter 完成（无 cookie、不存 IP），这里只负责显示。 */

(() => {
  "use strict";

  // ↓↓↓ 唯一需要改的一行：goatcounter.com 的站点代号（不是网址）。
  // 留空 = 全站不统计，统计页会自动隐藏。
  const GOATCOUNTER_SITE = "shuyuew1991";
  const GOATCOUNTER_SCRIPT = "assets/goatcounter-count.js";
  const DATA_URL = "stats.json";
  const MAX_COUNTRIES = 14;
  const MAX_PAGES = 24;
  const SHANGHAI = "Asia/Shanghai";

  // 页面路径按文件名认，换域名、换仓库名都不用改这里。
  const PAGE_LABELS = {
    "": "index",
    "contact.html": "contact",
    "instrumentality.html": "instrumentality",
    "illusion.html": "illusion",
    "initiatives.html": "initiatives",
    "novel.html": "novel",
    "qixia.html": "qixia",
    "papers.html": "papers",
    "exegesis.html": "exegesis",
    "essay.html": "essay",
    "quiet-tool.html": "quiet-tool",
    "notes.html": "notes",
    "stats.html": "visits",
  };

  const numberFormat = new Intl.NumberFormat("zh-Hans");
  const fmt = (value) => numberFormat.format(Number(value) || 0);

  let regionNames = null;
  try {
    regionNames = new Intl.DisplayNames(["zh-Hans"], { type: "region" });
  } catch {
    regionNames = null;
  }

  function keyOf(path) {
    const clean = String(path || "").split(/[?#]/, 1)[0];
    if (clean.endsWith("/")) return "";
    const parts = clean.split("/").filter(Boolean);
    const last = parts.length ? parts[parts.length - 1] : "";
    return last === "index.html" ? "" : last;
  }

  // 页脚只显示仍在本站根目录的 .html，避免把奇怪路径做成链接。
  function hrefFor(key) {
    if (key === "") return "index.html";
    return /^[A-Za-z0-9._-]+\.html$/.test(key) ? key : null;
  }

  function canonicalPath() {
    const link = document.querySelector('link[rel="canonical"][href]');
    try {
      return new URL(link ? link.href : location.href, location.href).pathname;
    } catch {
      return location.pathname;
    }
  }

  function setAll(selector, text) {
    document.querySelectorAll(selector).forEach((node) => {
      node.textContent = text;
    });
  }

  function reveal(selector) {
    document.querySelectorAll(selector).forEach((node) => {
      node.hidden = false;
    });
  }

  function startTracker() {
    if (!/^[a-z0-9-]+$/i.test(GOATCOUNTER_SITE)) return;
    if (!/^https?:$/.test(location.protocol)) return;
    if (/^(localhost|127\.0\.0\.0|0\.0\.0\.0|\[::1\])$/i.test(location.hostname)) {
      return;
    }

    const script = document.createElement("script");
    script.async = true;
    script.src = GOATCOUNTER_SCRIPT;
    script.dataset.goatcounter = `https://${GOATCOUNTER_SITE}.goatcounter.com/count`;
    document.head.appendChild(script);
  }

  async function loadStats() {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch(DATA_URL, {
        cache: "no-cache",
        credentials: "omit",
        signal: controller.signal,
      });
      if (!response.ok) return null;
      return await response.json();
    } catch {
      return null;
    } finally {
      window.clearTimeout(timer);
    }
  }

  function shanghaiStamp(iso) {
    const date = new Date(iso);
    if (Number.isNaN(date.getTime())) return "";
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: SHANGHAI,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).formatToParts(date);
    const get = (type) => (parts.find((p) => p.type === type) || {}).value || "";
    return `${get("year")}.${get("month")}.${get("day")} ${get("hour")}:${get("minute")}`;
  }

  function dateStamp(iso) {
    return String(iso || "").slice(0, 10).replace(/-/g, ".");
  }

  function shortDay(iso) {
    return String(iso || "").slice(5, 10).replace("-", ".");
  }

  function countryName(item) {
    const code = String(item.code || "").toUpperCase();
    if (/^[A-Z]{2}$/.test(code) && regionNames) {
      try {
        const name = regionNames.of(code);
        if (name && name !== code) return name;
      } catch {
        // 有些代码不是合法地区，退回 API 给的名字。
      }
    }
    if (code === "UNKNOWN" || !code) return "未知";
    return item.name || code;
  }

  function buildPages(data) {
    const map = new Map();
    for (const page of data.pages || []) {
      const key = keyOf(page.path);
      const entry = map.get(key) || { key, views: 0, title: "" };
      entry.views += Number(page.views) || 0;
      if (!entry.title && page.title) entry.title = page.title;
      map.set(key, entry);
    }
    return [...map.values()].sort((a, b) => b.views - a.views);
  }

  function labelFor(entry) {
    if (Object.prototype.hasOwnProperty.call(PAGE_LABELS, entry.key)) {
      return PAGE_LABELS[entry.key];
    }
    const title = String(entry.title || "").split(/\s+[—–-]\s+/)[0].trim();
    return title || entry.key || "/";
  }

  function renderFooters(data) {
    const pages = buildPages(data);
    const byKey = new Map(pages.map((page) => [page.key, page]));
    const current = byKey.get(keyOf(canonicalPath()));

    setAll("[data-stats-total]", fmt(data.site && data.site.views));
    setAll("[data-stats-page]", fmt(current ? current.views : 0));
    // 新站还没有任何记录时先不露出来，免得页脚挂一个「0 visits」。
    if (data.site && data.site.views > 0) reveal("[data-stats]");
  }

  function showUnavailable(selector, text) {
    document.querySelectorAll(selector).forEach((node) => {
      node.textContent = text;
      node.hidden = false;
    });
    document.querySelectorAll("[data-stats-block]").forEach((node) => {
      node.hidden = true;
    });
  }

  function renderChart(data, root) {
    const daily = Array.isArray(data.daily) ? data.daily : [];
    const max = Math.max(1, ...daily.map((day) => Number(day.views) || 0));
    const summary = daily.reduce((sum, day) => sum + (Number(day.views) || 0), 0);

    root.replaceChildren();
    const lastDay = daily.length ? daily[daily.length - 1].day : "";
    for (const day of daily) {
      const views = Number(day.views) || 0;
      const bar = document.createElement("span");
      bar.className = "chart-bar";
      bar.style.setProperty(
        "--h",
        views ? `${Math.max(3, Math.round((views / max) * 100))}%` : "1.5%"
      );
      if (!views) bar.classList.add("is-zero");
      if (day.day === lastDay && views > 0) bar.classList.add("is-last");
      bar.title = `${shortDay(day.day)} · ${fmt(views)} 次`;
      bar.setAttribute("aria-hidden", "true");
      root.appendChild(bar);
    }

    const note = document.querySelector("[data-stats-chart-note]");
    if (note) note.textContent = `30 天合计 ${fmt(summary)} 次`;
    const range = document.querySelector("[data-stats-chart-range]");
    if (range && daily.length) {
      range.textContent = `${shortDay(daily[0].day)} — ${shortDay(
        daily[daily.length - 1].day
      )}`;
    }
    const alt = document.querySelector("[data-stats-chart-alt]");
    if (alt) {
      alt.textContent = `过去 ${daily.length} 天共 ${fmt(summary)} 次浏览，单日最高 ${fmt(
        max
      )} 次。`;
    }
  }

  function renderPages(data, tbody) {
    const pages = buildPages(data).slice(0, MAX_PAGES);
    const max = Math.max(1, ...pages.map((page) => page.views));
    tbody.replaceChildren();

    if (!pages.length) {
      const row = document.createElement("tr");
      const cell = document.createElement("td");
      cell.colSpan = 4;
      cell.className = "ledger-empty";
      cell.textContent = "还没有访客记录。";
      row.appendChild(cell);
      tbody.appendChild(row);
      return;
    }

    pages.forEach((page, index) => {
      const row = document.createElement("tr");

      const rank = document.createElement("td");
      rank.className = "rank";
      rank.textContent = String(index + 1).padStart(2, "0");

      const name = document.createElement("td");
      name.className = "page-name";
      const href = hrefFor(page.key);
      if (href) {
        const link = document.createElement("a");
        link.href = href;
        link.textContent = labelFor(page);
        name.appendChild(link);
      } else {
        name.textContent = labelFor(page);
      }

      const barCell = document.createElement("td");
      barCell.className = "bar-cell";
      const bar = document.createElement("span");
      bar.className = "bar";
      const fill = document.createElement("span");
      fill.style.width = `${Math.max(2, Math.round((page.views / max) * 100))}%`;
      bar.appendChild(fill);
      barCell.appendChild(bar);

      const count = document.createElement("td");
      count.className = "num";
      count.textContent = fmt(page.views);

      row.append(rank, name, barCell, count);
      tbody.appendChild(row);
    });
  }

  function renderCountries(data, list) {
    const countries = (data.countries || []).filter((item) => item.views > 0);
    const top = countries.slice(0, MAX_COUNTRIES);
    list.replaceChildren();

    if (!top.length) {
      const empty = document.createElement("li");
      empty.className = "place-empty";
      empty.textContent = "还没有地区记录。";
      list.appendChild(empty);
      return;
    }

    for (const item of top) {
      const row = document.createElement("li");
      row.className = "place-row";

      const code = document.createElement("span");
      code.className = "place-code";
      code.textContent = /^[A-Z]{2}$/.test(String(item.code || ""))
        ? item.code
        : "—";

      const name = document.createElement("span");
      name.className = "place-name";
      name.textContent = countryName(item);

      const leader = document.createElement("span");
      leader.className = "place-leader";
      leader.setAttribute("aria-hidden", "true");

      const count = document.createElement("span");
      count.className = "place-count";
      count.textContent = fmt(item.views);

      row.append(code, name, leader, count);
      list.appendChild(row);
    }

    if (countries.length > top.length) {
      const more = document.createElement("li");
      more.className = "place-more";
      more.textContent = `另有 ${countries.length - top.length} 个地区`;
      list.appendChild(more);
    }
  }

  function renderDashboard(data) {
    const dashboard = document.querySelector("[data-stats-dashboard]");
    if (!dashboard) return;

    setAll("[data-stats-total]", fmt(data.site && data.site.views));
    setAll("[data-stats-today]", fmt(data.site && data.site.today));
    setAll("[data-stats-countries]", fmt(data.site && data.site.countries));
    setAll("[data-stats-pages]", fmt(data.site && data.site.pages));

    const generated = shanghaiStamp(data.generated);
    if (generated) {
      setAll("[data-stats-updated]", `更新于 ${generated}（上海时间）`);
      const updated = document.querySelector("[data-stats-updated]");
      const generatedAt = new Date(data.generated).getTime();
      if (
        updated &&
        Number.isFinite(generatedAt) &&
        Date.now() - generatedAt > 48 * 60 * 60 * 1000
      ) {
        updated.classList.add("is-stale");
        updated.textContent += " · 数据可能延迟";
      }
    }

    const since = data.site && data.site.since;
    if (since) setAll("[data-stats-since]", `自 ${dateStamp(since)} 起`);

    if (!data.site || !data.site.views) {
      dashboard.setAttribute("aria-busy", "false");
      showUnavailable("[data-stats-empty]", "还没有访客记录。");
      return;
    }

    reveal("[data-stats-block]");

    const chart = document.querySelector("[data-stats-chart]");
    if (chart) renderChart(data, chart);

    const pagesBody = document.querySelector("[data-stats-pages-body]");
    if (pagesBody) renderPages(data, pagesBody);

    const places = document.querySelector("[data-stats-places]");
    if (places) renderCountries(data, places);

    dashboard.setAttribute("aria-busy", "false");
    dashboard.classList.add("is-ready");
  }

  function markUnavailable() {
    document.querySelectorAll("[data-stats-empty]").forEach((node) => {
      node.textContent = "访客统计暂时不可用。";
      node.hidden = false;
    });
    document.querySelectorAll("[data-stats-block]").forEach((node) => {
      node.hidden = true;
    });
    const dashboard = document.querySelector("[data-stats-dashboard]");
    if (dashboard) dashboard.setAttribute("aria-busy", "false");
  }

  async function run() {
    startTracker();
    // 页脚不再显示计数；只有统计页需要拿 stats.json。
    if (!document.querySelector("[data-stats], [data-stats-dashboard]")) return;
    const data = await loadStats();
    if (!data || data.enabled !== true) {
      if (document.querySelector("[data-stats-dashboard]")) markUnavailable();
      return;
    }
    renderFooters(data);
    renderDashboard(data);
  }

  run();
})();
