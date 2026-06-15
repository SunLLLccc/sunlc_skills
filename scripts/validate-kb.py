#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate-kb.py — project-mastery 知识库机器校验（CI 可跑，stdlib 无依赖）

用法：
    python3 scripts/validate-kb.py {PROJECT_ROOT} [--json]

检查项（每项 PASS/FAIL/WARN，汇总 exit code：有 FAIL=1，仅 WARN=0）：
    1. scan-result.json 契约：存在 + required 字段齐全 + classifications 恰好 1 条 is_primary=true
       + 每条结论 confidence ∈ {confirmed,inferred,uncertain} + 带 evidence
    2. KB 文档占位符：01-06/README 无未替换的模板 token（{PROJECT_ROOT}/{功能}/{功能名}/{模块}/
       {NN-文档名}/{文件路径}/{n|m|a|b|c|d|N|M}/待填/待补占位）。注意：只查模板 token，
       不查裸 TODO/XXX（它们常见于代码示例与真实文件名，误报多）。
    3. README 死链：markdown 链接指向的文件存在
    4. 必填章节（WARN）：01 有"项目类型"/"入口"；README 有"何时读"/"任务"/"元信息"
    5. 三态枚举：scan-result.json 所有 confidence 字段值 ∈ 三态

注：skill 源码的通用化（grep 项目特定词 skills/ = 0）不在本脚本职责内——生成出来的 KB 文档
合法包含项目自身的名称与路径。skill 源码通用化由 CI 单独 grep 校验。

面向内网 qwen3.6 35b 小模型——机器校验是外置大脑，错误早发现早止（P1-2）。
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# --- 三态置信度枚举（机器字段英文，与 schemas/codebase-scan-result.schema.json 一致）---
CONFIDENCE_ENUM = {"confirmed", "inferred", "uncertain"}

# scan-result.json 的 required 顶层字段（与 schema 对齐）
SCAN_REQUIRED = [
    "schema_version", "project_root", "generated_at", "scanner",
    "project", "classifications", "technologies", "commands",
    "modules", "entrypoints", "documents", "questions",
]

# KB 文档里不该出现的未替换模板 token（已填的中文标签不算）。
# 刻意不查裸 TODO/TBD/XXX——它们常见于代码示例（ErrorCode.XXX）与真实文件名（TODO.md），误报多。
PLACEHOLDER_RE = re.compile(
    r"\{PROJECT_ROOT\}|\{功能\}|\{功能名\}|\{模块\}|\{NN-文档名\}|\{文件路径\}|"
    r"\{n\}|\{m\}|\{a\}|\{b\}|\{c\}|\{d\}|\{N\}|\{M\}|"
    r"待填|待补占位"
)


class Report:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warned = []

    def ok(self, check, detail=""):
        self.passed.append((check, detail))

    def fail(self, check, detail=""):
        self.failed.append((check, detail))

    def warn(self, check, detail=""):
        self.warned.append((check, detail))

    def exit_code(self):
        return 1 if self.failed else 0

    def text(self):
        lines = []
        lines.append("=" * 60)
        lines.append("validate-kb 报告")
        lines.append("=" * 60)
        for kind, items in (("FAIL", self.failed), ("WARN", self.warned), ("PASS", self.passed)):
            for check, detail in items:
                tag = f"[{kind}] {check}"
                lines.append(f"{tag}" + (f" — {detail}" if detail else ""))
        lines.append("-" * 60)
        lines.append(f"汇总：PASS {len(self.passed)} / WARN {len(self.warned)} / FAIL {len(self.failed)}")
        lines.append(f"exit code: {self.exit_code()}")
        return "\n".join(lines)

    def json(self):
        return json.dumps({
            "passed": [c for c, _ in self.passed],
            "warned": [{"check": c, "detail": d} for c, d in self.warned],
            "failed": [{"check": c, "detail": d} for c, d in self.failed],
            "exit_code": self.exit_code(),
        }, ensure_ascii=False, indent=2)


def _confidence_fields(obj, path="", acc=None):
    """递归收集所有名为 confidence 的字段值及其路径。"""
    if acc is None:
        acc = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if k == "confidence" and isinstance(v, str):
                acc.append((p, v))
            else:
                _confidence_fields(v, p, acc)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _confidence_fields(v, f"{path}[{i}]", acc)
    return acc


def _evidence_missing(item, path):
    """判断一条结论（classifications/technologies/... 的元素）是否缺证据。"""
    ev = item.get("evidence")
    if ev is None:
        return "缺 evidence 字段"
    if isinstance(ev, str) and not ev.strip():
        return "evidence 为空字符串"
    if isinstance(ev, list) and len(ev) == 0:
        return "evidence 为空数组"
    return None


