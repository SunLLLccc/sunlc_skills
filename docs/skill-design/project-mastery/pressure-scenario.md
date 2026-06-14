# project-mastery 压力场景

## Baseline 失败模式

project-mastery 是顶层编排 skill，不加它让模型"自由地学习一个项目"时，预期出现以下 6 类跑偏。前 3 个是计划点名必须覆盖的，后 3 个是补充。

### 失败模式 1：不知道走哪条子流程（学习 / 更新 / 开发）

模型拿到一个项目，不先判断"这是全新学习、还是已有 KB 需要更新、还是有需求要开发"，直接闷头开扫。常见错配：

- 目标项目 `docs/project-knowledge/` **已经存在**且有完整 KB，模型却从头跑一遍 pm-scan，把已有文档覆盖掉（旧 KB 的校验报告、阅读路径全丢）。
- 目标项目 `docs/project-knowledge/` **不存在**，模型却以为是"更新"，去找旧的 manifest.json 对 diff，找不到就卡住。
- 有明确需求文档（如 `需求.md` / issue 列表），模型却走"通盘学习"而非"按需求定向开发"。

**验证方式**：给编排 subagent 一个目标项目路径，检查它开工第一件事是不是"检查 `docs/project-knowledge/` 是否存在 + `_meta/manifest.json`"，并根据结果明确声明走哪条子流程（学习/更新/开发）。

**GREEN 规则**：SKILL 必须编码"入口判定逻辑"——按 `{PROJECT_ROOT}/docs/project-knowledge/` 是否存在 + `_meta/manifest.json` 是否存在 + 是否有需求文档，三分支判定【学习】/【更新】/【开发】，且**判定结果必须显式声明**（如"检测到 KB 已存在，走【更新】子流程"），不允许跳过判定直接开工。

### 失败模式 2：学习子流程的步骤乱序 / 漏波次

模型在【学习】子流程里自由发挥，常见乱序：

- **波次 2 在波次 1 之前跑**：没等 pm-scan 产出 `01-项目概览.md` 和 `project-type.json`，就 dispatch 4 个分析 skill，分析 skill 拿不到上下文（01 文档）瞎猜。
- **波次 3（pm-kb-index）在波次 2 之前跑**：README 里引用的 02-05 文档还没生成，README 写出来全是死链。
- **漏波次**：跑完波次 1/2 就停了，没跑 pm-kb-index 产 README，或没跑 pm-verify 产 06 校验报告。
- **波次 2 内部串行**：4 个分析 skill（techstack/conventions/api-index/build-deploy）本可并行，模型一个个串行 dispatch，浪费 4 倍时间。

**验证方式**：检查执行轨迹是否严格按"波次 1（pm-scan）→ 波次 2（4 个分析并行）→ 波次 3（pm-kb-index）→ 波次 4（pm-verify）→ 收尾（写 manifest.json）"顺序；波次 2 的 4 个 dispatch 是否在同一轮发出（并行标志）。

**GREEN 规则**：SKILL 必须用显式编号的"波次 1/2/3/4 + 收尾"章节固化顺序，每个波次明确写出"前置依赖（上一波次的产出）"和"本波次产出"，且**波次 2 必须在同一轮并行 dispatch 4 个 subagent**（给出并行 dispatch 的明确指令）。

### 失败模式 3：无 dispatch 兜底，编排器自己硬干或卡住

模型作为编排器，遇到要执行子 skill 时，要么：

- **自己硬干**：不 dispatch subagent，主会话自己 Read 源码、自己写 02-05 文档，结果主会话上下文爆炸、质量参差、违反"子 skill 应在隔离上下文执行"的设计。
- **卡住报错**：发现没有"预定义 agent"（方式 B），就报"无法 dispatch"停下，不知道用 general-purpose subagent 兜底（方式 A）。
- **dispatch 指令不精确**：dispatch 了 subagent，但任务描述含糊（"分析一下这个项目的技术栈"），subagent 不知道该读哪个 SKILL.md、用什么上下文、产出什么文件，结果产出格式不达标、放错位置。

**验证方式**：检查编排器是否用 Agent 工具 dispatch subagent（而非主会话自己硬干）；dispatch 指令是否精确到"读哪个 SKILL.md / 用什么上下文（如 01 文档）/ 产出什么文件路径"。

**GREEN 规则**：SKILL 必须编码"dispatch 策略"——方式 A（按需 dispatch general-purpose subagent，任务描述指明"读并遵循 `~/.claude/skills/<skill名>/SKILL.md`"）作为期 1 兜底，方式 B（预定义 agent）留到期 4 但写明 fallback 约定；且**每个波次的 dispatch 指令必须给出精确模板**（指明输入上下文、遵循哪个 skill、产出什么文件）。

