# 贡献指南

> 这个仓库是项目的**单一事实来源**。文档过期比没有文档更糟——所以有了 CI 校验。

## 一、开始之前

```bash
git clone <repo-url>
cd home-collab-robot
python scripts/calc_cost.py        # 看看数字对不对
python scripts/check_docs.py       # 跑一遍校验
```

只需要 Python 3.10+，无第三方依赖（`calc_cost.py` 只用了标准库）。

## 二、分支模型

| 分支 | 用途 | 生命周期 |
| --- | --- | --- |
| `main` | 稳定，受保护，只接受 PR | 长期 |
| `feat/<issue-id>-<slug>` | 新功能/新文档 | 合并后删除 |
| `fix/<issue-id>-<slug>` | 修 bug/修数据 | 合并后删除 |
| `data/<slug>` | 只改 `data/*.csv` 的变更 | 合并后删除 |

`main` 保护规则：禁止直推、至少 1 个 approve、CI 必须绿。

## 三、提交信息

```
<type>(<scope>): <subject>

type:  feat | fix | docs | data | chore | test
scope: mech | elec | sw | algo | ops | cost | risk | doc
```

例：

```
data(bom): 按 3 家报价更新机械臂小批单价 12000 -> 11500
docs(risk): 新增 R-15 认证代理更换风险
feat(sw): 接管客户端支持断线自动重连
```

## 四、改数字的唯一正确姿势

**永远不要直接改文档里的数字。**

```bash
# 1. 改数据
vim data/bom.csv

# 2. 重算并生成表格
python scripts/calc_cost.py --bom-md   # 输出 BOM 表格，粘回 docs/04 的 BOM:BEGIN/END 之间

# 3. 校验
python scripts/check_docs.py
```

`check_docs.py` 会检查：

- `docs/04` 的 BOM 表格块是否与 `data/bom.csv` 逐行一致
- 三档单台成本是否出现在 `docs/04`、`docs/05`
- 研发总投入是否出现在 `README`、`docs/00`、`docs/05`
- `issues/*.md` 的 front-matter 是否完整

CI 会跑同样的检查，不一致直接失败。

## 五、Issue 规范

`issues/*.md` 是 GitHub Issue 的源文件，必须包含 front-matter：

```yaml
---
id: P1-02
title: 爬楼台架搭建与 500 次循环测试
labels: [type/task, area/mech, prio/P0]
milestone: P1-关键技术验证
estimate: 25d
phase: P1
depends: P1-01
---
```

正文必须包含 `## 背景`、`## 交付物`、`## 验收标准（DoD）`、`## 依赖`。

导入 GitHub：

```bash
python scripts/create_issues.py --dry-run   # 先看会建什么
python scripts/create_issues.py             # 需要 GITHUB_TOKEN
```

## 六、PR 规范

- 标题与提交信息规范一致
- 描述里写 `Closes #<issue>`
- 涉及以下内容的 PR 需要 **2 个 approve**：
  - 安全模块（急停/抱闸/限速/围栏）
  - 搀扶、入室类功能定义
  - `docs/03` 的技术方案变更
- 涉及 `data/*.csv` 的 PR 必须在描述里贴 `calc_cost.py` 的输出

## 七、决策记录（ADR）

任何"改变方向"的决定——技术路线、场景取舍、成本目标调整——都要写 ADR：

```
docs/adr/0003-爬楼作为选配模块.md
```

格式：`状态 / 背景 / 决策 / 代价 / 替代方案 / 影响`。不要写"我们决定做 X"，要写"为什么不是 Y"。

## 八、评审原则

| 原则 | 说明 |
| --- | --- |
| 数据说话 | "感觉快"不算理由，要有采样数据 |
| 不做清单优先 | 新增功能前先确认它不在不做清单里 |
| 安全不妥协 | 任何为降本砍安全模块的提案直接否 |
| 可回滚 | 结构性变更要有回退方案 |
