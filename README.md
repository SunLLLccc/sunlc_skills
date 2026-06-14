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

## Skill 清单（12 个）

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
| `pm-verify` | 知识库抽样校验（只读、只报告）（波次4） | agent |

**学习管线**：4 波次 — `pm-scan`（定位/类型）→ 并行 4 分析（techstack / conventions / api / build-deploy）→ `pm-kb-index`（索引）→ `pm-verify`（校验）→ manifest 收尾。

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

```bash
# 把每个 skills/<name> 软链到 ~/.claude/skills/<name>，使其全局可发现
bash scripts/link-skills.sh
```

链接后，在任意项目里按需触发对应 skill（其 `description` 决定何时被自动选中）：

- 接手开发 → `/project-mastery`
- 生成学习文档 → `/learn-project`

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
├── skills/                     12 个通用 skill（SKILL.md + YAML frontmatter）
│   ├── project-mastery/        └ pm-* × 7（接手开发）
│   └── learn-project/          └ lp-* × 3（学习理解）
├── scripts/
│   └── link-skills.sh          软链 skills/ → ~/.claude/skills/
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
