# pm-scan 扫描策略（按需读取）

> 由 SKILL.md 抽出，执行扫描时按需加载。

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

