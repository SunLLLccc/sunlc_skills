# P0 地基：扫描缓存契约 + pm 断点续跑 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 qwen3.6 35b 小模型打地基——把 pm-scan 的扫描产物固化为机器可校验、可跨 skill 复用的 `.codebase/scan-result.json` 契约（退役半成品的 `project-type.json`、统一置信度为三态），并给 pm 学习流程引入 `_meta/progress.json` 断点续跑；顺带修 `link-skills.sh` 分发硬编码。

**Architecture:** 引入 `schemas/codebase-scan-result.schema.json` 作为唯一扫描契约（tri-state 置信度 confirmed/inferred/uncertain，英文枚举+中文展示）；pm-scan 生产该缓存；pm-techstack-generic 作为首个消费端优先读缓存；project-mastery 适配新契约（路由读 scan-result.json 而非 project-type.json）并维护 progress.json（与既有 manifest.json 并列：progress=在飞行态/断点续跑，manifest=完成态记录）。

**Tech Stack:** Claude Code skills（SKILL.md + YAML frontmatter），JSON Schema draft 2020-12，superpowers writing-skills TDD（压力场景→baseline RED→GREEN），bash。

**测试靶子**：`dsp`（gitignored，仅用于 GREEN 验证，不进 skill 源码）。

**通用化纪律**：每个 SKILL.md 改完立即 `grep -rni "dsp" skills/*/SKILL.md` 自检，0 命中。

**范围说明**：本计划只做 `claude优化清单.md` 的 **P2-1 + P0-1 + P0-4**（地基切片）。P0-2（12 skill 瘦身重构）、P0-3（全 skill 预算纪律）、P0-5（pm-verify-lite）留作后续计划。

---

## 关键设计决策（先读）

1. **scan-result.json 是唯一机器契约**。退役 `_meta/project-type.json`（其 types/primaryType 内容被 scan-result.json 的 `classifications` 取代）。避免两份重叠 JSON。
2. **置信度统一三态**：`confirmed`（已确认）/ `inferred`（推断得出）/ `uncertain`（不确定）。机器字段英文枚举，人类文档（01-项目概览.md）用中文标签。退役 pm-scan 现有的 0-1 浮点 + high/medium/low 模型。
3. **progress.json ≠ manifest.json**：
   - `progress.json`：**在飞行态**，每个 phase 跑完即更新 status，支持中断后续跑。
   - `manifest.json`：**完成态记录**，收尾一次性写，供【更新】子流程 diff。两者并列，各司其职。
4. **scan-result.json 落点**：`{PROJECT_ROOT}/.codebase/scan-result.json`（+ `.codebase/scan-summary.md` 人类速览）。schema 在工具集 `schemas/`。
5. **project-type.json 的唯一消费者是 project-mastery**（波次 2 路由 + 收尾 manifest 读字段）。退役它只需改 project-mastery 一处。

---

## File Structure

| 文件 | 职责 | 动作 |
|---|---|---|
| `scripts/link-skills.sh` | 软链 skills/ → ~/.claude/skills/ | 改硬编码路径（Task 1）|
| `schemas/codebase-scan-result.schema.json` | 扫描缓存机器契约 | 新建（Task 2）|
| `skills/pm-scan/SKILL.md` | 项目扫描 | 改：产 scan-result.json + 三态置信度 + 退役 project-type.json（Task 3）|
| `skills/pm-techstack-generic/SKILL.md` | 技术栈深挖 | 改：加 Step 0 读缓存（Task 4）|
| `skills/project-mastery/SKILL.md` | 顶层编排 | 改：路由读 scan-result.json + 维护 progress.json + manifest 适配（Task 5）|
| `docs/skill-design/pm-scan/pressure-scenario.md` | pm-scan TDD 压力场景 | 更新：加缓存产出 + 三态 GREEN 规则（Task 3）|
| `docs/skill-design/pm-techstack-generic/pressure-scenario.md` | pm-techstack TDD 压力场景 | 更新：加缓存复用 GREEN 规则（Task 4）|
| `docs/skill-design/project-mastery/pressure-scenario.md` | project-mastery TDD 压力场景 | 更新：加 scan-result 路由 + progress.json GREEN 规则（Task 5）|
| `docs/superpowers/plans/2026-06-14-p0-scan-cache-foundation-验收.md` | 验收记录 | 新建（Task 6）|