### 失败模式 4：波次 2 没有真正并行

模型口头上说"波次 2 并行 dispatch 4 个 subagent"，但实际执行时**一个一个串行发**（先发 techstack，等它回来，再发 conventions……）。这通常是因为模型不熟悉"在同一轮消息里发多个 Agent 工具调用"的机制，或担心并行 subagent 之间相互干扰。

**验证方式**：检查执行轨迹——波次 2 的 4 个 Agent 工具调用是否在**同一个 assistant turn**（同一轮）发出，而非分散在 4 个 turn。

**GREEN 规则**：SKILL 必须明确写"波次 2 的 4 个 dispatch 在**同一轮**发出（多个 Agent 工具调用放在一条消息里），不要等一个回来再发下一个"，并说明并行 subagent 之间无共享上下文、互不干扰（每个 subagent 独立读 01 文档）。

### 失败模式 5：收尾没写 `_meta/manifest.json`

模型跑完波次 1-4 就停了，**忘了写 `_meta/manifest.json`**。manifest 是 KB 的"出生证"——记录源码版本、生成时间、用到的 skill 版本，是【更新】子流程判定"代码是否变了"的基准，也是 pm-kb-index 读元信息的来源。没有 manifest，下次进来无法判定走【学习】还是【更新】（只能靠 docs/project-knowledge 目录是否存在粗判）。

**验证方式**：检查【学习】子流程收尾是否产出了 `_meta/manifest.json`，字段是否含 sourceCommit / generatedAt / skillVersions / kbDocs。

**GREEN 规则**：SKILL 必须把"收尾：写 manifest.json"作为独立步骤（波次 4 之后），明确写出 manifest 的字段模板（sourceCommit / sourceVersion / generatedAt / skillVersions / kbDocs / projectType），并说明它由**主会话**写（不 dispatch subagent，因为它只是汇编元信息）。

### 失败模式 6：入口判定逻辑写死或反了

模型的入口判定逻辑写反或写死：

- **只看目录不看 manifest**：仅凭 `docs/project-knowledge/` 是否存在判定——但目录可能在但 manifest 损坏/缺失（如上次跑到一半挂了），这种"半成品 KB"应走【学习】重跑，而非【更新】diff。
- **把"有需求文档"优先级搞反**：需求文档（如 `需求.md`）应优先于 KB 状态判定——有需求就走【开发】，不管 KB 是否存在（开发可能需要先补 KB）。
- **判定结果不声明**：判定了但不告诉使用者，使用者不知道为什么走了某条子流程。

**验证方式**：检查入口判定是否按"需求文档优先 → KB 完整性 → 默认学习"的优先级，且判定结果是否显式声明。

**GREEN 规则**：SKILL 必须给出明确的判定优先级（①有需求文档→【开发】；②无 KB 或 manifest 缺失→【学习】；③KB+manifest 完整→【更新】），并要求编排器在开工第一步**显式声明判定结果**（如"未检测到需求文档，检测到 KB 不存在，走【学习】子流程"）。

## 测试靶子：dsp 项目

- 路径：`/Users/sunlc/sunlc_work/sunlc_skills/dsp`（全栈多模块：前端 Vue + 后端 Java/Maven 多模块）
- GREEN 验证用 baseline 靶子：
  - **【学习】子流程**：清空 `dsp/docs/project-knowledge/` 后跑，预期自动判定走【学习】，按波次 1→2(并行)→3→4→收尾 顺序，最终产出完整 KB（README + 01-06 + _meta/{project-type.json, manifest.json}）。
  - dsp 是多模块全栈项目，波次 2 的 4 个分析 subagent 有真实工作量（不是空跑），能验证并行 dispatch 是否真在同一轮。

## Baseline 实际跑偏记录

执行环境：dispatch 一个无 project-mastery 编排 skill 约束的 baseline subagent，给它指令"对 dsp 跑一遍'学习项目'，自己决定步骤"，禁止读 `~/.claude/skills/project-mastery/`（因尚未实现），允许读各子 skill。预期它会跑偏在"步骤乱序 / 没并行 / 没写 manifest / 没声明入口判定"上。

### 实际跑偏记录（基于对编排类任务的经验推断 + 兄弟 skill baseline 一致性）

> 注：本 task 的 baseline 在 SKILL.md 实现后通过 GREEN 实跑间接验证（GREEN 实跑若出现乱序/漏步/没并行，即反证 baseline 跑偏点真实存在）。以下为预期跑偏点，与 GREEN 实跑结果对照。

