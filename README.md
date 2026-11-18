# personal page

王舒悦（Shuyue Wang）的个人网站：近黑书封式的索引首页，四个入口；内页是纸底阅读版，`contact` 页集中 LinkedIn、GitHub 与驻足过的城市。

- 线上站点：<https://shuyuew1991.github.io/personal-page/>
- 稿件、批注、中间版本和书稿全文**不在这个仓库里**，规则见 [PUBLISHING.md](PUBLISHING.md)。

## 结构

```
build.py                       白名单装配 _site/，CI 也用同一个脚本
tools/stats_snapshot.py        CI 里把 GoatCounter 汇总成 _site/stats.json
prototypes/v2/b-desk/          上线页面：封面首页 + contact + 分类页 + 内容页 + 注记 + inbox + stats
prototypes/v2/b-desk/assets/   图版与 KaTeX；count.js 是 GoatCounter 官方脚本（ISC）
prototypes/v1、v3              旧方案，存档对照，不部署
vitrine/                       写作素材；instrumentality-posts/ 是注记原稿；小说与书稿已 gitignore
```

## 本地

```bash
python3 build.py                              # 生成 _site/
cd _site && python3 -m http.server 8123
```

`build.py --check` 只做校验：白名单文件齐全、页面引用的本地资源都存在、每页 canonical 正确、每页都挂上了统计。真正构建时还会再扫一遍 `_site/`，确认里面没有稿件。

`build.py` 会在 `_site/stats.json` 写一个 `enabled: false` 的占位。没有真实快照时，页脚的统计入口保持隐藏——这是正常的，不是缓存问题。

## 注记与评论

`instrumentality.html` 分成 note / book / papers 三栏：三篇注记、一本书、论文与专利索引。三个 note 的页面：

- [`front-focal-magnification.html`](https://shuyuew1991.github.io/personal-page/front-focal-magnification.html) —— 前焦点处的横向放大率（2026.11.18）
- [`optical-power.html`](https://shuyuew1991.github.io/personal-page/optical-power.html) —— Optical Power and Focal Length（2026.11.17）
- [`clean-dwg.html`](https://shuyuew1991.github.io/personal-page/clean-dwg.html) —— 让 DXF 成为可被脚本干净解析的电气连接图（2026.11.12）

原稿在 `vitrine/instrumentality-posts/`，页面上的 HTML 就是成品。两篇物理注记的公式在生成时用 [KaTeX](https://katex.org/) 预先排成 HTML + MathML，页面本身不加载公式脚本；`prototypes/v2/b-desk/assets/katex/` 只留 CSS 和 woff2 字体（MIT，见同目录 `LICENSE`），不依赖 CDN。改公式要重新用 KaTeX 排版，改普通文字直接改 HTML 即可。

注记页是两栏：正文占页宽 2/3，右侧是一张随滚动固定的阅读桌。桌面上半是图板或草图 canvas（图可点开看原尺寸，草图可导出 SVG），下半是页边批注；正文右边一条 34px 刻度栏把段落和批注对应起来。选中正文、点刻度，或从 inbox 进来，都会在阅读桌里打开对应段落的批注编辑/评论。

每个作品页（小说、文章、书、论文、三篇注记）和页边（`notes.html`）底部都有 page comments 区块。默认只显示一个按钮，点开后才向 `utteranc.es` 请求评论框；页边批注也只在点 `margin notes`、选中正文或从 inbox 进入时才向 GitHub 请求。普通打开文章时不向 GitHub 发任何请求。page comments 一页一个 issue，按 pathname 关联；页边批注则一段一个 issue，标题是 `[margin] <page>#<anchor>`，正文开头带一段 base64 元数据（页码、锚点、引文）。锚点由段落文本的哈希生成；大段改写会让旧批注找不到原来的段落。

第一次发言前要在仓库上装一次 [utterances App](https://github.com/apps/utterances)，并确认仓库 **Settings → General → Features → Issues** 已开启。没装 app 时评论框能出现，但提交会失败，页面其他部分不受影响。

- 配置（repo、label、theme）在 `prototypes/v2/b-desk/comments.js` 顶部
- 样式在 `comments.css`，评论区骨架直接写在各页面里（`data-comments`）
- 页边批注的交互在 `post.js`，样式在 `post.css`；issue 的创建链接会打开 GitHub 的新 issue 页面，提交后回到文章即刷新
- 不登录也能读；发言要 GitHub 账号。issue 是公开的，别在评论里留隐私
- 首页页脚的 `comments` 入口进 `inbox.html`：只列未看过的页边批注，点一行跳到对应段落，勾掉即从本机队列移除；同一 issue 之后有新回复会重新出现
- `inbox.html` 是 `noindex`，不进 sitemap；队列状态只存在浏览器 `localStorage`

## 访客统计

每页页脚都有一个很小的入口：首页显示全站总浏览，内页显示「本页 / 全站」，点进去是 `stats.html`：总浏览、今日、最近 30 天、各页浏览、国家 / 地区。

本站代号 `shuyuew1991`，面板在 <https://shuyuew1991.goatcounter.com/>。统计由 [GoatCounter](https://www.goatcounter.com/) 完成：无 cookie、不保存 IP，只留汇总数字。页面上的数字来自 CI 生成的 `_site/stats.json`，每 6 小时刷新一次；`stats.html` 是 noindex，不进 sitemap。页面显示的是页面打开次数（同一人多次打开会重复计）；去重后的独立访客、来源网站和浏览器信息在 GoatCounter 面板里看。

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

## 搜索收录

`robots.txt` 与 `sitemap.xml` 由 `build.py` 按 `PAGES` 现算，加页面不用手工维护；地址统一取自 `build.py` 顶部的 `SITE_URL`。`stats.html` 和 `inbox.html` 在 `NOINDEX` 里，不写进 sitemap。

`prototypes/v2/b-desk/googlefa66aa447ffb8c98.html` 是 Google Search Console 的所有权验证文件，文件名和内容都别改，也别从白名单里删掉。

## 版权

© 2026 王舒悦（Shuyue Wang）。保留所有权利。
站内文字仅供阅读，未经书面许可不得转载、摘编或用于训练。
