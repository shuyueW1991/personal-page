# 参考与取舍

看了一些站点和书，最后没有做“笔记 / 语录 / 语言 / 活动”四个栏目，而是把它们压进同一条**页边**：日期在左，正文在中，出处、译文、地点在右。下面是参考，以及分别拿走了什么。

## 形式

| 参考 | 拿走的 | 没有拿的 |
|---|---|---|
| [Wittgenstein's Nachlass（卑尔根大学）](https://wab.uib.no/wab_nachlass.page/index.page) / [Notebooks 1914–1916](https://archive.org/details/notebooks191419100witt) | 日期、未完成、个人 remarks 与哲学 remarks 混在一起；不把每条都升格成文章。 | 手稿影印、编码、学术注释系统。 |
| [Lichtenberg, The Waste Books](https://www.nyrb.com/products/the-waste-books) | “废稿本”本身可以是一种书；碎片不是失败的长文。 | 格言式的机智表演。 |
| [Are.na](https://www.are.na/about) | 没有 feed / 算法 / like 数；把东西慢慢收进一个地方，让关系自己长出来。 | channel、block、社交层；这里只有一个人的账本。 |
| [XXIIVV](https://wiki.xxiivv.com/site/home.html) | 个人站可以同时是日记、索引和作品库；更新可以很慢。 | 密集的 wiki 导航和符号系统。 |
| [Kottke.org](https://kottke.org/quick-links/2023-01) | quick links / 短条目可以和长文章共处，不必另开一个“微博”。 | 每日更新节奏和链接博客的体量。 |

## 输入

| 参考 | 拿走的 | 没有拿的 |
|---|---|---|
| [Micro.blog](https://micro.blog/about) | 短帖和长文同一个站；手机端发布；自己的域名。 | 时间线、社区、跨平台转发。 |
| [Blot](https://blot.im/) | 把文件放进文件夹就发布；输入不该先经过一套 CMS。 | 完全依赖文件夹同步的发布方式。 |
| [flomo](https://flomoapp.com/) | 手机上“像发微信一样”记一句；不要求格式和分类。 | 标签、热力图、回顾统计。 |

## 技术路线

- 发布：一个私密 PWA（`compose.html` 的形态）+ iOS 分享菜单快捷指令；两者 POST 到同一个 serverless endpoint。
- 存储：endpoint 把一条 note 写成 Markdown（frontmatter 里存 `type / lang / source / translation / when / place / link`），提交到 Git。
- 构建：Vercel / Cloudflare Pages 监听 Git push，重新生成页边。
- 延迟：约 30–60 秒；前端立即回“已收”，不假装已经上线。
- 权限：私密 URL + token / passkey；只允许一个作者写入，不做公开注册。

这一轮只做了公开页面和输入界面的样张；发布接口还没接。
