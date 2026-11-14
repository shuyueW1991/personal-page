#!/usr/bin/env python3
"""Final draft of 《青年讲师》 as a paper book page.
Source: vitrine/novel贺六浑青年讲师202112/第七稿【为了通过审查】.docx
No synopsis, no version table, no reader notes; full text + watermark."""
import zipfile, re, os, html
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SRC = os.path.join(ROOT, 'vitrine/novel贺六浑青年讲师202112/第七稿【为了通过审查】.docx')
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def paragraphs(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
        out = []
        for el in root.find(W + 'body'):
            if el.tag == W + 'p':
                t = ''.join(n.text or '' for n in el.iter(W + 't')).strip()
                if t:
                    out.append(t)
        return out


def e(s):
    return html.escape(s, quote=True)


def main():
    ps = paragraphs(SRC)
    assert ps[0] == '青年讲师', ps[:4]
    start = 1
    while ps[start] in ('一个虚构的故事', 'M·贺六浑'):
        start += 1
    body = ps[start:]

    parts = []
    cur = None
    for p in body:
        if p in ('一', '二', '三', '四', '五'):
            cur = {'label': p, 'blocks': []}
            parts.append(cur)
            continue
        if cur is None:
            continue
        if re.fullmatch(r'\d{1,2}', p):
            cur['blocks'].append({'kind': 'no', 'label': p})
        elif p == '片段':
            cur['blocks'].append({'kind': 'frag'})
        elif p == '（全文终）':
            cur['blocks'].append({'kind': 'end'})
        else:
            cls = 'dialogue' if re.match(r'^[^：:\n]{1,6}[：:]', p) else ''
            cur['blocks'].append({'kind': 'p', 'text': p, 'cls': cls})

    nums = {'一': '01', '二': '02', '三': '03', '四': '04', '五': '05'}
    sections = []
    for part in parts:
        rows = []
        for b in part['blocks']:
            if b['kind'] == 'no':
                rows.append(f'<h3 class="sub-head"><span class="sub-no">{b["label"].zfill(2)}</span></h3>')
            elif b['kind'] == 'frag':
                rows.append('<h3 class="sub-head is-frag">片段</h3>')
            elif b['kind'] == 'end':
                rows.append('<p class="novel-end">（全文终）</p>')
            else:
                cls = f' class="{b["cls"]}"' if b['cls'] else ''
                rows.append(f'<p{cls}>{e(b["text"])}</p>')
        sections.append(f'''<section class="part" id="part-{nums[part['label']]}">
  <header class="part-head"><span class="part-no">{nums[part['label']]}</span><h2>第{part['label']}部分</h2></header>
  {''.join(rows)}
</section>''')

    nav = ''.join(f'<a href="#part-0{i}">{l}</a>' for i, l in zip(range(1, 6), ['一','二','三','四','五']))
    wm = ' '.join(['M·贺六浑 · 未刊稿'] * 24)

    doc = f'''<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>青年讲师 — 王舒悦</title>
  <meta name="description" content="青年讲师。一个虚构的故事。M·贺六浑。">
  <link rel="stylesheet" href="personal.css">
  <link rel="stylesheet" href="novel.css">
</head>
<body>
  <a class="skip" href="#text">跳到正文</a>

  <header class="page-top">
    <a class="back" href="index.html">← 首页</a>
    <span class="label">小说 / 未刊</span>
  </header>

  <section class="novel-title">
    <div class="title-main">
      <p class="title-kicker">NOVEL</p>
      <h1>青年讲师</h1>
      <p class="title-sub">一个虚构的故事</p>
      <p class="title-pen">M·贺六浑</p>
    </div>
    <div class="title-stamp" aria-hidden="true">未刊稿<br>请勿转载</div>
  </section>

  <div class="page-wm" aria-hidden="true"><div class="wm-rot"><div>{wm}</div><div>{wm}</div><div>{wm}</div><div>{wm}</div><div>{wm}</div><div>{wm}</div></div></div>

  <main class="novel-main" id="text">
    <nav class="part-nav" aria-label="章节">{nav}</nav>
    <article class="novel-text">{''.join(sections)}</article>
  </main>

  <footer class="page-foot">
    <span>© 2026 王舒悦</span>
    <div class="links"><a href="index.html">← 首页</a></div>
  </footer>
</body>
</html>
'''
    open(os.path.join(HERE, 'novel.html'), 'w', encoding='utf-8').write(doc)
    print('parts', len(parts), 'paragraphs', sum(1 for p in body if p not in ('一','二','三','四','五') and not re.fullmatch(r'\d{1,2}', p) and p != '片段'), 'bytes', len(doc))


if __name__ == '__main__':
    main()
