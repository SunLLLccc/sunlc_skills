---
name: pm-scan
description: 当开始学习一个已有项目、需要扫描其目录结构/配置文件/入口点以识别项目类型、启动 project-mastery 学习管线时使用。
---

# pm-scan — 项目扫描与多维度类型识别

## 定位

pm-scan 是 project-mastery 学习管线的**波次 1**，是**路由器**。它扫描项目、判定类型，产出的类型判定供 project-mastery 决定后续分发哪个技术栈 skill（pm-techstack-frontend / pm-techstack-backend / pm-techstack-fullstack / pm-techstack-generic）。

## 输入

- `PROJECT_ROOT`：目标项目的根目录绝对路径

## 产出

1. `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md` — 项目概览文档（人类可读）
2. `{PROJECT_ROOT}/.codebase/scan-result.json` — **机器契约**，须符合 `schemas/codebase-scan-result.schema.json`（后续 pm/lp skill 优先读它）
3. `{PROJECT_ROOT}/.codebase/scan-summary.md` — 人类速览（一段话总结项目类型/技术栈/入口/命令）

> 注：旧版产出的 `_meta/project-type.json` 已退役，其内容被 scan-result.json 的 `classifications` 取代。**若目标项目存在旧版 `_meta/project-type.json`（前序版本产物），pm-scan 执行时删除它**——该文件是本工具集的退役产物，非用户内容。

## 扫描缓存（机器契约，必产）

pm-scan 除人类可读的 01 文档外，**必须**产出机器可消费的扫描缓存，供后续 pm/lp skill 复用，避免重复扫描（小模型下尤其关键——重扫既费 context 又易不一致）。

### scan-result.json 写入规则

须符合 `schemas/codebase-scan-result.schema.json`，逐字段：

1. `schema_version` 固定 `"1.0"`；`project_root` 填目标项目绝对路径；`generated_at` 填执行时 ISO-8601 时间戳（`date -u +"%Y-%m-%dT%H:%M:%SZ"`）。
2. `scanner`：`{"name": "pm-scan", "version": "v2"}`（v2 = 引入缓存契约后的版本）。
3. `project`：`name`（从 package.json/pom.xml/README 取）+ `summary`（一句话）+ `confidence`（三态）+ `evidence`。
4. `classifications`：从"类型识别规则"的多维度叠加结果填入。每条带 `type` + `is_primary`（最核心类型标 true，仅 1 条）+ `confidence`（三态）+ `evidence`。**取代旧 types/primaryType**。
5. `technologies`：第 1 层识别到的技术栈（语言/框架/包管理/构建/测试工具），每条带 name/version(可空)/category/purpose/confidence/evidence。
6. `commands`：从配置文件 scripts 字段提取的命令（install/dev/build/test 等），每条带 name/command/working_directory/purpose/confidence/evidence。
7. `modules`：monorepo/多模块项目的子模块，每条带 name/path/role/module_type/depends_on/confidence/evidence。单模块项目可只填 1 条（项目自身）。
8. `entrypoints`：第 2 层定位的入口点，每条带 name/path/kind/description/confidence/evidence。无单一入口则留空数组并在 questions 里说明。
9. `documents`：扫描到的关键文档（README/CLAUDE.md/架构图等），每条带 path/role/notes。
10. `questions`：无法确认的项，每条带 question/reason/可选 suggested_confirmation。

### scan-result.json 三态置信度（取代 0-1 浮点）

每条结论的 `confidence` 字段是枚举：

| 英文枚举（机器字段） | 中文标签（人类文档展示） | 含义 |
|---|---|---|
| `confirmed` | 已确认 | 源码/配置/依赖声明/项目文档中有直接证据 |
| `inferred` | 推断得出 | 由目录结构、命名、调用关系等间接证据合理推断 |
| `uncertain` | 不确定 | 证据不足、存在冲突或需运行才能确认 |

**铁律**：机器字段一律用英文枚举（`confirmed`/`inferred`/`uncertain`）；人类文档（01-项目概览.md）一律用中文标签。`uncertain` 的结论必须同时在 `questions[]` 里写明缺口，不得臆造补全。

### scan-summary.md（人类速览）

一段话（3-8 行）：项目是什么、主要类型、核心语言/框架、入口、关键命令。从 scan-result.json 提炼，不引入新结论。

## 扫描策略

### 核心原则：先顶层后深扫，不盲目遍历全树

按以下层级逐步扫描，**每一层拿到足够信息后决定是否需要继续深扫**，避免读取不必要的文件：

#### 第 1 层：顶层结构识别（必须执行）

