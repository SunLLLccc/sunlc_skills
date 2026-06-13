# project-mastery（项目学习与开发）设计文档

> **子项目 A：开发导向**
> 日期：2026-06-14
> 状态：设计已确认，待写实现计划
> 输出语言：中文

---

## 1. 背景与目标

构建一套**通用的、可复用的** skills + agents 工具集，让模型在接手**任意已有项目**时能够：

1. **学习**：自动吃透项目（类型、技术栈、自封装框架、开发规范、API、构建部署），产出该项目的**知识库文档**。
2. **更新**：项目代码变更后，增量刷新知识库中受影响的文档。
3. **开发**：基于需求文档 + 知识库，串联 superpowers 现有 skills（brainstorming / writing-plans / executing-plans / TDD / verification）完成开发。

**核心定位**：skills 承载方法论（单一真相源），agents 作为执行壳执行对应 skill。知识库是学习阶段的产物，也是开发阶段的上下文输入。

**不在本 spec 范围**（推迟到后续 spec）：
- 子项目 B：开源项目学习文档生成（功能扫描 → 每功能提示词 → 初学者学习文档）。
- 知识库的可选深度章节：i18n 规范、性能分析、安全审计。

---

## 2. 关键设计决策（已与用户确认）

| # | 决策 | 选择 |
|---|---|---|
| 1 | 使用场景 | 通用工具集（每次应用到新项目，产出该项目专属知识库） |
| 2 | 架构形态 | 混合：skills 做方法论 + agents 执行对应 skill |
| 3 | agent 机制 | 方式 B（预定义 agent 薄壳）为主 + 方式 A（按需 dispatch）兜底 |
| 4 | 技术栈分析 | 路由器模式：pm-scan 识别类型 → 分发到 pm-techstack-{类型} 专属 skill |
| 5 | v1 路由器类型 | 前端 / 后端 / 全栈 + 通用兜底（generic） |
| 6 | 需求文档 | 外部输入；pm-dev 第一步做"理解与细化"（对齐、补全、去歧义、标冲突） |
| 7 | 拆分策略 | 拆 2 子项目；先做 A（开发导向），B（学习文档）下一周期 |
| 8 | 命名 | `pm-` 前缀，顶层编排 skill 为 `project-mastery` |
| 9 | 知识库位置 | 目标项目内 `docs/project-knowledge/` |
| 10 | verify 定位 | 只报告问题，不自动修改 |

---

## 3. 整体架构

### 3.1 skills 清单（方法论，单一真相源）

| Skill | 职责 | 执行者 |
|---|---|---|
| `project-mastery` | 顶层编排：判断走"学习 / 更新 / 开发"哪个子流程 | 主会话 |
| `pm-scan` | 扫描 + 类型识别（路由器），产「项目概览」+ 类型判定 | agent: pm-scan-agent |
| `pm-techstack-generic` | 通用技术栈分析（兜底，能处理所有类型） | agent: pm-techstack-agent |
| `pm-techstack-frontend` | 前端项目技术栈分析 | agent: pm-techstack-agent |
| `pm-techstack-backend` | 后端项目技术栈分析 | agent: pm-techstack-agent |
| `pm-techstack-fullstack` | 全栈项目技术栈分析 | agent: pm-techstack-agent |
| `pm-conventions` | 开发规范提取 | agent: pm-conventions-agent |
| `pm-api-index` | API 索引生成 | agent: pm-api-agent |
| `pm-build-deploy` | 构建打包部署梳理 | agent: pm-build-deploy-agent |
| `pm-kb-index` | 知识库总索引汇编（前门） | 主会话（轻） |
| `pm-verify` | 分析结果校验（引用 `verification-before-completion`） | agent: pm-verify-agent |
| `pm-update` | 增量更新编排 | 主会话 |
| `pm-dev` | 开发编排：需求细化 + 注入知识库 + 串联 superpowers | 主会话 |

> **类型扩展性**：未来增加新项目类型（移动端/桌面端/库/Monorepo/微服务）= 新增一个 `pm-techstack-{类型}` skill，pm-scan 路由器加一个分支，不动其他 skill。

### 3.2 agent 机制：方式 B 为主 + 方式 A 兜底

**dispatch 策略（写进 `project-mastery` 与 `pm-update` 的执行规则）：**