构建顺序：Task 1（小修）→ Task 2（契约）→ Task 3（生产端）→ Task 4（消费端）→ Task 5（编排适配）→ Task 6（验收）。

每个改 SKILL.md 的任务走 TDD：更新压力场景 → baseline RED → 改 SKILL.md → GREEN（dispatch agent 在 dsp 上验证）→ 通用化自检 + 提交。

---

### Task 1: 修 link-skills.sh 硬编码路径（P2-1 当天小修）

**Files:**
- Modify: `scripts/link-skills.sh:4`

- [ ] **Step 1: 改 SRC_DIR 为相对推导**

把 `scripts/link-skills.sh` 第 4 行：

```bash
SRC_DIR="/Users/sunlc/sunlc_work/sunlc_skills/skills"
```

改为：

```bash
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/skills"
```

（`DEST_DIR="$HOME/.claude/skills"` 保持不变，它已是正确的。）

- [ ] **Step 2: 验证从任意 cwd 都能跑**

Run（从 home 目录跑，验证不再依赖 cwd）:

```bash
cd /tmp && bash /Users/sunlc/sunlc_work/sunlc_skills/scripts/link-skills.sh
```

Expected: 输出每个 skill 的 `linked: <name>`，且 `ls -l ~/.claude/skills/pm-scan` 指向工具集的 pm-scan 目录（软链生效）。

- [ ] **Step 3: 通用化自检 + 提交**

```bash
cd /Users/sunlc/sunlc_work/sunlc_skills
grep -n "/Users/sunlc" scripts/link-skills.sh   # 期望 0 命中
git checkout -b p0-scan-cache-foundation
git add scripts/link-skills.sh
git commit -m "fix(scripts): link-skills.sh 用相对路径推导 SRC_DIR，去除个人硬编码"
```

---

### Task 2: 定义 scan-result.json JSON Schema（P0-1 契约 + P1-3 三态）

**Files:**
- Create: `schemas/codebase-scan-result.schema.json`

- [ ] **Step 1: 写 schema 文件**

