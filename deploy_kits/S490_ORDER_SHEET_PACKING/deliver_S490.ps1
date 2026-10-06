# =============================================================================
#  deliver_S490.ps1 - kit S490_ORDER_SHEET_PACKING - the medical PC (made from S480's deliver_S480.ps1)
#  Puts marg_txt.py S490 and KIT_MANIFEST.txt into Drive's ToMedical\_kit, from where the medical PC's agent installs the reader.
#  The watcher re-reads marg_txt.py when the file changes (S390) - no restart is needed and none is made; marg_watch.py is NOT changed.
#  Built and proven by the Sanjeevni chat on manojz (walk_s490.py: 10 of 10; the reader's own selftest; 72 kept texts, 71 the same).
#
#  Run on manojz (Windows PowerShell 5.1):   powershell -ExecutionPolicy Bypass -File deliver_S490.ps1
#  Pins:  Drive marg_txt.py       14b75012 (S480)        ->  7fa5136d (S490)
#         Drive KIT_MANIFEST.txt  ea2b437a (S480's, CRLF) ->  95a1dc5f (this folder's 5f44a5b3 with CRLF, as Drive keeps it)
#         Drive marg_watch.py     58b54f37 (S480) and marg_push.py 566e189e - must be at their pins, NOT changed
#  Backups beside them: marg_txt_S480.py.superseded, KIT_MANIFEST_S480.txt.superseded.
#  Red after placing: both put back byte-identically. No key or token is read or printed here.
#  The order sheet refused on 06-Oct 13:48 is offered to the new reader at the watcher's next start (S397's rule, texts of the last three
#  days) - or at once if the same report is exported again with any change in it.
# =============================================================================
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$T_FROM = "14b750120233e349d713d9de1d1edb7a"; $T_TO = "7fa5136d3bc134a55ffd1392d9f06675"
$M_FROM = "ea2b437a79f4829790820773e4ba26a9"; $M_LF = "5f44a5b32165c50027b2a0fc29829fc7"; $M_TO = "95a1dc5f1e5e3ffefe01207a3a9b39ce"
$W_PIN = "58b54f37865cb487720b95eaa4aedde5"; $P_PIN = "566e189e986128fa2ebb341a78b9ab65"

function Md5Bytes([byte[]]$b) { $h = [Security.Cryptography.MD5]::Create(); return ([BitConverter]::ToString($h.ComputeHash($b))).Replace("-", "").ToLower() }
function Md5File([string]$p) { return Md5Bytes ([IO.File]::ReadAllBytes($p)) }

