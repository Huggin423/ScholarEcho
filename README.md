# AI-Ready Research Vault

这是一个面向研究生长期研究的本地个人知识库骨架。它的目标不是替代 Zotero 或 Notion，而是把论文、笔记、研究问题、项目上下文组织成 AI Agent 可以稳定读取、检索、更新和复用的结构化上下文。

## 设计目标

- 让 Zotero 继续负责 PDF、引用、BibTeX 和阅读状态。
- 让本仓库负责可长期维护的研究知识结构。
- 让不同 AI 供应商都能读取统一的 `AGENTS.md`、Skills、模板和上下文包。
- 让每次 AI 处理论文、综合文献、生成研究问题时都留下 trace。
- 让知识库最终服务于 proposal、related work、实验设计、论文写作和答辩材料。

## 目录结构

```text
.
├── 00_inbox/                 # Zotero / Notion / 临时导入材料
├── 01_papers/                # 单篇论文卡片
├── 02_concepts/              # 概念节点
├── 03_methods/               # 方法节点
├── 04_questions/             # 开放研究问题
├── 05_projects/              # 研究项目上下文包
├── 06_synthesis/             # 周总结、主题综述、跨论文综合
├── 07_outputs/               # proposal、论文、汇报材料等输出
├── agent/                    # Agent profiles、prompts、skills、traces
├── docs/                     # 架构和使用文档
├── index/                    # metadata、embedding、graph 等索引产物
└── scripts/                  # 本地维护脚本
```

## 第一阶段工作流

1. 从 Zotero 选择 10-20 篇与你未来研究方向最相关的论文。
2. 按 `01_papers/_template.md` 为每篇论文建立结构化卡片。
3. 把每篇论文连接到至少一个 `Concept`、`Method`、`Question` 或 `Project`。
4. 每周运行一次 `agent/skills/weekly-synthesis/SKILL.md` 中定义的复盘流程。
5. 将形成的研究问题沉淀到 `04_questions/open_questions.md` 和项目上下文中。

## 多模型使用

模型供应商通过 `agent/profiles/*.yaml` 抽象。Skills 不绑定具体模型，只描述任务流程。实际运行时可以按 `agent/router.yaml` 选择 OpenAI、DeepSeek、本地模型或其他供应商。

建议原则：

- 批量初读、标签分类：优先使用低成本模型。
- 跨论文综合、proposal 写作：优先使用强推理和长上下文模型。
- 隐私敏感笔记：优先使用本地模型。
- 所有非平凡 AI 输出都要写入 `agent/traces/`。

## 快速开始

阅读顺序建议：

1. `AGENTS.md`
2. `docs/architecture.md`
3. `agent/router.yaml`
4. `agent/skills/read-paper/SKILL.md`
5. `01_papers/_template.md`

然后创建你的第一个项目上下文：

```text
05_projects/master_research_direction/context.md
```

把你的研究方向、已知关键词、导师/实验室关注点、已有论文列表先写进去。后续 AI Agent 会优先围绕这个上下文组织知识。

