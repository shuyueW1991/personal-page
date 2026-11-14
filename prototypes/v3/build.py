#!/usr/bin/env python3
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))
PAPERS = D['papers']
PATENTS = D['patents']
NOVEL = D['novel']
BOOK = D['booklet']
VIDEOS = D['videos']
SERIES = D['video_series']

def e(s): return html.escape(str(s), quote=True)
def fmt(n): return f'{n:,}'
def venue_short(v):
    v = re.sub(r'\s*·\s*\d{4}.*$', '', v)
    return v.rstrip('.')

def paper_row(p, show_year=False):
    title = e(p['title'])
    if p['doi']:
        title = f'<a href="{e(p["doi"])}" target="_blank" rel="noopener">{title}</a>'
    short = p['short'] or '—'
    cites = f'{p["cites"]} 引' if p['cites'] else ''
    zh = ' lang="zh-Hans"' if p['zh'] else ''
    return f'''<article class="a-row is-paper">
  <div class="a-rail"><span class="a-short">{e(short)}</span></div>
  <div class="a-main">
    <h3{zh}>{title}</h3>
    <p class="a-sub">{e(venue_short(p['venue']))}</p>
  </div>
  <div class="a-side">{cites}</div>
</article>'''

def chapter_row(ch):
    return f'''<article class="a-row is-chapter">
  <div class="a-rail"><span class="a-stage">{e(ch['no'])}</span></div>
  <div class="a-main">
    <h3 lang="en">{e(ch['title'])}</h3>
    <p class="a-sub">{e(ch['zh'])} · {e(ch['summary'])}</p>
  </div>
  <div class="a-side">{fmt(ch['words'])} 词</div>
</article>'''

def draft_row(d):
    words = d['words'] if isinstance(d['words'], str) else f"{fmt(d['words'])} 字"
    note = f" · {e(d['note'])}" if d['note'] else ''
    change = f"{e(d['change'])} 改动" if d['change'] != '—' else ''
    sub = f"{change}{note}" if change else e(d['note'])
    return f'''<article class="a-row">
  <div class="a-rail"><span class="a-stage">{e(d['stage'])}</span>{e(d['date'])}</div>
  <div class="a-main">
    <h3>{e(d['title'])}</h3>
    <p class="a-sub">{sub}</p>
  </div>
  <div class="a-side">{e(words)}</div>
</article>'''

def reader_row(r):
    return f'''<article class="a-row is-reader">
  <div class="a-rail"><span class="a-stage">{e(r['label'])}</span>{e(r['medium'])}</div>
  <div class="a-main">
    <p class="a-quote">“{e(r['quote'])}”</p>
    <p class="a-sub">“{e(r['quote2'])}”</p>
  </div>
  <div class="a-side">{r['count']} 处 · {e(r['date'])}</div>
</article>'''

VIDEO_ABBR = {'videomp3word': 'V2W', 'rurussian': 'RU', 'Agents orchestrator': 'AGT'}

def video_row(s, samples):
    return f'''<article class="a-row is-video">
  <div class="a-rail"><span class="a-short">{e(VIDEO_ABBR.get(s['name'], s['name']))}</span>{e(s['span'])}</div>
  <div class="a-main">
    <h3>{e(s['name'])}</h3>
    <p class="a-sub">{e(s['note'])}</p>
  </div>
  <div class="a-side">{s['n']} 条</div>
</article>'''

def sublabel(text, note=''):
    return f'''<div class="a-sublabel"><span>{e(text)}</span><span>{e(note)}</span></div>'''