> 每个 skill 的执行，**优先用其专属预定义 agent**（如 `pm-scan-agent`）。
> **若该 agent 未定义/未配置** → orchestrator **按需 dispatch 一个通用 subagent**，任务描述里指明"遵循 `<skill名>` 方法论"来执行。

**预定义 agent 清单（薄执行壳，方法论仍在 skill 里）：**

| Agent | 执行的 skill | 工具权限 |
|---|---|---|
| `pm-scan-agent` | pm-scan | Read, Glob, Grep, Bash, Write |
| `pm-techstack-agent` | pm-techstack-{由 scan 结果决定加载哪个} | Read, Glob, Grep, Write |
| `pm-conventions-agent` | pm-conventions | Read, Glob, Grep, Write |
| `pm-api-agent` | pm-api-index | Read, Glob, Grep, Write |
| `pm-build-deploy-agent` | pm-build-deploy | Read, Glob, Grep, Bash, Write |
| `pm-verify-agent` | pm-verify | Read, Glob, Grep（只读，返回问题清单） |

**协调类 skill 放主会话**（非"执行步骤"）：`pm-kb-index`（拼索引）、`pm-update`（编排）、`pm-dev`（编排）。

**带来的好处**：
1. 优雅降级——某 agent 没建好也能跑（靠按需 dispatch）。
2. 渐进式搭建——可先不建任何 agent 端到端跑通，后续按需给关键步骤配专属 agent 收紧权限。
3. DRY 不破坏——方法论只在 skill 里，agent 是薄壳。

### 3.3 三条子流程衔接

```
用户说"学习/开发这个项目"
        │
   project-mastery (主会话)
        │
   判定：知识库不存在 →【学习】；存在且代码变了 →【更新】；有需求文档 →【开发】
        │
   ┌────┼────────────┬──────────────┐
   ▼    ▼            ▼
 [学习]  [更新]     [开发]
```

---

## 4. 知识库文档结构

### 4.1 目录结构

```
docs/project-knowledge/
├─ README.md                ← 总索引（前门，pm-kb-index 产出）
├─ 01-项目概览.md            ← pm-scan
├─ 02-技术栈与架构.md        ← pm-techstack-{类型}
├─ 03-开发规范.md            ← pm-conventions
├─ 04-API索引.md             ← pm-api-index
├─ 05-构建打包部署.md        ← pm-build-deploy
├─ 06-校验报告.md            ← pm-verify
└─ _meta/
   ├─ manifest.json         ← 各文档：源码 git SHA、生成时间、来源 skill、文件 hash（增量更新用）
   └─ project-type.json     ← 类型判定结果 + 置信度 + 依据（router 决策 & update 都用）
```

### 4.2 各文档内容大纲

| 文档 | 关键章节 |
|---|---|
| **01-项目概览** | 项目类型（可多维度，如 frontend+lib）· 目录结构概览 · 规模指标（文件数/行数/语言占比）· 入口点 · 顶层技术栈速览 · **类型判定依据+置信度** |
| **02-技术栈与架构** | 开源框架清单（名称/版本/用途/配置位置）· **自封装框架**（项目自造的内部 SDK/基类/工具库/中间件——重点识别）· 架构模式（分层/模块划分/数据流）· 核心模块依赖关系 |
| **03-开发规范** | 目录规范 · 命名规范（文件/变量/函数/类/组件）· 代码封装规范（模块化/抽象层级）· **前端样式规范**（如适用：CSS 方案/主题/响应式）· 错误处理 · 测试规范 · Git 提交规范（从历史推断） |
| **04-API索引** | 按模块/领域分类 · 每个 API：路径或签名/入出参/用途/`文件:行` · 对外 API vs 内部 API · 调用关系 |
| **05-构建打包部署** | 环境要求 · 依赖安装 · 开发启动 · 构建/打包命令+产物 · 部署方式（Docker/K8s/静态托管）· 环境变量 · CI/CD |
| **06-校验报告** | 各文档置信度 · 抽样核对结果（文档断言 vs 实际代码）· 待人工确认的可疑项 |
| **README（总索引）** | 一句话简介 · 各文档导航（链接+"何时读哪份"）· 知识库元信息 · 快速上手路径（"开发某功能→先读 02+03+04"） |

