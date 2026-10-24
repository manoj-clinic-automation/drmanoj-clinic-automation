#!/bin/bash
# =============================================================================
#  install_S638_EXPIRY_WATCH.sh · kit S638 (24-Oct-2026, Sanjeevni session 348) · D771 / D777 / D780 (the owner's "yes", 21:47 IST)
#  THE EXPIRY WATCH: Marg's monthly Batch Stock filed under its own name (F-1008), read every night into the owner's list -- expired,
#  near expiry (F-1009), dump (orthotics apart), wrong batch, new products, out of stock -- on his page, Darpan's tab and Amir's card;
#  riding along: F-1015 (reception's late card names the medicines), F-1014 (an SMS-seen NEFT tells the suppliers), D778 (Shivani's
#  'Aaj ki reports' tile).  READ-ONLY for every stock figure: proved byte-identical by the walk.
#
#   /root/finance/sanjeevni_approvals.py          792f4a9a -> TO   (the page /finance/sanjeevni/expiry, its settings, Needs-you lines)
#   /root/finance/darpan_kal.py                   6159b75b -> TO   (the order tab's payload: sell_first)
#   /root/finance/darpan_kal.html                 81dbb26a -> TO   (the tab draws it)
#   /root/finance/amir_day.py                     2c99c29e -> TO   (his card: the Batch Stock card, write-offs, batch fixes)
#   /root/finance/porders_s454.py                 647f2925 -> TO   (F-1015)
#   /root/finance/supplier_msg.py                 4e3911a7 -> TO   (F-1014: the pay card's confirm)
#   /root/finance/bank_sms.py                     aa527840 -> TO   (F-1014: the OK queues the messages)
#   /root/finance/finance_ui/finance_approvals.html b32da7ff -> TO (a Needs-you line with href opens its page; the link row)
#   /root/finance/spine/near_expiry.py            627a3915 -> TO   (replaced whole: the nightly runs the expiry watch; crontab unchanged)
#   /root/finance/expiry_watch.py                 NEW
#   /root/portal/tile_grants.json                 6498a916 -> TO   (THE PARENT'S FILE -- D778, a PLANNED line on the board; the portal
#                                                                    re-reads it by its mtime: no portal restart)
#   /root/marg_ingest/signatures.json             21604e0f -> TO   (BATCH_STOCK before the batch-wise STOCK_CLOSING; read per take)
#  finance.db: backed up first (backup API); the first pass then creates stock_expiry_run / stock_expiry_line and seeds the eight
#  expiry.* settings. No crontab change. One restart of clinic-finance. The medical PC's reader (marg_txt.py S638) goes by Drive
#  ToMedical\_kit (README, "the medical-PC half") -- not by this script.
#  ORDER: gates (window 08:02-23:49 IST, SUMS, KIT_ID) -> the build lock -> ALREADY INSTALLED? -> the FROM pins -> build from the live
#  bytes (make_s638.py) -> compile (both pythons) -> scratch: the databases and the spine by the backup API, the box twice (OLD, NEW) ->
#  walk NEW (green) and OLD (--expect-red: every C: red) -> DRY stops -> backups -> DOCTOR_AUTO_OFF -> staged + renamed -> md5 read back
#  -> ONE restart -> healthz 200, the page 302 without a login, journal clean -> the first pass (facts printed) -> DOCTOR_AUTO_OFF removed
#  -> lock released -> DONE.  Red after placing: every file back from its backup, expiry_watch.py removed, one restart, healthz.
#  Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S638_EXPIRY_WATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
SHD="${SHD:-/root/shared}"
DB="${DB:-$FIN/finance.db}"
ADB="${ADB:-/root/assetapp/assets.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
# relative path (as make_s638 writes it) -> live path
declare -A LIVE FROM TO
LIVE[finance/sanjeevni_approvals.py]=$FIN/sanjeevni_approvals.py
LIVE[finance/darpan_kal.py]=$FIN/darpan_kal.py
LIVE[finance/darpan_kal.html]=$FIN/darpan_kal.html
LIVE[finance/amir_day.py]=$FIN/amir_day.py
LIVE[finance/porders_s454.py]=$FIN/porders_s454.py
LIVE[finance/supplier_msg.py]=$FIN/supplier_msg.py
LIVE[finance/bank_sms.py]=$FIN/bank_sms.py
LIVE[finance/finance_ui/finance_approvals.html]=$FIN/finance_ui/finance_approvals.html
LIVE[finance/spine/near_expiry.py]=$FIN/spine/near_expiry.py
LIVE[portal/tile_grants.json]=$POR/tile_grants.json
LIVE[marg_ingest/signatures.json]=$MARG/signatures.json
NEWREL="finance/expiry_watch.py"; LIVE[finance/expiry_watch.py]=$FIN/expiry_watch.py
EREL="finance/sanjeevni_approvals.py finance/darpan_kal.py finance/darpan_kal.html finance/amir_day.py finance/porders_s454.py finance/supplier_msg.py finance/bank_sms.py finance/finance_ui/finance_approvals.html finance/spine/near_expiry.py portal/tile_grants.json marg_ingest/signatures.json"
PYREL="finance/sanjeevni_approvals.py finance/darpan_kal.py finance/amir_day.py finance/porders_s454.py finance/supplier_msg.py finance/bank_sms.py finance/spine/near_expiry.py finance/expiry_watch.py"
FROM[finance/sanjeevni_approvals.py]=792f4a9af1728c76e8d5a656f5662421
FROM[finance/darpan_kal.py]=6159b75b09257d5087111f6aebac611a
FROM[finance/darpan_kal.html]=81dbb26a02043562bac6476326d9b9ed
FROM[finance/amir_day.py]=2c99c29eff254c9abfe1374b2e3f8ba3
FROM[finance/porders_s454.py]=647f29255e849e11afd4221b050b215b
FROM[finance/supplier_msg.py]=4e3911a79096a6c0ba48f2b0e698ed1e
FROM[finance/bank_sms.py]=aa5278403ec85c898d808486e4c3cde3
FROM[finance/finance_ui/finance_approvals.html]=b32da7ffe605ce2440414febb8cf7bce
FROM[finance/spine/near_expiry.py]=627a3915727fce3595c2fdfb11b8f01a
FROM[portal/tile_grants.json]=6498a9169ff5e088cbdff46317a4e00f
FROM[marg_ingest/signatures.json]=21604e0fa84f0403e1a86e7584c3a1bd
while read -r h f; do TO[$f]=$h; done < "$KDIR/TO_PINS.md5"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s638_inst_$STAMP"
DBBAK="$DB.bak_S638_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
bak() { echo "${LIVE[$1]}.bak_S638_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting every file back"
  for r in $EREL; do \cp -p "$(bak "$r")" "${LIVE[$r]}" || say "   !! could not put back ${LIVE[$r]}"; done
  rm -f "$FIN/expiry_watch.py" "$FIN"/.*.s638 "$FIN"/finance_ui/.*.s638 "$FIN"/spine/.*.s638 "$POR"/.*.s638 "$MARG"/.*.s638
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for r in $EREL; do say "   ${LIVE[$r]} $(m5 "${LIVE[$r]}") (expected ${FROM[$r]})"; done
  say "   expiry_watch.py removed; finance healthz $h; the first pass had not run: the database is as it was; its backup $DBBAK is kept"
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep sleep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/9] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for r in $EREL; do [ -f "${LIVE[$r]}" ] || { say "!! [1/9] ${LIVE[$r]} is not there - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$FIN/spine/spine.db" ] || { say "!! [1/9] finance.db or the spine is missing - nothing installed"; exit 1; }
ALL=1; for r in $EREL $NEWREL; do [ "$(m5 "${LIVE[$r]}")" = "${TO[$r]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the twelve files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/9] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/9] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

for r in $EREL; do C="$(m5 "${LIVE[$r]}")"; [ "$C" = "${FROM[$r]}" ] || stop_unlocked "!! [2/9] ${LIVE[$r]} is $C, expected ${FROM[$r]} - it changed after this kit was built: STOP, nothing installed"; done
[ -e "$FIN/expiry_watch.py" ] && stop_unlocked "!! [2/9] $FIN/expiry_watch.py already exists ($(m5 "$FIN/expiry_watch.py")) - not this kit's: STOP, nothing installed"
say "[2/9] live pins exact: eleven files at their FROM; expiry_watch.py absent"
say "       read only (not pinned): stock_figure.py $(m5 "$FIN/stock_figure.py" | cut -c1-8) . purchase_app.py $(m5 "$FIN/purchase_app.py" | cut -c1-8) . order_track.py $(m5 "$FIN/order_track.py" | cut -c1-8) . section_map.py $(m5 "$FIN/section_map.py" | cut -c1-8) . marg_take.py $(m5 "$MARG/marg_take.py" | cut -c1-8) . marg_router.py $(m5 "$MARG/marg_router.py" | cut -c1-8)"

mkdir -p "$SCR/built" "$SCR/pyc" "$SCR/pc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s638.py --finance "$FIN" --marg "$MARG" --portal "$POR" --out "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/9] the builder refused a live file - nothing installed"; }
for r in $EREL $NEWREL; do [ "$(m5 "$SCR/built/$r")" = "${TO[$r]}" ] || stop_unlocked "!! [3/9] rebuilt, $r is $(m5 "$SCR/built/$r"), not ${TO[$r]} - nothing installed"; done
for py in "$APY" "$VPY"; do for r in $PYREL; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$r" || stop_unlocked "!! [3/9] the built $r does not compile on $py - nothing installed"; done; done
"$APY" -c "import json,sys; json.load(open(sys.argv[1])); json.load(open(sys.argv[2]))" "$SCR/built/portal/tile_grants.json" "$SCR/built/marg_ingest/signatures.json" \
  || stop_unlocked "!! [3/9] a built JSON file does not parse - nothing installed"
