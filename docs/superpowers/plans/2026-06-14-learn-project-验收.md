# learn-project（子项目 B）验收记录

> 日期：2026-06-14
> 分支：`phase-b1-learn-project`
> spec：`docs/superpowers/specs/2026-06-14-learn-project-design.md`
> plan：`docs/superpowers/plans/2026-06-14-learn-project.md`
> 测试靶子：`dsp`（gitignored，仅验证）

## 交付物：4 个通用 skill（均 100% 通用，零项目特定）

| Skill | 职责 | 执行者 | TDD GREEN 结果 |
|---|---|---|---|
| `lp-feature-scan` | 功能识别（5 层扫描），产出 inventory.md | agent | dsp 上识别 16 个项目特定功能，四字段齐全，63 条证据路径全部真实，按核心度排序，带勾选框，零臆造 |
| `lp-prompt-gen` | 教学提示词生成（五要素） | agent | 2 个选中功能各产出提示词，五要素齐全（必读证据/学习目标/6 节结构/受众/撰写要求），9 条证据路径真实、精确到方法/行号 |
| `lp-index` | 学习路径索引 README（5 铁律） | 主会话 | 5 铁律全满足，学习路径按依赖正确排序（01→02），元信息来自 progress.json 非编造，0 死链 |
| `learn-project` | 顶层编排（定位→扫描→挑选→生成→索引） | 主会话 | 全流程产出 5 类齐备，第 0 步复用 A 的 01/02（未重扫），0 死链 |

复用（不修改）：`pm-scan`、`pm-techstack-generic`（第 0 步定位）。
doc 生成不成 skill：orchestrator 用 lp-prompt-gen 保存的提示词 dispatch 通用 subagent（提示词承载方法论）。

## 端到端验收（dsp）

第 0 步探测到 `dsp/docs/project-knowledge/01、02` 已存在（A 期1 已生成）→ **复用，未重跑 pm-scan/pm-techstack**（验证复用路径成立）。

选中功能 #1（XML DSL 引擎，无依赖）+ #2（DAG 编排，依赖 #1）→ 2 节点构成带依赖的学习路径。

产出树（`dsp/docs/learning-docs/`，5 类齐备）：
```
README.md                       ← 学习路径索引（01→02 依赖排序）
_meta/progress.json             ← 16 功能/2 选中/2 完成，generatedAt 真实
features/inventory.md           ← 16 功能清单（#1#2 标 [x]）
features/prompts/01-xml-dsl-engine.md
features/prompts/02-dag-orchestration.md
docs/01-xml-dsl-engine.md       ← 约 4500 字，6 节，6/6 学习目标覆盖
docs/02-dag-orchestration.md    ← 约 4500 字，6 节，7/7 学习目标覆盖
```

死链检查：README 内 7 个相对链接（含跨链到 `../project-knowledge/01、02`）全部 OK。

文档质量抽检：两份 doc 引用代码均精确到文件:行号，零臆造；2 个如实标注的"待补"点（InlineDataSourceRegistrar 实现细节、exportMode 分支语义），按 lp-prompt-gen 边界处理纪律处理。

## 通用化自检

`grep -rni "dsp" skills/{learn-project,lp-feature-scan,lp-prompt-gen,lp-index}/SKILL.md` → **0 命中**。dsp 内容仅出现在 `dsp/docs/learning-docs/`（产出）与 `docs/skill-design/lp-*/pressure-scenario.md`（TDD 笔记），符合 [[skills-must-be-generic]] 纪律。

软链：4 个新 skill 已通过 `scripts/link-skills.sh` 软链到 `~/.claude/skills/`，全局可发现。

## 延后 / 不做（spec §13）

- **doc-gen 独立 skill 化**：当前提示词驱动通用 subagent 足够；若需多稿迭代/交叉验证再独立。
- **lp-verify（文档质量校验 skill）**：参照 A 的 pm-verify 思路按需补充（如抽样核对 doc 引用的代码路径真实存在）。
- **多受众变体**：受众固定"有经验但不熟本项目的开发者"；其它受众按需延后。

## 已知 trade-off

- **e2e 选中 2 功能**：完整管线以 2 个功能验证（含 1 条依赖链），足以证明 prompt→doc→index→progress 全链路；功能数线性可扩展，未做 16 全量生成（无必要且耗时）。
- **doc-gen 质量依赖提示词**：提示词五要素约束了 doc 结构与证据，但 doc 最终质量仍取决于执行 subagent 的代码阅读深度；本次抽检良好，未引入自动质量校验（延后 lp-verify）。
