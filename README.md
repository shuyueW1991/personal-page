# personal page

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

`build.py --check` 只做校验：白名单文件齐全、页面引用的本地资源都存在、产物里没有稿件。

## 版权

© 2026 王舒悦（Shuyue Wang）。保留所有权利。
站内文字仅供阅读，未经书面许可不得转载、摘编或用于训练。