cp -p "$KDIR/marg_txt.py" "$SCR/pc/marg_txt.py" && [ "$(m5 "$SCR/pc/marg_txt.py")" = "${TO[medical/marg_txt.py]}" ] || stop_unlocked "!! [3/9] the kit's medical reader is not its TO - nothing installed"
say "[3/9] rebuilt here from this box's live bytes: each at its TO pin; the Python compiles under both pythons; the JSON parses"

copydb "$DB" "$SCR/base.db" && copydb "$FIN/spine/spine.db" "$SCR/spine_live.db" || stop_unlocked "!! [4/9] no copy of the databases - nothing installed"
if [ -f "$ADB" ]; then copydb "$ADB" "$SCR/base_a.db" || stop_unlocked "!! [4/9] no copy of assets.db - nothing installed"; else "$APY" -c "import sqlite3,sys; sqlite3.connect(sys.argv[1]).close()" "$SCR/base_a.db"; fi
mkside() {
  local d="$SCR/$1"; mkdir -p "$d/fin/spine" "$d/fin/finance_ui" "$d/marg/lib" "$d/marg/archive" "$d/por" "$d/shared"
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$d/fin/" 2>/dev/null; cp -p "$FIN"/*.sql "$d/fin/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/fin/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/fin/spine/" 2>/dev/null
  cp -p "$MARG"/*.py "$MARG"/*.json "$d/marg/" 2>/dev/null; cp -p "$MARG"/lib/*.py "$d/marg/lib/" 2>/dev/null
  for x in xlrd; do [ -d "$MARG/$x" ] && cp -rp "$MARG/$x" "$d/marg/"; done
  cp -p "$SHD"/*.py "$d/shared/" 2>/dev/null
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$d/por/"; done
  cp -p "$POR/tile_grants.json" "$d/por/"
  cp -p "$SCR/base.db" "$d/finance.db" && cp -p "$SCR/base_a.db" "$d/assets.db" && cp -p "$SCR/spine_live.db" "$d/fin/spine/spine.db"
}
for side in new old; do rm -rf "$SCR/$side"; mkside "$side" || stop_unlocked "!! [4/9] no scratch side '$side' - nothing installed"; done
for r in $EREL $NEWREL; do top="${r%%/*}"; rest="${r#*/}"; case "$top" in finance) dst="$SCR/new/fin/$rest";; portal) dst="$SCR/new/por/$rest";; marg_ingest) dst="$SCR/new/marg/$rest";; esac; cp -p "$SCR/built/$r" "$dst"; done
say "[4/9] scratch: finance.db, assets.db and the spine by the backup API; the box twice -- NEW (the twelve built files) and OLD (as they are)"
w638() { ( cd /tmp && SHARED_LIB_DIR="$SCR/$1/shared" timeout 2400 "$APY" -B "$KDIR/walk_s638.py" --side "$SCR/$1" --pc "$SCR/pc" "${@:2}" 2>&1 ) | mask; }
w638 new > "$SCR/walk_new.txt"; w638 old --expect-red > "$SCR/walk_old.txt"
say "       walk NEW: $(grep '^WALK' "$SCR/walk_new.txt") . walk OLD: $(grep '^WALK' "$SCR/walk_old.txt")"
grep -q "^WALK OK S638" "$SCR/walk_new.txt" || { cat "$SCR/walk_new.txt"; stop_unlocked "!! [5/9] the walk on the NEW files is red - nothing installed"; }
grep -q "^WALK NEGATIVE CONTROL RED S638" "$SCR/walk_old.txt" || { cat "$SCR/walk_old.txt"; stop_unlocked "!! [5/9] the negative control is not red on the OLD files - nothing installed"; }
say "[5/9] the walks: NEW green, OLD red on every control"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and both walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; } || stop_unlocked "!! [6/9] the walks ran past 23:49 IST - nothing placed; run it again tomorrow"
copydb "$DB" "$DBBAK" || stop_unlocked "!! [6/9] could not back up the database - nothing placed"
for r in $EREL; do \cp -p "${LIVE[$r]}" "$(bak "$r")" && [ "$(m5 "$(bak "$r")")" = "${FROM[$r]}" ] || stop_unlocked "!! [6/9] could not write the backup of ${LIVE[$r]} - nothing placed"; done
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop_unlocked "!! [6/9] could not write $OFFSW - nothing placed"
fi
for r in $EREL $NEWREL; do
  L="${LIVE[$r]}"; STG="$(dirname "$L")/.$(basename "$L").s638"
  { cat "$SCR/built/$r" > "$STG" && [ "$(m5 "$STG")" = "${TO[$r]}" ]; } || { rm -f "$FIN"/.*.s638 "$FIN"/finance_ui/.*.s638 "$FIN"/spine/.*.s638 "$POR"/.*.s638 "$MARG"/.*.s638; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; stop_unlocked "!! [6/9] could not stage $L - nothing placed"; }
  if [ -f "$L" ]; then chmod --reference="$L" "$STG" 2>/dev/null; chown --reference="$L" "$STG" 2>/dev/null; else chmod --reference="$FIN/amir_day.py" "$STG" 2>/dev/null; chown --reference="$FIN/amir_day.py" "$STG" 2>/dev/null; fi
