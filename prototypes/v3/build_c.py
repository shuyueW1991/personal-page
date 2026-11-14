#!/usr/bin/env python3
import json, os, math, html

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'data.json'), encoding='utf-8'))
PAPERS = D['papers']
PATENTS = D['patents']
NOVEL = D['novel']
BOOK = D['booklet']
VIDEOS = D['videos']
SERIES = D['video_series']


def e(s):
    return html.escape(str(s), quote=True)


def fmt(n):
    return f'{n:,}'


def seconds(d):
    parts = [int(x) for x in d.split(':')]
    while len(parts) < 3:
        parts.insert(0, 0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def spine_height(words):
    lo, hi = 29000, 35500
    return round(32 + (words - lo) / (hi - lo) * 140)


def page_c():
    stages = NOVEL['stages'][1:]  # 二稿至七稿
    spines = ''
    for d in stages:
        h = spine_height(d['words'])
        spines += f'''<div class="c-spine" title="{e(d['stage'])} · {e(d['date'])} · {fmt(d['words'])} 字">
  <div class="c-spine-bar" style="--h:{h}px"></div>
  <div class="c-spine-labels"><span class="st">{e(d['stage'])}</span><span class="dt">{e(d['date'])}</span><span class="wd">{fmt(d['words'])}</span></div>
</div>'''

    quote_data = [
        ('？？？这转变太突然了', '读者 A · PDF 批注 · 12.05'),
        ('警察姐姐看上杰哥了？', '读者 C · PDF 批注 · 12.02'),
        ('作者的构思非常巧妙，文本、现实、梦境、自己、女友等视角不断切换交织', '读者 D · Word 修订 · 12 月'),
    ]
    quotes = ''.join(f'''<div class="c-quote">
  <blockquote>“{e(q)}”</blockquote>
  <cite>{e(c)}</cite>
</div>''' for q, c in quote_data)

    plates = ''.join(f'''<figure class="c-plate">
  <img src="../{e(p['src'])}" alt="{e(p['zh'])}：{e(p['note'])}">
  <figcaption><span class="cap-zh">图版 {e(p['no'])} · {e(p['zh'])}</span><span>{e(p['en'])}</span></figcaption>
</figure>''' for p in BOOK['plates'])

    chapters = ''.join(f'''<li>
  <span class="n">{e(c['no'])}</span>
  <span class="t" lang="en">{e(c['title'])}</span>
  <span class="w">{fmt(c['words'])}</span>
</li>''' for c in BOOK['chapters'])

    papers = ''
    for p in PAPERS:
        title = e(p['title'])
        if p['doi']:
            title = f'<a href="{e(p["doi"])}" target="_blank" rel="noopener"><span class="t">{title}</span></a>'
        else:
            title = f'<span class="t">{title}</span>'
        cites = f'<span class="cites">{p["cites"]}</span>' if p['cites'] else ''
        zh = ' lang="zh-Hans"' if p['zh'] else ''
        papers += f'<p class="c-paper"{zh}><span class="y">{p["year"]}</span>{title}{cites}</p>'

    # 35 ticks, chronological, heights on a log scale
    chron = list(reversed(VIDEOS))
    max_s = max(seconds(v['duration']) for v in chron)
    ticks = ''
    series_class = {'videomp3word': 's1', 'rurussian': 's2', 'Agents orchestrator': 's3'}
    for v in chron:
        s = seconds(v['duration'])
        h = round(7 + (math.log(s + 1) / math.log(max_s + 1)) * 72)
        ticks += f'<span class="c-tick {series_class.get(v["series"], "s1")}" style="--h:{h}px" title="{e(v["title"])} · {e(v["duration"])}"></span>'

    series_list = ''.join(f'<li><span class="n">{e(s["name"])}</span><span>{s["n"]} 条 · {e(s["span"])}</span></li>' for s in SERIES)

    return f'''<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>展柜 — 王舒悦</title>
  <meta name="description" content="展柜：一部小说的七稿与批注，一本英文小册的四幅图版，以及一些论文和影像。">
  <link rel="stylesheet" href="../assets/base.css">
  <link rel="stylesheet" href="c.css">
</head>
<body>
  <a class="skip" href="#main">跳到正文</a>
  <header class="page-top">
    <a class="back" href="../../v2/b-desk/index.html">← 文章</a>
    <span class="label">展柜 / Vitrine</span>
  </header>

  <figure class="c-hero">
    <img src="../assets/plate-03.jpg" alt="石刻拱门：一道向里延伸的通道，光在入口，暗在深处">
  </figure>
  <div class="c-hero-cap">
    <span>图版 III · 通道 / Passage</span>
    <span>石刻，1024 × 1024 · 2025</span>
  </div>

  <main id="main">
    <div class="c-title">
      <div class="c-title-grid">
        <div>
          <h1>展柜<span>VITRINE</span></h1>
          <p class="c-meta">稿本 · 图版 · 记录 / 2014—2026<br>45 份文件 · 7 稿 · 4 位读者 · 30 篇论文 · 8 项专利</p>
        </div>
        <p class="c-intro">这里放的不是文章，是文章之前和之后的东西：一部小说的七稿与四位读者的批注，一本写在比什凯克的英文小册，一些论文、专利和影像。它们不按栏目分，按做出来的时间摆在一起。</p>
      </div>
    </div>

    <section class="c-section" id="manuscript">
      <span class="c-label">稿本 / 2021</span>
      <div class="c-section-head">
        <h2>青年讲师<span>M·贺六浑 · 一个虚构的故事</span></h2>
        <span class="c-period">2021.11—12 · 七稿 · 未刊</span>
      </div>
      <div class="c-manuscript">
        <div>
          <p class="c-novel-synopsis">{e(NOVEL['synopsis'])}</p>
          <div class="c-excerpt">
            <span class="c-excerpt-label">第一节 · 节选</span>
            {''.join(f'<p>{e(line)}</p>' for line in NOVEL['excerpt'])}
          </div>
          <blockquote class="c-novel-quote">“{e(NOVEL['purpose_quote'])}”<cite>《写作目的与致谢》，2021.12.11</cite></blockquote>
          <p class="c-process-note">十一月，十三份分日手稿；十二月，二稿到七稿。四位读者在 PDF 和 Word 里留下了 302 处批注与修订。</p>
        </div>
        <div class="c-artifacts">
          <figure class="c-facsimile">
            <img src="../assets/facsimile-page.jpg" alt="第三稿的一页，上面有绿色高亮和红色页边批注">
            <figcaption>第三稿，2021.12.02，页 3。读者 C 在 PDF 上的批注与高亮。</figcaption>
          </figure>
          <figure class="c-note-figure">
            <img src="../assets/facsimile-note.jpg" alt="手稿页边的红色批注：警察姐姐看上杰哥了？">
            <figcaption>页边：<b>警察姐姐看上杰哥了？</b><br>读者 C，2021.12.02。</figcaption>
          </figure>
        </div>
      </div>

      <div class="c-versions">
        <div class="c-versions-head">
          <h3>版本 / 二稿至七稿</h3>
          <p>从 3.1 万写到 3.5 万，后两稿又删回去。</p>
        </div>
        <div class="c-spines">{spines}</div>
        <p class="c-titles">旧题：<b>《课题组谋杀嫌疑犯》</b><span class="arrow">→</span><b>《讲师陶吕之死》</b><span class="arrow">→</span><b>《课题组之死》</b><span class="arrow">→</span><b>《青年讲师》</b></p>
      </div>

      <div class="c-quotes">{quotes}</div>
    </section>

    <section class="c-section" id="plates">
      <span class="c-label">图版 / 2025</span>
      <div class="c-section-head">
        <h2>四幅图版<span>PLATES</span></h2>
        <span class="c-period">2025.06 · 比什凯克 · 石刻</span>
      </div>

      <div class="c-plate-grid">{plates}</div>

      <div class="c-booklet">
        <div>
          <h3>A Preliminary Mathematical Exegesis of Diffusion Models</h3>
          <p class="c-booklet-zh">扩散模型的一个初步数学阐释 · Gaining Clarity From True Understanding</p>
          <blockquote class="c-booklet-quote">“{e(BOOK['quote'])}”<cite>Preface</cite></blockquote>
          <ol class="c-chapters">{chapters}</ol>
        </div>
        <div>
          <div class="c-math">
            <span class="math-label">Chapter IV · 前向过程</span>
            d<i>x</i><sub>t</sub> = − ½ <i>β</i>(<i>t</i>) <i>x</i><sub>t</sub> d<i>t</i> + √<span class="sqrt"><i>β</i>(<i>t</i>)</span> d<i>W</i><sub>t</sub>
          </div>
          <p class="c-math-note">“{e(BOOK['quote2'])}”<br><span>— Preface</span></p>
        </div>
      </div>
    </section>

    <section class="c-section" id="record">
      <span class="c-label">记录 / 2014—2026</span>
      <div class="c-section-head">
        <h2>论文与影像<span>RECORD</span></h2>
        <span class="c-period">30 篇 · 8 项专利 · 35 条</span>
      </div>

      <div class="c-record">
        <div class="c-papers">{papers}</div>
        <aside class="c-record-side">
          <h3>影像 / 2026</h3>
          <div class="c-video-strip">{ticks}</div>
          <ul class="c-video-series">{series_list}</ul>
          <p class="c-patents-line">另有 8 项专利，2018—2022。</p>
          <p class="c-math-note">影像这一组可以整段撤掉。它属于产品记录，不属于写作。</p>
        </aside>
      </div>
    </section>
  </main>

  <footer class="page-foot">
    <span>© 2026 王舒悦 · 部分材料未公开</span>
    <div class="links"><a href="#">写信</a><a href="#">RSS</a></div>
  </footer>
</body>
</html>
'''


if __name__ == '__main__':
    open(os.path.join(HERE, 'c/index.html'), 'w', encoding='utf-8').write(page_c())
    print('wrote c/index.html')