**自封装框架识别策略**（写进 pm-techstack skill）：扫 import、找被多处复用的基类/utils、找 `lib/` `core/` `sdk/` `common/` 等目录，区分"标准包/开源包" vs "项目自造的"。

---

## 5. 学习子流程详解

```
project-mastery 判定：知识库不存在 → 进入学习子流程

【波次 1】dispatch pm-scan-agent
   输入：项目根路径
   产出：01-项目概览.md + _meta/project-type.json（类型判定）
   策略：先扫顶层结构/配置文件/入口点，大项目不盲目全扫，先定位再深扫

【波次 2】主会话读 project-type.json → 确定分发哪个 pm-techstack-* skill
   并行 dispatch 4 个 agent（每个都拿 01-项目概览.md 作为上下文输入）：
   ├─ pm-techstack-agent   → 02-技术栈与架构.md
   ├─ pm-conventions-agent → 03-开发规范.md
   ├─ pm-api-agent         → 04-API索引.md
   └─ pm-build-deploy-agent→ 05-构建打包部署.md
   （4 者相互独立 → 真并行）

【波次 3】主会话执行 pm-kb-index
   读全部文档 → 产 README.md 总索引

【波次 4】dispatch pm-verify-agent
   抽样核对各文档 vs 实际代码 → 产 06-校验报告.md（返回问题清单，不自动改）

【收尾】写 _meta/manifest.json（git SHA/时间/hash）
   project-mastery 汇报完成，提示可进入开发子流程
```

**波次设计取舍**：波次 2 的 4 个分析 agent 都以波次 1 的「项目概览」为输入（拿到类型、结构、入口点就够开工），不等技术栈文档完成——这样真并行。若 verify 发现某文档因缺技术栈上下文而不准，会在校验报告里标出。

---

## 6. 更新子流程详解（pm-update）

**核心机制**：用 `_meta/manifest.json` 里的 git SHA 做基线，diff 出变更，按映射表定位受影响的文档，只重跑那几个 agent。

```
pm-update 流程（主会话编排）：

1. 读 manifest 的 baseSHA vs 当前 HEAD → git diff --name-only → 变更文件清单
   （无 git 仓库时退化为文件 hash 比对）

2. 按【变更→受影响文档】映射表定位：
   ┌─────────────────────────────┬──────────────────────────────────┐
   │ 变更特征                      │ 受影响文档                         │
   ├─────────────────────────────┼──────────────────────────────────┤
   │ package.json/构建配置/依赖变更 │ 02-技术栈 + 05-构建打包部署         │
   │ 目录结构/新增模块              │ 01-项目概览 + 02-技术栈             │
   │ 大量源码（命名/封装模式变化）   │ 03-开发规范                        │
   │ 路由/控制器/接口定义变更        │ 04-API索引                         │
   │ 换框架/类型根本变化/变更>阈值   │ ⚠ 提示：变更过大，建议全量重跑学习流程 │
   └─────────────────────────────┴──────────────────────────────────┘

3. 对受影响的文档，重新 dispatch 对应 agent（预定义优先，无则按需 dispatch）
4. 重跑 pm-kb-index 更新总索引
5. dispatch pm-verify 复核变更部分（只验变更的，不全验）
6. 更新 _meta/manifest.json（新 SHA/hash/时间）
```

**两个兜底**：
- **无 git** → 用 manifest 里的文件 hash 比对当前文件 hash 检测变更。
- **变更过大**（换框架 / 变更文件占比超阈值）→ 不硬打补丁，**提示走全量学习子流程**。

---

## 7. 开发子流程详解（pm-dev）

**定位：薄编排。** pm-dev 不重新实现 SDD/TDD，它只做三件事 + 一个可选回流。

