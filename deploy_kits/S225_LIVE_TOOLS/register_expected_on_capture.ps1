# register_expected_on_capture.ps1 -- S225: registers the MargExpectedOnCapture task (every 15 min, allowed on battery,
# 10-minute limit) and gives the 22:30 nightly a 30-minute limit so a hung run can never block the next night.
# Run through REGISTER_EXPECTED_ON_CAPTURE.bat (double-click) -- the window stays open and shows the result.
$ErrorActionPreference = 'Continue'
Write-Host ''
Write-Host '1 of 2 -- registering MargExpectedOnCapture ...'
$a = New-ScheduledTaskAction -Execute 'D:\Downloads\margsync\MargPull\EXPECTED_ON_CAPTURE.bat'
$t = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
$s = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName 'MargExpectedOnCapture' -Action $a -Trigger $t -Settings $s -Force | Out-Null
Get-ScheduledTask -TaskName 'MargExpectedOnCapture' | Select-Object TaskName, State | Format-Table -AutoSize
Write-Host '2 of 2 -- the 22:30 nightly: stopping any stuck instance, setting a 30-minute limit ...'
$n = Get-ScheduledTask | Where-Object { $_.TaskName -like '*nightly*' }
if ($n) {
  foreach ($task in $n) {
    Stop-ScheduledTask -TaskName $task.TaskName -ErrorAction SilentlyContinue
    $s2 = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 30)
    Set-ScheduledTask -TaskName $task.TaskName -Settings $s2 | Out-Null
    Get-ScheduledTask -TaskName $task.TaskName | Select-Object TaskName, State | Format-Table -AutoSize
  }
} else { Write-Host '   (no task with "nightly" in its name was found -- nothing changed there)' }
Write-Host ''
Write-Host 'DONE. Within a minute the first run writes D:\Downloads\margsync\_analysis\expected_on_capture_log.txt'
Write-Host 'and the drift page gets our figure whenever a sale or purchase export lands.'
