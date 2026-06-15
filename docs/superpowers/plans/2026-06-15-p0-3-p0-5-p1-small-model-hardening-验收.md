# P0-3 + P0-5 + P1 验收记录：小模型硬化

> 对应计划：`docs/superpowers/plans/2026-06-15-p0-3-p0-5-p1-small-model-hardening.md`
> 范围：claude优化清单 的 **P0-3**（输入输出预算纪律）+ **P0-5**（pm-verify-lite）+ **P1-1/2/6/7**（双区/validate/任务包/失败恢复）+ **P1-3**（三态硬化）
> 验收日期：2026-06-15
> 方式：内联执行 + dsp 实测（脚本真跑、结构校验、通用化 grep）

## 1. P0-3：输入输出预算纪律（8 叶 skill）

pm-scan 已有预算纪律；推广到其余 8 叶 skill，各加紧凑"输入输出预算（小模型纪律）"section（~7 行），插在"产出格式"与"执行检查清单"之间。四要素：**单步单产物 + 读预算（禁扫清单/限深/文件上限）+ 写预算（字数/top N+待生成）+ 证据先行**。

| skill | 预算后行数 | 单产物 |
|---|---|---|
| pm-techstack-generic | 156 | 02 |
| pm-conventions | 75 | 03 |
| pm-api-index | 87 | 04 |
| pm-build-deploy | 124 | 05 |
| pm-kb-index | 147 | README |
| lp-feature-scan | 141 | inventory.md |
| lp-prompt-gen | 108 | 每功能 prompt |
| lp-index | 124 | README |

**设计取舍**：预算纪律内联（非跨文件），因叶 skill 的 subagent 只读自己那份 SKILL.md，红线必须在眼前。常见骨架适度重复是 progressive-discipline 的取舍，DRY 在此会损可靠性。

## 2. P0-5：pm-verify-lite（默认）+ pm-verify（opt-in）

新建 `skills/pm-verify-lite/`（SKILL.md 105 行 + templates/06-校验报告.md + references/verify-lite-rules.md）：
- 每文档抽样 3-5 条（封顶）、三分类（一致/不一致/无法核对）、单次输出 ≤5000 字、只报告不修改。
- 风险信号（低/中/高）+ 升级触发条件（不一致≥3 / 关键文档 01/02/04 出问题 / 人工指定 / 关键项目）。
- **不做** full 的跨文档一致性/未发现独立复核/逐文档置信度——这些是 full 职责。

编排器路由：project-mastery 波次 4 默认 dispatch pm-verify-lite；wave-dispatch.md 加"波次4（默认）lite"+"波次4（opt-in）full"两模板；dispatch策略表/检查清单/产出清单同步。

## 3. P1-2：validate-kb.py（CI 校验脚本）

`scripts/validate-kb.py {PROJECT_ROOT} [--json]`，stdlib 无依赖，6 类检查：
1. scan-result.json 契约（存在/合法 JSON/required 字段/classifications 恰好 1 条 is_primary/每条带 evidence）
2. KB 文档（01-05/README）无未替换模板 token（排除 06 元报告 + 不查裸 TODO/XXX 防误报）
3. README 无死链
4. 必填章节抽检（WARN）
5. ~~通用化~~（移除：项目名在生成 KB 里合法；skill 源码通用化由 CI 单独 grep）
6. confidence 全部 ∈ 三态枚举（递归收集）

**dsp 实测**：PASS 8 / WARN 0 / FAIL 0，exit 0。text + JSON 双模式。
**误报修正**：初版查裸 TODO/XXX/泄露词 dsp 误报（ErrorCode.XXX 是代码示例、TODO.md 是真实文件、dsp 是项目本名）——收窄为只查模板 token、移除泄露词检查（改由 grep skills/ 校验源码）。

## 4. P1-1：AI/HUMAN 双区 + update_ai_generated_block.py

`scripts/update_ai_generated_block.py`（stdlib 无依赖），三模式：
- `--init`：按标题切 section 注入 AI-GENERATED + HUMAN-NOTES 骨架
- `--list`：列已标记 section + AI/HUMAN 有无
- `--section ID --ai-file F [--dry-run]`：替换 AI 块、HUMAN 块物理保留

**实测**：init→list→人工补 HUMAN→update 替换 AI，HUMAN-NOTES 原样保留 ✓，dry-run 出 diff ✓。

