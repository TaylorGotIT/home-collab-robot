# 一键推送脚本（首次使用）
#
# 用法：
#   .\tools\push.ps1 -RepoUrl https://github.com/<owner>/home-collab-robot.git
#
# 前提：仓库已在 GitHub 上创建（空仓库，不要勾选 README），
#       且本机已配置好凭据（HTTPS 需要 PAT，或使用 SSH 地址）。

param(
    [Parameter(Mandatory = $true)]
    [string]$RepoUrl,

    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "== 1/4 校验文档与数据 ==" -ForegroundColor Cyan
python scripts/calc_cost.py --check
python scripts/check_docs.py

Write-Host "== 2/4 检查工作区 ==" -ForegroundColor Cyan
$dirty = git status --porcelain
if ($dirty) {
    Write-Host "工作区有未提交改动，请先提交：" -ForegroundColor Yellow
    Write-Host $dirty
    exit 1
}

Write-Host "== 3/4 配置 remote ==" -ForegroundColor Cyan
$existing = git remote 2>$null
if ($existing -contains "origin") {
    git remote set-url origin $RepoUrl
} else {
    git remote add origin $RepoUrl
}
git remote -v

Write-Host "== 4/4 推送 ==" -ForegroundColor Cyan
git push -u origin $Branch

Write-Host ""
Write-Host "推送完成。下一步：" -ForegroundColor Green
Write-Host "  1) 在 GitHub 仓库 Settings -> Branches 给 main 加保护规则"
Write-Host "  2) 设置 GITHUB_TOKEN 后运行：python scripts/create_issues.py --repo <owner>/home-collab-robot"
Write-Host "  3) 在 Projects 里新建看板，按 milestone 分组"
