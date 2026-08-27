# VERIFY_KB_CANON.ps1 -- Phase 0 Lite step 1, on Windows.
# Replaces `md5sum -c MD5SUMS_ALL.txt`, which is NOT a Windows command.
# Read-only. Changes nothing. Exit 0 = all match, 1 = at least one did not.
param([string]$SumsFile = "MD5SUMS_ALL.txt")
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not [System.IO.Path]::IsPathRooted($SumsFile)) { $SumsFile = Join-Path $root $SumsFile }
if (-not (Test-Path $SumsFile)) { Write-Host "FATAL: no such sums file: $SumsFile"; exit 1 }
$base = Split-Path -Parent $SumsFile
$ok = 0; $bad = 0; $missing = 0
foreach ($line in Get-Content $SumsFile) {
    if ($line -notmatch '^\s*([0-9a-fA-F]{32})\s+\*?(.+?)\s*$') { continue }
    $want = $Matches[1].ToLower(); $name = $Matches[2]
    $path = Join-Path $base $name
    if (-not (Test-Path -LiteralPath $path)) { Write-Host "$name : MISSING"; $missing++; continue }
    $got = (Get-FileHash -LiteralPath $path -Algorithm MD5).Hash.ToLower()
    if ($got -eq $want) { $ok++ } else { Write-Host "$name : FAILED"; Write-Host "    expected $want"; Write-Host "    actual   $got"; $bad++ }
}
$total = $ok + $bad + $missing
Write-Host ""
Write-Host "checked $total   OK $ok   FAILED $bad   MISSING $missing"
if ($bad -eq 0 -and $missing -eq 0) { Write-Host "RESULT: PASS"; exit 0 }
Write-Host "RESULT: FAIL  -- Phase 0 halts here. Reconcile before any work (D172/D188)."
exit 1