1. **列出顶层目录**：`ls -la {PROJECT_ROOT}`，获取目录树的第一层
2. **识别并跳过无关目录**：`node_modules/`、`target/`、`build/`、`.git/`、`dist/`、`__pycache__/`、`vendor/`、`.idea/`、`.vscode/` 等不需要扫描
3. **读取关键配置文件**（按存在性探测，不是全部都读）：
   - `package.json` — Node.js / 前端项目标识
   - `pom.xml` 或 `build.gradle` 或 `build.gradle.kts` — Java 项目标识
   - `go.mod` — Go 项目标识
   - `Cargo.toml` — Rust 项目标识
   - `pyproject.toml` / `setup.py` / `requirements.txt` — Python 项目标识
   - `Gemfile` — Ruby 项目标识
   - `*.csproj` / `*.sln` — .NET 项目标识
   - `CMakeLists.txt` / `Makefile` — C/C++ 项目标识
   - `docker-compose.yml` / `Dockerfile` — 容器化标识
   - `CLAUDE.md` / `README.md` — 项目说明（快速获取上下文）
4. **判定是否为 Monorepo**：顶层有 `lerna.json`、`pnpm-workspace.yaml`、`nx.json`、或 pom.xml 的 `<modules>` 多模块声明、或 `workspace` 字段的 package.json

#### 第 2 层：入口点定位（按需执行）

application / cli / web 服务类项目必须执行；library 或纯聚合模块若无明确入口点可标注"无单一入口"并跳过。

根据第 1 层识别到的技术栈，定位入口点：

| 技术栈 | 入口点探测方式 |
|--------|---------------|
| Node.js / 前端 | `package.json` 的 `main` / `module` / `bin` 字段；`index.html`；`src/main.ts` / `src/main.js` / `src/App.vue` / `src/App.tsx` |
| Java / Spring Boot | pom.xml 中的 Spring Boot parent；`src/main/java/**/Application.java` 或 `*Application.java` |
| Go | `main.go` 或 `cmd/*/main.go` |
| Python | `setup.py` 的 `entry_points`；`main.py`；`manage.py`（Django）；`app.py`（Flask） |
| Rust | `src/main.rs` |

#### 第 3 层：按需深扫（仅在需要更多证据时）

当第 1-2 层信息不足以确定类型或需要更多规模指标时，才进入深扫：

1. **目录结构概览**（不含无关目录）：用 `find` 或递归 `ls` 获取 2-3 层深度目录树
2. **子模块扫描**（Monorepo / 多模块项目）：读取每个子模块的配置文件（子 pom.xml、子 package.json）
3. **框架探测**：读取依赖声明中的框架名（如 Spring Boot、Vue、React、Django 等）

### 扫描纪律

- **禁止扫描**：`node_modules/`、`target/`、`build/`、`.git/`、`dist/`、`__pycache__/`、`vendor/`、`.DS_Store`、二进制文件
- **限制深度**：一般情况下扫描不超过 3 层目录深度（子模块内部除外，子模块也只扫其配置文件）
- **限制文件读取量**：单次扫描总共读取的配置文件不超过 20 个；若需更多，说明原因并优先完成类型判定

## 类型识别规则

### 多维度叠加

项目类型是一个**数组**，不是单选。一个项目可以同时是多个类型。

例如：一个同时含前端与后端、且后端拆分为多个独立可部署服务的多模块项目 = `["fullstack", "microservices", "monorepo"]`

### 类型清单

| 类型标识 | 判定条件 |
|----------|----------|
| `frontend` | 有 `package.json` 且依赖含 React/Vue/Angular/Svelte 等前端框架；或有 HTML 入口 + 前端构建工具（Webpack/Vite/Rollup/esbuild） |
| `backend` | 有服务端框架（Spring Boot/Django/Express/FastAPI/NestJS 等）；或 pom.xml/build.gradle/go.mod 等后端项目标识 |
| `fullstack` | 同时有 `frontend` 和 `backend` 的证据 |
| `mobile` | 有 React Native/Flutter/SwiftUI/Kotlin Multiplatform/Capacitor 等移动端框架 |
| `desktop` | 有 Electron/Tauri/.NET WPF/Qt 等桌面端框架 |
| `cli` | package.json 有 `bin` 字段；或有 `commander.py`/`cobra` 等 CLI 框架 |
| `library` | package.json 的 `main` 字段指向库入口且无前端框架依赖；或有 `setup.py` 且 `py_modules`/`packages` 存在；Cargo.toml 有 `[lib]` |
| `monorepo` | 顶层有 workspace/lerna/nx/pnpm-workspace 配置；或 pom.xml 有多 `<module>`；或顶层 package.json 有 `workspaces` 字段 |
| `microservices` | 多个独立可部署的服务（每个有自己的启动入口/端口/独立配置）；或 docker-compose 定义多个服务；或 Dubbo/gRPC 等微服务框架 |
| `other` | 以上都不匹配时使用 |

### 判定流程

1. 逐一检查每个类型的判定条件
2. 收集匹配的证据（具体文件名、配置内容、依赖声明等）
3. 所有匹配的类型都加入类型数组（多维度叠加）
4. 若无任何匹配，标记为 `["other"]`
5. **is_primary 标记规则**：在 scan-result.json 的 `classifications` 里，给最核心（最能代表项目本质）的那条类型标 `is_primary: true`（仅 1 条）；若多个类型置信度并列，取最能代表项目本质的（如全栈项目取 `fullstack` 而非 `microservices`）。取代旧 `primaryType` 字段。

