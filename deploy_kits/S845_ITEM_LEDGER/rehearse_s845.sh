#!/bin/bash
# rehearse_s845.sh -- S845's installer and undo on a STAND (a made-up /root): every path, nothing of the server touched.
#   bash rehearse_s845.sh <bundle root dir (root/)> <finance.db copy> <spine.db> <S815 kit dir> <venv python> [all|A|B|A1..A5|B1..B6]
#   REH_W=<dir> keeps one stand across calls (each step is short enough for a shell that may stop after three minutes); A2..A5 need A1's stand.
set -u
SRC="$1"; DBC="$2"; SPC="$3"; OLD="$4"; PY="$5"; PART="${6:-all}"
KD="$(cd "$(dirname "$0")" && pwd)"; W="${REH_W:-$(mktemp -d /tmp/reh845.XXXXXX)}"; mkdir -p "$W"; P=0; F=0
on() { [ "$PART" = all ] || [ "$PART" = "${1:0:1}" ] || [ "$PART" = "$1" ]; }
chk() { if eval "$2"; then P=$((P+1)); echo "PASS  $1"; else F=$((F+1)); echo "FAIL  $1"; fi; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cat > "$W/hz.sh" <<'EOF'
#!/bin/bash
case "$1" in */ledger/api/healthz) if [ -e "$HZROOT/finance/item_ledger.py" ]; then echo "${HZ_LEDGER:-403}"; else echo 404; fi;; *) echo 200;; esac
EOF
chmod +x "$W/hz.sh"
stand() { rm -rf "$W/root" "$W/lock"; mkdir -p "$W/root"; cp -rp "$SRC/finance" "$W/root/finance"; cp -rp "$SRC/shared" "$W/root/shared"; rm -f "$W/root/finance/item_ledger.py"
  cp "$DBC" "$W/root/finance/finance.db"; mkdir -p "$W/root/finance/spine"; cp "$SPC" "$W/root/finance/spine/spine.db"; }
