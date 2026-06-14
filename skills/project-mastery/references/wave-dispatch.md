# project-mastery 波次 dispatch 指令模板（按需读取）

> 执行各波次 dispatch subagent 时读取本文件，按对应模板构造精确指令。
> 本文件由 project-mastery SKILL.md 抽出，供编排器执行时按需加载（progressive disclosure）。

## 波次 1：dispatch pm-scan

```
你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-scan/SKILL.md` 的全部指令，对目标项目 `{PROJECT_ROOT}` 执行 pm-scan。

**输入**：`PROJECT_ROOT = {PROJECT_ROOT绝对路径}`

**产出**（必须写到这三个绝对路径）：
- `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`
- `{PROJECT_ROOT}/.codebase/scan-result.json`
- `{PROJECT_ROOT}/.codebase/scan-summary.md`

按 pm-scan 的"执行检查清单"逐项完成，自检通过后结束。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**
```

## 波次 2：4 个并行 dispatch 指令模板（同一轮 assistant 消息发出 4 个 Agent 调用，不要等一个回来再发下一个）

波次 2 开始前先读 `.codebase/scan-result.json` 的 `classifications`（取 `is_primary=true`）作路由依据。

### dispatch A — pm-techstack-generic

```
你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-techstack-generic/SKILL.md` 的全部指令，对目标项目执行技术栈与架构分析。

**输入**：
- `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
- 上下文：`{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1 产出，提供项目类型、目录结构、入口点、顶层技术栈速览）

**产出**：`{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`

按 pm-techstack-generic 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**
```

### dispatch B — pm-conventions

```
你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-conventions/SKILL.md` 的全部指令，对目标项目执行开发规范提取。

**输入**：
- `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
- 上下文：`{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1 产出，提供目录结构、入口点）
- 上下文：`{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`（波次 2 并行同伴产出，提供自封装框架位置、模块依赖）—— **若 02 尚未写完，先等波次 2 全部完成后再读本文件**；若与其他同伴并行读到半成品，以实际内容为准并在自检里标注。

**产出**：`{PROJECT_ROOT}/docs/project-knowledge/03-开发规范.md`

按 pm-conventions 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**
```

### dispatch C — pm-api-index

```
你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-api-index/SKILL.md` 的全部指令，对目标项目执行 API 索引生成。

**输入**：
- `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
- 上下文：`{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1 产出，提供项目类型、目录结构）
- 上下文：`{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`（波次 2 并行同伴产出，提供自封装框架位置、模块依赖、SPI 解耦接口位置）

**产出**：`{PROJECT_ROOT}/docs/project-knowledge/04-API索引.md`

按 pm-api-index 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**
```

### dispatch D — pm-build-deploy

```
你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-build-deploy/SKILL.md` 的全部指令，对目标项目执行构建打包部署梳理。

**输入**：
- `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
- 上下文：`{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`（波次 1 产出，提供多模块划分、技术栈）
- 上下文：`{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`（波次 2 并行同伴产出，提供模块依赖）

**产出**：`{PROJECT_ROOT}/docs/project-knowledge/05-构建打包部署.md`

按 pm-build-deploy 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**
```

## 波次 4：dispatch pm-verify

```
你是 project-mastery 编排器 dispatch 的子 agent。请读并严格遵循 `~/.claude/skills/pm-verify/SKILL.md` 的全部指令，对目标项目的知识库执行抽样校验。

**输入**：
- `PROJECT_ROOT = {PROJECT_ROOT绝对路径}`
- 已生成的全部 KB 文档：`{PROJECT_ROOT}/docs/project-knowledge/` 下的 01-05 + README + `{PROJECT_ROOT}/.codebase/scan-result.json`

**产出**：`{PROJECT_ROOT}/docs/project-knowledge/06-校验报告.md`

**关键约束**：pm-verify **只报告不修改**——发现任何不一致，写入报告的"不一致项清单"，**禁止 Edit/Write 任何已生成的 KB 文档（01-05、README、_meta/*）**。

按 pm-verify 的"执行检查清单"逐项完成。**不要使用 TaskCreate/TaskUpdate/TodoWrite 工具。**
```
