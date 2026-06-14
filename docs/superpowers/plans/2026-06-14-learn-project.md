# learn-project 实现计划（子项目 B）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建一套通用 skills（learn-project + 3 个 lp-* 子 skill），对任意已有项目：复用 A 的扫描底座定位 → 扫描功能 → 人在回路挑选 → 逐功能生成教学提示词+学习文档 → 汇编学习路径索引。

**Architecture:** 顶层 skill `learn-project`（主会话编排）+ `lp-feature-scan`（功能识别，agent）+ `lp-prompt-gen`（教学提示词，agent）+ `lp-index`（学习路径索引，主会话）。doc 生成由 orchestrator 用保存的提示词 dispatch 通用 subagent，不单独成 skill。产出落 `{PROJECT_ROOT}/docs/learning-docs/`，复用（不修改）A 的 pm-scan/pm-techstack-generic。

**Tech Stack:** Claude Code skills（SKILL.md + YAML frontmatter），superpowers writing-skills TDD，subagent-driven-development。

**测试靶子**：`dsp`（gitignored，仅用于验证，不进 skill 源码）。

**通用化纪律**：每个 SKILL.md 写完立即 `grep -rni "dsp" skills/*/SKILL.md` 自检，0 命中。压力场景放 `docs/skill-design/<skill>/`。

---

## File Structure

| 文件 | 职责 |
|---|---|
| `skills/lp-feature-scan/SKILL.md` | 功能识别方法论（5 层扫描），产出 inventory.md |
| `skills/lp-prompt-gen/SKILL.md` | 教学提示词生成，产出 prompts/{feature}.md |
| `skills/lp-index/SKILL.md` | 学习路径索引 README 汇编（主会话） |
| `skills/learn-project/SKILL.md` | 顶层编排：定位→扫描→挑选→生成→索引 |
| `docs/skill-design/lp-feature-scan/pressure-scenario.md` | TDD 压力场景 |
| `docs/skill-design/lp-prompt-gen/pressure-scenario.md` | TDD 压力场景 |
| `docs/skill-design/lp-index/pressure-scenario.md` | TDD 压力场景 |
| `docs/skill-design/learn-project/pressure-scenario.md` | TDD 压力场景 |

构建顺序：先叶 skill（feature-scan → prompt-gen → index），后 orchestrator（learn-project），最后软链+e2e+通用化自检。

每个 skill 任务的 TDD 步骤（writing-skills 适配方法论 skill）：
1. 写压力场景（失败模式 → 验证方式 → GREEN 规则）
2. Baseline RED：在 dsp 上不依赖该 skill 尝试产出，确认缺失/失败
3. 写 SKILL.md
4. GREEN：dispatch agent 按 SKILL.md 在 dsp 上执行，验证产出满足 GREEN 规则
5. 通用化自检 + 提交

---

### Task 1: lp-feature-scan（功能识别核心能力）

**Files:**
- Create: `skills/lp-feature-scan/SKILL.md`
- Create: `docs/skill-design/lp-feature-scan/pressure-scenario.md`
- Output (验证用，gitignored): `dsp/docs/learning-docs/features/inventory.md`

- [ ] **Step 1: 写压力场景**

`docs/skill-design/lp-feature-scan/pressure-scenario.md` 含三段：
- **失败模式**：扫描项目时把功能识别成"一堆文件/目录罗列"或"业界通用功能清单"，而非项目特定、可学习的功能单元；功能粒度过细或过粗；清单缺核心度/依赖/证据字段导致无法排序与深挖。
- **验证方式**：在 dsp 上跑 lp-feature-scan，产出 `inventory.md`，检查：①每条是项目特定功能（非通用 CRUD 模板）；②含核心度/复杂度/依赖/证据四字段；③证据是真实路径+说明；④按核心度排序；⑤每条带 `[ ]` 勾选框供人在回路。
- **GREEN 规则**：inventory.md 至少识别出 dsp 的多个项目特定功能（如核心业务能力、自封装框架能力等，不点名具体业务，由执行者据实识别），每条四字段齐全且证据真实可验证，零臆造。

- [ ] **Step 2: Baseline RED**

在 dsp 上不写 skill，直接尝试让模型产出功能清单 → 应出现"通用模板化/缺字段/证据不可验证"等问题（或根本无结构化产出）。记录 RED 现象到压力场景。

- [ ] **Step 3: 写 SKILL.md**

`skills/lp-feature-scan/SKILL.md`，参照 spec §6（5 层扫描：文档层/结构层/入口层/示例层/聚类去重）+ §字段 + §边界处理。description 写"当需要在已有项目中识别可学习的功能、产出功能清单时使用"。零项目特定内容。

- [ ] **Step 4: GREEN 验证**

dispatch agent 读 SKILL.md，对 dsp 执行，产出 `dsp/docs/learning-docs/features/inventory.md`。按 GREEN 规则逐条核对。

- [ ] **Step 5: 通用化自检 + 提交**

`grep -rni "dsp" skills/lp-feature-scan/SKILL.md`（0 命中）。`git add` + 提交。

---

### Task 2: lp-prompt-gen（教学提示词生成）

**Files:**
- Create: `skills/lp-prompt-gen/SKILL.md`
- Create: `docs/skill-design/lp-prompt-gen/pressure-scenario.md`
- Output: `dsp/docs/learning-docs/features/prompts/{feature}.md`

