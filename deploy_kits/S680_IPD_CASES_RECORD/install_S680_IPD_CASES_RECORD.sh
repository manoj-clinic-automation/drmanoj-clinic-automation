#!/bin/bash
# =============================================================================
#  install_S680_IPD_CASES_RECORD.sh · kit S680 (the parent, session S368, 29-Oct-2026; FINAL, session S370, 30-Oct-2026) · D801 · D804
#  the IPD cases build, kit 1 of 6 -- rebuilt to the owner's review of the screens (D804) and his word of 30-Oct 12:49 / 13:07
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s680kit && cp -rp /root/deploy/repo/deploy_kits/S680_IPD_CASES_RECORD /tmp/s680kit && bash /tmp/s680kit/install_S680_IPD_CASES_RECORD.sh
#  (DRY=1 before bash: every gate, the walks and the probes, nothing written.)
#
#  THE RECORD -- Surgery cases becomes IPD cases (one record per admission). Four whole files, each pinned:
#   /root/finance/surgery_cases.py        7effc05e -> TO   type · source · payer of five · admission, IPD no., UHID, diagnosis, MLC ·
#                                                          the full mobile(s), searchable (+ the console's patients mirror, read only) ·
#                                                          three statuses (patient · hospital money · implant payment), each a filter ·
#                                                          the case opens in place in stage sections with one Next line · compact forms ·
#                                                          TPA / scheme drop-down · Case Pack number picked (case_ledger.csv, read only) ·
#                                                          old cases in the same list · Settings · a 'Call (IVR)' button per mobile
#                                                          (call_api.py, as Call ke baad) · Shavez sees all but the implant's actual cost
#   /root/portal/portal.py                1e0c6548 -> TO   the tile renamed IPD cases (its group and folder face follow)
#   /root/portal/tile_grants.json         83828b81 -> TO   v42: shavez's grant and bhawna's mask follow the new name
#   /root/wa/casepack/casepack_page.html  2dfe4221 -> TO   the Case Pack's link reads "Continue to IPD case" and carries the patient UID
#  Data: on the first request -- twelve columns added to surg_case, the tables surg_source (Clinic, DTH, Imran, Awdhesh), surg_tpa
#  (the names already on cases) and surg_call (who called, when, the last 4 digits), the old
#  rows' payer kind healed from their payer, the unit's name 'IPD cases'. Additive only; the database is copied before placing.
#  Restarts clinic-finance and clinic-portal. The Case Pack page is read per request (no restart). URLs unchanged.
#  Red after placing: all four files back from their backups, both services restarted, health read.
# =============================================================================
set -u
KIT="S680_IPD_CASES_RECORD"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; PPORT="${PPORT:-8099}"
FSVC="${FSVC:-clinic-finance}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
REL="finance/surgery_cases.py portal/portal.py portal/tile_grants.json wa/casepack/casepack_page.html"
declare -A FROM TO
FROM[finance/surgery_cases.py]=7effc05ebf1c069fb10074b4628d7a87
FROM[portal/portal.py]=1e0c6548323a083a896ef4e0d8d23951
FROM[portal/tile_grants.json]=83828b81030d007347a7cbb73a578cbf
FROM[wa/casepack/casepack_page.html]=2dfe4221e5261216d5fbe7964cfc1520
CONTROL_W="walk_s680: 60 of 77 green"
CONTROL_P="6 S680 check(s) red · 0 older red · 2 green"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s680_inst_$STAMP"
TOOK_LOCK=0; OFF_MINE=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
kf() { basename "$1"; }                                        # the kit holds each file under its own name
bak() { echo "$ROOT/$1.bak_S680_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
code() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
wait_for() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(code "$1"); [ "$h" = "$2" ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; release_lock; }
trap on_exit EXIT
stop() { say "!! STOPPED: $1"; say "   Nothing was changed. Send a photo of this screen to Claude."; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; exit 1; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting all four files back"
  for r in $REL; do [ -f "$(bak "$r")" ] && \cp -p "$(bak "$r")" "$ROOT/$r"; done
  rm -f "$FIN"/.surgery_cases.py.s680 "$ROOT"/portal/.*.s680 "$ROOT"/wa/casepack/.*.s680
  "$SYSTEMCTL" restart "$FSVC" || true
  "$SYSTEMCTL" restart "$PSVC" || true
  local f p; f=$(wait_for "http://127.0.0.1:$FIN_PORT/finance/healthz" 200); p=$(wait_for "http://127.0.0.1:$PPORT/portal/health" 200)
  for r in $REL; do say "   $ROOT/$r $(m5 "$ROOT/$r") (expected ${FROM[$r]})"; done
  say "   finance health $f · portal health $p. (The added columns and the sources table are harmless to the old files.)"
  say "   Send a photo of this screen to Claude."
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_signal INT TERM HUP
allgreen() { local g t; g=$(echo "$1" | sed -n 's/^walk_s680: \([0-9]*\) of \([0-9]*\) green$/\1/p'); t=$(echo "$1" | sed -n 's/^walk_s680: \([0-9]*\) of \([0-9]*\) green$/\2/p')
            [ -n "$g" ] && [ "$g" = "$t" ] && [ "$g" -ge 203 ]; }      # 205, or 203 where the database has no bank-statement table

say "== $KIT =="
cd "$KDIR" || { say "!! the kit folder is not there"; exit 1; }
for c in md5sum awk cp mv date curl grep sed sleep find timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || { say "!! the kit's files do not match SUMS.md5 - nothing installed"; exit 1; }
for r in $REL; do TO[$r]=$(m5 "$KDIR/$(kf "$r")"); done
say "[1/9] kit files: all match SUMS.md5"
mkdir -p "$(dirname "$LOCK")" && mkdir "$LOCK" 2>/dev/null || { say "!! another install is running (lock $LOCK). Wait 5 minutes and run the line again"; exit 1; }
TOOK_LOCK=1; echo "$KIT $STAMP" > "$LOCK/owner"
mkdir -p "$SCR" || stop "no scratch folder"
nto=0; nfrom=0; bad=""
for r in $REL; do
  h=$(m5 "$ROOT/$r")
  if [ "$h" = "${TO[$r]}" ]; then nto=$((nto+1)); elif [ "$h" = "${FROM[$r]}" ]; then nfrom=$((nfrom+1)); else bad="$bad $ROOT/$r=$h"; fi
done
if [ "$nto" = 4 ]; then say "ALREADY INSTALLED (all four files are the kit's). Nothing written."; exit 0; fi
[ -z "$bad" ] || stop "a file is neither its pinned live version nor the kit's:$bad"
[ "$nfrom" = 4 ] || stop "only $nfrom of the four files are at their pinned live version (a half-placed earlier run?) -- Claude must look"
grep -q "S579_SURGERY_CASES begin" "$FIN/finance_app.py" || stop "the finance app does not carry the S579 mount"
say "[2/9] pins: surgery_cases 7effc05e · portal 1e0c6548 · grants 83828b81 (v41) · Case Pack 2dfe4221; the S579 mount present"
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile surgery_cases.py portal.py walk_s680.py walk_s680_portal.py probe_s680.py || stop "the kit's python does not compile on $py"
done
"$APY" -c "import json,sys; d=json.load(open(sys.argv[1])); assert d['version']==42" tile_grants.json || stop "tile_grants.json is not valid v42 JSON"
say "[3/9] compiled on both pythons; the grants file is valid JSON v42"
W1="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s680.py" "$KDIR/surgery_cases.py" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk.db" || stop "no scratch copy of the database for the walk"
W2="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s680.py" "$KDIR/surgery_cases.py" --db "$SCR/walk.db" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk0.db"
W0="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s680.py" "$FIN/surgery_cases.py" --db "$SCR/walk0.db" 2>&1 | tail -1 )"
rm -f "$SCR"/walk*.db
allgreen "$W1" || stop "the walk on a made-up database is not all green ($W1)"
allgreen "$W2" || stop "the walk on a copy of the live database is not all green ($W2)"
[ "$W0" = "$CONTROL_W" ] || stop "the control is not the expected red: the live module gave '$W0', expected '$CONTROL_W'"
say "[4/9] the walk: made-up $W1 · a copy of the live database $W2 · the live module (control) $W0"
mkdir -p "$SCR/new/portal" "$SCR/old/portal"
\cp -p "$KDIR/portal.py" "$KDIR/tile_grants.json" "$SCR/new/portal/" && \cp -p "$KDIR/casepack_page.html" "$SCR/new/" || stop "could not lay out the portal walk"
\cp -p "$ROOT/portal/portal.py" "$ROOT/portal/tile_grants.json" "$SCR/old/portal/" && \cp -p "$ROOT/wa/casepack/casepack_page.html" "$SCR/old/" || stop "could not copy the live portal files"
P1="$( cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s680_portal.py" --new "$SCR/new" --base "$SCR/old" --lib "$ROOT" --scratch "$SCR/pw" 2>&1 | tail -1 )"
P0="$( cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s680_portal.py" --new "$SCR/new" --base "$SCR/old" --lib "$ROOT" --scratch "$SCR/pw0" --old 2>&1 | tail -1 )"
[ "$P1" = "8 of 8 green" ] || stop "the portal walk is not all green ($P1)"
[ "$P0" = "$CONTROL_P" ] || stop "the portal control is not the expected red: '$P0', expected '$CONTROL_P'"
say "[5/9] the portal walk (every login x role x PC): $P1 · its control on the live files: $P0"
mkdir -p "$SCR/fnew" "$SCR/fold"
for d in "$SCR/fnew" "$SCR/fold"; do
  cp -p "$FIN"/*.py "$d/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/" 2>/dev/null
  for sub in finance_ui spine vendor; do [ -d "$FIN/$sub" ] && mkdir -p "$d/$sub" && cp -rp "$FIN/$sub/." "$d/$sub/" 2>/dev/null; done
done
\cp -p "$KDIR/surgery_cases.py" "$SCR/fnew/"
copydb "$DB" "$SCR/fnew.db" && copydb "$DB" "$SCR/fold.db" || stop "no scratch copies of the database for the probe"
Q1="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s680.py" --fin "$SCR/fnew" --db "$SCR/fnew.db" 2>&1 )"
Q0="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s680.py" --fin "$SCR/fold" --db "$SCR/fold.db" --expect-red 2>&1 )"
echo "$Q1" | grep -q "^PROBE OK 15 of 15" || { echo "$Q1" | tail -14; stop "the look as manoj and shavez through the real finance app is red on copies"; }
echo "$Q0" | grep -q "^PROBE OK negative control" || { echo "$Q0" | tail -14; stop "the probe's control did not go red on the live files"; }
say "[6/9] the real finance app on copies: $(echo "$Q1" | grep '^PROBE OK') · its control: $(echo "$Q0" | grep '^PROBE OK')"
rm -rf "$SCR/fnew" "$SCR/fold" "$SCR"/*.db
f0=$(code "http://127.0.0.1:$FIN_PORT/finance/healthz"); p0=$(code "http://127.0.0.1:$PPORT/portal/health")
{ [ "$f0" = 200 ] && [ "$p0" = 200 ]; } || stop "not healthy before the install (finance $f0 · portal $p0)"
say "[7/9] healthy before the install: finance $f0 · portal $p0"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the probes green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

for r in $REL; do \cp -p "$ROOT/$r" "$(bak "$r")" && [ "$(m5 "$(bak "$r")")" = "${FROM[$r]}" ] || stop "the backup of $ROOT/$r failed"; done
DBBAK="$FIN/finance.db.bak_S680_$STAMP"
copydb "$DB" "$DBBAK" || stop "the copy of the database before the change failed"
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restarts below are this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop "could not write $OFFSW"
fi
for r in $REL; do
  Lf="$ROOT/$r"; STG="$(dirname "$Lf")/.$(basename "$Lf").s680"
  { cat "$KDIR/$(kf "$r")" > "$STG" && [ "$(m5 "$STG")" = "${TO[$r]}" ]; } || { rm -f "$STG"; stop "could not stage $Lf"; }
  chmod --reference="$Lf" "$STG" 2>/dev/null; chown --reference="$Lf" "$STG" 2>/dev/null
done
PLACED=1
for r in $REL; do Lf="$ROOT/$r"; mv -f "$(dirname "$Lf")/.$(basename "$Lf").s680" "$Lf" || restore "the rename of $Lf"; [ "$(m5 "$Lf")" = "${TO[$r]}" ] || restore "the md5 read back of $Lf"; done
say "[8/9] placed and read back: all four at their kit md5s (backups .bak_S680_*; the database copied to $(basename "$DBBAK"))"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait_for "http://127.0.0.1:$FIN_PORT/finance/healthz" 200)
c3=$(code "http://127.0.0.1:$FIN_PORT/finance/surgery")
"$SYSTEMCTL" is-active --quiet "$FSVC" || restore "$FSVC is not active"
{ [ "$c1" = 200 ] && [ "$c3" = 302 ]; } || restore "finance health $c1 / IPD cases page $c3 (302 expected without a login)"
MF=""
command -v "$JOURNALCTL" >/dev/null 2>&1 && MF="$("$JOURNALCTL" -u "$FSVC" --since "-3 min" --no-pager 2>/dev/null | grep -E "surgery_cases NOT mounted" | head -1)"
[ -z "$MF" ] || restore "the module did not mount: $MF"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c4=$(wait_for "http://127.0.0.1:$PPORT/portal/health" 200); [ "$c4" = 200 ] || restore "portal health $c4"
mkdir -p "$SCR/placed/portal" "$SCR/fpl"
\cp -p "$ROOT/portal/portal.py" "$ROOT/portal/tile_grants.json" "$SCR/placed/portal/" && \cp -p "$ROOT/wa/casepack/casepack_page.html" "$SCR/placed/"
P2="$( cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s680_portal.py" --new "$SCR/placed" --base "$SCR/old" --lib "$ROOT" --scratch "$SCR/pw2" 2>&1 | tail -1 )"
[ "$P2" = "8 of 8 green" ] || restore "the portal walk on the placed files: $P2"
cp -p "$FIN"/*.py "$SCR/fpl/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/fpl/" 2>/dev/null
for sub in finance_ui spine vendor; do [ -d "$FIN/$sub" ] && mkdir -p "$SCR/fpl/$sub" && cp -rp "$FIN/$sub/." "$SCR/fpl/$sub/" 2>/dev/null; done
copydb "$DB" "$SCR/fpl.db" || restore "no copy of the database for the look on the placed file"
Q2="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s680.py" --fin "$SCR/fpl" --db "$SCR/fpl.db" 2>&1 )"
echo "$Q2" | grep -q "^PROBE OK 15 of 15" || { echo "$Q2" | tail -14; restore "the look as manoj and shavez on the placed file is red"; }
say "[9/9] $FSVC restarted, health $c1, /finance/surgery $c3 without a login (the gate); $PSVC restarted, health $c4;"
say "      the portal walk on the placed files $P2; $(echo "$Q2" | grep '^PROBE OK') on the placed file"
[ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"
release_lock
[ -d /tmp/s581kit ] && rm -rf /tmp/s581kit && say "   housekeeping: removed /tmp/s581kit"
UNDO=""; for r in $REL; do UNDO="$UNDO\\cp -p $(bak "$r") $ROOT/$r && "; done
say ""
say "INSTALLED. Surgery cases is now IPD cases: three statuses on every case (patient, hospital money, implant payment), search by"
say "full mobile, a case opens in place in its stage sections with one Next line, compact forms, TPA names and the Case Pack number"
say "picked, old cases from 1-Apr-2025 in the same list, a 'Call (IVR)' button per mobile; Settings holds admission Rs 1,200,"
say "nursing Rs 500 a day, your share (not set yet), the sources and the TPA names. Shavez sees all but the implant's actual cost."
say "undo (one line): ${UNDO}$SYSTEMCTL restart $FSVC && $SYSTEMCTL restart $PSVC"
exit 0
