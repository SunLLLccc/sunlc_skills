---
name: pm-build-deploy
description: 当波次 1 已完成、需要从项目配置文件实际读取构建/打包/部署流程（不臆造命令、区分已验证与推断）时使用。
---

# pm-build-deploy — 从配置验证的构建打包部署梳理

## 定位

pm-build-deploy 是 project-mastery 学习管线的**波次 2** 部署梳理 skill。它扫描项目的构建/打包/部署相关配置文件，从**配置实际声明**中提取构建打包部署流程，逐项标注「已验证」（配置文件中直接找到）/「推断」（未直接找到，需人工确认），产出可供新成员照做部署、可供运维核对的流程文档。

与"凭项目类型印象写一套标准流程"的区别：本 skill 的每一条命令、每一种部署方式、每一个版本号，都必须能在配置文件中找到依据或在产出中显式标注为「推断」并说明依据，不臆造、不抄文档当配置、不补写顾问建议。

## 输入

- `PROJECT_ROOT`：目标项目的根目录绝对路径
- `01-项目概览.md`、`02-技术栈与架构.md`：波次 1/2 的产出（作为上下文输入，提供项目类型、目录结构、技术栈、多模块划分、自封装框架位置）

## 产出

- `{PROJECT_ROOT}/docs/project-knowledge/05-构建打包部署.md`

## 核心原则：命令/部署方式必须从配置文件实际读取

每一条命令、每一种部署方式、每一个版本号都必须满足以下三条铁律，否则禁止写入产出：

1. **有来源**：每条命令/部署方式/版本号必须附【来源】字段，标注它来自哪个配置文件的哪个字段（如 `{模块}/package.json: scripts.build`、`{模块}/pom.xml: build/plugins/spring-boot-maven-plugin`、`.nvmrc`）。禁止凭"这类项目一般这么跑"的印象写命令。
2. **有标注**：每条命令/部署方式/版本号必须附【标注】字段，值为「已验证」或「推断」：
   - **已验证**：在配置文件中**直接找到字面量**（如 package.json 的 scripts、pom.xml 的 plugin goal、Makefile 的 target）。附配置文件路径与字段。
   - **推断**：配置文件中**未直接找到**，需人工确认。必须说明推断依据（如"从 application.yml 的 server.port 推断端口"、从 baseURL 推断需要反向代理）。README/CLAUDE.md/AGENTS.md 等**文档**中的命令/版本号一律视为「推断」，标注来源文档（文档不是配置，可能过时）。
3. **只梳理现状**：产出只描述项目**当前实际**怎么构建打包部署。**禁止补写"建议流水线""推荐改造""若要补齐 CI/CD 应该…"等顾问建议**——那是另一个 skill 的职责。配置里没有的东西，要么注明"未发现"，要么标「推断」，不臆造、不建议。

**禁止行为**：把 README 的版本号当配置事实陈述；凭印象写"用 Docker 部署"而项目无 Dockerfile；补写"建议加 GitHub Actions"；把"配置里没写但我觉得生产应该这么跑"的 JVM 参数/守护方式当事实。

## 标注规则（贯穿全文档）

| 场景 | 标注 | 说明 |
|------|------|------|
| 命令字面量在 `package.json` scripts / `pom.xml` plugin goal / `Makefile` target / `Cargo.toml` 等配置中直接找到 | **已验证** | 附文件路径与字段 |
| 部署方式在 `Dockerfile` / `docker-compose.yml` / k8s manifest / `Makefile` 部署 target 中直接声明 | **已验证** | 附文件路径 |
| 版本号在 `<java.version>` / `engines` / `.nvmrc` / `.python-version` / `requires-python` 等配置中声明 | **已验证** | 附文件路径 |
| 环境变量/配置项在 `application.yml` / `.env.example` / `config.yaml` / 框架配置中声明 | **已验证** | 附文件路径 |
| CI 步骤在 `.github/workflows/*.yml` / `.gitlab-ci.yml` / `Jenkinsfile` 等中声明 | **已验证** | 附文件路径 |
| 命令/部署方式/版本号来自 README / CLAUDE.md / AGENTS.md / CONTRIBUTING.md 等文档 | **推断** | 标注来源文档（文档可能过时，需人工确认） |
| 配置文件未直接声明，从其他配置项间接推出（如从 server.port 推端口、从 baseURL 推反向代理） | **推断** | 说明推断依据 |
| 配置文件与文档均无，纯凭经验补的（如 JVM 参数、守护进程方式） | **推断** | 说明依据，并提示"需人工确认" |
| 探测某类配置（Dockerfile / CI / Makefile）后发现**不存在** | **未发现** | 显式注明"未发现 {配置类型}"，禁止臆造或补写建议 |

## 分析策略

