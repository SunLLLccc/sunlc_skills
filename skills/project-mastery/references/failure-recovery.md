# 失败恢复运行时策略（按需读取）

> 由 project-mastery 编排器按需加载。对应 claude优化清单 P1-7。
> 小模型（qwen3.6 35b）失败率高，**失败即重跑全流程会指数级放大成本**——本约定是 progress.json 的运行时配套。

## 核心原则：失败不重跑全流程，降级 + 续跑

单个 phase（波次内的一个 skill）失败时，**不重跑整条管线**，而是：

1. **说明原因**：把失败原因写入 `progress.json` 该 phase 的 `reason` 字段。
2. **降级产出**：该 phase 的结论标 `uncertain`（scan-result.json）或在 KB 文档里标「推断/待补」，产出降级内容（如"探测后未发现 X"或部分结果）。
3. **续跑下一独立 phase**：跳过失败 phase，继续管线里与之无依赖的后续 phase。
4. **记入 knownGaps**：收尾写 manifest 时，把 failed phase 记入 `knownGaps`，不阻塞收尾。

**为什么**：pm 管线里波次 2 的 4 个分析（techstack/conventions/api-index/build-deploy）彼此正交，一个失败不该拖垮其它三个。verify 失败更不该让前面 5 份文档作废。

## phase.status 状态机

`progress.json` 每个 phase 的 `status` 取值：

| status | 含义 | 额外字段 |
|--------|------|----------|
| `pending` | 未开始 | — |
| `in-progress` | 执行中 | — |
| `done` | 成功完成 | `output`（产出文件清单） |
| `skipped` | 主动跳过（不适用，如纯库项目无部署） | `reason` |
| `failed` | 失败 | `reason` + `partialOutput` + `retryable` |

`failed` phase 的字段：

```json
{
  "name": "api-index", "skill": "pm-api-index", "status": "failed",
  "reason": "探测后确认项目无 HTTP/RPC/SPI/CLI/事件/导出函数等对外 API 形态",
  "partialOutput": null,
  "retryable": false
}
```

- `reason`：人话说明为什么失败（不是堆栈）。
- `partialOutput`：若有部分产出（如只分析了一半模块），记录产出路径；无则 `null`。
- `retryable`：是否值得重试。`true`（瞬时错误、上下文不足可补）→ 收尾前重试一次；`false`（项目本身无该维度内容、硬约束）→ 不重试，记 knownGaps。

## 编排器对 failed phase 的处理

读 `progress.json` 遇到 failed phase 时：

1. **判断依赖**：该 phase 的产出是否是后续 phase 的硬依赖？
   - **是**（如 scan failed → 波次 2 全部失去路由依据）：停管线，向用户报告 scan 失败、需先修复。
   - **否**（如 api-index failed → kb-index 仍能汇编其它 4 份文档）：续跑。
2. **retryable=true 的 failed**：在收尾前对该 phase 单独重试一次（用同样或更强模型）。仍失败则保留 failed，记 knownGaps。
3. **retryable=false 的 failed**：不重试。该维度在 KB 里降级呈现（04-API索引 写"经探测无对外 API，本文档降级为记录现有可调用入口"或留空 + 注明）。
4. **收尾 manifest**：`knownGaps` 字段记录所有 failed/skipped phase，让使用者知道 KB 的缺口。

## 各 skill 的失败兜底（边界处理补充）

每个分析 skill 在自己的"边界处理"里已声明降级路径，这里汇总失败兜底原则：

| skill | 失败时降级为 |
|-------|-------------|
| pm-scan | scan-result.json 该结论标 `uncertain` + 进 questions；不阻断（scan 是硬依赖，scan 整体失败才停管线） |
| pm-techstack-generic | 自封装框架识别失败 → 02 注明"自封装识别未完成，仅开源框架清单"，confidence 标 inferred |
| pm-conventions | 某维度样例不足 → 降级为"记录现有样例（低置信度）"，不外推 |
| pm-api-index | 无 API 形态 → 04 注明"经探测无对外 API，降级记录现有入口"，不强制凑数 |
| pm-build-deploy | 某部署形态探测失败 → 标"未发现 {类型}"，不臆造 |
| pm-kb-index | 某份 KB 未生成 → README 标"未生成"，其余正常汇编 |
| pm-verify-lite | 某文档核对失败 → 该文档标"无法核对"，其余正常核对；整体仍出报告 |
| pm-verify | 同上，全量版 |

**共性原则**：skill 失败时**产出降级内容 + 标置信度低/待补**，不抛异常中断管线。失败信息回传给编排器写 progress.json 的 `reason`，由编排器决定续跑/重试/停。

## 与断点续跑（progress.json）的关系

- **断点续跑**：开工先读 progress.json，跳过 `done` 的 phase，从第一个非 done 续跑（已有机制，P0-4）。
- **失败恢复**（本约定）：续跑时对 `failed` 的 phase 按 retryable 决定重试或跳过；不因单个 failed 重跑已 done 的 phase。
- 两者共用 progress.json 的 phase 状态，互补：断点续跑管"中断续上"，失败恢复管"失败降级"。
