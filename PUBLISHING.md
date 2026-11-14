# 发布与保密

仓库公开 = 站点公开。这是 GitHub Pages 免费版的前提，改不了。

所以这里划的线不是"文件加密"，而是**分清哪些东西本来就不该进公开仓库**：
公开的是"读过就能抄"的正文；不公开的是稿件、批注、中间版本、构建脚本。

## 仓库里有什么

| 进仓库 | 说明 |
|---|---|
| `prototypes/v2/b-desk/*.html`、`*.css`、`assets/` | 上线页面、样式、图版 |
| `build.py` | 白名单装配 `_site/` |
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

## 验证

```bash
git ls-files | grep -Ei '\.(docx?|pdf|xlsx?|pyc)$' ; echo "exit=$?  (1 = 干净)"
git log --all --diff-filter=A --name-only | grep -Ei '\.docx?$'   # 应无输出
python3 build.py --check
```

要临时放行单个文件（例如以后真要公开一份 PDF），用 `git add -f 文件`。

## 第一次上线

1. 推到 `main`。
2. 仓库 **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。
   （workflow 里带了 `enablement: true`，通常第一次跑就会自动开；没开就手动点一下。）
3. 等 Action 变绿，站点地址：`https://shuyuew1991.github.io/mynamewebesite/`
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