### 第 0 步：多构建并存识别（必须执行）

项目可能同时有多种构建（前端 npm + 后端 Maven + 文档 mkdocs + 子模块 gradle）。开工时必须扫描项目内**所有**构建配置文件，每种构建独立成节梳理，不因"主技术栈"而漏掉次要构建。

**扫描清单**（按项目实际探测，存在的都要梳理）：

| 构建形态 | 探测方式 |
|----------|----------|
| Node.js / 前端 | 各级 `package.json`（含 monorepo 的每个 workspace） |
| Java / Maven | 各级 `pom.xml`（含多模块的每个子模块） |
| Java / Gradle | `build.gradle` / `build.gradle.kts` / `settings.gradle` |
| Python | `pyproject.toml` / `setup.py` / `requirements*.txt` / `Pipfile` |
| Go | `go.mod` + `Makefile`（Go 项目常借 Makefile 封装 build） |
| Rust | `Cargo.toml` |
| .NET | `*.csproj` / `*.sln` / `Directory.Build.props` |
| C/C++ | `CMakeLists.txt` / `Makefile` |
| Ruby | `Gemfile` / `Rakefile` |
| 文档/站点 | `mkdocs.yml` / `docusaurus.config.js` 等 |

### 第 1 步：环境要求（必须执行）

从**配置文件**提取运行时版本要求。**README/CLAUDE.md 的版本号只能作「推断」线索**，不能当配置事实。

| 运行时 | 配置来源（优先级从高到低） |
|--------|--------------------------|
| JDK | `pom.xml` 的 `<java.version>` / `<maven.compiler.source>` / `<release>`；Gradle 的 `sourceCompatibility` / `toolchain`；`.java-version` / `.sdkmanrc` |
| Node.js | `package.json` 的 `engines.node`；`.nvmrc` / `.node-version` |
| Python | `pyproject.toml` 的 `requires-python`；`.python-version`；`runtime.txt` |
| Go | `go.mod` 的 `go <version>` 声明 |
| Rust | `Cargo.toml` 的 `rust-version`；`rust-toolchain.toml` |
| 构建工具（Maven/Gradle/npm/cargo…） | 包装器版本（`mvnw`/`gradlew` 对应的 wrapper properties、`package-lock`/`pnpm-lock` 锁定的版本区间） |

**关键规则**：
- 配置文件**声明**了版本 → 标「已验证」，附路径。
- 配置文件**未声明**（如 package.json 无 `engines`）→ 注明"配置未声明 {运行时} 版本"，**禁止填一个看起来合理的数字**。README 中的版本号可作「推断」线索并列出，标注来源文档。
- 中间件（数据库/缓存/MQ）版本通常不在项目配置里声明，注明"未在配置中声明，需人工确认"，README 版本可作「推断」。

### 第 2 步：依赖安装（必须执行）

从包管理器配置读取依赖安装命令。

| 项目类型 | 安装命令来源 |
|----------|-------------|
| Node.js | `package.json` 存在即用 `npm install`（或 `pnpm install` / `yarn`，看有无 `pnpm-lock.yaml` / `yarn.lock` / `packageManager` 字段）；标「已验证」依据为 package.json 存在 + 锁文件类型 |
| Maven | 无独立安装步骤，依赖在 `mvn` 构建时自动解析；注明"构建时自动拉取，依赖管理在 `{pom 路径}` 的 dependencyManagement" |
| Gradle | 同上，依赖管理在 `build.gradle` 的 dependencies |
| Python | `pip install -r requirements.txt` / `pip install -e .` / `poetry install`（看配置文件类型） |
| Go | `go mod download`（`go.mod` 存在） |
| Rust | `cargo build` 自动拉取（`Cargo.toml`） |

### 第 3 步：开发启动（必须执行）

从配置读取开发态启动命令。

| 项目类型 | 启动命令来源 |
|----------|-------------|
| Node.js / 前端 | `package.json` 的 `scripts.dev` / `scripts.start`（字面量读，不要假定叫 `serve`） |
| Java / Spring Boot | IDE 直跑 `*Application.java` 主类（标「推断」，附启动类路径）；或 `mvn spring-boot:run`（需 pom 有 spring-boot-maven-plugin，标「已验证」）；或打包后 `java -jar` |
| Python (Django) | `manage.py runserver`（看有无 manage.py） |
| Python (Flask/FastAPI) | `flask run` / `uvicorn`（看配置） |
| Go | `go run main.go` / `go run ./cmd/...` |

**关键规则**：前端开发命令必须**字面量**对照 scripts 字段，不要把 `npm run serve` 当默认（很多项目叫 `dev`）。开发代理（Vite proxy / webpack devServer）从配置文件读，标「已验证」附 `vite.config.js` / `vue.config.js` 路径。

