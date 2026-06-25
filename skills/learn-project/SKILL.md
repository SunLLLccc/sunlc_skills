---
name: learn-project
description: 当需要对一个已有项目生成学习文档（定位→功能扫描→人在回路挑选→逐功能生成教学提示词+学习文档→汇编学习路径索引）时使用。
---

# learn-project — 已有项目学习文档生成（顶层编排）

## 定位

learn-project 是项目学习文档生成的**顶层编排 skill**（由主会话执行）。它串联一条完整管线：复用 project-mastery 的扫描底座定位项目 → 识别可学习功能 → 人在回路挑选 → 对选中功能生成教学提示词与学习文档 → 汇编学习路径索引。产出落在目标项目内的 `{PROJECT_ROOT}/docs/learning-docs/`，与 project-mastery 的 `docs/project-knowledge/`（工程事实）并列。

learn-project 本身**不做源码分析**——分析由它分发的子 skill（lp-feature-scan / lp-prompt-gen / lp-index）与复用的 pm-scan / pm-techstack-generic 承担。它的职责是：编排流程顺序、承担人在回路交互、维护 `_meta/progress.json`、用保存的提示词 dispatch doc 生成 subagent。

## 输入

- `PROJECT_ROOT`：目标项目的根目录绝对路径
- （可选）用户在挑选环节指定要深入的功能

## 产出

```
{PROJECT_ROOT}/docs/learning-docs/
├─ README.md                      ← 学习路径索引（lp-index，含章节目录页）
├─ _meta/
│  ├─ progress.json               ← 全流程状态（本 skill 维护）
│  └─ prompts/{章}-{节}-{功能}.md      ← 教学提示词（lp-prompt-gen，下沉中间产物）
├─ features/
│  └─ 01-001-功能清单.md                ← 功能清单 + 候选分章总览（lp-feature-scan）
└─ docs/{章}-{节}-{功能}.md                 ← 学习文档（doc-gen subagent，章=主题/节=章内序号）
```

## 核心原则

1. **复用不重复**：第 0 步探测并复用 project-knowledge/01、02；A 已跑过绝不重跑。
2. **人在回路**：功能清单交给用户挑选，只对选中的生成——不擅自对全部功能生成。
3. **提示词驱动 doc**：文档必须由 lp-prompt-gen 保存的提示词驱动生成，提示词是可复用重跑的产物。
4. **全程维护 progress.json**：每个功能的 prompt/doc 完成状态实时记录，支持断点续跑、供 lp-index 读取真实状态。
5. **顺序严格**：定位 → 扫描 → 挑选 → 提示词 → 文档 → 索引，不可跳序。

## 流程

### 第 0 步：定位（复用 project-mastery 扫描底座）

1. 探测 `{PROJECT_ROOT}/docs/project-knowledge/01-001-项目概览.md` 与 `02-001-技术栈与架构.md` 是否存在。
2. **存在** → 直接读，作为后续步骤与学习者的背景，跳过重扫。
3. **不存在** → dispatch `pm-scan` 产出 01 + `.codebase/scan-result.json`，再 dispatch `pm-techstack-generic` 产出 02。产出落 project-knowledge/（A 的目录），作为 B 的背景输入。

### 第 1 步：功能扫描

- dispatch `lp-feature-scan` → 产出 `features/01-001-功能清单.md`（功能清单，每条带 `- [ ]` 勾选框、核心度/复杂度/依赖/证据）。

### 第 2 步：人在回路挑选 + 确认分章（主会话）

- 把 01-001-功能清单.md（含「候选分章总览」段）呈现给用户：
  - **先确认分章**：呈现候选分章总览（章号/主题名/含功能编号），问用户"算法给出 N 章、主题名是否合适？要不要合并/拆分/调整章号或功能归属？"用户确认或直接编辑清单的候选分章总览段 + 各功能候选章字段。
  - **再挑选功能**：在要深入的功能前把 `- [ ]` 改为 `- [x]`（≤4 个可用 AskUserQuestion multiSelect；更多则直接编辑清单或口头告知）。
- 记录选中功能 + 确认后的分章，写入 `_meta/progress.json`。
- **分配章节号**：对每个选中功能，取其确认后的候选章为 `chapter`；章内按拓扑序（被依赖靠前）分配 3 位 `section`（`001`、`002`、…）。写入 features[].chapter/section。用于后续文件命名（`docs/{章}-{节}-{功能}.md`、`_meta/prompts/{章}-{节}-{功能}.md`），保证 prompt↔doc 同章节号配对。

### 第 3 步：逐功能生成提示词 + 文档

对每个选中功能（**可并行** dispatch，每个功能一条 prompt→doc 链）：

1. dispatch `lp-prompt-gen`（输入：该功能在 inventory 的证据 + 01/02 背景 + chapter/section）→ 产出 `_meta/prompts/{章}-{节}-{功能}.md`。
2. 用该提示词 dispatch 一个**通用 doc 生成 subagent**：
   - 给 subagent 的指令 = "读取提示词文件 → 按其必读证据实际打开代码阅读 → 按其 6 节结构与撰写要求产出文档 → 写到 docs/{章}-{节}-{功能}.md"。
   - 提示词承载教学方法论，subagent 只执行，不自行决定教什么。
