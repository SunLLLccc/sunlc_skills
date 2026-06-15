#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_ai_generated_block.py — KB 文档 AI/HUMAN 双区增量更新（stdlib 无依赖）

双区约定（详见 references/dual-zone-convention.md）：

    <!-- AI-GENERATED:<section-id> START -->
    ...AI 生成的内容（【更新】子流程可整块替换）...
    <!-- AI-GENERATED:<section-id> END -->

    <!-- HUMAN-NOTES:<section-id> START -->
    ...人工补充（永不被 AI 覆盖）...
    <!-- HUMAN-NOTES:<section-id> END -->

三种模式：
    --init            给一份无标记的文档注入默认骨架（按一级标题切 section，
                      每个 ## 一节 AI-GENERATED 块 + 空 HUMAN-NOTES 块）
    --section ID --ai-file F [--dry-run]
                      用 F 的内容替换该 section 的 AI-GENERATED 块；
                      HUMAN-NOTES 块原样保留；块外的人工编辑不动；
                      --dry-run 只打印 diff 不写盘
    --list            列出文档里所有已标记的 section id

面向内网 qwen3.6 35b 小模型——【更新】时只喂 AI 区 + 相关证据、不喂整篇文档（P1-1）。
人工补充物理隔离，小模型重生成不会覆盖。
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

START_RE = re.compile(
    r"<!--\s*(AI-GENERATED|HUMAN-NOTES):([^\s]+)\s+START\s*-->"
)
END_RE = re.compile(
    r"<!--\s*(AI-GENERATED|HUMAN-NOTES):([^\s]+)\s+END\s*-->"
)


def _find_blocks(text):
    """返回 {section_id: {kind: (start_match_end, end_match_start, end_match_end)}}。"""
    blocks = {}
    pos = 0
    open_stack = []
    while True:
        m = START_RE.search(text, pos)
        if not m:
            break
        kind, sid = m.group(1), m.group(2)
        # 找对应的 END（同 kind+sid）
        end_pat = re.compile(
            rf"<!--\s*{re.escape(kind)}:{re.escape(sid)}\s+END\s*-->"
        )
        em = end_pat.search(text, m.end())
        if not em:
            raise ValueError(f"未闭合的块：{kind}:{sid}（有 START 无 END）")
        blocks.setdefault(sid, {})[kind] = {
            "start_line_end": m.end(),      # START 标记后的位置
            "start_match_start": m.start(),
            "content_start": m.end(),
            "content_end": em.start(),
            "end_match_end": em.end(),
        }
        pos = em.end()
    return blocks


def cmd_list(args):
    text = Path(args.doc).read_text(encoding="utf-8")
    try:
        blocks = _find_blocks(text)
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 2
    if not blocks:
        print("（无已标记 section）")
        return 0
    for sid, kinds in sorted(blocks.items()):
        has_ai = "AI-GENERATED" in kinds
        has_human = "HUMAN-NOTES" in kinds
        print(f"{sid}\tAI={'有' if has_ai else '无'}\tHUMAN={'有' if has_human else '无'}")
    return 0


