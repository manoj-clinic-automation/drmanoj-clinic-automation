#!/bin/bash
# =============================================================================
#  install_S641_DAY_CHECK_TILES.sh · kit S641 (24-Oct-2026, session S347) · D776 follow-on, D775
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s641kit && cp -rp /root/deploy/repo/deploy_kits/S641_DAY_CHECK_TILES /tmp/s641kit && bash /tmp/s641kit/install_S641_DAY_CHECK_TILES.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  /root/finance/clinic_money.py   7152cd3a -> f8a64266  5 counted edits: the total difference handed to the day check; no rung-as-cash guess; bank_part()
#  /root/finance/day_check.py      332bc8d4 -> da63a580  3 counted edits: the bank part on the page; his tile's landing day
#  /root/finance/aaj_seed.py       ab6e4b14 -> 2f9ab396  1 counted edit: Morning match off reception's list
#  /root/finance/owner_console.py  32780bcb -> a6315bfd  1 counted edit: his console words the new verdict
#  /root/portal/portal.py          d6202952 -> 6470f894  2 counted edits: the Day check and Parchi desk tiles
#  No data step. Restarts clinic-finance and clinic-portal. Red after placing: all five back byte-identically, restart.
#  Undo:  for f in /root/finance/clinic_money.py /root/finance/day_check.py /root/finance/aaj_seed.py /root/finance/owner_console.py /root/portal/portal.py; do \cp -p $f.bak_S641 $f; done; systemctl restart clinic-finance clinic-portal
# =============================================================================
set -u
KIT="S641_DAY_CHECK_TILES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"; POR="${POR:-/root/portal}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"; PSVC="${PSVC:-clinic-portal}"; PPORT="${PPORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
NAMES="clinic_money.py day_check.py aaj_seed.py owner_console.py portal.py"
declare -A FROM=( [clinic_money.py]=7152cd3a7d3dcae6da2a9aee893064e7 [day_check.py]=332bc8d42d51cc3b829de29e71b510ef [aaj_seed.py]=ab6e4b14f83e665400efe91e2f3050e1 [owner_console.py]=32780bcbf4c2a0877df819519cb1334a [portal.py]=d6202952f80fdb8c831463be884ead36 )
declare -A TO=( [clinic_money.py]=f8a64266158cdaae45ec4067ab84006a [day_check.py]=da63a5806f0264188a7872ed4b786d99 [aaj_seed.py]=2f9ab3964769fa67f709f661db7e067f [owner_console.py]=a6315bfdcc0f4811bf546f89dd96002f [portal.py]=6470f8944f8ad3a313816139b9bc263b )
where() { [ "$1" = portal.py ] && echo "$POR/$1" || echo "$FIN/$1"; }
HAVE_LOCK=0; SN=""; SO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$SN" ] && rm -rf "$SN" "$SO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
phealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT/portal/health"; }
restore() { for n in $NAMES; do \cp -p "$(where $n).bak_S641" "$(where $n)"; done; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
all_to=1
for n in $NAMES; do [ "$(m5 "$KDIR/$n")" = "${TO[$n]}" ] || stop "the kit's $n is not the built file"; [ "$(m5 "$(where $n)")" = "${TO[$n]}" ] || all_to=0; done
[ "$all_to" = 1 ] && { echo "ALREADY INSTALLED."; exit 0; }
for n in $NAMES; do L=$(m5 "$(where $n)"); [ "$L" = "${FROM[$n]}" ] || stop "the live $(where $n) changed since this kit was built (live ${L:0:8}, kit expects ${FROM[$n]:0:8})"; done
echo "2. the five live files are the ones this kit was built from"
SN=$(mktemp -d /tmp/s641new.XXXX); SO=$(mktemp -d /tmp/s641old.XXXX)
for n in $NAMES; do \cp "$KDIR/$n" "$SN/$n"; \cp "$(where $n)" "$SO/$n"; done
for n in clinic_money.py day_check.py aaj_seed.py owner_console.py; do "$PY" -B -m py_compile "$SN/$n" || stop "$n does not compile with $PY"; done
/root/wa/venv/bin/python3 -W ignore::SyntaxWarning -B -m py_compile "$SN/portal.py" 2>/dev/null || "$PY" -W ignore::SyntaxWarning -B -m py_compile "$SN/portal.py" || stop "portal.py does not compile"
R=$("$PY" -B walk_s641.py "$SN" "$FIN" 2>&1 | tail -1); case "$R" in "14 of 14 green") echo "3. walk: $R";; *) "$PY" -B walk_s641.py "$SN" "$FIN" 2>&1 | grep RED; stop "the walk is not green ($R)";; esac
R=$("$PY" -B walk_s641.py "$SO" "$FIN" --old 2>&1 | tail -1); case "$R" in "10 S641 check(s) red · 0 older red · 4 green") echo "   control on the live files: $R";; *) echo "$R"; stop "the control on the live files did not go red as expected";; esac
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
PH0=$(phealth); [ "$PH0" = 200 ] || stop "the portal is not healthy before the install ($PH0)"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
for n in $NAMES; do \cp -p "$(where $n)" "$(where $n).bak_S641" || stop "could not keep a backup of $n"; done
for n in $NAMES; do \cp "$KDIR/$n" "$(where $n)" && chmod --reference="$(where $n).bak_S641" "$(where $n)" 2>/dev/null; done
for n in $NAMES; do [ "$(m5 "$(where $n)")" = "${TO[$n]}" ] || { restore; stop "read-back of $n did not match; the old files are back"; }; done
echo "4. placed the five files (backups *.bak_S641)"
"$SYSTEMCTL" restart "$SVC" "$PSVC"
h=000; p=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); p=$(phealth); [ "$h" = 200 ] && [ "$p" = 200 ] && break; done
if [ "$h" != 200 ] || [ "$p" != 200 ]; then
  echo "!! RED after placing (finance $h, portal $p) - putting the old files back"
  restore; "$SYSTEMCTL" restart "$SVC" "$PSVC"
  h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  echo "   after the restore: finance $h2, portal $(phealth). Send a photo of this screen to Claude."; exit 1
fi
echo "5. $SVC and $PSVC restarted; both healthy"
echo ""
echo "INSTALLED. Your PWA: 'Day check' under Docterz & clinic day, 'Parchi desk' under Patients."
