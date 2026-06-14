# {项目名} 学习文档

> 这是 {项目名} 的学习文档前门，由 learn-project 的 `lp-*` 系列 skill 自动生成。
> 打开这份 README，你应该能在 30 秒内知道：这是什么项目、有哪些功能学习文档、该按什么顺序读。

## 项目一句话简介

{一句话让学习者建立"这是什么项目"的认知。从 ../project-knowledge/01-项目概览.md 提炼，不是复制标题。}
深入背景见：[01-项目概览.md](../project-knowledge/01-项目概览.md)、[02-技术栈与架构.md](../project-knowledge/02-技术栈与架构.md)。

## 功能学习文档

{对每个已选中功能给出：文档链接 / 何时读 / 一句话定位}

| 文档 | 何时读 | 一句话定位 |
|------|--------|-----------|
| [docs/{功能A}.md](docs/{功能A}.md) | 当你想 {X} 时先读 | {一句话} |
| [docs/{功能B}.md](docs/{功能B}.md) | 当你想 {Y}（依赖 {功能A}）时读 | {一句话} |
| docs/{功能C}.md — 待生成 | {选了但未生成时的"何时读"} | {待生成} |

> 完整功能清单（含未选中的）见 [features/inventory.md](features/inventory.md)。

## 学习路径

> 带着学习目标来，从这里决定按什么顺序读。

### 从零到理解主线
1. 先读 [docs/{功能A}.md](docs/{功能A}.md) —— {为什么先读它：无依赖、是主线基础}
2. 再读 [docs/{功能B}.md](docs/{功能B}.md) —— {为什么接着读：依赖 A 的 X 能力}

{按依赖字段排出完整顺序，每步标注为什么这个顺序}

{若依赖了未选中功能：注明"前置 {功能} 未选入，建议另行挑选"}

## 元信息

| 字段 | 值 | 来源 |
|------|------|------|
| 项目名称 | {projectName 或"未记录"} | `_meta/progress.json` |
| 生成时间 | {generatedAt 或"未记录"} | `_meta/progress.json` 的 `generatedAt` |
| skill 版本 | {skillVersion 或"未记录"} | `_meta/progress.json` |
| 源码版本/commit | {commit 或"未记录"} | `_meta/progress.json` 或 git rev-parse |
| 功能/选中/完成状态 | 共 {n} 功能，选中 {m}，文档已生成 {k}/{m} | `_meta/progress.json` 的 `features`（或 inventory+docs 反推） |

> {_meta/progress.json 不存在时注明："_meta/progress.json 未生成，状态由实际文件反推，建议由 learn-project 生成该文件"}
