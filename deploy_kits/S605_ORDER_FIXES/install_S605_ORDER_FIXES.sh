#!/bin/bash
# =============================================================================
#  install_S605_ORDER_FIXES.sh · kit S605 (20-Oct-2026) · brief claude_code_briefs/S605_ORDER_FIXES.md (v1)
#  D749 / F-959 (Darpan says yes to the orthotic list first), F-960 + F-702 (one hand-out per message), F-961 (the send-all asks once),
#  F-962 (the call row on the home), the numbers (Call / WhatsApp on the cards and both PDFs), F-951 (the orthotic sizes keep their own
#  key in the spine), F-957 (the walks of S603 and S598 lay their own days).
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S605_ORDER_FIXES), 08:02-23:49 IST only:
#    rm -rf /tmp/s605kit && cp -rp <kit> /tmp/s605kit && bash /tmp/s605kit/install_S605_ORDER_FIXES.sh
#  (DRY=1 before bash: every gate, the scratch sides, the spine builds and the walks; nothing written, no lock, no wait.)
#
#   /root/finance/order_sheet.py        1f1e85c1 -> TO  ortho_offer / ortho_kept / ortho_answer / darpan_ortho; entries() reads the kept lines;
#                                                         wa_plan; whatsapp_all(expect); withdraw_late: handed + unconfirmed -> sent; owner lines
#   /root/finance/porders_s454.py       40f1755a -> TO  the confirm screen (GET /finance/porders/s454/order/whatsapp); #waall a link; the unlock line;
#                                                         the home's call row; nums_text on the cards, Ho chuke and the confirm list
#   /root/finance/supplier_msg.py       6366ed0f -> TO  api_next hands a message once (the owner's test apart); the setup page's sentence
#   /root/finance/order_sheet_pdf.py    7fca11db -> TO  the band: "Call: … · WhatsApp: …" ("Ph." retired)
#   /root/finance/marg_order_pdf.py     c9cd44a5 -> TO  a shaded "Phone book — Call: … · WhatsApp: …" line under each supplier's group
#   /root/finance/darpan_kal.py         b28d7342 -> TO  the section's payload (order_sheet.darpan_ortho); POST /finance/darpan/kal/api/ortho
#   /root/finance/darpan_kal.html       7c939191 -> TO  Orthotic kam hai -- N · Yuvika ko order?: हटाओ, हाँ, ऑर्डर में डालो / इस बार नहीं
#   /root/finance/spine/spine_build.py  e3d3ed85 -> TO  a rename of a shared old key keeps its own key (sp_alias rename_family, RENAME_SPLIT)
#   the clone's DUTY_MAP.json b75ea78e (v16) -> v17 and DUTY_MAP.md (Darpan's orthotic row, one dated line): placed by the PUBLISH, never here.
#   finance.db: ONE new table, ortho_yes (made by order_sheet.ensure on the first read after the restart). No DELETE, no hand edit, no setting.
#  Read only, must not move: purchase_app 447b745f, amir_day 1169a3d6, stock_app 40f2c922, stock_watch f0d9092a, amir_salts fc5c1d16,
#  stock_figure 51e1fc63, order_rules 8d078dbe, porders e5a5c4d4, porders.html 7a6799ae, spine/spine_read 10697b38, spine/spine_rules.json dd6c7616;
#  proved unmoved: finance_app, portal.py, tile_grants.json, the crontab (84 lines).
#  ORDER: gates -> pins (ALREADY first) + the read-only md5s + the clone's DUTY_MAP + the crontab -> the spine green and fresh -> the live facts
#  printed (today's orders, order messages, audit rows, the orthotic card, order.source) -> the wait (30 min at most, every 2) until no order
#  message was queued or handed in the last 10 minutes -> build from the live bytes -> compile (both pythons) -> scratch: the spine built OLD
#  and NEW (spine_cmp_s605: the stop conditions of 3.6) -> the finance folder twice (OLD, NEW with the NEW spine) -> walk_s605 OLD (red) and
#  NEW -> S604's walk on NEW -> F-957: S603's and S598's walks (S605's copies) on NEW (green) and on their own OLD files (every control red)
#  -> DRY stops -> the install-day state before / as NEW -> backups -> DOCTOR_AUTO_OFF -> the files staged and renamed in ONE command -> ONE
#  restart of clinic-finance -> healthz 200, the pages 302 -> journal clean -> one spine build as the cron runs it (its gate quoted; a failed
#  build puts the old spine_build.py back) -> the state AFTER -> nothing else moved -> md5 read-back -> DOCTOR_AUTO_OFF removed.
#  Red after placing: the files back from their .bak_S605_<from8>, one restart, healthz; ortho_yes stays, unread. The build lock stays held
#  until the report is written (released with rm -f .../owner; rmdir ...). Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S605_ORDER_FIXES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
DB="${DB:-$FIN/finance.db}"
REPO="${REPO:-/root/deploy/repo}"
BRIEFS="$REPO/claude_code_briefs"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
S603KIT="$REPO/deploy_kits/S603_AMIR_CALENDAR_SAFE"
S598KIT="$REPO/deploy_kits/S598_ARRIVALS_BY_LINE"
S604KIT="$REPO/deploy_kits/S604_PAY_SHEET_FIXES"
S604TEXT="${S604_TEXT:-/tmp/s604data/text_080612.txt}"
S604TEXT_MD5=405e52bbc187ac6c20d44712ae33549a
ROWS598="$FIN/purchase_order_line.bak_S598_20261019_095314.json"
ROWS598_MD5=a0d31a256afd3cdabdcdf1a4b3a54166
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDITED="order_sheet.py porders_s454.py supplier_msg.py order_sheet_pdf.py marg_order_pdf.py darpan_kal.py darpan_kal.html spine/spine_build.py"
declare -A FROM TO READ
FROM[order_sheet.py]=1f1e85c12c64521b50a10cea48220170
FROM[porders_s454.py]=40f1755a7655deb733765456b9a466fe
FROM[supplier_msg.py]=6366ed0f75e0496fcd5ea98866dbddbd
FROM[order_sheet_pdf.py]=7fca11db1c016ec86a0c57c5020a7079
FROM[marg_order_pdf.py]=c9cd44a55d4cb39247d3c2e8e2602f1d
FROM[darpan_kal.py]=b28d7342469814e85129602ea35a7423
FROM[darpan_kal.html]=7c9391912cf62972a8d9e3a41e9e2ebb
FROM[spine/spine_build.py]=e3d3ed85973eab2df0326dc9621e230e
DUTY_FROM=b75ea78ea5c65005d2a6420960bad19c
READ[purchase_app.py]=447b745f16c81ef62d389900d1d8ae13
READ[amir_day.py]=1169a3d6ae451ebb4c9806052de0856c
READ[stock_app.py]=40f2c92260ae6b6715d49729fef464ff
READ[stock_watch.py]=f0d9092a051c4cd043645e4510ef4cee
READ[amir_salts.py]=fc5c1d169cf971deb6b59010141a4550
READ[stock_figure.py]=51e1fc63ab3fb1ac21170cb214f15b6b
READ[order_rules.py]=8d078dbe1b63a4706dc6f35e3c31ac9a
READ[porders.py]=e5a5c4d4dfa15c3ecd0b0cdf4786abcd
READ[porders.html]=7a6799ae3c8b41e783051cd1280a6964
READ[spine/spine_read.py]=10697b3869218151a75268e2259248d7
READ[spine/spine_rules.json]=dd6c761665ce38fe4ec65d25b6102265
# S603's and S598's OLD files (their own backups on this box) -- the OLD sides of the F-957 walks
B603="amir_day.py:3af992d9e6b6c6050b1427e34757ca78 stock_app.py:4f73d0b02a167289d9439af7a35b5fa0 stock_watch.py:299c3ef76b73a10e4af1cd15974c7a3f amir_salts.py:d8d9ba772650a4d804add6953790d14d"
B598="stock_figure.py:92367a196b360f0cded4cda6a5ded700 stock_watch.py:c5f3ce21a785c45df58f21932cf920e7 porders.py:78ea72be7d87a7c56c65de7d4c96a952"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s605_inst_$STAMP"
PLACED=0
SPINE_PLACE=1
DBBAK="$FIN/finance.db.bak_S605_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S605_${FROM[$1]:0:8}"; }
stg() { echo "$(dirname "$FIN/$1")/.$(basename "$1").s605"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
on_exit() { [ "${KEEP:-0}" = 1 ] && [ "${DRY:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
sqlro() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); [print('   ', *[str(x) for x in r]) for r in c.execute(sys.argv[2]).fetchall()]" "$1" "$2" 2>/dev/null | mask; }
placed_list() { for n in $EDITED; do if [ "$n" = spine/spine_build.py ] && [ "$SPINE_PLACE" != 1 ]; then continue; fi; echo "$n"; done; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back from their .bak_S605_* in one command"
  for n in $(placed_list); do \cp -p "$(bak "$n")" "$FIN/$n" || say "   !! could not put back $n"; done
  rm -f "$FIN"/.*.s605 "$SPN"/.*.s605
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $(placed_list); do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h; the database backup stays: $DBBAK; the table ortho_yes stays, unread"
  rm -f "$OFFSW"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort cmp crontab diff flock; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"
{ { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/12] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/12] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/12] KIT_ID.txt names another kit - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/12] PINS.sh missing - nothing installed"; exit 1; }
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/12] $FIN/$n is not there - nothing installed"; exit 1; }; done
[ -f "$BRIEFS/DUTY_MAP.json" ] && [ -f "$BRIEFS/DUTY_MAP.md" ] || { say "!! [1/12] the clone's DUTY_MAP.json / DUTY_MAP.md is missing - nothing installed"; exit 1; }
for kf in "$S603KIT:DUTY_MAP.json" "$S598KIT:rejudge_s598.py" "$S598KIT:undo_s598.py" "$S604KIT:walk_s604.py" "$S604KIT:marg_txt.py"; do   # the files this kit reads from them, by their own SUMS
  k="${kf%%:*}"; f="${kf#*:}"
  ( cd "$k" && grep -E "  $f\$" SUMS.md5 | md5sum -c - >/dev/null 2>&1 ) || { say "!! [1/12] $k/$f is missing or fails its kit's SUMS - nothing installed"; exit 1; }
