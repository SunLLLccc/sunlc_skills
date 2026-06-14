---
name: project-mastery
description: 当需要接手一个已有项目、判断走"学习/更新/开发"哪条子流程并按波次调度 project-mastery 工具集各 skill 完成项目知识库建设或开发时使用。
---

# project-mastery — 顶层编排与学习子流程串联

## 定位

project-mastery 是 project-mastery 工具集的**顶层编排 skill**。它本身不做源码分析，而是：

1. **入口判定**：检查目标项目的知识库状态，决定走【学习】/【更新】/【开发】哪条子流程。
2. **按波次调度**：把 7 个子 skill（pm-scan / pm-techstack-generic / pm-conventions / pm-api-index / pm-build-deploy / pm-kb-index / pm-verify）串成完整学习管线，按依赖关系分波次执行（波次 2 内部并行）。
3. **dispatch 编排**：用 Agent 工具 dispatch subagent 执行各子 skill（方式 A 按需 dispatch 兜底），主会话只做编排与汇编，不亲自做源码分析。
4. **收尾汇编**：写 `_meta/manifest.json` 记录本次知识库的源码版本、生成时间、skill 版本，供【更新】子流程 diff 判定。

与"自己直接读源码写文档"的区别：本 skill 把"学习一个项目"这件重活**拆解为有依赖关系的波次 + 并行 dispatch**，避免主会话上下文爆炸、避免子 skill 乱序执行、避免漏波次或漏写 manifest。每个子 skill 在隔离的 subagent 上下文里执行，产出格式由各自 SKILL.md 保证。

**期 1 实现范围**：本 skill 完整实现【学习】子流程（波次 1-4 + 收尾）。【更新】与【开发】子流程在本 skill 末尾以 stub 形式给出方向性说明，具体逻辑留到期 2/3 实现（YAGNI）。

## 输入

- `PROJECT_ROOT`：目标项目的根目录绝对路径

## 产出

按子流程不同，产出不同。**【学习】子流程**（期 1 实现）产出：

