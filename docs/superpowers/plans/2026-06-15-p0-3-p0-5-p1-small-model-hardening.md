# P0-3 + P0-5 + P1 实施计划：小模型硬化（预算纪律 + 轻量校验 + 工程化护栏）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 P0-1（扫描缓存契约）+ P0-2（瘦身分层）基础上，落地小模型可用性的最后三道命门与工程化护栏：①全 skill 输入输出预算硬纪律（P0-3）；②pm-verify-lite 默认轻量校验、完整版降 opt-in（P0-5）；③AI/HUMAN 双区增量保护、确定性 validate 脚本、任务输入包、失败恢复运行时策略（P1-1/2/6/7），并把可信度三态硬化到全链路（P1-3）。

**Architecture:** 面向内网 qwen3.6 35b（200k 输入 / 64k 输出）。三条主线：
- **预算纪律**：每个叶 skill 内联紧凑的"输入输出预算"section（单步单产物 + 读预算 + 写预算 + 证据先行），让 dispatch 的 subagent 在它唯一读取的那份 SKILL.md 里直接看到红线（自包含，不靠跨文件）。
- **轻量校验**：新增 `pm-verify-lite` skill（默认波次 4），抽样 3-5 条/文档、单次输出短；完整 `pm-verify` 降为 opt-in。编排器波次 4 默认路由 lite。
- **工程化护栏**：`scripts/validate-kb.py`（CI 可跑的机器校验）、`scripts/update_ai_generated_block.py`（双区增量更新，--dry-run）、`references/{task-input-package,failure-recovery,dual-zone-convention}.md`（运行时约定形式化）。

**Tech Stack:** Claude Code skills（SKILL.md + templates/ + references/），Python 3 stdlib（脚本无硬依赖），JSON Schema draft 2020-12（scan-result.json 契约）。

**通用化纪律**：每个改动的 skill 自检 `grep -rni "dsp" skills/<skill>/`（0 命中）；新增脚本/references 同样 0 命中。测试靶子是 dsp（gitignored），只用于验证、不进源码——见 [[skills-must-be-generic]]。

**测试靶子**：dsp（gitignored）。本期含**新代码**（两个 Python 脚本 + 一个新 skill），故 GREEN = 脚本可跑通 + skill 结构校验 + 通用化 0 命中；脚本用 dsp 实测（读真实 scan-result.json/KB 文档）。

---

## 设计决策

1. **预算纪律内联，不跨文件**：叶 skill 的 subagent 只读自己那份 SKILL.md，预算红线必须在它眼前。常见骨架（禁扫清单 / 单步单产物 / top-N+待生成 / 证据先行）允许在 8 个叶 skill 间适度重复——这是 progressive-discipline 的取舍，DRY 在此会损可靠性。
2. **pm-verify-lite 是独立 skill，非 pm-verify 的开关**：lite 与 full 职责不同（lite=抽样速报、短输出；full=全量核对+推断项四分类+跨文档），各自一份 SKILL.md 更清晰。编排器波次 4 默认 dispatch lite，full 走 opt-in（人工指定 / 关键项目 / lite 发现高风险）。
3. **脚本 stdlib 优先**：validate-kb.py 与 update_ai_generated_block.py 只用 Python 3 标准库（json/re/os/sys/pathlib/argparse），CI 无需 pip install 即可跑；JSON Schema 校验用手写字段检查兜底（不强依赖 jsonschema 包）。
4. **P1 形式化为 references，不改核心流程**：任务输入包 / 失败恢复 / 双区约定写成 project-mastery/references/ 下的约定文档，供编排器按需加载；不动已有的波次硬依赖结构。
5. **三态置信度全链路一致**：机器字段英文枚举（confirmed/inferred/uncertain）、人类文档中文标签（已确认/推断得出/不确定）；validate 脚本强制 scan-result.json 的 confidence ∈ 三态枚举。

---

## per-skill 改动映射

### P0-3：输入输出预算纪律（pm-scan 已有，推广到其余 8 叶 skill）

