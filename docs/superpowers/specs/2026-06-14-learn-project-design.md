# 子项目 B 设计：learn-project（已有项目学习文档生成）

> 状态：设计稿（待评审 → writing-plans）
> 日期：2026-06-14
> 上游 spec：`docs/superpowers/specs/2026-06-14-project-mastery-design.md`（子项目 A，已完成期1）

## 1. 背景与定位

针对**任意已有项目**：扫描其功能 → 人在回路挑选 → 对选中功能生成「教学提示词 + 学习文档」，帮**有经验但不熟悉该项目的开发者**快速吃透其核心设计。

与子项目 A（project-mastery）的关系与分工：

| | 子项目 A：project-mastery | 子项目 B：learn-project |
|---|---|---|
| 面向场景 | 接手开发（写代码） | 学习理解（读懂代码） |
| 产出视角 | 工程事实（规范/API/构建/部署） | 教学理解（设计思想/核心概念/功能如何工作） |
| 产出目录 | `{PROJECT_ROOT}/docs/project-knowledge/` | `{PROJECT_ROOT}/docs/learning-docs/` |
| 受众 | 要在本项目里写代码的人 | 想搞懂本项目设计的人 |
| 复用关系 | 自成体系 | **复用 A 的扫描底座**（pm-scan + pm-techstack-generic） |

两者产出目录并列、互不覆盖。B 可直接读取 A 已生成的 01/02 作为背景。

## 2. 已确认的设计决策

| 决策 | 选择 |
|---|---|
| 核心机制 | 生成教学提示词文件 + 自动执行（dispatch subagent 生成文档）；提示词可复用/重跑 |
| 复用关系 | 直接复用 A 的 pm-scan + pm-techstack-generic 作为第 0 步定位 |
| 大项目取舍 | 人在回路：扫描产出功能清单 → 用户挑选 → 只对选中功能生成 |
| 目标受众 | 有经验的开发者，但不熟悉本项目（假设语言/框架熟练，聚焦项目特定知识） |
| 产出位置 | 目标项目内 `{PROJECT_ROOT}/docs/learning-docs/`（与 A 的 project-knowledge 并列） |
| 目标对象 | 任意已有项目（非仅限开源项目） |
| skill 命名 | 新顶层 skill `learn-project`，子 skill 前缀 `lp-` |
| 通用化 | skill 源码 100% 通用；目标项目只出现在产出里（沿用 A 纪律） |

## 3. skill 清单与职责

| Skill | 职责 | 执行者 | 新建/复用 |
|---|---|---|---|
| `learn-project` | 顶层编排：定位 → 功能扫描 → 人在回路挑选 → 逐功能生成提示词+文档 → 学习路径索引 | 主会话 | 新建 |
| `lp-feature-scan` | 扫描项目识别可学习的功能/能力，产出功能清单（含核心度/复杂度/依赖/证据） | agent | 新建 |
| `lp-prompt-gen` | 对每个选中功能生成教学提示词（含要读的代码/学习目标/文档结构），存为可复用文件 | agent | 新建 |
| `lp-index` | 汇编学习路径索引 README（推荐阅读顺序/前置依赖/进度） | 主会话（轻） | 新建 |
| `pm-scan` | 项目类型识别 + 概览（波次 1） | agent | **复用 A** |
| `pm-techstack-generic` | 技术栈与架构识别（波次 2） | agent | **复用 A** |

**doc 生成不单独成 skill**：orchestrator（learn-project）用 `lp-prompt-gen` 保存的提示词 dispatch 一个通用 subagent，产出 `docs/{feature}.md`。提示词承载教学方法论，subagent 只负责"读证据代码 + 按提示词结构成文"，无需独立 skill。

## 4. 整体流程

