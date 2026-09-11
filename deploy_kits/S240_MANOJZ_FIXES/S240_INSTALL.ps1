# S240_INSTALL.ps1 -- Session 240, 11-Sep-2026. Runs on MANOJZ. Two fixes, one run. Normal rights are enough.
#
#  1. F-429  Marg: the SUPPLIER/ITEM WISE purchase report was refused as "TRUNCATED" because Marg changed its
#            footer line on 09-Sep. The router now checks the report's own GRAND TOTAL row instead.
#            The next 10-minute pull sees the changed signatures and re-files the two refused exports itself.
#  2. F-430  Docterz: the DocterzPickup task was created "start only on AC power" and stopped at 11:55 on
#            battery. Battery flags cleared on it and on every other clinic task that still has them.
#
# Every step is checked and read back. A report is written to
#   D:\Downloads\margsync\_analysis\S240_install_report.txt
$ErrorActionPreference = 'Stop'
$KIT     = Split-Path -Parent $MyInvocation.MyCommand.Path
$PULL    = 'D:\Downloads\margsync\MargPull'
$TRACKER = 'C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker'
$REPORT  = 'D:\Downloads\margsync\_analysis\S240_install_report.txt'
$lines   = New-Object System.Collections.ArrayList
function Say($m) { Write-Host $m; [void]$lines.Add($m) }
function Md5($p) { (Get-FileHash -Algorithm MD5 -LiteralPath $p).Hash.ToLower() }
function Finish($code) {
  New-Item -ItemType Directory -Force -Path (Split-Path $REPORT) | Out-Null
  $lines | Set-Content -LiteralPath $REPORT -Encoding UTF8
  Write-Host ''
  Write-Host ('Report written: ' + $REPORT)
  exit $code
}
Say ('S240_INSTALL  ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))

# ---- 0. the kit's own sums, checked from inside its folder
$bad = 0
foreach ($ln in Get-Content -LiteralPath (Join-Path $KIT 'SUMS.md5')) {
  if ($ln -match '^([0-9a-f]{32})\s+\*?(.+)$') {
    $f = Join-Path $KIT $Matches[2].Trim()
    if (-not (Test-Path -LiteralPath $f)) { Say ('  MISSING ' + $Matches[2]); $bad++ }
    elseif ((Md5 $f) -ne $Matches[1]) { Say ('  FAILED  ' + $Matches[2]); $bad++ }
    else { Say ('  OK      ' + $Matches[2]) }
  }
}
if ($bad) { Say 'STOP: the kit does not match its sums. Nothing was changed.'; Finish 2 }

# ---- 1. Marg router + signatures (F-429)
Say ''
Say '1 of 2 -- Marg purchase report (F-429)'
$expect = @{ 'marg_router.py' = '5e034804b8cce5af86d309089cdd2410'; 'signatures.json' = '37bcfebef16e51f2b0a8351eff1097be' }
$new    = @{ 'marg_router.py' = (Md5 (Join-Path $KIT 'marg_router.py')); 'signatures.json' = (Md5 (Join-Path $KIT 'signatures.json')) }
$go = $true
foreach ($n in 'marg_router.py','signatures.json') {
  $live = Md5 (Join-Path $PULL $n)
  if ($live -eq $new[$n]) { Say ("  $n already installed ($($live.Substring(0,8)))") }
  elseif ($live -ne $expect[$n]) { Say ("  STOP: live $n is $($live.Substring(0,8)), not the $($expect[$n].Substring(0,8)) this kit was built on. Marg step skipped."); $go = $false }
}
if ($go) {
  foreach ($n in 'marg_router.py','signatures.json') {      # router FIRST, then the signatures that use it
    $dst  = Join-Path $PULL $n
    $live = Md5 $dst
    if ($live -eq $new[$n]) { continue }
    Copy-Item -LiteralPath $dst -Destination ($dst + '.bak_S240_' + $live.Substring(0,8)) -Force
    Copy-Item -LiteralPath (Join-Path $KIT $n) -Destination $dst -Force
    $back = Md5 $dst
    if ($back -eq $new[$n]) { Say ("  $n installed  $($live.Substring(0,8)) -> $($back.Substring(0,8))  (backup .bak_S240_$($live.Substring(0,8)))") }
    else { Say ("  FAILED: $n reads back $back"); $go = $false }
  }
  $py = $null
  foreach ($c in 'python','py') { if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break } }
  if ($py) {
    & $py -B -c "import sys; sys.path.insert(0, r'$PULL'); import marg_router as R; s=[x for x in R.load_signatures(r'$PULL\signatures.json') if x['type']=='PURCHASE_ITEMWISE'][0]; print('  router loads; PURCHASE_ITEMWISE closes on', ' '.join(s['end_row']))" 2>&1 | ForEach-Object { Say $_ }
  }
  Say '  The next 10-minute pull re-files the two refused exports by itself (signatures changed).'
}

