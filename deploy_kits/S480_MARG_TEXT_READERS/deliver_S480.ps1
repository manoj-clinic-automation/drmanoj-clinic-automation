# =============================================================================
#  deliver_S480.ps1 - kit S480_MARG_TEXT_READERS - the medical PC (made from S454's deliver_S454_P4C.ps1)
#  Puts marg_txt.py S480, marg_watch.py S480 and KIT_MANIFEST.txt into Drive's ToMedical\_kit, from where the medical PC's agent installs
#  them and restarts the watcher. PACKED, NOT RUN BY CLAUDE CODE: the Sanjeevni chat reads both files in full against the brief first
#  (F-715); then the owner runs the one line below. Until then the medical PC runs ed17bb76 / 297cc3d9 and nothing changes there.
#
#  Run on manojz (Windows PowerShell 5.1), from this folder:   powershell -ExecutionPolicy Bypass -File deliver_S480.ps1
#  Pins:  Drive marg_txt.py       ed17bb76 (S454)      ->  14b75012 (S480)
#         Drive marg_watch.py     297cc3d9 (S454 P4C)  ->  58b54f37 (S480)
#         Drive KIT_MANIFEST.txt  9e754e5c (P4C's, CRLF) -> ea2b437a (this folder's c9681701 with CRLF, as Drive keeps it)
#  Order on Drive: the reader, its manifest line, then the watcher - changing the watcher is what makes the agent restart it, and by then
#  the reader it needs is there. (Either order is safe: S480's watcher runs an older reader, and S454's watcher a newer one.)
#  Backups beside them: marg_txt_S454.py.superseded, marg_watch_S454P4C.py.superseded, KIT_MANIFEST_S454P4C.txt.superseded.
#  Red after placing: all three put back byte-identically. marg_push.py (566e189e) is not changed. No key or token is read or printed here.
#  At its first start the new watcher offers the reader again every text refused in the last three days (S397's rule): the purchase, list,
#  valuation, return and register texts of the last three days are then taken through the new specs.
# =============================================================================
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$T_FROM = "ed17bb763c202f81cb8b3708fac61b52"; $T_TO = "14b750120233e349d713d9de1d1edb7a"
$W_FROM = "297cc3d9ff5edddc894390426bdc463a"; $W_TO = "58b54f37865cb487720b95eaa4aedde5"
$M_FROM = "9e754e5c48407f0f08b72746e76a2bb2"; $M_LF = "c9681701ac23d4cbcf8ed39bc23e2b48"; $M_TO = "ea2b437a79f4829790820773e4ba26a9"
$P_PIN = "566e189e986128fa2ebb341a78b9ab65"

function Md5Bytes([byte[]]$b) { $h = [Security.Cryptography.MD5]::Create(); return ([BitConverter]::ToString($h.ComputeHash($b))).Replace("-", "").ToLower() }
function Md5File([string]$p) { return Md5Bytes ([IO.File]::ReadAllBytes($p)) }

