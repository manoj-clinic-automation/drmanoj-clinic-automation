# task_selfheal.ps1 -- kit S415_NIGHTLY_SELFHEAL (F-630, 26-Sep-2026). Run by NIGHTLY.bat on every run and by APPLY_S415.bat once.
# 1. the 03:10 task keeps its catch-up flags and gains WakeToRun (the PC wakes from sleep to run it);
# 2. a SECOND task 'KB Manifest Rebuild - morning' runs NIGHTLY.bat morning at 07:30 and at every log-on --
#    NIGHTLY.bat itself skips when the 03:10 run already happened today, so nothing runs twice;
# 3. the Task Scheduler history log is switched on if it is off, and the last 7 days of the tasks' own
#    events plus the PC's sleep / wake / boot / shutdown events are written to reports\TASK_HISTORY_LATEST.txt
#    so the next session can read WHY a night was missed instead of guessing.
# Never fails the nightly: every step is try/catch and reports in words.
$ErrorActionPreference = 'Continue'
$tools = Split-Path -Parent $MyInvocation.MyCommand.Path
$rep = Join-Path $tools 'reports\TASK_HISTORY_LATEST.txt'
$out = New-Object System.Collections.Generic.List[string]
$out.Add("TASK SELF-HEAL -- S415 v1.0")
$out.Add("when  : " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + " (local clock on this PC)")
$out.Add("")
# ---- 1. the 03:10 task
try {
  $t = Get-ScheduledTask -TaskName 'KB Manifest Rebuild' -ErrorAction Stop
  $s = $t.Settings; $chg = @()
  if (-not $s.StartWhenAvailable) { $s.StartWhenAvailable = $true; $chg += 'StartWhenAvailable' }
  if ($s.DisallowStartIfOnBatteries) { $s.DisallowStartIfOnBatteries = $false; $chg += 'DisallowStartIfOnBatteries' }
  if ($s.StopIfGoingOnBatteries) { $s.StopIfGoingOnBatteries = $false; $chg += 'StopIfGoingOnBatteries' }
  if (-not $s.WakeToRun) { $s.WakeToRun = $true; $chg += 'WakeToRun' }
  if ($chg.Count) { Set-ScheduledTask -InputObject $t | Out-Null; $out.Add("03:10 task : flags set -> " + ($chg -join ', ')) } else { $out.Add("03:10 task : flags already right (StartWhenAvailable, WakeToRun, battery off)") }
  $i = Get-ScheduledTaskInfo -TaskName 'KB Manifest Rebuild'
  $out.Add("03:10 task : last run " + $i.LastRunTime + "  result " + $i.LastTaskResult + "  next " + $i.NextRunTime)
} catch { $out.Add("03:10 task : could not read or set -- " + $_.Exception.Message) }
# ---- 2. the morning task
try {
  $m = Get-ScheduledTask -TaskName 'KB Manifest Rebuild - morning' -ErrorAction SilentlyContinue
  if (-not $m) {
    $act = New-ScheduledTaskAction -Execute (Join-Path $tools 'NIGHTLY.bat') -Argument 'morning' -WorkingDirectory $tools
    $tr1 = New-ScheduledTaskTrigger -Daily -At 07:30
    $tr2 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $tr2.Delay = 'PT3M'
    $st = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
    Register-ScheduledTask -TaskName 'KB Manifest Rebuild - morning' -Action $act -Trigger @($tr1, $tr2) -Settings $st -Description 'S415 (F-630): runs the nightly at 07:30 or at log-on ONLY if the 03:10 run did not happen today.' | Out-Null
    $out.Add("morning task : CREATED (07:30 daily + at log-on, argument morning)")
  } else {
    $mi = Get-ScheduledTaskInfo -TaskName 'KB Manifest Rebuild - morning'
    $out.Add("morning task : present -- last run " + $mi.LastRunTime + "  result " + $mi.LastTaskResult + "  next " + $mi.NextRunTime)
  }
} catch { $out.Add("morning task : could not create -- " + $_.Exception.Message) }
# ---- 3. history
try {
  $log = Get-WinEvent -ListLog 'Microsoft-Windows-TaskScheduler/Operational' -ErrorAction Stop
  if (-not $log.IsEnabled) {
    try { & wevtutil.exe sl 'Microsoft-Windows-TaskScheduler/Operational' /e:true 2>&1 | Out-Null; $out.Add("history log : was OFF -- switched on (events collect from now)") }
    catch { $out.Add("history log : is OFF and could not be switched on (needs an administrator once): " + $_.Exception.Message) }
  } else { $out.Add("history log : on") }
} catch { $out.Add("history log : not readable -- " + $_.Exception.Message) }
$since = (Get-Date).AddDays(-7)
$out.Add(""); $out.Add("=== the two tasks, last 7 days (Task Scheduler log) ===")
try {
  $ev = Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational'; StartTime=$since} -ErrorAction Stop |
        Where-Object { $_.Message -like '*KB Manifest Rebuild*' } | Sort-Object TimeCreated
  if ($ev) { foreach ($e in $ev) { $out.Add(($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')) + "  id " + $e.Id + "  " + (($e.Message -split "`n")[0]).Trim()) } }
  else { $out.Add("(no events -- the log was off, or nothing ran)") }
} catch { $out.Add("(could not read: " + $_.Exception.Message + ")") }
$out.Add(""); $out.Add("=== the PC: sleep / wake / boot / shutdown / log-on, last 7 days ===")
try {
  $ids = @{42='SLEEP'; 1='WAKE'; 6005='BOOT (event log started)'; 6006='SHUTDOWN (event log stopped)'; 6008='UNEXPECTED SHUTDOWN'; 41='REBOOT WITHOUT CLEAN SHUTDOWN'; 7001='LOG-ON'; 7002='LOG-OFF'}
  $pv = Get-WinEvent -FilterHashtable @{LogName='System'; Id=@(42,1,6005,6006,6008,41,7001,7002); StartTime=$since} -ErrorAction Stop |
        Where-Object { $_.ProviderName -in @('Microsoft-Windows-Kernel-Power','Microsoft-Windows-Power-Troubleshooter','EventLog','Microsoft-Windows-Winlogon') } | Sort-Object TimeCreated
  foreach ($e in $pv) { $out.Add(($e.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss')) + "  " + $ids[[int]$e.Id] + "  (" + $e.ProviderName + ")") }
  if (-not $pv) { $out.Add("(none)") }
} catch { $out.Add("(could not read the System log: " + $_.Exception.Message + ")") }
$out.Add(""); $out.Add("=== the nightly's own reports, last 10 ===")
try { Get-ChildItem (Join-Path $tools 'reports\REBUILD_*.txt') | Sort-Object Name | Select-Object -Last 10 | ForEach-Object { $out.Add($_.Name) } } catch {}
New-Item -ItemType Directory -Force -Path (Join-Path $tools 'reports') | Out-Null
[System.IO.File]::WriteAllLines($rep, $out)
$out | ForEach-Object { Write-Output $_ }
