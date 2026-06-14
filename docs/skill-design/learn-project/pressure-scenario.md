# learn-project 压力场景（TDD）

## 失败模式

编排"已有项目学习文档生成"全流程时常见的失败：

1. **不复用扫描底座**：第 0 步重复自己扫描项目，不读 project-knowledge/01、02，或 A 已跑过仍重跑 pm-scan/pm-techstack。
2. **跳过人在回路**：不对全部功能都生成（不挑），浪费且产出臃肿；或挑选机制缺失。
3. **doc-gen 不用提示词**：直接让模型写文档，没走"保存提示词→带提示词 dispatch"，导致提示词不可复用重跑、文档质量无方法论约束。
4. **不维护 progress.json**：无法断点续跑、lp-index 编造时间、完成状态不可查。
5. **流程顺序错乱**：未先扫描就生成、未生成提示词就生成文档、未生成文档就索引。

## 验证方式

在目标项目上跑 learn-project 全流程，检查：

- [ ] 第 0 步探测 project-knowledge/01、02：存在则读（不重跑 A）；不存在则 dispatch pm-scan + pm-techstack 补齐。
- [ ] 第 1 步 dispatch lp-feature-scan 产出 inventory.md。
- [ ] 第 2 步呈现 inventory 供人在回路挑选，记录选中项。
- [ ] 第 3 步对每个选中功能：先 dispatch lp-prompt-gen 产出提示词，再用提示词 dispatch doc subagent 产出文档。
- [ ] 全程维护 `_meta/progress.json`（功能清单/选中/各功能 prompt+doc 完成状态/时间）。
- [ ] 第 4 步调用 lp-index 产出 README.md。

## GREEN 规则

全流程产出齐备（README/inventory/prompts/docs/_meta 五类齐）；第 0 步正确复用或补齐 01/02；只对选中功能生成且经提示词驱动；progress.json 真实反映状态；doc 文档引用的代码路径真实、零臆造。满足即 GREEN。
