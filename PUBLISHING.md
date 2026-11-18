# 发布与保密

仓库公开 = 站点公开。这是 GitHub Pages 免费版的前提，改不了。

所以这里划的线不是"文件加密"，而是**分清哪些东西本来就不该进公开仓库**：
公开的是"读过就能抄"的正文；不公开的是稿件、批注、中间版本和生成物。

## 仓库里有什么

| 进仓库 | 说明 |
|---|---|
| `prototypes/v2/b-desk/*.html`、`*.css`、`cover.js`、`stats.js`、`comments.js`、`post.js`、`inbox.js`、`favicon.svg`、`assets/` | 上线页面、样式、脚本、图标与图版（含 GoatCounter 的 count.js、KaTeX 的 CSS 与字体） |
| `vitrine/instrumentality-posts/` | 三篇公开注记的 markdown 原稿与图版源文件（图版均为 SVG） |
| `build.py` | 白名单装配 `_site/` |
| `tools/stats_snapshot.py` | 取 GoatCounter 汇总，写 `_site/stats.json` |
| `.github/workflows/pages.yml` | 构建 + 部署 |

## 仓库里没有什么

| 排除 | 为什么 |
|---|---|
| `vitrine/novel*/` | 小说各稿 docx/pdf、评论、语段库 |
| `vitrine/exegesis_of_diffusion/` | 书稿全文 md 与图版原图 |
| `*.docx *.doc *.pdf *.xlsx *.pdf …` | 按扩展名兜底，挪到哪儿都拦 |
| `_site/` | 构建产物，由 CI 现场生成 |

`.gitignore` 只影响 git，**不会删本地文件**，稿子照常放在原处。

## 三道闸

1. **`.gitignore` 按扩展名兜底** —— 不依赖目录名，以后把稿子挪到 `drafts/` 也拦得住。
2. **`build.py` 白名单** —— 只复制点名的那几个文件；另有 `FORBIDDEN` 正则，稿件和 `.py` 永远进不了 `_site/`。
3. **CI 再查一遍** —— workflow 里 `find _site -iname '*.docx' …`，命中就构建失败。

## 评论

整页评论走 [utterances](https://utteranc.es/)，每个作品页（含页边）一个 GitHub Issue，公开可读；发言要 GitHub 账号。页面默认不加载评论脚本，点「Load comments」才连 `utteranc.es`。

页边批注也走 GitHub Issues，但不经过 utterances：每一段一个 issue，标题是 `[margin] <page>#<anchor>`，正文开头是一段 base64 元数据（页码、锚点、引文）。锚点由段落文本的哈希生成，大段改写会让旧批注找不到原来的段落。点 `margin notes`、选中正文或从 `inbox.html` 进入时才请求 issue 列表；在批注框里点 **Post on GitHub** 会打开预填好的新 issue 页面，提交后回到文章刷新即可看到。`inbox.html` 从同一个 issue 列表里取待看项，勾掉只写本机 `localStorage`，不会关闭或删除 GitHub issue。

- 评论内容不经过本站，存在仓库 Issues 里，作者和读者都能删改自己的话。
- utterances App 只申请 Issues 权限；token 不进仓库，也不需要自己去建。页边批注只用公开的 issue 创建页，不需要额外 token。
- issue 是公开的：评论里写的东西等于公开，和正文一样要当心。

## 统计与密钥

访客统计只公开汇总数字：`_site/stats.json` 里有总浏览、各页次数、国家 / 地区和 30 天曲线，没有人、没有 IP、没有 cookie。

- token 只放在 GitHub Actions secret `GOATCOUNTER_TOKEN`，由 `tools/stats_snapshot.py` 从环境变量读取。
- token 不进仓库，也不进 `_site`；本地 `build.py` 生成的是 `enabled: false` 的占位。
- 统计接口出错时 snapshot 这一步失败，CI 就不部署，线上继续保留上一份数字。

## 验证

```bash
git ls-files | grep -Ei '\.(docx?|pdf|xlsx?|pyc)$' ; echo "exit=$?  (1 = 干净)"
git log --all --diff-filter=A --name-only | grep -Ei '\.docx?$'   # 应无输出
python3 build.py --check
```

`build.py` 还会检查评论：页面上有 `data-comments` 挂载点，就必须同时引用 `comments.css` 和 `comments.js`。页边批注页需要 `post.js`、`post.css`；`inbox.html` 在 `NOINDEX` 里。

要临时放行单个文件（例如以后真要公开一份 PDF），用 `git add -f 文件`。

## 第一次上线

1. 推到 `main`。
2. 仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。
   （workflow 里带了 `enablement: true`，通常第一次跑就会自动开；没开就手动点一下。）
3. 等 Action 变绿，站点地址：`https://shuyuew1991.github.io/personal-page/`
   所有链接都是相对路径，挂在子路径下不会坏。

之后每次 `git push` 到 `main` 自动重新发布；本地预览用 `python3 build.py && cd _site && python3 -m http.server`。

## 这套方案挡得住谁

- **挡得住**：顺手 clone 仓库找稿子的人、想拿"第三稿 → 第七稿"做对比研究的人、爬源码的脚本、搜索引擎。
- **挡不住**：打开页面选中正文复制的人、按 F12 看 HTML 的人。这是静态站的物理上限，不是配置问题。

要再往上加，只有三条路，代价依次升高：

| 做法 | 效果 | 代价 |
|---|---|---|
| 正文 AES-GCM 加密成 `.enc`，页面 WebCrypto 解密 | 挡住"文件看起来不像正文"的顺手党 | 密钥在 JS 里，几分钟可提取 |
| Cloudflare Worker 持钥 + 口令/邮箱 | 真访问控制 | 站点不再是公开站 |
| 每份副本嵌不可见指纹 | 泄露后能定位到人 | 需要分发不同副本 |

就"被抄袭"这个具体担心而言，最有效的是**指纹 + 时间锚定**（证明你先写的、
抄的人带着你的标记），不是加密。需要的时候再加。
