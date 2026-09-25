# Auto-commit + push runner for PYRPG, invoked on a schedule by the
# "PYRPG-AutoCommit" Windows Scheduled Task (see scripts/auto_commit_task.xml).
#
# Safety gate: only commits/pushes if `python -c "import game.pyrpg"` still
# succeeds, so an obviously broken working tree never reaches GitHub unattended.
# There is no test suite in this repo (see CLAUDE.md) -- this import check is
# the only automated gate, it does NOT verify gameplay correctness.

param(
    # Fire a test notification and exit, to check that alerts are visible on this machine
    [switch]$TestAlert
)

$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$LogFile = Join-Path $PSScriptRoot "auto_commit.log"

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp  $Message" | Out-File -FilePath $LogFile -Append -Encoding utf8
}

# Non-blocking Windows toast, so a failed push is visible instead of only sitting in the log.
# Never throws: a notification problem must not break the commit cycle.
function Show-Alert {
    param([string]$Title, [string]$Body)
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
        [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
        $safeTitle = [System.Security.SecurityElement]::Escape($Title)
        $safeBody = [System.Security.SecurityElement]::Escape($Body)
        $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
        $xml.LoadXml("<toast><visual><binding template=`"ToastGeneric`"><text>$safeTitle</text><text>$safeBody</text></binding></visual></toast>")
        $appId = '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
        $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($appId).Show($toast)
    }
    catch {
        Write-Log "Could not show notification: $($_.Exception.Message)"
    }
}

# Pushes and, on failure, logs git's actual error text (not just "failed") and raises an alert
function Invoke-Push {
    param([string]$Branch, [string]$Context)
    # ForEach-Object "$_" flattens PowerShell's stderr error-records into plain message text
    $output = ((git push origin $Branch 2>&1 | ForEach-Object { "$_" }) -join " | ").Trim()
    if ($LASTEXITCODE -eq 0) {
        return $true
    }
    Write-Log "$Context FAILED for '$Branch'. git said: $output"
    Show-Alert "PYRPG auto-push failed" "Branch '$Branch' has unpushed commits. Pull/merge, then push. Details: scripts/auto_commit.log"
    return $false
}

if ($TestAlert) {
    Show-Alert "PYRPG auto-commit" "Test notification - if you can see this, push-failure alerts will work."
    Write-Log "Test alert fired."
    exit 0
}

Set-Location $RepoRoot

# Only run while actively working -- skip entirely if neither VS Code nor Claude Code is open
$isActive = (Get-Process -Name "Code" -ErrorAction SilentlyContinue) -or (Get-Process -Name "claude" -ErrorAction SilentlyContinue)
if (-not $isActive) {
    Write-Log "Neither VS Code nor Claude Code is running, skipping."
    exit 0
}

$branch = git rev-parse --abbrev-ref HEAD

# Clean tree: nothing to commit, but retry the push if an earlier push failed and left commits behind
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    $ahead = [int](git rev-list --count "origin/$branch..HEAD" 2>$null)
    if ($ahead -gt 0) {
        if (Invoke-Push -Branch $branch -Context "Retried push ($ahead commit(s) still unpushed)") {
            Write-Log "Retried push: $ahead earlier commit(s) pushed to '$branch'."
        } else {
            exit 1
        }
    } else {
        Write-Log "No changes, skipping."
    }
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

$changedFiles =(git diff --cached --name-only) -join ", "
$commitMessage = @"
Auto-commit: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Files: $changedFiles

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
"@

git commit -m $commitMessage | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Log "git commit FAILED."
    Show-Alert "PYRPG auto-commit failed" "Your changes were NOT committed. Details: scripts/auto_commit.log"
    exit 1
}

if (-not (Invoke-Push -Branch $branch -Context "git push (commit was made locally, not pushed)")) {
    exit 1
}

Write-Log "Committed and pushed to '$branch'."
exit 0
