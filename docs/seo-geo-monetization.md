# SEO / GEO / 商业化工作底稿

> 日期：2026-11-23 · 范围：`shuyuew1991.github.io/personal-page` 现状与下一步
>
> 这是一份工作底稿，不是法律意见。平台费率、可售品类、税务和出版资质以各平台/专业人士的当前口径为准。

## 0. 一句话结论

- **书页现在不到 200 个词，四章正文没有上线。** 这是 SEO/GEO 的第一瓶颈；标签可以优化，但没有可索引的内容，排名和 AI 引用都无从谈起。
- **商业化不要做“站内硬 paywall”。** GitHub Pages 是静态公开站，正文挡不住；正确姿势是“免费 HTML 做入口，付费 PDF/代码/课程/企业培训放托管平台”。
- **假评论、假争执不做。** 它同时踩虚假宣传、平台条款和学术信誉三条线；用真实早期读者、公开勘误、读者来信、真实争论题替代。

## 1. 现状审计

我检查了源页面、`build.py`、`_site/`、`.github/workflows/pages.yml` 和书稿目录。

| 项目 | 现状 | 影响 | 优先级 |
|---|---|---|---|
| 书页内容量 | `exegesis.html` 约 188 词：标题、4 张图版、2 段序言、5 行章节名 | 没有可索引正文；长尾词、AI 引用都没有抓手 | **P0** |
| 书稿 | `vitrine/exegesis_of_diffusion/` 约 120 KB，已被 `.gitignore` 排除，当前仓库历史里没有 | IP 安全；但站上没有任何章节内容 | **P0 决策** |
| 章节结构 | 章节名是 `<span>`，不是标题也不是链接；没有章节页 | 搜索引擎读不出目录层级；用户无法深读 | **P0** |
| 结构化数据 | 只有首页有 `Person` JSON-LD；书页、小说页都没有 `Book`/`Chapter`/`FAQ`/`Breadcrumb` | 实体理解弱；AI 难以判断“这是一本书” | **P0** |
| OG / Twitter | 内页大多只有 `og:url`；没有 `og:image`、`og:title`、`og:description`、Twitter card | 社交分享和 AI 预览缺少封面/摘要 | **P1** |
| 标题/描述 | 书页标题混用中文名；描述是 `Preface, four chapters, four plates.`；小说描述只有一句 | 点击率和相关性都吃亏 | **P0** |
| 作者实体 | ORCID 在 `papers.html` 里有；`Person.sameAs` 只有 LinkedIn/GitHub；Google Scholar 是搜索链接，不是个人主页 | E-E-A-T 信号不足 | **P1** |
| Sitemap / robots | 18 个 URL；无 `lastmod`；`robots.txt` 全放行；无 `llms.txt`、无 RSS | 收录和新鲜度信号一般 | **P1** |
| 域名 | `github.io/personal-page/` 子路径 | 域名信任、URL 长度、引用美观度都吃亏 | **P2** |
| 小说状态 | 约 3.2 万字全文公开、在 sitemap 里、可被索引；页面标着“未刊稿 请勿转载” | “公开全文”和“未刊稿/要商业化”是矛盾的；可能影响首发权 | **P0 决策** |
| 评论 | utterances，需 GitHub 登录，默认折叠 | 中文读者参与门槛高；互动数据少 | **P2** |
| 统计 | GoatCounter 只记页面打开；没有购买点击/邮件订阅等转化事件 | 无法判断商业化漏斗 | **P1** |
| 图片 | 4 张 1024×1024 JPG，147–289 KB；CSS 有 `aspect-ratio` | 目前可接受；可转 WebP/AVIF 再省一点 | **P2** |
| 内链 | `instrumentality.html` → `exegesis.html` 已有；书页 → 作者/论文/术语表没有 |  topical cluster 没形成 | **P1** |
| 构建 | 白名单 + `FORBIDDEN` 扩展名 + canonical 校验 + CI 二次检查 | 机制是好的，继续保持 | — |

## 2. SEO / GEO 路线图

### 2.1 先明确一件事：GEO 不是“给 AI 看的关键词”

GEO（Generative Engine Optimization）目前没有统一标准。能稳定起作用的东西还是老几样：

1. **AI 能抓到**：静态 HTML、服务端可读、不被 `robots.txt` 挡、不被 JS 门禁挡。
2. **AI 能读懂**：清楚的标题层级、问题式小标题、定义、列表、表格、每段自包含。
3. **AI 愿意引用**：作者可信、日期/版本清楚、有原始来源、有独特数据或例子、可被引用（citation / DOI / BibTeX）。