$now = Get-Date
$tz = [TimeZoneInfo]::Local.BaseUtcOffset
if ($tz -ne [TimeSpan]::FromMinutes(330)) { Write-Output "!! this PC's clock is not IST ($tz) - nothing delivered"; exit 1 }
$kitTxt = Join-Path $here "marg_txt.py"; $kitWatch = Join-Path $here "marg_watch.py"; $kitMan = Join-Path $here "KIT_MANIFEST.txt"
if ((Md5File $kitTxt) -ne $T_TO) { Write-Output "!! this folder's marg_txt.py is not $T_TO - nothing delivered"; exit 1 }
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
$dT = Join-Path $kit "marg_txt.py"; $dW = Join-Path $kit "marg_watch.py"; $dM = Join-Path $kit "KIT_MANIFEST.txt"; $dP = Join-Path $kit "marg_push.py"
$liveT = Md5File $dT; $liveW = Md5File $dW; $liveM = Md5File $dM
if ($liveT -eq $T_TO -and $liveW -eq $W_TO -and $liveM -eq $M_TO) { Write-Output "-- ALREADY DELIVERED: marg_txt.py $T_TO, marg_watch.py $W_TO, KIT_MANIFEST.txt $M_TO in $kit"; exit 0 }
if ($liveT -ne $T_FROM) { Write-Output "!! $dT is $liveT, not its FROM pin $T_FROM - someone changed it; nothing delivered"; exit 1 }
if ($liveW -ne $W_FROM) { Write-Output "!! $dW is $liveW, not its FROM pin $W_FROM - someone changed it; nothing delivered"; exit 1 }
if ($liveM -ne $M_FROM) { Write-Output "!! $dM is $liveM, not its FROM pin $M_FROM - someone changed it; nothing delivered"; exit 1 }
if ((Md5File $dP) -ne $P_PIN) { Write-Output "!! $dP is not $P_PIN - the pusher this kit was walked beside has changed; nothing delivered"; exit 1 }
Write-Output ("[1/4] {0} IST - the kit's three files and Drive's three files at their pins ({1}); marg_push.py at its pin, not changed" -f $now.ToString("dd-MM-yyyy HH:mm:ss"), $kit)
$bT = Join-Path $kit "marg_txt_S454.py.superseded"; $bW = Join-Path $kit "marg_watch_S454P4C.py.superseded"; $bM = Join-Path $kit "KIT_MANIFEST_S454P4C.txt.superseded"
if (Test-Path $bT) { $bT = Join-Path $kit "marg_txt_S454_S480.py.superseded" }
if (Test-Path $bW) { $bW = Join-Path $kit "marg_watch_S454P4C_S480.py.superseded" }
if (Test-Path $bM) { $bM = Join-Path $kit "KIT_MANIFEST_S454P4C_S480.txt.superseded" }
[IO.File]::WriteAllBytes($bT, [IO.File]::ReadAllBytes($dT)); [IO.File]::WriteAllBytes($bW, [IO.File]::ReadAllBytes($dW)); [IO.File]::WriteAllBytes($bM, [IO.File]::ReadAllBytes($dM))
if ((Md5File $bT) -ne $T_FROM -or (Md5File $bW) -ne $W_FROM -or (Md5File $bM) -ne $M_FROM) { Write-Output "!! the backups do not read back - nothing delivered"; exit 1 }
Write-Output "[2/4] backups: $(Split-Path -Leaf $bT) ($T_FROM), $(Split-Path -Leaf $bW) ($W_FROM), $(Split-Path -Leaf $bM) ($M_FROM)"
try {
    [IO.File]::WriteAllBytes($dT, [IO.File]::ReadAllBytes($kitTxt))
    [IO.File]::WriteAllBytes($dM, $crlf)
    [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($kitWatch))
    $rt = Md5File $dT; $rw = Md5File $dW; $rm = Md5File $dM
    if ($rt -ne $T_TO -or $rw -ne $W_TO -or $rm -ne $M_TO) { throw "read back $rt / $rw / $rm" }
} catch {
    Write-Output "!! RED after placing ($_) - putting all three back byte-identically"
    [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($bW)); [IO.File]::WriteAllBytes($dM, [IO.File]::ReadAllBytes($bM)); [IO.File]::WriteAllBytes($dT, [IO.File]::ReadAllBytes($bT))
    Write-Output ("   marg_txt.py {0} - marg_watch.py {1} - KIT_MANIFEST.txt {2}" -f (Md5File $dT), (Md5File $dW), (Md5File $dM))
    exit 1
}
Write-Output ("[3/4] placed at {0} IST; read back marg_txt.py {1}, marg_watch.py {2}, KIT_MANIFEST.txt {3}" -f (Get-Date).ToString("dd-MM-yyyy HH:mm:ss"), $T_TO, $W_TO, $M_TO)
Write-Output "[4/4] now: the medical PC's heartbeat (FromMedical\heartbeat.txt) must read marg_txt.py and marg_watch.py up to date (14b75012, 58b54f37),"
Write-Output "      and marg_watch_log.txt must show 'marg_watch S480 starting -- text reader S480' and what its start offered again (the texts"
Write-Output "      refused in the last three days). After that: ONE detail sale export of 04-10-2026 from Marg (any day after 04-10) lands the"
Write-Output "      empty Sunday, and the orthotic proof runs by itself."
Write-Output "S480_MARG_TEXT_READERS, the medical PC: DELIVERED"
