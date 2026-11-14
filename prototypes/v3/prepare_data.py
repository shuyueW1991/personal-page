#!/usr/bin/env python3
"""Build data.json for the v3 vitrine prototypes from the materials in ../../vitrine.
Run from the repository root or from prototypes/v3; paths are resolved from this file."""
import json, os, re, glob, zipfile
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

# ---------------------------------------------------------------- papers
def clean_venue(v):
    v = v.replace('**', '').replace('*', '')
    v = re.sub(r'\s+', ' ', v)
    v = v.rstrip('.')
    # *Journal* **36**(1) collapses to "Journal 36(1)" only if a space was there; ensure it
    v = re.sub(r'([A-Za-z\)])(\d)', r'\1 \2', v) if False else v
    return v

SHORT = [
    ('Proceedings of the Institution of Mechanical Engineers', 'PIMechE G'),
    ('Journal of Aerospace Engineering', 'JOAE'),
    ('Aerospace Science and Technology', 'AST'),
    ('Chinese Journal of Aeronautics', 'CJA'),
    ('Physics of Fluids', 'PoF'),
    ('European Journal of Mechanics', 'EJM-B'),
    ('Applied Sciences', 'Appl. Sci.'),
    ('eClinicalMedicine', 'eClinMed'),
    ('Computational and Experimental Simulations', 'Springer'),
    ('Asia-Pacific International Symposium', 'APISAT'),
    ('Guangdong-Hong Kong-Macao', 'AIBDF'),
    ('Qeios', 'Qeios'),
    ('arXiv', 'arXiv'),
    ('民用飞机设计与研究', '民用飞机'),
    ('力学季刊', '力学季刊'),
]
def short_of(v):
    for k, s in SHORT:
        if k in v:
            return s
    return ''

def parse_papers():
    md = open(os.path.join(ROOT, 'vitrine/wang-shuyue-fudan-publications.md'), encoding='utf-8').read()
    sections = re.split(r'\n## ', md)
    out = []
    for sec in sections:
        if not re.match(r'[二三四五六]、', sec):
            continue
        blocks = re.split(r'\n### (\d{4})\n', sec)
        for i in range(1, len(blocks), 2):
            year = int(blocks[i]); body = blocks[i+1]
            for e in re.split(r'\n\n(?=\*\*)', body):
                e = e.strip()
                if not e.startswith('**'):
                    continue
                m = re.match(r'\*\*(.+?)\*\*\s*\n(.*)', e, re.S)
                if not m:
                    continue
                title = m.group(1).strip()
                rest = m.group(2)
                lines = [l.strip() for l in rest.splitlines() if l.strip()]
                venue = clean_venue(lines[0]) if lines else ''
                cm = re.search(r'被引\s*\*\*(\d+)\*\*', e)
                cites = int(cm.group(1)) if cm else 0
                dm = re.search(r'\[DOI\]\(<?(https?://[^)>]+)', e)
                doi = dm.group(1) if dm else ''
                out.append({
                    'year': year,
                    'title': title,
                    'venue': venue,
                    'short': short_of(venue),
                    'cites': cites,
                    'doi': doi,
                    'zh': bool(re.search(r'[\u4e00-\u9fff]', title)),
                })
    # de-dupe by title, keep order
    seen, res = set(), []
    for p in out:
        if p['title'] in seen: continue
        seen.add(p['title']); res.append(p)
    res.sort(key=lambda p: (-p['year'], -p['cites']))
    return res

# ---------------------------------------------------------------- videos
def parse_videos():
    md = open(os.path.join(ROOT, 'vitrine/youtube-henriwang8603-作品清单.md'), encoding='utf-8').read()
    rows = []
    for line in md.splitlines():
        if not line.startswith('| '): continue
        cols = [c.strip() for c in line.strip('|').split('|')]
        if len(cols) < 8 or not re.match(r'^\d+$', cols[0]): continue
        rows.append({
            'n': int(cols[0]), 'date': cols[1], 'type': cols[2], 'series': cols[3],
            'title': cols[4], 'duration': cols[5], 'views': int(cols[6].replace(',', '')),
            'id': re.sub(r'\[([^\]]+)\].*', r'\1', cols[7]),
        })
    return rows

