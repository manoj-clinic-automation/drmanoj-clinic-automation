#!/bin/bash
# =============================================================================
#  install_S336_QUARANTINE.sh · kit S336_QUARANTINE (session 274, Sanjeevni, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S336_QUARANTINE/install_S336_QUARANTINE.sh
#
#  D567 item 3 · Book s11.4 3d: refused files KEPT in quarantine by the one door, not deleted -- when
#  phi_scan.clean() finds no person's detail in them -- and a server-side rescan that re-judges the
#  quarantine whenever signatures.json changes and re-takes what is rescued through the same door.
#
#  FILES (all under /root/marg_ingest/):
#    marg_take.py        4bcf0243 (S240) -> full-file replacement, TO below (anchored edits, the rest byte-identical)
#    phi_scan.py         NEW
#    marg_rescan.py      NEW here -- manojz's tool (S229) vendored byte-identical, c6a28fc6
#    marg_rescan_vps.py  NEW
#  CRONTAB: one root line added, tagged # S336_QUARANTINE (06:25 daily) -- DECLARED TO THE PARENT.
#  RESTART: clinic-finance (marg_door imports marg_take at start).  No table, no finance_app.py, no portal.
# =============================================================================
set -u
KIT="S336_QUARANTINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
ING="$ROOT/marg_ingest"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s336_walk_$STAMP"
TK_FROM=4bcf0243fb5ef5fa5b974acdb83cb5ac
TK_TO=75b8056cc43ad6f3034ea1fa819ed7a8
PS_TO=45ca44aad0311657091e4364c4d81e37
RS_TO=c6a28fc62e3048c0ebbfb0c98679da8c
RV_TO=0bbd8a56aaf3ef52b68b1d8ed7d21bd3
CRON_LINE='25 6 * * * /root/wa/venv/bin/python3 -B /root/marg_ingest/marg_rescan_vps.py --if-signatures-changed --apply >> /root/marg_ingest/rescan.log 2>&1 # S336_QUARANTINE'
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 marg_take.py)" = "$TK_TO" ] && [ "$(m5 phi_scan.py)" = "$PS_TO" ] && [ "$(m5 marg_rescan.py)" = "$RS_TO" ] && [ "$(m5 marg_rescan_vps.py)" = "$RV_TO" ] \
  || { say "!! [1/8] a kit file is not its pin - nothing installed"; exit 1; }
say "[1/8] kit gates green"
if [ "$(m5 "$ING/marg_take.py")" = "$TK_TO" ] && [ "$(m5 "$ING/phi_scan.py")" = "$PS_TO" ] && [ "$(m5 "$ING/marg_rescan_vps.py")" = "$RV_TO" ]; then
  say "-- ALREADY INSTALLED"; crontab -l 2>/dev/null | grep -q "# S336_QUARANTINE" && say "   cron line present" || say "   !! cron line ABSENT"; exit 0; fi
[ "$(m5 "$ING/marg_take.py")" = "$TK_FROM" ] || { say "!! [2/8] marg_take.py is $(m5 "$ING/marg_take.py"), not the S240 pin - nothing installed"; exit 1; }
for f in phi_scan.py marg_rescan.py marg_rescan_vps.py; do [ -e "$ING/$f" ] && { say "!! [2/8] $ING/$f already exists and is not this kit's - nothing installed"; exit 1; }; done
say "[2/8] live pin exact ($TK_FROM); the three new files absent"
mkdir -p "$WALK/compile" || exit 1
cp -p marg_take.py phi_scan.py marg_rescan.py marg_rescan_vps.py selftest_s336.py "$WALK/compile/" \
  && ( cd "$WALK/compile" && "$SPY" -m py_compile marg_take.py phi_scan.py marg_rescan.py marg_rescan_vps.py selftest_s336.py \
       && "$VPY" -m py_compile marg_take.py phi_scan.py marg_rescan.py marg_rescan_vps.py selftest_s336.py ) \
  || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green on both pythons (on copies)"
