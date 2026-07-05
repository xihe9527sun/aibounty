# 🔥 扒了28个AI编程工具的System Prompt，我发现了惊天秘密

> 140.8k star 的开源项目，把 Cursor / Claude Code / CodeBuddy / Windsurf 全部扒光

最近 GitHub 上有个仓库火得一塌糊涂——[system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)，140.8k star，收集了**28个AI编程工具**的系统提示词（System Prompt）和内部工具配置。

简单说就是：**各家AI编程助手的"大脑说明书"全被扒出来了。**

我看了一遍，发现几个有意思的事。

---

## 1. Cursor 的 Agent 模式到底强在哪？

Cursor 的 Prompt 被扒出 2.0 版本，核心策略是：

```
你是一个世界级的编程专家。
- 先理解需求，再写代码
- 每次最多改一个文件
- 改完后必须验证
```

最骚的是它有一个 **`/explain`** 内部工具，专门在开始写代码前分析代码库结构。这就是为什么 Cursor 在大型项目上比 Copilot 稳——它先读懂了再动手。

## 2. CodeBuddy 的"链路追踪"策略

CodeBuddy 的 Prompt 里有个很有意思的设计——它会追踪自己的思考链路：

```
每次操作前输出当前状态、目标、计划
出错时回滚到上一个确定状态而非从头开始
```

这本质上就是**带 checkpoint 的 Agent 架构**。对比来看，大部分 AI 编程工具出错了会直接重来，而 CodeBuddy 会回溯到最近正确的状态，这在调试复杂 Bug 时省了巨多时间。

## 3. Windsurf 的"流式思维"

Windsurf Wave 11 的 Prompt 强调**连续流式工作**：

```
不打断用户的工作流
预测用户的下一步操作并提前准备
```

这解释了为什么用 Windsurf 写代码时感觉它"知道你想干什么"——它不是在等指令，而是在预测指令。

## 4. Claude Code 的秘密武器

Claude Code 的 Prompt（来自 Anthropic 文件夹）最特殊的地方是它有**一套完整的 Bash 工具链**：

```
- 读文件、写文件
- 搜索代码（grep + 语义搜索）
- 运行测试
- Git 操作
- 浏览器预览
```

它不是"写代码的助手"，它是**直接在终端里干活的 Agent**。别的工具还在编辑器里打转，Claude Code 已经自己建分支、写测试、跑 CI 了。

---

## 一个规律

看完这 28 个 System Prompt，我发现一个规律：

| 代际 | 代表 | 核心能力 |
|:----:|:-----|:---------|
| 1代 | Copilot | 补全代码 |
| 2代 | Cursor | 理解项目 |
| 3代 | Claude Code / CodeBuddy | 自主执行 |
| 4代 | Windsurf / Cursor 2.0 | 预测需求 |

**下一代的 AI 编程工具，不是等你告诉它做什么，而是它知道你应该做什么。**

---

## 这些工具都在哪找？

这个仓库虽然收集了 Prompt，但它**不提供每个工具的使用体验评测、适用场景对比、价格信息**。

所以我把这 28 个工具（以及更多 AI 工具）整理到了 **[AIbounty](https://www.aibounty.cn)**——一个每日自动更新的 AI 工具导航站：

- 📊 已收录 **2021+** 个 AI 工具，每日自动新增
- 🔍 按 Agent / LLM / RAG / Dev Tool 分类
- 🌐 中英双语介绍
- 🆓 开源优先，标注付费/免费

👉 **[www.aibounty.cn](https://www.aibounty.cn)**

---

*本文由 AIbounty 的曦和系统自动生成，数据来源 [system-prompts-and-models-of-ai-tools](https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools)*