完整内容（创建 `schemas/codebase-scan-result.schema.json`）:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://sunlc-skills.local/schemas/codebase-scan-result.schema.json",
  "title": "Codebase Scan Result",
  "description": "pm-scan 产出的项目扫描缓存契约。后续 pm/lp skill 优先读取此缓存，避免重复扫描（小模型下尤其关键）。置信度三态：confirmed=已确认 / inferred=推断得出 / uncertain=不确定；机器字段用英文枚举，人类文档用中文标签。",
  "type": "object",
  "required": [
    "schema_version", "project_root", "generated_at", "scanner",
    "project", "classifications", "technologies", "commands",
    "modules", "entrypoints", "documents", "questions"
  ],
  "properties": {
    "schema_version": { "type": "string", "const": "1.0" },
    "project_root": { "type": "string" },
    "generated_at": { "type": "string", "description": "ISO-8601 时间戳，由执行 runner 注入" },
    "scanner": {
      "type": "object",
      "description": "生成此缓存的扫描器标识，供 manifest 引用",
      "required": ["name", "version"],
      "properties": {
        "name": { "type": "string" },
        "version": { "type": "string" }
      }
    },
    "project": {
      "type": "object",
      "required": ["name", "summary", "confidence", "evidence"],
      "properties": {
        "name": { "type": "string" },
        "summary": { "type": "string" },
        "confidence": { "$ref": "#/$defs/confidence" },
        "evidence": { "$ref": "#/$defs/evidence_list" }
      }
    },
    "classifications": {
      "type": "array",
      "description": "项目类型识别（多维度叠加，取代旧 project-type.json 的 types/primaryType）",
      "items": {
        "type": "object",
        "required": ["type", "confidence", "evidence"],
        "properties": {
          "type": { "type": "string", "enum": ["frontend","backend","fullstack","mobile","desktop","cli","library","monorepo","microservices","service","other"] },
          "is_primary": { "type": "boolean", "description": "true 表示该项目最核心的类型（取代旧 primaryType）" },
          "detail": { "type": "string" },
          "confidence": { "$ref": "#/$defs/confidence" },
          "evidence": { "$ref": "#/$defs/evidence_list" }
        }
      }
    },
    "technologies": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "category", "confidence", "evidence"],
        "properties": {
          "name": { "type": "string" },
          "version": { "type": "string" },
          "category": { "type": "string", "enum": ["language","framework","package-manager","build-tool","test-tool","database","runtime","deployment","library","unknown"] },
          "purpose": { "type": "string" },
          "confidence": { "$ref": "#/$defs/confidence" },
          "evidence": { "$ref": "#/$defs/evidence_list" }
        }
      }
    },
    "commands": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "command", "purpose", "confidence", "evidence"],
        "properties": {
          "name": { "type": "string" },
          "command": { "type": "string" },
          "working_directory": { "type": "string" },
          "purpose": { "type": "string", "enum": ["install","dev","build","test","lint","package","deploy","run","unknown"] },
          "confidence": { "$ref": "#/$defs/confidence" },
          "evidence": { "$ref": "#/$defs/evidence_list" }
        }
      }
    },
    "modules": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "path", "role", "confidence", "evidence"],
        "properties": {
          "name": { "type": "string" },
          "path": { "type": "string" },
          "role": { "type": "string" },
          "module_type": { "type": "string" },
          "depends_on": { "type": "array", "items": { "type": "string" } },
          "confidence": { "$ref": "#/$defs/confidence" },
          "evidence": { "$ref": "#/$defs/evidence_list" }
        }
      }
    },
    "entrypoints": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "path", "kind", "confidence", "evidence"],
        "properties": {
          "name": { "type": "string" },
          "path": { "type": "string" },
          "kind": { "type": "string", "enum": ["application","api","cli","frontend","test","script","library","unknown"] },
          "description": { "type": "string" },
          "confidence": { "$ref": "#/$defs/confidence" },
          "evidence": { "$ref": "#/$defs/evidence_list" }
        }
      }
    },
    "documents": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "role"],
        "properties": {
          "path": { "type": "string" },
          "role": { "type": "string" },
          "notes": { "type": "string" }
        }
      }
    },
    "questions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["question", "reason"],
        "properties": {
          "question": { "type": "string" },
          "reason": { "type": "string" },
          "suggested_confirmation": { "type": "string" }
        }
      }
    }
  },
  "$defs": {
    "confidence": {
      "type": "string",
      "enum": ["confirmed", "inferred", "uncertain"],
      "description": "confirmed=已确认（源码/配置/文档直接证据）/ inferred=推断得出（目录/命名/调用关系间接证据）/ uncertain=不确定（证据不足或冲突）"
    },
    "evidence_list": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path"],
        "properties": {
          "path": { "type": "string" },
          "detail": { "type": "string" }
        }
      }
    }
  }
}
```

- [ ] **Step 2: 验证 JSON 合法**

```bash
python3 -c "import json; json.load(open('schemas/codebase-scan-result.schema.json'))" && echo "JSON OK"
```

Expected: `JSON OK`。若本机有 `jsonschema` 库，可选自校 schema 自身合法（非必须）。

- [ ] **Step 3: 提交**

```bash
git add schemas/codebase-scan-result.schema.json
git commit -m "feat(schemas): 新增 scan-result.json 契约（三态置信度，取代 project-type.json）"
```

---

### Task 3: pm-scan 产出 scan-result.json + 三态置信度，退役 project-type.json（P0-1 生产端）

**Files:**
- Modify: `skills/pm-scan/SKILL.md`
- Modify: `docs/skill-design/pm-scan/pressure-scenario.md`
- Output (验证用, gitignored): `dsp/.codebase/scan-result.json`, `dsp/.codebase/scan-summary.md`

- [ ] **Step 1: 更新压力场景（加缓存产出 + 三态 GREEN 规则）**

在 `docs/skill-design/pm-scan/pressure-scenario.md` 末尾追加一节：

```markdown
## 增量 GREEN 规则（扫描缓存契约，2026-06-14 加入）

除原 GREEN 规则外，pm-scan 现在还必须：

