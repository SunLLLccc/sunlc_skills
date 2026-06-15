# AI/HUMAN 双区增量更新约定（按需读取）

> 由 project-mastery 编排器按需加载。【更新】子流程（期 2 实现）的核心机制。
> 对应 claude优化清单 P1-1：增量更新保护——小模型重生成更易覆盖人工补充，双区+脚本是物理隔离，切片喂入又省 context。

## 为什么要双区

小模型（qwen3.6 35b）在【更新】子流程里重生成某段文档时，**极易覆盖人工补充的注意点**——它把整段重写，人工备注就没了。双区是物理隔离：

- **AI-GENERATED 区**：AI 可整块替换（重生成时只换这一块）。
- **HUMAN-NOTES 区**：人工补充，脚本永不动它，AI 重生成不覆盖。

【更新】时只喂"AI 区 + 相关证据"给小模型，不喂整篇文档——既省 context，又防覆盖。

## 标记语法

每个逻辑 section（通常对应一个 `##` 二级标题）用成对 HTML 注释标记：

```markdown
<!-- AI-GENERATED:<section-id> START -->
...AI 生成的内容（重生成时整块替换）...
<!-- AI-GENERATED:<section-id> END -->

<!-- HUMAN-NOTES:<section-id> START -->
...人工补充（永不被覆盖；空块表示暂无人工备注）...
<!-- HUMAN-NOTES:<section-id> END -->
```

- `<section-id>`：该 section 的唯一标识，取标题 slug（中文标题原样可用，如 `技术栈`、`API`、`header`）。
- 一个 section 的 AI 区与 HUMAN 区用**同一个** `<section-id>` 配对。
- 标记是 HTML 注释，在渲染出的 markdown 里不可见，不影响阅读。

## 脚本：update_ai_generated_block.py

`scripts/update_ai_generated_block.py`（stdlib 无依赖）三种模式：

### 1. 注入骨架：`--init`

给一份无标记的文档按标题切 section，注入 AI-GENERATED + HUMAN-NOTES 骨架：

```bash
python3 scripts/update_ai_generated_block.py {PROJECT_ROOT}/docs/project-knowledge/01-项目概览.md --init
# 加 --dry-run 先看 diff
```

### 2. 列出 section：`--list`

```bash
python3 scripts/update_ai_generated_block.py 01-项目概览.md --list
# 输出：技术栈  AI=有  HUMAN=有
```

### 3. 替换 AI 块：`--section ID --ai-file F`

把新 AI 内容写进指定 section 的 AI-GENERATED 块，HUMAN-NOTES 块原样保留：

```bash
python3 scripts/update_ai_generated_block.py 01-项目概览.md \
    --section 技术栈 --ai-file /tmp/new-techstack.md --dry-run
# 确认 diff 后去掉 --dry-run 写盘
```

## 与【更新】子流程的衔接（期 2 实现）

【更新】子流程（入口判定命中"代码变化"时走）按如下使用双区：

1. 读 `_meta/manifest.json` 的 `sourceCommit` 与当前 `git rev-parse HEAD` diff，识别变化的文件/模块。
2. 对受影响的 KB 文档 section：
   - 把该 section 的**当前 AI 区内容** + **变化证据（diff 涉及的源码）**喂给小模型重生成。
   - **不喂** HUMAN-NOTES 区、**不喂**整篇文档（省 context + 防串味）。
   - 小模型产出新内容写到临时文件。
3. 调 `update_ai_generated_block.py --section <id> --ai-file <tmp>` 替换 AI 区；HUMAN 区物理保留。
4. `--dry-run` 先核对 diff，人工确认后写盘。

## 何时给文档加双区标记

- **【学习】子流程首次生成**：可选加标记。若预期该文档会被人工补充（典型：03-开发规范、01-项目概览的入口说明），首次生成时即 `--init` 注入骨架。
- **【更新】子流程**：必须已加标记才能增量替换；无标记的文档先 `--init`。
- **纯 AI 文档（无人工补充预期）**：可不加（如 06-校验报告，每次重生成整份覆盖即可）。

## 边界

- **无标记文档**：`--section` 更新会报错（找不到块）；先 `--init`。
- **标记未闭合**（有 START 无 END）：脚本报错拒绝操作，防半截损坏。
- **HUMAN-NOTES 为空块**：合法（表示该 section 暂无人工备注），更新时不影响。
- **section id 冲突**：`--init` 自动加 `-N` 后缀去重。
