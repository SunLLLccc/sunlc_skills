# project-mastery 期 1：学习管线核心 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现学习管线核心——对任意已有项目端到端产出知识库（6 文档 + 总索引 + 校验报告 + meta）。技术栈先走通用兜底（pm-techstack-generic），所有项目类型都能跑。

**Architecture:** 8 个 skills：`project-mastery`（顶层编排）+ `pm-scan`（扫描+类型识别/路由）+ `pm-techstack-generic`（通用技术栈）+ `pm-conventions`（开发规范）+ `pm-api-index`（API 索引）+ `pm-build-deploy`（构建部署）+ `pm-kb-index`（总索引汇编）+ `pm-verify`（校验）。skills 写在工作区 `skills/`，软链到 `~/.claude/skills/` 全局可发现。期 1 不建预定义 agent——project-mastery 用"按需 dispatch 兜底"（方式 A）调度；预定义 agent 留到期 4。

**Tech Stack:** Claude Code skills（SKILL.md + frontmatter）；superpowers 的 `writing-skills`（TDD for skills）、`verification-before-completion`；subagent 压力测试。

**Spec:** `docs/superpowers/specs/2026-06-14-project-mastery-design.md`

**测试靶子:** `/Users/sunlc/sunlc_work/sunlc_skills/dsp`（全栈：前端 dsp-admin-web + 后端多模块 dsp-parent）

**每个 skill 任务的 TDD 节奏（遵循 writing-skills）：**
1. 写压力场景（记录 baseline 失败模式）
2. 跑 baseline（dispatch subagent，**不带** skill，记录跑偏）
3. 写 SKILL.md（frontmatter + 必含章节 + 编码指定规则）
4. 软链 + 验证可发现
5. 跑验证（dispatch subagent，**带** skill，检查遵守）
6. 若有漏洞，refine 并重验
7. Commit

> subagent 测试机制详见 superpowers 的 `writing-skills` 配套文档 `testing-skills-with-subagents.md`。

---

### Task 0: 搭建工作区结构、软链机制与版本控制

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/`（目录）
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/scripts/link-skills.sh`
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/.gitignore`

- [ ] **Step 1: 初始化 git 仓库**

```bash
cd /Users/sunlc/sunlc_work/sunlc_skills
git init
git config user.name >/dev/null 2>&1 || git config user.email >/dev/null 2>&1 || echo "git 身份已配置或使用全局"
```

- [ ] **Step 2: 写 .gitignore（排除测试靶子 dsp 与 node_modules）**

`.gitignore` 内容：
```
# 测试靶子项目（不属于本工具集源码）
/dsp/

# 依赖
**/node_modules/

# 系统
.DS_Store