1. 产出 `{PROJECT_ROOT}/.codebase/scan-result.json`，且通过 `schemas/codebase-scan-result.schema.json` 结构校验（required 字段齐全）。
2. 产出 `{PROJECT_ROOT}/.codebase/scan-summary.md`（人类速览，一段话）。
3. scan-result.json 的 `classifications` 取代旧 `project-type.json` 的 types/primaryType；不再产出 `project-type.json`。
4. 每条结论的 `confidence` 字段是三态枚举之一（`confirmed`/`inferred`/`uncertain`），不再用 0-1 浮点。
5. 人类文档 `01-项目概览.md` 的置信度展示改为中文标签（已确认/推断得出/不确定），不再用 high/medium/low。
6. 每条结论带 ≥1 条真实 `evidence`（path 必须存在）；无法确认的写入 `questions[]`，不臆造。
```

- [ ] **Step 2: Baseline RED**

在 dsp 上用**旧版** pm-scan（即当前 SKILL.md）跑一次，确认：①不产 `.codebase/scan-result.json`；②仍产 `project-type.json`（0-1 浮点置信度）；③`01-项目概览.md` 用 high/medium/low。记录到压力场景的 RED 现象。可跳过实际跑、直接据 SKILL.md 现状断定（当前 SKILL.md 明确产 project-type.json、用 0-1 置信度、无 .codebase 产出）。

- [ ] **Step 3: 改 pm-scan/SKILL.md**

四处修改：

**(3a) 改 "## 产出" 节**——把现有两条产出改为：

```markdown
## 产出

1. `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md` — 项目概览文档（人类可读）
2. `{PROJECT_ROOT}/.codebase/scan-result.json` — **机器契约**，须符合 `schemas/codebase-scan-result.schema.json`（后续 pm/lp skill 优先读它）
3. `{PROJECT_ROOT}/.codebase/scan-summary.md` — 人类速览（一段话总结项目类型/技术栈/入口/命令）

> 注：旧版产出的 `_meta/project-type.json` 已退役，其内容被 scan-result.json 的 `classifications` 取代。
```

**(3b) 新增 "## 扫描缓存（机器契约，必产）" 节**——插在 "## 产出" 节之后、"## 扫描策略" 节之前：

```markdown
## 扫描缓存（机器契约，必产）

pm-scan 除人类可读的 01 文档外，**必须**产出机器可消费的扫描缓存，供后续 pm/lp skill 复用，避免重复扫描（小模型下尤其关键——重扫既费 context 又易不一致）。

### scan-result.json 写入规则

须符合 `schemas/codebase-scan-result.schema.json`，逐字段：

1. `schema_version` 固定 `"1.0"`；`project_root` 填目标项目绝对路径；`generated_at` 填执行时 ISO-8601 时间戳（`date -u +"%Y-%m-%dT%H:%M:%SZ"`）。
2. `scanner`：`{"name": "pm-scan", "version": "v2"}`（v2 = 引入缓存契约后的版本）。
3. `project`：`name`（从 package.json/pom.xml/README 取）+ `summary`（一句话）+ `confidence`（三态）+ `evidence`。
4. `classifications`：从"类型识别规则"的多维度叠加结果填入。每条带 `type` + `is_primary`（最核心类型标 true，仅 1 条）+ `confidence`（三态）+ `evidence`。**取代旧 types/primaryType**。
5. `technologies`：第 1 层识别到的技术栈（语言/框架/包管理/构建/测试工具），每条带 name/version(可空)/category/purpose/confidence/evidence。
6. `commands`：从配置文件 scripts 字段提取的命令（install/dev/build/test 等），每条带 name/command/working_directory/purpose/confidence/evidence。
7. `modules`：monorepo/多模块项目的子模块，每条带 name/path/role/module_type/depends_on/confidence/evidence。单模块项目可只填 1 条（项目自身）。
8. `entrypoints`：第 2 层定位的入口点，每条带 name/path/kind/description/confidence/evidence。无单一入口则留空数组并在 questions 里说明。
9. `documents`：扫描到的关键文档（README/CLAUDE.md/架构图等），每条带 path/role/notes。
10. `questions`：无法确认的项，每条带 question/reason/可选 suggested_confirmation。

### scan-result.json 三态置信度（取代 0-1 浮点）

每条结论的 `confidence` 字段是枚举：

| 英文枚举（机器字段） | 中文标签（人类文档展示） | 含义 |
|---|---|---|
| `confirmed` | 已确认 | 源码/配置/依赖声明/项目文档中有直接证据 |
| `inferred` | 推断得出 | 由目录结构、命名、调用关系等间接证据合理推断 |
| `uncertain` | 不确定 | 证据不足、存在冲突或需运行才能确认 |

