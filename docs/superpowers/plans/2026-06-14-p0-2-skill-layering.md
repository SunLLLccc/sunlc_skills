# P0-2 实施计划：12 skill 瘦身 + templates/references 分层

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 12 个 SKILL.md 的内嵌输出模板抽到 `templates/`、长规则细节抽到 `references/`，SKILL.md 只留流程核心（定位/输入/产出/流程/边界/检查清单），回归 superpowers progressive disclosure，目标单 skill ≤~150 行（重 skill 靠 references 压到 ~120）。

**Architecture:** 每个 skill 自包含 `skills/<skill>/{SKILL.md, templates/, references/}`。symlink 指向整个 skill 目录，子目录自动可见（无需重链）。SKILL.md 里用"产出格式见 `templates/<doc>.md`（执行时读取填充）"+"规则详见 `references/<topic>.md`"做按需加载。

**Tech Stack:** Claude Code skills（SKILL.md + YAML frontmatter），progressive disclosure，bash 结构校验。

**通用化纪律**：每个改动的 skill 自检 `grep -rni "dsp" skills/<skill>/SKILL.md`（0 命中）；抽出的 templates/references 也须 0 命中。

**测试靶子**：dsp（gitignored）。本期是**内容保持型重构**（剪切-粘贴-引用，不改语义），故 GREEN 以**结构校验**为主（frontmatter 完整、模板内容与原内嵌一致、目标行数达成、symlink 仍可发现、通用化 0 命中），不重跑每个 skill 的功能 GREEN（行为不变）。

---

## 设计决策

1. **per-skill 子目录**：`skills/<skill>/templates/` + `skills/<skill>/references/`（非顶层共享目录）。每个 skill 自包含，避免跨 skill 耦合。
2. **templates/**：内嵌 ` ```markdown ` / ` ```json ` 输出文档模板块 → `templates/<doc>.md`。SKILL.md 替换为一行引用。
3. **references/**：长规则/策略细节（类型表、识别四步法、校验规则等"判断依据"）→ `references/<topic>.md`。SKILL.md 保留 1-2 行摘要 + 引用。
4. **SKILL.md 保留**：frontmatter + 定位 + 输入 + 产出 + 核心流程（步骤序列）+ 边界处理要点 + 执行检查清单。
5. **引用措辞统一**：
   - 模板：`产出格式见 \`templates/<doc>.md\`（执行时读取该模板填充，勿自行发明结构）。`
   - 规则：`判定/识别规则详见 \`references/<topic>.md\`（按需读取）。`

## per-skill 抽离映射

| skill | 当前行数 | templates/ | references/ | 目标 |
|---|---|---|---|---|
| project-mastery | 410 | manifest.json, progress.json | wave-dispatch（波次+dispatch模板细节）| ~140 |
| pm-build-deploy | 345 | 05-构建打包部署.md | build-deploy-rules（构建/部署分析规则）| ~130 |
| pm-verify | 317 | 06-校验报告.md | verify-rules（三元组+抽样规则）| ~130 |
| pm-conventions | 241 | 03-开发规范.md | conventions-rules（规范推断规则）| ~120 |
| pm-api-index | 234 | 04-API索引.md | api-rules（API 提取规则）| ~120 |
| pm-scan | 243 | 01-项目概览.md | project-types（类型表+判定）, scan-strategy（扫描层级）| ~120 |
| pm-kb-index | 218 | README.md | reading-path-rules（任务路径设计）| ~120 |
| pm-techstack-generic | 216 | 02-技术栈与架构.md | analysis-strategy（4阶段+自封装四步法）| ~120 |
| lp-feature-scan | 158 | inventory.md | — | ~110 |
| lp-index | 163 | README.md | — | ~110 |
| lp-prompt-gen | 147 | prompt.md | — | ~100 |
| learn-project | 117 | （progress.json 小，保留内嵌）| — | ~117（已达标，不动）|

## 执行批次

- **Batch A（重，>300）**：project-mastery、pm-build-deploy、pm-verify（模板+references，最大收益）
- **Batch B（中，200-260）**：pm-scan、pm-techstack-generic、pm-kb-index、pm-conventions、pm-api-index（模板+部分 references）
- **Batch C（轻，<170）**：lp-feature-scan、lp-index、lp-prompt-gen（仅抽模板）；learn-project（已达标，跳过）

## File Structure（新增）

```
skills/<each-skill>/
├── SKILL.md            瘦身后的流程核心
├── templates/          输出文档模板（从 SKILL.md 抽出）
│   └── *.md / *.json
└── references/         长规则细节（从 SKILL.md 抽出）
    └── *.md
```

## 每个 skill 的标准步骤

1. [ ] 读当前 SKILL.md（已读的跳过）
2. [ ] Write `templates/<doc>.md`（原内嵌模板块的完整内容）
3. [ ] （重 skill）Write `references/<topic>.md`（原长规则段落的完整内容）
4. [ ] Edit SKILL.md：内嵌模板块 → 引用行；长规则段 → 摘要+引用行
5. [ ] 校验：`wc -l SKILL.md`（达标）+ `grep -rni "dsp" skills/<skill>/`（0 命中，含新 templates/references）+ frontmatter 完整
6. [ ] 提交（每 skill 一个 commit，或每批一个）

## 验收（全部完成后）

- [ ] 全 12 skill `wc -l`：无超过 ~150（重 skill ~140）
- [ ] 全 skill `grep -rni "dsp"` 含 templates/references = 0
- [ ] 抽出的 templates/references 内容与原内嵌一致（抽查）
- [ ] `bash scripts/link-skills.sh` 后 `ls ~/.claude/skills/<skill>/{templates,references}` 可见（symlink 解析子目录）
- [ ] 写验收记录 `docs/superpowers/plans/2026-06-14-p0-2-skill-layering-验收.md`
- [ ] finishing-a-development-branch 合入 main
