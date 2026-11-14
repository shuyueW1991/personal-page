#!/usr/bin/env python3
import os

HERE = os.path.dirname(os.path.abspath(__file__))
V2 = '../../v2/b-desk/'


def essays():
    return f'''
      <article class="latest cat-art">
        <div class="meta">
          <time datetime="2026-09-18">2026.09.18</time>
          <span class="cat"><span class="dot"></span>艺术</span>
        </div>
        <h3><a href="{V2}essay.html">在展厅里走神</a></h3>
        <p class="deck">观看并不总是专注。走神也是作品的一部分。</p>
      </article>

      <article class="item cat-tech">
        <div class="meta">
          <time datetime="2026-08-24">2026.08</time>
          <span class="cat"><span class="dot"></span>技术</span>
        </div>
        <h3 lang="en"><a href="{V2}quiet-tool.html">The Quiet Tool</a></h3>
      </article>

      <article class="item cat-politics">
        <div class="meta">
          <time datetime="2025-11-30">2025.11</time>
          <span class="cat"><span class="dot"></span>政论</span>
        </div>
        <h3><a href="{V2}essay.html">地方性的消逝</a></h3>
      </article>

      <article class="item cat-art">
        <div class="meta">
          <time datetime="2025-07-04">2025.07</time>
          <span class="cat"><span class="dot"></span>艺术</span>
        </div>
        <h3><a href="{V2}essay.html">一份关于注释的注释</a></h3>
      </article>

      <article class="item cat-phil">
        <div class="meta">
          <time datetime="2024-08-17">2024.08</time>
          <span class="cat"><span class="dot"></span>哲学</span>
        </div>
        <h3><a href="{V2}essay.html">空白的重量</a></h3>
      </article>'''


def home(extra='', rail_extra='', head_extra='', body_class=''):
    return f'''<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>王舒悦 — 文章</title>
  <meta name="description" content="王舒悦的文章：政论、艺术、技术、哲学。数量不多，更新不定。">
  <link rel="stylesheet" href="../../v2/b-desk/style.css">
  <link rel="stylesheet" href="../assets/home.css">
</head>
<body class="{body_class}">
  <a class="skip" href="#main">跳到正文</a>

  <div class="desk">
    <aside class="rail" aria-label="简介">
      <p class="statement">写政治、艺术、技术与哲学。<br>文章不多，更新不定。</p>
      <div class="rail-bottom">
        <div class="rail-links">
          <a href="#">写信</a>
          <a href="#">RSS</a>{rail_extra}
        </div>
      </div>
    </aside>

    <main id="main" class="stream">
      <h1 class="sr-only">文章</h1>

      <div class="stream-head">
        <h2>近作</h2>
        {head_extra or f'<a class="section-link" href="{V2}notes.html">页边 →</a>'}
      </div>
{essays()}
{extra}
      <p class="endnote">其余的还没整理完。</p>
      <p class="colophon">© 2026 王舒悦</p>
    </main>
  </div>
</body>
</html>
'''


def home_a():
    extra = '''
      <p class="endnote">其余的还没整理完。</p>
      <p class="endnote materials-line">稿本、论文和影像，另有一份<a href="index.html">材料账</a>。</p>
'''
    page = home(extra=extra, rail_extra='\n          <a href="index.html">材料</a>')
    page = page.replace('''      <p class="endnote">其余的还没整理完。</p>
      <p class="colophon">© 2026 王舒悦</p>''', '''      <p class="colophon">© 2026 王舒悦</p>''')
    return page


def home_b():
    extra = '''
      <p class="endnote">其余的还没整理完。</p>

      <div class="stream-head work-head">
        <h2>工作台</h2>
        <a class="section-link" href="index.html">四件东西 →</a>
      </div>

      <article class="work">
        <div class="work-kind">稿本</div>
        <div>
          <h3><a href="index.html#novel">《青年讲师》</a></h3>
          <p class="work-note">一个虚构的故事。七稿，四十五份文件，四位读者。</p>
        </div>
      </article>

      <article class="work">
        <div class="work-kind">图版</div>
        <div>
          <h3 lang="en"><a href="index.html#booklet">A Preliminary Mathematical Exegesis of Diffusion Models</a></h3>
          <p class="work-note">写在比什凯克的一本英文小册。四章，四幅图版。</p>
        </div>
      </article>

      <article class="work">
        <div class="work-kind">记录</div>
        <div>
          <h3><a href="index.html#record">论文与专利</a></h3>
          <p class="work-note">2014–2025，航空宇航、医学 AI 和几项专利。</p>
        </div>
      </article>

      <article class="work">
        <div class="work-kind">影像</div>
        <div>
          <h3><a href="index.html#video">videomp3word / rurussian</a></h3>
          <p class="work-note">产品说明，不是作品。可以整段不看。</p>
        </div>
      </article>
'''
    page = home(extra=extra)
    page = page.replace('''      <p class="endnote">其余的还没整理完。</p>
      <p class="colophon">© 2026 王舒悦</p>''', '''      <p class="colophon">© 2026 王舒悦</p>''')
    return page


def home_c():
    head_extra = f'''<div class="head-links">
          <a class="section-link" href="{V2}notes.html">页边 →</a>
          <a class="section-link" href="index.html">展柜 →</a>
        </div>'''
    extra = '''
      <figure class="home-vitrine">
        <a href="index.html" aria-label="打开展柜">
          <img src="../assets/plate-03.jpg" alt="石刻拱门：一道向里延伸的通道">
        </a>
        <figcaption>
          <span>展柜 / Vitrine</span>
          <span>稿本、图版、记录 →</span>
        </figcaption>
      </figure>
'''
    page = home(extra=extra, head_extra=head_extra)
    page = page.replace('<p class="endnote">其余的还没整理完。</p>', '<p class="endnote">其余的都在展柜里。</p>')
    return page


if __name__ == '__main__':
    for name, fn in [('a', home_a), ('b', home_b), ('c', home_c)]:
        open(os.path.join(HERE, name, 'home.html'), 'w', encoding='utf-8').write(fn())
        print('wrote', name, '/home.html')