# 构建产物
**/dist/
**/build/
**/target/
```

- [ ] **Step 3: 创建 skills/ 与 scripts/ 目录**

```bash
mkdir -p /Users/sunlc/sunlc_work/sunlc_skills/skills
mkdir -p /Users/sunlc/sunlc_work/sunlc_skills/scripts
```

- [ ] **Step 4: 写软链脚本 `scripts/link-skills.sh`**

```bash
#!/usr/bin/env bash
# 把工作区的每个 skills/<name> 软链到 ~/.claude/skills/<name>，使其全局可发现
set -euo pipefail
SRC_DIR="/Users/sunlc/sunlc_work/sunlc_skills/skills"
DEST_DIR="$HOME/.claude/skills"
mkdir -p "$DEST_DIR"
for skill_dir in "$SRC_DIR"/*/; do
  [ -d "$skill_dir" ] || continue
  name=$(basename "$skill_dir")
  ln -sfn "$skill_dir" "$DEST_DIR/$name"
  echo "linked: $name"
done
```

- [ ] **Step 5: 赋予执行权限**

Run: `chmod +x /Users/sunlc/sunlc_work/sunlc_skills/scripts/link-skills.sh`

- [ ] **Step 6: 用临时 skill 验证软链机制可用**

创建临时 `/Users/sunlc/sunlc_work/sunlc_skills/skills/pm-test/SKILL.md`：
```
---
name: pm-test
description: 临时验证软链用，验证后删除
---
# pm-test
临时占位。
```

Run: `bash /Users/sunlc/sunlc_work/sunlc_skills/scripts/link-skills.sh`
Expected: 输出 `linked: pm-test`

验证软链解析：
Run: `cat ~/.claude/skills/pm-test/SKILL.md | head -1`
Expected: `---`

- [ ] **Step 7: 删除临时 skill**

```bash
rm -rf /Users/sunlc/sunlc_work/sunlc_skills/skills/pm-test
rm -f ~/.claude/skills/pm-test
```

- [ ] **Step 8: Commit**

```bash
cd /Users/sunlc/sunlc_work/sunlc_skills
git add .gitignore scripts/link-skills.sh docs/
git commit -m "chore: 初始化工作区结构、软链脚本、版本控制"
```

---

### Task 1: pm-scan（扫描 + 类型识别 / 路由器）

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/pm-scan/SKILL.md`

**pressure scenario（baseline 失败模式）：** 不带 skill 扫描项目 → ① 盲目全扫导致超 token/超时；② 类型强塞进"前端/后端/全栈"三选一，忽略移动端/桌面端/库/Monorepo/微服务或多维度叠加；③ 不输出类型判定的依据与置信度，router 无法信任。

**该 skill 必须编码的规则：**
- 扫描策略：先扫顶层结构、配置文件（package.json/pom.xml/go.mod 等）、入口点，再按需深扫，不盲目遍历全树。
- 类型识别：多维度叠加（一个项目可同时是 frontend+lib），不强制三选一；覆盖前端/后端/全栈/移动端/桌面端/CLI库/Monorepo/微服务/其他。
- 必须输出：类型判定 + **置信度** + **判定依据**（哪些证据支持该判定）。
- 产出两份：`docs/project-knowledge/01-项目概览.md` 与 `_meta/project-type.json`（结构化，供 project-mastery 路由）。

- [ ] **Step 1: 写压力场景**

记录到 `skills/pm-scan/_pressure-scenario.md`：具体描述上述 3 类 baseline 失败模式，作为 TDD 的"测试用例"。

- [ ] **Step 2: 跑 baseline（RED）**

dispatch 一个 general-purpose subagent，prompt：
> "扫描项目 /Users/sunlc/sunlc_work/sunlc_skills/dsp，识别它是什么类型的项目，并给出项目概览。不要参考任何 skill。"

记录 subagent 的输出中出现的跑偏点（是否盲目全扫？类型是否三选一？是否给出依据？）。

- [ ] **Step 3: 写 SKILL.md**

按上述 frontmatter、必含章节、规则撰写 `skills/pm-scan/SKILL.md`：
- frontmatter: `name: pm-scan`，`description: 扫描已有项目，识别项目类型（多维度，不强制三选一），产出项目概览文档与结构化类型判定（供 project-mastery 路由）。`
- 章节：扫描策略（先顶层后深扫）、类型识别规则（多维叠加 + 覆盖类型清单）、规模指标采集、入口点定位、产出格式（01-项目概览.md + _meta/project-type.json 模板）、置信度与依据要求。

- [ ] **Step 4: 软链 + 验证可发现**

Run: `bash /Users/sunlc/sunlc_work/sunlc_skills/scripts/link-skills.sh`
验证：`head -3 ~/.claude/skills/pm-scan/SKILL.md` 显示 frontmatter。

- [ ] **Step 5: 跑验证（GREEN）**

dispatch 一个**新** subagent（fresh context），prompt：
> "使用 pm-scan skill 扫描项目 /Users/sunlc/sunlc_work/sunlc_skills/dsp，按 skill 要求产出概览文档与类型判定。"

验收标准（全部满足才算 GREEN）：
- 产出 `dsp/docs/project-knowledge/01-项目概览.md`
- 产出 `dsp/docs/project-knowledge/_meta/project-type.json`
- 类型判定为 `fullstack`（含 frontend + backend 多模块），**不是**强行三选一
- project-type.json 含 `confidence` 与 `evidence` 字段

- [ ] **Step 6: 若有漏洞，refine SKILL.md 并重验**

若验收任一项不满足，针对性补强 SKILL.md 对应规则，重跑 Step 5。

- [ ] **Step 7: Commit**

```bash
cd /Users/sunlc/sunlc_work/sunlc_skills
git add skills/pm-scan/
git commit -m "feat(pm-scan): 项目扫描与多维度类型识别 skill"
```

---

### Task 2: pm-techstack-generic（通用技术栈分析 / 兜底）

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/pm-techstack-generic/SKILL.md`

**pressure scenario：** 不带 skill 分析技术栈 → ① 只罗列 package.json/pom.xml 的依赖，**漏掉项目自封装的内部框架**；② 不区分开源框架 vs 项目自造；③ 不记版本/用途/配置位置。

**该 skill 必须编码的规则：**
- 开源框架清单：名称、版本、用途、配置文件位置。
- **自封装框架识别（重点）**：扫 import/require、找被多处复用的基类/工具类、检查 `lib/` `core/` `sdk/` `common/` `utils/` 等目录，明确区分"标准包/开源包" vs "项目自造的内部 SDK/基类/中间件"。
- 架构模式：分层、模块划分、数据流。
- 核心模块依赖关系。
- 产出：`02-技术栈与架构.md`。

- [ ] **Step 1: 写压力场景** → `skills/pm-techstack-generic/_pressure-scenario.md`（记录上述 3 类失败模式）

- [ ] **Step 2: 跑 baseline（RED）**

dispatch general-purpose subagent，prompt：
> "分析项目 /Users/sunlc/sunlc_work/sunlc_skills/dsp 的技术栈。不要参考任何 skill。"

记录跑偏点（是否只列依赖？是否漏自封装框架？）。

- [ ] **Step 3: 写 SKILL.md**

- frontmatter: `name: pm-techstack-generic`，`description: 通用技术栈分析（兜底，适用所有项目类型）：梳理开源框架与项目自封装框架，产出技术栈与架构文档。`
- 章节：开源框架清单、自封装框架识别（含具体识别策略）、架构模式、核心模块依赖、产出格式（02-技术栈与架构.md）。

- [ ] **Step 4: 软链** — Run: `bash scripts/link-skills.sh`；验证 `head -3 ~/.claude/skills/pm-techstack-generic/SKILL.md`

- [ ] **Step 5: 跑验证（GREEN）**

dispatch 新 subagent，prompt：
> "使用 pm-techstack-generic skill 分析 /Users/sunlc/sunlc_work/sunlc_skills/dsp 的技术栈（输入：dsp/docs/project-knowledge/01-项目概览.md 作为上下文）。按 skill 产出文档。"

验收标准：
- 产出 `dsp/docs/project-knowledge/02-技术栈与架构.md`
- 含独立的「自封装框架」章节
- 该章节识别出 ≥1 个 dsp 实际存在的自封装框架（如 dsp-common / dsp-core 内部的封装）
- 开源框架条目含版本

- [ ] **Step 6: refine + 重验**（若验收不满足）

- [ ] **Step 7: Commit**

```bash
git add skills/pm-techstack-generic/
git commit -m "feat(pm-techstack-generic): 通用技术栈分析（含自封装框架识别）"
```

---

### Task 3: pm-conventions（开发规范提取）

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/pm-conventions/SKILL.md`

**pressure scenario：** 不带 skill 提取规范 → ① **臆造**通用最佳实践，不对照项目实际代码；② 规范与项目真实用法不符。

**该 skill 必须编码的规则：**
- 覆盖：目录规范、命名规范（文件/变量/函数/类/组件）、代码封装规范（模块化/抽象层级）、前端样式规范（如适用：CSS 方案/主题/响应式）、错误处理、测试规范、Git 提交规范（从历史推断）。
- **核心原则：从代码实际推断，不臆造。** 每条规范必须能在代码中找到证据。
- 标注每条规范的「推断置信度」（高=多处一致证据；低=仅个别样例）。
- 产出：`03-开发规范.md`。

- [ ] **Step 1: 写压力场景** → `skills/pm-conventions/_pressure-scenario.md`

- [ ] **Step 2: 跑 baseline（RED）**

dispatch subagent，prompt：
> "提取项目 /Users/sunlc/sunlc_work/sunlc_skills/dsp 的开发规范。不要参考任何 skill。"

记录是否出现臆造规范、是否对照实际代码。

- [ ] **Step 3: 写 SKILL.md**

- frontmatter: `name: pm-conventions`，`description: 从项目代码提取实际开发规范（目录/命名/封装/样式/错误处理/测试/Git），每条规范附代码证据与置信度，产出开发规范文档。`
- 章节：上述 7 类规范 + 「证据与置信度」要求 + 产出格式。

- [ ] **Step 4: 软链** — Run: `bash scripts/link-skills.sh`；验证 frontmatter

- [ ] **Step 5: 跑验证（GREEN）**

dispatch 新 subagent，prompt：
> "使用 pm-conventions skill 提取 /Users/sunlc/sunlc_work/sunlc_skills/dsp 的开发规范（上下文：01-项目概览.md）。按 skill 产出文档。"

验收标准：
- 产出 `03-开发规范.md`
- 每条规范附代码证据（文件/样例）与置信度
- 抽检 2 条规范，在 dsp 代码中确实成立

- [ ] **Step 6: refine + 重验**

- [ ] **Step 7: Commit**

```bash
git add skills/pm-conventions/
git commit -m "feat(pm-conventions): 从代码实际推断的开发规范提取"
```

---

### Task 4: pm-api-index（API 索引生成）

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/pm-api-index/SKILL.md`

**pressure scenario：** 不带 skill 生成 API 索引 → ① 不区分对外 API vs 内部 API；② 缺位置信息（文件:行）；③ 平铺无组织，不按模块分类。

**该 skill 必须编码的规则：**
- 按模块/领域分类组织。
- 每个 API：路径或签名、入出参、用途、`文件:行`。
- 明确区分对外 API（HTTP 路由/RPC 接口/导出函数）vs 内部 API。
- 调用关系（谁调用谁，至少标注核心 API 的调用方）。
- 产出：`04-API索引.md`。

- [ ] **Step 1: 写压力场景** → `skills/pm-api-index/_pressure-scenario.md`

- [ ] **Step 2: 跑 baseline（RED）**

dispatch subagent，prompt：
> "生成项目 /Users/sunlc/sunlc_work/sunlc_skills/dsp 的 API 索引。不要参考任何 skill。"

记录跑偏点。

- [ ] **Step 3: 写 SKILL.md**

- frontmatter: `name: pm-api-index`，`description: 提取项目 API 索引，按模块分类，含路径/签名/入出参/用途/文件位置，区分对外与内部 API，产出 API 索引文档。`
- 章节：API 分类规则、API 条目格式（含 文件:行）、对外 vs 内部判定、调用关系、产出格式。

- [ ] **Step 4: 软链** — Run: `bash scripts/link-skills.sh`；验证 frontmatter

- [ ] **Step 5: 跑验证（GREEN）**

dispatch 新 subagent，prompt：
> "使用 pm-api-index skill 生成 /Users/sunlc/sunlc_work/sunlc_skills/dsp 的 API 索引（上下文：01-项目概览.md）。"

验收标准：
- 产出 `04-API索引.md`
- 按模块分类（非平铺）
- 区分对外/内部 API
- 抽检 2 个 API，其 `文件:行` 在 dsp 代码中可定位

- [ ] **Step 6: refine + 重验**

- [ ] **Step 7: Commit**

```bash
git add skills/pm-api-index/
git commit -m "feat(pm-api-index): 按模块分类、区分内外的 API 索引"
```

---

### Task 5: pm-build-deploy（构建打包部署梳理）

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/pm-build-deploy/SKILL.md`

**pressure scenario：** 不带 skill 梳理构建部署 → ① **猜命令不验证**（臆造 npm run build 等）；② 臆造部署方式。

**该 skill 必须编码的规则：**
- 覆盖：环境要求（运行时版本）、依赖安装、开发启动、构建/打包命令+产物、部署方式（Docker/K8s/静态托管…）、环境变量/配置项、CI/CD。
- **核心原则：命令必须从配置文件实际读取**（package.json scripts、pom.xml、Dockerfile、Makefile、CI 配置等），不臆造。
- 每条命令/部署方式标注「已验证」（在配置中找到）/「推断」（未直接找到，需人工确认）。
- 产出：`05-构建打包部署.md`。

- [ ] **Step 1: 写压力场景** → `skills/pm-build-deploy/_pressure-scenario.md`

- [ ] **Step 2: 跑 baseline（RED）**

dispatch subagent，prompt：
> "梳理项目 /Users/sunlc/sunlc_work/sunlc_skills/dsp 的构建、打包、部署流程。不要参考任何 skill。"

记录是否出现臆造命令。

- [ ] **Step 3: 写 SKILL.md**

- frontmatter: `name: pm-build-deploy`，`description: 从配置文件实际读取构建/打包/部署流程（不臆造），每项标注已验证或推断，产出构建打包部署文档。`
- 章节：上述 7 类 + 「命令来源验证」要求 + 产出格式。

- [ ] **Step 4: 软链** — Run: `bash scripts/link-skills.sh`；验证 frontmatter

- [ ] **Step 5: 跑验证（GREEN）**

dispatch 新 subagent，prompt：
> "使用 pm-build-deploy skill 梳理 /Users/sunlc/sunlc_work/sunlc_skills/dsp 的构建部署（上下文：01-项目概览.md）。"

验收标准：
- 产出 `05-构建打包部署.md`
- 每条命令标注「已验证/推断」
- 抽检 2 条「已验证」命令，在 dsp 的 package.json/pom.xml/Dockerfile 等中确实存在

- [ ] **Step 6: refine + 重验**

- [ ] **Step 7: Commit**

```bash
git add skills/pm-build-deploy/
git commit -m "feat(pm-build-deploy): 从配置验证的构建打包部署梳理"
```

---

### Task 6: pm-kb-index（知识库总索引汇编）

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/pm-kb-index/SKILL.md`

**pressure scenario：** 不带 skill 汇编索引 → ① 平铺文件列表，无"何时读哪份"导航逻辑；② 无基于任务的阅读路径。

**该 skill 必须编码的规则：**
- 产出 `README.md`（知识库前门）。
- 含：项目一句话简介、各文档导航（链接 + 「何时读哪份」一句话说明）、知识库元信息（生成时间、源码版本）、**快速上手路径**（基于任务的阅读指引，如"要开发某功能→先读 02+03+04"）。
- 主会话执行（非 agent）：读全部已生成文档，汇编索引。

- [ ] **Step 1: 写压力场景** → `skills/pm-kb-index/_pressure-scenario.md`

- [ ] **Step 2: 跑 baseline（RED）**

dispatch subagent，prompt：
> "为 /Users/sunlc/sunlc_work/sunlc_skills/dsp/docs/project-knowledge/ 下的知识库文档汇编一个总索引 README。不要参考任何 skill。"

记录是否平铺、是否有导航逻辑。

- [ ] **Step 3: 写 SKILL.md**

- frontmatter: `name: pm-kb-index`，`description: 汇编知识库总索引 README：各文档导航（何时读哪份）、元信息、基于任务的快速上手路径。主会话执行。`
- 章节：导航结构（每份文档的「何时读」）、快速上手路径模板、元信息、产出格式。

- [ ] **Step 4: 软链** — Run: `bash scripts/link-skills.sh`；验证 frontmatter

- [ ] **Step 5: 跑验证（GREEN）**

主会话执行 pm-kb-index，输入 dsp 已生成的 01-05 文档。

验收标准：
- 产出 `dsp/docs/project-knowledge/README.md`
- 每份文档有「何时读哪份」说明
- 含 ≥2 条基于任务的阅读路径

- [ ] **Step 6: refine + 重验**

- [ ] **Step 7: Commit**

```bash
git add skills/pm-kb-index/
git commit -m "feat(pm-kb-index): 知识库总索引与任务型阅读路径"
```

---

### Task 7: pm-verify（分析结果校验）

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/pm-verify/SKILL.md`

**pressure scenario：** 不带 skill 校验文档 → ① 橡皮图章，不实际对照代码；② 发现问题也不报告。

**该 skill 必须编码的规则：**
- 引用 superpowers 的 `verification-before-completion` 理念。
- 抽样核对：从每份文档抽取若干断言，对照实际代码验证。
- **只报告，不自动修改**（修改交给人工或重跑对应 skill）。
- 产出 `06-校验报告.md`：各文档置信度、抽样核对结果、待人工确认的可疑项清单。

- [ ] **Step 1: 写压力场景** → `skills/pm-verify/_pressure-scenario.md`

- [ ] **Step 2: 跑 baseline（RED）**

dispatch subagent，prompt：
> "校验 /Users/sunlc/sunlc_work/sunlc_skills/dsp/docs/project-knowledge/ 下知识库文档的准确性。不要参考任何 skill。"

记录是否实际对照代码、是否报问题。

- [ ] **Step 3: 写 SKILL.md**

- frontmatter: `name: pm-verify`，`description: 校验知识库文档准确性：抽样核对文档断言 vs 实际代码，产出校验报告（问题清单，不自动改）。`
- 章节：抽样策略、对照核对方法、置信度评估、「只报告不改」原则、产出格式（06-校验报告.md）。

- [ ] **Step 4: 软链** — Run: `bash scripts/link-skills.sh`；验证 frontmatter

- [ ] **Step 5: 跑验证（GREEN）**

dispatch 新 subagent，prompt：
> "使用 pm-verify skill 校验 /Users/sunlc/sunlc_work/sunlc_skills/dsp/docs/project-knowledge/ 的文档。"

验收标准：
- 产出 `06-校验报告.md`
- 含 ≥3 条实际抽样核对（每条：文档断言 + 代码验证结果）
- 若发现问题，列入可疑项（即使全部通过，也要说明抽样范围）

- [ ] **Step 6: refine + 重验**

- [ ] **Step 7: Commit**

```bash
git add skills/pm-verify/
git commit -m "feat(pm-verify): 知识库文档抽样校验（只报告不改）"
```

---

### Task 8: project-mastery（顶层编排 + 学习子流程串联）

**Files:**
- Create: `/Users/sunlc/sunlc_work/sunlc_skills/skills/project-mastery/SKILL.md`

**pressure scenario：** 不带编排 skill → ① 不知道何时用哪个子流程；② 学习流程步骤乱序或漏步；③ 没有 dispatch 兜底（某 agent 缺失就卡住）。

**该 skill 必须编码的规则：**
- **入口判定**：检查目标项目 `docs/project-knowledge/` 是否存在 + `_meta/manifest.json` → 不存在走【学习】；存在且代码变走【更新】；有需求文档走【开发】。（期 1 只实现【学习】；更新/开发留 stub 指向期 2/3。）
- **学习子流程编排**（按 spec 第 5 节波次）：
  - 波次 1：dispatch 执行 pm-scan 的 subagent → 产 01 + project-type.json
  - 波次 2：读 project-type.json → 并行 dispatch 4 个 subagent（pm-techstack-generic / pm-conventions / pm-api-index / pm-build-deploy），各自带 01 作为上下文
  - 波次 3：主会话执行 pm-kb-index → 产 README
  - 波次 4：dispatch 执行 pm-verify 的 subagent → 产 06
  - 收尾：写 `_meta/manifest.json`（源码版本/时间）
- **dispatch 策略**：期 1 用"按需 dispatch 兜底"（方式 A）——用 Agent 工具 dispatch general-purpose subagent，任务描述指明"遵循 `<skill名>` skill"。预定义 agent（方式 B）留到期 4。

- [ ] **Step 1: 写压力场景** → `skills/project-mastery/_pressure-scenario.md`

- [ ] **Step 2: 跑 baseline（RED）**

主会话（不带 project-mastery）尝试对 dsp 跑一遍"学习项目"。记录：步骤是否乱序、是否漏波次、dispatch 是否无兜底。

- [ ] **Step 3: 写 SKILL.md**

- frontmatter: `name: project-mastery`，`description: 项目学习与开发总编排：判定学习/更新/开发子流程，按波次调度对应 skills（预定义 agent 优先、无则按需 dispatch 兜底）。`
- 章节：入口判定逻辑、学习子流程（波次 1-4 + 收尾，含每步 dispatch 指令）、更新子流程 stub（指向期 2）、开发子流程 stub（指向期 3）、dispatch 策略（方式 A 兜底 + 方式 B 预留）。

- [ ] **Step 4: 软链** — Run: `bash scripts/link-skills.sh`；验证 frontmatter

- [ ] **Step 5: 跑验证（GREEN）**

在新会话中对 dsp 触发 project-mastery（说"学习这个项目 /Users/sunlc/sunlc_work/sunlc_skills/dsp"）。验收标准：
- 自动判定走【学习】子流程
- 按波次 1→2→3→4 顺序执行
- 波次 2 的 4 个分析 skill 真并行
- 最终产出完整知识库（README + 01-06 + _meta/）

- [ ] **Step 6: refine + 重验**（若编排乱序或漏步）

- [ ] **Step 7: Commit**

```bash
git add skills/project-mastery/
git commit -m "feat(project-mastery): 顶层编排与学习子流程串联（期1）"
```

---

### Task 9: 端到端验证 on dsp + manifest 收尾

**Files:**
- Verify: `dsp/docs/project-knowledge/` 全套产出

- [ ] **Step 1: 清空 dsp 已有知识库（若有），从干净状态重跑**

```bash
rm -rf /Users/sunlc/sunlc_work/sunlc_skills/dsp/docs/project-knowledge
```

- [ ] **Step 2: 全流程触发**

新会话中对 dsp 执行 project-mastery 学习子流程，完整跑完波次 1-4 + 收尾。

- [ ] **Step 3: 验收知识库完整性**

Run: `ls -1 /Users/sunlc/sunlc_work/sunlc_skills/dsp/docs/project-knowledge/`
Expected（全部存在）：
```
01-项目概览.md
02-技术栈与架构.md
03-开发规范.md
04-API索引.md
05-构建打包部署.md
06-校验报告.md
README.md
_meta/
```

Run: `ls -1 /Users/sunlc/sunlc_work/sunlc_skills/dsp/docs/project-knowledge/_meta/`
Expected: `manifest.json` 与 `project-type.json` 均存在。

- [ ] **Step 4: 抽样质量复核（人工）**

人工抽检：
- 02 是否识别出 dsp 的自封装框架（dsp-common/dsp-core 等）
- 03 的规范是否与 dsp 代码一致（非臆造）
- 04 的 API `文件:行` 是否可定位
- 05 的构建命令是否在配置中存在
- 06 是否报出至少 1 个待确认项或说明抽样范围

- [ ] **Step 5: 记录期 1 验收结论**

把验收结果（哪些通过、哪些需改进）记到 `docs/superpowers/plans/2026-06-14-project-mastery-phase1-验收.md`。发现的问题回流到对应 skill 的 _pressure-scenario.md，作为期 1 收尾的改进项。

- [ ] **Step 6: Commit**

```bash
cd /Users/sunlc/sunlc_work/sunlc_skills
git add docs/superpowers/plans/2026-06-14-project-mastery-phase1-验收.md skills/
git commit -m "test: 期1 端到端验证 on dsp + 验收记录"
```

---

## 自检（Self-Review）

**1. Spec 覆盖：** spec 期 1 范围的 8 个 skill（project-mastery / pm-scan / pm-techstack-generic / pm-conventions / pm-api-index / pm-build-deploy / pm-kb-index / pm-verify）→ 分别对应 Task 8/1/2/3/4/5/6/7，全覆盖。学习子流程波次 1-4 → Task 8 编码。✅

**2. 占位符扫描：** 无 TBD/TODO。每个 skill 的规则、压力场景、验收标准均具体可查。✅

**3. 类型/命名一致：** skill 名（pm-scan 等）在所有 task、frontmatter、commit message、验收命令中一致；产出文件名（01-项目概览.md 等）与 spec 第 4 节一致。✅

**4. 文件路径：** 所有 skill 写在 `skills/pm-xxx/SKILL.md`，软链脚本 `scripts/link-skills.sh`，产出在 `dsp/docs/project-knowledge/`，一致。✅
