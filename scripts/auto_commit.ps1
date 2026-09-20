# Auto-commit + push runner for PYRPG, invoked on a schedule by the
# "PYRPG-AutoCommit" Windows Scheduled Task (see scripts/auto_commit_task.xml).
#
# Safety gate: only commits/pushes if `python -c "import game.pyrpg"` still
# succeeds, so an obviously broken working tree never reaches GitHub unattended.
# There is no test suite in this repo (see CLAUDE.md) -- this import check is
# the only automated gate, it does NOT verify gameplay correctness.

$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $PSScriptRoot "auto_commit.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp  $Message" | Out-File -FilePath $LogFile -Append -Encoding utf8
}

Set-Location $RepoRoot

# Only run while actively working -- skip entirely if neither VS Code nor Claude Code is open
$isActive = (Get-Process -Name "Code" -ErrorAction SilentlyContinue) -or (Get-Process -Name "claude" -ErrorAction SilentlyContinue)
if (-not $isActive) {
    Write-Log "Neither VS Code nor Claude Code is running, skipping."
    exit 0
}

# Nothing to do if the working tree is clean
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Log "No changes, skipping."
    exit 0
}

# Prefer the project venv's Python if it exists, else fall back to PATH
$venvPython = Join-Path $RepoRoot "venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { "python" }

# Safety gate: skip commit/push entirely if the game doesn't even import
& $python -c "import game.pyrpg" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Log "Import check FAILED -- skipping commit/push. Working tree left as-is."
    exit 1
}

git add -A

# git diff --cached --quiet exits 1 if there IS staged content to commit
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Log "Nothing staged after add (e.g. only ignored files changed), skipping."
    exit 0
}

$branch = git rev-parse --abbrev-ref HEAD
$changedFiles = (git diff --cached --name-only) -join ", "
$commitMessage = @"
Auto-commit: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Files: $changedFiles

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
"@

git commit -m $commitMessage | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Log "git commit FAILED."
    exit 1
}

git push origin $branch 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Log "git push FAILED for branch '$branch' (commit was made locally, not pushed)."
    exit 1
}

Write-Log "Committed and pushed to '$branch'."
exit 0
