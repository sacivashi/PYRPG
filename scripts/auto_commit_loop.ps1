# Session-scoped auto-commit loop for PYRPG.
#
# Started by VS Code when the PYRPG folder opens (see .vscode/tasks.json) and exits on
# its own as soon as neither VS Code nor Claude Code is running, so nothing fires while
# you are not working. Every interval it runs auto_commit.ps1, which keeps its own import
# check gate, logging and push logic.

param(
    [double]$IntervalMinutes = 20,
    [string[]]$ProcessNames = @("Code", "claude"),
    [string]$CycleScript = (Join-Path $PSScriptRoot "auto_commit.ps1")
)

# Single instance: a second copy (another window, a manual launch) exits immediately
$createdNew = $false
$mutex = New-Object System.Threading.Mutex($true, "Local\PYRPG-AutoCommitLoop", [ref]$createdNew)
if (-not $createdNew) {
    exit 0
}

function Test-Working {
    return [bool](Get-Process -Name $ProcessNames -ErrorAction SilentlyContinue)
}

try {
    $nextRun = (Get-Date).AddMinutes($IntervalMinutes)
    while (Test-Working) {
        if ((Get-Date) -ge $nextRun) {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $CycleScript | Out-Null
            $nextRun = (Get-Date).AddMinutes($IntervalMinutes)
        }
        Start-Sleep -Seconds 15
    }
}
finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
