# P0-2 验收记录：12 skill 瘦身 + templates/references 分层

> 对应计划：`docs/superpowers/plans/2026-06-14-p0-2-skill-layering.md`
> 范围：`claude优化清单.md` 的 **P0-2**（progressive disclosure：SKILL.md 只留流程核心，模板→templates/、长规则→references/）
> 验收日期：2026-06-14
> 方式：python 脚本辅助的机械剪切-粘贴-引用（内容保持型重构，不改语义）

## 1. 总体效果

**12 skill 总行数 2809 → 1569（-44%，抽取 1240 行）**。11/12 skill ≤150 行；project-mastery 282（编排器，含入口判定/波次流程/dispatch 策略/检查清单/stub，天然较重，不强制压到 120）。

| skill | 抽取前 | 抽取后 | 变化 |
|---|---|---|---|
| pm-conventions | 241 | 68 | -173（7 维度推断表→references）|
| pm-api-index | 234 | 80 | -154（判定/形态/调用/分析→references）|
| pm-build-deploy | 345 | 117 | -228（8 步分析策略→references，模板→templates）|
| pm-verify | 317 | 124 | -193（抽样+核对规则→references，模板→templates）|
| project-mastery | 410 | 282 | -128（dispatch 模板→references，manifest/progress→templates）|
| pm-scan | 243 | 140 | -103（扫描策略+类型规则→references，模板→templates）|
| pm-techstack-generic | 216 | 149 | -67（模板→templates）|
| pm-kb-index | 218 | 140 | -78（模板→templates）|
| lp-feature-scan | 158 | 134 | -24（模板→templates）|
| lp-index | 163 | 117 | -46（模板→templates）|
| lp-prompt-gen | 147 | 101 | -46（模板→templates）|
| learn-project | 117 | 117 | 0（已达标，未动）|

## 2. 分层结构（每个 skill 自包含）

```
skills/<skill>/
├── SKILL.md            瘦身后的流程核心（定位/输入/产出/流程/边界/检查清单）
├── templates/          输出文档模板（从内嵌 ```markdown/```json 抽出）
└── references/         长规则细节（从 SKILL.md 抽出，执行时按需读取）
```

**templates/**（10 skill，10 个 markdown 模板 + project-mastery 的 manifest.json/progress.json）：
- pm-scan: 01-项目概览.md
- pm-techstack-generic: 02-技术栈与架构.md
- pm-conventions: 03-开发规范.md
- pm-api-index: 04-API索引.md
- pm-build-deploy: 05-构建打包部署.md
- pm-kb-index: README.md
- pm-verify: 06-校验报告.md
- lp-feature-scan: inventory.md
- lp-prompt-gen: prompt.md
- lp-index: README.md
- project-mastery: manifest.json, progress.json

**references/**（6 skill）：
- project-mastery: wave-dispatch.md（波次 1/2/4 的 dispatch 指令模板）
- pm-scan: scan-strategy.md（3 层扫描策略）、project-types.md（类型判定表）
- pm-build-deploy: build-deploy-rules.md（8 步分析策略 + 标注规则）
- pm-verify: verify-rules.md（抽样策略 + 5 步核对 + 四分类）
- pm-conventions: conventions-rules.md（7 维度推断方法）
- pm-api-index: api-rules.md（对外/内部判定 + 形态探测 + 调用关系 + 分析策略）

## 3. 引用契约（progressive disclosure）

SKILL.md 里统一用两类引用行，模型执行时按需加载对应文件：
- 模板：`> 产出格式见 \`templates/<doc>.md\`（执行时读取该模板填充，勿自行发明结构）。`
- 规则：`... 详细 ... 见 \`references/<topic>.md\`（执行时按需读取）。`

## 4. 验证

- **行数达标**：11/12 ≤150（见上表）；project-mastery 282（编排器，可接受）。
- **通用化**：`grep -rni "dsp" skills/`（含 templates/references）→ **0 active 命中**（仅剩"已退役/取代"说明性文字）。
- **frontmatter**：12/12 完整（`name:` + `description:`）。
- **symlink 可见性**：`~/.claude/skills/<skill>/{templates,references}/` 经 symlink 解析可见（symlink 指向整个 skill 目录，子目录自动可见，无需重链）。
- **内容保真**：脚本用 `lines[s:e]` 机械切片，抽取的 templates/references 内容与原内嵌一致；SKILL.md 保留流程核心 + 摘要。

## 5. 设计决策

1. **per-skill 子目录**（非顶层共享）：每个 skill 自包含 `templates/`+`references/`，避免跨 skill 耦合。
2. **脚本辅助机械抽取**：模板（```markdown/```json 块）+ 规则段（按章节边界）用 python 脚本统一抽，比逐个 Edit 更稳更快；手工处理 project-mastery 波次2 的交错结构 + wave-dispatch.md 清理。
3. **SKILL.md 保留**：定位 + 输入 + 产出 + 核心流程（步骤序列/摘要）+ 边界处理 + 执行检查清单；把"判断依据/探测清单/指令模板"等细节移到 references。
4. **编排器不强制压到 120**：project-mastery 的入口判定/波次硬依赖/dispatch 策略是编排核心，过度抽取会损精度；282 可接受。

## 6. commit 清单（分支 p0-2-skill-layering）

1. 抽取 10 skill markdown 模板到 templates/
2. project-mastery: manifest/progress 模板 + wave-dispatch references（411→282）
3. pm-build-deploy/pm-scan: 分析策略/扫描策略/类型规则 → references
4. pm-verify/pm-conventions/pm-api-index: 核对/推断/API 规则 → references
5. docs(plan): P0-2 计划

## 7. 延后 / 注意

- **行为未重跑验证**：本期是内容保持型重构（剪切-粘贴-引用），语义不变，故未重跑每个 skill 的功能 GREEN；结构校验（行数/通用化/frontmatter/symlink）已通过。下次跑 project-mastery 全流程时可顺带验证 references 按需加载正常。
- **project-mastery 仍 282**：编排器天然较重；若后续要进一步瘦身，可把"dispatch 策略 方式A/B + 职责划分"也抽到 references，但会损失编排精度的内联可见性，暂不做。
- **learn-project 未动**：117 行已达标，无内嵌 markdown 模板（仅 progress.json 小块，保留内嵌）。
