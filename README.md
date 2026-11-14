# mynamewebesite

王舒悦的个人网站。近黑书封式的索引首页，四个入口；内页是纸底阅读版，`contact` 页集中邮箱、LinkedIn 与 GitHub。

- 线上站点：`https://shuyuew1991.github.io/wangshuyue/`
- 稿件、批注、中间版本和书稿全文**不在这个仓库里**，发布规则见 [PUBLISHING.md](PUBLISHING.md)。

## 首页

- 四类索引占满一屏，悬停整行反白；`ideology` 暂时空着，保留 01 的位置。
- 姓名缩到右下角；页脚列出 Shanghai / Bishkek / Petersburg / Paris / Tallinn / Jeju。
- 页脚 `contact` 指向 [contact.html](prototypes/v2/b-desk/contact.html)。
- 首页与联系页共用 `cover.css` / `cover.js`；分类页和文章页仍是纸底。

## 结构

```
build.py                       白名单装配 _site/，CI 也用同一个脚本
prototypes/v2/b-desk/          上线页面：封面首页 + contact + 三个分类页 + 内容页
prototypes/v1、v3              旧方案，存档对照，不部署
vitrine/                       写作素材；其中小说与书稿已 gitignore，只留在本地
```

## 本地

```bash
python3 build.py                # → _site/（约 1.1 MB，31 个文件）
cd _site && python3 -m http.server 8123
```

`build.py --check` 只做校验：白名单文件齐全、页面引用的本地资源都存在、产物里没有稿件。

## 版权

© 2026 王舒悦（Shuyue Wang）。保留所有权利。
站内文字仅供阅读，未经书面许可不得转载、摘编或用于训练。
