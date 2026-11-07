#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/*.csv 计算 BOM 与预算汇总，输出 Markdown 表格。

用法:
    python scripts/calc_cost.py            # 打印汇总表格
    python scripts/calc_cost.py --check    # 只做一致性校验（CI 用）
    python scripts/calc_cost.py --write    # 把汇总写回 docs/_cost-summary.md

数据是唯一事实来源：文档里的数字应当与此脚本输出一致。
"""
from __future__ import annotations

import argparse
import csv
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

TIERS = [
    ("原型", "unit_proto", Decimal("0.08")),
    ("小批 100 台", "unit_small", Decimal("0.05")),
    ("量产 1000 台", "unit_mass", Decimal("0.03")),
]


def read_csv(name: str) -> list[dict]:
    with (DATA / name).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def money(v: Decimal) -> str:
    return f"{v:,.0f}"


def yuan_wan(v: Decimal) -> str:
    return f"{v / 10000:.1f}"


def bom_totals(rows: list[dict]) -> dict[str, dict[str, Decimal]]:
    out: dict[str, dict[str, Decimal]] = {}
    for label, field, spare_rate in TIERS:
        bom = sum(Decimal(r["qty"]) * Decimal(r[field]) for r in rows)
        spares = bom * spare_rate
        out[label] = {
            "bom": bom,
            "spares": spares,
            "total": bom + spares,
            "spare_rate": spare_rate,
        }
    return out


def print_bom(rows: list[dict], totals: dict) -> None:
    print("\n## BOM 汇总（元/台，含税估算）\n")
    print("| 版本 | BOM 小计 | 备件损耗 | 单台成本 | 折合万元 |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for label, _, spare_rate in TIERS:
        t = totals[label]
        print(
            f"| {label} | {money(t['bom'])} | {money(t['spares'])} "
            f"({spare_rate:.0%}) | {money(t['total'])} | {yuan_wan(t['total'])} |"
        )

    print("\n## 分系统成本占比（原型机）\n")
    print("| 分系统 | 原型小计 | 占比 | 量产小计 | 占比 |")
    print("| --- | ---: | ---: | ---: | ---: |")
    systems: dict[str, list[Decimal]] = {}
    for r in rows:
        systems.setdefault(r["system"], [Decimal(0), Decimal(0)])
        systems[r["system"]][0] += Decimal(r["qty"]) * Decimal(r["unit_proto"])
        systems[r["system"]][1] += Decimal(r["qty"]) * Decimal(r["unit_mass"])
    proto_total = totals["原型"]["bom"]
    mass_total = totals["量产 1000 台"]["bom"]
    for name, (p, m) in sorted(systems.items(), key=lambda kv: -kv[1][0]):
        print(
            f"| {name} | {money(p)} | {p / proto_total:.1%} | "
            f"{money(m)} | {m / mass_total:.1%} |"
        )


def print_bom_md(rows: list[dict]) -> None:
    """输出可直接粘进 Markdown 的完整 BOM 表。"""
    print("| ID | 分系统 | 物料 | 关键规格 | 数量 | 原型单价 | 原型小计 | 小批单价 | 量产单价 |")
    print("| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for r in rows:
        qty = Decimal(r["qty"])
        proto = qty * Decimal(r["unit_proto"])
        print(
            f"| {r['id']} | {r['system']} | {r['name']} | {r['spec']} | {qty:.0f} | "
            f"{money(Decimal(r['unit_proto']))} | {money(proto)} | "
            f"{money(Decimal(r['unit_small']))} | {money(Decimal(r['unit_mass']))} |"
        )


def budget_totals() -> tuple[Decimal, Decimal, Decimal]:
    rows = read_csv("budget.csv")
    base = sum(Decimal(r["amount_wan"]) for r in rows if r["code"] != "H")
    reserve = sum(Decimal(r["amount_wan"]) for r in rows if r["code"] == "H")
    return base, reserve, base + reserve


def print_budget() -> None:
    rows = read_csv("budget.csv")
    base, reserve, total = budget_totals()
    print("\n## 研发预算（万元）\n")
    print("| 科目 | 内容 | 金额 | 占基线 |")
    print("| --- | --- | ---: | ---: |")
    for r in rows:
        share = f"{Decimal(r['amount_wan']) / base:.1%}" if r["code"] != "H" else "—"
        print(f"| {r['code']} {r['item']} | {r['detail']} | {r['amount_wan']} | {share} |")
    print(f"| **合计** | 基线 {base} + 预备费 {reserve} | **{total}** | 100% |")


def print_roi() -> None:
    rows = {r["metric"]: r for r in read_csv("roi.csv") if r["scenario"] == "网络上门安装"}
    key = "单次服务成本"
    print("\n## 网络上门安装单次成本（元/单）\n")
    print(f"人工外包基线：{rows[key]['human_baseline']} 元/单")
    for col, label in [
        ("robot_conservative", "保守"),
        ("robot_base", "中性"),
        ("robot_optimistic", "乐观"),
    ]:
        cost = Decimal(rows[key][col])
        baseline = Decimal(rows[key]["human_baseline"])
        print(f"- {label}：{cost} 元，为外包的 {cost / baseline:.0%}")


LITE_TIERS = [
    ("L0 遥控分身", "L0"),
    ("L1 会拿东西", "L1"),
    ("L2 能上楼", "L2"),
]


def lite_totals(rows: list[dict] | None = None) -> dict[str, Decimal]:
    rows = rows if rows is not None else read_csv("bom-lite.csv")
    out: dict[str, Decimal] = {}
    for label, code in LITE_TIERS:
        out[label] = sum(
            Decimal(r["qty"]) * Decimal(r["price"]) for r in rows if code in r["tiers"].split(";")
        )
    return out


def print_lite() -> dict[str, Decimal]:
    rows = read_csv("bom-lite.csv")
    totals = lite_totals(rows)

    print("\n## 个人版三档合计（元）\n")
    print("| 档位 | 买到什么 | 合计 |")
    print("| --- | --- | ---: |")
    desc = {
        "L0 遥控分身": "能走、能看、能通话",
        "L1 会拿东西": "L0 + 4DOF 臂 + 升降 + 雷达 + 深度相机",
        "L2 能上楼": "L1 + 履带爬楼轮椅底盘（替换普通轮椅）",
    }
    for label, _ in LITE_TIERS:
        print(f"| {label} | {desc[label]} | {money(totals[label])} |")

    print("\n## 个人版物料明细\n")
    print("| 类别 | 物料 | 规格 | 数量 | 单价 | L0 | L1 | L2 |")
    print("| --- | --- | --- | ---: | ---: | :-: | :-: | :-: |")
    for r in rows:
        tiers = r["tiers"].split(";")
        marks = ["●" if t in tiers else "" for t in ("L0", "L1", "L2")]
        print(
            f"| {r['category']} | {r['item']} | {r['spec']} | {r['qty']} | "
            f"{money(Decimal(r['price']))} | {marks[0]} | {marks[1]} | {marks[2]} |"
        )
    return totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--bom-md", action="store_true")
    parser.add_argument("--lite", action="store_true")
    args = parser.parse_args()

    if args.lite:
        print_lite()
        return 0

    rows = read_csv("bom.csv")
    totals = bom_totals(rows)

    if args.bom_md:
        print_bom_md(rows)
        return 0

    # 一致性校验：预算表 H 项必须等于基线 8%
    base, reserve, total = budget_totals()
    expected = (base * Decimal("0.08")).quantize(Decimal("1"))
    if reserve != expected:
        print(f"[FAIL] 预备费 {reserve} 与基线 8%({expected}) 不一致", file=sys.stderr)
        return 1
    # 一致性校验：合计应为整数万元区间
    if not Decimal("2000") <= total <= Decimal("3000"):
        print(f"[WARN] 总投入 {total} 万元超出 2000-3000 万合理区间", file=sys.stderr)

    if args.check:
        print(f"[OK] BOM {len(rows)} 行，原型 {yuan_wan(totals['原型']['total'])} 万元/台")
        print(f"[OK] 预算基线 {base} 万 + 预备费 {reserve} 万 = {total} 万元")
        print("[OK] 数据一致")
        return 0

    print_bom(rows, totals)
    print_budget()
    print_roi()

    if args.write:
        # 供文档引用的小结
        out = ROOT / "docs" / "_cost-summary.md"
        out.parent.mkdir(exist_ok=True)
        lines = [
            "<!-- 由 scripts/calc_cost.py 生成，请勿手改 -->",
            "",
            "| 版本 | 单台成本（元） | 折合万元 |",
            "| --- | ---: | ---: |",
        ]
        for label, _, _ in TIERS:
            t = totals[label]
            lines.append(f"| {label} | {money(t['total'])} | {yuan_wan(t['total'])} |")
        lines.append("")
        lines.append(f"研发总投入：基线 {base} 万元 + 预备费 {reserve} 万元 = **{total} 万元**")
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n已写入 {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
