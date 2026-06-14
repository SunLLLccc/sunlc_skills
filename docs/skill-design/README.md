# skill 设计笔记（TDD 压力场景）

## 这个目录是什么

每个 skill 在用 `writing-skills`（TDD for skills）开发时，会先写一个**压力场景**：
记录"不带这个 skill 时，模型会怎么跑偏"，以及为防止跑偏而编码进 SKILL.md 的 **GREEN 规则**。
这些压力场景是**设计笔记 + 测试证据**，记录每个规则"为什么存在"。

## 为什么不放在 skills/ 里

`skills/` 里的 `SKILL.md` 是**可复用的通用方法论**——必须 100% 通用，不含任何具体项目（如 dsp）的内容。
压力场景里会带具体项目的 baseline 测试记录（这是 TDD 的证据，天然项目相关），所以**移到本目录**，
让 `skills/` 保持纯净、可对任意项目复用。

## 项目特定内容只允许出现在哪里

| 位置 | 是否允许项目特定内容 |
|------|----------------------|
| `skills/<name>/SKILL.md` | ❌ 禁止。必须通用（占位符、通用技术名） |
| `docs/skill-design/<name>/pressure-scenario.md` | ✅ 允许（这里是 TDD 测试记录） |
| `<目标项目>/docs/project-knowledge/*.md` | ✅ 允许（这是对该项目的分析产出） |

## 目录结构

```
docs/skill-design/
├─ README.md                              ← 本文件
├─ pm-scan/pressure-scenario.md
├─ pm-techstack-generic/pressure-scenario.md
└─ pm-conventions/pressure-scenario.md
```

新增 skill 时，按同样方式把压力场景放在 `docs/skill-design/<name>/pressure-scenario.md`。