- `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1，pm-scan 产）
- `{PROJECT_ROOT}/docs/project-knowledge/_meta/project-type.json`（波次 1，pm-scan 产）
- `{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`（波次 2，pm-techstack-generic 产）
- `{PROJECT_ROOT}/docs/project-knowledge/03-开发规范.md`（波次 2，pm-conventions 产）
- `{PROJECT_ROOT}/docs/project-knowledge/04-API索引.md`（波次 2，pm-api-index 产）
- `{PROJECT_ROOT}/docs/project-knowledge/05-构建打包部署.md`（波次 2，pm-build-deploy 产）
- `{PROJECT_ROOT}/docs/project-knowledge/README.md`（波次 3，pm-kb-index 产）
- `{PROJECT_ROOT}/docs/project-knowledge/06-校验报告.md`（波次 4，pm-verify 产）
- `{PROJECT_ROOT}/docs/project-knowledge/_meta/manifest.json`（收尾，主会话写）

## 入口判定逻辑（开工第一步，必须执行且必须显式声明）

开工第一件事不是扫描，是**判定走哪条子流程**。按以下优先级（从高到低，命中即定）：

| 优先级 | 判定条件 | 走哪条子流程 | 期 1 状态 |
|--------|----------|--------------|-----------|
| ① 最高 | 目标项目存在**需求文档**（如 `{PROJECT_ROOT}/需求.md`、`{PROJECT_ROOT}/docs/需求*.md`、issue 列表、`REQUIREMENTS.md` 等） | 【开发】 | stub（期 3 实现） |
| ② | `{PROJECT_ROOT}/docs/project-knowledge/` **不存在**，或存在但 `_meta/manifest.json` **缺失**（半成品 KB） | 【学习】 | ✅ 期 1 实现 |
| ③ | `{PROJECT_ROOT}/docs/project-knowledge/` 存在**且** `_meta/manifest.json` 存在**且**代码相对 manifest 记录的 sourceCommit 有变化 | 【更新】 | stub（期 2 实现） |
| ④ 默认 | 以上都不命中（如 KB 存在、manifest 存在、代码未变） | 提示"知识库已是最新，无需重新学习"，结束 | — |

**判定执行步骤**：

1. `ls {PROJECT_ROOT}/docs/project-knowledge/ 2>&1` —— 看 KB 目录是否存在、有哪些文件。
2. `ls {PROJECT_ROOT}/docs/project-knowledge/_meta/ 2>&1` —— 看 `_meta/` 下是否有 `project-type.json` 和 `manifest.json`。
3. 探测需求文档：`ls {PROJECT_ROOT}/{需求.md,REQUIREMENTS.md,docs/需求*.md} 2>&1`（按项目实际探测常见需求文档名）。
4. 若 manifest 存在，读它的 `sourceCommit` 字段，与 `git -C {PROJECT_ROOT} rev-parse HEAD`（若有 .git）比对，判断代码是否变化。

**强制要求：判定结果必须显式声明**。开工第一句话必须是类似：

> "入口判定：未检测到需求文档；检测到 `docs/project-knowledge/` 不存在（或 manifest 缺失）；走【学习】子流程。"

不允许跳过判定直接开工，也不允许判定了但不声明（使用者必须知道为什么走了某条子流程）。

## 【学习】子流程（期 1 实现）

### 总览：波次 1 → 波次 2（并行）→ 波次 3 → 波次 4 → 收尾

```
入口判定 →【学习】
  ├─ 波次 1：dispatch pm-scan        → 产 01 + project-type.json
  ├─ 波次 2：读 project-type.json，同一轮并行 dispatch 4 个 subagent
  │           ├─ pm-techstack-generic → 产 02
  │           ├─ pm-conventions       → 产 03
  │           ├─ pm-api-index         → 产 04
  │           └─ pm-build-deploy      → 产 05
  ├─ 波次 3：主会话执行 pm-kb-index   → 产 README
  ├─ 波次 4：dispatch pm-verify       → 产 06
  └─ 收尾：主会话写 manifest.json
```

**波次间的硬依赖**（不可乱序）：
- 波次 2 全部依赖波次 1 的 `01-项目概览.md`（作为上下文输入）和 `project-type.json`（路由依据）。
- 波次 3（README）依赖波次 2 全部产出（要读 02-05 汇编索引）。
- 波次 4（verify）依赖波次 1-3 全部产出（要校验 01-05 + README）。
- 收尾（manifest）依赖波次 1-4 全部产出（要记录全部文档的生成状态）。

### 波次 1：dispatch pm-scan

**执行方式**：用 Agent 工具 dispatch 1 个 subagent。

**dispatch 指令模板**（精确）：

> 你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-scan/SKILL.md` 的全部指令，对目标项目 `{PROJECT_ROOT}` 执行 pm-scan。
>
> **输入**：`PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
>
> **产出**（必须写到这两个绝对路径）：
> - `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`
> - `{PROJECT_ROOT}/docs/project-knowledge/_meta/project-type.json`
>
> 按 pm-scan 的"执行检查清单"逐项完成，自检通过后结束。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**

**前置依赖**：入口判定已声明走【学习】。
**本波次产出**：`01-项目概览.md` + `_meta/project-type.json`。
**波次 1 完成标志**：上述两个文件都已写入，且 `project-type.json` 的 `types` / `primaryType` 字段有值。

### 波次 2：读 project-type.json 后，同一轮并行 dispatch 4 个分析 subagent

**执行方式**：**在同一轮 assistant 消息里**发出 4 个 Agent 工具调用（不要等一个回来再发下一个）。这是本子流程的并行收益点——4 个分析维度彼此正交，无共享上下文，可真正并发。

**波次 2 开始前的动作**（主会话执行）：
1. 读 `{PROJECT_ROOT}/docs/project-knowledge/_meta/project-type.json`，确认 `types` / `primaryType`。
2. 读 `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`，确认上下文可用。
3. （可选）按 primaryType 决定波次 2 是否用特化 skill——期 1 统一用 `pm-techstack-generic`（通用兜底）；期 2 实现 `pm-techstack-frontend/backend/fullstack` 特化后再按 primaryType 路由。

**4 个并行 dispatch 指令模板**（每个都精确指明输入上下文、遵循哪个 skill、产出什么文件）：

**dispatch A — pm-techstack-generic**：

> 你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-techstack-generic/SKILL.md` 的全部指令，对目标项目执行技术栈与架构分析。
>
> **输入**：
> - `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
> - 上下文：`{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1 产出，提供项目类型、目录结构、入口点、顶层技术栈速览）
>
> **产出**：`{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`
>
> 按 pm-techstack-generic 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**

**dispatch B — pm-conventions**：

> 你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-conventions/SKILL.md` 的全部指令，对目标项目执行开发规范提取。
>
> **输入**：
> - `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
> - 上下文：`{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1 产出，提供目录结构、入口点）
> - 上下文：`{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`（波次 2 并行同伴产出，提供自封装框架位置、模块依赖）—— **若 02 尚未写完，先等波次 2 全部完成后再读本文件**；若与其他同伴并行读到半成品，以实际内容为准并在自检里标注。
>
> **产出**：`{PROJECT_ROOT}/docs/project-knowledge/03-开发规范.md`
>
> 按 pm-conventions 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**

**dispatch C — pm-api-index**：

> 你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-api-index/SKILL.md` 的全部指令，对目标项目执行 API 索引生成。
>
> **输入**：
> - `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
> - 上下文：`{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1 产出，提供项目类型、目录结构）
> - 上下文：`{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`（波次 2 并行同伴产出，提供自封装框架位置、模块依赖、SPI 解耦接口位置）
>
> **产出**：`{PROJECT_ROOT}/docs/project-knowledge/04-API索引.md`
>
> 按 pm-api-index 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**

**dispatch D — pm-build-deploy**：

> 你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-build-deploy/SKILL.md` 的全部指令，对目标项目执行构建打包部署梳理。
>
> **输入**：
> - `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
> - 上下文：`{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1 产出，提供多模块划分、技术栈）
> - 上下文：`{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`（波次 2 并行同伴产出，提供模块依赖）
>
> **产出**：`{PROJECT_ROOT}/docs/project-knowledge/05-构建打包部署.md`
>
> 按 pm-build-deploy 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**

**关于波次 2 内部依赖的说明**：pm-conventions / pm-api-index / pm-build-deploy 在各自 SKILL.md 里都声明"以 02-技术栈与架构.md 为上下文输入"。理论上它们应串行在 02 之后。但实践上：

- **并行收益 >> 串行精确性**：4 个分析维度工作量都很大，串行耗时 4 倍；并行虽有"02 可能尚未写完"的风险，但 02 的核心信息（自封装框架位置、模块依赖）在 pm-scan 的 01 里已有雏形（目录结构、顶层技术栈速览），各分析 subagent 即使 02 未就绪也能基于 01 启动，待 02 就绪后补充。
- **并行 dispatch 指令里已写明"若 02 尚未写完，以 01 为主、02 为辅"**，让 subagent 自适应。
- **这是期 1 的务实选择**。若发现并行导致质量下降（如 API 索引漏了 SPI 接口因 02 未就绪），期 2 可调整为"02 串行先行，03/04/05 并行"。

**前置依赖**：波次 1 完成（01 + project-type.json 已写入）。
**本波次产出**：02 + 03 + 04 + 05 四份文档。
**波次 2 完成标志**：上述 4 个文件都已写入（4 个 subagent 全部返回）。

### 波次 3：主会话执行 pm-kb-index 产 README

**执行方式**：**主会话直接执行**（不 dispatch subagent）。原因：pm-kb-index 的 SKILL.md 明确写"由主会话执行，非 agent"——它只汇编已有文档的索引，不做源码分析，无需隔离上下文。

**执行步骤**（主会话）：
1. 读 `~/.claude/skills/pm-kb-index/SKILL.md`，遵循其全部指令。
2. `ls {PROJECT_ROOT}/docs/project-knowledge/`，确认 01-05 已生成。
3. 读 01-05 全部文档 + `_meta/project-type.json`，提炼"何时读"触发条件与一句话定位。
4. 写 `{PROJECT_ROOT}/docs/project-knowledge/README.md`，按 pm-kb-index 的模板（含项目一句话简介、文档地图、任务型阅读路径 ≥2 条、元信息章节）。
5. **注意**：此时 `_meta/manifest.json` 尚未写（收尾才写），README 的元信息章节里 `manifest.json` 相关字段标注"未生成（收尾步骤尚未执行）"或从 project-type.json 读已有字段，不编造。

**前置依赖**：波次 2 全部完成（02-05 已写入）。
**本波次产出**：`README.md`。
**波次 3 完成标志**：README.md 已写入，自检通过（项目一句话简介、每份文档"何时读"、≥2 条任务路径、元信息章节齐全）。

### 波次 4：dispatch pm-verify 产 06 校验报告

**执行方式**：用 Agent 工具 dispatch 1 个 subagent。

**dispatch 指令模板**：

> 你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-verify/SKILL.md` 的全部指令，对目标项目的知识库执行抽样校验。
>
> **输入**：
> - `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
> - 已生成的全部 KB 文档：`{PROJECT_ROOT}/docs/project-knowledge/` 下的 01-05 + README + `_meta/project-type.json`
>
> **产出**：`{PROJECT_ROOT}/docs/project-knowledge/06-校验报告.md`
>
> **关键约束**：pm-verify **只报告不修改**——发现任何不一致，写入报告的"不一致项清单"，**禁止 Edit/Write 任何已生成的 KB 文档（01-05、README、_meta/*）**。
>
> 按 pm-verify 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**

**前置依赖**：波次 1-3 全部完成（01-05 + README 已写入）。
**本波次产出**：`06-校验报告.md`。
**波次 4 完成标志**：06 已写入，自检通过（三元组、四分类、抽样范围声明、未修改任何 KB 文档）。

**关于 verify 发现不一致后的处理**：pm-verify 只报告不修改。发现的不一致项写入 06 报告的"不一致项清单"，由**人工**决定是否修订 KB 文档。本编排 skill 不自动触发修订（那是【更新】子流程的职责，期 2 实现）。收尾写 manifest 时，把 verify 的总体结论（如"发现 N 条不一致"）记入 manifest 的 `verificationStatus` 字段。

### 收尾：主会话写 `_meta/manifest.json`

**执行方式**：**主会话直接写**（不 dispatch subagent）。原因：manifest 只是汇编本次运行的元信息，无需源码分析。

**这是 baseline 最易漏的步骤**——7 个子 skill 没有一个负责写 manifest（pm-kb-index 只读它不写它）。manifest 是**顶层编排的专属职责**，必须在波次 4 之后由主会话写。

**执行步骤**（主会话）：
1. `git -C {PROJECT_ROOT} rev-parse HEAD 2>&1` —— 获取源码 commit（若无 .git，标注 null）。
2. `date -u +"%Y-%m-%dT%H:%M:%SZ"` —— 获取当前 UTC 时间作为 generatedAt。
3. 读 `_meta/project-type.json` 的 `projectName` / `types` / `primaryType` / `scannedAt` / `scanVersion`。
4. 读 06-校验报告的总体结论，提炼 verificationStatus。
5. `ls {PROJECT_ROOT}/docs/project-knowledge/` 确认全部文档生成状态。
6. 写 `{PROJECT_ROOT}/docs/project-knowledge/_meta/manifest.json`，按下述模板。

**manifest.json 模板**：

```json
{
  "projectName": "{从 project-type.json 读}",
  "projectRoot": "{PROJECT_ROOT绝对路径}",
  "projectType": {
    "types": ["{从 project-type.json 读}"],
    "primaryType": "{从 project-type.json 读}",
    "confidence": "{从 project-type.json 读}"
  },
  "generatedAt": "{UTC ISO 8601 时间戳，本次 KB 生成完成时刻}",
  "scannedAt": "{从 project-type.json 读 pm-scan 的 scannedAt，KB 生成起始时刻}",
  "sourceCommit": "{git rev-parse HEAD，无 git 则 null}",
  "sourceVersion": "{若有版本号（如 pom.xml/package.json 的 version），填；否则 null}",
  "pipeline": "project-mastery v1（期 1 学习子流程）",
  "skillVersions": {
    "pm-scan": "{从 project-type.json 的 scanVersion 读}",
    "pm-techstack-generic": "v1",
    "pm-conventions": "v1",
    "pm-api-index": "v1",
    "pm-build-deploy": "v1",
    "pm-kb-index": "v1",
    "pm-verify": "v1"
  },
  "kbDocs": [
    {"id": "01", "file": "01-项目概览.md", "skill": "pm-scan", "status": "generated"},
    {"id": "02", "file": "02-技术栈与架构.md", "skill": "pm-techstack-generic", "status": "generated"},
    {"id": "03", "file": "03-开发规范.md", "skill": "pm-conventions", "status": "generated"},
    {"id": "04", "file": "04-API索引.md", "skill": "pm-api-index", "status": "generated"},
    {"id": "05", "file": "05-构建打包部署.md", "skill": "pm-build-deploy", "status": "generated"},
    {"id": "README", "file": "README.md", "skill": "pm-kb-index", "status": "generated"},
    {"id": "06", "file": "06-校验报告.md", "skill": "pm-verify", "status": "generated"}
  ],
  "verificationStatus": "{从 06 报告提炼：如 'passed（抽样 N 条全部一致）' / 'partial（发现 M 条不一致）' / 'failed'}",
  "subprocess": "learning"
}
```

**前置依赖**：波次 1-4 全部完成。
**收尾完成标志**：`_meta/manifest.json` 已写入，字段齐全。

### 【学习】子流程完成标志

以下全部满足才算【学习】子流程完成：

- [ ] 入口判定已显式声明走【学习】
- [ ] 波次 1：`01-项目概览.md` + `_meta/project-type.json` 已写入
- [ ] 波次 2：`02` + `03` + `04` + `05` 四份文档已写入，且 4 个 dispatch 在同一轮并行
- [ ] 波次 3：`README.md` 已写入
- [ ] 波次 4：`06-校验报告.md` 已写入
- [ ] 收尾：`_meta/manifest.json` 已写入

## dispatch 策略

### 方式 A（期 1 兜底，当前实现）：按需 dispatch general-purpose subagent

期 1 没有"预定义 agent"（方式 B），用通用 `general-purpose` subagent 兜底。**关键约定**：dispatch 指令里必须明确写"读并严格遵循 `~/.claude/skills/<skill名>/SKILL.md`"，让 subagent 在隔离上下文里加载子 skill 的指令执行。

**方式 A 的 dispatch 指令必须包含的要素**（每个波次的指令模板已在上文给出，此处是通用要素清单）：

| 要素 | 要求 |
|------|------|
| 子 agent 身份声明 | "你是 project-mastery 编排器 dispatch 的子 agent" |
| 遵循哪个 skill | "读并严格遵循 `~/.claude/skills/<skill名>/SKILL.md`" |
| 输入：PROJECT_ROOT | 绝对路径 |
| 输入：上下文文档 | 指明读哪几份已生成的 KB 文档作为上下文（如 01、02） |
| 产出：文件绝对路径 | 指明产出写到哪个绝对路径 |
| 工具约束 | "不要使用 TaskCreate/TaskUpdate/TodoWrite 工具" |
| 自检要求 | "按该 skill 的执行检查清单逐项完成，自检通过后结束" |

**不要犯的错**：
- ❌ `subagent_type: "pm-api-index"`（pm-api-index 是 skill 不是 subagent type，工具会拒绝）
- ❌ dispatch 指令只写"分析一下技术栈"（含糊，subagent 不知道读哪个 SKILL.md、产出什么）
- ❌ 主会话自己 Read 源码写 02-05（上下文爆炸，违反"子 skill 在隔离上下文执行"的设计）

### 方式 B（期 4 预留）：预定义 agent

期 4 计划为每个子 skill 定义专用的 subagent type（如 `pm-api-index` 成为合法的 subagent_type），届时 dispatch 指令可简化为 `subagent_type: "pm-api-index"`，无需在 prompt 里写"读 SKILL.md"。

**fallback 约定**（方式 B 实现后仍保留）：**预定义 agent 优先，无则按需 dispatch（方式 A）兜底**。即：编排器先尝试用预定义 agent type dispatch；若该 type 不存在（如旧环境未注册），自动 fallback 到 general-purpose + prompt 注入 SKILL.md 路径（方式 A）。这保证 skill 在任何环境都能跑。

### 主会话 vs subagent 的职责划分

| 职责 | 由谁执行 | 原因 |
|------|----------|------|
| 入口判定 | 主会话 | 轻量决策，需全局视角 |
| 波次 1 pm-scan | subagent（dispatch） | 源码扫描，重活，需隔离上下文 |
| 波次 2 四个分析 | subagent（dispatch，并行） | 源码分析，重活，并行收益大 |
| 波次 3 pm-kb-index（README） | **主会话** | 只汇编已有文档索引，不做源码分析，无需隔离（pm-kb-index 的 SKILL.md 明确要求主会话执行） |
| 波次 4 pm-verify | subagent（dispatch） | 校验需读代码对照，重活 |
| 收尾 manifest.json | **主会话** | 只汇编元信息，轻量 |

## 【更新】子流程（stub，期 2 实现）

当入口判定命中优先级 ③（KB 存在 + manifest 存在 + 代码变化）时走【更新】。期 1 不实现具体逻辑，方向性说明：

- 读 `_meta/manifest.json` 的 `sourceCommit` 与当前 `git rev-parse HEAD` diff，识别变化的文件/模块。
- 按变化范围决定重跑哪些波次（如只前端变了，只重跑前端相关分析；如 API 变了，重跑 pm-api-index + pm-verify）。
- 增量更新对应文档，而非全量重建（保留未变化文档的手工修订）。
- 重写 manifest.json 的 sourceCommit 为新 commit。

**期 2 实现时**：补充变化检测策略、增量波次调度规则、manifest diff 字段。

## 【开发】子流程（stub，期 3 实现）

当入口判定命中优先级 ①（有需求文档）时走【开发】。期 1 不实现具体逻辑，方向性说明：

- 读需求文档，拆解为开发任务。
- 若 KB 不完整（01-05 缺失），先走【学习】子流程补齐 KB（开发依赖 KB 提供的规范、架构、API 索引）。
- 按 KB 的规范（03）、架构（02）、API 索引（04）实现需求。
- 开发完成后，触发【更新】子流程刷新受影响的 KB 文档。

**期 3 实现时**：补充需求拆解策略、开发任务调度、与【学习】/【更新】的衔接。

## 执行检查清单

执行 project-mastery 的【学习】子流程时，按以下顺序完成：

1. [ ] **入口判定**：`ls` KB 目录 + `_meta/` + 探测需求文档 + （若 manifest 存在）比对 commit
2. [ ] **显式声明判定结果**：开工第一句话声明走哪条子流程及理由
3. [ ] 若走【学习】：
   - [ ] **波次 1**：dispatch 1 个 pm-scan subagent（指令含 PROJECT_ROOT、遵循 SKILL.md、产出 01 + project-type.json）
   - [ ] 确认波次 1 产出已写入（01 + project-type.json）
   - [ ] **波次 2**：读 project-type.json + 01，**在同一轮**并行 dispatch 4 个分析 subagent（techstack / conventions / api-index / build-deploy）
   - [ ] 确认波次 2 的 4 个产出已写入（02 + 03 + 04 + 05）
   - [ ] **波次 3**：主会话读 pm-kb-index SKILL.md，汇编 README
   - [ ] 确认 README 已写入
   - [ ] **波次 4**：dispatch 1 个 pm-verify subagent
   - [ ] 确认 06 已写入
   - [ ] **收尾**：主会话写 `_meta/manifest.json`（含 sourceCommit / generatedAt / skillVersions / kbDocs / verificationStatus）
4. [ ] 若走【更新】：当前为 stub，声明"【更新】子流程期 2 实现，本次按【学习】全量重建或提示人工处理"
5. [ ] 若走【开发】：当前为 stub，声明"【开发】子流程期 3 实现，本次按【学习】补齐 KB 后提示人工开发"
6. [ ] **自检**：
   - [ ] 入口判定是否显式声明？判定优先级是否正确（需求 > KB完整性 > 默认）？
   - [ ] 波次顺序是否严格 1→2→3→4→收尾？有没有乱序或漏波次？
   - [ ] 波次 2 的 4 个 dispatch 是否在同一轮（并行）？还是串行发了 4 轮？（串行不合格）
   - [ ] 每个 dispatch 指令是否精确（含 PROJECT_ROOT、遵循哪个 SKILL.md、产出什么文件）？
   - [ ] 波次 3（README）和收尾（manifest）是否由主会话执行（非 dispatch）？
   - [ ] `_meta/manifest.json` 是否写入？字段是否齐全（sourceCommit / generatedAt / skillVersions / kbDocs）？
   - [ ] 有没有把任何具体项目路径/标识符硬编码进执行过程？（SKILL.md 本体零项目特定内容，执行时才填 PROJECT_ROOT）
