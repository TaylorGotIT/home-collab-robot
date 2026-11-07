# GitHub 一键上线脚本
#
# 三条路径，任选其一：
#
#  A) 不用 token（浏览器登录）
#     .\tools\setup-github.ps1 -RepoUrl https://github.com/<owner>/home-collab-robot.git
#     → git push 时会弹出 GitHub 登录窗口（Git Credential Manager），登录后自动推送
#
#  B) 带 token，建仓库 + 推送 + 建 Issue 全自动
#     $env:GITHUB_TOKEN = "github_pat_xxx"
#     .\tools\setup-github.ps1 -CreateRepo home-collab-robot -Private:$false
#
#  C) 只预览，不动网络
#     .\tools\setup-github.ps1 -RepoUrl https://github.com/<owner>/home-collab-robot.git -DryRun

param(
    [string]$RepoUrl,
    [string]$CreateRepo,
    [switch]$Private,
    [switch]$SkipIssues,
    [switch]$DryRun,
    [string]$Branch = "main"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

# 让 Python 的中文输出在 Windows 控制台不乱码
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = "utf-8"

function Resolve-Python {
    foreach ($cand in @("python", "py")) {
        $cmd = Get-Command $cand -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $probe = $cand
        if ($cand -eq "py") { $probe = "py -3" }
        & $cmd.Source --version *> $null
        if ($LASTEXITCODE -eq 0) { return $cmd.Source }
    }
    $bundled = Join-Path $env:USERPROFILE ".dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $bundled) { return $bundled }
    throw "未找到 Python 3.10+，请先安装：https://www.python.org/downloads/"
}

$PY = Resolve-Python
Write-Host "使用 Python：$PY" -ForegroundColor DarkGray

function Step($n, $text) { Write-Host "`n== $n  $text ==" -ForegroundColor Cyan }

Step "1/5" "校验文档与数据"
& $PY scripts/calc_cost.py --check
& $PY scripts/check_docs.py
if ($LASTEXITCODE -ne 0) { throw "校验失败，先修数据再推送" }

Step "2/5" "检查工作区"
$dirty = git status --porcelain
if ($dirty) {
    Write-Host "有未提交改动：" -ForegroundColor Yellow
    Write-Host $dirty
    throw "请先提交（git add -A; git commit -m ...）"
}
Write-Host "干净，$(git rev-list --count HEAD) 个提交待推送"

Step "3/5" "确定目标仓库"
if ($CreateRepo) {
    if (-not $env:GITHUB_TOKEN) { throw "-CreateRepo 需要 GITHUB_TOKEN" }
    if (-not $env:GITHUB_OWNER) { throw "请设置 `$env:GITHUB_OWNER = '你的用户名'（或改用 -RepoUrl）" }
    $RepoUrl = "https://github.com/$env:GITHUB_OWNER/$CreateRepo.git"
    Write-Host "将创建并推送到 $RepoUrl"
} elseif (-not $RepoUrl) {
    throw "需要 -RepoUrl 或 -CreateRepo"
} else {
    Write-Host "目标：$RepoUrl"
}

if ($DryRun) {
    Write-Host "`n[dry-run] 以下动作将被跳过：git remote 配置、push、issue 创建" -ForegroundColor Yellow
    Write-Host "  git remote add origin $RepoUrl"
    Write-Host "  git push -u origin $Branch"
    if (-not $SkipIssues) { Write-Host "  python scripts/create_issues.py --repo <owner>/<name>" }
    exit 0
}

Step "4/5" "配置 remote 并推送"
if ($CreateRepo) {
    $vis = if ($Private) { "--private" } else { "--public" }
    & $PY scripts/create_issues.py --create-repo $CreateRepo --create-repo-only --repo "$env:GITHUB_OWNER/$CreateRepo" $vis
    if ($LASTEXITCODE -ne 0) { throw "仓库创建失败" }
}
$existing = git remote 2>$null
if ($existing -contains "origin") { git remote set-url origin $RepoUrl } else { git remote add origin $RepoUrl }
git remote -v
git push -u origin $Branch
if ($LASTEXITCODE -ne 0) { throw "推送失败：检查仓库是否已在 GitHub 创建，或登录凭据是否有效" }

Step "5/5" "创建标签、里程碑与 Issue"
if ($SkipIssues) {
    Write-Host "已跳过（-SkipIssues）"
} elseif ($env:GITHUB_TOKEN) {
    $slug = ($RepoUrl -replace '^https://github.com/', '' -replace '\.git$', '')
    & $PY scripts/create_issues.py --repo $slug
} else {
    Write-Host "未检测到 GITHUB_TOKEN，跳过 Issue 创建。" -ForegroundColor Yellow
    Write-Host "之后补跑："
    Write-Host "  `$env:GITHUB_TOKEN='github_pat_xxx'; python scripts/create_issues.py --repo <owner>/home-collab-robot"
}

Write-Host "`n完成。" -ForegroundColor Green
Write-Host "建议后续："
Write-Host "  1) Settings → Branches：给 main 加保护（要求 PR + CI 通过）"
Write-Host "  2) Projects → 新建看板，按 Milestone 分组，视图选 Board"
Write-Host "  3) Actions：确认 docs-check 工作流已启用"
