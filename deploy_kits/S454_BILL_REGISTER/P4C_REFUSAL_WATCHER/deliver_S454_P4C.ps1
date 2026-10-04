# =============================================================================
#  deliver_S454_P4C.ps1 - kit S454_BILL_REGISTER, part 4C - the medical PC, corrected (S454 section 20; made from P4B's script)
#  Puts marg_watch.py S454 P4C and KIT_MANIFEST.txt into Drive's ToMedical\_kit, from where the medical PC's agent installs them and restarts
#  the watcher. NOT BEFORE 04-Oct-2026 13:00 IST: a restart offers the reader again every refused text younger than three days, and before
#  that hour it would send the refused sale texts of 30-Sep and 01-Oct once more (S454 10.3). The script refuses to run before then.
#
#  Run on manojz (Windows PowerShell 5.1), from this folder:   powershell -ExecutionPolicy Bypass -File deliver_S454_P4C.ps1
#  Pins:  Drive marg_watch.py   81145aa7 (S397, what the medical PC runs)  ->  297cc3d9 (S454 P4C)
#         Drive KIT_MANIFEST.txt 05fb3485 (part 1's, CRLF)                 ->  9e754e5c (this folder's b8ff9568 with CRLF, as Drive keeps it;
#                                                                              P4B's bytes: no word of its S454 comment had to change)
#  P4B's watcher 20ec1602 is NEVER placed on Drive; if Drive already holds it, this script stops and says so.
#  Backups beside them: marg_watch_S397.py.superseded, KIT_MANIFEST_S454P1.txt.superseded. Red after placing: both put back byte-identically.
#  marg_push.py and marg_txt.py are not changed. No key or token is read or printed here.
# =============================================================================
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$NOT_BEFORE = [datetime]"2026-10-04 13:00:00"
$W_FROM = "81145aa7d7c8e9f7e23072cfab1ee620"; $W_TO = "297cc3d9ff5edddc894390426bdc463a"; $W_P4B = "20ec1602174cea5e2726d87797fa8e88"
$M_FROM = "05fb348589ba967e26bf8b7c9ff2aebc"; $M_LF = "b8ff9568aca2b9c6e47e54f99430444e"; $M_TO = "9e754e5c48407f0f08b72746e76a2bb2"

function Md5Bytes([byte[]]$b) { $h = [Security.Cryptography.MD5]::Create(); return ([BitConverter]::ToString($h.ComputeHash($b))).Replace("-", "").ToLower() }
function Md5File([string]$p) { return Md5Bytes ([IO.File]::ReadAllBytes($p)) }

