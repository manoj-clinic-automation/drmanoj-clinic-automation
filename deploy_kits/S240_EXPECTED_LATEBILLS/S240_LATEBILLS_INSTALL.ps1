# S240_LATEBILLS_INSTALL.ps1 -- Session 240. Runs on MANOJZ.
#  push_expected.py (the computed "ours" stock) learns late-keyed bills:
#  a purchase bill DATED on/before the baseline but KEYED into Marg after the
#  baseline stock export was taken is now added (D465 -- Ravi 7617, Jubilee 15521,
#  Yuvika 571). Replaces deploy_kits\S208_STOCK_LEDGER\push_expected.py in place,
#  gated on the live copy being a0e47a98, with a backup. Then: selftest, and a
#  DRY RUN on the real archive (nothing is sent). Any crash rolls back.
# Emergency switch-off without reinstalling: set LATE_KEYED=off
# Report: D:\Downloads\margsync\_analysis\S240_latebills_install_report.txt
$ErrorActionPreference = 'Stop'
$KIT    = Split-Path -Parent $MyInvocation.MyCommand.Path
$DIR    = 'D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S208_STOCK_LEDGER'
$PIN    = 'a0e47a981cf03b8fdf7d35d1a9168295'
$NEW    = 'eefc8f4918fa6735371be298cbc731d8'
$REPORT = 'D:\Downloads\margsync\_analysis\S240_latebills_install_report.txt'
$DRY    = 'D:\Downloads\margsync\_analysis\S240_latebills_dryrun.txt'
$lines  = New-Object System.Collections.ArrayList
function Say($m) { Write-Host $m; [void]$lines.Add($m) }
function Md5($p) { (Get-FileHash -Algorithm MD5 -LiteralPath $p).Hash.ToLower() }
function Finish($code) {
  New-Item -ItemType Directory -Force -Path (Split-Path $REPORT) | Out-Null
  $lines | Set-Content -LiteralPath $REPORT -Encoding UTF8
  Write-Host ''; Write-Host ('Report written: ' + $REPORT); exit $code
}
Say ('S240_LATEBILLS_INSTALL  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$bad = 0
foreach ($ln in Get-Content -LiteralPath (Join-Path $KIT 'SUMS.md5')) {
  if ($ln -match '^([0-9a-f]{32})\s+\*?(.+)$') {
    $f = Join-Path $KIT $Matches[2].Trim()
    if (-not (Test-Path -LiteralPath $f) -or (Md5 $f) -ne $Matches[1]) { Say ('  FAILED  ' + $Matches[2]); $bad++ }
  }
}
if ($bad) { Say 'STOP: the kit does not match its sums. Nothing was changed.'; Finish 2 }
Say '  kit sums OK'
$ErrorActionPreference = 'Continue'
$py = $null
foreach ($c in 'python','py') { if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break } }
if (-not $py) { Say 'STOP: no python on this PC.'; Finish 2 }
$env:PYTHONUTF8 = '1'

$pe  = Join-Path $DIR 'push_expected.py'
$bak = $pe + '.bak_S240_a0e47a98'
$live = Md5 $pe
if ($live -eq $NEW) { Say '  push_expected.py is already the S240 version' }
elseif ($live -ne $PIN) { Say ("STOP: push_expected.py is $($live.Substring(0,8)), not a0e47a98. Nothing was changed."); Finish 2 }
else {
  Copy-Item -LiteralPath $pe -Destination $bak -Force
  Copy-Item -LiteralPath (Join-Path $KIT 'push_expected.py') -Destination $pe -Force
  Say ("  push_expected.py  a0e47a98 -> $((Md5 $pe).Substring(0,8))  (backup .bak_S240_a0e47a98)")
}
if ((Md5 $pe) -ne $NEW) { Say 'STOP: the copied file does not match the kit.'; if (Test-Path $bak) { Copy-Item -LiteralPath $bak -Destination $pe -Force; Say '  rolled back' }; Finish 2 }

Push-Location $DIR
$st = & $py -B (Join-Path $KIT 'selftest_latebills.py') 2>&1
$stc = $LASTEXITCODE
Say ('  selftest: ' + (($st | Select-Object -Last 1) -join ''))
$out = & $py -B push_expected.py --baseline 03-09-2026 --dry-run 2>&1
$dc = $LASTEXITCODE
Pop-Location
$out | ForEach-Object { "$_" } | Set-Content -LiteralPath $DRY -Encoding UTF8
$crash = ($out | Where-Object { "$_" -match 'Traceback' }).Count -gt 0
if ($stc -ne 0 -or $crash) {
  $st | Select-Object -Last 15 | ForEach-Object { Say ('    ' + $_) }
  $out | Select-Object -Last 15 | ForEach-Object { Say ('    ' + $_) }
  if (Test-Path $bak) { Copy-Item -LiteralPath $bak -Destination $pe -Force; Say '  ROLLED BACK to a0e47a98' }
  Say 'FAILED -- nothing changed on the live side.'; Finish 1
}
Say "  dry run on the real archive (baseline 03-09-2026, nothing sent), exit ${dc}:"
$show = $false
foreach ($l in $out) { $s = "$l"
  if ($s -match '^keying') { $show = $true }
  if ($s -match '^dates|^sales') { $show = $false }
  if ($show -or $s -match '^EXPECTED AS ON|REFUSING') { Say ('    ' + $s) } }
Say ('  full dry-run output: ' + $DRY)
Say ''; Say 'DONE.'
Finish 0