### 第 4 步：构建/打包命令 + 产物（必须执行）

从构建配置读取打包命令与产物路径。

| 项目类型 | 构建命令 | 产物 | 依据 |
|----------|----------|------|------|
| 前端（Vite/Webpack） | `npm run build`（字面量读 scripts.build） | `dist/` 或 `build/`（看配置 `build.outDir`） | package.json scripts + 构建工具配置 |
| Maven 多模块 | `mvn clean package [-DskipTests]` | `{module}/target/*.jar`；含 spring-boot-maven-plugin 的模块产 fat-jar | `pom.xml` 的 build/plugins |
| Gradle | `./gradlew build` / `bootJar` | `build/libs/*.jar` | `build.gradle` 的 tasks / plugins |
| Python | `python -m build` / `poetry build` | `dist/*.whl` / `*.tar.gz` | `pyproject.toml` |
| Go | `go build -o {bin}` 或 Makefile target | 可执行二进制 | `Makefile` / `go.mod` |
| Rust | `cargo build --release` | `target/release/{bin}` | `Cargo.toml` |

**关键规则**：
- 命令字面量读配置（scripts 字段、plugin goal、Makefile target），不臆造。
- 产物路径从构建工具默认或配置的 outDir 读；标「已验证」附配置依据。
- 区分**可执行产物**（fat-jar / 二进制 / dist）与**依赖产物**（普通 jar / 库包）——多模块项目里通常只有部分模块产可执行产物，从 `pom.xml` 的 spring-boot-maven-plugin / Gradle 的 application plugin 区分。

### 第 5 步：部署方式（必须执行，逐项探测）

按"部署方式探测清单"**逐项探测**，每项声明发现/未发现。**未发现的形态必须显式注明"未发现 {类型}"**，禁止凭"现代项目都用 Docker"臆造。

| 部署形态 | 探测方式 | 发现时 |
|----------|----------|--------|
| Dockerfile | 项目内 `Dockerfile` / `*.dockerfile` / `docker/` | 标「已验证」，附路径，概述构建阶段（base image、COPY、构建命令、CMD） |
| docker-compose | `docker-compose.yml` / `compose.yaml` / `*.compose.yml` | 标「已验证」，附路径，列服务清单与依赖 |
| Kubernetes | `k8s/` / `deploy/` / `manifests/` / `*.yaml`（含 Deployment/Service） | 标「已验证」，附路径 |
| Makefile 部署 target | `Makefile` 的 deploy/install/push 等 target | 标「已验证」，附 target 名与命令 |
| 裸机/直跑 | 上述都未发现 | 注明"未发现容器化配置（Dockerfile/docker-compose/k8s）"，部署形态为裸机/虚机直跑（标「推断」，说明依据为无可执行产物 + 无容器配置） |
| 静态托管（前端） | 前端构建产物 `dist/` 存在且无后端嵌入 | 标「推断」，说明"前端为纯静态产物，托管方式（Nginx/对象存储/CDN）未在配置中声明，需人工确认" |
| 反向代理配置 | `nginx.conf` / `Caddyfile` / `traefik.yml` | 标「已验证」附路径；**仅从 baseURL/server.port 推断需要反向代理而无配置文件时，标「推断」并说明依据**，不能当事实陈述 |

**关键规则**：部署章节是 baseline 最易臆造的地方。任何"配置文件没写但模型觉得生产应该这么部署"的内容（JVM 参数、守护进程方式、反向代理拓扑、负载均衡），必须标「推断」+ 说明依据，不能与「已验证」的事实混在一起陈述。

### 第 6 步：环境变量/配置项（必须执行）

从**框架配置文件**提取可外置的配置项（数据库、缓存、密钥、端口、第三方凭证等）。

| 项目类型 | 配置来源 |
|----------|----------|
| Spring Boot | `application.yml` / `application.properties` / `application-{profile}.yml`；`${VAR:default}` 占位符即为可外置项 |
| Node.js | `.env` / `.env.example` / `config/` / 框架配置（如 `next.config.js` 的 env） |
| Python | `.env` / `settings.py` / `pyproject.toml` 的 tool 配置 |
| Go | `config.yaml` / 环境变量（看代码或 viper 配置） |
| Docker | `docker-compose.yml` 的 `environment:` / `env_file:` |

**记录要求**：
- 每个可外置配置项记录：**yml 路径 / 环境变量名 / 默认值 / 来源文件**。
- 带 `${VAR}` 占位符的项标「已验证」（配置中明确外置）。
- 写死的值（如端口直接写死而非 `${PORT:default}` 占位符）注明"配置中写死，未做外置"。
- **敏感配置**（密钥、密码、token）带默认值的，提示"生产必须替换"（这是从配置读出的事实，不是顾问建议）。
- 配置文件**不存在**（极简项目）注明"未发现配置外置机制"。