所以书页的第一优先级不是加 meta，而是**让它有真正的、可被引用的内容**。

### 2.2 P0：本周就能做（不改正文）

#### A. 把书页改成真正的落地页

建议在 `exegesis.html` 现有图版和序言之后，按这个顺序加：

1. **作者与版本**：`Shuyue Wang（王舒悦）`、ORCID 链接、`2026 · v1.0`、`Last updated`。
2. **一句话定位**：这本书解决什么问题、和别的教程有什么不同。
3. **适合谁 / 需要什么基础**：3–5 条，写给研究生、工程师、转行者。
4. **章节目录**：把 5 行 `<span>` 改成 `<h2>`/`<a>`；每章下面加 80–120 词摘要（自己写，不抄书稿）。
5. **读完能得到什么**：5 条具体能力，不要空话。
6. **FAQ**：6–8 个真实问题，每个 40–80 词。示例：
   - 这本书和 Lilian Weng / Hugging Face 的教程有什么不同？
   - 需要什么数学基础？
   - 为什么从高维几何讲起？
   - ELBO 和 score matching 是什么关系？
   - 有没有代码？
   - 更新/勘误怎么处理？
7. **引用格式**：BibTeX + 一行 plain text。
8. **CTA**：`Read the free preface` / `Get the PDF` / `For teams`（没有链接就先不放，别放死链）。

#### B. 标题和描述

书页：

```html
<title>A Preliminary Mathematical Exegesis of Diffusion Models — Shuyue Wang</title>
<meta name="description" content="A rigorous, intuition-first book on diffusion models: high-dimensional data, the ELBO, score-based SDEs, Fokker–Planck, and implementation. By Shuyue Wang.">
```

小说页：

```html
<title>青年讲师 — M·贺六浑（王舒悦）</title>
<meta name="description" content="一部关于高校学术生态的长篇小说：青年教师辛子杰与警察 Z 的故事。M·贺六浑著，约 3.2 万字。">
```

#### C. 结构化数据