`references/dual-zone-convention.md`：标记语法 + 三模式用法 + 与【更新】子流程衔接（期2 实现时只喂 AI 区+证据、调脚本替换）。project-mastery【更新】stub 指向它。

## 5. P1-7：失败恢复运行时策略

`references/failure-recovery.md`：单步失败**不重跑全流程**——降级产出（标 uncertain/待补）+ 写 reason/partialOutput/retryable + 续跑下一独立 phase + 收尾记 knownGaps。phase 状态机扩展（pending/in-progress/done/skipped/failed），failed 带 reason+partialOutput+retryable。各 skill 失败兜底汇总表。

progress.json 模板：phase.status 五态语义 + failed 示例（_failedPhaseExample）；verify 默认 pm-verify-lite。manifest 模板：加 knownGaps 字段。project-mastery 维护规则加"失败恢复"条。

## 6. P1-6：任务输入包形式化

`references/task-input-package.md`：五组件（task.md/relevant-files.txt/scan-result.json/previous-output.md/output-template.md）+ 编排器 dispatch 前核对职责。wave-dispatch.md 顶部加引用，说明各波次模板即任务输入包实例。

## 7. P1-3：三态置信度硬化

- **机器契约层**（scan-result.json）：schema `$defs.confidence` enum [confirmed,inferred,uncertain] ✓；validate-kb.py 递归收集所有 confidence 字段强制 ∈ 枚举（dsp 47 条全 PASS）✓。
- **人类文档层**：机器字段英文枚举、人类文档中文标签（已确认/推断得出/不确定）。01（项目类型）、03（规范置信度）用中文三态；02/04/05 各保留领域适用标注（05 的 已验证/推断/未发现、04 的 文件:行 事实）——不强行统一，避免过度工程与各 doc 标注体系冲突。
- pm-scan SKILL.md 铁律条款记录双语规则。

## 8. 整体验证

- **行数**：12 skill 共 1736 行（P0-2 后 1569 + P0-3 预算段 + pm-verify-lite 105 + 路由调整）；11/12 ≤156，project-mastery 288（编排器，含入口判定/波次/dispatch/失败恢复/stub）。
- **通用化**：`grep -rni dsp skills/`（含新 pm-verify-lite + 3 references + 2 脚本）= **0 active 命中**。
- **脚本可跑**：validate-kb.py dsp PASS；update_ai_generated_block.py 三模式实测通过。
- **symlink 可见**：`bash scripts/link-skills.sh` 后 pm-verify-lite（含 templates/references）可见。
- **JSON 合法**：progress.json / manifest.json 模板 `json.load` 通过。

## 9. commit 清单（分支 p0-3-p0-5-p1-hardening）

1. docs(plan): P0-3+P0-5+P1 计划
2. feat(skills): P0-3 全叶 skill 输入输出预算纪律
3. feat(pm-verify-lite): P0-5 默认轻量校验 skill + 编排器路由
4. feat(scripts): P1-2 validate-kb.py
5. feat(scripts,refs): P1-1 AI/HUMAN 双区
6. feat(refs): P1-7 失败恢复策略
7. feat(refs): P1-6 任务输入包形式化

## 10. 延后 / 注意

- **脚本单元测试**：本期用 dsp 实测 + 临时文件实测，未建 pytest 套件；CI 接入时可补（validate 的 negative case：故意造个坏 scan-result.json 验 FAIL 路径）。
- **【更新】/【开发】子流程**：仍 stub（期2/3）；P1-1 双区脚本 + P1-7 失败恢复已为期2【更新】铺好基础设施。
- **任务输入包磁盘化**（task-input-package.md 边界提的）：期1 用 prompt 内嵌（wave-dispatch.md 形态）已足够；期2/4 可演进为 `_meta/tasks/<phase>/` 真实文件。
- **P0-3 预算数字**（≤15 文件/≤500 行/8000-12000 字等）是经验默认值，跑真实项目后可据实调。
- **行为未端到端重跑**：本期是 skill 源码增量（预算段/新 skill/脚本/约定文档），未重跑 project-mastery 全流程；结构校验 + dsp 脚本实测已过。下次跑全流程时验证 pm-verify-lite 默认路由 + 预算纪律 + 失败恢复的端到端表现。