# ---------------------------------------------------------------- page A
def page_a():
    papers_by_year = {}
    for p in PAPERS:
        papers_by_year.setdefault(p['year'], []).append(p)
    years = [2026, 2025] + sorted([y for y in papers_by_year if y <= 2024], reverse=True) + [2021]
    seen = set(); order = []
    for y in years:
        if y not in seen:
            seen.add(y); order.append(y)

    def year_head(y, label):
        return f'''<div class="a-year"><span>{y}</span><span class="a-year-label">{label}</span></div>'''

    def year_body(y):
        out = []
        if y == 2026:
            out.append(year_head(y, '影像 / VIDEO'))
            for s in SERIES:
                ss = [v for v in VIDEOS if v['series'] == s['name']]
                out.append(video_row(s, ss))
        elif y == 2025:
            out.append(year_head(y, '图版 · 论文'))
            out.append(f'''<div class="a-group">
  <div class="a-group-head">
    <div class="a-group-kicker">图版 · 2025.06<br>比什凯克</div>
    <div>
      <h2 lang="en">{e(BOOK['title_en'])}</h2>
      <p class="a-group-deck">{e(BOOK['title_zh'])} — {e(BOOK['subtitle_en'])}。一本英文小册，四章，四幅图版。</p>
    </div>
    <div class="a-side">{fmt(BOOK['words'])} 词<br>四章</div>
  </div>
  {''.join(chapter_row(c) for c in BOOK['chapters'])}
</div>''')
            out.append(sublabel('论文', '2025'))
            for p in papers_by_year.get(2025, []):
                out.append(paper_row(p))
        elif y == 2021:
            out.append(year_head(y, '稿本 · 论文'))
            out.append(f'''<div class="a-group">
  <div class="a-group-head">
    <div class="a-group-kicker">稿本 · 七稿<br>2021.11–12</div>
    <div>
      <h2>《{e(NOVEL['title'])}》</h2>
      <p class="a-group-deck">一个虚构的故事。七稿，四十五份文件，四位读者。一个青年讲师在课题组组会前分发了一份材料。</p>
    </div>
    <div class="a-side">45 份文件<br>4 位读者</div>
  </div>
  {''.join(draft_row(d) for d in NOVEL['stages'])}
  {''.join(reader_row(r) for r in NOVEL['readers_data'])}
  <details class="a-materials">
    <summary><span>材料清单</span><span>45 份 · 未公开</span></summary>
    <div class="a-file-groups">
      {''.join(f'<div class="a-file-group"><h4>{e(g["name"])}<span>{g["n"]} 份</span></h4><p>{e(" · ".join(g["files"]))}</p></div>' for g in NOVEL['groups'])}
    </div>
  </details>
</div>''')
            out.append(sublabel('论文', '2021'))
            for p in papers_by_year.get(2021, []):
                out.append(paper_row(p))
        else:
            out.append(year_head(y, '论文 / PAPERS'))
            for p in papers_by_year.get(y, []):
                out.append(paper_row(p))
        return ''.join(out)

    body = ''.join(year_body(y) for y in order)

    patents = ''.join(f'''<tr>
      <td>{p['year']}</td>
      <td class="patent-name">{e(p['title'])}</td>
      <td>{e(p['no'])} · {e(p['status'])}</td>
    </tr>''' for p in PATENTS)

    return f'''<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>材料 — 王舒悦</title>
  <meta name="description" content="一部小说的七稿、一本英文小册、一些论文和影像。按时间排成一条材料账。">
  <link rel="stylesheet" href="../assets/base.css">
  <link rel="stylesheet" href="a.css">
</head>
<body>
  <a class="skip" href="#main">跳到正文</a>
  <header class="page-top">
    <a class="back" href="../../v2/b-desk/index.html">← 文章</a>
    <span class="label">材料 / Materials</span>
  </header>

  <main id="main" class="page-shell a-shell">
    <h1 class="sr-only">材料</h1>

    <p class="a-intro">不是文章。一部小说的七稿、一本没写完的小册、一些论文和影像。按时间从近到远放在同一条账上。左栏是稿次、刊物或频道；中间是标题；右栏是长度。不是目录，也不是简历。</p>
    <p class="a-meta">2014—2026 · 稿本、图版、论文、影像</p>

    <section class="a-ledger" aria-label="材料账">
      {body}
    </section>

    <p class="a-note">手稿、批注与背景材料暂不公开；这里只列目录。论文与影像的链接指向公开页面。</p>

    <section class="a-appendix" aria-label="专利">
      <h2>附录 · 专利 / 2018–2022</h2>
      <table class="a-patents">
        <thead><tr><th>年份</th><th>名称</th><th>专利号</th></tr></thead>
        <tbody>{patents}</tbody>
      </table>
    </section>
  </main>

  <footer class="page-foot">
    <span>© 2026 王舒悦</span>
    <div class="links"><a href="#">写信</a><a href="#">RSS</a></div>
  </footer>
</body>
</html>
'''

if __name__ == '__main__':
    open(os.path.join(HERE, 'a/index.html'), 'w', encoding='utf-8').write(page_a())
    print('wrote a/index.html')