3. 每完成一个功能，更新 `_meta/progress.json` 该功能的 prompt/doc 完成状态。

### 第 4 步：汇编学习路径索引

- 主会话执行 `lp-index` → 产出 `README.md`（读取 inventory/prompts/docs + progress.json）。

## `_meta/progress.json` 维护规则

本 skill 在第 1 步创建该文件并随流程更新。字段（v2）：

```json
{
  "projectName": "{项目名}",
  "projectRoot": "{PROJECT_ROOT 绝对路径}",
  "generatedAt": "{ISO 8601，本 skill 起始时刻}",
  "skillVersion": "learn-project v2",
  "sourceCommit": "{git rev-parse 或 未记录}",
  "chapters": [
    {"num": "01", "topic": "{章主题名}", "featureNums": ["#4", "#3", "#11"]}
  ],
  "chaptersConfirmed": true,
  "features": [
    {"num": "#4", "name": "{功能A}", "selected": true, "chapter": "01", "section": "001", "topic": "{章主题名}", "prompt": "_meta/prompts/01-001-{功能A}.md", "doc": "docs/01-001-{功能A}.md", "status": "done"},
    {"num": "#5", "name": "{功能B}", "selected": true, "chapter": "02", "section": "001", "topic": "{章主题名}", "prompt": "_meta/prompts/02-001-{功能B}.md", "doc": "docs/02-001-{功能B}.md", "status": "prompted"},
    {"num": "#9", "name": "{功能C}", "selected": false, "status": "skipped"}
  ]
}
```

- `generatedAt` 用本 skill 起始时刻（真实），供 lp-index 读取，**杜绝 lp-index 编造时间**。
- `chapters`：确认后的章列表（章号 `num` / 主题名 `topic` / 含功能编号 `featureNums`）。`chaptersConfirmed`：人在回路第 2 步是否确认过分章（false = 用算法默认）。
- `features[].num`：清单内编号（`#N`，对应功能清单 `### N.`）。`features[].chapter`/`section`：所属章 + 章内节号（被依赖靠前），用于文件命名；未选中的无 chapter/section。`features[].topic`：所属章主题名（冗余便于查阅）。
- `features` 每条的 status：`skipped`（未选中）/ `prompted`（仅提示词完成）/ `done`（文档完成）。
- 断点续跑：重跑时先读 progress.json，跳过已 `done` 的功能，只补未完成的。
- **v1 检测**：若读到 `skillVersion` 为 `learn-project v1`（features 用旧 `seq` 字段、无 chapters），**报错提示用户手动迁移**（不自动迁移——自动改写易错）；提示"旧版结构（02-{seq} 扁平命名），请按 v2 章节结构重组或重跑"。

## 边界处理

- **第 0 步探测到 01/02 部分缺失**（如只有 01 无 02）：补齐缺失的那个（dispatch 对应 skill），不重跑已有的。
- **用户未挑选任何功能**：在第 2 步提示并等待，不进入第 3 步；或默认建议选核心度=核心的前 N 个，但需用户确认。
- **某功能 doc 生成失败**：progress.json 该功能 status 留 `prompted`，doc 字段标"待生成"，继续其它功能；lp-index 会标注"待生成"。
- **大项目功能过多**：依赖 lp-feature-scan 的排序与大项目取舍；第 2 步引导用户聚焦核心度=核心的功能，避免全量生成。
- **断点续跑**：检测到 progress.json 已存在时，询问用户是"续跑（补未完成）"还是"重跑（清空重来）"。

## 执行检查清单

执行 learn-project 时，按以下顺序完成：

1. [ ] 第 0 步：探测 project-knowledge/01、02；缺失则 dispatch pm-scan/pm-techstack 补齐
2. [ ] 创建/续读 `_meta/progress.json`（写 projectName/generatedAt/sourceCommit；**读到 v1 报错提示迁移**）
3. [ ] 第 1 步：dispatch lp-feature-scan → 01-001-功能清单.md（含候选分章总览）
4. [ ] 第 2 步：呈现 inventory + 候选分章总览，人在回路**确认分章** + 挑选，记录 selected/chapter/section
5. [ ] 第 3 步：对每个选中功能 dispatch lp-prompt-gen（产出 _meta/prompts/{章}-{节}- 提示词）→ 用提示词 dispatch doc subagent（产出 docs/{章}-{节}- 文档），逐个更新 progress.json
6. [ ] 第 4 步：执行 lp-index → README.md（含章节目录页）
7. [ ] 自检：
    - [ ] 第 0 步未重复扫描（A 已有就复用）？
    - [ ] 分章经人在回路确认、只对选中功能生成、文档由提示词驱动？
    - [ ] progress.json 为 v2（chapters + features[].chapter/section）、generatedAt 真实？
    - [ ] 产出齐备（README/功能清单/_meta/prompts/docs）？
    - [ ] doc 文档引用的代码路径真实、零臆造？
