#!/bin/bash
# install_S302_DAILY_PRINT.sh -- the router learns the owner's daily summary sale report (Marg's print-layout
# BILL WISE SALES STATEMENT). New type SALE_DAILY_PRINT: dated from its day line, never uploaded, and deleted
# at this door because it carries names and mobiles (PHI_TYPES). Every other report is read exactly as before.
#   /root/marg_ingest/marg_ingest.py   1a7f266f -> 7f6b4dc2  (PHI_TYPES gains SALE_DAILY_PRINT -- placed FIRST)
#   /root/marg_ingest/marg_router.py   da8fc928 -> 318086e3  (the print-layout reading, only where no header row exists)
#   /root/marg_ingest/signatures.json  65d1e1ee -> b2dcb211  (one new block -- placed LAST)
# Placed under the collector's own lock, in that order, so no run ever sees the signature without the PHI rule.
# Before anything is placed: the new three in a scratch copy -- router selftest, every kept export judged as before.
# clinic-finance restarted (the door imports these modules).
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S302_DAILY_PRINT/install_S302_DAILY_PRINT.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOWALK=1
set -u
KIT="S302_DAILY_PRINT"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; MID="$ROOT/marg_ingest"; LOCK="${LOCK:-/tmp/marg_ingest.lock}"
VPY="$ROOT/wa/venv/bin/python3"; [ -x "$VPY" ] || VPY="$(command -v python3)"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s302_walk_$STAMP"
declare -A FROM=( [marg_ingest.py]=1a7f266f0ed57392faa320543b95bb87 [marg_router.py]=da8fc9284bed077d0d86da07d95f439e [signatures.json]=65d1e1ee3cc0d564b9673a54c5da4877 )
declare -A TO=(   [marg_ingest.py]=7f6b4dc25d1c247c8b45f05108e600ca [marg_router.py]=318086e36b0088f2da57b95d19a86b98 [signatures.json]=b2dcb2115a208bff81fac1c37c839428 )
ORDER=(marg_ingest.py marg_router.py signatures.json)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
echo "== $KIT installer =="
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$f")" = "${TO[$f]}" ] || { echo "!! [1/8] the kit's $f is not the predicted file - nothing installed"; exit 1; }; done
echo "[1/8] kit sums green"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$MID/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then echo "ALREADY INSTALLED (every live md5 == its to-pin)."; exit 0; fi
for f in "${ORDER[@]}"; do
  cur="$(m5 "$MID/$f")"; echo "$f : from ${FROM[$f]} -> to ${TO[$f]} ; live $cur"
  [ "$cur" = "${FROM[$f]}" ] || { echo "!! [2/8] $MID/$f is $cur, expected ${FROM[$f]} - nothing installed"; exit 1; }
done
echo "[2/8] every live pin exact"
"$VPY" -c "import sys, os, json, tempfile, py_compile; d = tempfile.mkdtemp(); [py_compile.compile(f, cfile=os.path.join(d, f + 'c'), doraise=True) for f in sys.argv[1:3]]; json.load(open(sys.argv[3]))" marg_ingest.py marg_router.py signatures.json \
  || { echo "!! [3/8] the kit's files do not compile / parse - nothing placed"; exit 1; }
echo "[3/8] kit files compile; signatures.json parses"
if [ "${NOWALK:-0}" != "1" ]; then
  mkdir -p "$WALK" && cp -p "$MID"/*.py "$MID"/*.json "$WALK/" 2>/dev/null; [ -d "$MID/lib" ] && cp -rp "$MID/lib" "$WALK/"
  for f in "${ORDER[@]}"; do \cp -p "$f" "$WALK/$f"; done
  WOUT="$( cd "$WALK" && timeout 170 "$VPY" -B "$KDIR/walk_s302.py" "$MID" "$WALK" 2>&1 | tail -2 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q "^WALK OK" || { echo "!! [4/8] walk red - nothing placed"; rm -rf "$WALK"; exit 1; }
  rm -rf "$WALK"; echo "[4/8] walk green on a scratch copy"
else echo "[4/8] walk skipped (NOWALK=1, test only)"; fi
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="$MID/$f.bak_S302_${FROM[$f]:0:8}"; \cp -p "$MID/$f" "${BAK[$f]}" || { echo "!! [5/8] backup failed - nothing placed"; exit 1; }; echo "backup : ${BAK[$f]}"; done
restore() { echo "!! RED - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$MID/$f"; done
  rm -f "$MID"/*.S302new
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; sleep 3; fi
  for f in "${ORDER[@]}"; do echo "   $MID/$f $(m5 "$MID/$f")"; done; exit 1; }
for f in "${ORDER[@]}"; do \cp -p "$f" "$MID/$f.S302new" || { rm -f "$MID"/*.S302new; echo "!! [5/8] copy failed - nothing placed"; exit 1; }; done
exec 9>"$LOCK"
flock -w 90 9 || { rm -f "$MID"/*.S302new; echo "!! [5/8] the collector's lock stayed busy for 90 s - nothing placed; run the line again"; exit 1; }
for f in "${ORDER[@]}"; do mv -f "$MID/$f.S302new" "$MID/$f" || { flock -u 9; restore; }; done
flock -u 9; exec 9>&-
for f in "${ORDER[@]}"; do [ "$(m5 "$MID/$f")" = "${TO[$f]}" ] || restore; done
echo "[5/8] placed under the collector's lock: marg_ingest.py, then marg_router.py, then signatures.json"
if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 4
  systemctl is-active --quiet clinic-finance || { echo "!! clinic-finance not active"; restore; }
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
  echo "health : finance $c1"
  [ "$c1" = 200 ] || restore
  echo "[6/8] clinic-finance active and answering"
else echo "[6/8] restart skipped (NORESTART=1, test only)"; fi
echo "[7/8] md5 of the installed files:"; for f in "${ORDER[@]}"; do md5sum "$MID/$f"; done
echo "[8/8] $KIT: DONE -- the next daily summary print files as SALE_DAILY_PRINT instead of being refused"
