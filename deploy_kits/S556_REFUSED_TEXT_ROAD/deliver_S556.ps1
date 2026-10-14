# =============================================================================
#  deliver_S556.ps1 - kit S556_REFUSED_TEXT_ROAD - the medical PC (made from S491's deliver_S491.ps1)
#  Puts marg_watch.py S556 (a change of the reader re-offers the texts it refused in the last three days, within a minute; F-893) into
#  Drive's ToMedical\_kit. Changing the watcher is what makes the medical PC's agent (S499) install it and restart the watcher.
#  Run ONLY after the server part of S556 is green.
#
#  Run on manojz (Windows PowerShell 5.1):   powershell -ExecutionPolicy Bypass -File deliver_S556.ps1 [-WatchMinutes 45]
#  Pins:  Drive marg_watch.py     0a78ae15 (S488)  ->  39fa2773 (S556, this folder's file, the same bytes)
#         Drive marg_txt.py       a59a222f (S546), KIT_MANIFEST.txt 0bf248e4 (CRLF), marg_push.py 566e189e - at their pins, NOT changed
#  Backup beside it: marg_watch_S488.py.superseded (read back). Red after placing: put back byte-identically.
#  Then the heartbeat (Drive FromMedical\heartbeat.json, every ~5 min), up to -WatchMinutes: DONE = two beats at least 5 min apart, each with
#  the watcher file at 39fa2773, the watcher ALIVE, the same pid and the same restart count, and the watcher's log on Drive
#  (FromMedical\marg_watch_log.txt) carrying the 'marg_watch S556 starting' line. A rising restart count or a dead watcher: 0a78ae15 is put
#  back on Drive (the agent restarts the old one) and this says RED. Not seen in time: left placed, said so.
#  No key or token is read or printed here; nothing is exported in Marg; the medical PC is touched only through Drive's _kit.
# =============================================================================
param([int]$WatchMinutes = 45)
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$W_FROM = "0a78ae15be60d8a0293b96ecfa38f35b"; $W_TO = "39fa27739757ff8e9c8731f77d07b40b"
$T_PIN = "a59a222faf32a72ccc19c8635955cf8d"; $M_PIN = "0bf248e43381bd27f6d011648b8405ee"; $P_PIN = "566e189e986128fa2ebb341a78b9ab65"

function Md5Bytes([byte[]]$b) { $h = [Security.Cryptography.MD5]::Create(); return ([BitConverter]::ToString($h.ComputeHash($b))).Replace("-", "").ToLower() }
function Md5File([string]$p) { return Md5Bytes ([IO.File]::ReadAllBytes($p)) }
function Ist() { return (Get-Date).ToString("dd-MM-yyyy HH:mm:ss") }

$tz = [TimeZoneInfo]::Local.BaseUtcOffset
if ($tz -ne [TimeSpan]::FromMinutes(330)) { Write-Output "!! this PC's clock is not IST ($tz) - nothing delivered"; exit 1 }
$kitWatch = Join-Path $here "marg_watch.py"
if ((Md5File $kitWatch) -ne $W_TO) { Write-Output "!! this folder's marg_watch.py is not $W_TO - nothing delivered"; exit 1 }
$kit = $null; $fm = $null
foreach ($L in "DEFGHIJKLMNOPQRSTUVWXYZ".ToCharArray()) {
    $p = "{0}:\My Drive\Clinic Data Archive\ToMedical\_kit" -f $L
    if (Test-Path $p) { $kit = $p; $fm = "{0}:\My Drive\Clinic Data Archive\FromMedical" -f $L; break }
}
if (-not $kit) { Write-Output "!! Drive's ToMedical\_kit is not on this PC - nothing delivered"; exit 1 }
$dW = Join-Path $kit "marg_watch.py"; $dT = Join-Path $kit "marg_txt.py"; $dM = Join-Path $kit "KIT_MANIFEST.txt"; $dP = Join-Path $kit "marg_push.py"
$liveW = Md5File $dW
$placedNow = $false
if ($liveW -eq $W_TO) {
    Write-Output "-- ALREADY DELIVERED: marg_watch.py $W_TO in $kit - going on to read the heartbeat"
} else {
    if ($liveW -ne $W_FROM) { Write-Output "!! $dW is $liveW, not its FROM pin $W_FROM - someone changed it; nothing delivered"; exit 1 }
    if ((Md5File $dT) -ne $T_PIN) { Write-Output "!! $dT is not $T_PIN - the reader this watcher was walked beside has changed; nothing delivered"; exit 1 }
    if ((Md5File $dM) -ne $M_PIN) { Write-Output "!! $dM is not $M_PIN - the manifest has changed; nothing delivered"; exit 1 }
    if ((Md5File $dP) -ne $P_PIN) { Write-Output "!! $dP is not $P_PIN - the pusher has changed; nothing delivered"; exit 1 }
    Write-Output ("[1/4] {0} IST - Drive's marg_watch.py at its FROM pin {1}; marg_txt.py, KIT_MANIFEST.txt and marg_push.py at their pins, not changed ({2})" -f (Ist), $W_FROM.Substring(0, 8), $kit)
    $bW = Join-Path $kit "marg_watch_S488.py.superseded"
    if (Test-Path $bW) { $bW = Join-Path $kit "marg_watch_S488_S556.py.superseded" }
    [IO.File]::WriteAllBytes($bW, [IO.File]::ReadAllBytes($dW))
    if ((Md5File $bW) -ne $W_FROM) { Write-Output "!! the backup does not read back - nothing delivered"; exit 1 }
    Write-Output "[2/4] backup: $(Split-Path -Leaf $bW) ($W_FROM), read back"
    try {
        [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($kitWatch))
        $rw = Md5File $dW
        if ($rw -ne $W_TO) { throw "read back $rw" }
    } catch {
        Write-Output "!! RED after placing ($_) - putting it back byte-identically"
        [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($bW))
        Write-Output ("   marg_watch.py {0}" -f (Md5File $dW))
        exit 1
    }
    $placedNow = $true
    Write-Output ("[3/4] placed at {0} IST; read back marg_watch.py {1}" -f (Ist), $W_TO)
}

