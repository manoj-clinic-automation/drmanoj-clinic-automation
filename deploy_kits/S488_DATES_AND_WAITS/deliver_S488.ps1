# =============================================================================
#  deliver_S488.ps1 - kit S488_DATES_AND_WAITS (part E) - the medical PC (made from S480's deliver_S480.ps1)
#  Puts marg_watch.py S488 and KIT_MANIFEST.txt into Drive's ToMedical\_kit, from where the medical PC's agent installs the watcher and
#  restarts it. PACKED, NOT RUN BY CLAUDE CODE: the Sanjeevni chat reads marg_watch.py S488 in full against the brief first (F-715);
#  then the owner runs the one line below. Until then the medical PC runs 58b54f37 and nothing changes there.
#
#  Run on manojz (Windows PowerShell 5.1), from this folder:   powershell -ExecutionPolicy Bypass -File deliver_S488.ps1
#  Pins:  Drive marg_watch.py     58b54f37 (S480)       ->  0a78ae15 (S488)
#         Drive KIT_MANIFEST.txt  ea2b437a (S480's, CRLF) -> a1bf114f (this folder's 59b31641 with CRLF, as Drive keeps it)
#         Drive marg_txt.py       14b75012 (S480)  and  marg_push.py 566e189e  -- PIN ONLY: they must be these, and are not written.
#  Order on Drive: the manifest, then the watcher - changing the watcher is what makes the agent restart it.
#  Backups beside them: marg_watch_S480.py.superseded, KIT_MANIFEST_S480.txt.superseded.
#  Red after placing: both put back byte-identically. No key or token is read or printed here.
#  What changes: a refused text's body reaches FromMedical\refused_text only when it can carry no person's detail (a purchase, a list,
#  a valuation, an expiry report, the closing stock); any other leaves <stem>.withheld.txt there; every .why.txt there becomes two lines.
#  At its first census (within 10 minutes of its start) the new watcher sweeps that folder: the bodies already there that may not be
#  there are removed (Drive keeps them in its own bin for 30 days) and the whole reasons are rewritten. _captured_txt\refused on the
#  medical PC is not touched.
# =============================================================================
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$W_FROM = "58b54f37865cb487720b95eaa4aedde5"; $W_TO = "0a78ae15be60d8a0293b96ecfa38f35b"
$M_FROM = "ea2b437a79f4829790820773e4ba26a9"; $M_LF = "59b31641eced4e6ee0ba0ce0ca70a8e6"; $M_TO = "a1bf114fd9e6940befe74592ffa78322"
$T_PIN = "14b750120233e349d713d9de1d1edb7a"; $P_PIN = "566e189e986128fa2ebb341a78b9ab65"

function Md5Bytes([byte[]]$b) { $h = [Security.Cryptography.MD5]::Create(); return ([BitConverter]::ToString($h.ComputeHash($b))).Replace("-", "").ToLower() }
function Md5File([string]$p) { return Md5Bytes ([IO.File]::ReadAllBytes($p)) }

