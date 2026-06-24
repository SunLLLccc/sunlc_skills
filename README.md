# sunlc_skills — 通用 Claude Code Skills 工具集

一套**通用的、可复用的** Claude Code skills 工具集，面向"已有项目"的两类核心场景：**接手开发**与**学习理解**。所有 skill 源码 100% 通用（零项目特定内容），适用于任意技术栈的任意已有项目。

> skills = 方法论（单一事实来源）；执行由主会话或分发的 subagent 承担。

---

## 两套互补的工具集

| | **project-mastery**（接手开发） | **learn-project**（学习理解） |
|---|---|---|
| 面向场景 | 接手一个项目要**写代码**：吃透规范/API/构建/部署，建立项目内知识库 | 想要**读懂**一个项目：理解设计思想/核心概念/关键功能如何工作 |
| 受众 | 要在本项目里写代码、改代码的人 | 想搞懂本项目设计的开发者（有经验但不熟此项目） |
| 产出视角 | 工程事实（规范/API/构建/部署/校验） | 教学理解（设计/概念/功能走读） |
| 产出目录 | `{PROJECT_ROOT}/docs/project-knowledge/` | `{PROJECT_ROOT}/docs/learning-docs/` |
| 复用关系 | 自成体系 | **复用 project-mastery 的扫描底座**（pm-scan / pm-techstack-generic） |

两者产出目录并列、互不覆盖。

---

## Skill 清单（13 个）

### project-mastery（接手开发）— `pm-*`

| Skill | 职责 | 执行者 |
|---|---|---|
| `project-mastery` | 顶层编排：判定 学习/更新/开发 子流程并分发 | 主会话 |
| `pm-scan` | 项目扫描 + 多维度类型识别（路由器/波次1） | agent |
| `pm-techstack-generic` | 技术栈与架构识别（含自封装框架）（波次2） | agent |
| `pm-conventions` | 从代码实际推断开发规范（波次2） | agent |
| `pm-api-index` | API 索引（波次2） | agent |
| `pm-build-deploy` | 构建/打包/部署文档（波次2） | agent |
| `pm-kb-index` | 知识库总索引 + 任务型阅读路径（波次3） | 主会话 |
| `pm-verify-lite` | 轻量抽样校验（**默认**，每文档 3-5 条断言、输出短、只报告）（波次4） | agent |
| `pm-verify` | 全量抽样校验（**opt-in**，风险信号/人工指定/关键项目时升级）（波次4） | agent |

**学习管线**：4 波次 — `pm-scan`（定位/类型）→ 并行 4 分析（techstack / conventions / api / build-deploy）→ `pm-kb-index`（索引）→ `pm-verify-lite`（校验，默认；全量改 opt-in `pm-verify`）→ manifest 收尾。

### learn-project（学习理解）— `lp-*`

| Skill | 职责 | 执行者 |
|---|---|---|
| `learn-project` | 顶层编排：定位 → 功能扫描 → 人在回路挑选 → 逐功能生成提示词+文档 → 学习路径索引 | 主会话 |
| `lp-feature-scan` | 5 层扫描识别可学习功能，产出功能清单（核心度/复杂度/依赖/证据） | agent |
| `lp-prompt-gen` | 对选中功能生成教学提示词（必读证据/学习目标/6 节结构/受众/撰写要求），存为可复用文件 | agent |
| `lp-index` | 学习路径索引 README（5 铁律：速览/何时读/按依赖排序的路径/元信息/区分已未生成） | 主会话 |

**学习管线**：4 步 — 第 0 步复用 `pm-scan`+`pm-techstack-generic` 定位 → `lp-feature-scan`（功能清单）→ 人在回路挑选 → `lp-prompt-gen`（提示词）+ dispatch subagent 生成文档 → `lp-index`（学习路径）。
**doc 生成不单独成 skill**：orchestrator 用保存的提示词 dispatch 通用 subagent（提示词承载教学方法论，subagent 只执行）。

---

## 安装与使用

### 1. 环境要求

- **Claude Code**（CLI / 桌面 / IDE 插件均可）—— 承载 skill 发现与执行
- **Codex**（可选）—— 同样原生认 SKILL.md 格式，本工具集可同一份源码两边复用
- **bash** —— `link-skills.sh`
- **Python 3.6+**（可选）—— 仅 `scripts/validate-kb.py` 与 `update_ai_generated_block.py` 需要，纯 stdlib、无第三方依赖

### 2. 安装（软链到全局）

```bash
git clone <repo> ~/sunlc_skills
bash ~/sunlc_skills/scripts/link-skills.sh          # Claude Code（默认，~/.claude/skills）
bash ~/sunlc_skills/scripts/link-skills.sh codex    # Codex（~/.codex/skills）
bash ~/sunlc_skills/scripts/link-skills.sh all      # 两者都链
```