书页加 `Book` + `Person` + `BreadcrumbList`；有 FAQ 再加 `FAQPage`。最小可用版本：

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Book",
  "name": "A Preliminary Mathematical Exegesis of Diffusion Models",
  "alternateName": "Gaining Clarity From True Understanding",
  "url": "https://shuyuew1991.github.io/personal-page/exegesis.html",
  "image": "https://shuyuew1991.github.io/personal-page/assets/plate-01.jpg",
  "inLanguage": "en",
  "bookFormat": "https://schema.org/EBook",
  "author": {
    "@type": "Person",
    "name": "Shuyue Wang",
    "alternateName": "王舒悦",
    "url": "https://shuyuew1991.github.io/personal-page/",
    "sameAs": [
      "https://orcid.org/0000-0001-8452-5602",
      "https://www.linkedin.com/in/shuyuew1991/",
      "https://github.com/shuyueW1991"
    ]
  },
  "about": [
    { "@type": "Thing", "name": "Diffusion models" },
    { "@type": "Thing", "name": "Generative AI" },
    { "@type": "Thing", "name": "Evidence lower bound" },
    { "@type": "Thing", "name": "Score-based generative modeling" },
    { "@type": "Thing", "name": "Stochastic differential equations" }
  ],
  "abstract": "A mathematical, intuition-first treatment of diffusion models, from the high-dimensional structure of natural images to the ELBO, score-based SDEs, Fokker–Planck dynamics, and implementation.",
  "copyrightHolder": { "@type": "Person", "name": "Shuyue Wang" },
  "copyrightYear": 2026
}
</script>
```

小说页加 `Book`（或 `CreativeWork`），`author` 用笔名，`inLanguage: "zh-Hans"`，`genre`、`wordCount`、`copyrightNotice`。不要为了 schema 把笔名和真名强行合并；如果不想公开关联，就只写笔名。

#### D. OG / Twitter

至少给书页和小说的页加上：

```html
<meta property="og:title" content="…">
<meta property="og:description" content="…">
<meta property="og:type" content="book">
<meta property="og:image" content="https://…/assets/og-book.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="…">
<meta name="twitter:description" content="…">
<meta name="twitter:image" content="https://…/assets/og-book.jpg">
```

`og-book.jpg` 可以用 `plate-01.jpg` 裁一张 1200×630，压到 200 KB 以内。不要直接把 1024×1024 方图当 OG 图，微信/LinkedIn 会裁得很难看。

#### E. 收录

- Google Search Console：提交 sitemap，对书页/小说页请求编入索引；看 `Coverage` 里“已抓取但未编入索引”的原因。
- Bing Webmaster：提交 sitemap；Bing 的 IndexNow 也可以接，但需要 key 文件和 CI 调用。
- 确认 `googlefa66aa447ffb8c98.html` 还在，别动。

#### F. 内链

- `instrumentality.html` 的 book shelf 已经链到书页，保留。
- 书页加“作者”链接到 `papers.html` / `contact.html`，加“相关注记”链接到 `instrumentality.html`。
- 小说页加“更多小说”到 `illusion.html`，加“支持作者”（等付费入口上线再加）。
- 首页不必动；两层深度对 SEO 没问题。

### 2.3 P1：两周内

1. **样章/章节页决策**（见 §2.5）。每个章节页一个 URL，`h1`、摘要、`Key idea`、上一章/下一章、canonical、`Chapter` schema、CTA。
2. **术语表**：20–30 个词，每个 40–80 词，链回章节。这是 GEO 最容易被引用的形态。
   - ELBO、KL divergence、score function、Fokker–Planck、SDE、DDPM、DDIM、latent diffusion、classifier-free guidance、variance schedule、reparameterization、ELBO gap……
3. **勘误 / 开放问题页**：用 GitHub Issues 承载；每条写清楚“原文、问题、修正”。这是真实争论的入口，不是假争执。
4. **Zenodo DOI**：上传 PDF 或只上传 metadata，拿一个 DOI；书页加 `Cite this book`。DOI 对学术引用和 AI 判断“这是正式作品”都有帮助。
5. **作者实体**：建 Google Scholar 个人主页（现在只是搜索链接）；把 ORCID、Scholar、LinkedIn、GitHub 写进 `Person.sameAs` 和 `contact.html`；加 `rel="me"`。
6. **自定义域名**：`shuyuewang.com` / `wangshuyue.com` 之类。GitHub Pages 可以绑，但旧 `github.io` URL 的 301 需要 Cloudflare/Netlify 规则；如果决定搬，越早越好。
7. **RSS / llms.txt**：
   - RSS 给注记做 `feed.xml`，方便订阅和聚合。
   - `llms.txt` 是提案，不是标准；低成本可加，但别指望所有 AI 都读。
8. **AI 爬虫策略**：现在 `robots.txt` 全放行，但页脚写“不得用于训练”，两者不一致。三选一：
   - **全放行**：最大曝光，放弃训练控制。
   - **允许搜索/问答爬虫，拒绝纯训练爬虫**：例如允许 `OAI-SearchBot`、`PerplexityBot`、`ChatGPT-User`、`Claude-SearchBot`，拒绝 `GPTBot`、`Google-Extended`、`CCBot`、`ClaudeBot`、`Applebot-Extended`、`meta-externalagent`。具体 UA 以各公司最新文档为准。
   - **全拒绝**：放弃 GEO，只做传统搜索/直接访问。
   
   无论选哪个，都在书页/页脚写清楚许可范围；`robots.txt` 不是法律合同，不能真正阻止训练，但能表达意愿。

### 2.4 P2：持续

- **外链**：LinkedIn、GitHub README、知乎、Medium/Substack、Hacker News、Reddit（r/MachineLearning 的 self-promo 帖、r/learnmachinelearning、r/diffusionmodels）、AI newsletter、播客、课程书单、`awesome-diffusion-models` 类仓库。
- **客座/访谈**：比自推更有效；每篇都链回书页。
- **会议/meetup**：把书的内容讲成 30 分钟 talk；视频和 slides 都是外链。
- **监测 AI 引用**：每月用固定问题问 ChatGPT/Perplexity/Gemini/Copilot，记录是否引用书页；看 GoatCounter 里 `chatgpt.com`、`perplexity.ai`、`gemini.google.com` 等 referrer。
- **季度刷新**：更新日期、勘误、版本号；AI 和搜索都偏好新鲜内容。

### 2.5 关键决策：书稿要不要上线

这是 SEO 和商业化之间最大的取舍。

| 方案 | SEO/GEO | IP/商业化 | 建议 |
|---|---|---|---|
| A. 全书 HTML 公开 | 最强 | 书稿全文公开，PDF 付费理由变弱 | 只在“书是引流品，钱在培训/课程”时选 |
| B. 序言 + 1 章样章 | 强 | 保留大部分正文；样章可引流 | **最平衡，推荐** |
| C. 每章 300–500 词摘要 | 中 | 不暴露正文；能覆盖长尾词 | 不想上线正文时的最低方案 |
| D. 只有现在的 188 词 | 很弱 | 最安全 | 不适合把 SEO 当目标 |

如果选 B，建议公开 `Preface` + `Chapter I`，并在样章末尾放“完整版 PDF / 后续章节”的 CTA。样章本身要能独立回答几个问题，不然 AI 不会引用。

## 3. 商业化

### 3.1 现实判断

 diffusion 教程的免费供给非常强：Lilian Weng、Hugging Face、arXiv、YouTube、各类博客。一本短书的**直接销售收入大概率有限**。这本书真正的商业价值是：

1. **作者权威**：证明你能把 diffusion 的数学讲清楚。
2. **企业培训/咨询的敲门砖**：序言里已经提到在 Emzan Technology / autoslide.cc 做过讲座，这条线比卖 PDF 更值钱。
3. **课程/社群的入口**：书是免费的，陪跑和答疑是付费的。

所以产品阶梯应该是“书 → 代码/课程 → 企业培训”，而不是“书 → 更多书”。

### 3.2 产品阶梯（测试价）

| 产品 | 价格测试 | 交付 | 作用 |
|---|---|---|---|
| 免费 HTML / 样章 | 0 | 站内 | SEO/GEO 入口 |
| PDF / EPUB | $9.99–19.99 / ¥39–69 | Gumroad、Leanpub、面包多 | convenience + 支持作者 |
| PDF + 代码/习题 | $29–49 / ¥99–169 | 同上 | 提高客单 |
| 小班/office hours | $99–199 / ¥399–799 | Zoom | 验证需求、收集真实反馈 |
| 企业工作坊 | $1.5k–5k/天 / ¥1–3 万/天 | 定制 | 主要收入 |
| 赞助 | 按受众规模谈 | newsletter/书页 | 有流量后再做 |
| 翻译/授权 | 按合同 | 出版社 | 长期 |

价格是测试价，不是定价建议；先卖 20 份，看退款和反馈再调。

### 3.3 平台选择

**国际（英文书）**

- **Lemon Squeezy**：MoR，数字商品、license key、VAT 处理；适合 solo author。
- **Gumroad**：最简单，适合有受众后直接挂；费率/付款方式以官网为准。
- **Leanpub**：技术书专用，PDF/EPUB、更新、pay-what-you-want；和这本书的形态很匹配。
- **Paddle**：MoR，偏 SaaS；数字书也能用。
- **Payhip / Ko-fi**：轻量；Ko-fi 适合打赏。

**中国（中文小说/中文版）**

- **爱发电**：赞助、会员、付费内容；微信/支付宝；适合“支持作者”和连载。
- **面包多**：数字商品；微信/支付宝；可售品类和资质需确认。
- **小报童**：付费专栏/newsletter；适合把“书 + 更新 + 问答”打包。
- **知识星球**：付费社群；适合读书会/答疑。
- **豆瓣阅读 / 知乎盐选**：小说平台；有审稿和分成。
- **微信公众号付费阅读**：有开通门槛，不适合作为唯一渠道。

**支付现实**

- 你已经有 rurussian 的 Stripe 账户，可以直接在同一个账户下建书的产品；不需要重新开户。
- Stripe 的 Alipay 是否可用取决于账户所在地/币种；美国、英国、香港、新加坡等账户通常能看到（以 Dashboard 为准）。
- 大陆个人主体通常开不了 Stripe；如果你没有境外主体，用 MoR 平台或国内平台，别自己接信用卡。
- 不管哪个平台，**不要在自己的静态站上收集卡号**。

### 3.4 静态站怎么接付费

1. **托管结账**：书页放 `Get the PDF` 按钮，跳到 Gumroad/Leanpub/面包多；支付、发票、退款、文件分发都由平台做。
2. **付费文件不要进仓库/`_site`**：`build.py` 的 `FORBIDDEN` 会拦 PDF，但文本/图片仍可能漏；付费内容只放平台。
3. **License**：个人使用、不可转售/再分发；PDF 里写清楚。
4. **退款/隐私/条款**：至少三页；数字商品下载后的退款政策要写明。
5. **邮件列表**：Buttondown/Substack/MailerLite；国内可用小报童/公众号。书页放一个“Get updates”入口。
6. **转化追踪**：给购买链接加 UTM；GoatCounter 支持出站/事件追踪的用法以其文档为准；至少能看到“点击购买”与“页面浏览”的比例。
7. **Product/Offer schema**：只有在你真的展示价格、且有退款/条款页时才加；否则别加。

### 3.4.1 复用 rurussian 的 Stripe 账户（具体接法）

我看了 `aliladder/remote/litelanglearn` 的配置：Stripe 是 Python daemon + Next.js 前端，`CHECKOUT_PLANS` 里是 `month_1` / `year_1` / `year_3` 三个订阅价，`payment_method_types=['card']`。这套代码不适合直接搬给书：

- 书是**一次性数字商品**，不是订阅；不要往 `rurussian_users` 表里塞买书的人。
- `personal-page` 是纯静态站，没有 Python daemon，不能直接调 `create_checkout_session`。
- 正确做法是**同一个 Stripe 账户下新建产品 + 一次性 Price + Payment Link**，和 rurussian 的订阅产品分开。

具体步骤：

1. **建产品**：Stripe Dashboard → Product catalog → 新建 `A Preliminary Mathematical Exegesis of Diffusion Models`，建两个 one-time price：
   - `PDF / EPUB`：$12（测试价）
   - `PDF + code + updates`：$29（测试价）
2. **开 Alipay**：Settings → Payment methods → Alipay。Stripe 的 Alipay 对商家所在地/币种有要求（美国、英国、香港、新加坡等可用；以 Dashboard 是否显示为准）。如果看不到，联系 Stripe Support；如果账户不符合，走国内平台，不要硬接。
3. **建 Payment Link**：每个 price 建一个 link，开启“Collect email”，success URL 指到 `thanks.html`，cancel URL 回 `exegesis.html`。Payment Link 同时支持卡和 Alipay（如果已启用）。
4. **交付**：
   - MVP：付款后 Stripe 发收据，你 24 小时内手动邮件发 PDF；先卖 20 份验证需求。
   - 自动化：Stripe webhook → Cloudflare Worker / Vercel Function → 写订单 + 发带签名/有效期的下载链接；或者用 Zapier/Make 触发邮件。
   - 不要用“付款后跳到一个公开 PDF 链接”的做法；链接会被转发。
5. **合规**：Stripe 的 Alipay 要求网站公开可访问、清楚展示商品/价格/交付条款/退款政策。书页在开卖前要补这几块，否则审核可能不过。
6. **密钥**：`sk_...` 只放服务端（Worker/Function 的环境变量），永远不进 `personal-page` 的 HTML/JS；`price_id` 和 Payment Link 是公开的，可以放页面。

**关于附图的支付宝收款码**

这张是**个人收款码**（`henri(**悦)`），不是商户收单产品。我的建议：

- **只放在“打赏/支持”里**，写明“自愿打赏，不是购买，不对应任何商品交付”。
- **不要放进书的购买流程**：没有订单号、没有自动交付、没有退款凭证；买家付了之后只能靠截图/邮件人工核对，容易起纠纷，也可能触发支付宝的风控/个人码商用限制。
- **商品收款**用 Stripe Alipay（如果开了）或面包多/爱发电（它们代收支付宝并处理交付/退款）。
- 这张图里有头像和部分姓名；公开到站上等于公开这些信息。建议在支付宝里换一张**不含个人照片、昵称中性**的收款码，或者用商户码；你确认可以公开我再放。
- 如果坚持用个人码卖书：页面必须写清“扫码后请把截图发到邮箱，24 小时内人工发 PDF”，并说明退款规则；这是人工流程，不适合规模化。

### 3.5 发布节奏

- **预发布（2–4 周）**：每周一篇样章/摘要；收集邮件；在 LinkedIn/知乎发“我在写一本什么样的书”。
- **发布周**：早期读者 30–50% 折扣，换取诚实反馈（披露“收到免费副本”）；同时发 HN/Reddit/newsletters。
- **发布后**：把真实反馈做成 testimonials（要授权）；更新勘误；每季度发一次“更新日志”。
- **打包**：PDF + 代码 + 更新 = 中档；PDF + 课程/office hours = 高档。

### 3.6 小说怎么商业化

先做一个决定：**这本小说是“免费名片”还是“要卖的作品”**。

- **免费名片**：保留全文，加 metadata、内容警告、作者简介、打赏入口；用它积累读者，卖下一部/特别版。
- **要卖的作品**：把全文从公开站撤下或 `noindex`，只留 2–3 章样章；投豆瓣阅读/知乎盐选/出版社/文学期刊。注意：全文公开可能被视为“已发表”，影响首发权；投稿前先确认。
- **付费特别版**：注释版、删节章、作者手记、创作谈、续篇抢先看。不要只是把免费全文打包成 EPUB 卖——读者会觉得被割。
- **平台**：豆瓣阅读（文学向）、知乎盐选（故事向）、爱发电/面包多（自出版）、传统出版社/文学期刊。
- **法务**：小说涉及学术圈、暴力、性、以及可被映射的现实机构；加“人物/机构/事件均为虚构”的免责声明；商业发布前找律师看一遍诽谤/隐私风险；做作品登记或时间戳。

### 3.7 法务/税务清单

- 中国：电子出版物/网络出版、ISBN、出版物经营许可证——自售和平台代售的责任不同，别假设“平台卖 = 我没事”。
- 税务：收入类型、发票、增值税；平台代扣/代缴规则。
- 隐私政策、服务条款、退款政策。
- 版权登记/时间戳；侵权投诉/下架流程。
- 小说：虚构声明、内容警告、真实人物/机构映射审查。
- 书：引用他人论文/图片的授权；图版是 AI 生成/购买的，确认商用许可。

**密钥安全（我检查到的）**

- `aliladder/remote/litelanglearn/.env.local` 和 `.env.local.live.bak` 里有 `STRIPE_WEBHOOK_SECRET`；`.gitignore` 覆盖了 `.env.*`，`git ls-files` 里也没有，当前 git 历史里没搜到 `whsec_`/`sk_live_`/`sk_test_` 的提交记录。
- 但这两个文件是明文本地文件；如果这个目录被压缩、共享、上传网盘，或者在别的机器上同步过，建议到 Stripe Dashboard **roll/rotate webhook secret**，并确认 `.stripe_secret_key` 也没有离开本机。
- 以后 `personal-page` 只放公开的 `price_id` / Payment Link；`sk_...`、`whsec_...` 只放 Worker/Function 的环境变量。

## 4. 假评论 / 假争执：不做

### 4.1 为什么不做

这不是“运营灰色技巧”，是**虚假宣传/刷单炒信**，而且很容易被拆穿。

| 层面 | 具体风险 |
|---|---|
| 中国法 | 《反不正当竞争法》第八条禁止对用户评价等作虚假/引人误解的商业宣传；《电子商务法》第十七条禁止虚构交易、编造用户评价；《消费者权益保护法》第二十条要求真实全面信息；《网络信息内容生态治理规定》禁止流量造假、操纵账号 |
| 美国 | FTC 2024 年消费者评论与推荐规则（16 CFR Part 465）禁止买卖评论、虚假评论、内部评论等；违反会有民事罚款 |
| 欧盟 | UCPD 附件一明确禁止提交/委托虚假评论、操纵评论；DSA 也有相关透明度义务 |
| 平台 | GitHub Acceptable Use Policy 禁止垃圾信息和虚假账号；utterances 的评论就是 GitHub Issues，账号、时间、历史都可查 |
| 信誉 | 你的读者是学术/工程圈；伪造被发现一次，书和作者的可信度一起归零，商业化只会更难 |
| 反噬 | 假争执会引来真争议；你很难控制走向，最后可能变成公关危机 |

### 4.2 可以做真的

| 替代做法 | 怎么做 | 注意 |
|---|---|---|
| 早期读者计划 | 招 5–10 个真实读者，送 PDF，换诚实反馈 | 披露“收到免费副本”；不要指定好评 |
| 真实推荐语 | 只采真实读者/同行，署名+身份 | 不要代写；不要用“匿名用户”编 |
| 勘误/找茬页 | 公开邀请读者挑数学错误；每条给回应和修正 | 这是真实争论，而且对书的质量有好处 |
| 读者来信 | 经授权摘录邮件/评论，配“读者原话” | 匿名要征得同意；不要改意思 |
| 公开问答 | 收集真实问题，书页做 FAQ / 直播答疑 | 问题来自读者，不是自问自答 |
| 读书会 | 每月一次，公开报名；录播/笔记 | 真实互动会产生真实讨论 |
| 真实指标 | 下载数、GitHub star、DOI 引用、邮件订阅数 | 只有真实才放；不要买量 |
| 测试/投票 | 问读者“下一章想先看什么” | 结果真实展示 |

### 4.3 真实的争论题（不是假争执）

书：

- ELBO 到底是“目标函数”还是“代理目标”？书里的 framing 和主流教程有什么不同？
- 从高维几何讲起，是必要的，还是绕远了？
- SDE/Fokker–Planck 视角对做工程的人有没有实际收益？
- score matching 和 ELBO 的等价性，应该在第一章讲还是第三章讲？
- 代码应该用 PyTorch 还是 JAX？

小说：

- 学术圈的“宫廷化”是结构问题还是个人问题？
- 辛子杰的复仇幻想，是批判还是共谋？
- Z 的职业暴力与亲密关系，怎么写才不浪漫化？
- 结尾的“光柱”是救赎还是逃避？

这些是作品本身的问题，邀请读者回答，比伪造对立更有参与感。

### 4.4 如果要在页面上写“社会证明”

只用这三种：

1. **真实读者的话**：姓名/ID + 身份 + 授权；送过书就写“收到赠书”。
2. **真实数字**：下载数、订阅数、引用数；注明统计口径和时间。
3. **真实机构/事件**：上过的课、做过的讲座、合作过的团队；对方允许再写。

不要写：编造的销量、编造的“读者说”、编造的“业内热议”、编造的“某大厂内部推荐”。

## 5. 30 / 60 / 90 天

**第 1–2 周**

- 书页落地页化（作者、版本、章节目录、摘要、FAQ、引用）。
- `Book`/`Person`/`Breadcrumb`/`FAQ` schema；OG 图；标题/描述。
- 小说 metadata + 虚构声明 + 内容警告。
- GSC/Bing 提交；请求编入索引。

**第 3–4 周**

- 决定样章方案；上线序言 + 第一章（或章节摘要）。
- 术语表第一版（15 个词）。
- 勘误页 + GitHub Issue 模板。
- 邮件列表入口。

**第 2 个月**

- Zenodo DOI；Google Scholar 主页；`sameAs` 补全。
- 自定义域名决策/迁移。
- PDF/EPUB 制作；Leanpub/Gumroad 上架；定价测试。
- 2–3 篇外链文章/知乎/Medium；1 次读书会或直播。

**第 3 个月**

- 企业培训 one-pager + `For teams` 页面。
- 小班/office hours 试点。
- 复盘：搜索词、AI 引用、邮件订阅、购买点击、退款、真实反馈。
- 决定是否扩大付费产品，还是把书继续当引流品。

## 6. 指标

| 层级 | 指标 | 工具 |
|---|---|---|
| 可见性 | GSC 曝光/点击/平均排名；收录页数 | Google Search Console |
| AI | ChatGPT/Perplexity/Gemini 引用次数；AI referrer | 手动抽查 + GoatCounter |
| 站内 | 书页浏览、样章浏览、停留/滚动 | GoatCounter（可加事件） |
| 线索 | 邮件订阅数、`For teams` 咨询数 | 邮件平台/表单 |
| 转化 | 购买点击、购买数、客单、退款率 | 平台后台 + UTM |
| 口碑 | 真实推荐语、勘误数、GitHub star | 手动/平台 |

## 7. 需要你决定的事

1. **书稿上线到什么程度？** 全书 / 序言+1 章 / 每章摘要 / 保持现状。
2. **小说是免费名片还是要卖？** 决定是否 `noindex`/撤全文。
3. **支付平台**：国际走 Lemon Squeezy/Gumroad/Leanpub，国内走爱发电/面包多/小报童？
4. **自定义域名**：现在换，还是继续 `github.io`？
5. **AI 爬虫策略**：全放行 / 只允许搜索问答 / 全拒绝？
6. **要不要我直接做 P0 的技术改动？**（metadata、schema、OG、书页结构、内链；不碰正文和付费链接）

## 8. 备注

- 这本书的免费竞品很强；不要用“SEO 技巧”去补内容的不足，先把书页做成一个真正有用的资源页。
- 任何“快速见效”的评论/流量技巧，只要涉及伪造，都不值得；你的长期资产是“这个作者讲得清楚、可信”。
- 平台费率和可售品类变化很快；上架前以官网/客服为准。
