#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 issues/*.md 导入 GitHub：创建标签、里程碑、Issue。

只依赖标准库，不需要 gh CLI。

准备 token（fine-grained PAT，最小权限）:
    Repository permissions:
      - Metadata: Read
      - Contents: Read and write      (推送代码用)
      - Issues: Read and write        (建 issue)
      - Administration: Read and write(仅首次建仓库时需要)

用法:
    # 预览（不调用 API）
    python scripts/create_issues.py --repo taylorgogo/home-collab-robot --dry-run

    # 实际创建（token 从环境变量读，不要写进命令行）
    set GITHUB_TOKEN=github_pat_xxx
    python scripts/create_issues.py --repo taylorgogo/home-collab-robot

    # 首次：先建仓库再导入
    python scripts/create_issues.py --create-repo home-collab-robot --private
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUE_DIR = ROOT / "issues"
API = "https://api.github.com"

LABELS = [
    ("type/task", "1D76DB", "任务"),
    ("type/risk", "D93F0B", "风险"),
    ("type/bug", "B60205", "缺陷"),
    ("type/decision", "5319E7", "需要决策留档"),
    ("area/mech", "C2E0C6", "结构机械"),
    ("area/electrical", "BFDADC", "电子电气"),
    ("area/software", "BFD4F2", "软件与云"),
    ("area/perception", "D4C5F9", "感知与算法"),
    ("area/product", "FBCA04", "产品与需求"),
    ("area/ops", "F9D0C4", "运营与实施"),
    ("area/supply", "E6E6E6", "供应链与制造"),
    ("area/compliance", "FEF2C0", "认证与合规"),
    ("area/test", "D3D3D3", "测试与质量"),
    ("prio/P0", "B60205", "必须，阻塞发布"),
    ("prio/P1", "D93F0B", "重要"),
    ("prio/P2", "FBCA04", "一般"),
    ("prio/P3", "0E8A16", "可延后"),
]

MILESTONES = [
    ("P0-立项与定义", "2027-01-31", "需求冻结、预算批准、不做清单确认"),
    ("P1-关键技术验证", "2027-06-30", "爬楼/抓取/遥操作/安全 四项台架达标"),
    ("P2-A样原型", "2027-11-30", "3 台 A 样整机，100 项功能测试通过率 ≥95%"),
    ("P3-B样试点", "2028-05-31", "2 城市 120 单 + 10 户家庭，任务成功率 ≥85%"),
    ("P4-C样与认证", "2028-10-31", "30 台 C 样 + SRRC/CCC/EMC 齐套"),
    ("P5-量产导入", "2029-01-31", "产线跑通，首批 100 台交付"),
]


def parse_issue(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path.name} 缺少 front-matter")
    meta_text, body = m.group(1), m.group(2)
    meta: dict[str, object] = {}
    for line in meta_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key == "labels":
            meta[key] = [v.strip() for v in value.strip("[]").split(",") if v.strip()]
        else:
            meta[key] = value
    meta["body"] = body.strip()
    return meta


def api(method: str, path: str, token: str, payload: dict | None = None) -> tuple[int, dict]:
    url = path if path.startswith("http") else API + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "homemate-project-bot")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", "replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"message": raw[:300]}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repo", help="owner/name")
    p.add_argument("--create-repo", metavar="NAME", help="先创建仓库")
    p.add_argument("--create-repo-only", action="store_true", help="只创建仓库，不导入 issue")
    p.add_argument("--private", action="store_true", default=True)
    p.add_argument("--public", dest="private", action="store_false")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--only", help="只导入某个阶段，如 P1")
    args = p.parse_args()

    files = sorted(ISSUE_DIR.glob("*.md"))
    issues = [parse_issue(f) for f in files if f.name != "INDEX.md"]
    if args.only:
        issues = [i for i in issues if str(i.get("phase")) == args.only]

    print(f"待导入 {len(issues)} 个 issue，{len(LABELS)} 个标签，{len(MILESTONES)} 个里程碑")

    if args.dry_run:
        for i in issues[:5]:
            print(f"  - [{i['id']}] {i['title']}  labels={i['labels']} milestone={i['milestone']}")
        if len(issues) > 5:
            print(f"  ... 另有 {len(issues) - 5} 个")
        print("dry-run 结束，未调用 API")
        return 0

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("缺少 GITHUB_TOKEN 环境变量", file=sys.stderr)
        return 2

    if args.create_repo:
        status, resp = api(
            "POST", "/user/repos", token,
            {"name": args.create_repo, "private": args.private,
             "description": "家庭互动与工作协作机器人 · 项目单一事实来源",
             "has_issues": True, "has_wiki": False, "auto_init": False},
        )
        if status not in (200, 201):
            print(f"仓库创建失败 {status}: {resp.get('message')}", file=sys.stderr)
            return 1
        args.repo = resp["full_name"]
        print(f"已创建仓库 {args.repo}（{'私有' if args.private else '公开'}）")
        if args.create_repo_only:
            return 0

    if not args.repo or "/" not in args.repo:
        print("需要 --repo owner/name", file=sys.stderr)
        return 2

    ok = 0
    for name, color, desc in LABELS:
        status, resp = api("POST", f"/repos/{args.repo}/labels", token,
                           {"name": name, "color": color, "description": desc})
        ok += status in (200, 201) or status == 422
    print(f"标签就绪 {ok}/{len(LABELS)}")

    milestone_numbers: dict[str, int] = {}
    for title, due, desc in MILESTONES:
        status, resp = api("POST", f"/repos/{args.repo}/milestones", token,
                           {"title": title, "due_on": f"{due}T00:00:00Z", "description": desc})
        if status in (200, 201):
            milestone_numbers[title] = resp["number"]
        elif status == 422:
            s2, r2 = api("GET", f"/repos/{args.repo}/milestones?state=all&per_page=100", token)
            for m in r2 if isinstance(r2, list) else []:
                if m["title"] == title:
                    milestone_numbers[title] = m["number"]
    print(f"里程碑就绪 {len(milestone_numbers)}/{len(MILESTONES)}")

    created = 0
    for i in issues:
        payload = {
            "title": f"[{i['id']}] {i['title']}",
            "body": i["body"],
            "labels": i["labels"],
        }
        ms = milestone_numbers.get(str(i["milestone"]))
        if ms:
            payload["milestone"] = ms
        status, resp = api("POST", f"/repos/{args.repo}/issues", token, payload)
        if status in (200, 201):
            created += 1
            print(f"  ✓ #{resp['number']} [{i['id']}] {i['title']}")
        else:
            print(f"  ✗ [{i['id']}] {status} {resp.get('message')}", file=sys.stderr)
        time.sleep(0.6)

    print(f"完成：创建 {created}/{len(issues)} 个 issue")
    return 0 if created == len(issues) else 1


if __name__ == "__main__":
    raise SystemExit(main())
