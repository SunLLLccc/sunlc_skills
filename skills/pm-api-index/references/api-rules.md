# pm-api-index API 收录与调用关系规则（按需读取）

> 由 pm-api-index SKILL.md 抽出，执行时按需加载。


## 对外 vs 内部判定

## 对外 vs 内部判定方法

**判定标准**（按 API 的**契约边界**判定，不按传输协议）：

- **对外 API** = 跨进程 / 跨模块的**契约入口**，是项目承诺给外部或其它模块的调用接口。改它意味着破坏契约。
  - HTTP 路由（Spring 的 `@RestController`/`@RequestMapping`、Express/Fastify 路由、Flask/Django view、ASP.NET Controller 等）
  - RPC 服务接口（Dubbo `@DubboService`、gRPC `*ServiceImpl`、Thrift service、Spring `@FeignClient` 提供方等）
  - **SPI 接口 / 项目自定义的跨模块服务契约**（一个模块定义接口、另一个模块实现/调用，用于解耦）—— **SPI 属于对外，不是内部**
  - CLI 命令（`package.json` 的 `bin`、cobra/clap/argparse 注册的子命令等）
  - 事件 handler / 消息消费者（Kafka/RabbitMQ/RocketMQ listener、Spring `@EventListener`/`@KafkaListener`、NestJS `@EventPattern` 等对外部消息的入口）
  - 导出函数（library 的 `index.js`/`__init__.py`/`mod.rs`/`lib.rs` 对外暴露的公共 API、package 的 `main`/`exports` 字段指向的入口）

- **内部 API** = **单模块内**的分层调用，是实现细节而非契约。改它通常不影响外部。
  - Service 层方法（业务逻辑，模块内 Controller → Service）
  - Repository / DAO / Mapper 方法（数据访问层，Service → DAO）
  - 私有/包级工具方法、内部 helper、private 函数
  - 框架继承的标准方法（如 MyBatis-Plus `BaseMapper`/`ServiceImpl` 的 `save`/`getById`/`list`、JPA `JpaRepository` 的默认方法）—— 这类**可省略不收**，除非项目有自定义覆写

**边界模糊时的判定**（优先级从高到低，命中即定）：

1. **跨模块优先**：当一条 API 既被同模块调用又被**跨模块**调用时（典型：单仓多模块中一个模块的 Service 接口被另一个 Maven/npm/go 模块 import 注入），**只要存在跨模块调用方，就判为对外**——它承担跨模块契约职责。即使它同时也是模块内分层的一部分。
2. **框架继承方法不算对外**：MyBatis-Plus `BaseMapper`/`ServiceImpl`、JPA `JpaRepository`、EF Core `DbContext` 的默认方法不是项目自封装的契约，**可省略不收**（除非有自定义覆写）。
3. **私有/包级不算对外**：`private`/包级可见的方法/函数默认是内部，除非被反射/动态调用对外暴露（罕见）。

## API 形态探测清单（必须逐项执行）

不同项目 API 形态差异巨大。**开工时必须逐项探测下述 7 类形态**，存在的都要收录，不存在的注明"未发现"。禁止只识别 HTTP 而漏掉其他。

| 序 | API 形态 | 探测方式（通用指引，按项目实际技术栈调整关键词） |
|----|----------|------------------------------------------------|
| 1 | HTTP 路由 | 搜索 Web 框架路由注解/装饰器：Spring `@*Mapping`/`@RestController`、JS `router.get/post`、Python `@app.route`/`@*Api_view`、.NET `[Http*]` |
| 2 | RPC 服务接口 | 搜索 RPC 框架服务声明：Dubbo `@DubboService`/`@Service`(dubbo)、gRPC `*ServiceImpl` + `.proto`、Thrift、`@FeignClient` |
| 3 | SPI / 跨模块服务接口 | 从 `02-技术栈与架构.md` 的自封装框架清单找"解耦接口"；搜索项目内跨模块 import 的 interface/trait/protocol 定义 |
| 4 | 前端调用层 | 前端项目的 `api/`/`services/`/`request` 目录；axios/fetch 封装；rpc-client 生成代码 |
| 5 | CLI 命令 | `package.json` 的 `bin`、`setup.py`/`pyproject.toml` 的 `entry_points`/`[project.scripts]`、cobra/clap 注册的命令 |
| 6 | 事件 handler / 消息消费者 / 定时触发器 | 搜索消息监听注解：`@KafkaListener`/`@RabbitListener`/`@RocketMQMessageListener`/`@EventListener`/`@EventPattern`/`@Consumer`；定时任务入口：Spring `@Scheduled`、Quartz Job、cron 配置、Node `node-cron`/`setInterval` 调度的入口 |
| 7 | 导出函数（library） | library 的入口文件：`index.{js,ts}`、`__init__.py`、`mod.rs`/`lib.rs`、`package.json` 的 `main`/`exports`、go 的 `package` 导出标识符（仅 library 项目适用，application/web 服务项目注明"不适用"） |

