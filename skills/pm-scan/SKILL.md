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

1. `{PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md` — 项目概览文档
2. `{PROJECT_ROOT}/docs/project-knowledge/_meta/project-type.json` — 结构化类型判定（供 router 读取）

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

例如：dsp 项目 = `["fullstack", "microservices", "monorepo"]`

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
5. **primaryType 选取规则**：从 types 数组中取置信度最高的类型作为 primaryType；若多个类型置信度并列，取最能代表项目本质的那个（如全栈项目取 `fullstack` 而非 `microservices`）

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
- **置信度**：{high/medium/low}（{具体数值，如 0.9}）
- **判定依据**：见 `_meta/project-type.json` 中的 evidence 字段

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

### _meta/project-type.json 模板

```json
{
  "projectName": "项目名称（从 package.json/pom.xml/README 获取）",
  "projectRoot": "项目根目录的绝对路径",
  "types": ["fullstack", "microservices", "monorepo"],
  "primaryType": "fullstack",
  "confidence": 0.9,
  "requiresHumanReview": false,
  "evidence": [
    {
      "type": "fullstack",
      "indicators": [
        "dsp-admin-web/package.json: 存在 Vue 3 + Vite 前端依赖",
        "dsp-parent/pom.xml: 存在 Spring Boot 后端多模块"
      ]
    },
    {
      "type": "microservices",
      "indicators": [
        "dsp-parent/pom.xml: 6个子模块，含独立服务模块 dsp-data-service, dsp-offline-service, dsp-admin-service",
        "依赖 Dubbo 3.2.11 微服务框架"
      ]
    },
    {
      "type": "monorepo",
      "indicators": [
        "dsp-parent/pom.xml: <modules>声明 6 个子模块",
        "顶层包含独立前端项目 dsp-admin-web"
      ]
    }
  ],
  "scannedAt": "ISO 8601 时间戳",
  "scanVersion": "pm-scan v1"
}
```

## 置信度与依据要求

### 置信度等级

| 等级 | 范围 | 含义 |
|------|------|------|
| high | 0.8 - 1.0 | 配置文件/依赖声明中有明确证据，几乎无歧义 |
| medium | 0.5 - 0.79 | 有间接证据（如目录结构推断），但缺少配置文件直接声明 |
| low | 0.0 - 0.49 | 证据不足，类型判定不确定，建议人工复核 |

### 低置信度处理

当整体置信度为 low（<0.5）时：
- 在 `project-type.json` 中添加可选字段 `"requiresHumanReview": true`
- 在概览文档的项目类型处标注"**建议人工复核**"

### 依据要求

**每一条类型判定都必须附带至少一条具体证据。** 证据必须是：

- **具体**：指出具体的文件名、配置项、依赖声明，不能用"看起来像"等模糊描述
- **可验证**：他人可以根据证据描述找到源文件并验证
- **格式**：`{文件路径}: {具体内容描述}`

例如：
- 好：`dsp-admin-web/package.json: dependencies 含 "vue": "^3.5.32", "element-plus": "^2.13.7"`
- 差：`有 Vue 相关的依赖`

## 执行检查清单

执行 pm-scan 时，按以下顺序完成：

1. [ ] 列出顶层目录，识别并跳过无关目录
2. [ ] 探测并读取关键配置文件（最多 20 个）
3. [ ] 判定是否为 Monorepo / 多模块项目
4. [ ] 定位入口点
5. [ ] 按类型清单逐一判定，收集证据
6. [ ] 计算置信度
7. [ ] 采集规模指标
8. [ ] 写入 `docs/project-knowledge/01-项目概览.md`
9. [ ] 写入 `docs/project-knowledge/_meta/project-type.json`
10. [ ] 自检：每条类型都有证据？置信度合理？产出格式符合模板？