def cmd_init(args):
    """按一级/二级标题切 section，注入 AI-GENERATED + HUMAN-NOTES 骨架。"""
    path = Path(args.doc)
    text = path.read_text(encoding="utf-8")
    if START_RE.search(text):
        print("文档已含双区标记，拒绝重复 --init（先用 --list 查看）", file=sys.stderr)
        return 2
    lines = text.splitlines(keepends=True)
    out = []
    # 简单策略：每个 `## ` 二级标题开一个 section；标题行之前的内容（含 # 一级标题）
    # 归入一个 "header" section。section id 取标题文本的 slug。
    current_header_buf = []
    sections = []

    def slug(line):
        s = line.lstrip("#").strip()
        s = re.sub(r"[^\w一-鿿]+", "-", s).strip("-")
        return s or "section"

    for line in lines:
        if line.startswith("## "):
            # 收尾上一个 section
            if current_header_buf:
                sections.append(("header" if not sections else sections[-1][0], current_header_buf))
                current_header_buf = []
            sid = slug(line)
            sections.append((sid, [line]))
        elif line.startswith("# ") and not sections:
            current_header_buf.append(line)
        else:
            if sections:
                sections[-1][1].append(line)
            else:
                current_header_buf.append(line)
    if current_header_buf:
        sid = "header"
        sections.append((sid, current_header_buf))

    seen = {}
    for sid, body in sections:
        # 去重 sid
        base = sid
        while sid in seen:
            seen[base] += 1
            sid = f"{base}-{seen[base]}"
        seen[sid] = 0
        body_str = "".join(body).rstrip("\n")
        out.append(f"<!-- AI-GENERATED:{sid} START -->")
        out.append(body_str)
        out.append(f"<!-- AI-GENERATED:{sid} END -->")
        out.append("")
        out.append(f"<!-- HUMAN-NOTES:{sid} START -->")
        out.append(f"<!-- HUMAN-NOTES:{sid} END -->")
        out.append("")

    new_text = "\n".join(out) + "\n"
    if args.dry_run:
        _print_diff(text, new_text, path.name)
        return 0
    path.write_text(new_text, encoding="utf-8")
    print(f"已注入 {len(seen)} 个 section 的双区标记到 {path}")
    return 0


def cmd_update(args):
    path = Path(args.doc)
    text = path.read_text(encoding="utf-8")
    try:
        blocks = _find_blocks(text)
    except ValueError as e:
        print(f"错误：{e}", file=sys.stderr)
        return 2
    sid = args.section
    if sid not in blocks or "AI-GENERATED" not in blocks[sid]:
        print(f"错误：section '{sid}' 无 AI-GENERATED 块（用 --list 查看已有 section，或 --init 注入骨架）",
              file=sys.stderr)
        return 2
    new_ai = Path(args.ai_file).read_text(encoding="utf-8").rstrip("\n")
    ai = blocks[sid]["AI-GENERATED"]
    # 替换 content_start..content_end 之间的内容
    new_text = (
        text[: ai["content_start"]]
        + "\n" + new_ai + "\n"
        + text[ai["content_end"]:]
    )
    # 校验：替换后块结构仍闭合
    try:
        _find_blocks(new_text)
    except ValueError as e:
        print(f"错误：替换后块结构损坏：{e}", file=sys.stderr)
        return 2
    if args.dry_run:
        _print_diff(text, new_text, path.name)
        return 0
    path.write_text(new_text, encoding="utf-8")
    # 报告 HUMAN-NOTES 是否保留
    human_kept = sid in blocks and "HUMAN-NOTES" in blocks[sid]
    print(f"已更新 {path} 的 section '{sid}' AI-GENERATED 块"
          + ("（HUMAN-NOTES 块原样保留）" if human_kept else ""))
    return 0


def _print_diff(old, new, name):
    diff = difflib.unified_diff(
        old.splitlines(keepends=True),
        new.splitlines(keepends=True),
        fromfile=f"{name} (旧)",
        tofile=f"{name} (新)",
        n=3,
    )
    out = sys.stdout
    for line in diff:
        out.write(line if line.endswith("\n") else line + "\n")


def main():
    ap = argparse.ArgumentParser(
        description="KB 文档 AI/HUMAN 双区增量更新",
        usage="%(prog)s <doc> (--init | --list | --section ID --ai-file F) [--dry-run]",
    )
    ap.add_argument("doc", help="目标 KB 文档路径")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--init", action="store_true", help="注入默认双区骨架（按标题切 section）")
    mode.add_argument("--list", action="store_true", help="列出文档里已标记的 section id")
    mode.add_argument("--section", metavar="ID", help="更新模式：替换该 section 的 AI-GENERATED 块")
    ap.add_argument("--ai-file", help="更新模式：新 AI 内容文件路径（与 --section 配合）")
    ap.add_argument("--dry-run", action="store_true", help="只打印 diff，不写盘")
    args = ap.parse_args()

    if args.init:
        return cmd_init(args)
    if args.list:
        return cmd_list(args)
    if args.section:
        if not args.ai_file:
            ap.error("--section 需配合 --ai-file")
        return cmd_update(args)
    ap.error("需要指定模式：--init / --list / --section")


if __name__ == "__main__":
    sys.exit(main())
