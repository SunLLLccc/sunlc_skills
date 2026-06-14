---
name: lp-index
description: 当功能清单与各功能学习文档均已生成、需要汇编学习路径索引 README（项目速览+何时读+按依赖排序的阅读路径+元信息）时使用。
---

# lp-index — 学习路径索引汇编

## 定位

lp-index 是 learn-project 管线的**第 4 步**索引 skill（由主会话执行）。它读取已生成的功能清单、教学提示词、学习文档与 `_meta/progress.json`，汇编一份**学习路径前门 README**：让学习者在 30 秒内知道"这是什么项目、有哪些功能学习文档、该按什么顺序读"。

**由主会话执行，非 agent**——本 skill 不做源码分析，只汇编已有产出的索引。

与"列一份文档目录"的区别：本 skill 的产出是**学习路径驱动的查阅入口**，强制要求项目一句话简介、每份文档的"何时读"、按依赖排序的学习路径、从 `_meta/progress.json` 读取的元信息、对未生成文档的显式标注。

## 输入

- `PROJECT_ROOT`：目标项目的根目录绝对路径
- `{PROJECT_ROOT}/docs/learning-docs/features/inventory.md`：功能清单（读取每条的名称/核心度/复杂度/依赖/是否选中）
- `{PROJECT_ROOT}/docs/learning-docs/features/prompts/`：教学提示词（确认哪些功能已生成提示词）
- `{PROJECT_ROOT}/docs/learning-docs/docs/`：学习文档（确认哪些功能已生成文档）
- `{PROJECT_ROOT}/docs/learning-docs/_meta/progress.json`：元信息来源（项目名/生成时间/功能清单/选中项/完成状态/skill 版本）
- `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`、`02-技术栈与架构.md`：项目背景（提炼一句话简介、提供链接）

## 产出

- `{PROJECT_ROOT}/docs/learning-docs/README.md` — 学习路径前门索引

## 核心原则：5 条铁律

README 必须满足以下 5 条，否则禁止定稿：

### 铁律 1：开篇有项目一句话简介 + 背景链接

README 开篇（在功能清单之前）必须有一句话让学习者建立"这是什么项目"的整体认知（从 project-knowledge/01 提炼，不是复制标题），并链接到 `../project-knowledge/01-项目概览.md`、`02-技术栈与架构.md` 作为深入背景。定位是"前门"而非"目录"。

### 铁律 2：每份已生成文档有「何时读」

功能文档清单中**每份已生成的文档**必须有触发式的"何时读"描述（"想理解 X 时读这份 / 想搞懂 Y 时先读这份"），不是仅"这份讲什么"的内容陈述。触发条件尽量互不重叠。

### 铁律 3：有按依赖排序的学习路径

README 必须含"学习路径"章节，**按功能清单的"依赖"字段排序**：

- 无依赖的功能在前，依赖其它功能的在后（先读被依赖的）。
- 至少 1 条"从零到理解主线"的路径：明确标注"先读 A、再读 B"。
- 路径要具体到文档名，并标注为什么这个顺序（如"B 依赖 A 的执行内核，先读 A 建立 XML DSL 基础"）。
- 对未选中的功能，在路径里说明"如需深入可另行挑选生成"。

### 铁律 4：元信息从 `_meta/progress.json` 读，缺失标注不编造

README 必须含元信息章节，字段从 `_meta/progress.json` 读取：

| 字段 | 来源 | 缺失时 |
|------|------|--------|
| 项目名称 | `_meta/progress.json` 的 `projectName` | 标注"未记录" |
| 生成时间 | `_meta/progress.json` 的 `generatedAt` | 标注"未记录（_meta/progress.json 无时间戳）"，**禁止编造当前时间** |
| skill 版本 | `_meta/progress.json` 的 `skillVersion` | 标注"未记录" |
| 源码版本/commit | `_meta/progress.json` 的 `sourceCommit`（若有）；否则尝试 `git -C {PROJECT_ROOT} rev-parse --short HEAD` | 都无则标注"未记录（无 git 仓库或 _meta 无 commit 字段）" |
| 功能清单/选中/完成状态 | `_meta/progress.json` 的 `features`（selected/status） | `_meta/progress.json` 不存在时，从 inventory.md 的 `- [x]` 与 docs/ 实际文件反推，并注明"_meta/progress.json 未生成，状态由实际文件反推" |