```
learn-project (主会话编排)
  │
  ├─【第 0 步·定位】（复用 A）
  │    若 {PROJECT_ROOT}/docs/project-knowledge/01、02 已存在 → 直接读
  │    否则 → dispatch pm-scan 产出 01 → dispatch pm-techstack-generic 产出 02
  │    （产出落在 project-knowledge/，作为 B 的背景输入）
  │
  ├─【第 1 步·功能扫描】
  │    dispatch lp-feature-scan → 产出 features/inventory.md（功能清单，按核心度排序）
  │
  ├─【第 2 步·人在回路挑选】（主会话）
  │    呈现 inventory.md → 用户勾选要深入的功能（[ ] → [x]）
  │    ≤4 个核心功能可用 AskUserQuestion(multiSelect)；更多则用户直接编辑 inventory 勾选框
  │
  ├─【第 3 步·逐功能生成】（对每个选中功能，可并行）
  │    ├─ dispatch lp-prompt-gen → features/prompts/{feature}.md（教学提示词，可复用/重跑）
  │    └─ dispatch 通用 subagent（带提示词）→ docs/{feature}.md（学习文档）
  │
  └─【第 4 步·学习路径索引】
       主会话执行 lp-index → README.md（推荐阅读顺序/前置依赖/进度）
```

## 5. 各 skill 详细设计

### 5.1 learn-project（顶层编排，主会话）

**职责**：串联全流程、承担人在回路交互、在末步调用 lp-index。本身不做源码分析。

**关键行为**：
- 第 0 步探测 project-knowledge/01、02 是否存在；不存在则 dispatch pm-scan + pm-techstack-generic 补齐。
- 第 2 步把 inventory.md 呈现给用户挑选；记录选中功能清单。
- 第 3 步对每个选中功能先 dispatch lp-prompt-gen 产出提示词，再用该提示词 dispatch 通用 subagent 生成文档；多个功能可并行 dispatch（每个功能一条 prompt→doc 链）。
- 第 4 步调用 lp-index 汇编 README。
- 维护 `{PROJECT_ROOT}/docs/learning-docs/_meta/progress.json`：记录功能清单、选中项、各功能 prompt/doc 完成状态，供断点续跑与 lp-index 读取。

### 5.2 lp-feature-scan（功能识别，agent）

**职责**：扫描项目，识别"值得学习"的功能/能力，产出功能清单。这是 B 的核心新增能力。

详见 §6 功能识别方法论。

**产出**：`features/inventory.md`（含未选中项，按核心度排序，每条带 `[ ]` 勾选框）。

### 5.3 lp-prompt-gen（教学提示词生成，agent）

**职责**：对一个选中的功能，结合其证据（来自 inventory）与项目背景（01/02），生成一份结构化的教学提示词，保存为可复用文件。

**产出**：`features/prompts/{feature}.md`。详见 §8 教学提示词模板。

**核心原则（写入 SKILL.md）**：
- 提示词必须列出**要读的具体证据代码**（文件路径 + 说明），让 doc-gen subagent 实际打开阅读、不臆造。
- 提示词必须规定**学习目标**（读者读完后应能回答的问题）与**文档结构**（6 节，见 §7）。
- 提示词必须声明**受众**（有经验但不熟本项目）与**撰写要求**（讲 WHY、引用真实路径、不讲通用语法）。

### 5.4 lp-index（学习路径索引，主会话）

**职责**：汇编 `docs/learning-docs/README.md`，让学习者在 30 秒内知道"项目是什么、有哪些功能学习文档、该按什么顺序读"。

**核心原则**（参照 A 的 pm-kb-index 铁律，但面向学习路径）：
1. 开篇有项目一句话简介（从 project-knowledge/01 提炼，并链接到 01/02 背景）。
2. 每个已生成的功能文档有「何时读」触发式描述。
3. 有**学习路径**章节：按依赖关系给出推荐阅读顺序（先读哪个、再读哪个），≥1 条"从零到理解主线"的路径。
4. 有元信息章节：从 `_meta/progress.json` 读取（功能清单/选中/完成状态/生成时间），缺失字段显式标注，禁止编造。
5. 区分已生成与未生成文档（选了但还没生成的，标注"待生成"，不给死链）。

## 6. 功能识别方法论（lp-feature-scan 核心）

分层扫描（沿用 pm-scan"先顶层后深扫、不盲目遍历"的纪律）：

