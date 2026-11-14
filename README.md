# personal page

王舒悦（Shuyue Wang）的个人网站：近黑书封式的索引首页，四个入口；内页是纸底阅读版，`contact` 页集中 LinkedIn、GitHub 与驻足过的城市。

- 线上站点：<https://shuyuew1991.github.io/personal-page/>
- 稿件、批注、中间版本和书稿全文**不在这个仓库里**，规则见 [PUBLISHING.md](PUBLISHING.md)。

## 结构

```
build.py                       白名单装配 _site/，CI 也用同一个脚本
prototypes/v2/b-desk/          上线页面：封面首页 + contact + 分类页 + 内容页
prototypes/v1、v3              旧方案，存档对照，不部署
vitrine/                       写作素材；其中小说与书稿已 gitignore，只留在本地
```

## 本地

```bash
python3 build.py                              # 生成 _site/
cd _site && python3 -m http.server 8123
```

`build.py --check` 只做校验：白名单文件齐全、页面引用的本地资源都存在、每页 canonical 正确、产物里没有稿件。

## 搜索收录

`robots.txt` 与 `sitemap.xml` 由 `build.py` 按 `PAGES` 现算，加页面不用手工维护；地址统一取自 `build.py` 顶部的 `SITE_URL`。

`prototypes/v2/b-desk/googlefa66aa447ffb8c98.html` 是 Google Search Console 的所有权验证文件，文件名和内容都别改，也别从白名单里删掉。

## 版权

© 2026 王舒悦（Shuyue Wang）。保留所有权利。
站内文字仅供阅读，未经书面许可不得转载、摘编或用于训练。
