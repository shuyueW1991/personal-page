#!/usr/bin/env python3
import json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, '..', '..', 'v3', 'data.json'), encoding='utf-8'))
BOOK = D['booklet']


def e(s):
    return html.escape(str(s), quote=True)


def works():
    preview = ''.join(f'<img src="{e(p["src"])}" alt="" aria-hidden="true">' for p in BOOK['plates'])
    return f'''<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>工作台 — 王舒悦</title>
  <meta name="description" content="技术书籍与以后的技术写作。">
  <link rel="stylesheet" href="personal.css">
  <link rel="stylesheet" href="workbench.css">
</head>
<body>
  <a class="skip" href="#main">跳到正文</a>
  <header class="page-top">
    <a class="back" href="index.html">← 首页</a>
    <span class="label">技术 / Workbench</span>
  </header>

  <main id="main" class="tech-shell">
    <h1>工作台</h1>
    <ul class="tech-list">
      <li>
        <a class="tech-item" href="booklet.html">
          <span class="tech-type">BOOK</span>
          <span class="tech-title" lang="en">{e(BOOK['title_en'])}</span>
          <span class="tech-arrow">↗</span>
        </a>
      </li>
    </ul>
    <div class="tech-preview" aria-hidden="true">{preview}</div>
  </main>

  <footer class="page-foot">
    <span>© 2026 王舒悦</span>
    <div class="links"><a href="index.html">← 首页</a></div>
  </footer>
</body>
</html>
'''


def booklet():
    plates = ''.join(f'''<figure class="book-plate">
  <img src="{e(p['src'])}" alt="{e(p['zh'])}：{e(p['note'])}">
  <figcaption><span>{e(p['no'])} · {e(p['zh'])}</span><span>{e(p['en'])}</span></figcaption>
</figure>''' for p in BOOK['plates'])
    chapters = ''.join(f'''<li>
  <span class="book-ch-no">{e(c['no'])}</span>
  <span class="book-ch-title" lang="en">{e(c['title'])}</span>
  <span class="book-ch-zh">{e(c['zh'])}</span>
</li>''' for c in BOOK['chapters'])
    return f'''<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>A Preliminary Mathematical Exegesis of Diffusion Models — 王舒悦</title>
  <meta name="description" content="A Preliminary Mathematical Exegesis of Diffusion Models. 序、四章、四幅图版。">
  <link rel="stylesheet" href="personal.css">
  <link rel="stylesheet" href="booklet.css">
</head>
<body>
  <a class="skip" href="#main">跳到正文</a>
  <header class="page-top">
    <a class="back" href="works.html">← 工作台</a>
    <span class="label">技术书籍 / Book</span>
  </header>

  <main id="main" class="book-shell">
    <h1 class="book-title" lang="en">{e(BOOK['title_en'])}</h1>
    <p class="book-sub">{e(BOOK['subtitle_en'])} · {e(BOOK['title_zh'])}</p>

    <div class="book-plates">{plates}</div>

    <div class="book-preface" lang="en">
      <p>Generative AI has transformed countless aspects of our world. Among its many techniques, the diffusion model stands out as a groundbreaking framework—powering innovations like Stable Diffusion, whose magic captivates anyone (myself included) who remembers a time before the AI revolution.</p>
      <p>For learners like me, most tutorials and code snippets in blogs and papers provide only fragmented insights—forcing us to piece together scattered, incomplete explanations. I’ve tried to write it like something where ideas build naturally.</p>
    </div>

    <ol class="book-chapters">{chapters}</ol>
  </main>

  <footer class="page-foot">
    <span>© 2026 王舒悦</span>
    <div class="links"><a href="works.html">← 工作台</a></div>
  </footer>
</body>
</html>
'''


if __name__ == '__main__':
    open(os.path.join(HERE, 'works.html'), 'w', encoding='utf-8').write(works())
    open(os.path.join(HERE, 'booklet.html'), 'w', encoding='utf-8').write(booklet())
    print('wrote works.html, booklet.html')