```
pm-dev 流程（主会话执行）：

【步骤 1】需求文档理解与细化
   输入：外部需求文档（可能粗糙）+ 项目知识库
   做什么：
   - 把需求"接地"到项目：映射到实际模块/API/规范
   - 粗糙的需求 → 结构化、补全、去歧义
   - 发现矛盾/与规范冲突 → 标出，请用户决策（不擅自定）
   产出：对齐过的【需求理解】（要改什么/涉及哪些模块/约束/验收标准）

【步骤 2】选择性注入知识库（不全塞，避免上下文爆炸）
   按【需求理解】涉及的范围，注入相关章节：
   - 必注入：01-项目概览（类型/结构）+ 03-开发规范
   - 按需注入：02-技术栈（涉及框架/自封装库时）、04-API索引（改/加 API 时）、05-构建部署（涉及构建/部署时）
   全文留在磁盘供深挖，上下文里只放精选摘要 + 引用指针

【步骤 3】串联 superpowers（每步都"接地"到知识库）
   brainstorming   ← 带【需求理解】+ 注入的KB，做设计
   writing-plans   ← 计划遵循 03规范 + 02架构
   executing-plans / subagent-driven-development ← 实现时用自封装框架、走 05构建流程
   TDD             ← 测试遵循 03提取的测试规范
   verification-before-completion ← 完成前对照知识库确认没破坏规范

【步骤 4】知识库回流（仅提示，不自动）
   若本次开发新增了 API / 改了架构 / 改了构建方式 → 提示用户：
   "建议触发 pm-update 更新知识库" —— 由用户决定是否更新
```

**关键原则**：
- pm-dev 是胶水，不是新方法论——SDD/TDD 全交给 superpowers，pm-dev 只确保这些步骤"接地"到项目知识库。
- 需求细化阶段必须标冲突、不擅自定——遇到需求与项目规范矛盾，停下问用户。
- 知识库回流仅提示——不自动触发 update，避免打扰。

---

## 8. 构建顺序（4 期，每期是执行检查点）

利用 dispatch-fallback 原则：**先让所有 skill 跑通（按需 dispatch），再补 agent**。

| 期 | 范围 | 产出 | 验证 |
|---|---|---|---|
| **期 1：学习管线核心** | `project-mastery` + `pm-scan`(路由) + `pm-techstack-generic` + `pm-conventions` + `pm-api-index` + `pm-build-deploy` + `pm-kb-index` + `pm-verify` | 对任意项目端到端产出知识库（技术栈先走通用兜底，所有类型都能跑） | 在 dsp 项目上跑通 |
| **期 2：路由器特化 + 更新** | `pm-techstack-frontend/backend/fullstack`（router 分支）+ `pm-update` | 前后端全栈精准分析 + 增量更新 | dsp 各子模块验证；改代码验证增量更新 |
| **期 3：开发编排** | `pm-dev` | 需求→细化→注入KB→串superpowers 全链路 | 用 1 个需求文档走完整开发流程 |
| **期 4：预定义 agents** | 给关键步骤配专属 agent（build-deploy 的 Bash、scan 的只读收紧等） | 权限收紧 + 可发现性 | 验证 agent 正确执行其 skill |

**技术栈分析起步策略**：期 1 先做 `pm-techstack-generic`（通用兜底，能处理所有类型，只是不深），这样期 1 就能对任意项目工作；期 2 再加前端/后端/全栈特化让 router 分流（YAGNI）。

---

## 9. 测试策略

### 9.1 每个 skill 用 writing-skills（TDD for skills）

每个 skill 用 superpowers 的 `writing-skills` 技能来写——TDD 应用到文档：
1. 先设计"压力场景"（一个 subagent 在没有这个 skill 时会怎么跑偏）
2. 记录跑偏的 baseline 行为
3. 写 skill 文档针对那些跑偏
4. 验证 subagent 现在遵守了
5. 找新漏洞 → 补 → 再验

### 9.2 测试靶子：dsp 项目

**路径**：`/Users/sunlc/sunlc_work/sunlc_skills/dsp`
**类型**：全栈（前端 `dsp-admin-web` + 后端多模块 `dsp-parent`，含 dsp-core/dsp-engine/dsp-data-service/dsp-offline-service/dsp-common/dsp-admin-service）
**用途**：
- 期 1：验证学习管线对全栈项目产出准确知识库。
- 期 2：验证 fullstack 特化 + 多模块场景 + 增量更新。
- 不作为 spec 主体——spec 是通用工具集设计，dsp 仅作验证靶子。

---

## 10. 推迟范围（不在本 spec）

- **子项目 B**：开源项目学习文档生成（独立 spec，下一周期）。复用本子项目的扫描底座（pm-scan / pm-techstack）。
- **知识库可选深度章节**：i18n 规范、性能分析、安全审计——未来按需加为知识库的可选文档。
