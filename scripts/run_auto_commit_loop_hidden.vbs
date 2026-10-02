' Launches auto_commit_loop.ps1 with zero visible window, fire-and-forget. The loop
' itself runs for the whole VS Code session, so this launcher returns immediately
' (waitOnReturn=False) instead of blocking on it -- mirrors run_auto_commit_hidden.vbs,
' which wraps the one-shot auto_commit.ps1 the same way for the Scheduled Task.
Set objFSO = CreateObject("Scripting.FileSystemObject")
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
psScript = scriptDir & "\auto_commit_loop.ps1"

Set objShell = CreateObject("WScript.Shell")
objShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & psScript & """", 0, False
