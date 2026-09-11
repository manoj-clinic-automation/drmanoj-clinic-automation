# S240_PC_INSTALL.ps1 -- Session 240. Runs on MANOJZ, AFTER the VPS kit S240_SANJEEVNI_123 is GREEN.
#  1. push_purchases.py gets the F-431 fix (the nightly feed no longer reads a running pull as "asleep")
#  2. the sale bills' money rows are sent to the server (Rung 1 backfill: every archived SALE_BILLWISE)
#  3. task MargPushEvery30 -- purchases and sale bills sent every 30 minutes, hidden, allowed on battery
# Report: D:\Downloads\margsync\_analysis\S240_pc_install_report.txt
$ErrorActionPreference = 'Stop'
$KIT    = Split-Path -Parent $MyInvocation.MyCommand.Path
$PPDIR  = 'D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S224_MARG_PURCHASES'
$HIDDEN = 'D:\Downloads\margsync\MargPull\RUN_HIDDEN.vbs'
$REPORT = 'D:\Downloads\margsync\_analysis\S240_pc_install_report.txt'
$lines  = New-Object System.Collections.ArrayList
function Say($m) { Write-Host $m; [void]$lines.Add($m) }
function Md5($p) { (Get-FileHash -Algorithm MD5 -LiteralPath $p).Hash.ToLower() }
function Finish($code) {
  New-Item -ItemType Directory -Force -Path (Split-Path $REPORT) | Out-Null
  $lines | Set-Content -LiteralPath $REPORT -Encoding UTF8
  Write-Host ''; Write-Host ('Report written: ' + $REPORT); exit $code
}
Say ('S240_PC_INSTALL  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$bad = 0
foreach ($ln in Get-Content -LiteralPath (Join-Path $KIT 'SUMS.md5')) {
  if ($ln -match '^([0-9a-f]{32})\s+\*?(.+)$') {
    $f = Join-Path $KIT $Matches[2].Trim()
    if (-not (Test-Path -LiteralPath $f) -or (Md5 $f) -ne $Matches[1]) { Say ('  FAILED  ' + $Matches[2]); $bad++ }
  }
}
if ($bad) { Say 'STOP: the kit does not match its sums. Nothing was changed.'; Finish 2 }
Say '  kit sums OK'
$ErrorActionPreference = 'Continue'   # native python output must never throw (PS 5.1 wraps stderr lines)
$py = $null
foreach ($c in 'python','py') { if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break } }
if (-not $py) { Say 'STOP: no python on this PC.'; Finish 2 }

# ---- 1. push_purchases.py (F-431)
$pp = Join-Path $PPDIR 'push_purchases.py'
$live = Md5 $pp; $new = Md5 (Join-Path $KIT 'push_purchases.py')
if ($live -eq $new) { Say '  push_purchases.py already the S240 version' }
elseif ($live -ne '13a5cb8ed373f7529d232928caa9d471') { Say ("  push_purchases.py is $($live.Substring(0,8)), not the S224 copy -- left alone (F-431 fix NOT applied)") }
else {
  Copy-Item -LiteralPath $pp -Destination ($pp + '.bak_S240_13a5cb8e') -Force
  Copy-Item -LiteralPath (Join-Path $KIT 'push_purchases.py') -Destination $pp -Force
  Say ("  push_purchases.py  13a5cb8e -> $((Md5 $pp).Substring(0,8))  (backup .bak_S240_13a5cb8e)")
}

# ---- 2. the sale bills
$env:PYTHONUTF8 = '1'
& $py -B (Join-Path $KIT 'push_sale_bills.py') --selftest 2>&1 | Select-Object -Last 1 | ForEach-Object { Say ('  ' + $_) }
$door = & $py -B (Join-Path $KIT 'push_sale_bills.py') --verify 2>&1
$door | ForEach-Object { Say ('  ' + $_) }
if ($LASTEXITCODE -eq 0) {
  Say '  sending the archived sale bills now ...'
  & $py -B (Join-Path $KIT 'push_sale_bills.py') 2>&1 | Select-Object -Last 3 | ForEach-Object { Say ('  ' + $_) }
} else { Say '  the server door is not open yet -- the 30-minute task will send them once the VPS kit is in.' }

# ---- 3. task MargPushEvery30
$bat = Join-Path $KIT 'PUSH_MARG_EVERY_30.bat'
$now = Get-Date; $m = if ($now.Minute -lt 15) { 15 } elseif ($now.Minute -lt 45) { 45 } else { 75 }
$start = $now.Date.AddHours($now.Hour).AddMinutes($m)
$a = New-ScheduledTaskAction -Execute 'wscript.exe' -Argument ('"' + $HIDDEN + '" "' + $bat + '"')
$t = New-ScheduledTaskTrigger -Once -At $start -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 20) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName 'MargPushEvery30' -Action $a -Trigger $t -Settings $s -Force | Out-Null
$r = Get-ScheduledTask -TaskName 'MargPushEvery30'
Say ("  task MargPushEvery30: $($r.State), first run $($start.ToString('HH:mm')), battery ok = $(-not $r.Settings.DisallowStartIfOnBatteries)")
Say ''; Say 'DONE.'
Finish 0
