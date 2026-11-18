#!/bin/bash
# =============================================================================
#  install_S890_RENEWALS_ONE_LIST.sh · kit S890 (the parent, S488, 18-Nov-2026) · his "proceed with the build" 22:59 · D1017
#  Every renewal on ONE list on the server; the personal Janitor only reads Gmail and sends the 08:42 mail; the Sheets unused.
#   1. NEW /root/assetapp/renewals_one.py             the table renewal_item (+ renewal_mail, renewal_nag) in assets.db, the page
#                                                     sections (Found in your mail · Licences, documents and subscriptions · Staff
#                                                     documents), + Add renewal / Mark renewed, the token doors (due list, sent, mail
#                                                     intake, the one-time seed), the health page's renewals_state.json written
#                                                     from the list (finance_app.py untouched)
#   2. /root/assetapp/asset_register.py  b668771c -> TO   THRESHOLD_DEFAULT 60 -> 45; the /renewals template draws the new sections
#                                                     (4 anchors) + the guarded mount block at the foot  [the SCAN APP's file, PLANNED]
#   3. /root/portal/portal.py            cb37c7fb -> TO   every folder tile draws its inside tiles as bold lines; the Renewals line
#                                                     takes the red count from the one list (3 anchors)
#   + the token file /root/assetapp/renewals_one.token (0600) copied from clinic-finance's own FINANCE_RENEWALS_TOKEN -- no new secret
#   + one cron line (02:45): the health file rewritten from the list  # S890_RENEWALS_STATE
#  Run as root on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s890kit && cp -rp /root/deploy/repo/deploy_kits/S890_RENEWALS_ONE_LIST /tmp/s890kit && bash /tmp/s890kit/install_S890_RENEWALS_ONE_LIST.sh
#  DRY=1 before bash: every gate and both walks (made-up data; the controls on the live files); nothing live changes.
#  --undo: the two patched files back, the cron line and the token file removed, both services restarted. The tables and the list stay
#          (data is never deleted by an undo); renewals_one.py stays unmounted and inert.
# =============================================================================
set -u
KIT="S890_RENEWALS_ONE_LIST"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; AD="${AD:-$ROOT/assetapp}"; PD="${PD:-$ROOT/portal}"; SH="${SH:-$ROOT/shared}"; FINDIR="${FINDIR:-$ROOT/finance}"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ASVC="${ASVC:-assetapp}"; APORT="${APORT:-8030}"; PSVC="${PSVC:-clinic-portal}"; PPORT="${PPORT:-8099}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
DB="${DB:-$AD/assets.db}"; TOK="$AD/renewals_one.token"
CRON_TAG="# S890_RENEWALS_STATE"
CRON_LINE="45 2 * * * cd $AD && TZ=Asia/Kolkata $APY -B renewals_one.py --state $DB >> $AD/renewals_one.log 2>&1 $CRON_TAG"
NAMES="asset_register.py portal.py"
dir_of() { case "$1" in asset_register.py|renewals_one.py) echo "$AD";; portal.py) echo "$PD";; esac; }
from_of() { case "$1" in asset_register.py) echo b668771c;; portal.py) echo cb37c7fb;; esac; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s890_inst_$STAMP"; TOOK_LOCK=0; OFF_MINE=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
m8() { m5 "$1" | cut -c1-8; }
isfrom() { [ "$(m8 "$(dir_of "$1")/$1")" = "$(from_of "$1")" ]; }
isto() { [ "$(m5 "$(dir_of "$1")/$1")" = "$(to_of "$1")" ]; }
say() { echo "$@"; }
bak() { echo "$(dir_of "$1")/$1.bak_S890_$(from_of "$1")"; }
hget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1" "$2"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$1$2"; fi; }
ahz() { hget "$APORT" /healthz; }
phz() { hget "$PPORT" /portal/health; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(hget "$1" "$2"); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for n in $NAMES renewals_one.py; do rm -f "$(dir_of "$n")/.$n.s890"; done; release; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release; exit 1; }
pause_doctor() { if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
CRON_BEFORE=""
cron_read() {                        # the estate's one crontab, read ONCE into a file; never written from an empty read (a failed -l must not wipe it)
  CRON_BEFORE="$SCR/cron.before"; $CRONTAB -l > "$CRON_BEFORE" 2>"$SCR/cron.err" || { grep -q "no crontab" "$SCR/cron.err" && : > "$CRON_BEFORE" || return 1; }; return 0; }
cron_without() { [ -n "$CRON_BEFORE" ] && [ -f "$CRON_BEFORE" ] && grep -vF "$CRON_TAG" "$CRON_BEFORE"; }
cron_write() {                       # $1 = the new text's file; refused when it lost more than the one tagged line
  local b n; b=$(grep -cvF "$CRON_TAG" "$CRON_BEFORE"); n=$(grep -cvF "$CRON_TAG" "$1"); [ "$n" -ge "$b" ] || return 1; $CRONTAB - < "$1"; }
restore() { say "!! RED after placing ($1) - putting the files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$(dir_of "$n")/$n"; done
  rm -f "$TOK"; if cron_read; then cron_without > "$SCR/cron.new"; cron_write "$SCR/cron.new" || say "   (the cron line could not be removed - tell Claude)"; fi
  "$SYSTEMCTL" restart "$ASVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
  for n in $NAMES; do say "   $n $(m8 "$(dir_of "$n")/$n") (expected $(from_of "$n"))"; done
  say "   $ASVC healthz $(wait200 "$APORT" /healthz), $PSVC health $(wait200 "$PPORT" /portal/health). Send a photo of this screen to Claude."; release; exit 1; }
pyv() { local py="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 600 "$py" -W ignore -B "$@" 2>&1); }
token_src() {                       # the finance service's own token: Environment=, or its EnvironmentFile; printed NEVER, only found/not found
  local v f
  v="$("$SYSTEMCTL" show "$FSVC" -p Environment --value 2>/dev/null | tr ' ' '\n' | sed -n 's/^FINANCE_RENEWALS_TOKEN=//p' | head -1)"
  if [ -z "$v" ]; then for f in $("$SYSTEMCTL" show "$FSVC" -p EnvironmentFiles --value 2>/dev/null | tr ' ' '\n' | sed 's/ (ignore_errors=.*//' | grep '^/'); do
      [ -f "$f" ] && v="$(sed -n 's/^FINANCE_RENEWALS_TOKEN=//p' "$f" | head -1 | tr -d "\"'")" && [ -n "$v" ] && break; done; fi
  printf '%s' "$v"; }

if [ "${1:-}" = "--undo" ]; then
  U=1; for n in $NAMES; do isfrom "$n" || U=0; done
  mkdir -p "$SCR" && chmod 700 "$SCR"
  [ "$U" = 1 ] && { rm -f "$TOK"; cron_read && { cron_without > "$SCR/cron.new"; cron_write "$SCR/cron.new"; }; say "-- $KIT is not installed - nothing to undo (token file and cron line cleared if any)."; exit 0; }
  for n in $NAMES; do isfrom "$n" || isto "$n" || { say "!! $(dir_of "$n")/$n is $(m8 "$(dir_of "$n")/$n"), not this kit's - nothing undone. Tell Claude."; exit 1; }; done
  for n in $NAMES; do isfrom "$n" && continue; b=$(bak "$n"); [ -f "$b" ] && [ "$(m8 "$b")" = "$(from_of "$n")" ] || { say "!! no good backup $b - nothing undone"; exit 1; }; done
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"; pause_doctor
  for n in $NAMES; do isfrom "$n" || \cp -p "$(bak "$n")" "$(dir_of "$n")/$n"; done
  rm -f "$TOK"; cron_read || { release; say "!! the crontab could not be read - files NOT touched. Tell Claude."; exit 1; }
  cron_without > "$SCR/cron.new"; cron_write "$SCR/cron.new" || { release; say "!! the crontab would lose lines - nothing undone. Tell Claude."; exit 1; }
  "$SYSTEMCTL" restart "$ASVC"; "$SYSTEMCTL" restart "$PSVC"
  a=$(wait200 "$APORT" /healthz); p=$(wait200 "$PPORT" /portal/health); release
  [ "$a" = 200 ] && [ "$p" = 200 ] || { say "!! UNDONE but $ASVC healthz $a / $PSVC health $p - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (two files back, cron line and token file removed; both services restarted, health 200/200). The list's tables stay; renewals_one.py is inert."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES renewals_one.py; do [ "$(m5 "$KDIR/$n")" = "$(to_of "$n")" ] || { say "!! [1/6] the kit's $n is not as built - nothing installed"; exit 1; }; done
ALL=1; for n in $NAMES renewals_one.py; do isto "$n" || ALL=0; done
[ "$ALL" = 1 ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for n in $NAMES; do isfrom "$n" || stop "!! [2/6] $(dir_of "$n")/$n is $(m8 "$(dir_of "$n")/$n"), expected $(from_of "$n") - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
[ -f "$DB" ] || stop "!! [2/6] $DB is not there - nothing installed"
PYTHONPYCACHEPREFIX="$SCR/pyc" "$APY" -W ignore -m py_compile "$KDIR/asset_register.py" "$KDIR/renewals_one.py" || stop "!! [2/6] the asset files do not compile on $APY - nothing installed"
PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -W ignore -m py_compile "$KDIR/portal.py" || stop "!! [2/6] portal.py does not compile on $VPY - nothing installed"
SC=$(pyv "$APY" "$KDIR/renewals_one.py" --selfcheck | tail -1); case "$SC" in *"selfcheck: OK") ;; *) stop "!! [2/6] renewals_one selfcheck: $SC - nothing installed";; esac
TV="$(token_src)"; if [ -n "$TV" ]; then TOKMSG="the renewals token found in $FSVC's settings"; else TOKMSG="NO renewals token in $FSVC's settings: the mail doors will answer 503 until it is set (the page itself works)"; fi
say "[2/6] the live pins exact; the three files compile; selfcheck OK; $TOKMSG"
R1=$(pyv "$APY" "$KDIR/walk_s890_app.py" --live "$AD" --shared "$SH" --files "$KDIR" --box | tail -1)
case "$R1" in "WALK S890 APP: 28 green, 0 red") ;; *) pyv "$APY" "$KDIR/walk_s890_app.py" --live "$AD" --shared "$SH" --files "$KDIR" --box | grep -E "^RED|stderr" | head -8; stop "!! [3/6] walk_s890_app on the new files: $R1 - nothing installed";; esac
R1c=$(pyv "$APY" "$KDIR/walk_s890_app.py" --live "$AD" --shared "$SH" --expect-red --box | tail -1)
case "$R1c" in *"AS IT MUST BE"*) case "$R1c" in *"NOT AS IT MUST BE"*) stop "!! [3/6] walk_s890_app's control (the live files): $R1c - nothing installed";; esac;; *) stop "!! [3/6] walk_s890_app's control did not finish ($R1c) - nothing installed";; esac
R2=$(pyv "$VPY" "$KDIR/walk_s890_portal.py" --live "$PD" --files "$KDIR" --box | tail -1)
case "$R2" in "WALK S890 PORTAL: 10 green, 0 red") ;; *) pyv "$VPY" "$KDIR/walk_s890_portal.py" --live "$PD" --files "$KDIR" --box | grep -E "^RED" | head -6; stop "!! [3/6] walk_s890_portal on the new file: $R2 - nothing installed";; esac
R2c=$(pyv "$VPY" "$KDIR/walk_s890_portal.py" --live "$PD" --expect-red --box | tail -1)
case "$R2c" in *"NOT AS IT MUST BE"*) stop "!! [3/6] walk_s890_portal's control: $R2c - nothing installed";; *"AS IT MUST BE"*) ;; *) stop "!! [3/6] walk_s890_portal's control did not finish ($R2c) - nothing installed";; esac
say "[3/6] $R1 (control: red as it must be); $R2 (control: red as it must be) -- made-up data only, nothing of the live store read"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and both walks green; nothing live changed"; exit 0; fi
a0=$(ahz); p0=$(phz); [ "$a0" = 200 ] && [ "$p0" = 200 ] || stop "!! [4/6] health before the install: $ASVC $a0 / $PSVC $p0 - nothing installed"
cron_read || stop "!! [4/6] the crontab could not be read - nothing installed"
for n in $NAMES; do b=$(bak "$n"); { \cp -p "$(dir_of "$n")/$n" "$b" && [ "$(m8 "$b")" = "$(from_of "$n")" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for n in $NAMES renewals_one.py; do st="$(dir_of "$n")/.$n.s890"; ref="$(dir_of "$n")/asset_register.py"; [ "$n" = portal.py ] && ref="$PD/portal.py"
  { cat "$KDIR/$n" > "$st" && chmod --reference="$ref" "$st" 2>/dev/null; chown --reference="$ref" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
pause_doctor
EN=$(cd "$AD" && TZ=Asia/Kolkata timeout 120 "$APY" -W ignore -B "$AD/.renewals_one.py.s890" --ensure "$DB" 2>&1 | tail -1)
case "$EN" in "renewals_one S890: tables ready"*) ;; *) stop "!! [4/6] the tables could not be made in $DB ($EN) - nothing placed";; esac
if [ -n "$TV" ]; then ( umask 077; printf '%s\n' "$TV" > "$TOK" ) && chmod 600 "$TOK" || stop "!! [4/6] could not write the token file - nothing placed"; fi
unset TV
for n in renewals_one.py asset_register.py portal.py; do mv -f "$(dir_of "$n")/.$n.s890" "$(dir_of "$n")/$n" || restore "the rename of $n"; done
for n in $NAMES renewals_one.py; do isto "$n" || restore "read back of $n"; done
"$SYSTEMCTL" restart "$ASVC" || restore "restart $ASVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
a1=$(wait200 "$APORT" /healthz); [ "$a1" = 200 ] || restore "$ASVC healthz $a1 after the restart"
for u in /renewals /renewals/one/api/count; do pg=$(hget "$APORT" "$u"); case "$pg" in 200|302|303) ;; *) restore "$u answered $pg";; esac; done
dd=$(hget "$APORT" /renewals/one/api/due); case "$dd" in 401|503) ;; *) restore "/renewals/one/api/due without a token answered $dd (401 or 503 expected)";; esac
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200 "$PPORT" /portal/health); [ "$p1" = 200 ] || restore "$PSVC health $p1 after the restart"
pg=$(hget "$PPORT" /portal); case "$pg" in 200|302|303) ;; *) restore "/portal answered $pg";; esac
{ cron_without; echo "$CRON_LINE"; } > "$SCR/cron.new"; cron_write "$SCR/cron.new" || restore "the cron line"
$CRONTAB -l | grep -qF "$CRON_TAG" || restore "the cron line was not kept"
release
say "[4/6] placed and read back: renewals_one.py NEW, asset_register.py and portal.py at their TO pins; $ASVC restarted (healthz $a1; /renewals $(hget "$APORT" /renewals); the due door without a token $dd); $PSVC restarted (health $p1); cron 02:45 set $(TZ=Asia/Kolkata date '+%H:%M IST')"
say "[5/6] the list is EMPTY until the seed: Claude runs seedServerOnce in the Janitor (his personal Apps Script); until then the health page's Renewals row keeps the Janitor's own push"
say "[6/6] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""; say "$KIT: DONE. The page: https://followup.dr-manoj.in/scanapp/renewals"; exit 0
