---
name: pm-techstack-generic
description: 当波次 1 已完成、需要分析已有项目的技术栈（开源框架与自封装框架）与架构时使用。
---

# pm-techstack-generic — 通用技术栈分析与自封装框架识别

## 定位

pm-techstack-generic 是 project-mastery 学习管线的**波次 2** 分析 skill。它负责：
1. 清点**开源第三方框架/库**（名称、版本、用途、配置文件位置）
2. **识别项目自封装的内部框架/SDK/基类/中间件**（与开源框架明确区分）
3. 分析**架构模式**（分层、模块划分、数据流）
4. 梳理**核心模块依赖关系**

通用兜底：不区分项目类型，对所有项目类型（frontend / backend / fullstack / mobile / cli / library / other）均可执行。期 2 的特化 skill（pm-techstack-frontend / pm-techstack-backend / pm-techstack-fullstack）会在此基础上做深度特化。

## 输入

- `PROJECT_ROOT`：目标项目的根目录绝对路径
- `01-项目概览.md`：波次 1 pm-scan 的产出（作为上下文输入，提供项目类型、目录结构、入口点、顶层技术栈速览）
- `.codebase/scan-result.json`：波次 1 pm-scan 的机器契约缓存（Step 0 优先读）

## 产出

- `{PROJECT_ROOT}/docs/project-knowledge/02-技术栈与架构.md`

## Step 0：优先读扫描缓存（必做）

开始技术栈深挖前，先检查 `{PROJECT_ROOT}/.codebase/scan-result.json`：

- **存在**：直接复用其 `classifications` 与 `technologies` 字段作为基础清单。本 skill 只做**深挖补充**——版本细节、自封装框架识别、模块依赖关系、用途细化——**不重做顶层技术栈识别**。在产出的 02 文档顶部注明"基础技术栈清单复用自 `.codebase/scan-result.json`（pm-scan 生成）"。
- **不存在**：提示用户/编排器先跑 `pm-scan` 生成缓存；**不得自行重建一份 scan-result.json**（避免双份漂移）。若编排器坚持跳过，照常从零识别，并在 02 文档标注"未使用扫描缓存（.codebase/scan-result.json 缺失）"。

读缓存是小模型下的关键省 context 手段——避免把整份代码库再喂一遍。

## 分析策略

### 核心原则：先开源后自封装，先结构后细节

按以下顺序执行分析，**每一阶段拿到足够信息后决定是否需要继续深扫**：

#### 第 1 阶段：开源框架清点（必须执行）

从包管理器/构建配置中提取所有第三方依赖：

| 项目类型 | 依赖来源 |
|----------|----------|
| Java / Maven | `pom.xml`（含 parent POM 的 `<dependencyManagement>` 版本管理） |
| Java / Gradle | `build.gradle` / `build.gradle.kts` |
| Node.js / 前端 | `package.json`（dependencies + devDependencies） |
| Python | `pyproject.toml` / `requirements.txt` / `setup.py` |
| Go | `go.mod` |
| Rust | `Cargo.toml` |
| .NET | `*.csproj` / `packages.config` |
| Ruby | `Gemfile` / `Gemfile.lock` |

**清点纪律**：
- 每个框架/库必须记录：**名称、版本、用途、配置文件位置**
- 版本号必须从配置文件中提取，不猜测
- 用途一句话概括该框架在项目中的具体使用场景（不是泛泛描述）
- 配置文件位置：指出该框架的配置写在哪个文件（如 `application.yml`、`vite.config.js`）
- 排除项目自封装模块（Maven 子模块不属于开源框架）

#### 第 2 阶段：自封装框架识别（重点，必须执行）

这是本 skill 的**核心差异化能力**。不带 skill 的分析最容易在此处跑偏——只列依赖、漏掉项目自造的内部框架。

**识别策略——四步法**：

**步骤 1：定位自封装目录**

扫描项目目录结构，关注以下典型的自封装目录名：
- `common/`、`shared/`、`base/` — 公共模型/工具/接口定义
- `core/`、`kernel/` — 核心业务逻辑封装
- `engine/`、`runtime/` — 引擎/运行时封装
- `sdk/`、`lib/`、`libs/` — 内部 SDK
- `framework/`、`platform/` — 自造框架
- `utils/`、`util/`、`helpers/` — 被多处复用的工具库
- `middleware/` — 自造中间件
- `plugin/`、`plugins/` — 自造插件
- `components/`（非 node_modules 下） — 自造组件库
- `stores/`、`composables/`、`hooks/` — 自造状态/逻辑复用