done
[ "$(m5 "$S604TEXT")" = "$S604TEXT_MD5" ] || { say "!! [1/12] S604's text ($S604TEXT, md5 ${S604TEXT_MD5:0:8}) is not here -- S604's walk needs it; nothing installed"; exit 1; }
[ "$(m5 "$ROWS598")" = "$ROWS598_MD5" ] || { say "!! [1/12] the S598 install's rows JSON is not at its pin - nothing installed"; exit 1; }
for p in $B603; do n="${p%%:*}"; h="${p#*:}"; [ "$(m5 "$FIN/$n.bak_S603_${h:0:8}")" = "$h" ] || { say "!! [1/12] $n.bak_S603_${h:0:8} is not here at its md5 - nothing installed"; exit 1; }; done
for p in $B598; do n="${p%%:*}"; h="${p#*:}"; [ "$(m5 "$FIN/$n.bak_S598_${h:0:8}")" = "$h" ] || { say "!! [1/12] $n.bak_S598_${h:0:8} is not here at its md5 - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: the eight files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz); the clone's DUTY_MAP.json $(m5 "$BRIEFS/DUTY_MAP.json" | cut -c1-8) (v17 = ${TO[DUTY_MAP.json]:0:8}, placed by the publish)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/12] DRY RUN: kit gates green (SUMS, KIT_ID, PINS, S603's / S598's / S604's kits, S604's text, S598's rows, the backups, the window); no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/12] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/12] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi

for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, expected ${FROM[$n]} - it changed after the brief: STOP, nothing installed"; exit 1; }; done
say "[2/12] live pins exact: $(for n in $EDITED; do printf '%s %s . ' "$n" "${FROM[$n]:0:8}"; done)"
DM5="$(m5 "$BRIEFS/DUTY_MAP.json")"
if [ "$DM5" = "$DUTY_FROM" ]; then say "       the clone's DUTY_MAP.json $DM5 (v16, the brief's pin; v17 reaches it by the publish)";
elif [ "$DM5" = "${TO[DUTY_MAP.json]}" ]; then say "       the clone's DUTY_MAP.json is already v17 ($DM5) - the publish has landed; fine";
else say "!! [2/12] the clone's DUTY_MAP.json is $DM5, neither v16 ($DUTY_FROM) nor the kit's v17 - STOP, nothing installed"; exit 1; fi
say "       the read-only files' live md5s (the brief, section 1):"
for n in purchase_app.py amir_day.py stock_app.py stock_watch.py amir_salts.py stock_figure.py order_rules.py porders.py porders.html spine/spine_read.py spine/spine_rules.json; do
  C="$(m5 "$FIN/$n")"; say "         $n $C"
  [ "$C" = "${READ[$n]}" ] || { say "!! [2/12] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading it: STOP, nothing installed"; exit 1; }
done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SPN/spine.db" ] && [ -f "$SPN/spine_state.json" ] && [ -d "$SPN/readings" ] && [ -f "$POR/tile_grants.json" ] || { say "!! [2/12] a database, the spine or the portal is missing - nothing installed"; exit 1; }
CRONN="$(crontab -l 2>/dev/null | wc -l | awk '{print $1}')"
say "       the crontab: $CRONN lines"
[ "$CRONN" = 84 ] || { say "!! [2/12] the crontab is not as the brief read it (84 lines) - STOP, nothing installed"; exit 1; }
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
SP_AGE="$("$APY" -c "import sys,datetime as d; t=d.datetime.fromisoformat(sys.argv[1]); print(int((d.datetime.now(t.tzinfo)-t).total_seconds()//60))" "$SP_AT" 2>/dev/null || echo 9999)"
GATE_N="${SP_GATE%/*}"; GATE_D="${SP_GATE#*/}"
[ "$SP_OK" = True ] && [ -n "$GATE_N" ] && [ "$GATE_N" = "$GATE_D" ] && [ "$SP_AGE" -le 30 ] \
  || { say "!! [2/12] the spine is red or stale (passed $SP_OK, gate $SP_GATE, last success $SP_AT, $SP_AGE min ago) - nothing installed (charter 1b)"; exit 4; }
NOTT=("$FIN/purchase_app.py" "$FIN/amir_day.py" "$FIN/stock_app.py" "$FIN/stock_watch.py" "$FIN/amir_salts.py" "$FIN/stock_figure.py" "$FIN/order_rules.py" "$FIN/porders.py" "$FIN/porders.html" "$SPN/spine_read.py" "$SPN/spine_rules.json" "$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json")
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "       charter 1b: the spine passed $SP_GATE, last success $SP_AT ($SP_AGE min ago)"
TODAY="$(date +%Y-%m-%d)"
say "       the live facts, read from the live database (read only) at $(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M:%S IST'):"
say "         order.source: $(sqlro "$DB" "SELECT value FROM setting WHERE key='order.source'" | awk '{print $1}')"
say "         today's purchase_order rows of the new flow (id, vendor, status, order_via, created_by, created_at):"
sqlro "$DB" "SELECT id, vendor, status, order_via, created_by, created_at FROM purchase_order WHERE order_src='s454' AND substr(created_at,1,10)='$TODAY' ORDER BY id"
say "         today's supplier_msg order rows (id, vendor, status, attempts, queued_at, handed_at, sent_at -- no number, no body):"
sqlro "$DB" "SELECT id, vendor, status, attempts, queued_at, COALESCE(handed_at,'-'), COALESCE(sent_at,'-') FROM supplier_msg WHERE kind='order' AND substr(queued_at,1,10)='$TODAY' ORDER BY id"
say "         today's purchase_audit rows of s454_whatsapp_all / _queued / _sent / _withdrawn (action, who, at, ref):"
sqlro "$DB" "SELECT action, who, at, ref FROM purchase_audit WHERE action IN ('s454_whatsapp_all','s454_whatsapp_queued','s454_whatsapp_sent','s454_whatsapp_withdrawn','s454_whatsapp_requeued') AND substr(at,1,10)='$TODAY' ORDER BY id"

# ---- the wait: no order message queued or handed in the last 10 minutes (30 minutes at most, every 2)
busy() { "$APY" -c "import sqlite3,sys,datetime as d; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); t=(d.datetime.now()-d.timedelta(minutes=10)).replace(microsecond=0).isoformat(); print(c.execute(\"SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND (status='queued' OR replace(COALESCE(handed_at,''),' ','T')>=? OR replace(queued_at,' ','T')>=?)\", (t, t)).fetchone()[0])" "$DB" 2>/dev/null || echo 0; }
if [ "${DRY:-0}" = 1 ]; then
  say "       the wait: DRY RUN -- not waited ($(busy) order message(s) queued or handed in the last 10 minutes now)"
else
  W0="$(TZ=Asia/Kolkata date '+%H:%M:%S')"; WAITED=0
  while [ "$(busy)" != 0 ] && [ "$WAITED" -lt 30 ]; do say "       $(TZ=Asia/Kolkata date '+%H:%M:%S IST'): $(busy) order message(s) queued or handed in the last 10 minutes -- waiting 2 minutes"; sleep 120; WAITED=$((WAITED+2)); done
  if [ "$(busy)" != 0 ]; then say "       the wait: 30 minutes from $W0 IST and still $(busy) order message(s) active -- proceeding anyway (the brief: bounded 30 minutes, then proceed and say so)";
  else say "       the wait: from $W0 IST, $WAITED minute(s) -- no order message queued or handed in the last 10 minutes at $(TZ=Asia/Kolkata date '+%H:%M:%S IST')"; fi
fi

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s605.py walk_s605.py spine_cmp_s605.py walk_s603.py walk_s598.py || { say "!! [3/12] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s605.py --finance "$FIN" --repo "$REPO" --out "$SCR/built" > "$SCR/make.txt" || { mask < "$SCR/make.txt"; say "!! [4/12] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED DUTY_MAP.json DUTY_MAP.md walk_s603.py walk_s598.py; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/12] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for n in DUTY_MAP.json DUTY_MAP.md walk_s603.py walk_s598.py; do cmp -s "$SCR/built/$n" "$KDIR/$n" || { say "!! [4/12] the built $n is not the kit's shipped copy - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do case "$n" in *.py) PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/12] the built $n does not compile on $py - nothing installed"; exit 1; };; esac; done
done
say "[3/12] the kit's python files and the seven built python files compile on $APY and $VPY"
say "[4/12] rebuilt here from this box's live bytes ($(grep -c 'anchored once, applied' "$SCR/make.txt") anchored edits + DUTY_MAP v17 + the two walks): each at its TO pin; the built DUTY_MAP and walks = the kit's copies"

# ---- 5: the spine twice (3.6), then the finance folder twice
copydb "$DB" "$SCR/base.db" && copydb "$ADB" "$SCR/base_a.db" && copydb "$SPN/spine.db" "$SCR/spine_live.db" || { say "!! [5/12] no copy of the databases - nothing installed"; exit 1; }
spbuild() {   # $1 = side (old | new): the spine built from the live readings (read only) into a scratch folder, as the cron runs it
  local d="$SCR/sp_$1"; mkdir -p "$d"
  cp -p "$SPN/spine_read.py" "$d/" && if [ "$1" = new ]; then cp -p "$SCR/built/spine/spine_build.py" "$d/"; else cp -p "$SPN/spine_build.py" "$d/"; fi
  ( cd "$d" && timeout 1200 "$VPY" -B spine_build.py --readings "$SPN/readings" --rules "$SPN/spine_rules.json" --out "$d/spine.db" --finance-db "$SCR/base.db" > "$d/build.txt" 2>&1 )
}
spbuild old; SPO=$?; spbuild new; SPNW=$?
say "[5/12] 3.6: the spine built on scratch from the live readings -- OLD spine_build exit $SPO ($(grep -E '^SPINE BUILT|^GATE FAILED' "$SCR/sp_old/build.txt" | head -1 | cut -c1-40)), NEW exit $SPNW ($(grep -E '^SPINE BUILT|^GATE FAILED' "$SCR/sp_new/build.txt" | head -1 | cut -c1-40))"
CMP="$( "$APY" -B "$KDIR/spine_cmp_s605.py" --old "$SCR/sp_old/spine.db" --new "$SCR/sp_new/spine.db" --finance-db "$SCR/base.db" --rules "$SPN/spine_rules.json" 2>&1 )"; CMPRC=$?
echo "$CMP" | mask | sed 's/^/       /'
if [ "$SPO" != 0 ] || [ "$SPNW" != 0 ] || [ "$CMPRC" != 0 ] || ! echo "$CMP" | grep -q "^SPINE CMP OK S605"; then
  SPINE_PLACE=0
  say "       !! 3.6 STOP: a key outside the eight families moved, or a build or the gate is red -- spine_build.py will NOT be placed (the rest of the kit goes on)"
fi
mkside() {   # $1 = side: a copy of the live finance code (spine folder included), a portal copy (never the live secret or user store), the ingest reader, the databases
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive" "$d/marg_ingest/lib" "$d/portal"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$SPN"/*.py "$SPN"/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do cp -p "$MARG/$f" "$d/marg_ingest/" || return 1; done
  cp -p "$MARG"/lib/*.py "$d/marg_ingest/lib/" 2>/dev/null
  cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/" || return 1
  for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$d/portal/"; done
  cp -p "$POR/tile_grants.json" "$d/portal/" || return 1; cp -rp "$POR/forms" "$d/portal/" 2>/dev/null
  for x in por603 por604; do mkdir -p "$d/$x" && cp -rp "$d/portal/." "$d/$x/"; done
  for x in f f603 f598 f604; do cp -p "$SCR/base.db" "$d/$x.db" || return 1; done
  cp -p "$SCR/base_a.db" "$d/a.db" && cp -p "$SCR/spine_live.db" "$d/finance/spine/spine.db"
  cp -p "$S604TEXT" "$d/text.txt" && cp -p "$S604KIT/marg_txt.py" "$d/marg_txt_s604.py"
}
for side in new old o603 o598; do mkside "$side" || { say "!! [5/12] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do [ "$n" = spine/spine_build.py ] && [ "$SPINE_PLACE" != 1 ] && continue; cp -p "$SCR/built/$n" "$SCR/new/finance/$n"; done
if [ "$SPINE_PLACE" = 1 ]; then for s in new o603 o598; do cp -p "$SCR/sp_new/spine.db" "$SCR/$s/finance/spine/spine.db"; cp -p "$SCR/sp_new/spine_state.json" "$SCR/$s/finance/spine/spine_state.json"; done; fi
for s in o603 o598; do for n in $EDITED; do [ "$n" = spine/spine_build.py ] && [ "$SPINE_PLACE" != 1 ] && continue; cp -p "$SCR/built/$n" "$SCR/$s/finance/$n"; done; done
for p in $B603; do n="${p%%:*}"; h="${p#*:}"; cp -p "$FIN/$n.bak_S603_${h:0:8}" "$SCR/o603/finance/$n"; done
for p in $B598; do n="${p%%:*}"; h="${p#*:}"; cp -p "$FIN/$n.bak_S598_${h:0:8}" "$SCR/o598/finance/$n"; done
say "[5/12] scratch: the finance folder four times -- NEW (the built files, the NEW spine), OLD (as it is, the live spine), and NEW with S603's / S598's own OLD files (F-957);"
say "       a portal copy per side; finance.db, assets.db and the spine by the backup API"

# ---- 6: the walks
w605() { ( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s605.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/portal" --duty-map "$KDIR/DUTY_MAP.json" --dump "$SCR/dump_$1" "${@:2}" 2>&1 ); }
ROUT="$(w605 old --expect-red)"; RRC=$?
WOUT="$(w605 new --old-dump "$SCR/dump_old")"; WRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S605"; then say "!! [6/12] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | mask | grep -E "^  RED on the old files:|^  FAIL C:|^WALK OK negative|^NEGATIVE CONTROL|^  NOT RED|^WALK RED" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [6/12] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | mask | tail -30; exit 1; fi
say "[6/12] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK negative control" | tail -1 | sed 's/^WALK OK negative control S605: //')"
w604() { ( cd /tmp && timeout 2400 "$APY" -B "$S604KIT/walk_s604.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f604.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por604" \
         --reader "$SCR/$1/marg_txt_s604.py" --text "$SCR/$1/text.txt" --kit "$S604KIT" --dump "$SCR/dump604_$1" 2>&1 ); }
W604="$(w604 new)"; W604RC=$?; W604O="$(w604 old)"; W604ORC=$?
find "$S604KIT" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
w604lines() { grep -E '^  (ok|FAIL) ' | sed -E 's/[0-9]+\.[0-9]+s/N.Ns/g; s/[0-9]{2}:[0-9]{2}(:[0-9]{2})?/HH:MM/g; s/\(200, [0-9]+ bytes\)/(200, N bytes)/; s/[0-9]{10,}/##########/g'; }
echo "$W604" | w604lines > "$SCR/w604_new.txt"; echo "$W604O" | w604lines > "$SCR/w604_old.txt"
say "       S604's walk (walk_s604.py, whole) on the NEW files: $(echo "$W604" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-80)... (exit $W604RC; $(grep -c '^  FAIL ' "$SCR/w604_new.txt") FAIL of $(wc -l < "$SCR/w604_new.txt"))"
say "       ... and on the OLD files: $(echo "$W604O" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-80)... (exit $W604ORC; $(grep -c '^  FAIL ' "$SCR/w604_old.txt") FAIL of $(wc -l < "$SCR/w604_old.txt"))"
grep '^  FAIL ' "$SCR/w604_new.txt" | cut -c1-200 | sed 's/^/         (both sides, the live day) /'
[ -s "$SCR/w604_new.txt" ] || { say "!! [6/12] S604's walk printed no check line - nothing installed"; exit 1; }
if [ "$W604RC" = 0 ] && echo "$W604" | grep -q "^WALK OK S604"; then
  say "       S604's walk is green on the NEW files"
elif cmp -s "$SCR/w604_new.txt" "$SCR/w604_old.txt"; then
  say "       S604's walk is red on the untouched live files too, line for line ($(wc -l < "$SCR/w604_new.txt") check lines identical on both sides): its scenarios read the live"
  say "       day its own 09:51 data step changed (the F-957 class) -- this kit changes nothing it sees. Named in the report for the chat."
else
  say "!! [6/12] S604's walk reads differently on the NEW files than on the OLD files - nothing installed"; diff "$SCR/w604_old.txt" "$SCR/w604_new.txt" | head -20; exit 1
fi
say "       F-957 -- S603's walk (S605's copy: its own visit day) and S598's walk (S605's copy: its own rows), green on NEW, every control red on their own OLD files:"
w603() { ( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s603.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f603.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --por "$SCR/$1/por603" --duty-map "$S603KIT/DUTY_MAP.json" --dump "$SCR/dump603_$1" "${@:2}" 2>&1 ); }
w598() { ( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s598.py" --fin "$SCR/$1/finance" --db "$SCR/$1/f598.db" --adb "$SCR/$1/a.db" --marg "$SCR/$1/marg_ingest" --kit "$S598KIT" --rows-json "$ROWS598" --dump "$SCR/dump598_$1" "${@:2}" 2>&1 ); }
O603="$(w603 o603 --expect-red)"; O603RC=$?; N603="$(w603 new --old-dump "$SCR/dump603_o603")"; N603RC=$?
O598="$(w598 o598 --expect-red)"; O598RC=$?; N598="$(w598 new --old-dump "$SCR/dump598_o598")"; N598RC=$?
printf "%s\n" "$N603" > "$SCR/w603_new.out"; printf "%s\n" "$O603" > "$SCR/w603_old.out"; printf "%s\n" "$N598" > "$SCR/w598_new.out"; printf "%s\n" "$O598" > "$SCR/w598_old.out"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "         walk_s603 NEW: $(echo "$N603" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $N603RC)"
echo "$N603" | grep '^  FAIL ' | mask | cut -c1-200 | sed 's/^/           /'
say "         walk_s603 on S603's own OLD files: $(echo "$O603" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $O603RC)"
echo "$O603" | grep '^  NOT RED' | mask | cut -c1-200 | sed 's/^/           /'
say "         walk_s598 NEW: $(echo "$N598" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $N598RC)"
echo "$N598" | grep '^  FAIL ' | mask | cut -c1-200 | sed 's/^/           /'
say "         walk_s598 on S598's own OLD files: $(echo "$O598" | grep -E '^WALK (OK|RED)' | tail -1 | mask | cut -c1-110) (exit $O598RC)"
echo "$O598" | grep '^  NOT RED' | mask | cut -c1-200 | sed 's/^/           /'
{ [ "$N603RC" = 0 ] && echo "$N603" | grep -q "^WALK OK S603" && [ "$O603RC" = 0 ] && echo "$O603" | grep -q "^WALK OK negative control S603" \
  && [ "$N598RC" = 0 ] && echo "$N598" | grep -q "^WALK OK S598" && [ "$O598RC" = 0 ] && echo "$O598" | grep -q "^WALK OK negative control S598"; } \
  || { say "!! [6/12] F-957: a walk of S603 / S598 is not green on NEW, or its control not red on its own OLD files - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [6/12] $FIN/$n changed during the walks - nothing installed"; exit 1; }; done
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the scratch sides, the spine builds and the walks green; NOTHING written, nothing placed, nothing restarted (spine_build.py to be placed: $SPINE_PLACE)"; exit 0; fi

# ---- 7: the install-day state on the OLD and the NEW files (fresh copies of the live database)
statelook() {   # $1 = a scratch finance folder, or LIVE (a fresh scratch copy of /root/finance as it stands); $2 = label
  local d="$SCR/st_$2" fin="$1"; mkdir -p "$d"
  if [ "$1" = LIVE ]; then
    mkside "st_$2" >/dev/null 2>&1 || return 1
    copydb "$SPN/spine.db" "$d/finance/spine/spine.db" || return 1
    fin="$d/finance"
  fi
  copydb "$DB" "$d/f.db" || return 1
  ( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s605.py" --state --label "$2" --fin "$fin" --db "$d/f.db" --adb "$SCR/base_a.db" --marg "$SCR/new/marg_ingest" --por "$SCR/new/portal" --duty-map "$KDIR/DUTY_MAP.json" 2>&1 ) | mask
}
say "[7/12] the install-day state BEFORE (the live files on a copy) and as the NEW files read the same copy (charter 7):"
SB="$(statelook "$SCR/old/finance" before)"; echo "$SB" | grep -E "^STATE|^   " | sed 's/^/ /'
SN="$(statelook "$SCR/new/finance" new)"; echo "$SN" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SB" | grep -q "^STATE OK S605" && echo "$SN" | grep -q "^STATE OK S605" || { say "!! [7/12] the install-day state could not be read - nothing placed"; exit 1; }
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; exit 1; }

# ---- 8: backups
copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [8/12] database backup failed - nothing placed"; exit 1; }
for n in $(placed_list); do
  \cp -p "$FIN/$n" "$(bak "$n")" || { say "!! [8/12] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak "$n")")" = "${FROM[$n]}" ] || { say "!! [8/12] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[8/12] backups: $(basename "$DBBAK") (sqlite backup API, $(stat -c %s "$DBBAK") bytes); $(for n in $(placed_list); do printf '%s ' "$(bak "$n" | sed "s#$FIN/##")"; done)"

# ---- 9-10: the files in ONE move, one restart
mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" || { say "!! [9/12] could not write $OFFSW - nothing placed"; exit 1; }
for n in $(placed_list); do
  { \cp -p "$FIN/$n" "$(stg "$n")" && cat "$SCR/built/$n" > "$(stg "$n")" && [ "$(m5 "$(stg "$n")")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s605 "$SPN"/.*.s605 "$OFFSW"; say "!! [9/12] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
MV=""; for n in $(placed_list); do MV="$MV mv -f '$(stg "$n")' '$FIN/$n' &&"; done
eval "${MV% &&}" || restore "placing the files"
for n in $(placed_list); do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && cmp -s "$FIN/$n" "$SCR/built/$n" || restore "$n did not land at its pin"; done
say "[9/12] placed by rename in ONE command; md5 read back: $(for n in $(placed_list); do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's TO pins, byte-identical to the walked files)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/porders); c3=$(health /finance/porders/s454/order); c4=$(health /finance/porders/s454/order/whatsapp); c5=$(health /finance/darpan/kal); c6=$(health /finance/porders/s454/sheet.pdf); c7=$(health /finance/porders/s454/marg.pdf)
for c in "$c2" "$c3" "$c4" "$c5" "$c6" "$c7"; do case "$c" in 302|401|303) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): porders $c2 / order $c3 / order/whatsapp $c4 / darpan/kal $c5 / sheet.pdf $c6 / marg.pdf $c7";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[10/12] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/porders $c2, /s454/order $c3, /s454/order/whatsapp $c4, /darpan/kal $c5, sheet.pdf $c6, marg.pdf $c7 without a login (302 = the login gate, expected) - journal clean"

# ---- 3.6 after placing: one spine build the way the cron runs it (under its flock); a failed build keeps the old spine -- then the old spine_build.py back
if [ "$SPINE_PLACE" = 1 ]; then
  SB0="$(TZ=Asia/Kolkata date '+%H:%M:%S IST')"
  SPOUT="$( cd "$SPN" && flock -w 900 /tmp/spine.lock sh -c "$VPY -B spine_evidence.py && $VPY -B spine_build.py --readings readings --out spine.db --finance-db $DB" 2>&1 )"; SPRC=$?
  echo "$SPOUT" | grep -E "^  (ok|FAIL|note) |SPINE BUILT|GATE FAILED" | mask | cut -c1-180 | sed 's/^/       /'
  if [ "$SPRC" = 0 ] && echo "$SPOUT" | grep -q "SPINE BUILT AND SWAPPED"; then
    say "       the spine built at $SB0 with the NEW spine_build.py: gate $(jget "$SPN/spine_state.json" gate), passed $(jget "$SPN/spine_state.json" passed); sp_alias rename_family rows: $(sqlro "$SPN/spine.db" "SELECT COUNT(*) FROM sp_alias WHERE kind='rename_family'" | awk '{print $1}')"
  else
    say "       !! the spine build after placing did not swap (exit $SPRC) -- the old spine stays (atomic); the old spine_build.py goes back:"
    \cp -p "$(bak spine/spine_build.py)" "$SPN/spine_build.py" && say "       $SPN/spine_build.py $(m5 "$SPN/spine_build.py") (= FROM ${FROM[spine/spine_build.py]:0:8})"
    SPINE_PLACE=0
  fi
fi

# ---- 11: the state AFTER; nothing else moved
say "[11/12] the install-day state AFTER placing (the live files, a fresh copy of the live database; the box's clock in the first STATE line):"
SA_="$(statelook LIVE after)"; echo "$SA_" | grep -E "^STATE|^   " | sed 's/^/ /'
echo "$SA_" | grep -q "^STATE OK S605" || restore "the state after placing could not be read"
echo "$SA_" | grep -q "^STATE after: files NEW (S605)" || restore "the state after placing does not read the NEW files"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health /finance/healthz)" = 200 ] || restore "healthz at the end"
rm -f "$OFFSW"
say "        nothing else moved (the read-only files, finance_app, portal.py, tile_grants.json, the crontab); healthz 200; $OFFSW removed"
say "        the clone's DUTY_MAP.json is $(m5 "$BRIEFS/DUTY_MAP.json" | cut -c1-8) now; v17 (${TO[DUTY_MAP.json]:0:8}) reaches it by the publish and the clone's pull"

find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[12/12] md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE. The build lock stays held by $KIT until the report is written (release: rm -f $LOCK/owner; rmdir $LOCK)."
say "undo (the files): $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak "$n")" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