- [ ] **Step 1: 写压力场景**

失败模式：提示词太泛（"请讲讲这个功能"），没列出要读的具体证据代码 → doc-gen subagent 臆造；没规定学习目标/文档结构/受众 → 产出跑偏。
验证方式：对 inventory.md 中选中的功能跑 lp-prompt-gen，产出 prompts/{feature}.md，检查含：①必读证据（真实路径+说明）；②学习目标；③6 节文档结构；④受众声明；⑤撰写要求。
GREEN 规则：每个提示词的"必读证据"列出的文件在 dsp 中真实存在且指向该功能核心；结构完整可复用重跑。

- [ ] **Step 2: Baseline RED** — 不写 skill 直接让模型生成提示词 → 应缺证据清单/学习目标。记录。

- [ ] **Step 3: 写 SKILL.md** — 参照 spec §8 模板 + §5.3 核心原则。零项目特定内容。

- [ ] **Step 4: GREEN 验证** — dispatch agent 对 dsp 的选中功能执行，产出 prompts/{feature}.md，按 GREEN 规则核对（证据路径真实存在）。

- [ ] **Step 5: 通用化自检 + 提交。**

---

### Task 3: lp-index（学习路径索引，主会话）

**Files:**
- Create: `skills/lp-index/SKILL.md`
- Create: `docs/skill-design/lp-index/pressure-scenario.md`
- Output: `dsp/docs/learning-docs/README.md`

- [ ] **Step 1: 写压力场景**

失败模式：README 写成纯目录树；缺学习路径排序；编造生成时间；未区分已生成/未生成文档给死链。
验证方式：跑 lp-index 产出 README.md，检查 5 条铁律（spec §5.4）：项目一句话简介+链接 01/02；每文档"何时读"；学习路径≥1 条且按依赖排序；元信息从 _meta/progress.json 读、缺失标注不编造；区分已生成/未生成。
GREEN 规则：README 含可用的学习路径（先读 X 再读 Y），元信息时间来自 _meta 不编造，死链 0 个。

- [ ] **Step 2: Baseline RED** — 不写 skill 直接汇编 → 应成目录树/编造时间。记录。

- [ ] **Step 3: 写 SKILL.md** — 参照 spec §5.4 铁律 + §9 元信息读取规则（_meta/progress.json）。零项目特定内容。

- [ ] **Step 4: GREEN 验证** — 主会话执行（或 dispatch agent 模拟），产出 README.md，按 GREEN 规则核对。

- [ ] **Step 5: 通用化自检 + 提交。**

---

### Task 4: learn-project（顶层编排）

**Depends on:** Task 1-3 完成。

**Files:**
- Create: `skills/learn-project/SKILL.md`
- Create: `docs/skill-design/learn-project/pressure-scenario.md`
- Output: `dsp/docs/learning-docs/` 全流程产出 + `_meta/progress.json`

- [ ] **Step 1: 写压力场景**

失败模式：第 0 步不复用 A 的 01/02 重复扫描；没做人在回路挑选就对全部功能生成；doc-gen 没用保存的提示词；不维护 progress.json 导致无法断点续跑/索引编造时间。
验证方式：在 dsp 上跑 learn-project 全流程，检查：①第 0 步探测到 project-knowledge/01、02 则复用、否则 dispatch pm-scan/pm-techstack；②呈现 inventory 供挑选；③只对选中功能 dispatch lp-prompt-gen + doc subagent；④产出 docs/{feature}.md；⑤维护 progress.json。
GREEN 规则：全流程产出齐备（README/inventory/prompts/docs/_meta），doc 文档引用的代码路径真实，零臆造。

- [ ] **Step 2: Baseline RED** — 不写 orchestrator，手动分步跑 → 记录缺乏编排/无 progress 的问题。

- [ ] **Step 3: 写 SKILL.md** — 参照 spec §4 流程 + §5.1 关键行为 + §5.4 编排职责。description 写"当需要对已有项目生成学习文档（功能扫描→挑选→逐功能生成→学习路径索引）时使用"。零项目特定内容。

- [ ] **Step 4: GREEN 验证（端到端）** — 在 dsp 上跑通 learn-project 全流程，产出 `dsp/docs/learning-docs/` 全部产物，按 GREEN 规则核对。

- [ ] **Step 5: 通用化自检 + 提交。**

---

### Task 5: 软链 + 全局通用化自检 + 验收

- [ ] **Step 1: 软链新 skills** — `bash scripts/link-skills.sh`，确认 learn-project、lp-feature-scan、lp-prompt-gen、lp-index 软链到 ~/.claude/skills/。

- [ ] **Step 2: 全局通用化自检** — `grep -rni "dsp" skills/{learn-project,lp-feature-scan,lp-prompt-gen,lp-index}/SKILL.md`（0 命中）；确认产出里 dsp 内容只在 `dsp/docs/learning-docs/` 与 `docs/skill-design/` 压力场景。

- [ ] **Step 3: 端到端验收记录** — 写 `docs/superpowers/plans/2026-06-14-learn-project-验收.md`，记录全流程跑通结果、4 个 skill 的 TDD RED/GREEN、通用化自检、延后项。

- [ ] **Step 4: 提交 + finishing-a-development-branch** — 提交，用 superpowers:finishing-a-development-branch 收尾（验证、呈现选项、合入 main）。
