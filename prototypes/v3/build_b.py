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


def e(s):
    return html.escape(str(s), quote=True)


def fmt(n):
    return f'{n:,}'


def paper_card(p):
    title = e(p['title'])
    if p['doi']:
        title = f'<a href="{e(p["doi"])}" target="_blank" rel="noopener">{title}</a>'
    cites = f'{p["cites"]} 引' if p['cites'] else '—'
    zh = ' lang="zh-Hans"' if p['zh'] else ''
    return f'''<article class="paper">
  <p class="paper-title"{zh}>{title}</p>
  <p class="paper-meta"><span>{e(p['short'])} · {p['year']}</span><span class="paper-cites">{cites}</span></p>
</article>'''


def patent_table():
    rows = ''.join(
        f"<tr><td>{p['year']}</td><td>{e(p['title'])}</td><td>{e(p['no'])} · {e(p['status'])}</td></tr>"
        for p in PATENTS
    )
    return f'''<table class="patents">
  <thead><tr><th>年份</th><th>名称</th><th>专利号</th></tr></thead>
  <tbody>{rows}</tbody>
</table>'''


def short_video_title(t):
    t = re.sub(r'\s*#.*$', '', t)
    t = t.replace('…', '').strip()
    return t[:78] + ('…' if len(t) > 78 else '')


def video_samples(name, n=3):
    rows = [v for v in VIDEOS if v['series'] == name][:n]
    return ''.join(
        f'<li><a href="https://youtu.be/{e(v["id"])}" target="_blank" rel="noopener">{e(short_video_title(v["title"]))}</a> · {e(v["duration"])}</li>'
        for v in rows
    )