**铁律**：机器字段一律用英文枚举（`confirmed`/`inferred`/`uncertain`）；人类文档（01-项目概览.md）一律用中文标签。`uncertain` 的结论必须同时在 `questions[]` 里写明缺口，不得臆造补全。

### scan-summary.md（人类速览）

一段话（3-8 行）：项目是什么、主要类型、核心语言/框架、入口、关键命令。从 scan-result.json 提炼，不引入新结论。
```

**(3c) 改 "## 产出格式" 节**——
- `01-项目概览.md` 模板里的"置信度：{high/medium/low}（{具体数值，如 0.9}）"改为"**置信度**：{已确认/推断得出/不确定}（对应 scan-result.json 的 confirmed/inferred/uncertain）"。
- 删除整个 "### _meta/project-type.json 模板" 子节（含其 json 代码块），替换为一句："类型判定的结构化结果已迁入 `.codebase/scan-result.json` 的 `classifications` 字段，不再单独产 project-type.json。"

**(3d) 改 "## 置信度与依据要求" 节**——把"### 置信度等级"（high/medium/low + 0-1 范围表）整段替换为引用三态：

```markdown
### 置信度等级（三态）

见上文"扫描缓存（机器契约）"的三态表：`confirmed`（已确认）/ `inferred`（推断得出）/ `uncertain`（不确定）。机器字段用英文枚举，01 文档用中文标签。
```

把"### 低置信度处理"里的"整体置信度为 low（<0.5）"改为"存在 `uncertain` 结论时"，`requiresHumanReview: true` 改为"在该结论的 `questions[]` 写明缺口并标注待人工确认"。

**(3e) 改 "## 执行检查清单"**——更新末尾两步：

```markdown
8. [ ] 写入 `docs/project-knowledge/01-项目概览.md`（置信度用中文三态标签）
9. [ ] 写入 `.codebase/scan-result.json`（schema 校验通过）+ `.codebase/scan-summary.md`
10. [ ] 自检：scan-result.json required 字段齐全？每条结论带 evidence 且 path 真实？uncertain 项进 questions？不再产 project-type.json？
```

- [ ] **Step 4: GREEN 验证**

dispatch general-purpose subagent，读改后的 `~/.claude/skills/pm-scan/SKILL.md`，对 `dsp` 执行 pm-scan。验证：

```bash
test -f /Users/sunlc/my_workspace/dsp/.codebase/scan-result.json && echo "cache produced"
python3 -c "import json; d=json.load(open('/Users/sunlc/my_workspace/dsp/.codebase/scan-result.json')); assert d['schema_version']=='1.0'; assert all(c['confidence'] in ('confirmed','inferred','uncertain') for c in d['classifications']); print('schema-fields OK')"
test ! -f /Users/sunlc/my_workspace/dsp/docs/project-knowledge/_meta/project-type.json && echo "project-type.json retired"
```

Expected: 三行全输出（cache produced / schema-fields OK / project-type.json retired）。逐条核对压力场景的 6 条增量 GREEN 规则。

- [ ] **Step 5: 通用化自检 + 提交**

```bash
grep -rni "dsp" skills/pm-scan/SKILL.md   # 期望 0 命中
git add skills/pm-scan/SKILL.md docs/skill-design/pm-scan/pressure-scenario.md
git commit -m "feat(pm-scan): 产 scan-result.json 缓存契约（三态置信度），退役 project-type.json"
```

---

### Task 4: pm-techstack-generic 优先读 scan-result.json 缓存（P0-1 消费端验证）

**Files:**
- Modify: `skills/pm-techstack-generic/SKILL.md`
- Modify: `docs/skill-design/pm-techstack-generic/pressure-scenario.md`

- [ ] **Step 1: 读 pm-techstack-generic/SKILL.md 定位插入点**

读 `skills/pm-techstack-generic/SKILL.md`，找到其 "## 输入" 节（接受 01-项目概览.md 作为上下文的那段）。Step 0 插在 "## 输入" 之后、第一个分析步骤之前。

- [ ] **Step 2: 更新压力场景**

在 `docs/skill-design/pm-techstack-generic/pressure-scenario.md` 追加：

```markdown
## 增量 GREEN 规则（缓存复用，2026-06-14 加入）