$now = Get-Date
$tz = [TimeZoneInfo]::Local.BaseUtcOffset
if ($tz -ne [TimeSpan]::FromMinutes(330)) { Write-Output "!! this PC's clock is not IST ($tz) - nothing delivered"; exit 1 }
$kitWatch = Join-Path $here "marg_watch.py"; $kitMan = Join-Path $here "KIT_MANIFEST.txt"
if ((Md5File $kitWatch) -ne $W_TO) { Write-Output "!! this folder's marg_watch.py is not $W_TO - nothing delivered"; exit 1 }
# the repository keeps the manifest LF; whatever line ends this checkout gave it, the LF form must be $M_LF and the CRLF form $M_TO
$manTxt = ([Text.Encoding]::UTF8.GetString([IO.File]::ReadAllBytes($kitMan))).Replace("`r", "")
if ((Md5Bytes ([Text.Encoding]::UTF8.GetBytes($manTxt))) -ne $M_LF) { Write-Output "!! this folder's KIT_MANIFEST.txt is not $M_LF - nothing delivered"; exit 1 }
$crlf = [Text.Encoding]::UTF8.GetBytes($manTxt.Replace("`n", "`r`n"))
if ((Md5Bytes $crlf) -ne $M_TO) { Write-Output "!! the manifest with CRLF is not $M_TO - nothing delivered"; exit 1 }
$kit = $null
foreach ($L in "DEFGHIJKLMNOPQRSTUVWXYZ".ToCharArray()) {
    $p = "{0}:\My Drive\Clinic Data Archive\ToMedical\_kit" -f $L
    if (Test-Path $p) { $kit = $p; break }
}
if (-not $kit) { Write-Output "!! Drive's ToMedical\_kit is not on this PC - nothing delivered"; exit 1 }
$dW = Join-Path $kit "marg_watch.py"; $dM = Join-Path $kit "KIT_MANIFEST.txt"; $dT = Join-Path $kit "marg_txt.py"; $dP = Join-Path $kit "marg_push.py"
$liveW = Md5File $dW; $liveM = Md5File $dM
if ($liveW -eq $W_TO -and $liveM -eq $M_TO) { Write-Output "-- ALREADY DELIVERED: marg_watch.py $W_TO, KIT_MANIFEST.txt $M_TO in $kit"; exit 0 }
if ((Md5File $dT) -ne $T_PIN) { Write-Output "!! $dT is not $T_PIN - the reader this kit was tested beside has changed; nothing delivered"; exit 1 }
if ((Md5File $dP) -ne $P_PIN) { Write-Output "!! $dP is not $P_PIN - the pusher this kit was tested beside has changed; nothing delivered"; exit 1 }
if ($liveW -ne $W_FROM) { Write-Output "!! $dW is $liveW, not its FROM pin $W_FROM - someone changed it; nothing delivered"; exit 1 }
if ($liveM -ne $M_FROM) { Write-Output "!! $dM is $liveM, not its FROM pin $M_FROM - someone changed it; nothing delivered"; exit 1 }
Write-Output ("[1/4] {0} IST - the kit's two files and Drive's two files at their pins ({1}); marg_txt.py and marg_push.py at their pins, not changed" -f $now.ToString("dd-MM-yyyy HH:mm:ss"), $kit)
$bW = Join-Path $kit "marg_watch_S480.py.superseded"; $bM = Join-Path $kit "KIT_MANIFEST_S480.txt.superseded"
if (Test-Path $bW) { $bW = Join-Path $kit "marg_watch_S480_S488.py.superseded" }
if (Test-Path $bM) { $bM = Join-Path $kit "KIT_MANIFEST_S480_S488.txt.superseded" }
[IO.File]::WriteAllBytes($bW, [IO.File]::ReadAllBytes($dW)); [IO.File]::WriteAllBytes($bM, [IO.File]::ReadAllBytes($dM))
if ((Md5File $bW) -ne $W_FROM -or (Md5File $bM) -ne $M_FROM) { Write-Output "!! the backups do not read back - nothing delivered"; exit 1 }
Write-Output "[2/4] backups: $(Split-Path -Leaf $bW) ($W_FROM), $(Split-Path -Leaf $bM) ($M_FROM)"
try {
    [IO.File]::WriteAllBytes($dM, $crlf)
    [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($kitWatch))
    $rw = Md5File $dW; $rm = Md5File $dM; $rt = Md5File $dT; $rp = Md5File $dP
    if ($rw -ne $W_TO -or $rm -ne $M_TO -or $rt -ne $T_PIN -or $rp -ne $P_PIN) { throw "read back $rw / $rm / $rt / $rp" }
} catch {
    Write-Output "!! RED after placing ($_) - putting both back byte-identically"
    [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($bW)); [IO.File]::WriteAllBytes($dM, [IO.File]::ReadAllBytes($bM))
    Write-Output ("   marg_watch.py {0} - KIT_MANIFEST.txt {1}" -f (Md5File $dW), (Md5File $dM))
    exit 1
}
Write-Output ("[3/4] placed at {0} IST; read back marg_watch.py {1}, KIT_MANIFEST.txt {2}; marg_txt.py {3} and marg_push.py {4} unchanged" -f (Get-Date).ToString("dd-MM-yyyy HH:mm:ss"), $W_TO, $M_TO, $T_PIN, $P_PIN)
Write-Output "[4/4] now: the medical PC's heartbeat (FromMedical\heartbeat.txt) must read marg_watch.py up to date (0a78ae15). Its start line in"
Write-Output "      marg_watch_log.txt still reads 'marg_watch S480 starting' (S488 changes only what is shared, not the start line) - the md5 is"
Write-Output "      the proof. Within ten minutes of that start, FromMedical\refused_text holds no sale or register text: each such text there"
Write-Output "      shows a <stem>.withheld.txt, and every .why.txt there is two lines (a stamp, and 'why:' with the short reason)."
Write-Output "S488_DATES_AND_WAITS part E, the medical PC: DELIVERED"