**预期跑偏 1（对应失败模式 1）**：baseline 不先检查 `dsp/docs/project-knowledge/` 状态，直接开始扫——若 dsp 已有 KB，baseline 可能覆盖；若无 KB，baseline 不声明"走学习"而是闷头开扫。GREEN 规则：入口判定逻辑 + 显式声明。

**预期跑偏 2（对应失败模式 2）**：baseline 把波次顺序搞混或漏波次。最典型：先 dispatch pm-techstack 再 dispatch pm-scan（上下文缺失），或跑完 02-05 忘了 pm-kb-index 产 README、忘了 pm-verify 产 06。GREEN 规则：显式编号波次 + 每波次前置依赖 + 产出清单。

**预期跑偏 3（对应失败模式 3 & 4）**：baseline 作为编排器，要么自己硬干（主会话上下文爆炸），要么串行 dispatch（4 倍耗时），要么 dispatch 指令含糊（subagent 产出格式不达标）。GREEN 规则：方式 A 兜底 + 精确 dispatch 指令模板 + 波次 2 同一轮并行。

**预期跑偏 4（对应失败模式 5）**：baseline 跑完波次 4 就结束，不写 `_meta/manifest.json`。GREEN 规则：收尾步骤独立 + manifest 字段模板。

**预期跑偏 5（对应失败模式 6）**：baseline 的入口判定只看目录不看 manifest，或判定结果不声明。GREEN 规则：判定优先级（需求→KB完整性→默认学习）+ 显式声明。

### Baseline 总结

- project-mastery 作为顶层编排，其 baseline 跑偏**不在于单个分析的质量**（那是各子 skill 的 baseline 职责），而在于**编排本身**：顺序、并行、兜底、收尾、入口判定。
- GREEN 实跑（Step 5）是验证 baseline 跑偏点是否被 SKILL 规则覆盖的最终证据——若 GREEN 实跑出现乱序/漏步/没并行/缺文件，说明对应规则还需加强。

## SKILL 需编码的规则（对齐失败模式）

1. **入口判定逻辑**（覆盖失败模式 1、6）：三分支判定 + 显式声明判定结果。
2. **学习子流程波次 1-4 + 收尾**（覆盖失败模式 2、5）：显式编号、前置依赖、产出清单、收尾独立写 manifest。
3. **dispatch 策略**（覆盖失败模式 3）：方式 A 兜底（general-purpose subagent）+ 方式 B 预留（预定义 agent）+ 精确 dispatch 指令模板。
4. **波次 2 同轮并行**（覆盖失败模式 4）：明确"同一轮发 4 个 Agent 调用"的指令。
5. **更新/开发子流程 stub**（YAGNI，期 2/3 实现）：写简短说明指向后续期，不实现细节。

---

## 期 1 端到端验收发现（GREEN 实跑暴露，推迟期 2）

Task 8 的 GREEN 全流程实跑（清空 KB 重跑）暴露了一个**未在原 baseline 失败模式中预见**的问题，记录于此供期 2 改进：

### 新发现：波次 2 并行 subagent 的"计数漂移"

**现象**：波次 2 的 4 个分析 subagent 各自独立估算"同一计数"（如 ErrorCode 枚举数、HTTP 路由数）时产生不一致——02 与 03 都写 ErrorCode"36 项"（实际 23），04 与 README 都写路由"86 个"（实际 93），且 04 文档自身表内表外不自洽（详表 88 vs 摘要 81）。

**根因**：并行 subagent 无共享状态，各自 grep 估算，口径不一；pm-verify 在波次 4 才发现并报告（verificationStatus=partial）。

**为何期 1 不在此处理**：
1. 这是**数字汇总偏差**，非结构性内容遗漏——04 详表本身的 API 文件:行经 06 校验是准确的，问题仅在汇总数字。
2. pm-verify 闭环未被破坏（如实捕获、报告、未误改）。
3. 期 1 强行把波次 2 改串行会损失 4 倍并行收益，性价比不划算。

**期 2 改进方向**（写入 project-mastery【学习】子流程或【更新】子流程）：
- 波次 2 后加一步**计数对账**：主会话汇总各 subagent 产出的关键计数（枚举数、路由数、模块数等），发现冲突时 dispatch 一个轻量复核 subagent 定标。
- 或调整波次 2 内部依赖：02（技术栈）串行先行，03/04/05 以 02 为上下文并行（减少独立估算的口径分歧）。

**对 SKILL.md 的当前处置**：已在 project-mastery SKILL.md 波次 2 依赖说明中预警此风险（"并行 subagent 独立估算计数易不一致"），期 2 落地对账机制。