| 层 | 来源 | 提取什么 |
|---|---|---|
| ① 文档层 | README、docs/ 目录大纲、CHANGELOG | 项目自己宣传的功能/主题（最权威的功能框架） |
| ② 结构层 | 顶层模块/包/目录 | 候选功能区 |
| ③ 入口层 | CLI 命令、API 路由组、导出符号、插件/扩展注册点 | 用户可感知的能力 |
| ④ 示例层 | examples/、demos/、sample | 展示的用例 |
| ⑤ 聚类去重 | 交叉比对 ①-④ | 合并成统一功能清单 |

**每条功能清单的字段**：
- 功能名（项目语境下的自然名称）
- 一句话简介（它做什么）
- 核心度（核心 / 边缘）——是否属于项目主线能力
- 复杂度（高 / 中 / 低）——学习成本
- 依赖（学它前建议先懂的功能或概念；无则标"无"）——驱动学习路径排序
- 证据（定义该功能的文件/目录/入口/文档，`{路径}: {说明}` 格式）——供 lp-prompt-gen 深挖

**大项目取舍**：限制扫描深度（同 pm-scan，≤3 层、≤20 个配置文件），产出按核心度排序的清单，交人挑选；不强求穷举所有功能，避免在扫描阶段就消耗过多。

**边界处理**：
- **无文档/无明确功能区**：从入口层+结构层反推，清单注明"基于入口与结构推断"。
- **功能粒度过细**：相近的小能力聚类成一个功能（如多个 CRUD 端点归为"X 资源管理"）。
- **极小项目**：功能数少则如实呈现（可能只有 1-3 个功能），不凑数。

## 7. 学习文档结构模板（6 节）

面向"有经验但不熟本项目"的读者，每份 `docs/{feature}.md` 严格含：

1. **概览**：这功能是啥、为什么存在、在项目里处于什么位置
2. **核心概念**：关键抽象、术语、数据结构
3. **如何工作**：设计思路 + 关键代码走读（讲 WHY 不止 WHAT，引用真实文件路径与片段）
4. **使用示例**：怎么用，具体例子（从 examples/tests/调用方提取）
5. **与其它部分的关系**：怎么和项目其它功能/模块衔接，依赖与被依赖
6. **延伸**：下一步探索什么、相关功能链接

## 8. 教学提示词模板（lp-prompt-gen 产出）

`features/prompts/{feature}.md` 结构：

```markdown
# 教学提示词 — {功能名}

> 由 lp-prompt-gen 生成。供 doc-gen subagent 执行，产出 docs/{功能名}.md。
> 可复用/重跑：修改本文件后重新 dispatch 即可重新生成文档。

## 任务
你是技术文档撰写者。目标读者：有经验的开发者，但不熟悉本项目（假设语言/框架熟练，缺的是项目特定知识）。
请阅读下列证据代码，撰写关于「{功能名}」的学习文档，写到 {PROJECT_ROOT}/docs/learning-docs/docs/{功能名}.md。

## 功能背景
- 功能名：{功能名}
- 简介：{一句话}
- 核心度/复杂度：{...}
- 前置依赖：{建议读者先读的功能/概念；或"无"}

## 必读证据（请实际打开阅读，勿臆造）
- {证据文件1}: {说明}
- {证据文件2}: {说明}
- {可选：背景文档，如 ../project-knowledge/01-项目概览.md、02-技术栈与架构.md 的相关章节}

## 学习目标（读者读完后应能回答）
1. ...
2. ...

## 文档结构（严格按此 6 节输出）
（同 §7 的 6 节）

## 撰写要求
- 讲设计思想与 WHY，不只是堆代码。
- 代码走读引用真实文件路径与关键片段。
- 假设读者懂语言/框架，不讲通用语法。
- 篇幅适中，宁可聚焦讲透，不灌水。
```

## 9. 产出目录结构

```
{PROJECT_ROOT}/docs/learning-docs/
├─ README.md                     ← 学习路径索引（lp-index）
├─ _meta/
│  └─ progress.json              ← 功能清单/选中项/各功能完成状态/时间（learn-project 维护）
├─ features/
│  ├─ inventory.md               ← 功能清单（含未选中的，每条带 [ ] 勾选框）（lp-feature-scan）
│  └─ prompts/
│     └─ {功能名}.md             ← 教学提示词（可复用/重跑）（lp-prompt-gen）
└─ docs/
   └─ {功能名}.md                ← 生成的学习文档（doc-gen subagent）
```