# ---- the heartbeat: the agent installs it, restarts the watcher, and the watcher's start banner reaches Drive
$hb = Join-Path $fm "heartbeat.json"; $lg = Join-Path $fm "marg_watch_log.txt"
$deadline = (Get-Date).AddMinutes($WatchMinutes)
$beats = @(); $lastAt = ""; $banner = $false
Write-Output ("[4/4] reading the heartbeat in {0} until {1} IST (every 60 s)" -f $fm, $deadline.ToString("HH:mm:ss"))
while ((Get-Date) -lt $deadline) {
    try {
        $j = Get-Content $hb -Raw -Encoding UTF8 | ConvertFrom-Json
        $at = [string]$j.written_at
        if ($at -ne $lastAt) {
            $lastAt = $at
            $md = [string]$j.watcher_file.md5; $alive = [bool]$j.watcher.alive; $wpid = [string]$j.watcher.pid; $rs = [string]$j.watcher.restarts_since_agent_start
            Write-Output ("      beat {0}: watcher file {1}, alive {2}, pid {3}, restarts {4}" -f $at, $md.Substring(0, [Math]::Min(8, $md.Length)), $alive, $wpid, $rs)
            if ($md.StartsWith($W_TO.Substring(0, 8))) {
                if (-not $alive) { $beats += ,@($at, $alive, $wpid, $rs, "dead"); break }
                $beats += ,@($at, $alive, $wpid, $rs, "ok")
            }
        }
        if (-not $banner -and (Test-Path $lg)) { $banner = [bool](Select-String -Path $lg -Pattern "marg_watch S556 starting" -SimpleMatch -Quiet) }
        if ($beats.Count -ge 2) {
            $first = $beats[0]; $last = $beats[$beats.Count - 1]
            if ($last[2] -ne $first[2] -or $last[3] -ne $first[3]) { break }
            $gap = ([datetime]::Parse($last[0]) - [datetime]::Parse($first[0])).TotalMinutes
            if ($gap -ge 5 -and $banner) { break }
        }
    } catch { Write-Output ("      (the heartbeat could not be read just now: {0})" -f $_.Exception.Message) }
    Start-Sleep -Seconds 60
}
$red = $false; $why = ""
if ($beats.Count -ge 1 -and $beats[$beats.Count - 1][4] -eq "dead") { $red = $true; $why = "the watcher is dead on the new file" }
elseif ($beats.Count -ge 2 -and ($beats[$beats.Count - 1][2] -ne $beats[0][2] -or $beats[$beats.Count - 1][3] -ne $beats[0][3])) { $red = $true; $why = "the watcher restarted again (pid or restart count moved)" }
if ($red) {
    $bk = @("marg_watch_S488_S556.py.superseded", "marg_watch_S488.py.superseded") | ForEach-Object { Join-Path $kit $_ } | Where-Object { (Test-Path $_) -and ((Md5File $_) -eq $W_FROM) } | Select-Object -First 1
    if ($bk) { [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($bk)) }
    Write-Output ("!! RED: {0} - Drive's marg_watch.py put back: {1} (the agent restarts the old watcher); the server part stays" -f $why, (Md5File $dW))
    exit 1
}
$done = $false
if ($beats.Count -ge 2) {
    $gap = ([datetime]::Parse($beats[$beats.Count - 1][0]) - [datetime]::Parse($beats[0][0])).TotalMinutes
    $done = ($gap -ge 5 -and $banner)
}
if ($done) {
    Write-Output ("S556_REFUSED_TEXT_ROAD, the medical PC: DONE at {0} IST - two beats {1} and {2} on marg_watch.py {3}, alive, pid {4}, restarts {5}; the watcher's log on Drive carries 'marg_watch S556 starting'" -f (Ist), $beats[0][0], $beats[$beats.Count - 1][0], $W_TO.Substring(0, 8), $beats[0][2], $beats[0][3])
    exit 0
}
Write-Output ("S556_REFUSED_TEXT_ROAD, the medical PC: PLACED, NOT YET SEEN by {0} IST - beats on the new file: {1}; start banner on Drive: {2}. Left placed; the chat reads the heartbeat later." -f (Ist), $beats.Count, $banner)
exit 2