pm-techstack-generic 现在 Step 0 必须先读 `.codebase/scan-result.json`：
- 存在 → 复用其 classifications/technologies 作为基础清单，只深挖（版本细节、自封装框架、用途细化），不重做顶层识别；02 文档注明"基础清单复用自 .codebase/scan-result.json"。
- 不存在 → 提示先跑 pm-scan，不自行重建契约。
```

- [ ] **Step 3: Baseline RED**

当前 pm-techstack-generic 直接读源码做技术栈识别，不读 .codebase/缓存。据 SKILL.md 现状断定（无 Step 0 读缓存逻辑）。

- [ ] **Step 4: 改 pm-techstack-generic/SKILL.md，加 Step 0**

在 "## 输入" 节之后插入：

```markdown
## Step 0：优先读扫描缓存（必做）

开始技术栈深挖前，先检查 `{PROJECT_ROOT}/.codebase/scan-result.json`：

- **存在**：直接复用其 `classifications` 与 `technologies` 字段作为基础清单。本 skill 只做**深挖补充**——版本细节、自封装框架识别、模块依赖关系、用途细化——**不重做顶层技术栈识别**。在产出的 02 文档顶部注明"基础技术栈清单复用自 `.codebase/scan-result.json`（pm-scan 生成）"。
- **不存在**：提示用户/编排器先跑 `pm-scan` 生成缓存；**不得自行重建一份 scan-result.json**（避免双份漂移）。若编排器坚持跳过，照常从零识别，并在 02 文档标注"未使用扫描缓存（.codebase/scan-result.json 缺失）"。

读缓存是小模型下的关键省 context 手段——避免把整份代码库再喂一遍。
```

- [ ] **Step 5: GREEN 验证**

dispatch subagent 对 dsp（此时 Task 3 已产 scan-result.json）执行 pm-techstack-generic。验证：subagent 在日志/产出里声明读了 `.codebase/scan-result.json`；02 文档顶部有"复用自 scan-result.json"标注；未重新扫描整棵树（对比无缓存时的文件读取量下降）。

- [ ] **Step 6: 通用化自检 + 提交**

```bash
grep -rni "dsp" skills/pm-techstack-generic/SKILL.md   # 期望 0 命中
git add skills/pm-techstack-generic/SKILL.md docs/skill-design/pm-techstack-generic/pressure-scenario.md
git commit -m "feat(pm-techstack-generic): Step 0 优先读 scan-result.json 缓存，避免重扫"
```

---

### Task 5: project-mastery 改读 scan-result.json + 引入 progress.json 断点续跑（P0-1 路由适配 + P0-4）

**Files:**
- Modify: `skills/project-mastery/SKILL.md`
- Modify: `docs/skill-design/project-mastery/pressure-scenario.md`

- [ ] **Step 1: 更新压力场景**

在 `docs/skill-design/project-mastery/pressure-scenario.md` 追加：

```markdown
## 增量 GREEN 规则（scan-result 路由 + progress.json 断点续跑，2026-06-14 加入）

1. 波次 2 路由依据改为读 `.codebase/scan-result.json` 的 `classifications`（取 is_primary=true 的 type），不再读已退役的 `project-type.json`。
2. 全流程维护 `_meta/progress.json`：每个 phase 跑完即更新其 status（done/skipped/failed）；重跑时先读它、跳过 done 的 phase。
3. 收尾 manifest.json 的 projectType/scannedAt 字段改为从 scan-result.json 读（project.name / generated_at / scanner.version）。
```

- [ ] **Step 2: Baseline RED**

当前 project-mastery 波次 2 读 `_meta/project-type.json`（已退役，会找不到文件）；无 progress.json 维护逻辑。据 SKILL.md 现状断定。

- [ ] **Step 3: 改 project-mastery/SKILL.md**

四处修改：

**(5a) 改 "## 产出" 节**——在现有产出列表里：
- 删除 `_meta/project-type.json`（波次 1 产）那条，改为 `.codebase/scan-result.json` + `.codebase/scan-summary.md`（波次 1 产）。
- 新增一条：`{PROJECT_ROOT}/docs/project-knowledge/_meta/progress.json`（全流程维护，断点续跑）。

**(5b) 改波次 2 开始前的动作**——把"读 `_meta/project-type.json`，确认 types/primaryType"改为：

```markdown
1. 读 `{PROJECT_ROOT}/.codebase/scan-result.json`，从 `classifications` 取 `is_primary=true` 的 type 作为路由依据（取代旧 project-type.json 的 primaryType）。若多个 is_primary 或缺失，取 confidence=confirmed 且最核心的。
2. 读 `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md`，确认上下文可用。
3. （可选）按 primary type 决定波次 2 是否用特化 skill——期 1 统一用 `pm-techstack-generic`；期 2 实现特化后再按 primary type 路由。
```

**(5c) 新增 "## 断点续跑：_meta/progress.json（全流程维护）" 节**——插在 "### 【学习】子流程完成标志" 之后、"## dispatch 策略" 之前：

```markdown
## 断点续跑：_meta/progress.json（全流程维护）

