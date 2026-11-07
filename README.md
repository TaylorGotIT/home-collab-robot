# 家庭互动与工作协作机器人 · Project HomeMate

[![docs-check](https://github.com/TaylorGotIT/home-collab-robot/actions/workflows/ci.yml/badge.svg)](https://github.com/TaylorGotIT/home-collab-robot/actions/workflows/ci.yml)
[![Issues](https://img.shields.io/github/issues/TaylorGotIT/home-collab-robot)](https://github.com/TaylorGotIT/home-collab-robot/issues)
[![Milestones](https://img.shields.io/github/milestones/all/TaylorGotIT/home-collab-robot)](https://github.com/TaylorGotIT/home-collab-robot/milestones)

> 一台**可远程接管的轮式移动操作机器人**：在家陪老人孩子、搭把手；出门替我们上门装路由器、跑现场。
> 这个仓库是本项目的**单一事实来源（SSOT）**——需求、方案、BOM、预算、排期、风险、认证、任务清单全部在此，不再另建 Word/Excel 文档。

---

## 一页看懂

| 指标 | 数值 | 说明 |
| --- | ---: | --- |
| 单台成本（原型 / 小批 100 台 / 量产 1000 台） | **10.6 / 6.5 / 4.1 万元** | 含税 BOM + 装配 + 备件损耗，不含研发摊销 |
| 研发总投入 | **2,495 万元** | 基线 2,310 万 + 8% 预备费，26 个月 |
| 团队规模 | 12 → 24 人（540 人月） | 峰值在 C 样与认证阶段 |
| 上市节奏 | A 样 12 个月 / B 样试点 18 个月 / 小批 23 个月 / 量产 26 个月 | 见 [开发计划](docs/06-开发计划.md) |
| 工作场景单次服务成本 | **118 元/单**（区间 64–245） | 对标人工外包 500 元/单 |
| 单台回本月数 | **7 个月**（区间 4–17） | 按对外报价 300 元/单、日均 2.5 单 |

## 为什么做

现有机器人厂家分两类：**玩具/教育**（便宜但没用）和**工业/人形**（有用但进不了家）。中间那段——"能替人跑一趟、能在家里搭把手"的**移动操作机器人**——几乎是空白。

而我们手里有两个别人没有的条件：

1. **真实的高频付费场景**：网络上门安装，外包 500 元/次，动作标准化到"放设备、接电源、插网线、接 console"。这是机器人的天然训练场和现金流。
2. **真实的高频情感场景**：异地子女愿意为"随时看到、随时帮上"付费，而这件事的技术门槛远低于"全自主家政"。

## 我们的核心判断（也是本项目的立项理由）

1. **不做"全自主家政机器人"，做"可远程接管的分身机器人"。** 全自主是十年工程，远程接管是两年工程；而 80% 的真实需求，本质是"我想在场但我到不了"。
2. **先工后家，一套硬件、两套软件。** 工作场景付费方明确、场景标准化、容错率高；用它的收入和真实数据养家庭场景。
3. **六类需求里，四类现在就能做，两类必须限定条件，两类三年内不做。** 详见[能力矩阵](docs/01-可行性分析.md#三12-项能力逐条评级)。
4. **成本不是瓶颈，单量与人力配比才是。** 敏感性分析显示：硬件降价 20% 只影响单次成本 8%，而"一人管几台"能把单次成本改变 2 倍。
5. **合规与安全责任是硬门槛，不是流程。** 搀扶老人一旦出事，赔的是公司；所以它被设计成"有人监护下的辅助站立"，而不是"抱起转移"。

## 仓库结构

```
.
├─ docs/                 # 项目文档（人读的唯一入口）
│  ├─ 00-项目概览.md      # 一页纸结论，先读这个
│  ├─ 01-可行性分析.md    # 12 项能力评级 + 技术/商业/合规论证
│  ├─ 02-场景与需求.md    # 用户画像、场景剧本、不做清单、KPI
│  ├─ 03-技术方案.md      # 架构、规格、分系统选型、遥操作与安全
│  ├─ 04-BOM与成本.md     # 三档 BOM、成本占比、降本路径
│  ├─ 05-预算与ROI.md     # 研发预算、单台经济模型、敏感性分析
│  ├─ 06-开发计划.md      # 26 个月排期、里程碑 gate、关键路径
│  ├─ 07-风险登记册.md    # 14 项风险 + Top5 深挖
│  └─ 08-认证与合规.md    # 认证清单、数据合规、责任边界
├─ data/                 # 机器可读的数据源（CSV，文档数字的唯一来源）
│  ├─ bom.csv            # 物料清单，三档单价
│  ├─ budget.csv         # 研发预算
│  ├─ schedule.csv       # 阶段与里程碑
│  ├─ risks.csv          # 风险登记册
│  ├─ capabilities.csv   # 能力矩阵
│  └─ roi.csv            # 经济模型假设与结果
├─ issues/               # 任务清单（GitHub Issue 的源文件，含 front-matter）
├─ scripts/
│  ├─ calc_cost.py       # 由 CSV 计算 BOM/预算汇总
│  ├─ check_docs.py      # 文档与数据一致性校验（CI 用）
│  ├─ gen_issues.py      # 生成 issues/*.md 与索引
│  └─ create_issues.py   # 导入标签/里程碑/Issue（纯标准库调 REST API）
├─ tools/setup-github.ps1 # 一键上线脚本（三种鉴权路径）
└─ .github/              # Issue 模板、PR 模板、CI、bootstrap-issues 工作流
```

## 从哪里开始读

- **只想看结论** → [`docs/00-项目概览.md`](docs/00-项目概览.md)
- **要拍板投不投** → [`docs/01-可行性分析.md`](docs/01-可行性分析.md) + [`docs/05-预算与ROI.md`](docs/05-预算与ROI.md)
- **要报价/采购** → [`docs/04-BOM与成本.md`](docs/04-BOM与成本.md)
- **要排期/带队** → [`docs/06-开发计划.md`](docs/06-开发计划.md) + [`issues/`](issues/)
- **关心合规** → [`docs/08-认证与合规.md`](docs/08-认证与合规.md)

## 里程碑

| 编号 | 里程碑 | 时间 | 通过标准（Gate） | 状态 |
| --- | --- | --- | --- | --- |
| M2 | 需求冻结 | 2027-01 | PRD v1.0 签署，不做清单确认 | ⬜ |
| M7 | 关键技术评审 | 2027-06 | 爬楼/抓取/遥操作/安全 四项台架达标 | ⬜ |
| M12 | A 样内部验收 | 2027-11 | 3 台整机，100 项功能测试通过率 ≥95% | ⬜ |
| M18 | 试点复盘 | 2028-05 | 2 城市 120 单 + 10 户家庭，任务成功率 ≥85% | ⬜ |
| M23 | 认证齐套 | 2028-10 | SRRC/CCC/EMC/可靠性报告齐全，500h 无致命故障 | ⬜ |
| M26 | SOP 首批交付 | 2029-01 | 产线跑通，首批 100 台交付 | ⬜ |

## 数据怎么改

文档里所有金额、成本、排期数字都来自 `data/*.csv`。**改数据，不改文档**：

```bash
python scripts/calc_cost.py          # 查看最新汇总
python scripts/calc_cost.py --check  # CI 用：校验预算与 BOM 一致性
```

CI 会在每次 push 时跑 `--check`，数据与文档不一致会直接失败。

## 上线到 GitHub（三种方式，任选其一）

仓库已在本地提交完毕，随时可推。

### 路径 A · 全程不用 token（推荐）

1. 在 GitHub 网页新建**空仓库** `home-collab-robot`（公开，不要勾选 README / .gitignore）。
2. 在本目录执行：

```powershell
git remote add origin https://github.com/<你的用户名>/home-collab-robot.git
git push -u origin main
```

首次 push 会弹出浏览器登录窗口（Git Credential Manager），登录后自动完成推送——**不需要手工创建 PAT**。

3. 打开仓库 **Actions → bootstrap-issues → Run workflow**。
   工作流会用 Actions 自带的 `GITHUB_TOKEN` 自动创建 **17 个标签、6 个里程碑、31 个 Issue**，同样不需要你的 PAT。

### 路径 B · 一条命令全自动（需要 PAT）

```powershell
$env:GITHUB_TOKEN = "github_pat_xxx"
$env:GITHUB_OWNER = "<你的用户名>"
.\tools\setup-github.ps1 -CreateRepo home-collab-robot
```

PAT 只需 4 项权限：Metadata 读、Contents 读写、Issues 读写、Administration 读写。**用完立即删除**。

### 路径 C · 只推代码，Issue 以后再说

```powershell
.\tools\setup-github.ps1 -RepoUrl https://github.com/<你的用户名>/home-collab-robot.git -SkipIssues
```

### 上线后建议做的三件事

1. **Settings → Branches**：给 `main` 加保护，要求 PR + `docs-check` 通过。
2. **Projects**：新建 Board 视图，按 Milestone 分组，就是项目看板。
3. **Actions**：确认 `docs-check` 已启用，之后每次改数据都会被校验。

## 如何参与

见 [CONTRIBUTING.md](CONTRIBUTING.md)。任务从 [`issues/`](issues/) 领，按 `P0 → P1` 顺序推进，每个阶段结束跑一次 gate 评审。

## 免责与边界

本仓库是**立项阶段的工程与商业评估**，不是产品承诺。所有价格为 2026 年国内市场的**估算区间中值**，需以实际询价为准；认证标准号需复核最新有效版本；涉及老人的功能均以"辅助、有人监护"为前提，不构成医疗或照护承诺。
