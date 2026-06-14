# pm-build-deploy 分析策略与标注规则（按需读取）

> 由 SKILL.md 抽出，执行 8 步梳理时按需加载。

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

