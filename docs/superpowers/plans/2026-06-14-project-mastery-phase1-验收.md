# project-mastery 期 1 端到端验收记录

> 日期：2026-06-14
> 验收靶子：`dsp`（全栈：dsp-admin-web 前端 + dsp-parent 后端 Maven 多模块 Spring Boot）
> 分支：`phase1-learning-pipeline`

---

## 1. 期 1 范围与交付物

期 1 目标：交付**学习管线核心**——顶层编排 + 7 个子 skill，对任意项目端到端产出知识库。

### 1.1 skill 交付清单

| Task | Skill | 状态 | Commit |
|------|-------|------|--------|
| 1 | pm-scan（扫描 + 多维类型识别 / 路由器） | ✅ 建成 + review APPROVED | `7ed0977` |
| 2 | pm-techstack-generic（通用技术栈 + 自封装框架识别） | ✅ 建成 + review APPROVED | `8b23c44` |
| 3 | pm-conventions（从代码推断开发规范） | ✅ 建成 + review APPROVED | `0a5faee` |
| 4 | pm-api-index（按模块分类、区分内外的 API 索引） | ✅ 建成 + review APPROVED | `763f764` |
| 5 | pm-build-deploy（从配置验证的构建部署） | ✅ 建成 + review APPROVED | `5b0114d` |
| 6 | pm-kb-index（总索引 + 任务型阅读路径） | ✅ 建成 + review APPROVED + Minor 修复 | `53b8140` / `1ffc077` |
| 7 | pm-verify（抽样校验，只报告不改） | ✅ 建成 + review APPROVED | `333cb78` |
| 8 | project-mastery（顶层编排 + 学习子流程串联） | ✅ 建成 + review APPROVED | `a7c3d88` |

**每个 skill 均经两阶段 review（规范符合性 → 质量），全部 APPROVED。**

### 1.2 通用化（用户最高优先级要求）

`skills/*/SKILL.md` **全部 100% 通用，零 dsp / 零项目专有内容**。TDD 压力场景统一迁至 `docs/skill-design/<skill>/pressure-scenario.md`（设计笔记 + 测试证据，不随可复用 skill 发布）。

验证：`grep -rni "dsp" skills/*/SKILL.md` → 0 命中（含端口 8080/8081/8082 等隐性词，均 0）。

---

## 2. 端到端实跑结果（Task 8 GREEN，作为本验收基线）

清空 `dsp/docs/project-knowledge/` 后，由编排 subagent 严格遵循 `project-mastery` SKILL.md 执行完整【学习】子流程。

### 2.1 编排正确性

| 验收项 | 结果 |
|--------|------|
| 入口判定正确走【学习】（KB 已清空） | ✅ |
| 波次严格 1→2→3→4→收尾顺序 | ✅ 无乱序无漏波 |
| 波次 2 的 4 个分析 subagent **真并行**（同一轮 dispatch） | ✅（pm-conventions subagent 自述执行时 02 尚未写完，证明并行非串行） |
| 波次 3 pm-kb-index 由主会话执行 | ✅ |
| 波次 4 pm-verify dispatch | ✅ |
| 收尾 `_meta/manifest.json` 由主会话写 | ✅ |

### 2.2 知识库完整性

`dsp/docs/project-knowledge/` 产出 **9 项齐全**：

```
01-项目概览.md      02-技术栈与架构.md   03-开发规范.md
04-API索引.md       05-构建打包部署.md   06-校验报告.md
README.md
_meta/manifest.json   _meta/project-type.json
```

- `manifest.json` / `project-type.json` 均 JSON 合法（`python3 -m json.tool` 校验通过）。
- `manifest.json`：subprocess=learning、generatedAt=2026-06-14T11:48:21Z、sourceCommit=333cb78（宿主仓库 HEAD，dsp 无独立 .git 已注明）、7 kbDocs + 7 skillVersions 齐全。
- `project-type.json`：primaryType=fullstack、confidence=0.98。

### 2.3 抽样质量复核（人工）

