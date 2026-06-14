# P0 地基（扫描缓存契约 + pm 断点续跑）验收记录

> 对应计划：`docs/superpowers/plans/2026-06-14-p0-scan-cache-foundation.md`
> 范围：`claude优化清单.md` 的 **P2-1 + P0-1 + P0-4**（地基切片）
> 测试靶子：dsp（gitignored，仅验证用）
> 验收日期：2026-06-14

## 1. 任务 GREEN 状态

| Task | 内容 | 状态 | commit |
|---|---|---|---|
| 1 | link-skills.sh 去硬编码（P2-1） | ✅ GREEN | 31a697b |
| 2 | scan-result.json JSON Schema（P0-1 契约 + P1-3 三态） | ✅ GREEN | 8727abe |
| 3 | pm-scan 产 scan-result.json + 退役 project-type.json | ✅ GREEN | 678fdc1 |
| 4 | pm-techstack-generic Step 0 读缓存 | ✅ GREEN | 06a36db |
| 5 | project-mastery 读 scan-result + progress.json | ✅ GREEN（并入 e2e） | a1dafe4 |
| 6 | 端到端验收 | ✅ GREEN | （本文 + 6314883）|

> Task 5 的 GREEN 验证（编排器新逻辑）并入 Task 6 端到端跑——编排器的验证即 e2e，跑两遍是浪费。

## 2. 扫描缓存契约（P0-1）验证证据

- **schema**：`schemas/codebase-scan-result.schema.json`，JSON 合法，三态枚举 confirmed/inferred/uncertain、scanner、classifications[].is_primary、evidence_list 字段就位。
- **生产端**（pm-scan v2）：dsp 上产出 `.codebase/scan-result.json`，程序化校验——12 required 字段齐全；5 classifications（恰好 1 个 is_primary=fullstack）；19 technologies / 11 commands / 8 modules / 4 entrypoints 全带 evidence（72 条 path 经 os.path.exists 验证全真实）；confidence 全三态枚举。
- **消费端**（pm-techstack-generic）：dsp 上 Step 0 读 scan-result.json，02 文档顶部"基础技术栈清单复用自 .codebase/scan-result.json"，19 顶层框架带 † 标记与缓存一致、无冲突，识别 5 个自封装框架（dsp-engine / 公共报文层 / SPI 接口层 / 安全工具层 / 鉴权审计套件）。
- **闭环成立**：pm-scan 生产 → pm-techstack 消费复用，扫描缓存契约端到端跑通。

## 3. project-type.json 退役（全 skill 收尾）

退役 `_meta/project-type.json`（半成品契约），其内容被 scan-result.json 的 classifications 取代。

- **生产端**：pm-scan 不再产 project-type.json；执行时若发现旧版残留则删除（本工具集退役产物，非用户内容）。
- **消费者全改读 scan-result.json**：
  - pm-techstack-generic（Step 0，Task 4）
  - project-mastery（波次 2 路由 + manifest 收尾，Task 5）
  - pm-kb-index（元信息章节 9 处，e2e 发现）
  - pm-verify（校验输入 + 表行 2 处，e2e 发现）
  - learn-project（step 0 复用描述，e2e 发现）
- **复 grep 确认**：全 skill 源码 0 活跃 project-type.json 引用，仅剩"已退役/取代/不再产/不再依赖"说明性文字。

> **e2e 发现的遗漏**：退役时计划只覆盖了 pm-scan/pm-techstack/project-mastery，端到端跑暴露 pm-kb-index/pm-verify/learn-project 三个消费者仍引用 project-type.json，已一并修复（commit 6314883）。教训：退役一个契约时必须 grep 全部消费者，不能只改计划点名的 skill。

## 4. 三态置信度（P1-3）

scan-result.json 机器字段用英文枚举 `confirmed`/`inferred`/`uncertain`；人类文档（01-项目概览.md）用中文标签"已确认/推断得出/不确定"。pm-scan 现已退役旧的 0-1 浮点 + high/medium/low 模型。

## 5. progress.json 断点续跑（P0-4）

- `_meta/progress.json`（在飞行态，每 phase 更新 status）与 `_meta/manifest.json`（完成态记录，收尾一次性写）并列，职责区分清晰。
- e2e：dsp 全新【学习】，progress.json 全程维护，7 phase（scan/techstack/conventions/api-index/build-deploy/kb-index/verify）全部 done + output。
- 重跑逻辑：开工先读 progress.json，跳过 status=done 的 phase。

## 6. 端到端 e2e（dsp 全新【学习】）

清空 dsp 的 KB + .codebase，充当 project-mastery 编排器跑完整【学习】子流程：

- **入口判定**：KB 半成品（残留旧 01/02 + 已退役 project-type.json + 无 manifest）→ 走【学习】，显式声明。
- **波次 1**：dispatch pm-scan → scan-result.json + scan-summary.md + 01。
- **波次 2**：读 scan-result.json classifications（fullstack is_primary=true）路由，同一轮并行 dispatch 4 个分析 subagent → 02/03/04/05。
- **波次 3**：主会话 pm-kb-index → README（元信息从 scan-result.json 读）。
- **波次 4**：dispatch pm-verify → 06（只报告不修改，抽样 52 条，partial：一致 41 / 不一致 5 / 无法核对 6，0 严重）。
- **收尾**：主会话 manifest.json，projectType.source=`.codebase/scan-result.json`、primaryType=fullstack、scannedAt=scan-result.generated_at、skillVersions.pm-scan=v2（**全部与 scan-result.json 一致**）。
- **关键断言**：全程未产/未读 project-type.json；路由 + 元信息全部走 scan-result.json。

## 7. 通用化自检

`grep -rni "dsp" skills/*/SKILL.md` → **0 命中**（skill 源码零项目特定内容，通用化纪律保持）。

## 8. commit 清单（分支 p0-scan-cache-foundation）

| commit | 内容 |
|---|---|
| 31a697b | fix(scripts): link-skills.sh 相对路径推导 |
| 8727abe | feat(schemas): scan-result.json 契约 |
| 678fdc1 | feat(pm-scan): 产 scan-result.json，退役 project-type.json |
| 06a36db | feat(pm-techstack-generic): Step 0 读缓存 |
| a1dafe4 | feat(project-mastery): 读 scan-result + progress.json |
| 6314883 | feat(skills): 退役收尾（pm-kb-index/pm-verify/learn-project）|

## 9. 延后项（不在本期）

- **P0-2** SKILL.md 瘦身 + templates/references 分层（12 skill 重构，单独立 plan）
- **P0-3** 全 skill 输入输出预算纪律（pm-scan 已有，需推广到其余 skill）
- **P0-5** pm-verify-lite（默认轻量抽样校验，完整 pm-verify 降为 opt-in）
- **P1** 其余项（AI/HUMAN 双区增量保护 / validate 脚本 / 任务输入包 / 失败恢复运行时策略）
- **期2 计数对账**（波次 2 并行 subagent 独立估算漂移，e2e 再次复现：06 报告 ErrorCode 28 vs 实际 23）
- **schema 部署**：当前 schema 文件未随 skill 软链分发，模型按 SKILL.md 内嵌字段规格执行（已验证合规）；schema 文件的机器校验留给 P1-2 validate 脚本。