# ---------------------------------------------------------------- novel
def docx_text(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
        body = root.find(W + 'body')
        out = []
        for el in body:
            tag = el.tag.split('}')[-1]
            if tag == 'p':
                out.append(''.join(n.text or '' for n in el.iter(W + 't')))
            elif tag == 'tbl':
                for tr in el.findall(W + 'tr'):
                    cells = []
                    for tc in tr.findall(W + 'tc'):
                        cells.append(' '.join(''.join(n.text or '' for n in p.iter(W + 't')) for p in tc.findall(W + 'p')))
                    out.append(' | '.join(cells))
        return '\n'.join(out)

def count_chars(path):
    t = docx_text(path)
    return len(re.sub(r'\s+', '', t))

novel_dir = os.path.join(ROOT, 'vitrine/novel贺六浑青年讲师202112')
draft_files = ['第二稿.docx','第三稿.docx','第三稿-微调.docx','第四稿.docx','第四稿-调整.docx','第五稿.docx','第六稿.docx','第七稿【为了通过审查】.docx']
draft_words = {f: count_chars(os.path.join(novel_dir, f)) for f in draft_files}

# ---------------------------------------------------------------- assemble
out = {
    'papers': parse_papers(),
    'videos': parse_videos(),
    'novel': {
        'title': '青年讲师',
        'pen': 'M·贺六浑',
        'status': '未刊',
        'words': draft_words['第七稿【为了通过审查】.docx'],
        'files': 45,
        'readers': 4,
        'stages': [
            {'stage':'一稿','date':'11.19–11.28','title':'《课题组谋杀嫌疑犯》→《讲师陶吕之死》→《课题组之死》','words':'2.2–2.6 万（分日）','change':'—','note':'13 份分日手稿'},
            {'stage':'二稿','date':'11 月末','title':'《青年讲师》','words':draft_words['第二稿.docx'],'change':'—','note':'第一次完整成篇'},
            {'stage':'三稿','date':'12.02','title':'《青年讲师》','words':draft_words['第三稿.docx'],'change':'11%','note':'另有微调版 33,755 字'},
            {'stage':'四稿','date':'12.03','title':'青年讲师','words':draft_words['第四稿.docx'],'change':'5%','note':'另有调整版 35,039 字'},
            {'stage':'五稿','date':'12.06','title':'青年讲师','words':draft_words['第五稿.docx'],'change':'2%','note':''},
            {'stage':'六稿','date':'12.11','title':'青年讲师 · M·贺六浑','words':draft_words['第六稿.docx'],'change':'4%','note':'首次署名'},
            {'stage':'七稿','date':'12.11 后','title':'青年讲师 · 一个虚构的故事','words':draft_words['第七稿【为了通过审查】.docx'],'change':'1%','note':'“为了通过审查”版'},
        ],
        'titles': ['《课题组谋杀嫌疑犯》','《讲师陶吕之死》','《课题组之死》','《青年讲师》'],
        'readers_data': [
            {'label':'读者 A','medium':'PDF 批注','count':15,'date':'12.05','quote':'？？？这转变太突然了','quote2':'每个牌子都写出来，像郭敬明的《小时代》2333'},
            {'label':'读者 B','medium':'PDF 批注','count':60,'date':'12.03–12.06','quote':'病句','quote2':'读起来别别扭扭的'},
            {'label':'读者 C','medium':'PDF 批注','count':55,'date':'12.02','quote':'警察姐姐看上杰哥了？','quote2':'这显得警察姐姐很没钱！'},
            {'label':'读者 D','medium':'Word 修订','count':172,'date':'12 月','quote':'作者的构思非常巧妙，文本、现实、梦境、自己、女友等视角不断切换交织','quote2':'佩服作者的执行力，可以在主业之外有自己的想法，并且付诸实践写成文，而且修改七稿'},
        ],
        'groups': [
            {'name':'框架','n':6,'note':'一份表格、五版线性框架，11.04–11.27','files':['框架20211104.xlsx','线性框架20211106.docx','线性框架20211111.docx','线性框架20211112.docx','线性框架20211113.docx','线性框架20211127.docx']},
            {'name':'分日手稿','n':13,'note':'11.19–11.28，按天推进的片段与整章','files':['稿20211119.docx','稿20211120.docx','稿20211121.docx','稿20211123.docx','稿20211124.docx','稿20211125.docx','稿20211125.pdf','稿20211127-〇一.docx','稿20211127-〇二.docx','稿20211127-〇三.docx','稿20211127-〇四.docx','稿20211128-〇五.docx','稿20211128-〇六.docx']},
            {'name':'完整稿','n':13,'note':'二稿至七稿；含 PDF 与微调/调整版','files':['第二稿.docx','第三稿.docx','第三稿-微调.docx','第三稿.pdf','第三稿-微调-没加密.pdf','第四稿.docx','第四稿-调整.docx','第四稿.pdf','第五稿.docx','第五稿.pdf','第六稿.docx','第六稿.pdf','第七稿（审查版）.docx']},
            {'name':'读者批注','n':4,'note':'三位读者在 PDF 上批注，一位在 Word 里修订；姓名从文件名里拿掉','files':['第四稿评论 · 读者 A.pdf','第四稿批注 · 读者 B.pdf','第三稿改动 · 读者 C.pdf','第七稿修订 · 读者 D.docx']},
            {'name':'副文本','n':3,'note':'写作目的、作品简介、语段与 idea 库','files':['写作目的与致谢.docx','作品简介20-300.docx','语段和idea库.docx']},
            {'name':'片段','n':3,'note':'审讯、事后、开篇三个早期片段','files':['0.docx','1.docx','2.docx']},
            {'name':'背景','n':3,'note':'真实事件材料与外界评论；暂不公开','files':['真实事件材料（未公开）.docx','外界评价（未公开）.docx','20201110-paper.docx']},
        ],
        'excerpt': [
            'Z：我们先走个流程，做下笔录，你说的和我们讲的都会在这个东西里记录。',
            '辛子杰：好的，警官。',
            'Z：说话说得响一点。否则可能录音不到位会要你重说。',
            '辛子杰：咳咳……好的。',
            'Z：姓名？',
            '辛子杰：辛子杰。',
        ],
        'purpose_quote': '每个人在自己的角度都没有错，但大家聚在一起就拉开悲剧的序幕。',
        'synopsis': '一所顶尖高校。一场震动学术界的谋杀。一个才华横溢但心生疲倦的青年讲师。他坐在课题组组会里，几个小时，他拿着刀出现在实验室。',
    },
    'booklet': {
        'title_en': 'A Preliminary Mathematical Exegesis of Diffusion Models',
        'subtitle_en': 'Gaining Clarity From True Understanding',
        'title_zh': '扩散模型的一个初步数学阐释',
        'place': '比什凯克',
        'date': '2025.06',
        'words': 20251,
        'chapters': [
            {'no':'序','title':'Preface','zh':'为什么写这本小册','words':829,'summary':'为什么写、写给谁，以及四个 deus ex machina。'},
            {'no':'I','title':'The High-Dimensional Structure of True Data','zh':'真实数据的高维结构','words':3868,'summary':'自然图像在高维空间里的低维结构；把生成建模写成密度估计。'},
            {'no':'II','title':'The ELBO Paradigm','zh':'ELBO 范式','words':3150,'summary':'引入隐变量与 KL，推出 ELBO，把不可算的 log p(x) 变成可优化的代理目标。'},
            {'no':'III','title':'Dissecting the ELBO','zh':'拆开 ELBO','words':11234,'summary':'从 ELBO 走到分布迁移、score matching 与 SDE；扩散模型的骨架。'},
            {'no':'IV','title':'Implementation on machine','zh':'在机器上实现','words':1170,'summary':'把前向/反向过程写成可执行代码；文末仍然开放。'},
        ],
        'plates': [
            {'src':'assets/plate-01.jpg','no':'I','zh':'观星','en':'Looking Up','note':'一个人站在石壁的开口前，看星星。'},
            {'src':'assets/plate-02.jpg','no':'II','zh':'制陶','en':'Making','note':'两个人，一只还没有烧的陶罐。'},
            {'src':'assets/plate-03.jpg','no':'III','zh':'通道','en':'Passage','note':'一道向里延伸的拱门，光在入口，暗在深处。'},
            {'src':'assets/plate-04.jpg','no':'IV','zh':'收获','en':'Harvest','note':'太阳、镰刀和麦穗，刻在石头上。'},
        ],
        'quote': 'The math is precise by my best, but I hope it feels more like following a story than reading a textbook.',
        'quote2': 'Nothing’s introduced without context, and no idea exists just for show.',
    },
    'patents': [
        {'no':'CN113343347B','title':'一种翼型前缘CST的垂直补偿修正方法及装置','year':2022,'status':'授权'},
        {'no':'CN112417785B','title':'基于微纳米沟槽壁面滑移效应的跨尺度数值模拟方法','year':2022,'status':'授权'},
        {'no':'CN112580151B','title':'基于目标空间的自然层流翼型的优化问题指标获取方法','year':2022,'status':'授权'},
        {'no':'CN112989718A','title':'一种翼型前缘CST的全局转换修正方法及装置','year':2021,'status':'驳回'},
        {'no':'CN112800663A','title':'基于神经网络的航空发动机压气机转子叶片的反设计方法','year':2021,'status':'申请'},
        {'no':'CN106189631B','title':'一种基于微纳米涂层的飞机机翼转捩延迟方法','year':2019,'status':'授权'},
        {'no':'CN104778327B','title':'基于人工神经网络的飞机翼型优化设计方法','year':2018,'status':'授权'},
        {'no':'CN104834772B','title':'基于人工神经网络的飞机翼型/机翼反设计方法','year':2018,'status':'授权'},
    ],
    'video_series': [
        {'name':'videomp3word','n':22,'span':'2026.01–03','note':'视频 / 音频 / 文字互转工具的产品说明。'},
        {'name':'rurussian','n':10,'span':'2026.02–04','note':'AI 俄语学习工作台；含三场直播。'},
        {'name':'Agents orchestrator','n':3,'span':'2026.08','note':'工作相关的技术切片，5–27 秒。'},
    ],
}

# totals
out['totals'] = {
    'papers': len(out['papers']),
    'cites': sum(p['cites'] for p in out['papers']),
    'patents': len(out['patents']),
    'videos': len(out['videos']),
    'video_hours': 5.0,
    'novel_files': out['novel']['files'],
    'booklet_words': out['booklet']['words'],
}
json.dump(out, open(os.path.join(HERE, 'data.json'), 'w'), ensure_ascii=False, indent=1)
print(json.dumps(out['totals'], ensure_ascii=False, indent=1))
print('draft words', draft_words)
print('papers first', out['papers'][0])
print('videos', out['videos'][0])
