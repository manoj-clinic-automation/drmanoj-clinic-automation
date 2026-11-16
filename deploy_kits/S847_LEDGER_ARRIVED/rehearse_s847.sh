#!/bin/bash
# rehearse_s847.sh -- S847's installer and undo on a STAND (a made-up /root with S845 installed): every path, nothing of the server touched.
#   bash rehearse_s847.sh <bundle root/> <S845 kit dir> <made-up finance.db> <made-up spine.db> <python> [all|A1..A5|B1..B7]   (REH_W keeps one stand)
set -u
SRC="$1"; K845="$2"; DBC="$3"; SPC="$4"; PY="$5"; PART="${6:-all}"
KD="$(cd "$(dirname "$0")" && pwd)"; W="${REH_W:-$(mktemp -d /tmp/reh847.XXXXXX)}"; mkdir -p "$W"; P=0; F=0
on() { [ "$PART" = all ] || [ "$PART" = "$1" ]; }
chk() { if eval "$2"; then P=$((P+1)); echo "PASS  $1"; else F=$((F+1)); echo "FAIL  $1"; fi; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
FROM=22c24bd91e82f77cc34c5f4d27d8dc51; TO=$(awk '$2=="finance/item_ledger.py"{print $1}' "$KD/TO_PINS.md5")
cat > "$W/hz.sh" <<'EOF'
#!/bin/bash
case "$1" in */ledger/api/healthz) echo "${HZ_LEDGER:-403}";; *) echo 200;; esac
EOF
chmod +x "$W/hz.sh"
stand() { rm -rf "$W/root" "$W/lock"; mkdir -p "$W/root"; cp -rp "$SRC/finance" "$W/root/finance"; cp -rp "$SRC/shared" "$W/root/shared"
  python3 "$K845/make_s845.py" "$SRC/finance" "$W/root/finance" >/dev/null && cp "$K845/item_ledger.py" "$W/root/finance/item_ledger.py"
  cp "$DBC" "$W/root/finance/finance.db"; mkdir -p "$W/root/finance/spine"; cp "$SPC" "$W/root/finance/spine/spine.db"; }
KIT="$W/kit"; [ -d "$KIT" ] || cp -rp "$KD" "$KIT"
run() { (cd /tmp && env ROOT="$W/root" APY="$PY" VPY="$PY" SYSTEMCTL=true NAP=0 HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" K845="$K845" TMPW="$W" "$@" bash "$KIT/install_S847_LEDGER_ARRIVED.sh" 2>&1); }
undo() { (cd /tmp && env ROOT="$W/root" SYSTEMCTL=true NAP=0 HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" bash "$KIT/undo_s847.sh" 2>&1); }
at() { [ "$(m5 "$W/root/finance/item_ledger.py")" = "$1" ]; }
if on A1; then stand; O=$(run DRY=1); chk "A1 dry run: green, nothing written" 'echo "$O" | grep -q "DRY RUN: every gate" && at $FROM'; fi
if on A2; then O=$(run); chk "A2 install: DONE at the TO pin, backup at S845's, lock released" 'echo "$O" | grep -q "S847_LEDGER_ARRIVED: DONE" && at $TO && [ "$(m5 "$W/root/finance/item_ledger.py.bak_S847_22c24bd9")" = $FROM ] && [ ! -e "$W/lock" ]'; fi
if on A3; then O=$(run); chk "A3 again: ALREADY INSTALLED" 'echo "$O" | grep -q "ALREADY INSTALLED"'; fi
if on A4; then O=$(undo); chk "A4 undo: S845's page back" 'echo "$O" | grep -q "S847 UNDONE" && at $FROM'; fi
if on A5; then O=$(run); chk "A5 install after the undo: DONE" 'echo "$O" | grep -q "S847_LEDGER_ARRIVED: DONE" && at $TO'; fi
if on B1; then stand; O=$(run REHEARSE_RED_AT=4); chk "B1 a red at [4/5]: S845's page back, lock released" 'echo "$O" | grep -q "RED after placing" && at $FROM && [ ! -e "$W/lock" ]'; fi
if on B2; then stand; O=$(run HZ_LEDGER=404); chk "B2 not mounted after the restart: restored" 'echo "$O" | grep -q "not mounted" && at $FROM'; fi
if on B3; then stand; echo "# drift" >> "$W/root/finance/item_ledger.py"; O=$(run); chk "B3 the live page is not S845's: STOP, nothing placed" 'echo "$O" | grep -q "expected S845" && tail -1 "$W/root/finance/item_ledger.py" | grep -q drift'; fi
if on B4; then stand; echo x >> "$KIT/README.md"; O=$(run); chk "B4 a corrupt kit: refused" 'echo "$O" | grep -q "SUMS.md5 gate failed" && at $FROM'; rm -rf "$KIT"; cp -rp "$KD" "$KIT"; fi
if on B5; then stand; mkdir -p "$W/lock"; echo other > "$W/lock/owner"; O=$(run); chk "B5 the lock held: refused" 'echo "$O" | grep -q "another build holds the lock" && at $FROM'; rm -rf "$W/lock"; fi
if on B6; then stand; printf '#!/bin/bash\n[ -e "%s/killed" ] || { touch "%s/killed"; kill -TERM $PPID; sleep 1; }\nexit 0\n' "$W" "$W" > "$W/killer.sh"; chmod +x "$W/killer.sh"; rm -f "$W/killed"
  O=$(run SYSTEMCTL="$W/killer.sh"); chk "B6 interrupted while placing: S845's page back, lock released" 'echo "$O" | grep -q "interrupted while placing" && at $FROM && [ ! -e "$W/lock" ]'; fi
if on B7; then stand; O=$(run); echo "# later kit" >> "$W/root/finance/item_ledger.py"; O=$(undo); chk "B7 undo refuses when the page moved on" 'echo "$O" | grep -q "not at S847" && tail -1 "$W/root/finance/item_ledger.py" | grep -q "later kit"'; fi
echo "REHEARSAL S847 ($PART): $P PASS, $F FAIL"
[ -n "${REH_W:-}" ] || rm -rf "$W"
[ "$F" = 0 ]
