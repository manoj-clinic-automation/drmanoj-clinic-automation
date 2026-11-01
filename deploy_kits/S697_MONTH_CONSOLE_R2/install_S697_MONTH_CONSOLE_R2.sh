#!/bin/bash
# =============================================================================
#  install_S697_MONTH_CONSOLE_R2.sh · kit S697 (01-Nov-2026, the parent, session 377) · D818, F-1079, F-1080, and the owner's
#  words 20:17-20:32 IST on the Sanjeevni chat's list for his console (S375): the console and the month page, round 2.
#   (a)(i) the console's section bars styled as the month page's; the colour off the dot, onto the line (a tinted strip with its
#          figure in bold at the end); the pill on the closed bar tinted the same             -> owner_console.html
#   (b)    two month chips on The month's bar; the running month's line second; no second link to the page -> owner_console.py, month_read.py
#   (c)    F-1079: the IPD implant-bill count from S682's own column (voided_at)                -> month_read.py
#   (d)    F-1080b: "due since <day>" for a home-medicines count due and not made             -> month_read.py
#   (e)    F-1080a: Bought for the rooms = films + the three room groups; OTHER PAPERS OF THE MONTH (every other lane and
#          section, the unsorted bills amber, the pharmacy scans counted, rupees never added)  -> month_read.py, month_page.html
#   (g)    F-1080c: the film log's no-count day shows its slip films; "Mornings not counted" names the month -> xray_film.py
#   (h)    the Sanjeevni section: his daily and periodic pages with their own figures (purchase orders ?old=1 with the reception
#          phone's state, review queue, expiry watch, stock check, corrections) and ONE Marg-reports line; TARGET_DOOR learns
#          the expiry page and the owner's purchase-orders page                                  -> owner_console.py
#  The purchase-orders ?old=1 line lives HERE (daily, the console), not on The month (one page, one link -- D818 (f) so settled).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s697kit && cp -rp /root/deploy/repo/deploy_kits/S697_MONTH_CONSOLE_R2 /tmp/s697kit && bash /tmp/s697kit/install_S697_MONTH_CONSOLE_R2.sh
#  (DRY=1 before bash: every gate, the walk, the control and the builder; nothing written.)
#  FIVE FILES, each placed WHOLE from the kit, each pinned FROM (the live bytes, read whole and hashed) -> TO (the kit's file):
#   /root/finance/owner_console.py    391823ad -> TO     /root/finance/owner_console.html  e0d7d62f -> TO
#   /root/finance/month_read.py       9aa2e053 -> TO     /root/finance/month_page.html    29db7c20 -> TO
#   /root/finance/xray_film.py        961e779a -> TO
#  No data step, no new table, no portal change. Restarts clinic-finance only; the reading file is rebuilt once after the restart.
#  ORDER: gates -> the five live pins -> both pythons compile -> the walk on made-up databases + the control on a copy of the live
#  folder + the builder on a copy of the live database with the new files -> backups -> DOCTOR_AUTO_OFF -> stage + atomic move ->
#  restart -> healthz 200, the pages' gates, the NEW master's journal names no module of this kit -> the builder on the box once ->
#  the walk on the placed folder. Red after placing: ALL FIVE back.
# =============================================================================
set -u
KIT="S697_MONTH_CONSOLE_R2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"
DB="${DB:-$FIN/finance.db}"
SNAPF="${SNAPF:-$FIN/console_reading.dat}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
ALL="owner_console.py owner_console.html month_read.py month_page.html xray_film.py"
PY="owner_console.py month_read.py xray_film.py"
declare -A FROM=( [owner_console.py]=391823add07b6cedc1054992b3185b12 [owner_console.html]=e0d7d62fe2c8e6184748052e3896905c
                  [month_read.py]=9aa2e053238a4c606dbd41ddc7c8a495 [month_page.html]=29db7c20687ab52028f76bfa24543537 [xray_film.py]=961e779a134cbe2584670f09fc26d87f )
