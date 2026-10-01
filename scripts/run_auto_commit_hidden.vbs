' Launches auto_commit.ps1 with zero visible window. powershell.exe's own -WindowStyle
' Hidden still briefly flashes a console before hiding it; WScript.Shell.Run with
' windowStyle 0 never creates one in the first place. Path-agnostic (resolves its own
' folder), same as the .ps1 scripts next to it, so it works on any machine's checkout.
Set objFSO = CreateObject("Scripting.FileSystemObject")
scriptDir = objFSO.GetParentFolderName(WScript.ScriptFullName)
psScript = scriptDir & "\auto_commit.ps1"

Set objShell = CreateObject("WScript.Shell")
objShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -File """ & psScript & """", 0, True
