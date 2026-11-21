# 尚雯婕听写跟读教练 · shangwenjie-dictation-coach 🎧✍️🗣️

把英语学习从 **“我大概听懂了”** 推进到 **“我听得出、跟得上、说得出，而且能复盘”**。

这是一个面向 AI Agent 的英语听写学习 Skill：你告诉它想学什么领域，它帮你找带可靠原文的音频材料；你完成听写后，它帮你诊断听力薄弱点、整理知识点、生成可打印的跟读练习单，并把每天的学习沉淀成可导出的记录。

![Skill](https://img.shields.io/badge/Agent-Skill-purple) ![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Obsidian](https://img.shields.io/badge/Obsidian-Compatible-black) ![Learning](https://img.shields.io/badge/Listening--Dictation--Shadowing-green)

## ✨ 它能做什么

- 🌍 **多领域找材料**：AI、经济、法律、营销、医学等，优先官方文章、正式演讲、播客和机构材料
- 🎙️ **优先高质量原文**：官方文章 + `Listen to article`、官方 transcript、正式音频，不拿低质量自动字幕冒充原文
- ✍️ **听写对齐**：保留你的原始听写，自动识别漏听、误听、多写和拼写差异
- 🧠 **薄弱点诊断**：区分功能词/弱读、连读、词汇、词组、句法和信息记忆问题
- 🖨️ **当天跟读单**：生成可打印 HTML，在原文上标出错误，拆成意群，附跟读任务
- 🗣️ **舒服的跟读模式**：默认连续跟读不打断，在自然停顿处集中反馈；也支持 `checkpoint` 和 `coaching`
- 💬 **脱稿输出**：跟读之后，用中文提示让你脱稿说英文，再做轻量纠正
- 📚 **知识沉淀**：只总结材料中真实出现的搭配、句型和领域词汇
- 📈 **长材料学习**：按段落、时间戳或句子保存进度，学完再生成全文高亮复盘
- 📓 **Obsidian 兼容记录**：Markdown + YAML + JSON + CSV，可配合 Dataview、Tasks、Calendar
- 🗓️ **周/月复盘**：从真实记录生成错误趋势、重复问题和下一阶段任务
- 🔗 **来源可验证**：不根据标题猜 URL，记录 `verified`、`user_provided_verified`、`blocked` 等状态

## 🚀 三分钟上手

### Codex

```bash
git clone https://github.com/magique1124/shangwenjie-dictation-coach.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/shangwenjie-dictation-coach"
```

然后新开对话：

```text
使用 shangwenjie-dictation-coach，帮我找一篇 AI 领域、5 分钟以上、带官方原文和音频的材料。
```

### Claude Code

```bash
git clone https://github.com/magique1124/shangwenjie-dictation-coach.git \
  "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/shangwenjie-dictation-coach"
```

### 其他支持 Agent Skill 的工具

把仓库放到对应 Skill 目录，保留完整结构：

```text
shangwenjie-dictation-coach/
├── SKILL.md
├── agents/
├── references/
├── scripts/
└── tests/
```

### ChatGPT Project / Custom GPT

这类环境不一定支持运行本地脚本。可以：

1. 把 `SKILL.md` 和 `references/` 的内容加入项目说明；
2. 保留“找材料 → 听写 → 诊断 → 跟读 → 记录”的流程；
3. 文件导出和长期记录由支持本地文件的 Agent 完成。

## 🎯 推荐使用方式

### 1. 找今天想学的材料

```text
用 shangwenjie-dictation-coach 找一篇经济领域、5 分钟以上、带可靠原文的最新材料。
```

Skill 会返回：

- 标题与作者；
- 发布日期；
- 来源类型；
- 音频时长；
- transcript 质量；
- 可点击的官方链接；
- 为什么适合今天学习。

### 2. 完成听写

没有听出来的地方保留：

```text
The world is in a ____ of capability ____, where AI models ...
```

不要先查词，也不要提前看答案。

### 3. 发给 Agent 诊断

```text
这是我今天的听写内容，请分析我哪里听得不好，并总结值得积累的知识点。
```

输出重点：

- 核心信息有没有抓到；
- 2–3 个最高优先级问题；
- 漏听、误听、弱读、词组和长句结构；
- 今天最值得积累的表达；
- 下一步跟读任务。

### 4. 打开当天跟读单

每天会生成一份可打印的 HTML：

```text
2026-11-21-practice.html
```

里面包含：

- 原文错误高亮；
- 你的原始听写；
- 逐块中文理解；
- 连读/弱读提示；
- 跟读任务；
- 知识点；
- 完成清单。

### 5. 跟读与脱稿输出

默认使用 **flow 模式**：

```text
连续跟读
→ 不逐句打断
→ 自然停顿时给 1–3 个反馈
→ 看中文提示脱稿说一次
```

需要更精细时：

```text
用 coaching 模式，每读一次就帮我纠正。
```

或：

```text
用 checkpoint 模式，每读完一个意群反馈一次。
```

### 6. 结束时保存进度

Agent 只问一次：

```text
今天学到哪里？时间戳、段落编号，还是已经学完全文？
```

之后自动保存：

- 原始听写；
- 修改记录；
- 错误类型；
- 知识点；
- 跟读表现；
- 下次复盘；
- 学习进度。

## 🧩 为什么这个流程更舒服

传统 AI 英语学习常常是：

```text
你发内容
→ AI 一次性给一大段分析
→ 你看完就结束
```

这个 Skill 改成句子级微循环：

```text
原始听写
→ 对照修改
→ 逐块理解
→ 连续跟读
→ 自然节点反馈
→ 中文提示脱稿输出
→ 保存这一句
→ 下一处修改
```

它不会在你跟读时每个词都打断，也不会把整篇文章一次性灌给你。

## 🧭 多领域怎么用

| 领域 | 优先来源示例 | 适合学习的内容 |
| --- | --- | --- |
| AI | OpenAI、Anthropic、DeepMind、Microsoft Research、TED | 模型、Agent、企业 AI、研究演讲 |
| 经济 | The Economist、IMF、World Bank、央行、NBER | 宏观经济、政策、市场、产业 |
| 法律 | 最高法院、联邦法院、ABA、法学院 | 口头辩论、法律演讲、案例评论 |
| 营销 | Think with Google、LinkedIn Business、HubSpot、AMA | 品牌、增长、消费者、营销策略 |
| 医学 | WHO、NIH、CDC、FDA、医学期刊 | 公共卫生、医学研究、临床科普 |

来源库只是起点；每个候选材料仍会检查：

```text
发布日期
音频
原文
访问权限
transcript 类型
来源可信度
```

## 🧱 目录结构

```text
shangwenjie-dictation-coach/
├── SKILL.md                         # Skill 入口与核心工作流
├── agents/
│   └── openai.yaml                  # Agent 展示信息
├── references/
│   ├── domain-sources.json          # 多领域来源起点
│   ├── error-taxonomy.md            # 听写错误诊断规则
│   ├── material-search.md           # 材料搜索、URL 验证与降级策略
│   ├── obsidian-schema.md           # Obsidian 记录结构
│   ├── reporting.md                 # 日/周/月/全文复盘
│   └── session-flow.md              # 舒适的逐句学习流程
├── scripts/
│   ├── dictation_tools.py           # 对齐、HTML、记录、报告
│   └── rank_candidates.py           # 材料候选排序
└── tests/                           # 自动化测试
```

## 🛠️ 技术原理

| 模块 | 实现 |
| --- | --- |
| 材料搜索 | 来源类型优先级 + 多领域来源库 + freshness/access/transcript 维�合排序 |
| URL 验证 | canonical/share/user-provided URL；不根据标题猜 slug |
| 听写对齐 | Python 标准库词级 diff，识别 omission、replacement、insertion、spelling |
| 错误诊断 | 可观察错误与推断原因分开，证据不足时标记置信度 |
| 当日练习 | 生成 HTML，原文高亮 + 原始听写 + 意群跟读 + 知识点 |
| 学习记录 | Markdown/YAML/JSON/CSV，兼容 Obsidian 插件 |
| 长材料 | `progress.json` 保存段落和时间戳，支持中断续学 |
| 复盘报告 | 周/月报告只从真实 session 记录生成，不依赖聊天记忆 |

本地运行脚本：

```bash
python3 scripts/dictation_tools.py --help
python3 scripts/rank_candidates.py --help
python3 -m unittest discover -s tests -v
```

## 🔒 隐私与边界

- 学习记录默认写入你指定的本地目录或 Obsidian Vault。
- 不绕过付费墙、登录墙、DRM 或地区限制。
- 没有真实语音时，不假装评价发音和流利度。
- 自动字幕不冒充官方 transcript。
- 分数和诊断是训练参考，不是官方考试成绩。
- 不根据标题猜材料链接，无法验证时明确标记 `blocked` 或 `inferred`。

## ❓ FAQ

### 可以学长材料吗？

可以。长材料按段落、时间戳或句子学习，每天结束时保存进度，学完后生成全文高亮版。

### 可以直接纠正我的跟读吗？

如果 Agent 支持语音输入，可以听你读并纠正。只有文字时，可以纠正用词、语法和句子结构，但不能可靠评价发音。

### 可以装到普通聊天机器人里吗？

可以移植核心流程，但联网搜索、文件保存、HTML 导出和语音反馈取决于 Agent 能力。Codex、Claude Code 等支持 Skill 和本地脚本的环境最完整。

### 为什么每天只总结几个知识点？

因为重点是能复述、能跟读、能迁移。不是把所有生词堆成一张表。

---

把材料交给我，把耳朵和嘴巴练起来。听写不是抄写，跟读不是模仿声音，而是一点点把英语变成自己的反应。🎧