`_meta/progress.json` 示例（字段占位符化，通用）：
```json
{
  "projectName": "{项目名}",
  "generatedAt": "{ISO 8601}",
  "skillVersion": "learn-project v1",
  "sourceCommit": "{commit 或 未记录}",
  "features": [
    {"name": "{功能A}", "selected": true, "prompt": "features/prompts/{功能A}.md", "doc": "docs/{功能A}.md", "status": "done"},
    {"name": "{功能B}", "selected": false, "status": "skipped"}
  ]
}
```

## 10. 输出位置与复用关系

- **输出位置**：`{PROJECT_ROOT}/docs/learning-docs/`，与 A 的 `docs/project-knowledge/` 并列、不覆盖。
- **复用 A 的扫描底座**：第 0 步探测 `project-knowledge/01-项目概览.md`、`02-技术栈与架构.md`；存在则读，不存在则 dispatch `pm-scan` + `pm-techstack-generic` 补齐（产出落 project-knowledge/）。**不修改 A 的 skill**，纯调用。
- **README 背景链接**：lp-index 产出的 README 在"项目一句话简介"处链接到 `../project-knowledge/01-项目概览.md`、`02-技术栈与架构.md`，让学习者可顺藤摸到 A 的工程事实文档。

## 11. 通用化纪律（沿用 A）

- 所有 `skills/{learn-project,lp-*}/SKILL.md` **100% 通用**：零具体项目内容（项目名、模块名、类名、专有标识符一律不得作为例子，只能用占位符 `{...}`）。
- 通用技术名词（Spring/Vue/Maven 等）作为跨项目识别指引允许。
- 写完每个 skill 立即 `grep -rni "<项目名>" skills/*/SKILL.md` 自检，必须 0 命中。
- TDD 压力场景放 `docs/skill-design/<skill>/pressure-scenario.md`（不进 skills/，因 skills/ 软链到 ~/.claude/skills/ 全局发布）。

## 12. 测试靶子与验收

- **测试靶子**：`dsp`（全栈 / 多模块，gitignored）。仅用于 TDD 验证，不进 skill 源码。
- **验收方式**：用 writing-skills 的 TDD 流程为每个 skill 建压力场景（baseline RED → 写 skill → GREEN 验证）。
- **端到端验收**：在 dsp 上跑通 learn-project 全流程：定位（A 已有 01/02 则复用）→ 功能清单 → 挑选 2-3 个功能 → 生成提示词 + 文档 → 学习路径索引；产出落在 `dsp/docs/learning-docs/`；最后 `grep` 自检 skill 源码零 dsp 命中。

## 13. 范围与延后项

**本期（期B-1）交付**：learn-project + lp-feature-scan + lp-prompt-gen + lp-index，复用 pm-scan/pm-techstack-generic，端到端跑通。B 较 A 小，**一个期完成**。

**延后 / 不做**：
- **doc-gen 独立 skill 化**：本期 doc 生成靠提示词驱动通用 subagent；若未来需要更复杂的文档质量把控（多稿迭代、交叉验证），再考虑独立 skill。
- **学习文档质量校验 skill（lp-verify）**：本期不做，参照 A 的 pm-verify 思路未来按需补充（如抽样核对文档引用的代码路径是否真实存在）。
- **多语言/多受众变体**：本期受众固定"有经验开发者"；其它受众（纯新手、非开发）按需延后。

## 14. 构建方式

- 使用 superpowers 的 `writing-plans` 生成实现计划 → `subagent-driven-development` 逐任务实现（每个 skill 一个任务：implementer + spec reviewer + code quality reviewer）。
- skills/ 软链到 ~/.claude/skills/（沿用 `scripts/link-skills.sh`）。
- 实现分支：`phase-b1-learn-project`，完成后按 finishing-a-development-branch 合入 main。