$now = Get-Date
$tz = [TimeZoneInfo]::Local.BaseUtcOffset
if ($tz -ne [TimeSpan]::FromMinutes(330)) { Write-Output "!! this PC's clock is not IST ($tz) - nothing delivered"; exit 1 }
if ($now -lt $NOT_BEFORE) {
    Write-Output ("!! it is {0} IST: the watcher is not delivered before 04-Oct-2026 13:00 IST (S454 10.3) - nothing delivered" -f $now.ToString("dd-MM-yyyy HH:mm:ss"))
    exit 2
}
$kitWatch = Join-Path $here "marg_watch.py"; $kitMan = Join-Path $here "KIT_MANIFEST.txt"
if ((Md5File $kitWatch) -ne $W_TO) { Write-Output "!! this folder's marg_watch.py is not $W_TO - nothing delivered"; exit 1 }
if ((Md5File $kitMan) -ne $M_LF) { Write-Output "!! this folder's KIT_MANIFEST.txt is not $M_LF - nothing delivered"; exit 1 }
$crlf = [Text.Encoding]::UTF8.GetBytes(([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($kitMan))).Replace("`n", "`r`n"))
if ((Md5Bytes $crlf) -ne $M_TO) { Write-Output "!! the manifest with CRLF is not $M_TO - nothing delivered"; exit 1 }
$kit = $null
foreach ($L in "DEFGHIJKLMNOPQRSTUVWXYZ".ToCharArray()) {
    $p = "{0}:\My Drive\Clinic Data Archive\ToMedical\_kit" -f $L
    if (Test-Path $p) { $kit = $p; break }
}
if (-not $kit) { Write-Output "!! Drive's ToMedical\_kit is not on this PC - nothing delivered"; exit 1 }
$dW = Join-Path $kit "marg_watch.py"; $dM = Join-Path $kit "KIT_MANIFEST.txt"
$liveW = Md5File $dW; $liveM = Md5File $dM
if ($liveW -eq $W_TO -and $liveM -eq $M_TO) { Write-Output "-- ALREADY DELIVERED: marg_watch.py $W_TO, KIT_MANIFEST.txt $M_TO in $kit"; exit 0 }
if ($liveW -eq $W_P4B) { Write-Output "!! $dW is P4B's watcher ($W_P4B), which was never to be placed on Drive (S454 20.4) - STOP; nothing delivered"; exit 1 }
if ($liveW -ne $W_FROM) { Write-Output "!! $dW is $liveW, not its FROM pin $W_FROM - someone changed it; nothing delivered"; exit 1 }
if ($liveM -ne $M_FROM) { Write-Output "!! $dM is $liveM, not its FROM pin $M_FROM - someone changed it; nothing delivered"; exit 1 }
Write-Output ("[1/4] {0} IST - past 04-Oct 13:00; the kit's two files and Drive's two files at their pins ({1})" -f $now.ToString("dd-MM-yyyy HH:mm:ss"), $kit)
$bW = Join-Path $kit "marg_watch_S397.py.superseded"; $bM = Join-Path $kit "KIT_MANIFEST_S454P1.txt.superseded"
if (Test-Path $bW) { $bW = Join-Path $kit "marg_watch_S397_S454.py.superseded" }
if (Test-Path $bM) { $bM = Join-Path $kit "KIT_MANIFEST_S454P1_S454.txt.superseded" }
[IO.File]::WriteAllBytes($bW, [IO.File]::ReadAllBytes($dW)); [IO.File]::WriteAllBytes($bM, [IO.File]::ReadAllBytes($dM))
if ((Md5File $bW) -ne $W_FROM -or (Md5File $bM) -ne $M_FROM) { Write-Output "!! the backups do not read back - nothing delivered"; exit 1 }
Write-Output "[2/4] backups: $(Split-Path -Leaf $bW) ($W_FROM), $(Split-Path -Leaf $bM) ($M_FROM)"
try {
    [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($kitWatch))
    [IO.File]::WriteAllBytes($dM, $crlf)
    $rw = Md5File $dW; $rm = Md5File $dM
    if ($rw -ne $W_TO -or $rm -ne $M_TO) { throw "read back $rw / $rm" }
} catch {
    Write-Output "!! RED after placing ($_) - putting both back byte-identically"
    [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($bW)); [IO.File]::WriteAllBytes($dM, [IO.File]::ReadAllBytes($bM))
    Write-Output ("   marg_watch.py {0} - KIT_MANIFEST.txt {1}" -f (Md5File $dW), (Md5File $dM))
    exit 1
}
Write-Output ("[3/4] placed at {0} IST; read back marg_watch.py {1}, KIT_MANIFEST.txt {2}" -f (Get-Date).ToString("dd-MM-yyyy HH:mm:ss"), $W_TO, $M_TO)
Write-Output "[4/4] now: the medical PC's heartbeat (FromMedical\heartbeat.txt) must read 'marg_watch.py up to date (297cc3d9)' and 'WATCHER FILE ... md5 297cc3d9',"
Write-Output "      and marg_watch_log.txt must show 'marg_watch S454 P4C starting', the first-start line (texts already in refused marked, none announced,"
Write-Output "      sentinel written) and what its start offered again (S397's retry of the last three days)."
Write-Output "S454_BILL_REGISTER part 4C: DELIVERED"