### 第 7 步：CI/CD（必须执行，逐项探测）

按清单探测 CI 配置，**只梳理现状**，未发现时注明"未发现 CI/CD 配置"，**禁止补写建议流水线**。

| CI 系统 | 探测位置 |
|---------|----------|
| GitHub Actions | `.github/workflows/*.yml` |
| GitLab CI | `.gitlab-ci.yml` |
| Jenkins | `Jenkinsfile` / `jenkins/` |
| CircleCI | `.circleci/config.yml` |
| Azure Pipelines | `azure-pipelines.yml` |
| Drone | `.drone.yml` |
| Travis | `.travis.yml` |
| Buddy / 其他 | 按项目实际 |

**发现 CI 配置时**：标「已验证」，概述触发条件（push/PR/tag）、构建步骤、部署步骤、密钥/凭证管理方式（secrets/vault），引用配置文件路径。

**未发现 CI 配置时**：注明"未发现 CI/CD 配置（探测了 .github/workflows、.gitlab-ci.yml、Jenkinsfile 等均无）"。**禁止补写"若要补齐 CI/CD 应该…"的示例 yaml**——那是顾问建议，不是现状梳理。如项目有 CONTRIBUTING.md 描述 PR/分支/版本规范（人工流程），可作「推断」线索注明"有人工协作规范（见 CONTRIBUTING.md），但无自动化流水线"。

## 边界处理

### 纯库项目（无可执行产物 / 无部署）

- 部署章节注明"本项目为库（library），无可执行部署单元，部署章节不适用"。
- 构建/打包章节正常梳理（库也要打包发布：npm publish / mvn deploy / cargo package）。
- 发布流程（如有）从配置读（package.json 的 `publishConfig`、pom.xml 的 `distributionManagement`），标「已验证」。

### 多构建并存

- 每种构建（前端 npm + 后端 Maven + 文档 mkdocs + …）独立成节，按第 0 步扫描结果组织，不因主技术栈漏掉次要构建。

### 极简项目（单文件脚本 / 无构建）

- 注明"项目为单文件脚本/无构建配置，构建打包部署维度降级为记录现有可执行入口"，相关章节标「推断」或"未发现"。

### 配置文件与文档冲突

- 以**配置文件**为准（配置是运行时实际生效的）。文档（README/CLAUDE.md）与配置不一致时，配置标「已验证」，文档版本号作「推断」并注明"与配置不一致，需人工确认"。

## 产出格式

### 05-构建打包部署.md 模板

> 产出格式见 `templates/05-构建打包部署.md`（执行时读取该模板填充，勿自行发明结构）。

## 执行检查清单

执行 pm-build-deploy 时，按以下顺序完成：

1. [ ] 读取 `01-项目概览.md`、`02-技术栈与架构.md` 作为上下文输入
2. [ ] 第 0 步：扫描项目内所有构建配置文件，识别多构建并存形态
3. [ ] 第 1 步：从配置文件提取环境要求（版本号只认配置，README 作推断线索）
4. [ ] 第 2 步：从包管理器配置读取依赖安装命令
5. [ ] 第 3 步：从配置读取开发启动命令（前端字面量对照 scripts）
6. [ ] 第 4 步：从构建配置读取打包命令与产物，区分可执行产物与依赖产物
7. [ ] 第 5 步：部署方式探测清单逐项探测（Dockerfile/compose/k8s/Makefile/静态托管/反向代理），未发现的形态显式注明
8. [ ] 第 6 步：从框架配置提取环境变量/配置项（占位符=已验证外置）
9. [ ] 第 7 步：CI 配置逐项探测，只梳理现状，未发现时注明，禁止补写建议流水线
10. [ ] 每条命令/部署方式/版本号填写【来源】【标注】字段
11. [ ] 处理边界（纯库无部署 / 多构建并存 / 极简项目 / 配置与文档冲突）
12. [ ] 按模板格式写入 `05-构建打包部署.md`
13. [ ] 自检：
    - [ ] 每条命令/部署方式/版本号都有【来源】【标注】？是否有命令没标来源？（不合格）
    - [ ] 「已验证」标注的命令，来源字段是否指向配置文件（而非 README/CLAUDE.md）？
    - [ ] 部署方式是否逐项探测、未发现的形态是否显式注明"未发现"？
    - [ ] 版本号是否只认配置文件？README 版本号是否标为「推断」？
    - [ ] CI/CD 章节是否只梳理现状？有没有补写"建议流水线"？（不合格）
    - [ ] 有没有把推断（JVM 参数、守护进程、反向代理拓扑）当事实陈述？
    - [ ] 抽检 2 条「已验证」命令，对照配置文件确实存在字面量？