脚本把每个 `skills/<name>` 软链到目标 agent 的 skills 目录，使其全局可发现。**同一份 skill 源码（SKILL.md + YAML frontmatter）在 Claude Code 与 Codex 两边格式通用**——Codex 的 skill 目录就是 `~/.codex/skills/<name>/`，结构与 Claude Code 对称，一次开发、两边复用，无需维护两套。脚本用 `$(dirname "${BASH_SOURCE[0]}")/..` 相对定位源目录，**在任意目录调用均可**；也支持 `DEST_DIR=/custom/path bash scripts/link-skills.sh codex` 覆盖默认目录，或 `bash scripts/link-skills.sh /custom/dir` 直接装到任意路径。

校验链接是否生效：

```bash
ls -l ~/.claude/skills/ | grep -E 'pm-scan|learn-project'   # Claude Code
ls -l ~/.codex/skills/  | grep -E 'pm-scan|learn-project'   # Codex
# 应指向 .../sunlc_skills/skills/ 下对应目录
```

> skill 源码更新后**无需重新链接**（软链跟随源码）；新增 skill 目录后重跑对应命令即可补链。

> **Codex 并行 dispatch（可选）**：`project-mastery` 波次 2 会并行 dispatch 子 skill（subagent）。Codex 下需在 `~/.codex/config.toml` 开启 `[features] multi_agent = true` 才能用 `spawn_agent` 并行；不开也能跑，只是顺序执行（功能不受影响）。skill 内用的是 Claude Code 的 `Agent` 工具名，Codex 会按其工具映射（`Agent` → `spawn_agent`）执行。

### 3. 在目标项目里触发

进入**目标项目根目录**启动 Claude Code（或 Codex），两种等价方式：

- **自然语言**（推荐）—— skill 的 `description` 字段决定何时自动选中：
  - 「接手这个项目，帮我建立项目知识库」→ 自动选中 `project-mastery`
  - 「我想读懂这个项目，生成学习文档」→ 自动选中 `learn-project`
  - 也可直接给出项目根：「学习 `/abs/path/to/project`」
- **显式 slash**：`/project-mastery`、`/learn-project`（直接点名叫起；Codex 无 `/skill` slash，用自然语言即可）

### 4. 典型流程

#### A. 接手开发 → `project-mastery`

主会话先做**入口判定**（探测目标项目的知识库状态：有需求文档→开发、无 KB/无 manifest→学习、KB 在且代码变了→更新），命中【学习】后按 4 波次跑：

```
波次1  pm-scan            → 01-项目概览  +  .codebase/scan-result.json（扫描缓存/类型识别）
波次2  并行四分析          → 02-技术栈 / 03-规范 / 04-API索引 / 05-构建部署
波次3  pm-kb-index        → README（知识库总索引 + 任务型阅读路径）
波次4  pm-verify-lite     → 06-校验报告（默认轻量抽样；要全量改 opt-in 的 pm-verify）
收尾   主会话             → _meta/manifest.json（记录源码版本，供【更新】diff 判定）
```

- 产出落 `{PROJECT_ROOT}/docs/project-knowledge/`
- 中途可中断，`_meta/progress.json` 支持**断点续跑**
- 产出每条结论附真实证据，零臆造；可信度三态（已确认 / 推断 / 不确定）

#### B. 学习理解 → `learn-project`

主会话串一条管线，第 0 步**复用 project-mastery 的扫描底座**（已有 project-knowledge/ 就直接读、不重扫）：

```
第0步  复用 pm-scan + pm-techstack-generic 定位（已有则复用）
第1步  lp-feature-scan     → 01-功能清单（可勾选，带核心度/复杂度/依赖/证据）
第2步  人在回路挑功能 ← 你在这里勾选要深入的功能（≤4 个可 AskUserQuestion，更多直接改清单）
第3步  逐功能：lp-prompt-gen 出教学提示词 → dispatch subagent 按提示词出学习文档
第4步  lp-index           → README（学习路径索引）
```

- 产出落 `{PROJECT_ROOT}/docs/learning-docs/`，与 A 的目录并列、互不覆盖
- 只对**选中**的功能生成；文档由保存的提示词驱动，提示词可改后定点重跑

### 5. 产出文件命名

统一 `类型号-序号-文件名.md`（全中文，除命令/代码）。例：

- **project-mastery**：`01-001-项目概览.md` … `06-001-校验报告.md`（各类型当前单文件，序号 001；同类拆分时 002/003 递增）
- **learn-project**：`features/01-001-功能清单.md`、`docs/02-001-<功能>.md`、`features/prompts/03-001-<功能>.md`（序号=选中顺序，prompt↔doc 同序号配对）

