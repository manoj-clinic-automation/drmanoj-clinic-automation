# =============================================================================
#  deliver_S491.ps1 - kit S491_MEDICAL_WATCHER_DELIVERY - the medical PC (made from S490's deliver_S490.ps1)
#  Puts marg_watch.py S488 (part E: a refused text with a person's detail stays off Drive) and KIT_MANIFEST.txt into Drive's
#  ToMedical\_kit, on the pins as they stand AFTER S490. Changing the watcher is what makes the medical PC's agent restart it.
#  It replaces deliver_S488.ps1, whose pins are S480's and which must never be run.
#
#  FOR THE RECORD: on 06-Oct-2026 15:39:22 IST this delivery was made by the Sanjeevni chat through the file tools, with these same
#  pins, backups and read-backs (the owner's PowerShell did not find deliver_S490.ps1 at its path that afternoon). Run now, this
#  script answers ALREADY DELIVERED. It stays here as the way to repeat or check the delivery.
#
#  Run on manojz (Windows PowerShell 5.1):   powershell -ExecutionPolicy Bypass -File deliver_S491.ps1
#  Pins:  Drive marg_watch.py     58b54f37 (S480)        ->  0a78ae15 (S488)
#         Drive KIT_MANIFEST.txt  95a1dc5f (S490's, CRLF) ->  d557f934 (this folder's e06e9a3e with CRLF, as Drive keeps it)
#         Drive marg_txt.py       7fa5136d (S490) and marg_push.py 566e189e - must be at their pins, NOT changed
#  Backups beside them: marg_watch_S480.py.superseded, KIT_MANIFEST_S490.txt.superseded.
#  Red after placing: both put back byte-identically. No key or token is read or printed here.
# =============================================================================
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$W_FROM = "58b54f37865cb487720b95eaa4aedde5"; $W_TO = "0a78ae15be60d8a0293b96ecfa38f35b"
$M_FROM = "95a1dc5f1e5e3ffefe01207a3a9b39ce"; $M_LF = "e06e9a3e290e956e65540a0032b80a03"; $M_TO = "d557f9346b089e039f2a48b781bd6933"
$T_PIN = "7fa5136d3bc134a55ffd1392d9f06675"; $P_PIN = "566e189e986128fa2ebb341a78b9ab65"

function Md5Bytes([byte[]]$b) { $h = [Security.Cryptography.MD5]::Create(); return ([BitConverter]::ToString($h.ComputeHash($b))).Replace("-", "").ToLower() }
function Md5File([string]$p) { return Md5Bytes ([IO.File]::ReadAllBytes($p)) }

$now = Get-Date
$tz = [TimeZoneInfo]::Local.BaseUtcOffset
if ($tz -ne [TimeSpan]::FromMinutes(330)) { Write-Output "!! this PC's clock is not IST ($tz) - nothing delivered"; exit 1 }
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
$dW = Join-Path $kit "marg_watch.py"; $dM = Join-Path $kit "KIT_MANIFEST.txt"; $dT = Join-Path $kit "marg_txt.py"; $dP = Join-Path $kit "marg_push.py"
$liveW = Md5File $dW; $liveM = Md5File $dM
if ($liveW -eq $W_TO -and $liveM -eq $M_TO) { Write-Output "-- ALREADY DELIVERED: marg_watch.py $W_TO, KIT_MANIFEST.txt $M_TO in $kit"; exit 0 }
if ($liveW -ne $W_FROM) { Write-Output "!! $dW is $liveW, not its FROM pin $W_FROM - someone changed it; nothing delivered"; exit 1 }
if ($liveM -ne $M_FROM) { Write-Output "!! $dM is $liveM, not its FROM pin $M_FROM - someone changed it; nothing delivered"; exit 1 }
if ((Md5File $dT) -ne $T_PIN) { Write-Output "!! $dT is not $T_PIN - the reader this watcher was walked beside has changed; nothing delivered"; exit 1 }
if ((Md5File $dP) -ne $P_PIN) { Write-Output "!! $dP is not $P_PIN - the pusher has changed; nothing delivered"; exit 1 }
Write-Output ("[1/4] {0} IST - the kit's two files and Drive's two files at their pins ({1}); marg_txt.py and marg_push.py at their pins, not changed" -f $now.ToString("dd-MM-yyyy HH:mm:ss"), $kit)
$bW = Join-Path $kit "marg_watch_S480.py.superseded"; $bM = Join-Path $kit "KIT_MANIFEST_S490.txt.superseded"
if (Test-Path $bW) { $bW = Join-Path $kit "marg_watch_S480_S491.py.superseded" }
if (Test-Path $bM) { $bM = Join-Path $kit "KIT_MANIFEST_S490_S491.txt.superseded" }
[IO.File]::WriteAllBytes($bW, [IO.File]::ReadAllBytes($dW)); [IO.File]::WriteAllBytes($bM, [IO.File]::ReadAllBytes($dM))
if ((Md5File $bW) -ne $W_FROM -or (Md5File $bM) -ne $M_FROM) { Write-Output "!! the backups do not read back - nothing delivered"; exit 1 }
Write-Output "[2/4] backups: $(Split-Path -Leaf $bW) ($W_FROM), $(Split-Path -Leaf $bM) ($M_FROM)"
try {
    [IO.File]::WriteAllBytes($dM, $crlf)
    [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($kitWatch))
    $rw = Md5File $dW; $rm = Md5File $dM
    if ($rw -ne $W_TO -or $rm -ne $M_TO) { throw "read back $rw / $rm" }
} catch {
    Write-Output "!! RED after placing ($_) - putting both back byte-identically"
    [IO.File]::WriteAllBytes($dW, [IO.File]::ReadAllBytes($bW)); [IO.File]::WriteAllBytes($dM, [IO.File]::ReadAllBytes($bM))
    Write-Output ("   marg_watch.py {0} - KIT_MANIFEST.txt {1}" -f (Md5File $dW), (Md5File $dM))
    exit 1
}
Write-Output ("[3/4] placed at {0} IST; read back marg_watch.py {1}, KIT_MANIFEST.txt {2}" -f (Get-Date).ToString("dd-MM-yyyy HH:mm:ss"), $W_TO, $M_TO)
Write-Output "[4/4] now: the medical PC's heartbeat (FromMedical\heartbeat.txt) must read marg_watch.py up to date (0a78ae15), and marg_watch_log.txt"
Write-Output "      a new 'starting' line and what its start offered again (the texts refused in the last three days)."
Write-Output "S491_MEDICAL_WATCHER_DELIVERY, the medical PC: DELIVERED"