pm 学习流程在 `{PROJECT_ROOT}/docs/project-knowledge/_meta/progress.json` 维护在飞行态，支持中断后续跑（小模型长程规划弱、易丢状态，这是"能跑完"的工程兜底）。**与 manifest.json 区分**：progress=在飞行态（每步更新），manifest=完成态记录（收尾一次性写）。

模板：

```json
{
  "projectName": "{从 scan-result.json 的 project.name 读}",
  "projectRoot": "{绝对路径}",
  "generatedAt": "{首次生成时 ISO-8601，重跑不覆盖}",
  "skillVersion": "project-mastery v1",
  "sourceCommit": "{git -C {PROJECT_ROOT} rev-parse --short HEAD 或 未记录}",
  "phases": [
    { "name": "scan",       "skill": "pm-scan",             "status": "done", "output": [".codebase/scan-result.json", "01-项目概览.md"] },
    { "name": "techstack",  "skill": "pm-techstack-generic", "status": "pending" },
    { "name": "conventions","skill": "pm-conventions",       "status": "pending" },
    { "name": "api-index",  "skill": "pm-api-index",         "status": "pending" },
    { "name": "build-deploy","skill": "pm-build-deploy",     "status": "pending" },
    { "name": "kb-index",   "skill": "pm-kb-index",          "status": "pending" },
    { "name": "verify",     "skill": "pm-verify",            "status": "pending" }
  ]
}
```

### 维护规则

