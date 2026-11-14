#!/usr/bin/env python3
"""Academic publications page from vitrine/wang-shuyue-fudan-publications.md."""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SRC = os.path.join(ROOT, 'vitrine/wang-shuyue-fudan-publications.md')
D = json.load(open(os.path.join(HERE, '..', '..', 'v3', 'data.json'), encoding='utf-8'))
PATENTS = D['patents']


def e(s):
    return html.escape(str(s), quote=True)


def md_inline(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    for name in ('Shuyue Wang', 'Shu-Yue Wang', '王舒悦'):
        s = s.replace(f'<strong>{name}</strong>', f'<strong class="me">{name}</strong>')
    return s


def parse():
    lines = open(SRC, encoding='utf-8').read().splitlines()
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        m = re.fullmatch(r'\*\*(.+)\*\*', line)
        if m and not line.startswith('**被引'):
            title = m.group(1).strip()
            j = i + 1
            block = []
            while j < len(lines) and not lines[j].startswith('## ') and not lines[j].startswith('### '):
                t = lines[j].strip()
                if t:
                    block.append(t)
                if j + 1 < len(lines):
                    nxt = lines[j + 1].strip()
                    if re.fullmatch(r'\*\*(.+)\*\*', nxt) and not nxt.startswith('**被引'):
                        break
                j += 1
            if len(block) >= 2:
                venue = block[0].rstrip(' .')
                authors = ''
                for t in block[1:]:
                    if t.startswith('[') or t.startswith('<sub>'):
                        continue
                    authors = t
                    break
                links = '\n'.join(block)
                dm = re.search(r'\[DOI\]\(<([^>]+)>\)', links) or re.search(r'\[DOI\]\(([^)]+)\)', links)
                doi = dm.group(1) if dm else ''
                cm = re.search(r'被引\s*\*\*(\d+)\*\*', links)
                cites = int(cm.group(1)) if cm else 0
                # classify
                v = venue.lower()
                if 'arxiv' in v or 'qeios' in v or 'preprint' in v:
                    kind = 'preprint'
                elif ('asia-pacific international symposium' in v or 'aibdf' in v or 'guangdong-hong-kong-macao' in v or 'computational and experimental simulations' in v):
                    kind = 'conference'
                else:
                    kind = 'journal'
                entries.append({'title': title, 'venue': venue, 'authors': authors, 'doi': doi, 'cites': cites, 'kind': kind})
            i = j
        else:
            i += 1
    # de-dupe by title
    seen, out = set(), []
    for x in entries:
        if x['title'] in seen: continue
        seen.add(x['title']); out.append(x)
    return out


def page():
    pubs = parse()
    groups = [('journal', '期刊论文', 'Journal Articles'), ('conference', '会议与章节', 'Conference & Chapters'), ('preprint', '预印本', 'Preprints')]

    sections = ''
    for kind, zh, en in groups:
        items = [p for p in pubs if p['kind'] == kind]
        rows = ''
        for p in items:
            links = []
            if p['doi']:
                links.append(f'<a href="{e(p["doi"])}" target="_blank" rel="noopener">DOI</a>')
            if p['cites']:
                links.append(f'<span>被引 {p["cites"]}</span>')
            rows += f'''<article class="pub">
  <p class="pub-authors">{md_inline(p['authors'])}</p>
  <h3 class="pub-title">{e(p['title'])}</h3>
  <p class="pub-venue">{md_inline(p['venue'])}</p>
  <p class="pub-links">{' · '.join(links) if links else '—'}</p>
</article>'''
        sections += f'''<section class="pub-section">
  <div class="pub-section-head"><h2>{zh}<span>{en}</span></h2><span>{len(items)} 篇</span></div>
  {rows}
</section>'''

    patents = ''.join(f'''<tr><td>{p['year']}</td><td>{e(p['title'])}</td><td>{e(p['no'])} · {e(p['status'])}</td></tr>''' for p in PATENTS)

    return f'''<!doctype html>
<html lang="zh-Hans">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>论文 — 王舒悦</title>
  <meta name="description" content="王舒悦的论文与专利。">
  <link rel="stylesheet" href="personal.css">
  <link rel="stylesheet" href="papers.css">
</head>
<body>
  <a class="skip" href="#main">跳到正文</a>
  <header class="page-top">
    <a class="back" href="index.html">← 首页</a>
    <span class="label">论文 / Publications</span>
  </header>

  <main id="main" class="papers-shell">
    <div class="papers-head">
      <h1>论文</h1>
      <p class="pub-meta">{len(pubs)} 篇论文 · {len(PATENTS)} 项专利<br>
        <a href="https://orcid.org/0000-0001-8452-5602" target="_blank" rel="noopener">ORCID</a> ·
        <a href="https://scholar.google.com/scholar?hl=zh-CN&amp;q=%22Shuyue+Wang%22+%22Fudan+University%22" target="_blank" rel="noopener">Google Scholar</a>
      </p>
    </div>

    {sections}

    <section class="pub-section patents-section">
      <div class="pub-section-head"><h2>专利<span>Patents</span></h2><span>{len(PATENTS)} 项</span></div>
      <table class="patents">
        <thead><tr><th>年份</th><th>名称</th><th>专利号</th></tr></thead>
        <tbody>{patents}</tbody>
      </table>
    </section>
  </main>

  <footer class="page-foot">
    <span>© 2026 王舒悦</span>
    <div class="links"><a href="index.html">← 首页</a></div>
  </footer>
</body>
</html>
'''


if __name__ == '__main__':
    open(os.path.join(HERE, 'papers.html'), 'w', encoding='utf-8').write(page())
    print('wrote papers.html', len(parse()))
