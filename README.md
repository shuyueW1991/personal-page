# mynamewebesite

王舒悦的个人网站。纸底、索引式首页；小说、论文、技术、文章、页边各一页。

- 线上站点：`https://shuyuew1991.github.io/mynamewebesite/`
- 稿件、批注、中间版本和书稿全文**不在这个仓库里**，发布规则见 [PUBLISHING.md](PUBLISHING.md)。

## 结构

```
build.py                       白名单装配 _site/，CI 也用同一个脚本
prototypes/v2/b-desk/          上线页面（index / novel / papers / works / booklet / essay / quiet-tool / notes）
prototypes/v1、v3              旧方案，存档对照，不部署
vitrine/                       写作素材；其中小说与书稿已 gitignore，只留在本地
```

## 本地

```bash
python3 build.py                # → _site/（约 1 MB，21 个文件）
cd _site && python3 -m http.server 8123
```

`build.py --check` 只做校验：白名单文件齐全、页面引用的本地资源都存在、产物里没有稿件。

## 版权

© 2026 王舒悦（Shuyue Wang）。保留所有权利。
站内文字仅供阅读，未经书面许可不得转载、摘编或用于训练。

