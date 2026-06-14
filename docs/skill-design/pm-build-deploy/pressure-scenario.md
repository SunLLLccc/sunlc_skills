# pm-build-deploy 压力场景

## Baseline 失败模式

不加 pm-build-deploy skill，让模型直接"梳理 dsp 的构建打包部署流程"时，预期出现以下 7 类跑偏：

### 失败模式 1：臆造构建/启动命令，不从配置文件实际读取

模型凭借对"Spring Boot 项目一般怎么跑"的印象，直接写出 `mvn spring-boot:run`、`java -jar dsp-admin-service.jar`、`npm run serve` 等命令，而不去打开 `package.json` 的 `scripts` 字段、`pom.xml` 的 `spring-boot-maven-plugin` 配置确认项目**实际声明的**命令。结果写出项目里根本不存在的 script（如 `serve` 实际叫 `dev`），或漏掉项目自定义的打包命令。

**验证方式**：抽检产出中标注为「已验证」的 2 条命令，对照 dsp 的 `package.json` / `pom.xml`，确认命令字面量在配置文件中确实存在；检查是否有「推断」标注用于配置文件中找不到的命令。

**GREEN 规则**：SKILL 规定"核心原则：命令/部署方式必须从配置文件实际读取"——明确列出每个命令必须来自哪类配置文件（`package.json` 的 `scripts` 字段、`pom.xml` 的 plugin 配置、`Makefile` 的 target、`Dockerfile` 的指令等），且产出中每条命令必须标注「已验证」（配置中找到）/「推断」（未直接找到，需人工确认），禁止把臆造命令当事实陈述。

### 失败模式 2：臆造部署方式（Docker/K8s/云平台）

模型假定"现代项目都用 Docker 部署"，凭空写"使用 Dockerfile 构建 + K8s 部署 + Nginx 反向代理"，但项目实际上**根本没有** Dockerfile、k8s manifest 或 nginx 配置。或者反过来——项目有 `docker-compose.yml` 但模型没探测到，遗漏了容器化部署方式。

**验证方式**：检查产出中"部署方式"章节是否如实反映项目实际的容器化/裸机/静态托管状态；对 dsp 这种**无 Dockerfile/无 CI** 的项目，正确做法是注明"未发现容器化配置（Dockerfile/docker-compose）"和"未发现 CI/CD 配置"，而不是臆造一套部署流水线。

**GREEN 规则**：SKILL 要求"部署方式探测清单"——逐项探测 Dockerfile / docker-compose / k8s manifest / Makefile / 静态托管产物目录 / CI 配置（.github/workflows、.gitlab-ci.yml、Jenkinsfile），**未发现的形态必须显式注明"未发现"**，禁止凭"项目类型印象"臆造部署方式。

### 失败模式 3：忽略环境要求（运行时版本）

模型直接跳过"这个项目需要什么版本的 JDK / Node / Maven / 数据库"这一节，或泛泛写"需要 Java 8+"而不去 `pom.xml` 的 `<java.version>`、`package.json` 的 `engines` 字段、`.nvmrc` / `.java-version` 等配置中确认项目**实际声明**的版本要求。

**验证方式**：检查产出"环境要求"章节是否给出了从配置文件读取的版本号（如 `<java.version>1.8</java.version>`），而非泛泛的"建议使用较新版本"。

**GREEN 规则**：SKILL 规定"环境要求"必须从配置文件读取（Java 从 pom.xml 的 `<java.version>` / `maven.compiler.source`；Node 从 package.json 的 `engines` / `.nvmrc`；Python 从 `pyproject.toml` 的 `requires-python` / `.python-version`；构建工具版本从 `pom.xml` 的 parent 版本、`package.json` 的 devDependencies 中的构建工具版本等），版本号标注来源，不臆造。

### 失败模式 4：CI/CD 漏掉或臆造

模型要么完全跳过 CI/CD 这一节（即使项目有 `.github/workflows`），要么反过来——项目根本没有 CI 配置，模型却凭印象写"通过 GitHub Actions 自动构建部署"。

