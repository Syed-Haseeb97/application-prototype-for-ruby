# Creates Desktop and Start Menu shortcuts to the built Ruby.exe. No admin rights needed.
param([string]$Exe = (Join-Path $PSScriptRoot "..\dist\Ruby\Ruby.exe"))
$ErrorActionPreference = "Stop"
$Exe = (Resolve-Path $Exe).Path
$shell = New-Object -ComObject WScript.Shell
$targets = @(
  (Join-Path ([Environment]::GetFolderPath("Desktop")) "Ruby.lnk"),
  (Join-Path ([Environment]::GetFolderPath("Programs")) "Ruby.lnk")
)
foreach ($lnk in $targets) {
  $s = $shell.CreateShortcut($lnk)
  $s.TargetPath = $Exe
  $s.WorkingDirectory = Split-Path $Exe
  $s.IconLocation = "$Exe,0"
  $s.Description = "Ruby AI desktop assistant"
  $s.Save()
  Write-Host "Created $lnk"
}
