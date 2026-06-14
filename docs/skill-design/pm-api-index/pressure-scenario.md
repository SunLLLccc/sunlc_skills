# pm-api-index 压力场景

## Baseline 失败模式

不加 pm-api-index skill，让模型直接"为 dsp 生成 API 索引"时，预期出现以下 6 类跑偏：

### 失败模式 1：不区分对外 API 与内部 API

模型把 HTTP 路由、RPC 接口、Service 方法、私有工具方法全部混在一起罗列，使用者无法判断"哪些是跨系统可调用的对外契约、哪些是模块内部实现细节"。

**验证方式**：检查产出是否明确区分"对外 API"与"内部 API"两类，且每条 API 都有分类归属。

**GREEN 规则**：SKILL 定义"对外 API vs 内部 API"判定方法（对外 = 跨进程/跨系统的契约入口，如 HTTP 路由 / RPC 服务接口 / CLI 命令 / 事件 handler / 导出函数；内部 = 模块/分层间调用，如 Service 方法 / Repository 方法 / 私有工具），要求产出必须分两区呈现。

### 失败模式 2：缺 `文件:行` 位置信息，无法定位

模型只写 API 路径/签名，不标注它在源码中的精确位置，读者想去验证或修改时找不到代码。

**验证方式**：抽查 2 个 API，检查产出中是否带可定位到代码的 `文件路径:行号`，且该行号在代码中确实指向该 API 声明。

**GREEN 规则**：SKILL 规定每个 API 条目必须含 `位置: {文件路径}:{行号}` 字段，行号指向 API 声明所在行（注解行或方法签名行），执行检查清单明确要求抽检可定位。

### 失败模式 3：平铺罗列，无模块/领域分类

模型按扫描顺序或字母序把所有 API 平铺成一张大表，不按业务模块/领域分组，使用者难以按"我要找用户管理的 API"这种业务维度查找。

**验证方式**：检查产出是否按模块/领域分章节组织（如"用户与权限"、"接口管理"、"数据查询"等），而非单张平铺表。

**GREEN 规则**：SKILL 要求"按模块/领域分类组织（不平铺）"，产出模板以"## {模块/领域}"为二级章节，每个章节下再列该模块的 API。

### 失败模式 4：API 形态识别不全

模型只识别 HTTP 路由（`@RequestMapping`），漏掉其他形态：RPC 服务接口（Dubbo/gRPC 服务声明）、SPI 接口（项目自定义的对外服务契约）、前端 API 调用层（axios 封装）、CLI 命令、事件 handler、导出的库函数等。导致索引覆盖面不全。

**验证方式**：检查产出是否覆盖了项目中实际存在的多种 API 形态（dsp 至少有 HTTP 路由、SPI 解耦接口、前端 API 调用层三类），而非只有 HTTP。

**GREEN 规则**：SKILL 列出"常见 API 形态清单"（HTTP 路由 / RPC 服务接口 / SPI 接口 / 前端调用层 / CLI 命令 / 事件 handler / 导出函数），要求逐项探测、存在的形态都要收录。

### 失败模式 5：无调用关系

模型只列出 API"是什么、在哪"，但不梳理"谁调用谁"——核心 API 的调用方、被调用方不明，使用者无法理解 API 在系统中的角色。

**验证方式**：检查产出中至少核心/对外 API 是否标注了调用关系（调用方 / 被调用方 / 下游）。

**GREEN 规则**：SKILL 要求"调用关系梳理方法"章节，至少为对外 API 和核心 API 标注调用方（如前端调用层 → HTTP 路由 → Service → 数据访问），产出模板含调用关系字段。

### 失败模式 6：API 过多时静默截断

当项目 API 数量很大时（dsp 有数十个 HTTP 端点 + 多个 SPI + 前端调用），模型为了控制输出长度，悄悄只列前 N 个、后面省略，且不告知使用者覆盖率，导致使用者误以为索引是完整的。