**探测纪律**：
- 每类形态搜索后，记录"发现 N 个 / 未发现"，写入产出的"形态覆盖声明"。
- **禁止**只探测项目主技术栈而漏次形态（如 Spring 项目也可能有事件 handler、有 CLI 启动命令）。

## 调用关系梳理方法

调用关系回答"这个 API 在系统中扮演什么角色"。梳理方法：

1. **对外 API**：必标"调用方"（谁触发这个 API）与"下游"（它调用哪些内部 API / 外部资源）。
   - HTTP 路由：调用方通常是前端调用层 / 外部应用 / 定时任务；下游是注入的 Service。
   - RPC/SPI 接口：调用方是消费者模块；下游是实现类依赖。
   - CLI/事件 handler：调用方是触发源（用户/消息/调度）；下游是业务逻辑。
2. **核心内部 API**（核心 Service / 引擎门面 / 自封装框架入口）：标"被调用方"（哪些对外 API 或其它内部 API 调用它）。
3. **梳理手段**：
   - 静态：grep 该 API 方法名/路径的调用点；import/依赖关系。
   - 利用 `02-技术栈与架构.md` 的模块依赖图作为宏观参照。
4. **不必逐条标全**：非核心的 CRUD 内部方法、私有 helper 可不标调用关系，但**对外 API 必须全标**。

## 大量 API 的采样与覆盖率声明（禁止静默截断）

当 API 数量很大时（经验阈值：对外 API ≥ 50 个，或总 API ≥ 100 个），允许采样收录，但必须满足：

1. **声明覆盖率**：产出开头声明"API 总数 / 已收录数 / 覆盖率 / 采样策略"四项。即使是全量收录，也要注明"全覆盖（共 N 个）"。
2. **采样策略透明**：若采样，必须说明采了什么、漏了什么。典型策略：
   - 按模块采样（每个模块收录代表性 API，其余列计数）
   - 按重要性采样（对外 API 全收、内部 API 只收核心）
   - 省略框架继承方法（如 MyBatis-Plus/JPA 的标准 CRUD）—— 必须注明"省略了 X 类继承方法，共约 Y 个"
3. **禁止静默截断**：不得为了控制输出长度而悄悄只列前 N 个、后面不说明。



## 分析策略

## 分析策略

### 第 1 步：加载上下文与形态探测（必须执行）

1. 读 `01-项目概览.md`、`02-技术栈与架构.md`，获取项目类型、目录结构、技术栈、自封装框架位置（SPI 接口通常在这里）。
2. 按"API 形态探测清单"逐项 grep/搜索，记录每类形态的发现情况。

### 第 2 步：逐形态收录 API（必须执行）

对每类存在的形态，提取 API 条目，每条至少包含：
- **标识**：HTTP 方法+路径 / 方法签名 / 命令名
- **用途**：一句话说明
- **归属**：对外 / 内部（按判定方法）
- **位置**：`{文件路径}:{行号}`
- **调用关系**：对外 API 与核心 API 必填（调用方 / 下游）

### 第 3 步：按模块/领域分类（必须执行）

把所有 API **按模块/领域分组**（不平铺）。分组维度优先级：
1. **按部署服务/可独立运行的子系统**（微服务项目：每个服务一章）
2. **按业务领域**（用户管理 / 接口管理 / 数据查询 等）
3. **按 API 形态**（HTTP / RPC / SPI / 前端调用 / CLI）作为顶层分组—— 仅当项目只有单一形态或形态差异是主要维度时

每个模块/领域章节内，对外 API 排前，内部 API 排后。

### 第 4 步：调用关系梳理（必须执行）

按"调用关系梳理方法"为对外 API 全量标注、为核心内部 API 标注。

### 第 5 步：覆盖率声明与边界检查（必须执行）

声明覆盖率；处理无 API 层 / 过多 API / 形态缺失等边界。