`README.md`、`_meta/*.json`、`.codebase/*` 不套此规则（分别是索引前门 / 元信息 / 机器契约）。

### 6. 配套脚本（可选）

```bash
# 校验知识库质量（CI 可跑，查 scan-result.json 契约 / 三态枚举 / 占位符 / 死链 / 必填章节）
python3 scripts/validate-kb.py {PROJECT_ROOT}        # 人类可读报告
python3 scripts/validate-kb.py {PROJECT_ROOT} --json # 机读 JSON

# AI/HUMAN 双区增量更新（供【更新】子流程；也可手动用于任意 KB 文档）
python3 scripts/update_ai_generated_block.py {KB文档}.md --init                # 按 ## 标题注入双区骨架
python3 scripts/update_ai_generated_block.py {KB文档}.md --list                 # 列出 section 及其 AI/HUMAN 区状态
python3 scripts/update_ai_generated_block.py {KB文档}.md --section <id> --ai-file <新内容> --dry-run  # 试替换 AI 区（HUMAN 区物理保留）
```

### 7. 何时用哪套

- 要在本项目里**写 / 改代码** → `project-mastery`（产出规范/API/构建/部署，工程事实）
- 要**读懂**本项目设计 → `learn-project`（产出设计/概念/功能走读，教学理解）
- 两者可先后用、产出目录独立；先 `learn-project` 读懂再用 `project-mastery` 建库也常见

---

## 设计原则

1. **skill 源码 100% 通用**：SKILL.md 零项目特定内容（路径/模块名/类名/专有端口一律占位符 `{...}`）。通用技术名词（Spring/Vue/Maven 等）作为跨项目识别指引允许。写完每个 skill 自检 `grep -rni "<项目名>" skills/*/SKILL.md`，须 0 命中。
2. **skill = 方法论，agent = 执行**：skill 是单一事实来源；重活由主会话或分发的 subagent 承载，主会话负责编排与人在回路。
3. **TDD 构建**：每个 skill 用压力场景（失败模式 → 验证方式 → GREEN 规则）驱动，baseline RED → 写 skill → GREEN 验证。
4. **证据驱动，零臆造**：产出里每条结论附真实证据（文件路径 + 说明），低置信度显式标注，禁止编造。

---

## 仓库结构

```
sunlc_skills/
├── skills/                     13 个通用 skill（SKILL.md + YAML frontmatter）
│   ├── project-mastery/        └ pm-* × 8（接手开发，含 pm-verify-lite）
│   └── learn-project/          └ lp-* × 3（学习理解）
├── scripts/
│   ├── link-skills.sh          软链到 ~/.claude/skills/ 或 ~/.codex/skills/（参数 claude/codex/all）
│   ├── validate-kb.py          知识库机器校验（CI 可跑，stdlib 无依赖）
│   └── update_ai_generated_block.py   AI/HUMAN 双区增量更新
├── schemas/
│   └── codebase-scan-result.schema.json   scan-result.json 机器契约（三态枚举等）
├── docs/
│   ├── skill-design/           TDD 压力场景（<skill>/pressure-scenario.md）+ README（通用化纪律）
│   └── superpowers/
│       ├── specs/              设计稿（spec）
│       └── plans/              实现计划 + 验收记录
└── .gitignore                  排除测试靶子 / 依赖 / 构建产物 / .claude 运行时
```

**测试靶子**：一个 gitignored 的目标项目（**不属于工具集源码**），仅用于 TDD GREEN 验证，其内容只出现在该项目的分析产出与 `docs/skill-design/` 压力场景里，永不进 skill 源码。

---

## 设计文档

| 文档 | 内容 |
|---|---|
| `docs/superpowers/specs/2026-06-14-project-mastery-design.md` | 子项目 A（project-mastery）设计 |
| `docs/superpowers/specs/2026-06-14-learn-project-design.md` | 子项目 B（learn-project）设计 |
| `docs/superpowers/plans/` | 各期实现计划与验收记录 |
| `docs/skill-design/README.md` | 通用化纪律说明 |

---

## 进度

- ✅ **project-mastery 期1**：学习管线核心（pm-scan + pm-techstack-generic + pm-conventions + pm-api-index + pm-build-deploy + pm-kb-index + pm-verify + project-mastery 编排）已完成、通过整体最终审查。
- ✅ **learn-project**：4 个 skill 全部完成，测试靶子上端到端 GREEN。
- ⏳ **project-mastery 期2-4（规划中）**：期2 路由器特化（pm-techstack-{frontend/backend/fullstack}）+ pm-update 增量更新；期3 pm-dev 开发编排；期4 预定义 agents。
- ⏳ **learn-project 延后**：lp-verify 文档质量校验、多受众变体。