**验证方式**：检查产出是否声明了 API 总数、已收录数、覆盖率；若采样，是否明确标注采样策略与覆盖率。

**GREEN 规则**：SKILL 要求"大量 API 采样策略"——超过阈值（如 50 个对外 API）时可采样，但必须标注"总数 / 收录数 / 覆盖率 / 采样策略"，禁止静默截断。

## 测试靶子：dsp 项目

- 路径：`/Users/sunlc/sunlc_work/sunlc_skills/dsp`
- 预期 API 形态（帮助设计 baseline/验证，SKILL 本体不硬编码）：
  - **对外 HTTP 路由**：dsp-admin-service（~17 个 `@RestController`，管理后台 API）、dsp-data-service（数据查询 API `POST /dsp/api/{transno}`）、dsp-offline-service（离线导出）
  - **对外 SPI 接口**：dsp-common 的 `DataQueryService`、`XmlConfigCacheInvalidator`（项目自定义的跨模块对外契约）
  - **内部 API**：dsp-core 的 ~16 个 Service 接口（业务逻辑层）、Mapper 接口（数据访问层）
  - **前端调用层**：dsp-admin-web 的 `src/api/`（axios 封装的 HTTP 调用）
- 预期边界挑战：
  - API 形态多样（4+ 类），baseline 易漏
  - HTTP 端点数较多（90+ 个 `@RequestMapping` 级注解），是"大量 API 采样"边界的真实场景
  - 对外 vs 内部判定：SPI 接口（项目自定义、跨模块对外但非 HTTP）是判定方法的典型考验点

## Baseline 实际跑偏记录

执行环境：dispatch 一个无 skill 约束的 baseline subagent，要求"直接为 dsp 生成 API 索引"，禁止读 skills 目录，禁止读已有的 project-knowledge 产出（避免前置产出污染）。baseline 整体质量较高（继承了前序 task 的注释风格，HTTP 端点逐条带 `文件:行`，按业务域分组），但对照 6 个失败模式仍有清晰命中点。

### 实际跑偏 1：内部 API 缺 `文件:行`（对应失败模式 2，最严重且最普遍）

baseline 对**全部 94 个 HTTP 端点**都精确标注了 `文件:行`（如 `InterfaceAdminController.java:114`），但在第 7 章「Service 层关键接口」中，**14 个内部 Service 接口只给了文件名**（如 `InterfaceInfoService.java`），既无完整路径也无行号。原话：「仅列出每个域的核心接口……实现类在同目录 `impl/` 下」——读者要找 `submitApproval` 方法在哪个文件第几行，得自己进目录翻。

这正是失败模式 2 的典型表现：**对外 API 严格、内部 API 松懈**。SKILL 必须强制"每个 API 条目（不分对外/内部）都含 `位置: {文件路径}:{行号}`"。

**结论**：失败模式 2 命中（内部 API 维度）。GREEN 规则：文件:行 字段是所有 API 条目的硬要求，内部 API 不得例外。

### 实际跑偏 2：对外 vs 内部的边界判定不一致（对应失败模式 1，结构性）

baseline 用了三层临时分类："对外"（外部应用 JWT）/ "内部管理"（运营 Admin-Token）/ "Java 内部 API"（模块间）。看似清晰，但关键问题：**SPI 解耦接口（`DataQueryService`、`XmlConfigCacheInvalidator`）被放进"Java 内部 API"区**，可它们是 dsp-common 定义的**跨模块对外契约**——dsp-data-service/dsp-offline-service 通过这个接口调用 dsp-engine，是项目级的"对外 API"（只是不通过 HTTP）。把跨模块契约和同模块内的 Service 方法混在同一个"内部"区，使用者无法区分"跨模块要遵守的契约"vs"某模块的实现细节"。

**结论**：失败模式 1 部分命中。GREEN 规则：SKILL 必须给"对外 vs 内部"的**判定方法**而非临时分类——对外 = 跨进程/跨模块的契约入口（HTTP/RPC/SPI/CLI/事件/导出函数），内部 = 单模块内的分层调用（Service/Repository/私有工具）。SPI 接口属于对外。

