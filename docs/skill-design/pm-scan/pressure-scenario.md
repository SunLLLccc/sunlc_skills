# pm-scan 压力场景

## Baseline 失败模式

不加 pm-scan skill，让模型直接"扫描项目 dsp，识别项目类型并给概览"时，预期出现以下 3 类跑偏：

### 失败模式 1：盲目全扫导致超 token / 超时

模型试图遍历项目的每一个目录和文件（包括 node_modules、target、.git 等），消耗大量 token，甚至超时，而不是先扫顶层结构、配置文件、入口点，再按需深扫。

**验证方式**：观察 subagent 是否读取了大量不必要的文件（node_modules、target 下的 class 文件、.git 内部等）。

### 失败模式 2：类型强塞进"前端/后端/全栈"三选一

模型将项目类型硬塞为三选一，忽略移动端/桌面端/CLI/库/Monorepo/微服务等类型。对于 dsp 这样前端+后端多模块的项目，可能只判定为"全栈"而丢失微服务架构维度。更可能直接忽略 dsp-parent 是 Maven 多模块的微服务事实。

**验证方式**：检查类型判定是否支持多维度叠加（如 `["fullstack", "microservices", "monorepo"]`），还是只有一个字符串。

### 失败模式 3：不输出类型判定的依据与置信度

模型给出一个类型判定（如"这是一个全栈项目"），但不说明为什么这么判定、基于哪些证据、置信度如何。router 无法信任这个判定，无法判断是否需要人工复核。

**验证方式**：检查产出中是否有 `evidence`（证据列表）和 `confidence`（置信度）字段。

## 测试靶子：dsp 项目

- 路径：`/Users/sunlc/sunlc_work/sunlc_skills/dsp`
- 预期类型判定：`fullstack` + `microservices` + `monorepo`（多维度叠加）
- 证据：dsp-admin-web（Vue 3 + Vite 前端）+ dsp-parent（Spring Boot 多模块后端，6 个子模块，Dubbo 微服务）
- 置信度：高（≥ 0.9），因为 package.json 和 pom.xml 的证据非常明确

## Baseline 实际跑偏记录（2026-06-14）

使用 general-purpose subagent，prompt「扫描项目 dsp，识别它是什么类型的项目并给概览，不要参考任何 skill」。

### 失败模式 1（盲目全扫）：部分确认

baseline 用了 10 个 Bash + 5 个 Read 调用。虽然未直接扫描 node_modules/target（可能因 dsp 项目规模中等、这些目录未被 find maxdepth=2 覆盖），但它：
- 用 `find ... -maxdepth 2 -type f | head -80` 扫描了大量源文件
- 深扫了 dsp-parent 子目录结构和 dsp-engine Java 源文件
- 对更大的项目（数千文件），这种模式会超 token/超时

### 失败模式 2（类型强塞三选一）：确认

baseline 输出为非结构化文本，类型描述为"前后端分离的全栈 Java Web 项目"+"后端微服务（多模块 Maven）"——语义上是对的，但：
- 不是结构化的多维度数组
- 无标准化的类型标识符（如 fullstack/microservices/monorepo）
- router 无法程序化读取和决策

### 失败模式 3（无依据和置信度）：确认

baseline 产出仅为一段 Markdown 文本，没有：
- `confidence` 字段
- `evidence` 字段
- 结构化的 JSON 判定文件
- 任何可供 router 信任的可验证证据

### 额外跑偏：产出过多

baseline 产出了大量本属于 pm-techstack 阶段的信息（架构详情、缓存机制、29个内置函数、安全漏洞列表等），超出 pm-scan 的职责范围。pm-scan 应只做概览和类型判定，详细分析留给后续 skill。
