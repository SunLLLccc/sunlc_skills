# 任务输入包约定（按需读取）

> 由 project-mastery 编排器按需加载。对应 claude优化清单 P1-6（吸收自 codex 点评）。
> 小模型不该在 200k context 里自己找上下文——工具层（编排器）切好片，模型只填空。

## 为什么要任务输入包

小模型（qwen3.6 35b）指令遵循弱、长程规划弱。如果 dispatch 时只给一句"分析技术栈"，它要自己在 200k 输入里找：读哪个 SKILL.md、读哪些已生成文档、读哪些源码、产出写到哪、按什么模板。每一环缺失都导致跑偏。

**任务输入包**把每步执行前的上下文准备**显式化、结构化**——编排器在 dispatch 前切好 5 个组件，subagent 拿到即可执行，无需自行推断缺失信息（对应 M-1：每个 dispatch 提示词自包含）。

## 五个组件

| 组件 | 内容 | 在 wave-dispatch 模板里的体现 |
|------|------|-------------------------------|
| **task.md** | 本次任务一句话 + 遵循哪个 SKILL.md + 产出绝对路径 + 工具约束 | dispatch 指令正文的"身份/遵循/产出/约束"段 |
| **relevant-files.txt** | 本步证据文件清单（从 scan-result.json 的 evidence/path 派生） | dispatch 指令的"输入：上下文"段指明的具体文档 |
| **scan-result.json** | 路由依据 + 基础结论（classifications/technologies/commands/...） | 波次 2+ 的输入里明确"读 .codebase/scan-result.json" |
| **previous-output.md** | 前置波次产出（01-001-项目概览 / 02-001-技术栈与架构） | dispatch 指令的"输入：上下文文档"段（如 01、02） |
| **output-template.md** | 本步输出模板（templates/<doc>.md） | SKILL.md 的"产出格式见 templates/<doc>.md"引用行 |

## 编排器的职责：dispatch 前切包

dispatch 每个 subagent 前，编排器（主会话）应核对这 5 个组件齐备：

1. **task.md 齐备？**——dispatch 指令含：身份声明 + "读并严格遵循 `~/.claude/skills/<skill>/SKILL.md`" + PROJECT_ROOT 绝对路径 + 产出绝对路径 + "不要使用 TaskCreate/TaskUpdate/TodoWrite"。
2. **relevant-files.txt 齐备？**——指令指明读哪几份已生成 KB 文档作为上下文（不靠 subagent 自己猜）。
3. **scan-result.json 齐备？**——波次 2+ 的指令显式写"读 `.codebase/scan-result.json`"。
4. **previous-output.md 齐备？**——依赖前置波次的，指令写明读 01（波次 2 全部）/ 02（波次 2 并行同伴）。
5. **output-template.md 齐备？**——SKILL.md 里有"产出格式见 `templates/<doc>.md`"引用行，subagent 执行时读取。

## 与 wave-dispatch.md 的关系

`references/wave-dispatch.md` 的每个波次 dispatch 指令模板**已经是任务输入包的实例化**——它把上述 5 个组件填进了具体波次的具体内容。本约定是"为什么这么写"的形式化说明：

- wave-dispatch.md = 任务输入包的**实例**（每波次一份）
- task-input-package.md = 任务输入包的**约定**（5 组件清单 + 编排器核对职责）

**期 2/4 增强**：未来可让编排器真正把 5 组件写成磁盘文件（`_meta/tasks/<phase>/{task.md,relevant-files.txt,...}`），subagent 读文件而非读 prompt——进一步降 prompt 长度、提可重放性。期 1 用 prompt 内嵌（当前 wave-dispatch.md 形态）已足够。

## 边界

- **前置产出未就绪**（如波次 2 并行时 02 尚未写完）：relevant-files/previous-output 组件降级——指令写明"以 01 为主、02 为辅，02 未就绪则基于 01 启动"（见 wave-dispatch.md 波次 2 的处理）。
- **scan-result.json 缺失**：波次 2+ 的指令提示"先跑 pm-scan"，不自行重建（避免双份漂移）。
- **无对应模板**（如 06-001-校验报告 lite/full 两版）：output-template 组件指明当前用哪个模板（lite 默认 / full opt-in）。