### 实际跑偏 3：API 形态识别是"碰巧做对"而非"系统探测"（对应失败模式 4，隐患）

baseline 报告说"已 grep 确认无 `@DubboService`、无 dubbo 配置；Dubbo 仅作为引擎客户端执行器存在"。这个结论**正确**，但问题是：baseline 是靠自己的临场判断去 grep 的，**没有系统性的形态探测清单**。换一个项目（如有 gRPC 但无 Dubbo），baseline 可能漏掉 gRPC 服务声明；有 CLI 子命令的 Node 项目，baseline 可能漏掉 `bin/` 下的命令。

**结论**：失败模式 4 在 dsp 上未明显跑偏（因 baseline 经验丰富），但**风险真实存在**——缺乏"常见 API 形态清单"导致识别靠运气。GREEN 规则：SKILL 必须给出"API 形态探测清单"（HTTP 路由 / RPC 服务接口 / SPI 接口 / 前端调用层 / CLI 命令 / 事件 handler / 导出函数），逐项探测、存在即收录。

### 实际跑偏 4：无覆盖率声明（对应失败模式 6，轻度）

baseline 第 9 章「没有收录的内容与取舍说明」明确声明了"省略 MyBatis-Plus 继承的标准 CRUD"和"Mapper/Entity 不收"——这是**诚实取舍**，没有静默截断。但 baseline **没有给出覆盖率数字**：收录了 94 个 HTTP + 约 20 个内部入口，那项目总共有多少 API？覆盖率是多少？使用者无法判断"这个索引覆盖了 90% 还是 30%"。

**结论**：失败模式 6 轻度命中（取舍诚实，但缺覆盖率量化）。GREEN 规则：SKILL 要求产出声明"API 总数 / 已收录数 / 覆盖率 / 采样策略（若采样）"，即使是全量收录也要标注"全覆盖"。

### 实际跑偏 5：调用关系标注零散（对应失败模式 5，部分命中）

baseline 在引擎层（§6）和鉴权链路（§5）标注了调用关系（如"`invalidate` 被审批通过/下线/配置导入触发"），这部分做得不错。但**核心 HTTP API 的调用关系普遍缺失**——例如 `POST /dsp/interface/{transno}/approve`（审批通过发布接口），它调用 `InterfaceVersionService` + `XmlConfigCacheInvalidator` + `SqlSecurityValidator`，但条目里只有"鉴权/角色 + 文件:行"，没有"调用下游"字段。对外 API 是调用关系的核心载体，却没被系统标注。

**结论**：失败模式 5 部分命中。GREEN 规则：SKILL 要求至少为"对外 API + 核心内部 API"标注调用关系（调用方/被调用方/下游），产出模板含调用关系字段。

### Baseline 总结

- 明确命中失败模式：2（内部 API 缺文件:行，最严重）、5（调用关系部分缺失）、6（缺覆盖率声明）
- 部分命中失败模式：1（对外/内部边界判定不一致，SPI 错归类）、4（形态识别靠运气非系统）
- 未命中失败模式：3（平铺——baseline 按业务域分组做得好）
- 整体观察：baseline 质量高于预期（前序 task 训练的痕迹），但**一致性不足**——对外 API 严格、内部 API 松懈；调用关系零散而非系统；覆盖率无量化。SKILL 的核心价值在于"强制一致性 + 系统化探测 + 边界判定方法"。
- SKILL 需额外编码的规则：
  1. 文件:行 是所有 API 条目的硬要求（含内部 API）
  2. 对外 vs 内部用判定方法定义（不是临时分类），SPI 属于对外
  3. API 形态探测清单（7 类），逐项探测
  4. 调用关系字段强制（对外 + 核心 API）
  5. 覆盖率声明强制（总数/收录数/覆盖率/采样策略）