## 规模指标采集

在扫描过程中，采集以下规模指标（写入概览文档）：

| 指标 | 采集方式 |
|------|----------|
| 顶层目录数 | `ls` 统计 |
| 子模块数 | 从 monorepo/workspace/pom modules 配置获取 |
| 主要语言 | 从配置文件和源码扩展名推断 |
| 配置文件列表 | 扫描到的配置文件清单 |

**注意**：不要求精确的行数统计（避免全树遍历）。用 `find` 做粗略的文件数估计即可（排除 node_modules/target 等无关目录）。

## 产出格式

### 01-项目概览.md 模板

```markdown
# 项目概览

> 由 pm-scan 自动生成

## 项目类型

- **类型判定**：{type1}, {type2}, ...
- **置信度**：{已确认/推断得出/不确定}（对应 scan-result.json 的 confirmed/inferred/uncertain）
- **判定依据**：见 `.codebase/scan-result.json` 中对应条目的 evidence 字段

## 目录结构概览

{用树形或缩进列表展示顶层和关键子目录结构，不含 node_modules/target 等无关目录}

## 规模指标

| 指标 | 值 |
|------|------|
| 子模块/子项目数 | {n} |
| 主要语言 | {language1}, {language2}, ... |
| 配置文件 | {列出关键配置文件} |

## 入口点

| 模块/子项目 | 入口文件 | 说明 |
|------------|----------|------|
| {module} | {file} | {brief description} |

## 顶层技术栈速览

| 技术 | 版本 | 用途 | 证据位置 |
|------|------|------|----------|
| {tech} | {version，如配置中可直接读到则填，不强制} | {purpose} | {config file} |
```

### _meta/project-type.json（已退役）

类型判定的结构化结果已迁入 `.codebase/scan-result.json` 的 `classifications` 字段，不再单独产 project-type.json。

## 置信度与依据要求

### 置信度等级（三态）

见上文"扫描缓存（机器契约）"的三态表：`confirmed`（已确认）/ `inferred`（推断得出）/ `uncertain`（不确定）。机器字段用英文枚举，01 文档用中文标签。

### 低置信度处理

当某条结论为 `uncertain`（不确定）时：
- 在 scan-result.json 该结论对应条目的 `questions[]` 里写明缺口（question + reason）。
- 在概览文档（01）的项目类型处标注"**建议人工复核**"。

### 依据要求

**每一条类型判定都必须附带至少一条具体证据。** 证据必须是：

- **具体**：指出具体的文件名、配置项、依赖声明，不能用"看起来像"等模糊描述
- **可验证**：他人可以根据证据描述找到源文件并验证
- **格式**：`{文件路径}: {具体内容描述}`

例如：
- 好：`{模块路径}/package.json: dependencies 含 "vue": "^x.y.z"（写明具体文件路径与依赖名/版本）`
- 差：`有 Vue 相关的依赖（未指出文件与具体依赖）`

## 边界处理

- **无单一入口**：library、纯聚合模块、无明确启动入口的项目——入口点定位步骤标注"无单一入口"并跳过，不强行编造入口。
- **配置文件超过 20 个**：优先完成类型判定，超出部分说明原因（如"多模块项目，每模块一组配置"）并只读对判定关键的，不强求全读。
- **多类型并列选 is_primary**：当多个类型置信度相同时，取最能代表项目本质的那个标 `is_primary: true`（如全栈项目取 `fullstack` 而非 `microservices`；库项目取 `library` 而非 `cli`）。
- **低置信度（uncertain）**：当某条类型判定为 `uncertain` 时，在 scan-result.json 该条目的 `questions[]` 写明缺口，并在概览文档项目类型处标注"**建议人工复核**"。
- **极小项目（<20 文件）**：证据可能不足以高置信度判定，如实标注 confidence（多为 `inferred`/`uncertain`），不强行拔高；规模指标如实反映小规模。

## 执行检查清单

执行 pm-scan 时，按以下顺序完成：

1. [ ] 列出顶层目录，识别并跳过无关目录
2. [ ] 探测并读取关键配置文件（最多 20 个）
3. [ ] 判定是否为 Monorepo / 多模块项目
4. [ ] 定位入口点
5. [ ] 按类型清单逐一判定，收集证据
6. [ ] 计算置信度
7. [ ] 采集规模指标
8. [ ] 写入 `docs/project-knowledge/01-项目概览.md`（置信度用中文三态标签）
9. [ ] 写入 `.codebase/scan-result.json`（schema 校验通过）+ `.codebase/scan-summary.md`
10. [ ] 自检：scan-result.json required 字段齐全？每条结论带 evidence 且 path 真实？uncertain 项进 questions？不再产 project-type.json？