| skill | 预算 section 放在哪 | 单产物 | 读预算要点 | 写预算 |
|---|---|---|---|---|
| pm-scan | 已有（扫描策略/规模指标） | 01+scan-result.json+scan-summary | 禁扫清单/限深3层/配置≤20 | 01 模板填充 |
| pm-techstack-generic | 新增 `## 输入输出预算` | 02 | Step0 读 scan-result.json；深挖≤15 文件/单文件≤500 行/禁扫 | 8000-12000 字；自封装>8 个详写 top N |
| pm-conventions | 新增 | 03 | 先读显式协作文档（≤8）+抽样代表性源文件≤15；禁扫 | 8000-12000 字；7 维度不足降级记录不外推 |
| pm-api-index | 新增 | 04 | 7 形态探测；源码打开≤20 文件；禁扫 | top N 对外全标调用关系，内部按引用排序 |
| pm-build-deploy | 新增 | 05 | 多构建并存扫描；配置文件≤20；禁扫 | 8000-12000 字；探测清单逐项，未发现显式注明 |
| pm-kb-index | 新增 | README | 读全部已生成 KB（01-05）+scan-result.json | README；任务路径≥2 |
| lp-feature-scan | 新增 | inventory.md | 5 层扫描；限深3层/文件≤20；禁扫 | 按 core 排序，不强求穷举 |
| lp-prompt-gen | 新增 | 每功能 prompt | 读 inventory 证据+01/02；证据路径 ls/grep 验证 | 单 prompt；五要素齐全 |
| lp-index | 新增 | README | 读 inventory/prompts/docs+progress.json | README；路径按依赖拓扑排序 |

**预算 section 模板**（~7 行，每 skill 适配）：
```
## 输入输出预算（小模型纪律）

- **单步单产物**：本次只产 `<doc名>`（一篇），不并行产其它。
- **读预算**：先读 <前置缓存/文档>；深挖按需打开 ≤N 个源码/配置文件，单文件 ≤500 行；禁扫 node_modules/dist/target/build/.git/vendor/__pycache__；限深 ≤3 层。
- **写预算**：默认 8000-12000 字；大项目只输出 top N（按 <依据>），其余进"待生成清单"延后。
- **证据先行**：每条结论带 `{文件路径}:行` 或配置字段；无证据标 `uncertain`/「推断」，不臆造。
```

### P0-5：pm-verify-lite（新 skill）

```
skills/pm-verify-lite/
├── SKILL.md                       (~110 行：定位/输入/产出/核心原则/抽样/边界/检查清单)
├── templates/06-校验报告.md        (lite 版，短：每文档抽样表 + 不一致项 + 覆盖率 + 风险信号)
└── references/verify-lite-rules.md (抽样 3-5 条/文档的规则 + lite vs full 何时升级)
```

**编排器改动**：
- project-mastery/SKILL.md 波次 4：默认 dispatch pm-verify-lite；完整 pm-verify 改为 opt-in（注明触发条件：人工指定 / 关键项目 / lite 报高风险）。
- project-mastery/references/wave-dispatch.md：新增 `### 波次 4（默认）：dispatch pm-verify-lite`；现有 `## 波次 4：dispatch pm-verify` 改标题为 `## 波次 4（opt-in）：dispatch pm-verify`。
- pm-kb-index 元信息：06-校验报告 由 lite 或 full 产，统一文件名。

### P1-2：validate-kb.py（新脚本）

`scripts/validate-kb.py {PROJECT_ROOT}`，检查项（每项 PASS/FAIL，汇总 exit code）：
1. **scan-result.json 契约**：存在；required 字段齐全（schema_version/project_root/generated_at/scanner/project/classifications/technologies/commands/modules/entrypoints/documents/questions）；classifications 恰好 1 条 is_primary=true；每条 confidence ∈ {confirmed,inferred,uncertain}；evidence 非空。
2. **占位符**：KB 文档（01-06/README）无未填占位符（`{PROJECT_ROOT}`/`{功能}`/`{模块}`/`TODO`/`TBD`/`XXX`）。
3. **死链**：README 的 markdown 链接指向的文件存在。
4. **必填章节**：01 有"项目类型"/"入口"；README 有"一句话简介"/"何时读"/"任务路径"/"元信息"（按存在性检查，缺失 WARN）。
5. **通用化**：`docs/project-knowledge/` 下文档无 `dsp` 字样（防泄露项目特定内容）。
6. **三态枚举**：scan-result.json 所有 confidence 字段值 ∈ 三态。

**输出**：人类可读报告 + 非零 exit code on FAIL。`--json` 可选输出机读。

### P1-1：update_ai_generated_block.py（新脚本）+ 双区约定

`scripts/update_ai_generated_block.py <doc.md> --section <id> --ai-file <new.md> [--dry-run]`：
- 约定标记：`<!-- AI-GENERATED:<section-id> START -->` ... `<!-- AI-GENERATED:<section-id> END -->` 与 `<!-- HUMAN-NOTES:<section-id> START -->` ... END。
- 只替换指定 section 的 AI-GENERATED 块，HUMAN-NOTES 块原样保留；块外的人工编辑不动。
- `--dry-run`：打印 diff 不写盘。
- `--init`：给一份无标记的文档注入默认标记骨架（按一级标题切 section）。

