# pm-scan 类型识别规则（按需读取）

> 由 SKILL.md 抽出，识别项目类型时按需加载。

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