declare -A TO
for n in $ALL; do TO[$n]="$(awk -v f="$n" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s697_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0
GREEN="WALK S697: 85 of 85 green · mutants caught 13 of 13 · "
CONTROL="CONTROL: 33 red"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S697_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
off_clear() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd "$SCR" && PYTHONPYCACHEPREFIX="$SCR/pyc" WALK_TMPDIR="$SCR/wtmp" timeout 600 "$VPY" -B "$KDIR/walk_s697.py" "$@" 2>&1); }
mkscratch() {   # $1 = a folder: a copy of the live finance CODE (never the database, never a backup)
  mkdir -p "$1/finance_ui" "$1/spine"
  cp -p "$FIN"/*.py "$1/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$1/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$1/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$1/spine/" 2>/dev/null
  rm -f "$1"/*.bak_* "$1"/console_reading.dat* "$1"/*.lock 2>/dev/null; return 0
}
# the console's builder on a database copy, with the code in $1: writes $2; prints the verdict; 0 when the month and Sanjeevni are read
build_month() {
  (cd "$1" && PYTHONPYCACHEPREFIX="$SCR/pyc" TMPDIR="$SCR/wtmp" timeout 170 "$VPY" -B "$1/owner_console.py" --build --db "$3" --out "$2" --lock "$2.lock" >"$SCR/build.txt" 2>&1) || { tail -3 "$SCR/build.txt"; return 1; }
  "$APY" - "$2" <<'EOF'
import json, sys
s = json.load(open(sys.argv[1], encoding="utf-8"))
m = s.get("month") or {}
sec = (s.get("sections") or {}).get("month") or {}
sj = (s.get("sections") or {}).get("sanj") or {}
links = [l.get("link") for l in sj.get("lines") or []]
have = [k for k in ("purchase orders", "review queue", "expiry watch", "stock check", "corrections", "Aaj ki reports") if k in links]
# the gate: the month and the Sanjeevni section READ (the kit's shape there), never "every page read" -- a page a reader could not
# read is one grey line by design (cold review, item 2); the pages read and unread are printed for the record
ok = bool(m.get("ok")) and sec.get("ok") is True and "month" not in (s.get("failed") or []) and "sanj" not in (s.get("failed") or []) \
     and s.get("version") == "S697 1.5" and sj.get("ok") is True and len(sec.get("chips") or []) == 2 and (have or any("could not be read" in (l.get("text") or "") for l in sj.get("lines") or []))
ms = m.get("months") or []
words = " · ".join("%s: %d of %d done, %d need him, other papers %d" % (x["label"], x["summary"]["done"], x["summary"]["n"], x["summary"]["yours"],
                   int((x.get("others") or {}).get("n_bills") or 0)) for x in ms)
unread = [l.get("text") for l in sj.get("lines") or [] if "could not be read" in (l.get("text") or "")]
print(("read: %s; Sanjeevni %s, pages read %d of 6 (%s)" % (words, sj.get("chip"), len(have), ("; ".join(unread)[:200] if unread else "every page read"))) if ok
      else ("NOT READ: month ok=%s sanj ok=%s links=%s chips=%s failed=%s version=%s" % (sec.get("ok"), sj.get("ok"), links, sec.get("chips"), s.get("failed"), s.get("version"))))
sys.exit(0 if ok else 1)
EOF
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting all five files back"
  PLACED=2
  for n in $ALL; do \cp -p "$(bak $n)" "$FIN/$n" || say "   !! could not put back $FIN/$n"; done
  rm -f "$FIN"/.*.s697
  [ "${SNAP_MINE:-0}" = 1 ] && rm -f "$SNAPF" "$SNAPF.lock"             # the reading this run wrote: the service makes a fresh one
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $ALL; do say "   $FIN/$n $(m5 "$FIN/$n" | cut -c1-8) (expected ${FROM[$n]:0:8})"; done
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  off_clear; release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; off_clear; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; off_clear; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout sleep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${SKIP_WINDOW:-0}" = 1 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $ALL; do [ -n "${TO[$n]}" ] || { say "!! [1/8] TO_PINS.md5 does not name $n - nothing installed"; exit 1; }; done
for n in $ALL; do [ "$(m5 "$KDIR/$n")" = "${TO[$n]}" ] || { say "!! [1/8] the kit's $n is not at its TO pin - nothing installed"; exit 1; }; done
for n in $ALL; do [ -f "$FIN/$n" ] || { say "!! [1/8] $FIN/$n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/8] $DB is missing - nothing installed"; exit 1; }
AT=0; for n in $ALL; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && AT=$((AT+1)); done
lock_pid() { awk -v k="$KIT" '$1==k{print $2}' "$LOCK/owner" 2>/dev/null; }
lock_stale() { local p; p="$(lock_pid)"; [ -n "$p" ] && ! kill -0 "$p" 2>/dev/null; }
if [ "$AT" = 5 ]; then
  STALE=0
  if [ -d "$LOCK" ] && lock_stale; then rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; STALE=1; say "   (a build lock left by an earlier $KIT run that was stopped was released)"; fi
  if [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ] && ! [ -d "$LOCK" ]; then
    rm -f "$OFFSW"; STALE=1; say "   (a DOCTOR_AUTO_OFF left by an earlier $KIT run that was stopped was removed)"
  fi
  if [ "$STALE" = 1 ] && [ "${DRY:-0}" != 1 ]; then
    "$SYSTEMCTL" restart "$FSVC" || true
    say "   clinic-finance restarted after the stopped run: healthz $(wait200 fhz) (anything but 200: send a photo of this screen to Claude)"
  fi
  say "-- ALREADY INSTALLED: the five files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0
fi
if [ "$AT" != 0 ]; then
  say "!! [1/8] $AT of the five files are already at the kit's TO and the rest are not - HALF PLACED: nothing installed. Tell Claude."; exit 1
fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window, the kit's five files at their TO pins); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif lock_stale; then
  TOOK_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock left by an earlier $KIT run that was stopped is taken over"
elif [ -n "$(lock_pid)" ]; then
  say "!! [1/8] another $KIT run (process $(lock_pid)) is still going - nothing installed. Wait for it to finish."; exit 3
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3
fi
if [ "$TOOK_LOCK" = 1 ] && [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
  OFF_MINE=1; say "      a DOCTOR_AUTO_OFF left by an earlier $KIT run that was stopped is this run's to clear"
fi
for n in $ALL; do C=$(m5 "$FIN/$n"); [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/8] $FIN/$n is ${C:0:8}, expected ${FROM[$n]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
say "[2/8] live pins exact: $(for n in $ALL; do printf '%s %s  ' "$n" "${FROM[$n]:0:8}"; done)"

mkdir -p "$SCR/built" "$SCR/pyc" "$SCR/wtmp" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
for n in $ALL; do \cp -p "$KDIR/$n" "$SCR/built/$n"; done
for py in "$APY" "$VPY"; do for n in $PY; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || stop_unlocked "!! [3/8] $n does not compile on $py - nothing installed"
done; done
say "[3/8] the kit's five files at their TO pins; the three python files compile on both pythons"

mkscratch "$SCR/old"; mkscratch "$SCR/new"
for n in $ALL; do \cp -p "$SCR/built/$n" "$SCR/new/$n"; done
WOUT="$(walk "$SCR/new")"; R="$(echo "$WOUT" | tail -1)"
[ "$R" = "$GREEN" ] || { echo "$WOUT" | grep -E '^  RED|^  MISSED' | head -12; stop_unlocked "!! [4/8] the walk on the new files is not green ($R) - nothing installed"; }
COUT="$(walk "$SCR/old" --control)"; R0="$(echo "$COUT" | tail -1)"
[ "$R0" = "$CONTROL" ] || stop_unlocked "!! [4/8] the control on the live folder is not as expected ($R0) - nothing installed"
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
MV="$(build_month "$SCR/new" "$SCR/snap_new.dat" "$SCR/walk.db")" || stop_unlocked "!! [4/8] the console's builder with the new files, on a copy of the live database: $MV - nothing installed"
rm -f "$SCR/walk.db" "$SCR/snap_new.dat"
for n in $ALL; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || stop_unlocked "!! [4/8] $FIN/$n changed during the walk - nothing installed"; done
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk on made-up databases: $GREEN; the control on the live folder: $R0; the builder on a copy of the live database with the new files: $MV; finance $f0"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the builder green; NOTHING written"; exit 0; fi

for n in $ALL; do
  [ -e "$(bak $n)" ] && [ "$(m5 "$(bak $n)")" != "${FROM[$n]}" ] && stop_unlocked "!! [5/8] a backup $(bak $n) is there and is not the FROM bytes - left as it is; nothing placed. Tell Claude."
  { \cp -p "$FIN/$n" "$(bak $n)" && [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ]; } || stop_unlocked "!! [5/8] could not write the backup $(bak $n) - nothing placed"
done
if [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
  OFF_MINE=1; say "[5/8] DOCTOR_AUTO_OFF was left by an earlier $KIT run that was stopped - this run takes it as its own and removes it at the end"
elif [ -e "$OFFSW" ]; then
  say "[5/8] DOCTOR_AUTO_OFF is already on ($(head -c 120 "$OFFSW" 2>/dev/null)) - left exactly as it is; this kit will not remove it"
else
  mkdir -p "$(dirname "$OFFSW")" || stop_unlocked "!! [5/8] could not make the folder of $OFFSW - nothing placed"
  if (set -o noclobber; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's" > "$OFFSW") 2>/dev/null; then OFF_MINE=1
  else stop_unlocked "!! [5/8] could not write $OFFSW (or someone else set it just now) - nothing placed"; fi
fi
for n in $ALL; do
  STG="$FIN/.$n.s697"
  { cat "$SCR/built/$n" > "$STG" && [ "$(m5 "$STG")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s697; stop_unlocked "!! [5/8] could not stage $n - nothing placed"; }
  chmod --reference="$FIN/$n" "$STG" 2>/dev/null; chown --reference="$FIN/$n" "$STG" 2>/dev/null
done
PLACED=1
for n in month_read.py month_page.html xray_film.py owner_console.html owner_console.py; do mv -f "$FIN/.$n.s697" "$FIN/$n" || restore "the rename of $n"; done
for n in $ALL; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "read back $n"; done
say "[5/8] placed and read back: $(for n in $ALL; do printf '%s %s  ' "$n" "${TO[$n]:0:8}"; done)(backups *.bak_S697_<from8>)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(hcode "http://127.0.0.1:$FIN_PORT/finance/console"); case "$c2" in 302|401|403|303) ;; *) restore "/finance/console answered $c2 without a login";; esac
c3=$(hcode "http://127.0.0.1:$FIN_PORT/finance/console/month"); case "$c3" in 302|401|403|303) ;; *) restore "/finance/console/month answered $c3 without a login";; esac
c4=$(hcode "http://127.0.0.1:$FIN_PORT/finance/slips/film/log"); case "$c4" in 302|401|403|303) ;; *) restore "/finance/slips/film/log answered $c4 without a login";; esac
command -v "$JOURNALCTL" >/dev/null 2>&1 || restore "no $JOURNALCTL to read the service's own word on the mount"
sleep 2
# the NEW master's lines only (S375's lesson: the old master's own shutdown traceback is not this kit's): from the first start line since T0
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn|Listening at:/{f=1} f{print} END{if(!f)exit 9}')" || JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -c -i -E 'month_read|xray_film|owner_console|NOT mounted|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'month_read|xray_film|owner_console|NOT mounted|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR line(s) naming a module of this kit, an import error, a traceback or a part NOT mounted since the restart"; }
say "[6/8] $FSVC restarted at $T0: healthz $c1; the console $c2, the month page $c3 and the film log $c4 without a login (the gate); the new master's journal ($(printf '%s\n' "$JL" | grep -c .) line(s)) names no module of this kit, import error, traceback or 'NOT mounted'"

if [ -e "$SNAPF.lock" ] && [ $(( $(date +%s) - $(stat -c %Y "$SNAPF.lock" 2>/dev/null || echo 0) )) -lt 150 ]; then
  say "[7/8] the service's own reading is being made this moment; the new sections arrive with it"
  MV2="(the service's reading)"
else
  if MV2="$(build_month "$FIN" "$SNAPF" "$DB")"; then
    SNAP_MINE=1; chown --reference="$FIN/owner_console.py" "$SNAPF" 2>/dev/null; chmod 600 "$SNAPF" 2>/dev/null
  elif [ -e "$SNAPF.lock" ]; then
    MV2="(the service's own reading took the lock this moment; the new sections arrive with it)"
  else
    restore "the reading on the box with the placed files: $MV2"
  fi
fi
mkscratch "$SCR/placed"
POUT="$(walk "$SCR/placed")"; R="$(echo "$POUT" | tail -1)"
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || { echo "$POUT" | grep -E '^  RED|^  MISSED' | head -8; restore "the walk on the placed folder: $R"; }
say "[7/8] the reading on the box: $MV2; the walk on the placed folder: $R"
PLACED=3
off_clear; release_lock
say "[8/8] DOCTOR_AUTO_OFF removed if this kit set it; the build lock released"
say "undo (one line): for n in $ALL; do \\cp -p \$(ls $FIN/\$n.bak_S697_* | head -1) $FIN/\$n; done && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The console's bars and lines wear the new look; Sanjeevni carries your pages with their figures; The month has its chips and Other papers; the film log's empty mornings show their slips."
exit 0
