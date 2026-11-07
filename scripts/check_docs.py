#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验文档中的关键数字与 data/*.csv 一致。

检查项：
1. docs/04 的 BOM 表格块 与 data/bom.csv 生成结果逐行一致
2. 三档单台成本、研发总投入出现在关键文档中
3. issues/ 的 front-matter 必需字段完整
"""
from __future__ import annotations

import io
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import calc_cost  # noqa: E402

BEGIN = "<!-- BOM:BEGIN -->"
END = "<!-- BOM:END -->"

errors: list[str] = []


def check_bom_table() -> None:
    doc = (ROOT / "docs" / "04-BOM与成本.md").read_text(encoding="utf-8")
    if BEGIN not in doc or END not in doc:
        errors.append("docs/04 缺少 BOM 表格标记 " + BEGIN + " / " + END)
        return
    embedded = doc.split(BEGIN, 1)[1].split(END, 1)[0].strip("\n").splitlines()

    rows = calc_cost.read_csv("bom.csv")
    buf = io.StringIO()
    with redirect_stdout(buf):
        calc_cost.print_bom_md(rows)
    generated = buf.getvalue().strip("\n").splitlines()

    embedded = [ln.rstrip() for ln in embedded]
    generated = [ln.rstrip() for ln in generated]
    if embedded != generated:
        errors.append(
            f"docs/04 的 BOM 表格与 data/bom.csv 不一致（文档 {len(embedded)} 行，"
            f"应为 {len(generated)} 行）。请运行: python scripts/calc_cost.py --bom-md"
        )
        for i, (a, b) in enumerate(zip(embedded, generated)):
            if a != b:
                errors.append(f"  第 {i + 1} 行:\n    文档: {a}\n    应为: {b}")
                break


def check_numbers() -> None:
    rows = calc_cost.read_csv("bom.csv")
    totals = calc_cost.bom_totals(rows)
    base, reserve, total = calc_cost.budget_totals()

    bom_numbers = [calc_cost.money(totals[k]["total"]) for k in ("原型", "小批 100 台", "量产 1000 台")]
    budget_number = f"{total:,.0f}"

    # 需要出现三档单台成本（精确到元）的文件
    for rel in ("docs/04-BOM与成本.md", "docs/05-预算与ROI.md"):
        text = read(rel)
        if text is None:
            continue
        for num in bom_numbers:
            if num not in text:
                errors.append(f"{rel} 缺少单台成本 {num}（请以 data/bom.csv 为准同步）")

    # 需要出现研发总投入的文件
    for rel in ("README.md", "docs/00-项目概览.md", "docs/05-预算与ROI.md"):
        text = read(rel)
        if text is None:
            continue
        if budget_number not in text:
            errors.append(f"{rel} 缺少研发总投入 {budget_number}（预算数据已变更？）")


def read(rel: str) -> str | None:
    path = ROOT / rel
    if not path.exists():
        errors.append(f"缺少文件 {rel}")
        return None
    return path.read_text(encoding="utf-8")


def check_issues() -> None:
    issue_dir = ROOT / "issues"
    files = sorted(p for p in issue_dir.glob("*.md") if p.name != "INDEX.md")
    if not files:
        errors.append("issues/ 为空")
        return
    required = {"title", "labels", "milestone", "estimate"}
    for path in files:
        text = path.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        if not m:
            errors.append(f"{path.name} 缺少 front-matter")
            continue
        keys = {ln.split(":", 1)[0].strip() for ln in m.group(1).splitlines() if ":" in ln}
        missing = required - keys
        if missing:
            errors.append(f"{path.name} front-matter 缺少字段: {sorted(missing)}")
        if "## 验收标准" not in text and "## 验收标准（DoD）" not in text:
            errors.append(f"{path.name} 缺少「验收标准」章节")


def main() -> int:
    check_bom_table()
    check_numbers()
    check_issues()
    if errors:
        print("[FAIL] 文档与数据不一致：", file=sys.stderr)
        for e in errors:
            print(" - " + e, file=sys.stderr)
        return 1
    print("[OK] BOM 表格与 CSV 一致")
    print("[OK] 关键数字已在文档中同步")
    print("[OK] issues front-matter 完整")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
