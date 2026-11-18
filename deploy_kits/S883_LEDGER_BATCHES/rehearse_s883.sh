#!/bin/bash
# rehearse_s883.sh -- S883's installer and undo on a STAND (a made-up /root from the code bundle, COPIES of the databases): every path,
# nothing of the server touched.
#   bash rehearse_s883.sh <bundle root/> <kits dir> <finance.db copy> <spine.db copy> <MargArchive dir> <python> [all|A1..A5|B1..B7]   (REH_W keeps one stand)
set -u
SRC="$1"; KITS="$2"; DBC="$3"; SPC="$4"; ARCHD="$5"; PY="$6"; PART="${7:-all}"
KD="$(cd "$(dirname "$0")" && pwd)"; W="${REH_W:-$(mktemp -d /tmp/reh883.XXXXXX)}"; mkdir -p "$W"; P=0; F=0
on() { [ "$PART" = all ] || [ "$PART" = "$1" ]; }
chk() { if eval "$2"; then P=$((P+1)); echo "PASS  $1"; else F=$((F+1)); echo "FAIL  $1"; fi; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
F1=1ed95b6cda37af1b1a279129119fae4a; F2=b4040d8fc2d09719b27747c9f6a51d26
T1=$(awk '$2=="finance/expiry_watch.py"{print $1}' "$KD/TO_PINS.md5"); T2=$(awk '$2=="finance/item_ledger.py"{print $1}' "$KD/TO_PINS.md5")
cat > "$W/hz.sh" <<'EOS'
#!/bin/bash
case "$1" in */ledger/api/healthz) echo "${HZ_LEDGER:-302}";; *) echo 200;; esac
EOS
chmod +x "$W/hz.sh"
mkdir -p "$W/ingest"; ln -sfn "$ARCHD" "$W/ingest/archive"
stand() { rm -rf "$W/root" "$W/lock"; mkdir -p "$W/root"; cp -rp "$SRC/finance" "$W/root/finance"; [ -d "$SRC/shared" ] && cp -rp "$SRC/shared" "$W/root/shared"
  cp "$DBC" "$W/root/finance/finance.db"; mkdir -p "$W/root/finance/spine"; cp "$SPC" "$W/root/finance/spine/spine.db"; }
KIT="$W/kit"; [ -d "$KIT" ] || cp -rp "$KD" "$KIT"
run() { (cd /tmp && env ROOT="$W/root" APY="$PY" VPY="$PY" SYSTEMCTL=true NAP=0 HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" KITS="$KITS" ARCH="$ARCHD" MARG_INGEST="$W/ingest" SAMPLE="${SAMPLE:-8}" TMPW="$W" "$@" bash "$KIT/install_S883_LEDGER_BATCHES.sh" 2>&1); }
undo() { (cd /tmp && env ROOT="$W/root" SYSTEMCTL=true NAP=0 HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" bash "$KIT/undo_s883.sh" 2>&1); }
at() { [ "$(m5 "$W/root/finance/expiry_watch.py")" = "$1" ] && [ "$(m5 "$W/root/finance/item_ledger.py")" = "$2" ]; }
rows() { "$PY" -c 'import sqlite3,sys;c=sqlite3.connect(sys.argv[1]);print(c.execute("SELECT COUNT(*) FROM stock_batch_now").fetchone()[0])' "$W/root/finance/finance.db" 2>/dev/null || echo 0; }
if on A1; then stand; O=$(run DRY=1); chk "A1 dry run: green, nothing written" 'echo "$O" | grep -q "DRY RUN: every gate" && at $F1 $F2 && [ "$(rows)" = 0 ]'; echo "$O" | tail -8; fi
if on A2; then O=$(run); chk "A2 install: DONE at the TO pins, backups at FROM, the Expiry watch ran, rows kept, lock released" 'echo "$O" | grep -q "S883_LEDGER_BATCHES: DONE" && at $T1 $T2 && [ "$(m5 "$W/root/finance/expiry_watch.py.bak_S883_1ed95b6c")" = $F1 ] && [ "$(m5 "$W/root/finance/item_ledger.py.bak_S883_b4040d8f")" = $F2 ] && [ "$(rows)" -gt 50 ] && [ ! -e "$W/lock" ]'; echo "$O" | tail -6; fi
if on A3; then O=$(run); chk "A3 again: ALREADY INSTALLED" 'echo "$O" | grep -q "ALREADY INSTALLED"'; fi
if on A4; then O=$(undo); chk "A4 undo: both files back" 'echo "$O" | grep -q "S883 undone" && at $F1 $F2'; fi
if on A5; then O=$(run); chk "A5 install after the undo: DONE" 'echo "$O" | grep -q "S883_LEDGER_BATCHES: DONE" && at $T1 $T2'; fi
if on B1; then stand; O=$(run REHEARSE_RED_AT=4); chk "B1 a red at [4/5]: both files back, lock released" 'echo "$O" | grep -q "RED after placing" && at $F1 $F2 && [ ! -e "$W/lock" ]'; fi
if on B2; then stand; O=$(run HZ_LEDGER=404); chk "B2 not mounted after the restart: restored" 'echo "$O" | grep -q "not mounted" && at $F1 $F2'; fi
if on B3; then stand; echo "# drift" >> "$W/root/finance/expiry_watch.py"; O=$(run); chk "B3 a live file not at FROM: STOP, nothing placed" 'echo "$O" | grep -q "STOP, nothing installed" && tail -1 "$W/root/finance/expiry_watch.py" | grep -q drift && [ "$(m5 "$W/root/finance/item_ledger.py")" = $F2 ]'; fi
if on B4; then stand; echo x >> "$KIT/README.md"; O=$(run); chk "B4 a corrupt kit: refused" 'echo "$O" | grep -q "SUMS.md5 gate failed" && at $F1 $F2'; rm -rf "$KIT"; cp -rp "$KD" "$KIT"; fi
if on B5; then stand; mkdir -p "$W/lock"; echo other > "$W/lock/owner"; O=$(run); chk "B5 the lock held: refused" 'echo "$O" | grep -q "another build holds the lock" && at $F1 $F2'; rm -rf "$W/lock"; fi
if on B6; then stand; printf '#!/bin/bash\n[ -e "%s/killed" ] || { touch "%s/killed"; kill -TERM $PPID; sleep 1; }\nexit 0\n' "$W" "$W" > "$W/killer.sh"; chmod +x "$W/killer.sh"; rm -f "$W/killed"
  O=$(run SYSTEMCTL="$W/killer.sh"); chk "B6 interrupted while placing: both files back, lock released" 'echo "$O" | grep -q "interrupted while placing" && at $F1 $F2 && [ ! -e "$W/lock" ]'; fi
if on B7; then stand; O=$(run); echo "# later kit" >> "$W/root/finance/item_ledger.py"; O=$(undo); chk "B7 undo refuses when a file moved on" 'echo "$O" | grep -q "neither S883" && tail -1 "$W/root/finance/item_ledger.py" | grep -q "later kit"'; fi
echo "REHEARSAL S883 ($PART): $P PASS, $F FAIL"
[ -n "${REH_W:-}" ] || rm -rf "$W"
[ "$F" = 0 ]