def check_scan_result(report, project_root):
    """1 + 6：scan-result.json 契约 + 三态枚举。"""
    sr_path = project_root / ".codebase" / "scan-result.json"
    if not sr_path.exists():
        report.fail("scan-result.json 存在", f"未找到 {sr_path}")
        return None
    report.ok("scan-result.json 存在")

    try:
        data = json.loads(sr_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        report.fail("scan-result.json 是合法 JSON", f"解析失败：{e}")
        return None
    report.ok("scan-result.json 是合法 JSON")

    # required 字段
    missing = [f for f in SCAN_REQUIRED if f not in data]
    if missing:
        report.fail("scan-result.json required 字段齐全", f"缺失：{missing}")
    else:
        report.ok("scan-result.json required 字段齐全")

    # classifications：恰好 1 条 is_primary=true
    cls = data.get("classifications", [])
    if not isinstance(cls, list):
        report.fail("classifications 是数组", f"实际类型 {type(cls).__name__}")
    else:
        primaries = [c for c in cls if isinstance(c, dict) and c.get("is_primary") is True]
        if len(primaries) != 1:
            report.fail("classifications 恰好 1 条 is_primary=true",
                        f"实际 {len(primaries)} 条（共 {len(cls)} 条）")
        else:
            report.ok("classifications 恰好 1 条 is_primary=true")
        # 每条带 evidence
        for i, c in enumerate(cls):
            if isinstance(c, dict):
                miss = _evidence_missing(c, f"classifications[{i}]")
                if miss:
                    report.fail(f"classifications[{i}] 带证据", miss)

    # 结论类字段（technologies/commands/modules/entrypoints）每条带 evidence
    for field in ("technologies", "commands", "modules", "entrypoints"):
        items = data.get(field, [])
        if isinstance(items, list):
            for i, it in enumerate(items):
                if isinstance(it, dict):
                    miss = _evidence_missing(it, f"{field}[{i}]")
                    if miss:
                        report.fail(f"{field}[{i}] 带证据", miss)

    # 6. 三态枚举：所有 confidence 字段值 ∈ 三态
    confs = _confidence_fields(data)
    bad = [(p, v) for p, v in confs if v not in CONFIDENCE_ENUM]
    if bad:
        report.fail("confidence 全部 ∈ 三态枚举",
                    f"{len(bad)} 条非法：{bad[:3]}{'...' if len(bad)>3 else ''}")
    else:
        report.ok(f"confidence 全部 ∈ 三态枚举（共 {len(confs)} 条）")

    return data


def check_placeholders(report, kb_dir):
    """2：KB 文档（01-05/README）无未替换模板 token。

    刻意排除 06-001-校验报告.md——它是描述核对格式的元报告，正文 legend 永久含
    `{文件路径}:{行号}` 等格式 token（说明三元组结构），不是未填槽位。
    """
    docs = [d for d in _kb_docs(kb_dir) if d.name != "06-001-校验报告.md"]
    if not docs:
        report.warn("KB 文档存在", "docs/project-knowledge/ 下无 01-05/README")
        return
    hits = []
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for m in PLACEHOLDER_RE.finditer(text):
            line_no = text[:m.start()].count("\n") + 1
            hits.append(f"{doc.name}:{line_no} 『{m.group(0)}』")
    if hits:
        report.fail("KB 文档（01-05/README）无未替换模板 token",
                    f"{len(hits)} 处：{hits[:5]}{'...' if len(hits)>5 else ''}")
    else:
        report.ok(f"KB 文档（01-05/README）无未替换模板 token（{len(docs)} 份）")


def check_dead_links(report, kb_dir):
    """3：README 的 markdown 链接指向的文件存在。"""
    readme = kb_dir / "README.md"
    if not readme.exists():
        report.warn("README.md 存在", "未找到 README.md，跳过死链检查")
        return
    text = readme.read_text(encoding="utf-8")
    # [label](target) —— 只查相对路径、.md/无协议的本地链接
    link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
    dead = []
    for m in link_re.finditer(text):
        target = m.group(1).split("#")[0].strip()
        if not target or target.startswith(("http://", "https://", "mailto:", "/")):
            continue
        resolved = (kb_dir / target).resolve()
        if not resolved.exists():
            dead.append(target)
    if dead:
        report.fail("README 无死链", f"{len(dead)} 个死链：{dead[:5]}{'...' if len(dead)>5 else ''}")
    else:
        report.ok("README 无死链")


def check_required_sections(report, kb_dir):
    """4（WARN）：必填章节存在性。"""
    checks = []
    doc01 = kb_dir / "01-001-项目概览.md"
    if doc01.exists():
        t = doc01.read_text(encoding="utf-8")
        if "项目类型" not in t:
            checks.append(("01-001-项目概览 有'项目类型'章节", "未找到'项目类型'"))
        if "入口" not in t:
            checks.append(("01-001-项目概览 有'入口'相关章节", "未找到'入口'"))
    readme = kb_dir / "README.md"
    if readme.exists():
        t = readme.read_text(encoding="utf-8")
        for kw in ("何时读", "任务", "元信息"):
            if kw not in t:
                checks.append((f"README 有'{kw}'章节", f"未找到'{kw}'"))
    for check, detail in checks:
        report.warn(check, detail)
    if not checks:
        report.ok("必填章节抽检（01/README 关键词）")


def _kb_docs(kb_dir):
    """收集 KB 文档（01-06 + README，排除 _meta/）。"""
    if not kb_dir.exists():
        return []
    docs = []
    for name in ("01-001-项目概览.md", "02-001-技术栈与架构.md", "03-001-开发规范.md",
                 "04-001-API索引.md", "05-001-构建打包部署.md", "06-001-校验报告.md", "README.md"):
        p = kb_dir / name
        if p.exists():
            docs.append(p)
    return docs


def main():
    ap = argparse.ArgumentParser(description="project-mastery 知识库机器校验")
    ap.add_argument("project_root", help="目标项目根目录绝对路径")
    ap.add_argument("--json", action="store_true", help="输出机读 JSON")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.is_dir():
        print(f"错误：{project_root} 不是目录", file=sys.stderr)
        return 2

    kb_dir = project_root / "docs" / "project-knowledge"
    report = Report()

    check_scan_result(report, project_root)
    if kb_dir.exists():
        check_placeholders(report, kb_dir)
        check_dead_links(report, kb_dir)
        check_required_sections(report, kb_dir)
    else:
        report.warn("docs/project-knowledge/ 存在", "KB 目录未生成，仅校验 scan-result.json")

    if args.json:
        print(report.json())
    else:
        print(report.text())
    return report.exit_code()


if __name__ == "__main__":
    sys.exit(main())
