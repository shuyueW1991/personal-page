# personal page

王舒悦（Shuyue Wang）的个人网站：近黑书封式的索引首页，四个入口；内页是纸底阅读版，`contact` 页集中 LinkedIn、GitHub 与驻足过的城市。

- 线上站点：<https://shuyuew1991.github.io/personal-page/>
- 稿件、批注、中间版本和书稿全文**不在这个仓库里**；公开样章（序言 + 第一章）在 `tools/book/sample.md`，规则见 [PUBLISHING.md](PUBLISHING.md)。

## 结构

```
build.py                       白名单装配 _site/，CI 也用同一个脚本
tools/posts/build.mjs           构建时把 Markdown 注记排成整页（KaTeX 预渲染 + 图版桌面）
tools/posts/note-template.html  注记页外壳：阅读桌、页边批注、评论、上下篇
tools/book/sample.md            书的免费样章源（序言 + 第一章）；build.py 用同一个 KaTeX 生成器排版
tools/book/sample-template.html 样章页外壳（和注记页不同，没有阅读桌）
tools/book/build-pdf.py        本地把完整书稿排成 dist/*.pdf（读 gitignore 的书稿；不进 CI）
tools/stats_snapshot.py        CI 里把 GoatCounter 汇总成 _site/stats.json
prototypes/v2/b-desk/          上线页面：封面首页 + contact + 分类页 + inbox + stats
prototypes/v2/b-desk/assets/   图版与 KaTeX；count.js 是 GoatCounter 官方脚本（ISC）
prototypes/v1、v3              旧方案，存档对照，不部署
vitrine/instrumentality/       注记唯一源：Markdown + 图版；推上来就自动发布
```

注记页不再手工维护。`vitrine/instrumentality/` 下每个 `.md` 在构建时生成
`_site/<slug>.html`，`instrumentality.html` 的 notes 列表和 sitemap 也一起更新。

## 本地

注记生成需要 Node.js 18+；第一次先装依赖，之后只用 `build.py`：

```bash
cd tools/posts && npm ci && cd ../..
python3 build.py                              # 生成 _site/
cd _site && python3 -m http.server 8123
```

`build.py --check` 只做校验：白名单文件齐全、注记和样章能生成、页面引用的本地资源都存在、每页 canonical 正确、每页都挂上了统计。它会在临时目录里完整构建一遍，不碰 `_site/`；真正构建时还会再扫一遍 `_site/`，确认里面没有完整书稿。

`build.py` 会在 `_site/stats.json` 写一个 `enabled: false` 的占位。没有真实快照时，统计页只显示占位、不显示数字——这是正常的，不是缓存问题。

## 注记与评论

`instrumentality.html` 分成 notes / quotes / book / papers 四栏：六篇注记、0 则语录（先留空）、一本书、论文与专利索引。notes 按年份分组、两列排布，外层限高滚动；列表在构建时按 `vitrine/instrumentality/` 的日期自动生成，新年份也会自己出现。quotes 的 `.quote-entry` 形态也已定义，等第一条语录。现在的六篇：

