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
├─ README.md                      ← 学习路径索引（lp-index）
├─ _meta/progress.json            ← 全流程状态（本 skill 维护）
├─ features/
│  ├─ 01-001-功能清单.md                ← 功能清单（lp-feature-scan）
│  └─ prompts/03-{序号}-{功能}.md           ← 教学提示词（lp-prompt-gen）
└─ docs/02-{序号}-{功能}.md                 ← 学习文档（doc-gen subagent）
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

### 第 2 步：人在回路挑选（主会话）

- 把 01-001-功能清单.md 呈现给用户挑选要深入的功能：
  - 若核心功能 ≤4 个，可用 AskUserQuestion（multiSelect）让用户勾选。
  - 若更多，请用户直接编辑 01-001-功能清单.md 把 `- [ ]` 改为 `- [x]`，或口头告知功能名/编号。
- 记录选中功能清单，写入 `_meta/progress.json` 的 features[].selected。
- **分配序号**：按选中顺序给每个选中功能分配 3 位序号（`001`、`002`、…），写入 features[].seq。该序号用于后续文档/提示词文件命名（`docs/02-{seq}-{功能}.md`、`prompts/03-{seq}-{功能}.md`），保证 prompt↔doc 同序号配对、文件按序排列。

### 第 3 步：逐功能生成提示词 + 文档

对每个选中功能（**可并行** dispatch，每个功能一条 prompt→doc 链）：

1. dispatch `lp-prompt-gen`（输入：该功能在 inventory 的证据 + 01/02 背景）→ 产出 `features/prompts/03-{序号}-{功能}.md`。
2. 用该提示词 dispatch 一个**通用 doc 生成 subagent**：
   - 给 subagent 的指令 = "读取提示词文件 → 按其必读证据实际打开代码阅读 → 按其 6 节结构与撰写要求产出文档 → 写到 docs/02-{序号}-{功能}.md"。
   - 提示词承载教学方法论，subagent 只执行，不自行决定教什么。
3. 每完成一个功能，更新 `_meta/progress.json` 该功能的 prompt/doc 完成状态。

### 第 4 步：汇编学习路径索引

- 主会话执行 `lp-index` → 产出 `README.md`（读取 inventory/prompts/docs + progress.json）。

## `_meta/progress.json` 维护规则

本 skill 在第 1 步创建该文件并随流程更新。字段：

```json
{
  "projectName": "{项目名}",
  "projectRoot": "{PROJECT_ROOT 绝对路径}",
  "generatedAt": "{ISO 8601，本 skill 起始时刻}",
  "skillVersion": "learn-project v1",
  "sourceCommit": "{git rev-parse 或 未记录}",
  "features": [
    {"name": "{功能A}", "selected": true,  "seq": "001", "prompt": "features/prompts/03-001-{功能A}.md", "doc": "docs/02-001-{功能A}.md", "status": "done"},
    {"name": "{功能B}", "selected": true,  "seq": "002", "prompt": "features/prompts/03-002-{功能B}.md", "doc": "docs/02-002-{功能B}.md", "status": "prompted"},
    {"name": "{功能C}", "selected": false, "status": "skipped"}
  ]
}
```

- `generatedAt` 用本 skill 起始时刻（真实），供 lp-index 读取，**杜绝 lp-index 编造时间**。
- `features[].seq`：选中功能的 3 位序号（按选中顺序 001/002/…），用于文件命名（`docs/02-{seq}-{功能}.md`、`prompts/03-{seq}-{功能}.md`）；未选中的无 seq。
- `features` 每条的 status：`skipped`（未选中）/ `prompted`（仅提示词完成）/ `done`（文档完成）。
- 断点续跑：重跑时先读 progress.json，跳过已 `done` 的功能，只补未完成的。

## 边界处理

- **第 0 步探测到 01/02 部分缺失**（如只有 01 无 02）：补齐缺失的那个（dispatch 对应 skill），不重跑已有的。
- **用户未挑选任何功能**：在第 2 步提示并等待，不进入第 3 步；或默认建议选核心度=核心的前 N 个，但需用户确认。
- **某功能 doc 生成失败**：progress.json 该功能 status 留 `prompted`，doc 字段标"待生成"，继续其它功能；lp-index 会标注"待生成"。
- **大项目功能过多**：依赖 lp-feature-scan 的排序与大项目取舍；第 2 步引导用户聚焦核心度=核心的功能，避免全量生成。
- **断点续跑**：检测到 progress.json 已存在时，询问用户是"续跑（补未完成）"还是"重跑（清空重来）"。

## 执行检查清单

执行 learn-project 时，按以下顺序完成：

1. [ ] 第 0 步：探测 project-knowledge/01、02；缺失则 dispatch pm-scan/pm-techstack 补齐
2. [ ] 创建/续读 `_meta/progress.json`（写 projectName/generatedAt/sourceCommit）
3. [ ] 第 1 步：dispatch lp-feature-scan → 01-001-功能清单.md
4. [ ] 第 2 步：呈现 inventory，人在回路挑选，记录 selected
5. [ ] 第 3 步：对每个选中功能 dispatch lp-prompt-gen（产出提示词）→ 用提示词 dispatch doc subagent（产出文档），逐个更新 progress.json
6. [ ] 第 4 步：执行 lp-index → README.md
7. [ ] 自检：
    - [ ] 第 0 步未重复扫描（A 已有就复用）？
    - [ ] 只对选中功能生成、且文档由提示词驱动？
    - [ ] progress.json 真实反映状态、generatedAt 真实？
    - [ ] 产出五类齐备（README/inventory/prompts/docs/_meta）？
    - [ ] doc 文档引用的代码路径真实、零臆造？