**步骤 2：找被多处复用的基类/接口/工具**

通过 import/require 引用关系识别被多个模块依赖的内部类/模块：
- 搜索项目内部包的 import 语句（排除标准库和开源包）
- 找出被 3 个以上文件 import 的内部类/接口/函数
- 特别关注：基类（BaseXxx、AbstractXxx）、工厂类（XxxFactory）、注册器（XxxRegistry）、策略接口

**步骤 3：验证自封装特征**

对步骤 1-2 识别出的候选，验证以下特征（满足 2 条以上即可确认）：
- [ ] 有独立的目录/模块（不是零散文件）
- [ ] 有自己的内部包结构（子包、子目录）
- [ ] 被项目内多个其他模块/文件引用
- [ ] 提供了抽象/封装/统一接口（不是纯业务逻辑）
- [ ] 有文档/注释说明其设计意图
- [ ] 包含配置类/注解/自定义注解等框架级代码

**步骤 4：区分自封装 vs 开源**

严格区分：
- **开源第三方**：来自 Maven Central / npm registry / PyPI 等外部源的依赖
- **项目自封装**：项目源码目录内的模块/类/函数，且满足上述自封装特征
- **标准库**：语言自带的标准库（如 java.util、java.lang、Node.js 内置模块）不列入开源框架清单，也不列入自封装

**自封装框架记录要求**：
- 每个自封装框架需记录：**名称、所在目录/模块、核心组件清单、被哪些模块依赖、设计意图（一句话）**
- 核心组件清单需列出关键类/接口/文件及其职责
- **极小项目豁免**：若项目规模极小或确无自封装模块，在自封装章节注明"经扫描未发现项目自封装框架"，不强制凑数

#### 第 3 阶段：架构模式分析（必须执行）

基于前两阶段收集的信息和目录结构，分析：

1. **分层架构**：识别 Controller → Service → Repository/DAO → Database 等分层
2. **模块划分**：识别功能模块（如用户模块、订单模块、引擎模块）及其职责
3. **数据流**：从请求入口到响应出口的核心数据流路径
4. **设计模式**：识别项目显著使用的设计模式（如策略模式、工厂模式、观察者模式、DAG 编排等）

#### 第 4 阶段：模块依赖关系（必须执行）

梳理模块间的依赖关系。**执行方法**：通过 import/require 引用关系、模块配置（pom.xml 的 `<modules>` 声明、package.json 的内部包引用、go.mod 的 replace 指向等）构建依赖关系。

- 用依赖矩阵或 DAG 图表示
- 标注解耦接口（通过接口/抽象避免循环依赖的设计）
- 标注外部基础设施依赖（数据库、缓存、消息队列等）

## 产出格式

### 02-技术栈与架构.md 模板

> 产出格式见 `templates/02-技术栈与架构.md`（执行时读取该模板填充，勿自行发明结构）。

## 执行检查清单

执行 pm-techstack-generic 时，按以下顺序完成：

0. [ ] **Step 0**：检查 `.codebase/scan-result.json`——存在则复用其 classifications/technologies 基础清单（只深挖、不重做顶层识别），并在 02 文档注明复用来源；不存在则提示先跑 pm-scan
1. [ ] 读取 `01-项目概览.md` 作为上下文输入
2. [ ] 从包管理器/构建配置中清点所有开源框架（名称/版本/用途/配置位置）
3. [ ] 执行自封装框架识别四步法：定位目录 → 找引用 → 验证特征 → 区分自封装
4. [ ] 记录每个自封装框架的详细信息（核心组件/依赖方/设计意图）
5. [ ] 分析架构模式（分层/模块划分/数据流/设计模式）
6. [ ] 梳理模块依赖关系（DAG/解耦接口/外部依赖）
7. [ ] 按模板格式写入 `02-技术栈与架构.md`
8. [ ] 自检：开源框架有版本？自封装章节独立（若无可注明未发现）？架构模式完整？模块依赖清晰？