- [`object-image-zones.html`](https://shuyuew1991.github.io/personal-page/object-image-zones.html) —— 物像区域：四种基础光学元件的成像分区（2026.11.20）
- [`gaussian-reduction.html`](https://shuyuew1991.github.io/personal-page/gaussian-reduction.html) —— 高斯约化（Gaussian Reduction）与双光组等效系统（2026.11.20）
- [`nodal-points.html`](https://shuyuew1991.github.io/personal-page/nodal-points.html) —— 节点与主平面（2026.11.19）
- [`front-focal-magnification.html`](https://shuyuew1991.github.io/personal-page/front-focal-magnification.html) —— 前焦点处的横向放大率（2026.11.18）
- [`optical-power.html`](https://shuyuew1991.github.io/personal-page/optical-power.html) —— Optical Power and Focal Length（2026.11.17）
- [`clean-dwg.html`](https://shuyuew1991.github.io/personal-page/clean-dwg.html) —— 让 DXF 成为可被脚本干净解析的电气连接图（2026.11.12）

### 新增一篇注记

在 `vitrine/instrumentality/` 下放一个 `.md`，推到 `main` 就不用管了：CI 会重新生成页面、notes 列表、`inbox` 的标题表和 sitemap。最短只要标题和日期：

```markdown
---
title: 标题
date: 2026-11-21
---

# 标题

正文……
```

front matter 都可选：

| 字段 | 作用 |
|---|---|
| `title` | 列表标题、`<title>` 和上下篇链接 |
| `heading` | 页面大标题；想和 `title` 不同时用（可写数学） |
| `list_title` | notes 列表里想用更长的标题时写 |
| `deck` | 大标题下的副标题 |
| `date` | `YYYY-MM-DD`；不写就按文件名 / git 首次提交 / 文件时间推 |
| `slug` | 英文短名和输出文件名；英文子目录可省，不写会自动生成稳定短名 |
| `summary` | meta description；不写取第一段 |
| `lang` | `zh-Hans` 或 `en`；不写按正文判断 |
| `draft: true` | 不发布这一篇 |

- 子目录可以自动当 slug：`vitrine/instrumentality/foo/bar.md` → `foo.html`；中文目录名或想自定义时写 `slug:`。没写 slug 时会自动用 `note-<日期>-<短哈希>`，构建日志里会提示。
- 以 `_` 或 `.` 开头的文件和目录不发布，可用来放草稿和素材。
- 图片写相对路径（`./images/x.svg`）。构建时只把被引用的图片复制到 `assets/posts/<slug>/`；独立成段的图片收进右侧阅读桌的图版 tabs，正文不重复放图。图注优先取图片下一段以 `**Figure 1.**` 开头的整段，其次取 Markdown 图片 title，最后用 alt。
- 公式用 `$...$`、`$$...$$`、`\(...\)` 或 `\[...\]`，构建时用本地 [KaTeX](https://katex.org/) 预排成 HTML + MathML，页面不加载公式脚本；`prototypes/v2/b-desk/assets/katex/` 只留 CSS 和 woff2 字体（MIT，见同目录 `LICENSE`），不依赖 CDN。

注记页是两栏：左侧是一张随滚动固定的阅读桌，右侧是占页宽 2/3 的正文。帖子图全部收进桌面，正文不再重复放图：桌面上半是图版 tabs 或草图 canvas（第一次点图进入 1:1 对照，第二次完全放大；草图可导出 SVG），下半是页边批注；正文左边一条 34px 刻度栏把段落和批注对应起来。选中正文、点刻度，或从 inbox 进来，都会在阅读桌里打开对应段落的批注编辑/评论。

每个作品页（小说、文章、书、论文、六篇注记）和页边（`notes.html`）底部都有 page comments 区块。默认只显示一个按钮，点开后才向 `utteranc.es` 请求评论框；页边批注也只在点 `margin notes`、选中正文或从 inbox 进入时才向 GitHub 请求。普通打开文章时不向 GitHub 发任何请求。page comments 一页一个 issue，按 pathname 关联；页边批注则一段一个 issue，标题是 `[margin] <page>#<anchor>`，正文开头带一段 base64 元数据（页码、锚点、引文）。锚点由段落文本的哈希生成；大段改写会让旧批注找不到原来的段落。

第一次发言前要在仓库上装一次 [utterances App](https://github.com/apps/utterances)，并确认仓库 **Settings → General → Features → Issues** 已开启。没装 app 时评论框能出现，但提交会失败，页面其他部分不受影响。

- 配置（repo、label、theme）在 `prototypes/v2/b-desk/comments.js` 顶部
- 样式在 `comments.css`，评论区骨架直接写在各页面里（`data-comments`）
- 页边批注的交互在 `post.js`，样式在 `post.css`；issue 的创建链接会打开 GitHub 的新 issue 页面，提交后回到文章即刷新
- 不登录也能读；发言要 GitHub 账号。issue 是公开的，别在评论里留隐私
- 首页页脚的 `comments` 入口进 `inbox.html`：只列未看过的页边批注，点一行跳到对应段落，勾掉即从本机队列移除；同一 issue 之后有新回复会重新出现。页码对应的标题来自构建生成的 `post-titles.js`，新注记不用手改 `inbox.js`
- `inbox.html` 是 `noindex`，不进 sitemap；队列状态只存在浏览器 `localStorage`

## 书与样章

`exegesis.html` 是书的落地页：免费样章入口、章节目录、FAQ、引用格式和购买区。`exegesis-sample.html` 是免费样章（序言 + 第一章），源文件在 `tools/book/sample.md`，由 `build.py` 调 `tools/posts/build.mjs` 排版，模板是 `tools/book/sample-template.html`。完整书稿仍在 `vitrine/exegesis_of_diffusion/`，被 `.gitignore` 排除；只有样章进仓库。

购买区在 `exegesis.html#buy`，价格、交付和退款说明都写在页面上；按钮读 `prototypes/v2/b-desk/payments.js` 里的 `window.BOOK_PAYMENT_LINKS`。链接为空时按钮隐藏，显示 `Payment link coming soon`，所以可以先上线页面再补链接。

`thanks.html` 是 Stripe 付款后的静态确认页，`noindex`，不进 sitemap；它不验证付款，下载链接由邮件发出。

### 接 Stripe（一次性）

1. Stripe Dashboard → Product catalog：新建书的产品，建两个 one-time price（PDF、supporter bundle）。
2. Settings → Payment methods → Alipay：账户所在地/币种支持的话打开；不支持就走国内平台，不要硬接。
3. Payment links：每个 price 建一个链接，Collect email 打开，success URL 填 `https://shuyuew1991.github.io/personal-page/thanks.html`。Payment Link 没有单独的 cancel URL；买家取消会回到链接页。
4. 把两个链接粘进 `payments.js` 的 `pdf` / `bundle`；页面上的 $12 / $29 要和 Stripe 的 price 一致，改价时两边一起改。
5. `sk_...`、`whsec_...` 只放服务端环境变量；`payments.js` 只放公开的 Payment Link。

当前 live 配置（2026-11-23）：

- Product：`prod_VgIcbdBMpl2zte`
- Price：`price_1Uew1UGA5UrdluwQ7EyhsfS4`（$12 PDF）、`price_1Uew1WGA5UrdluwQABvQABBN`（$29 supporter bundle）
- Payment Links：见 `payments.js` 的 `pdf` / `bundle`
- Alipay 已在默认 payment method configuration 里 `available: on`；结账页会同时显示银行卡和支付宝

## 访客统计

页脚不再显示「本页 / 全站」次数；统计仍由 GoatCounter 在每页计数。统计页 `stats.html` 可以直接打开（noindex）：总浏览、今日、最近 30 天、各页浏览、国家 / 地区。

本站代号 `shuyuew1991`，面板在 <https://shuyuew1991.goatcounter.com/>。统计由 [GoatCounter](https://www.goatcounter.com/) 完成：无 cookie、不保存 IP，只留汇总数字。统计页上的数字来自 CI 生成的 `_site/stats.json`，每 6 小时刷新一次；`stats.html` 是 noindex，不进 sitemap，页脚也不再提供计数入口。页面显示的是页面打开次数（同一人多次打开会重复计）；去重后的独立访客、来源网站和浏览器信息在 GoatCounter 面板里看。

### 接入（一次性）

1. 在 goatcounter.com 注册，站点代号（code）用比如 `shuyuew1991`（本站已注册）。
2. 打开 `prototypes/v2/b-desk/stats.js`，把顶部的 `GOATCOUNTER_SITE` 改成这个代号（本站已填 `shuyuew1991`）。
3. 在 GoatCounter 右上角的 **Preferences** 里把 Timezone 设为 `Asia/Shanghai`，这样「今日」按上海时间切。
4. GoatCounter → Settings → API → 新建 token，权限只给 **Read statistics**。
5. GitHub 仓库 → Settings → Secrets and variables → Actions → New repository secret，名字 `GOATCOUNTER_TOKEN`，值粘贴 token。
6. push 到 `main`，或手动跑一次 `Deploy site`。

没有 token 时站点照常发布，只是统计入口隐藏；接口出错时 CI 会失败、不部署，线上继续保留上一份数字。`stats.js` 里的代号留空则完全不统计。

本地想先看效果：

```bash
python3 build.py
cp tools/stats.example.json _site/stats.json   # 示例数据，只看版式
# 或：GOATCOUNTER_TOKEN=... python3 tools/stats_snapshot.py --out _site/stats.json
cd _site && python3 -m http.server 8123
```

不想统计自己：在浏览器打开一次 `站点#toggle-goatcounter`（count.js 的本地开关），或在 GoatCounter 设置里忽略自己的 IP。完整面板在 `https://<代号>.goatcounter.com/`。

`assets/goatcounter-count.js` 是 GoatCounter 官方的 `count.js`（ISC 许可），本地托管是为了不依赖 `gc.zgo.at` 的 CDN；升级时从 GoatCounter 仓库的 `public/count.v5.js` 取同名文件替换即可。

> 地点只到国家 / 地区一级，不含城市；GoatCounter 不采集到那么细。

## Initiatives

`initiatives.html` 用三张网站截图 + 项目说明做成三条现场记录：截图统一在左，说明在右；每项只借网站自己的一个颜色。截图在 `prototypes/v2/b-desk/assets/initiatives/`。

## 搜索收录

`robots.txt` 与 `sitemap.xml` 由 `build.py` 按静态页面白名单 + 注记清单现算，加页面或加注记都不用手工维护；地址统一取自 `build.py` 顶部的 `SITE_URL`。`stats.html` 和 `inbox.html` 在 `NOINDEX` 里，不写进 sitemap。

`prototypes/v2/b-desk/googlefa66aa447ffb8c98.html` 是 Google Search Console 的所有权验证文件，文件名和内容都别改，也别从白名单里删掉。

## 版权

© 2026 王舒悦（Shuyue Wang）。保留所有权利。
站内文字仅供阅读，未经书面许可不得转载、摘编或用于训练。