# ---- 2. battery flags (F-430)
Say ''
Say '2 of 2 -- scheduled tasks: allowed on battery (F-430)'
$pattern = 'margsync|followup_tracker|DocterzArchive|dr-manoj-git|SendToClinic'
$tasks = Get-ScheduledTask | Where-Object {
  ($_.Actions | ForEach-Object { "$($_.Execute) $($_.Arguments)" }) -join ' ' -match $pattern }
foreach ($t in $tasks) {
  $s = $t.Settings
  if (-not $s.DisallowStartIfOnBatteries -and -not $s.StopIfGoingOnBatteries) { Say ("  already fine : " + $t.TaskName); continue }
  try {
    $s.DisallowStartIfOnBatteries = $false; $s.StopIfGoingOnBatteries = $false; $s.StartWhenAvailable = $true
    Set-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath -Settings $s -ErrorAction Stop | Out-Null
    $r = (Get-ScheduledTask -TaskName $t.TaskName -TaskPath $t.TaskPath).Settings
    if (-not $r.DisallowStartIfOnBatteries -and -not $r.StopIfGoingOnBatteries) { Say ("  FIXED        : " + $t.TaskName) }
    else { Say ("  NOT CHANGED  : " + $t.TaskName + " (read back still on AC only)") }
  } catch { Say ("  NEEDS ADMIN  : " + $t.TaskName + " -- " + $_.Exception.Message.Split("`n")[0]) }
}
if (-not ($tasks | Where-Object TaskName -eq 'DocterzPickup')) { Say '  WARNING: no task named DocterzPickup was found.' }

# the tracker folder's register script, so a re-register can never bring the fault back
$reg = Join-Path $TRACKER 'REGISTER_DOCTERZ_PICKUP.bat'
if (Test-Path -LiteralPath $reg) {
  $old = Md5 $reg; $newr = Md5 (Join-Path $KIT 'REGISTER_DOCTERZ_PICKUP.bat')
  if ($old -ne $newr) {
    Copy-Item -LiteralPath $reg -Destination ($reg + '.bak_S240_' + $old.Substring(0,8)) -Force
    Copy-Item -LiteralPath (Join-Path $KIT 'REGISTER_DOCTERZ_PICKUP.bat') -Destination $reg -Force
    Say ("  tracker REGISTER_DOCTERZ_PICKUP.bat  $($old.Substring(0,8)) -> $((Md5 $reg).Substring(0,8))")
  } else { Say '  tracker REGISTER_DOCTERZ_PICKUP.bat already the S240 version' }
}

# run the pickup now and read its heartbeat back
$hb = 'D:\Downloads\DocterzArchive\_last_pass.txt'
$before = (Get-Item -LiteralPath $hb).LastWriteTime
Start-ScheduledTask -TaskName 'DocterzPickup'
Say '  DocterzPickup started -- waiting up to 3 minutes for its heartbeat ...'
$ok = $false
for ($i = 0; $i -lt 36; $i++) { Start-Sleep 5; if ((Get-Item -LiteralPath $hb).LastWriteTime -gt $before) { $ok = $true; break } }
if ($ok) { Say ('  heartbeat: ' + (Get-Content -LiteralPath $hb -Raw).Trim()) }
else     { Say ('  heartbeat NOT refreshed (still ' + $before.ToString('HH:mm:ss') + ')') }
$ac = (Get-CimInstance -ClassName BatteryStatus -Namespace root\wmi -ErrorAction SilentlyContinue | Select-Object -First 1).PowerOnline
if ($ac -ne $null) { Say ('  on AC power right now: ' + $ac) }
Say ''
Say 'DONE.'
Finish 0