$now = Get-Date
$tz = [TimeZoneInfo]::Local.BaseUtcOffset
if ($tz -ne [TimeSpan]::FromMinutes(330)) { Write-Output "!! this PC's clock is not IST ($tz) - nothing delivered"; exit 1 }
$kitTxt = Join-Path $here "marg_txt.py"; $kitMan = Join-Path $here "KIT_MANIFEST.txt"
if ((Md5File $kitTxt) -ne $T_TO) { Write-Output "!! this folder's marg_txt.py is not $T_TO - nothing delivered"; exit 1 }
if ((Md5File $kitMan) -ne $M_LF) { Write-Output "!! this folder's KIT_MANIFEST.txt is not $M_LF - nothing delivered"; exit 1 }
$crlf = [Text.Encoding]::UTF8.GetBytes(([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($kitMan))).Replace("`n", "`r`n"))
if ((Md5Bytes $crlf) -ne $M_TO) { Write-Output "!! the manifest with CRLF is not $M_TO - nothing delivered"; exit 1 }
$kit = $null
foreach ($L in "DEFGHIJKLMNOPQRSTUVWXYZ".ToCharArray()) {
    $p = "{0}:\My Drive\Clinic Data Archive\ToMedical\_kit" -f $L
    if (Test-Path $p) { $kit = $p; break }
}
if (-not $kit) { Write-Output "!! Drive's ToMedical\_kit is not on this PC - nothing delivered"; exit 1 }
$dT = Join-Path $kit "marg_txt.py"; $dM = Join-Path $kit "KIT_MANIFEST.txt"; $dW = Join-Path $kit "marg_watch.py"; $dP = Join-Path $kit "marg_push.py"
$liveT = Md5File $dT; $liveM = Md5File $dM
if ($liveT -eq $T_TO -and $liveM -eq $M_TO) { Write-Output "-- ALREADY DELIVERED: marg_txt.py $T_TO, KIT_MANIFEST.txt $M_TO in $kit"; exit 0 }
if ($liveT -ne $T_FROM) { Write-Output "!! $dT is $liveT, not its FROM pin $T_FROM - someone changed it; nothing delivered"; exit 1 }
if ($liveM -ne $M_FROM) { Write-Output "!! $dM is $liveM, not its FROM pin $M_FROM - someone changed it; nothing delivered"; exit 1 }
if ((Md5File $dW) -ne $W_PIN) { Write-Output "!! $dW is not $W_PIN - the watcher this reader was walked beside has changed; nothing delivered"; exit 1 }
if ((Md5File $dP) -ne $P_PIN) { Write-Output "!! $dP is not $P_PIN - the pusher has changed; nothing delivered"; exit 1 }
Write-Output ("[1/4] {0} IST - the kit's two files and Drive's two files at their pins ({1}); marg_watch.py and marg_push.py at their pins, not changed" -f $now.ToString("dd-MM-yyyy HH:mm:ss"), $kit)
$bT = Join-Path $kit "marg_txt_S480.py.superseded"; $bM = Join-Path $kit "KIT_MANIFEST_S480.txt.superseded"
if (Test-Path $bT) { $bT = Join-Path $kit "marg_txt_S480_S490.py.superseded" }
if (Test-Path $bM) { $bM = Join-Path $kit "KIT_MANIFEST_S480_S490.txt.superseded" }
[IO.File]::WriteAllBytes($bT, [IO.File]::ReadAllBytes($dT)); [IO.File]::WriteAllBytes($bM, [IO.File]::ReadAllBytes($dM))
if ((Md5File $bT) -ne $T_FROM -or (Md5File $bM) -ne $M_FROM) { Write-Output "!! the backups do not read back - nothing delivered"; exit 1 }
Write-Output "[2/4] backups: $(Split-Path -Leaf $bT) ($T_FROM), $(Split-Path -Leaf $bM) ($M_FROM)"
try {
    [IO.File]::WriteAllBytes($dT, [IO.File]::ReadAllBytes($kitTxt))
    [IO.File]::WriteAllBytes($dM, $crlf)
    $rt = Md5File $dT; $rm = Md5File $dM
    if ($rt -ne $T_TO -or $rm -ne $M_TO) { throw "read back $rt / $rm" }
} catch {
    Write-Output "!! RED after placing ($_) - putting both back byte-identically"
    [IO.File]::WriteAllBytes($dM, [IO.File]::ReadAllBytes($bM)); [IO.File]::WriteAllBytes($dT, [IO.File]::ReadAllBytes($bT))
    Write-Output ("   marg_txt.py {0} - KIT_MANIFEST.txt {1}" -f (Md5File $dT), (Md5File $dM))
    exit 1
}
Write-Output ("[3/4] placed at {0} IST; read back marg_txt.py {1}, KIT_MANIFEST.txt {2}" -f (Get-Date).ToString("dd-MM-yyyy HH:mm:ss"), $T_TO, $M_TO)
Write-Output "[4/4] now: the medical PC's heartbeat (FromMedical\heartbeat.txt) must read marg_txt.py up to date (7fa5136d) within a few minutes."
Write-Output "      The order sheet refused today is read at the watcher's next start, or at once if it is exported again with a change in it."
Write-Output "S490_ORDER_SHEET_PACKING, the medical PC: DELIVERED"