run() { (cd /tmp && env ROOT="$W/root" APY="$PY" VPY="$PY" SYSTEMCTL=true NAP=0 HZROOT="$W/root" HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" OLDK="$OLD" TMPW="$W" "$@" bash "$KIT/install_S845_ITEM_LEDGER.sh" 2>&1); }
undo() { (cd /tmp && env ROOT="$W/root" SYSTEMCTL=true NAP=0 HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" bash "$KIT/undo_s845.sh" 2>&1); }
fromok() { [ "$(m5 "$W/root/finance/sanjeevni_approvals.py")" = cd5174d6bfb9d62b55dd037e903e1d74 ] && [ "$(m5 "$W/root/finance/finance_ui/finance_approvals.html")" = 9f6295856e36f93a00028de7cc3fe769 ] && [ ! -e "$W/root/finance/item_ledger.py" ]; }
took() { awk '$2=="finance/sanjeevni_approvals.py"{a=$1} $2=="finance/finance_ui/finance_approvals.html"{b=$1} $2=="finance/item_ledger.py"{c=$1} END{print a" "b" "c}' "$KD/TO_PINS.md5"; }
took_ok() { set -- $(took); [ "$(m5 "$W/root/finance/sanjeevni_approvals.py")" = "$1" ] && [ "$(m5 "$W/root/finance/finance_ui/finance_approvals.html")" = "$2" ] && [ "$(m5 "$W/root/finance/item_ledger.py")" = "$3" ]; }
KIT="$W/kit"
[ -d "$KIT" ] || { rm -rf "$KIT"; cp -rp "$KD" "$KIT"; }
if on A1; then stand; O=$(run DRY=1); chk "A1 dry run: green and nothing written" 'echo "$O" | grep -q "DRY RUN: every gate" && fromok'; fi
if on A2; then O=$(run); chk "A2 install: DONE, the three at their TO pins" 'echo "$O" | grep -q "S845_ITEM_LEDGER: DONE" && took_ok'
  chk "A2 backups at their FROM pins" '[ "$(m5 "$W/root/finance/sanjeevni_approvals.py.bak_S845_cd5174d6")" = cd5174d6bfb9d62b55dd037e903e1d74 ]'
  chk "A2 the lock released" '[ ! -e "$W/lock" ]'; fi
if on A3; then O=$(run); chk "A3 again: ALREADY INSTALLED" 'echo "$O" | grep -q "ALREADY INSTALLED"'; fi
if on A4; then O=$(undo); chk "A4 undo: FROM pins back, the page gone" 'echo "$O" | grep -q "S845 UNDONE" && fromok'; fi
if on A5; then O=$(run); chk "A5 install after the undo: DONE" 'echo "$O" | grep -q "S845_ITEM_LEDGER: DONE" && took_ok'; fi
if on B1; then stand; O=$(run REHEARSE_RED_AT=4); chk "B1 a red at [4/6]: restored to FROM, the page gone, the lock released" 'echo "$O" | grep -q "RED after placing" && fromok && [ ! -e "$W/lock" ]'; fi
if on B2; then stand; O=$(run HZ_LEDGER=404); chk "B2 the ledger not mounted after the restart: restored" 'echo "$O" | grep -q "not mounted" && fromok'; fi
if on B3; then stand; echo "<!-- drift -->" >> "$W/root/finance/finance_ui/finance_approvals.html"; O=$(run)
  chk "B3 a live file changed since the build: STOP, nothing placed" 'echo "$O" | grep -q "changed after this kit was built" && [ ! -e "$W/root/finance/item_ledger.py" ]'; fi
if on B4; then stand; echo "x" >> "$KIT/README.md"; O=$(run); chk "B4 a corrupt kit: refused at the SUMS gate" 'echo "$O" | grep -q "SUMS.md5 gate failed" && fromok'; rm -rf "$KIT"; cp -rp "$KD" "$KIT"; fi
if on B5; then stand; mkdir -p "$W/lock"; echo other > "$W/lock/owner"; O=$(run); chk "B5 another build holds the lock: refused, nothing placed" 'echo "$O" | grep -q "another build holds the lock" && fromok'; rm -rf "$W/lock"; fi
if on B7; then stand; O=$(run JOURNAL_CMD="echo item_ledger NOT mounted: made-up"); chk "B7 the Hub's log says NOT mounted: restored" 'echo "$O" | grep -q "was NOT mounted" && fromok'; fi
if on B8; then stand; O=$(run); echo "<!-- a later kit -->" >> "$W/root/finance/finance_ui/finance_approvals.html"; O=$(undo)
  chk "B8 undo refuses when a file moved on since S845 (a later kit)" 'echo "$O" | grep -q "not at S845" && [ -e "$W/root/finance/item_ledger.py" ]'; fi
if on B9; then stand; printf '#!/bin/bash\n[ -e "%s/killed" ] || { touch "%s/killed"; kill -TERM $PPID; sleep 1; }\nexit 0\n' "$W" "$W" > "$W/killer.sh"; chmod +x "$W/killer.sh"; rm -f "$W/killed"
  O=$(run SYSTEMCTL="$W/killer.sh"); chk "B9 interrupted while placing: restored to FROM, the page gone, the lock released" 'echo "$O" | grep -q "interrupted while placing" && fromok && [ ! -e "$W/lock" ]'; fi
if on B6; then stand; echo "# not ours" > "$W/root/finance/item_ledger.py"; O=$(run); chk "B6 an item_ledger.py not this kit's: refused" 'echo "$O" | grep -q "already exists and is not this kit" && [ "$(cat "$W/root/finance/item_ledger.py")" = "# not ours" ]'; fi
echo "REHEARSAL S845 ($PART): $P PASS, $F FAIL"
[ -n "${REH_W:-}" ] || rm -rf "$W"
[ "$F" = 0 ]