def page_b():
    version_rows = ''
    for d in NOVEL['stages']:
        words = d['words'] if isinstance(d['words'], str) else fmt(d['words'])
        note = f'<span class="v-note">{e(d["note"])}</span>' if d['note'] else ''
        change = d['change'] if d['change'] != '—' else '—'
        version_rows += f'''<tr>
  <td class="v-stage">{e(d['stage'])}</td>
  <td class="v-date">{e(d['date'])}</td>
  <td class="v-title">{e(d['title'])}{note}</td>
  <td class="v-words">{e(words)}</td>
  <td class="v-change">{e(change)}</td>
</tr>'''

    readers = ''.join(f'''<li class="reader">
  <div class="reader-label">{e(r['label'])}<span>{e(r['medium'])}</span></div>
  <div>
    <p class="reader-quote">“{e(r['quote'])}”</p>
    <p class="reader-quote">“{e(r['quote2'])}”</p>
    <p class="reader-meta">{r['count']} 处 · {e(r['date'])}</p>
  </div>
</li>''' for r in NOVEL['readers_data'])

    material_groups = ''.join(f'''<div class="mat-group">
  <div class="mat-head"><h4>{e(g['name'])}</h4><span>{g['n']} 份</span></div>
  <p>{e(g['note'])}</p>
  <p class="mat-files">{e(' · '.join(g['files']))}</p>
</div>''' for g in NOVEL['groups'])

    chapters = ''.join(f'''<li class="chapter">
  <span class="ch-no">{e(c['no'])}</span>
  <div>
    <p class="ch-title" lang="en">{e(c['title'])}</p>
    <span class="ch-zh">{e(c['zh'])}</span>
    <p class="ch-summary">{e(c['summary'])}</p>
  </div>
  <span class="ch-words">{fmt(c['words'])} 词</span>
</li>''' for c in BOOK['chapters'])

    papers = ''.join(paper_card(p) for p in PAPERS)

    series_rows = ''
    for s in SERIES:
        series_rows += f'''<li class="video-row">
  <div class="video-name">{e(s['name'])}<span>{s['n']} 条 · {e(s['span'])}</span></div>
  <div>
    <p class="video-note">{e(s['note'])}</p>
    <ul class="video-samples">{video_samples(s['name'], 3)}</ul>
  </div>
</li>'''

    return f'''<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>工作台 — 王舒悦</title>
  <meta name="description" content="四件东西：一部小说，一本英文小册，一批论文，一些影像。">
  <link rel="stylesheet" href="../assets/base.css">
  <link rel="stylesheet" href="b.css">
</head>
<body>
  <a class="skip" href="#main">跳到正文</a>
  <header class="page-top">
    <a class="back" href="../../v2/b-desk/index.html">← 文章</a>
    <span class="label">工作台 / Workbench</span>
  </header>

  <main id="main" class="page-shell b-shell">
    <h1 class="sr-only">工作台</h1>

    <p class="b-intro">四件东西。一部小说，一本小册，一批论文，一些影像。有的完成，有的还在改。<br>不是作品集，是一张桌子；抽屉拉开，里面是稿子、图版和记录。</p>

    <nav class="b-index" aria-label="抽屉">
      <a href="#novel">稿本<span>青年讲师 · 2021</span></a>
      <a href="#booklet">图版<span>扩散模型 · 2025</span></a>
      <a href="#record">记录<span>论文与专利</span></a>
      <a href="#video">影像<span>2026</span></a>
    </nav>

    <section class="drawer" id="novel">
      <aside class="drawer-rail">
        <span class="drawer-kicker">稿本</span>
        <dl>
          <dt>类型</dt><dd>小说</dd>
          <dt>时间</dt><dd>2021.11–12</dd>
          <dt>状态</dt><dd>未刊</dd>
          <dt>篇幅</dt><dd>约 3.5 万字</dd>
          <dt>材料</dt><dd>45 份</dd>
          <dt>读者</dt><dd>4 位</dd>
        </dl>
      </aside>
      <div class="drawer-main">
        <h2>《{e(NOVEL['title'])}》<span class="pen">{e(NOVEL['pen'])} · 一个虚构的故事</span></h2>
        <p class="drawer-deck">七稿，四十五份文件，四位读者。一个虚构的故事。</p>
        <p class="drawer-lede">{e(NOVEL['synopsis'])}</p>
        <p class="drawer-lede">写的是高校里的伦理，也是一个人怎样被一个共同体慢慢推到墙角。作者在《写作目的与致谢》里说，这不是把责任推给某个人，而是想把责任推给那个 system。</p>
        <blockquote class="pull">“{e(NOVEL['purpose_quote'])}”<cite>《写作目的与致谢》，2021.12.11</cite></blockquote>
        <div class="excerpt">
          <span class="excerpt-label">第一节 · 节选</span>
          {''.join(f'<p>{e(line)}</p>' for line in NOVEL['excerpt'])}
        </div>

        <div class="section-label"><span>版本 / 七稿</span><span class="count">二稿至七稿为完整文件</span></div>
        <table class="version-table">
          <colgroup><col style="width:38px"><col style="width:64px"><col><col style="width:62px"><col style="width:40px"></colgroup>
          <thead><tr><th>稿</th><th>日期</th><th>标题</th><th>字数</th><th>改动</th></tr></thead>
          <tbody>{version_rows}</tbody>
        </table>

        <div class="section-label"><span>读者 / 四位</span><span class="count">批注与修订</span></div>
        <ul class="readers">{readers}</ul>

        <div class="section-label"><span>材料 / 45 份</span><span class="count">未公开</span></div>
        <details class="materials" open>
          <summary><span>目录</span><span>收起</span></summary>
          {material_groups}
        </details>
        <p class="drawer-note">手稿、批注与背景材料暂不公开；这里只列目录。读者姓名也暂不列出。</p>
      </div>
      <aside class="drawer-rail" aria-hidden="true"></aside>
    </section>

    <section class="drawer" id="booklet">
      <aside class="drawer-rail">
        <span class="drawer-kicker">图版</span>
        <dl>
          <dt>时间</dt><dd>2025.06</dd>
          <dt>语言</dt><dd>English</dd>
          <dt>篇幅</dt><dd>{fmt(BOOK['words'])} 词</dd>
          <dt>章节</dt><dd>序 + 四章</dd>
          <dt>图版</dt><dd>4 幅</dd>
        </dl>
      </aside>
      <div class="drawer-main">
        <h2 lang="en">{e(BOOK['title_en'])}<span class="pen">{e(BOOK['subtitle_en'])}</span></h2>
        <p class="drawer-deck">{e(BOOK['title_zh'])}。写在{e(BOOK['place'])}，2025 年 6 月。</p>
        <figure class="plate-main">
          <img src="../assets/plate-01.jpg" alt="观星：一个人站在石壁的开口前，看星星">
          <figcaption><span class="cap-zh">图版 I · 观星 / Looking Up</span><span>fig_ch01</span></figcaption>
        </figure>
        <div class="preface" lang="en">
          <p>Generative AI has transformed countless aspects of our world. Among its many techniques, the diffusion model stands out as a groundbreaking framework—powering innovations like Stable Diffusion, whose magic captivates anyone (myself included) who remembers a time before the AI revolution.</p>
          <p>For learners like me, most tutorials and code snippets in blogs and papers provide only fragmented insights—forcing us to piece together scattered, incomplete explanations. I’ve tried to write it like something where ideas build naturally.</p>
        </div>
        <div class="section-label"><span>章节 / 五</span><span class="count">2025</span></div>
        <ol class="chapter-list">{chapters}</ol>
        <div class="formula">
          <span class="formula-label">Chapter IV · 前向过程</span>
          d<i>x</i><sub>t</sub> = − ½ <i>β</i>(<i>t</i>) <i>x</i><sub>t</sub> d<i>t</i> + √<span class="sqrt"><i>β</i>(<i>t</i>)</span> d<i>W</i><sub>t</sub>
        </div>
        <div class="section-label"><span>材料</span><span class="count">7 份</span></div>
        <details class="materials">
          <summary><span>目录</span><span>展开</span></summary>
          <div class="mat-group"><div class="mat-head"><h4>正文</h4><span>5 份</span></div><p>序、四章；Markdown 与 LaTeX 公式。</p><p class="mat-files">Chapter 0 - Preface.md · Chapter I ... · Chapter II ... · Chapter III ... · Chapter IV ...</p></div>
          <div class="mat-group"><div class="mat-head"><h4>图版</h4><span>4 份</span></div><p>每章开场的石刻图版，1024 × 1024。</p><p class="mat-files">fig_ch01.png · fig_ch02.png · fig_ch03.png · fig_ch04.png</p></div>
          <div class="mat-group"><div class="mat-head"><h4>其他</h4><span>3 份</span></div><p>路线图、图版说明、参考。</p><p class="mat-files">A roadmap - 20250611.md · figures of four chapters.md · references.md</p></div>
        </details>
        <p class="drawer-note">图版是每章的开场，不是示意图。四张图放在<a href="../c/index.html">展柜</a>里看更完整。</p>
      </div>
      <aside class="drawer-rail" aria-hidden="true"></aside>
    </section>

    <section class="drawer" id="record">
      <aside class="drawer-rail">
        <span class="drawer-kicker">记录</span>
        <dl>
          <dt>时间</dt><dd>2014–2025</dd>
          <dt>论文</dt><dd>30 篇</dd>
          <dt>引用</dt><dd>662</dd>
          <dt>专利</dt><dd>8 项</dd>
        </dl>
      </aside>
      <div class="drawer-main">
        <h2>论文与专利</h2>
        <p class="drawer-deck">不是文章，是工作的记录。按年份排，不按问题排。</p>
        <p class="record-lede">从航空宇航的代理模型、反设计和自然层流，到 2024 年以后的医学 AI 与表格插补。这里只留题名、刊物、年份和引用数；作者列表与检索说明在原始清单里。</p>
        <div class="section-label"><span>论文 / 30</span><span class="count">2014–2025</span></div>
        <div class="papers-grid">{papers}</div>
        <div class="section-label"><span>专利 / 8</span><span class="count">2018–2022</span></div>
        {patent_table()}
      </div>
      <aside class="drawer-rail" aria-hidden="true"></aside>
    </section>

    <section class="drawer" id="video">
      <aside class="drawer-rail">
        <span class="drawer-kicker">影像</span>
        <dl>
          <dt>时间</dt><dd>2026</dd>
          <dt>系列</dt><dd>3 条</dd>
          <dt>条数</dt><dd>35 条</dd>
          <dt>时长</dt><dd>约 5 小时</dd>
        </dl>
      </aside>
      <div class="drawer-main">
        <h2>影像</h2>
        <p class="drawer-deck">产品的说明书，不是作品。两个工具，一条工作记录。</p>
        <p class="record-lede">2026 年 1 月到 8 月，35 条视频：videomp3word 的功能演示与版本公告，rurussian 的教程与三场直播，以及 8 月一次性上传的三条技术切片。频道没有个人向内容。</p>
        <div class="section-label"><span>系列 / 三</span><span class="count">按发布时间</span></div>
        <ul class="video-series">{series_rows}</ul>
        <p class="drawer-note">这个抽屉可以关掉。它属于产品记录，不属于写作；如果不想把频道和这个站绑在一起，整段撤掉即可。</p>
      </div>
      <aside class="drawer-rail" aria-hidden="true"></aside>
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
    open(os.path.join(HERE, 'b/index.html'), 'w', encoding='utf-8').write(page_b())
    print('wrote b/index.html')
