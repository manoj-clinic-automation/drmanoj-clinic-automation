#!/bin/bash
# undo_s869.sh -- S869_HUB_DAYS_CASH's FILES taken away: the four backups back (each checked against its FROM pin first), hub_cash.py removed,
# clinic-finance restarted. The data the one-off wrote (the owner's rulings, every row audited) STAYS: the old files simply do not read
# owner_day_entry, and the 9-Oct / 3-Nov corrections are the records as he ruled them.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
KD="$(cd "$(dirname "$0")" && pwd)"; LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
to_of() { awk -v f="$1" '$2==f{print $1}' "$KD/TO_PINS.md5"; }
PINS="finance/sanjeevni_cash.py 8e58691bac16fceb00602e7f8eabdaf8
finance/sanjeevni_day.py 22a38006a4e3be59b47ea091ea1f971f
finance/day_resync.py 00b45a150df15123106fbcc641f913ab
finance/finance_ui/finance_approvals.html 17f13acc3b9f18ef2be71eefcc811c07"
while read -r n f; do [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || { echo "!! $ROOT/$n is not at S869's TO pin (changed since: a later kit?) - nothing undone. Tell Claude."; exit 1; }; done <<< "$PINS"
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "undo_s869 $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
while read -r n f; do b="$ROOT/$n.bak_S869_${f:0:8}"; [ "$(m5 "$b")" = "$f" ] || { echo "!! the backup $b is not at its FROM pin ${f:0:8} - nothing changed. Tell Claude."; exit 1; }; done <<< "$PINS"
while read -r n f; do \cp -p "$ROOT/$n.bak_S869_${f:0:8}" "$ROOT/$n" || { echo "!! could not put $n back"; exit 1; }; done <<< "$PINS"
rm -f "$ROOT/finance/hub_cash.py"
"$SYSTEMCTL" restart "$FSVC" || true
h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; if [ -n "${HEALTH_CMD:-}" ]; then h=$($HEALTH_CMD /finance/healthz); else h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); fi; [ "$h" = 200 ] && break; done
echo "S869 UNDONE (files): sanjeevni_cash.py $(m5 "$ROOT/finance/sanjeevni_cash.py" | cut -c1-8), sanjeevni_day.py $(m5 "$ROOT/finance/sanjeevni_day.py" | cut -c1-8), day_resync.py $(m5 "$ROOT/finance/day_resync.py" | cut -c1-8), finance_approvals.html $(m5 "$ROOT/finance/finance_ui/finance_approvals.html" | cut -c1-8), hub_cash.py present: $([ -e "$ROOT/finance/hub_cash.py" ] && echo yes || echo no); finance healthz $h. The audited data stays."