1. 入口判定走【学习】后，立即写 progress.json（所有 phase 初始 pending，scan 即将开始）。
2. 每个 phase 的 subagent 返回后，立即把该 phase status 改为 `done`（成功）/`skipped`（跳过）/`failed`（失败），并填 output。
3. **重跑**：开工先读 progress.json；status=done 的 phase 跳过（除非用户指定强制重跑某 phase）；从第一个非 done 的 phase 续跑。
4. `generatedAt` 只在首次生成（progress.json 不存在）时写入；重跑不覆盖（禁止编造时间）。
5. `sourceCommit` 用 `git -C {PROJECT_ROOT} rev-parse --short HEAD`；无 git 标"未记录（无 git 仓库）"。
```

**(5d) 改收尾 manifest.json 模板 + 步骤**——
- 收尾步骤 3"读 project-type.json 的 projectName/types/primaryType/scannedAt/scanVersion"改为"读 `.codebase/scan-result.json` 的 project.name / classifications（取 is_primary）/ generated_at / scanner.version"。
- manifest 模板里 `projectType` 字段改为：

```json
"projectType": {
  "primaryType": "{scan-result.json classifications 里 is_primary=true 的 type}",
  "allTypes": "{scan-result.json classifications 的 type 列表}",
  "confidence": "{scan-result.json project.confidence}",
  "source": ".codebase/scan-result.json"
},
"scannedAt": "{scan-result.json generated_at}",
```

- manifest 的 `skillVersions.pm-scan` 改为"{scan-result.json scanner.version 读}"（应为 v2）。

**(5e) 改 "## 执行检查清单"**——在"波次 1"前加一步"写 progress.json（初始全 pending）"；每个波次确认后加"更新 progress.json 该 phase 为 done"；末尾自检加"progress.json 是否全程维护？重跑能跳过 done 的 phase？"

- [ ] **Step 4: GREEN 验证（端到端片段）**

在 dsp 上跑 project-mastery【学习】子流程（至少跑到波次 2）。验证：

```bash
test -f /Users/sunlc/my_workspace/dsp/docs/project-knowledge/_meta/progress.json && echo "progress.json exists"
python3 -c "import json; d=json.load(open('/Users/sunlc/my_workspace/dsp/docs/project-knowledge/_meta/progress.json')); assert any(p['status']=='done' for p in d['phases']); print('phases tracked')"
```

并人为模拟"中断后续跑"：把 scan phase 标 done、其余 pending，重跑确认编排器跳过 scan 直接从 techstack 续。

- [ ] **Step 5: 通用化自检 + 提交**

```bash
grep -rni "dsp" skills/project-mastery/SKILL.md   # 期望 0 命中
git add skills/project-mastery/SKILL.md docs/skill-design/project-mastery/pressure-scenario.md
git commit -m "feat(project-mastery): 路由读 scan-result.json + 引入 progress.json 断点续跑"
```

---

### Task 6: 端到端验收 + 通用化自检 + 验收记录

**Files:**
- Create: `docs/superpowers/plans/2026-06-14-p0-scan-cache-foundation-验收.md`

- [ ] **Step 1: 全局通用化自检**

```bash
cd /Users/sunlc/sunlc_work/sunlc_skills
grep -rni "dsp" skills/*/SKILL.md   # 期望 0 命中（skill 源码零项目特定）
```

- [ ] **Step 2: 端到端验收（dsp 上 pm 全流程）**

在 dsp 上跑 project-mastery【学习】子流程全流程，确认产出齐备：

- `.codebase/scan-result.json`（schema 校验通过、三态置信度）
- `.codebase/scan-summary.md`
- `docs/project-knowledge/_meta/progress.json`（phases 全 done）
- `docs/project-knowledge/_meta/manifest.json`（projectType.source 指向 scan-result.json）
- `docs/project-knowledge/01-06 + README`
- **无** `_meta/project-type.json`（已退役）

- [ ] **Step 3: 写验收记录**

创建 `docs/superpowers/plans/2026-06-14-p0-scan-cache-foundation-验收.md`，记录：
- 6 个任务的 RED/GREEN 结果
- scan-result.json schema 校验通过证据
- progress.json 断点续跑验证证据
- project-type.json 退役确认
- 通用化自检 0 命中
- 延后项（P0-2 瘦身、P0-3 预算、P0-5 verify-lite）

- [ ] **Step 4: 提交 + 收尾**

```bash
git add docs/superpowers/plans/2026-06-14-p0-scan-cache-foundation-验收.md
git commit -m "docs(验收): P0 地基（扫描缓存契约 + 断点续跑）端到端 GREEN"
```

用 superpowers:finishing-a-development-branch 收尾（验证、呈现选项、合入 main）。

---

## 自检（写计划后 fresh-eyes review）

**1. Spec 覆盖**：
- P2-1（link-skills 硬编码）→ Task 1 ✓
- P0-1 扫描缓存契约（schema + 生产 + 消费）→ Task 2/3/4 ✓
- P0-4 progress.json 断点续跑 → Task 5 ✓
- P1-3 三态置信度（machine 英文枚举 + 文档中文）→ Task 2（schema）+ Task 3（pm-scan）✓
- 明确不在本期：P0-2 瘦身、P0-3 全预算、P0-5 verify-lite、P1 其余、P2 其余 → 范围说明已声明 ✓

**2. Placeholder 扫描**：schema 完整 JSON ✓；pm-scan/project-mastery 的 4 处修改均给了完整新文本 ✓；link-skills 给了确切替换行 ✓。无 TBD/TODO。

**3. 一致性**：
- `scanner.version` = "v2"（pm-scan 引入缓存后的版本）在 Task 3(3b) 与 Task 5(5d) 一致 ✓
- `classifications[].is_primary` 取代 `primaryType`，在 schema(Task2) / pm-scan(3b) / project-mastery(5b,5d) 三处用法一致 ✓
- progress.json 与 manifest.json 职责区分在关键决策#3、Task5(5c)、验收(Task6) 一致 ✓
- 三态枚举英文 + 中文标签映射在 schema(Task2) / pm-scan(3b,3c) / 压力场景 一致 ✓