done
PLACED=1
for r in $EREL $NEWREL; do L="${LIVE[$r]}"; mv -f "$(dirname "$L")/.$(basename "$L").s638" "$L" || restore "the rename of $L"; [ "$(m5 "$L")" = "${TO[$r]}" ] || restore "the md5 read back of $L"; done
say "[6/9] placed and read back: twelve files at their TO pins (backups *.bak_S638_<from8>; the database $DBBAK)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000; for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/sanjeevni/expiry); c3=$(health /finance/porders/s454/late)
case "$c2" in 302|401|303) ;; *) restore "the expiry page answered $c2 without a login (302 = the login gate, expected)";; esac
case "$c3" in 302|401|303) ;; *) restore "the late page answered $c3 without a login (302 = the login gate, expected)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q -i "not mounted" && restore "a finance module not mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[7/9] $SVC restarted at $T0 (the box's clock) and active - healthz $c1 - expiry page $c2, late page $c3 without a login; journal clean"

say "       the first pass (the nightly, once, as cron runs it):"
( cd "$FIN/spine" && timeout 900 "$VPY" -B near_expiry.py 2>&1 ) | mask | sed 's/^/       /'
NRUN="$("$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); print(c.execute('SELECT COUNT(*) FROM stock_expiry_run WHERE ok=1').fetchone()[0])" "$DB" 2>/dev/null)"
[ "${NRUN:-0}" -ge 1 ] && say "       first pass: a list is made (stock_expiry_run ok rows $NRUN)" || say "       !! the first pass made no list -- the pages show 'no list yet'; tonight's 23:57 run tries again (named in the report)"
"$APY" - "$DB" <<'PYEOF' 2>&1 | mask | sed 's/^/       /'
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
r = c.execute("SELECT id, at, export_name, counts, substr(note,1,160) FROM stock_expiry_run ORDER BY id DESC LIMIT 1").fetchone()
print("stock_expiry_run:", r)
print("settings:", c.execute("SELECT COUNT(*) FROM setting WHERE key LIKE 'expiry.%'").fetchone()[0], "expiry.* keys")
print("Batch Stock received this month:", c.execute("SELECT COUNT(*) FROM mi_file WHERE type='BATCH_STOCK' AND substr(received_at,1,7)=strftime('%Y-%m','now','localtime')").fetchone()[0])
PYEOF
if [ "$OFF_MINE" = 1 ]; then rm -f "$OFFSW"; say "[8/9] $OFFSW removed (this kit's)"; else say "[8/9] $OFFSW not this kit's -- left as found"; fi
release_lock
say "[9/9] the build lock released"
UNDO=""; for r in $EREL; do UNDO="$UNDO\\cp -p $(bak "$r") ${LIVE[$r]} && "; done
say "undo (one line): ${UNDO}rm -f $FIN/expiry_watch.py && $SYSTEMCTL restart $SVC"
say "$KIT: DONE"
exit 0
