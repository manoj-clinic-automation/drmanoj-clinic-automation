#!/bin/bash
# =============================================================================
#  install_S784_HUB_GOTO_LABEL.sh · kit S784 (11-Nov-2026, Sanjeevni session 426) · the owner's go 06:38 IST
#  The Sanjeevni Hub's "Go to" panel: the link to the Purchase bills page is renamed
#  "Purchase bills — in Marg · scanned · differences" (it read "Scan register (bills ↔ Marg)"). One line; a page file, no restart.
#   /root/finance/finance_ui/finance_approvals.html   dcd94412 -> TO
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s784kit && cp -rp /root/deploy/repo/deploy_kits/S784_HUB_GOTO_LABEL /tmp/s784kit && bash /tmp/s784kit/install_S784_HUB_GOTO_LABEL.sh
# =============================================================================
set -u
KIT="S784_HUB_GOTO_LABEL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"
F="finance/finance_ui/finance_approvals.html"
FROM="dcd94412d3c342b38c237d86d451178b"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s784_inst_$STAMP"; TOOK_LOCK=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$ROOT/$F.bak_S784_${FROM:0:8}"; STG="$(dirname "$ROOT/$F")/.$(basename "$F").s784"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; [ "$PLACED" = 2 ] || rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the file back"; PLACED=2; \cp -p "$BAK" "$ROOT/$F"; say "   $ROOT/$F $(m5 "$ROOT/$F" | cut -c1-8) (expected ${FROM:0:8}). Send a photo of this screen to Claude."; release_lock; exit 1; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/4] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/4] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ -f "$ROOT/$F" ] || { say "!! [1/4] TO pin or $ROOT/$F missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$F")" = "$TO" ] && { say "-- ALREADY INSTALLED: the page is the kit's. Nothing written."; exit 0; }
mkdir -p "$SCR/built" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/4] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/4] kit gates green; the build lock taken by $KIT"
else say "!! [1/4] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$F")" = "$FROM" ] || stop "!! [2/4] $ROOT/$F is $(m5 "$ROOT/$F" | cut -c1-8), expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
"$APY" -B make_s784.py "$ROOT/finance" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/4] the builder refused - nothing installed"; }
[ "$(m5 "$SCR/built/finance_approvals.html")" = "$TO" ] || stop "!! [2/4] rebuilt, the page is not at its TO pin - nothing installed"
R=$("$APY" -B walk_s784.py "$SCR/built/finance_approvals.html" "$ROOT/$F" | tail -1); [ "$R" = "WALK S784 GREEN" ] || stop "!! [3/4] the walk: $R - nothing installed"
R0=$("$APY" -B walk_s784.py "$ROOT/$F" "$ROOT/$F" --control | tail -1); [ "$R0" = "CONTROL S784 RED as it must be" ] || stop "!! [3/4] the control: $R0 - nothing installed"
say "[2/4] live pin exact (dcd94412); rebuilt here at its TO pin · [3/4] walk_s784: $R; its control red as it must be"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the control green; NOTHING written"; exit 0; fi
{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/4] could not write the backup - nothing placed"
{ cat "$SCR/built/finance_approvals.html" > "$STG" && chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null; [ "$(m5 "$STG")" = "$TO" ]; } || stop "!! [4/4] could not stage - nothing placed"
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/4]"
h=$(fhz); [ "$h" = 200 ] || restore "finance healthz $h"
release_lock
say "[4/4] placed and read back: finance_approvals.html ${TO:0:8}; finance healthz $h (a page file: no restart)"
say "undo (one line): \\cp -p $BAK $ROOT/$F"
say ""
say "$KIT: DONE. The Hub's Go to ▾ now reads 'Purchase bills — in Marg · scanned · differences': https://followup.dr-manoj.in/finance/approvals"
exit 0