**关键规则**：`_meta/progress.json` 不存在不得报错或跳过元信息章节——从 inventory.md 与 docs/ 实际文件反推完成状态，其余字段显式标注"未记录"。**禁止编造时间**。

### 铁律 5：区分已生成与未生成文档

对**选中但尚未生成文档**的功能（典型：选了但因故 doc 未生成），在清单中**显式标注"待生成"**，不给链接或链接前注明"待生成"。不静默忽略——学习者必须知道哪些还没读。

## 学习路径排序算法

按 inventory.md 各功能的"依赖"字段构建顺序：

1. 收集所有**已选中**功能及其依赖（"依赖"字段里点名的是其它功能名）。
2. 拓扑排序：无依赖的排最前；依赖 N 个的功能排在它依赖的全部功能之后。
3. 依赖链断裂（依赖了未选中功能）时，在该功能路径处注明"前置 {功能} 未选入，建议另行挑选或接受背景缺失"。
4. 同层（依赖数相同）按核心度（核心优先）→ 复杂度（低优先）细排。

## 边界处理

### 学习文档不完整（部分选中功能未生成文档）
- 对选中但无文档的功能，清单标注"待生成"，学习路径里仍按依赖顺序排列其位置（标注"待生成"）。

### `_meta/progress.json` 不存在
- 从 inventory.md 的 `- [x]` 反推选中项，从 docs/ 实际文件反推已生成文档；元信息其余字段标注"未记录"；并在 README 注明"_meta/progress.json 未生成，状态由实际文件反推，建议由 learn-project 生成该文件"。

### inventory.md 不存在
- 本 skill **不应执行**——没有功能清单无法索引。注明"未检测到 features/inventory.md，请先执行 lp-feature-scan"。

### 无任何选中功能
- 若 inventory.md 全是 `- [ ]`（无人挑选），README 注明"暂无选中功能，请在 inventory.md 标记 `- [x]` 后重跑 lp-prompt-gen/doc 生成，再重跑本 skill"。不汇编空学习路径。

### 项目无 git 仓库
- 源码 commit 字段标注"未记录（项目无 git 仓库）"，不报错。

## 产出格式

### README.md 模板

> 产出格式见 `templates/README.md`（执行时读取该模板填充，勿自行发明结构）。

## 执行检查清单

执行 lp-index 时，按以下顺序完成：

1. [ ] 读取 inventory.md（必须有），解析每功能的名称/核心度/复杂度/依赖/是否选中（`- [x]`）
2. [ ] `ls` prompts/ 与 docs/，确认哪些功能已生成提示词/文档
3. [ ] 读取 `_meta/progress.json`（若有）；无则标注将反推
4. [ ] 从 project-knowledge/01 提炼项目一句话简介
5. [ ] 写"功能学习文档"表——每份已生成文档含链接/何时读/定位；未生成的标"待生成"
6. [ ] 写"学习路径"——按依赖字段拓扑排序，标注每步为什么这个顺序
7. [ ] 写"元信息"——从 `_meta/progress.json` 读，缺失显式标注，**禁止编造时间**
8. [ ] 写入 `README.md`
9. [ ] 自检：
    - [ ] 开篇有项目一句话简介 + 01/02 链接？
    - [ ] 每份已生成文档有「何时读」？
    - [ ] 学习路径按依赖排序、标注理由？
    - [ ] 元信息时间来自 _meta 不编造？_meta 不存在时反推+标注？
    - [ ] 未生成文档标"待生成"、无死链？