`references/dual-zone-convention.md`（project-mastery）：标记语法、何时用、与【更新】子流程的衔接（期2 实现【更新】时调用本脚本）。

### P1-7：failure-recovery.md（project-mastery references）+ progress.json 语义

`references/failure-recovery.md`：
- 单步失败运行时策略：**不重跑全流程**；"说明原因（写入 progress.json 的 phase.failure）→ 该结论标 pending/uncertain → 续跑下一独立步骤"。
- progress.json 的 phase status 扩展：`pending`/`in-progress`/`done`/`skipped`/`failed`；failed 带 `{reason, partialOutput, retryable}`。
- 编排器读到 failed phase：若 retryable=true 在收尾前重试一次；否则记入 manifest 的 `knownGaps`，不阻塞收尾。
- 各叶 skill 边界处理补一行"失败兜底"：本 skill 失败时产出降级（标 uncertain / 写部分 + 待补），不抛异常中断管线。

### P1-6：task-input-package.md（project-mastery references）

`references/task-input-package.md`：形式化每个 dispatch 任务的标准输入包组件：
- `task.md`：本次任务一句话 + 遵循哪个 SKILL.md + 产出路径（已在 wave-dispatch 模板里）
- `relevant-files.txt`：本步证据文件清单（scan-result.json 的 evidence/path 派生）
- `scan-result.json`：路由 + 基础结论（已有）
- `previous-output.md`：前置波次产出（01/02，已有）
- `output-template.md`：本步输出模板（templates/<doc>.md，已有）

wave-dispatch.md 各模板补一行"输入包组件"枚举（大多已有，形式化为显式清单）。

### P1-3：三态置信度硬化（验证 + 补齐）

- scan-result.json schema 已有 confidence enum（P0-1）→ validate 脚本强制（P1-2）。
- 检查 KB doc templates 是否要求中文三态标签：01 模板已要求；02-05 模板补"置信度用中文三态标签"提示（若缺）。
- learn-project 管线：lp-* 产出的 inventory/prompt 是否需要三态——inventory 的"证据"已隐含 confirmed；不强行加三态（学习链路证据导向，非结论判定），仅在 verify-lite 可选标注。

---

## 执行批次（commit 粒度）

1. **docs(plan)**：本计划文档。
2. **P0-3**：8 叶 skill 加预算 section（一批一个 commit，或两批：pm-* 一批 + lp-* 一批）。
3. **P0-5**：pm-verify-lite skill + project-mastery 路由 + wave-dispatch 更新。
4. **P1-2**：validate-kb.py + 用 dsp 实测。
5. **P1-1**：update_ai_generated_block.py + dual-zone-convention.md。
6. **P1-7**：failure-recovery.md + progress.json 语义 + 叶 skill 失败兜底。
7. **P1-6**：task-input-package.md + wave-dispatch 形式化。
8. **P1-3**：三态硬化检查 + template 补齐。
9. **验收**：写验收文档 + finishing 合并 main + 更新 memory。

---

## 验收（全部完成后）

- [ ] 8 叶 skill 各有"输入输出预算"section，且 ≤150 行（编排器 project-mastery 例外）。
- [ ] pm-verify-lite skill 完整（SKILL.md + template + reference），symlink 后 `~/.claude/skills/pm-verify-lite` 可见。
- [ ] project-mastery 波次 4 默认 dispatch lite；wave-dispatch.md 有 lite（默认）+ full（opt-in）两模板。
- [ ] `python3 scripts/validate-kb.py {dsp项目}` 在 dsp 上跑通（PASS/WARN/FAIL 合理）。
- [ ] `python3 scripts/update_ai_generated_block.py <test.md> --init --dry-run` 跑通。
- [ ] project-mastery/references/ 新增 task-input-package.md / failure-recovery.md / dual-zone-convention.md。
- [ ] 全 skill `grep -rni "dsp"`（含新文件）= 0 active 命中。
- [ ] 三态置信度全链路一致（schema + template + validate 脚本）。
- [ ] 写验收记录 `docs/superpowers/plans/2026-06-15-p0-3-p0-5-p1-small-model-hardening-验收.md`。
- [ ] finishing-a-development-branch 合入 main；更新 memory。