| 文档 | 抽检点 | 结果 |
|------|--------|------|
| 02-技术栈与架构 | 是否识别自封装框架 | ✅ 识别出 dsp-engine XML 执行引擎（核心）+ 3 个轻量自封装层，四步法特征完整 |
| 03-开发规范 | 规范是否与代码一致（非臆造） | ✅ 每条规范附证据 + 置信度，抽检 ServiceImpl/ErrorCode/style.css 均成立 |
| 04-API索引 | API `文件:行` 是否可定位 | ✅ 抽检 `DataApiController.java:31` 实为 `@PostMapping("/{transno}")`，行号精确 |
| 05-构建部署 | 构建命令是否在配置中存在 | ✅ `npm run dev`/`npm run build` 在 package.json scripts；spring-boot-maven-plugin 在 pom.xml |
| 06-校验报告 | 是否报出待确认项 / 说明抽样范围 | ✅ 抽样 38 条，报出 4 条不一致 + 4 条无法核对，含抽样范围声明 |

### 2.4 pm-verify 报告的不一致项（verificationStatus = partial）

pm-verify 抽样 38 条：**一致 30 / 不一致 4 / 无法核对 4**。3 个问题点（N1/N2 各跨 2 文档重复计数）：

| 编号 | 级别 | 问题 | 处置 |
|------|------|------|------|
| N1 | 中等 | ErrorCode 枚举数：02 与 03 均称"36 项"，实际 `ErrorCode.java:13-36` 仅 23 项 | 期 2 改进（见 §3） |
| N2 | 中等 | HTTP 路由数：04 与 README 称"86 个（admin 81）"，实际 admin-service 88 个（总计 93）；且 04 文档**表内表外不自洽**（详表 88 行 vs 摘要 81） | 期 2 改进（见 §3） |
| N3 | 轻微 | microservices 类型标签与实际 RPC 形态张力（项目零 `@DubboService`，Dubbo 仅作引擎消费侧） | 判定为标注偏差非实质错误；README/02/04 已多处显式标注缓解 |

**根因**：N1/N2 是波次 2 并行 subagent **各自独立估算同一计数**时的漂移——印证了 project-mastery SKILL.md 预警的并行依赖风险。pm-verify 如实捕获、未修改任何 KB 文档（只报告不改原则生效）。

---

## 3. 已知问题与推迟项（期 2+ 处理）

| 项 | 归属 | 说明 |
|----|------|------|
| **并行计数漂移对账** | 期 2 | 波次 2 并行 subagent 独立估算同一数字（ErrorCode/路由数）会漂移。期 2 拟在波次 2 后加"计数对账"步骤（主会话汇总关键计数，冲突时 dispatch 复核），或调整波次 2 内部依赖（02 串行先行，03/04/05 并行）。当前由 pm-verify 兜底捕获，闭环未破。 |
| **M1 dispatch B/C/D 一致性** | 期 1 收尾（可选） | project-mastery 波次 2 dispatch C/D 对 02 上下文的兜底说明与 dispatch B 不一致；已被统一"波次 2 内部依赖说明"段落覆盖，风险低，可推迟。 |
| **【更新】子流程** | 期 2 | pm-update：git diff + 变更→文档影响映射 + 增量重跑。当前为 stub。 |
| **【开发】子流程** | 期 3 | pm-dev：需求细化 + 注入 KB + 串联 superpowers（brainstorming/writing-plans/TDD/verification）。当前为 stub。 |
| **预定义 agents（方式 B）** | 期 4 | 给关键步骤配专属 agent 收紧权限（build-deploy 的 Bash、verify 的只读等）。当前用方式 A 按需 dispatch 兜底。 |
| **路由器特化** | 期 2 | pm-techstack-frontend/backend/fullstack（router 分支）。期 1 用 pm-techstack-generic 通用兜底，所有类型可跑。 |

---

## 4. 期 1 验收结论

**通过**。期 1 范围（学习管线核心：顶层编排 + 7 子 skill）全部建成、经两阶段 review APPROVED、对 dsp 全栈项目端到端实跑产出完整知识库。通用化要求（零 dsp）严格达标。pm-verify 暴露的计数漂移属已知并行 trade-off，由校验机制兜底，推迟期 2 优化，不影响期 1 交付。

**子项目 A（开发导向）期 1 完成**，可进入期 2（路由器特化 + 更新子流程）。