SOUT="$( "$VPY" -B "$KDIR/selftest_s336.py" --ingest-src "$ING" --kit "$KDIR" 2>&1 )"
echo "$SOUT" | grep -E '^  (ok|FAIL)|selftest:' | sed 's/^/   /'
echo "$SOUT" | grep -q "^selftest: 21/21" || { say "!! [4/8] selftest red on a scratch copy of the live folder - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] selftest 21/21 on a scratch copy of the live marg_ingest (the real signatures), scratch archive and db"
Q=$(find "$ING/archive/_REFUSED" "$ING/archive/_UNKNOWN" -maxdepth 1 -type f \( -iname '*.xls' -o -iname '*.xlsx' \) 2>/dev/null | wc -l)
say "[5/8] the live quarantine holds $Q file(s) today (sidecars: $(find "$ING/archive/_REFUSED" "$ING/archive/_UNKNOWN" -maxdepth 1 -name '*.txt' 2>/dev/null | wc -l))"
BAK="$ING/marg_take.py.bak_S336_${TK_FROM:0:8}"
CBAK="$ING/crontab.bak_S336_$STAMP"
crontab -l > "$CBAK" 2>/dev/null || : > "$CBAK"
\cp -p "$ING/marg_take.py" "$BAK" || { say "!! [6/8] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$ING/marg_take.py"; rm -f "$ING/phi_scan.py" "$ING/marg_rescan.py" "$ING/marg_rescan_vps.py"
  crontab "$CBAK" 2>/dev/null || true
  systemctl restart clinic-finance || true; sleep 3
  say "   $ING/marg_take.py $(m5 "$ING/marg_take.py") · new files removed · crontab restored from $CBAK"
  exit 1
}
\cp -p phi_scan.py "$ING/phi_scan.py" && \cp -p marg_rescan.py "$ING/marg_rescan.py" && \cp -p marg_rescan_vps.py "$ING/marg_rescan_vps.py" \
  && [ "$(m5 "$ING/phi_scan.py")" = "$PS_TO" ] && [ "$(m5 "$ING/marg_rescan.py")" = "$RS_TO" ] && [ "$(m5 "$ING/marg_rescan_vps.py")" = "$RV_TO" ] || restore
\cp -p marg_take.py "$ING/marg_take.py" && [ "$(m5 "$ING/marg_take.py")" = "$TK_TO" ] || restore
rm -rf "$WALK"
say "[6/8] placed; backup $BAK · crontab backup $CBAK"
if ! crontab -l 2>/dev/null | grep -q "# S336_QUARANTINE"; then
  { crontab -l 2>/dev/null; echo "$CRON_LINE"; } | crontab - || restore
fi
crontab -l 2>/dev/null | grep -q "# S336_QUARANTINE" || restore
systemctl restart clinic-finance || restore
sleep 4
systemctl is-active --quiet clinic-finance || restore
say "[7/8] cron line placed (06:25, # S336_QUARANTINE) · clinic-finance active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
DOOR="$( cd "$ING" && "$VPY" -B -c "import marg_take as t; print('rescan' in t.SOURCES and hasattr(t, '_quarantine_clean'))" 2>/dev/null )"
say "health : finance $c2 · the placed door answers $DOOR"
[ "$c2" = 200 ] && [ "$DOOR" = "True" ] || restore
RS="$( "$VPY" -B "$ING/marg_rescan_vps.py" --if-signatures-changed --apply 2>&1 | tail -2 )"
say "   first rescan on the box (sets the signatures marker): $RS"
ST="$( "$VPY" -B "$ING/marg_rescan_vps.py" --status 2>&1 | tail -1 )"
say "[8/8] $ST"
md5sum "$ING/marg_take.py" "$ING/phi_scan.py" "$ING/marg_rescan.py" "$ING/marg_rescan_vps.py"
say "$KIT: DONE -- a refused export with no person's detail now stays in $ING/archive/_REFUSED or _UNKNOWN beside its .txt; the rescan runs 06:25 when signatures.json has changed"
