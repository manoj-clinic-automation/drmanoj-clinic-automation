#!/bin/bash
# rehearse_s909.sh -- the installer on a MADE-UP root: dry, red at [4/5], door not mounted, install, again, undo, undo again, tamper, drift, lock.
#   bash rehearse_s909.sh <dir holding the FROM finance tree (with spine/)> <a copy of finance.db>
set -u; K="$(cd "$(dirname "$0")" && pwd)"; SRC="$1"; DBC="$2"; W=$(mktemp -d /tmp/s909reh.XXXX); P=0; F=0
ok() { echo "ok   $1"; P=$((P+1)); }; bad() { echo "RED  $1"; F=$((F+1)); }
mk() { rm -rf "$W/root" "$W/kit" "$W/cron"; mkdir -p "$W/root/finance/spine" "$W/root/shared"; cp -p "$SRC"/*.py "$W/root/finance/"; rm -f "$W/root/finance/phone_check.py"
  cp -p "$SRC"/spine/*.py "$W/root/finance/spine/" 2>/dev/null; cp "$DBC" "$W/root/finance/finance.db"; cp -rp "$K" "$W/kit"; echo "0 3 * * * echo nightly # OTHER" > "$W/cron"
  mkdir -p "$W/root/wa/wa_logs" "$W/root/wa/wa_inbox"; touch "$W/root/wa/wa_logs/$(date +%F).jsonl"
  python3 -c 'import sqlite3,sys;c=sqlite3.connect(sys.argv[1]);c.execute("CREATE TABLE IF NOT EXISTS msgs(rid INTEGER PRIMARY KEY, body TEXT)");c.commit()' "$W/root/wa/wa_inbox/inbox.db"; }
printf '#!/bin/bash\necho "$@" >> %s/sysctl.log\n' "$W" > "$W/sc"; printf '#!/bin/bash\necho 200\n' > "$W/hz"; printf '#!/bin/bash\necho 401\n' > "$W/door"; printf '#!/bin/bash\necho 404\n' > "$W/door404"
printf '#!/bin/bash\nif [ "$1" = "-l" ]; then cat %s/cron 2>/dev/null; elif [ "$1" = "-" ]; then cat > %s/cron.new && mv %s/cron.new %s/cron; fi\n' "$W" "$W" "$W" "$W" > "$W/ct"
chmod +x "$W"/sc "$W"/hz "$W"/door "$W"/door404 "$W"/ct
run() { (export ROOT="$W/root" LOCK="$W/lock" SYSTEMCTL="$W/sc" CRONTAB="$W/ct" HEALTH_CMD="$W/hz" DOOR_CMD="${DC:-$W/door}" VPY=python3 APY=python3 NAP=0 TMPW="$W"; "$@" bash "$W/kit/install_S909_PHONE_DAILY_CHECK.sh" 2>&1); }
und() { (export ROOT="$W/root" LOCK="$W/lock" SYSTEMCTL="$W/sc" CRONTAB="$W/ct" VPY=python3; bash "$W/kit/undo_s909.sh") 2>&1; }
pins() { for f in supplier_msg.py porders_s454.py phone_check.py; do [ -f "$W/root/finance/$f" ] && md5sum "$W/root/finance/$f" | cut -c1-8 || echo absent; done | tr '\n' ' '; }
cronn() { grep -c "S909_PHONE_CHECK" "$W/cron" 2>/dev/null; }
FROM="407d2b1d 06966a0f absent "; TO="$(awk '{print substr($1,1,8)}' "$K/TO_PINS.md5" | tr '\n' ' ')"
mk; o=$(run env DRY=1); echo "$o" | grep -q "DRY RUN: every gate" && [ "$(pins)" = "$FROM" ] && [ "$(cronn)" = 0 ] && ok "A1 dry: walk green, nothing written" || { bad "A1 dry"; echo "$o" | tail -6; }
mk; o=$(run env REHEARSE_RED_AT=4); [ "$(pins)" = "$FROM" ] && [ "$(cronn)" = 0 ] && echo "$o" | grep -q "RED after placing" && ok "A2 red at [4/5]: all back, phone_check.py gone, no cron line" || { bad "A2"; echo "$o" | tail -5; }
mk; o=$(DC="$W/door404" run env); [ "$(pins)" = "$FROM" ] && [ "$(cronn)" = 0 ] && echo "$o" | grep -q "not mounted" && ok "A3 door 404 = not mounted: all back" || { bad "A3"; echo "$o" | tail -4; }
mk; o=$(run env); [ "$(pins)" = "$TO" ] && [ "$(cronn)" = 1 ] && grep -q "OTHER" "$W/cron" && echo "$o" | grep -q "S909_PHONE_DAILY_CHECK: DONE" && ok "A4 install: three files at TO, one cron line, other lines kept" || { bad "A4"; echo "$o" | tail -8; }
[ ! -d "$W/lock" ] && ls "$W"/root/finance/*.bak_S909_* >/dev/null 2>&1 && ok "A5 backups beside, lock gone" || bad "A5"
o=$(run env); echo "$o" | grep -q "ALREADY INSTALLED" && [ "$(cronn)" = 1 ] && ok "A6 again: ALREADY INSTALLED, still one cron line" || { bad "A6"; echo "$o" | tail -3; }
o=$(und); [ "$(pins)" = "$FROM" ] && [ "$(cronn)" = 0 ] && grep -q "OTHER" "$W/cron" && echo "$o" | grep -q "UNDONE" && ok "A7 undo: files back, phone_check.py out, cron line out, others kept" || { bad "A7"; echo "$o"; }
o=$(und); echo "$o" | grep -q "already gone" && echo "$o" | grep -c "already at its old" | grep -q 2 && ok "A8 undo again: nothing to do" || { bad "A8"; echo "$o"; }
mk; echo "#" >> "$W/kit/porders_s454.py"; o=$(run env); echo "$o" | grep -q "SUMS.md5 gate failed" && [ "$(pins)" = "$FROM" ] && ok "A9 tampered kit refused" || bad "A9"
mk; echo "#" >> "$W/root/finance/supplier_msg.py"; o=$(run env); echo "$o" | grep -q "STOP, nothing installed" && ok "A10 live drift refused" || bad "A10"
mk; mkdir "$W/lock"; o=$(run env); echo "$o" | grep -q "another build holds the lock" && ok "A11 lock held: refused" || bad "A11"; rmdir "$W/lock"
mk; echo "*/5 * * * * x # S909_PHONE_CHECK" >> "$W/cron"; o=$(run env); echo "$o" | grep -q "cron line tagged" && [ "$(pins)" = "$FROM" ] && ok "A12 a stray S909 cron line: refused" || bad "A12"
mk; rm -f "$W"/root/wa/wa_logs/*.jsonl; o=$(run env); echo "$o" | grep -q "no receiver file" && [ "$(pins)" = "$FROM" ] && ok "A13 no receiver file: refused at [2/5]" || { bad "A13"; echo "$o" | tail -3; }
mk; o=$(run env); python3 -c 'import sqlite3,sys;c=sqlite3.connect(sys.argv[1]);c.execute("INSERT INTO supplier_msg (month,vendor_norm,vendor,kind,ref,to_number,body,status,queued_at) VALUES (\x27check\x27,\x27CHECK\x27,\x27x\x27,\x27check\x27,999,\x27x\x27,\x27b\x27,\x27failed\x27,\x272026-01-01T00:00:00\x27)");c.commit()' "$W/root/finance/finance.db"
o=$(und); n=$(python3 -c 'import sqlite3,sys;print(sqlite3.connect(sys.argv[1]).execute("SELECT COUNT(*) FROM supplier_msg WHERE kind=\x27check\x27 AND status IN (\x27queued\x27,\x27failed\x27)").fetchone()[0])' "$W/root/finance/finance.db")
[ "$n" = 0 ] && echo "$o" | grep -q "check messages withdrawn: 1" && ok "A14 undo withdraws check messages still on the road" || { bad "A14"; echo "$o"; }
rm -rf "$W"; echo "rehearse_s909: $P ok, $F red"; [ "$F" = 0 ]
