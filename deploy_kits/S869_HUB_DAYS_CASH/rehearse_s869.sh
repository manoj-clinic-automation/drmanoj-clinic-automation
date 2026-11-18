#!/bin/bash
# rehearse_s869.sh -- S869's installer and undo on a STAND (a made-up /root): every path, nothing of the server touched.
#   bash rehearse_s869.sh <bundle root dir (root/)> <finance.db copy> <deploy_kits dir (the older walks)> <python with flask> [all|A|B|A1..A5|B1..B8]
#   REH_W=<dir> keeps one stand across calls (each step is short enough for a shell that may stop after three minutes); A2..A5 need A1's stand.
set -u
SRC="$1"; DBC="$2"; OLD="$3"; PY="$4"; PART="${5:-all}"
KD="$(cd "$(dirname "$0")" && pwd)"; W="${REH_W:-$(mktemp -d /tmp/reh869.XXXXXX)}"; mkdir -p "$W"; P=0; F=0
on() { [ "$PART" = all ] || [ "$PART" = "${1:0:1}" ] || [ "$PART" = "$1" ]; }
chk() { if eval "$2"; then P=$((P+1)); echo "PASS  $1"; else F=$((F+1)); echo "FAIL  $1"; fi; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cat > "$W/hz.sh" <<'EOF'
#!/bin/bash
case "$1" in */hub-cash/healthz) if [ -e "$HZROOT/finance/hub_cash.py" ]; then echo "${HZ_HUB:-200}"; else echo 404; fi;; *) echo 200;; esac
EOF
chmod +x "$W/hz.sh"
stand() { rm -rf "$W/root" "$W/lock"; mkdir -p "$W/root"; cp -rp "$SRC/finance" "$W/root/finance"; rm -f "$W/root/finance/hub_cash.py" "$W/root/finance/finance.db"; cp "$DBC" "$W/root/finance/finance.db"; }
run() { (cd /tmp && env ROOT="$W/root" APY="$PY" VPY="$PY" SYSTEMCTL=true NAP=0 HZROOT="$W/root" HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" OLDK="$OLD" TMPW="$W" "$@" bash "$KIT/install_S869_HUB_DAYS_CASH.sh" 2>&1); }
undo() { (cd /tmp && env ROOT="$W/root" SYSTEMCTL=true NAP=0 HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" bash "$KIT/undo_s869.sh" 2>&1); }
fromok() { [ "$(m5 "$W/root/finance/sanjeevni_cash.py")" = 8e58691bac16fceb00602e7f8eabdaf8 ] && [ "$(m5 "$W/root/finance/sanjeevni_day.py")" = 22a38006a4e3be59b47ea091ea1f971f ] && [ "$(m5 "$W/root/finance/day_resync.py")" = 00b45a150df15123106fbcc641f913ab ] && [ "$(m5 "$W/root/finance/finance_ui/finance_approvals.html")" = 17f13acc3b9f18ef2be71eefcc811c07 ] && [ ! -e "$W/root/finance/hub_cash.py" ]; }
took_ok() { local n; for n in finance/sanjeevni_cash.py finance/sanjeevni_day.py finance/day_resync.py finance/finance_ui/finance_approvals.html finance/hub_cash.py; do [ "$(m5 "$W/root/$n")" = "$(awk -v f="$n" '$2==f{print $1}' "$KD/TO_PINS.md5")" ] || return 1; done; }
drawer() { "$PY" - "$W/root/finance" "$W/root/finance/finance.db" <<'EOF'
import sqlite3, sys; sys.path.insert(0, sys.argv[1]); import sanjeevni_cash as sc
c = sqlite3.connect(sys.argv[2]); r = sc.days(c, "2026-09-01", "9999-12-31"); print(r["rows"][-1]["close"]["drawer"])
EOF
}
kept() { "$PY" - "$W/root/finance/finance.db" <<'EOF'
import sqlite3, sys; c = sqlite3.connect(sys.argv[1])
print(c.execute("SELECT COUNT(*) FROM owner_day_entry WHERE removed_at IS NULL").fetchone()[0], c.execute("SELECT handed_p FROM darpan_kal_day WHERE business_date='2026-10-09'").fetchone()[0])
EOF
}
KIT="$W/kit"
[ -d "$KIT" ] || { rm -rf "$KIT"; cp -rp "$KD" "$KIT"; }
if on A1; then stand; O=$(run DRY=1); chk "A1 dry run: green and nothing written (files at FROM, drawer unchanged 21,508)" 'echo "$O" | grep -q "DRY RUN: every gate" && fromok && [ "$(drawer)" = 2150800 ]'; fi
if on A2; then O=$(run); chk "A2 install: DONE, the five at their TO pins" 'echo "$O" | grep -q "S869_HUB_DAYS_CASH: DONE" && took_ok'
  chk "A2 day_resync fixed 9-Oct and 14-Oct on the stand" 'echo "$O" | grep -q "FIXED     2026-10-09" && echo "$O" | grep -q "FIXED     2026-10-14"'
  chk "A2 the one-off applied: drawer 549 (17-Oct left for his tap)" 'echo "$O" | grep -q "one-off APPLY: OK" && [ "$(drawer)" = 54900 ]'
  chk "A2 backups at their FROM pins; the lock released" '[ "$(m5 "$W/root/finance/sanjeevni_day.py.bak_S869_22a38006")" = 22a38006a4e3be59b47ea091ea1f971f ] && [ ! -e "$W/lock" ]'; fi
if on A3; then O=$(run); chk "A3 again: ALREADY INSTALLED, the one-off re-run says already, drawer still 549" 'echo "$O" | grep -q "ALREADY INSTALLED" && echo "$O" | grep -q "already" && [ "$(drawer)" = 54900 ]'; fi
if on A4; then O=$(undo); chk "A4 undo: FROM pins back, the module gone, the data stays (3 entries, 9-Oct 13,258)" 'echo "$O" | grep -q "S869 UNDONE" && fromok && [ "$(kept)" = "3 1325800" ]'; fi
if on A5; then O=$(run); chk "A5 install after the undo: DONE, every one-off step already done" 'echo "$O" | grep -q "S869_HUB_DAYS_CASH: DONE" && took_ok && echo "$O" | grep -q "already"'; fi
if on B1; then stand; O=$(run REHEARSE_RED_AT=4); chk "B1 a red at [4/7]: restored to FROM, the module gone, the lock released, nothing written" 'echo "$O" | grep -q "RED after placing" && fromok && [ ! -e "$W/lock" ] && [ "$(drawer)" = 2150800 ]'; fi
if on B2; then stand; O=$(run HZ_HUB=404); chk "B2 hub_cash not mounted after the restart: restored, nothing written" 'echo "$O" | grep -q "not mounted" && fromok && [ "$(drawer)" = 2150800 ]'
  stand; O=$(run HZ_HUB=302); chk "B2b hub_cash answers 302 (behind the login gate, as on the box): installed" 'echo "$O" | grep -q "S869_HUB_DAYS_CASH: DONE" && took_ok'; fi
if on B3; then stand; echo "<!-- drift -->" >> "$W/root/finance/finance_ui/finance_approvals.html"; O=$(run)
  chk "B3 a live file changed since the build: STOP, nothing placed" 'echo "$O" | grep -q "changed after this kit was built" && [ ! -e "$W/root/finance/hub_cash.py" ]'; fi
if on B4; then stand; echo "x" >> "$KIT/README.md"; O=$(run); chk "B4 a corrupt kit: refused at the SUMS gate" 'echo "$O" | grep -q "SUMS.md5 gate failed" && fromok'; rm -rf "$KIT"; cp -rp "$KD" "$KIT"; fi
if on B5; then stand; mkdir -p "$W/lock"; echo other > "$W/lock/owner"; O=$(run); chk "B5 another build holds the lock: refused, nothing placed" 'echo "$O" | grep -q "another build holds the lock" && fromok'; rm -rf "$W/lock"; fi
if on B6; then stand; O=$(run); echo "<!-- a later kit -->" >> "$W/root/finance/finance_ui/finance_approvals.html"; O=$(undo)
  chk "B6 undo refuses when a file moved on since S869 (a later kit)" 'echo "$O" | grep -q "not at S869" && [ -e "$W/root/finance/hub_cash.py" ]'; fi
if on B7; then stand; O=$(run JOURNAL_CMD="echo hub_cash not mounted: made-up"); chk "B7 the Hub's log says NOT mounted: restored" 'echo "$O" | grep -q "was NOT mounted" && fromok'; fi
if on B8; then stand; touch "$W/root/finance/hub_cash.py"; O=$(run); chk "B8 a stranger hub_cash.py already there: refused, nothing placed" 'echo "$O" | grep -q "already exists and is not this kit" && [ "$(m5 "$W/root/finance/sanjeevni_day.py")" = 22a38006a4e3be59b47ea091ea1f971f ]'; fi
echo "REHEARSE S869: $P PASS, $F FAIL"
[ "$PART" = all ] && rm -rf "$W"
exit $F