**验证方式**：检查产出是否明确探测了 CI/CD 配置（.github/workflows/*.yml、.gitlab-ci.yml、Jenkinsfile、.circleci/config.yml、azure-pipelines.yml），并对 dsp 这种无 CI 的项目如实注明"未发现 CI/CD 配置"。

**GREEN 规则**：SKILL 要求 CI/CD 作为 7 类分析之一独立成节，必须探测常见 CI 配置位置，探测结果（发现/未发现）显式声明，不臆造流水线。

### 失败模式 5：不标「已验证/推断」，事实与猜测混在一起

模型把"package.json 里写死的 `vite build`"（事实）和"生产环境大概用 Nginx 托管 dist/"（猜测）混在同一个清单里，不加任何区分。读者无法判断哪些可以直接照做、哪些需要人工确认。

**验证方式**：检查产出中每条命令/部署方式是否带「已验证」或「推断」标注；抽检 2 条「已验证」标注的命令确实能在配置文件中找到原文。

**GREEN 规则**：SKILL 规定每条命令/部署方式必须标注「已验证」（配置文件中直接找到，附文件路径）/「推断」（未直接找到，需人工确认，必须说明推断依据）两态之一，产出模板的字段含此标注。

### 失败模式 6：版本号臆造

模型写出 `JDK 17`、`Node 18`、`Maven 3.9` 等具体版本号，但这些数字并非来自项目配置，而是模型的训练数据默认值或"最新稳定版"猜测。实际项目可能用 JDK 1.8、Node 16。

**验证方式**：抽检产出中的版本号（JDK/Node/Maven/构建工具），对照 dsp 的 pom.xml（`<java.version>1.8</java.version>`、parent 版本）、package.json（vite 版本等），确认版本号来自配置而非臆造。

**GREEN 规则**：SKILL 规定版本号必须从配置文件提取，不猜测；配置文件中找不到具体版本号时，标注"未在配置中声明，需人工确认"而非填一个看起来合理的数字。

### 失败模式 7：多构建并存时只识别一种

项目可能同时有多种构建方式（前端 npm + 后端 Maven + 文档 mkdocs + 子模块 gradle）。模型只识别主技术栈的构建（如 Java 项目的 Maven），漏掉前端的 npm、Python 脚手的 pip、文档站点的构建。dsp 正是这种多形态：前端 npm/Vite + 后端 Maven 多模块，baseline 易只写一种。

**验证方式**：检查产出是否覆盖了项目实际存在的所有构建形态（dsp 应同时覆盖前端 npm/Vite 与后端 Maven 多模块），而非只写主技术栈。

**GREEN 规则**：SKILL 要求"多构建并存识别"——扫描项目内**所有**构建配置文件（多模块项目的每个子模块 pom/package.json、monorepo 的每个 workspace），每种构建独立成节，不因"主技术栈"而漏掉次要构建。

## 测试靶子：dsp 项目

- 路径：`/Users/sunlc/sunlc_work/sunlc_skills/dsp`
- 预期构建/部署形态（帮助设计 baseline/验证，SKILL 本体不硬编码）：
  - **环境要求**：JDK 1.8（pom.xml `<java.version>1.8</java.version>`）；Node 版本未在 package.json `engines` 声明（需注明"未声明"）；Maven 版本由 parent pom 隐含
  - **依赖安装**：前端 `npm install`（dsp-admin-web）；后端 Maven 自动解析依赖
  - **开发启动**：前端 `npm run dev`（= `vite`）；后端各服务 `java -jar` 或 IDE 启动 Application 主类
  - **构建/打包**：前端 `npm run build`（= `vite build`，产物 dist/）；后端 `mvn package` + spring-boot-maven-plugin 打 fat jar（dsp-data-service / dsp-offline-service / dsp-admin-service 三个可执行模块）
  - **部署方式**：**未发现** Dockerfile / docker-compose / k8s manifest / Makefile（典型"未发现"边界场景）；前端静态托管（dist/ 交由 Web 服务器），后端 `java -jar` 独立启动
  - **环境变量/配置项**：各服务 `src/main/resources/application.yml`（数据库、Dubbo 注册中心、端口等），无 `.env` 文件
  - **CI/CD**：**未发现** .github/workflows / .gitlab-ci.yml / Jenkinsfile（典型"未发现"边界场景）
- 预期边界挑战：
  - **无容器化 + 无 CI**：dsp 是"裸机部署、手工构建"的典型，baseline 易凭印象臆造 Docker/CI 流水线（失败模式 2、4 的真实场景）
  - **多构建并存**：前端 npm/Vite + 后端 Maven 多模块，baseline 易只写后端漏前端（失败模式 7）
  - **版本声明不完整**：JDK 在 pom.xml 有声明，Node 版本未声明，是"版本号从配置读 vs 臆造"的典型考验（失败模式 3、6）

## Baseline 实际跑偏记录

执行环境：dispatch 一个无 skill 约束的 baseline subagent，要求"直接梳理 dsp 的构建打包部署流程，不要参考任何 skill，不要读已有的 project-knowledge 产出"。baseline 整体质量较高（命令大多来自 package.json/pom.xml，覆盖前后端双构建，正确探测到无 Docker/无 CI），但对照 7 个失败模式仍有清晰命中点。

### 实际跑偏 1：全文档无「已验证/推断」标注（对应失败模式 5，最严重且最普遍）

baseline 全程**没有出现任何一处「已验证」或「推断」字样**。结果：事实（`npm run build` = `vite build`，来自 package.json）与推断（"反向代理把 /dsp/admin→8082"）混在同一份文档里，读者无法区分"哪些可以直接照做、哪些是模型脑补需人工确认"。例如部署章节里"java -jar -Xms512m -Xmx2g -DDSP_JWT_SECRET=..."这条命令，JVM 参数和 -D 注入是推断（仓库无启动脚本规定），但和"mvn clean package"这种事实命令并列陈述，毫无区分。

**结论**：失败模式 5 命中（最严重）。GREEN 规则：SKILL 必须强制每条命令/部署方式/版本号标注「已验证」（配置文件中直接找到，附文件路径）或「推断」（未直接找到，需人工确认 + 说明推断依据），产出模板字段含此标注，执行检查清单要求抽检。

### 实际跑偏 2：臆造 Nginx 反向代理部署拓扑（对应失败模式 2，结构性）

baseline 正确探测到仓库**无 Dockerfile / 无 docker-compose / 无 k8s manifest**（这点做得好，没有臆造容器化），但在部署章节画了一张"反向代理 (Nginx) 把 /dsp/admin→8082、/dsp/offline→8081、/dsp/api→8080"的拓扑图。问题：**仓库内没有任何 nginx 配置文件**，这张拓扑是从前端 axios `baseURL: /dsp/admin`（相对路径）+ 三个服务分端口的事实**推断**出来的。更糟的是，这个推断**没有被标注为推断**，而是作为"部署方式"章节的事实陈述呈现。读者会误以为项目就是这样部署的。

**结论**：失败模式 2 命中（部署方式维度）。GREEN 规则：SKILL 要求"部署方式探测清单"逐项探测（Dockerfile / docker-compose / k8s / Makefile / 静态托管 / 反向代理配置），**未发现的形态必须显式注明"未发现"**；推断出的部署形态（如"从 baseURL 推断需要反向代理"）必须标注「推断」并说明依据，不能当事实陈述。

### 实际跑偏 3：版本号来源不严格，README 当配置（对应失败模式 6，部分命中）

baseline 的 JDK 版本（`1.8`）正确来自 `pom.xml` 的 `<java.version>`，这点合格。但其他版本号——`Maven 3.6+`、`Node.js 16+`、`MySQL 5.7+`、`Redis 5.0+`、`MongoDB 4.0+`——全部**来自 README.md 的"环境要求"小节**，而非配置文件。问题有二：
1. README 是文档不是配置文件，其版本号本身是否经过验证未知（README 可能过时或写错）。
2. `package.json` **没有 `engines` 字段**，Node 版本在配置层面是"未声明"，但 baseline 写"Node.js 16+"当事实，掩盖了"配置未声明 Node 版本"这一真相。

**结论**：失败模式 6 部分命中。GREEN 规则：SKILL 规定版本号必须从**配置文件**提取（pom.xml 的 java.version、package.json 的 engines、.nvmrc 等），README/CLAUDE.md 等文档中的版本号只能作为「推断」线索并标注来源；配置文件中找不到具体版本号时，标注"未在配置中声明，需人工确认"，禁止填一个看起来合理的数字或直接抄 README。

### 实际跑偏 4：CI/CD 章节写"建议补齐"的示例流水线（对应失败模式 4，轻度）

baseline 正确探测到仓库无 CI 配置（无 .github/workflows、无 Jenkinsfile、无 .gitlab-ci.yml），这点合格。但它在 CI/CD 章节写了一段**"若要补齐 CI/CD，基于现有构建命令的标准做法"**的 GitHub Actions 示例 yaml。虽然开头声明了"仓库当前未配置，此为推荐形态"，但这种"建议补齐"内容超出"梳理现状"的职责——它是顾问建议而非现状梳理。读者（尤其后续维护者）容易把这段示例误读为既有配置，或误以为"梳理 skill 应该给部署建议"。

**结论**：失败模式 4 轻度命中（探测正确，但越界给建议）。GREEN 规则：SKILL 规定 CI/CD 章节**只梳理现状**——探测到的配置如实描述（流水线触发条件、构建步骤、部署步骤、密钥管理方式）；**未发现 CI/CD 时显式注明"未发现"**，禁止补写"建议流水线"（那是另一个 skill 的职责，不是梳理 skill 的产出）。

### Baseline 总结

- 明确命中失败模式：5（全文档无已验证/推断标注，最严重）、2（臆造 Nginx 反向代理拓扑，未标注推断）
- 部分命中失败模式：6（版本号抄 README 当配置、Node 版本当事实）、4（探测正确但越界给 CI 建议）
- 未命中失败模式：1（命令大多来自配置）、3（JDK 版本读对了）、7（前后端双构建都覆盖了）
- 整体观察：baseline 质量高于预期（前序 task 训练痕迹明显，命令绝大多数有配置依据，无容器化/无 CI 的边界处理基本正确），但**事实与推断不分**是系统性问题——部署拓扑、JVM 参数、版本号、CI 建议，凡是"配置文件没写但模型觉得应该是这样"的内容，全部和事实混在一起陈述，无一标注。SKILL 的核心价值在于"强制每条命令/部署方式/版本号标注来源（已验证/推断）+ 部署方式探测清单逐项声明（含未发现）+ 版本号只认配置文件 + 现状梳理不越界给建议"。
- SKILL 需额外编码的规则：
  1. 「已验证/推断」是每条命令/部署方式/版本号的硬要求（附文件路径）
  2. 部署方式探测清单（6 类），逐项声明发现/未发现，未发现的形态显式注明"未发现"
  3. 版本号必须来自配置文件，README/文档版本号只能作为「推断」线索
  4. CI/CD 章节只梳理现状，未发现时注明"未发现"，禁止补写建议流水线
  5. 多构建并存识别：扫描所有构建配置文件，每种独立成节
