#!/bin/bash
# rehearse_s826.sh <kit dir> <assetapp dir> <shared dir> <scratch dir> [python] -- the installer rehearsed on a MADE-UP root (never the box):
# the live bytes of assetapp/ and shared/, stubs for systemctl and the health probe, a lock inside the scratch. Five runs:
# dry (nothing written) . real (the TO pins placed) . again (ALREADY) . red at [5/6] (the FROM files back) . a changed live file (stopped).
set -u
KIT="$1"; AST="$2"; SHR="$3"; W="$4"; PY="${5:-$(command -v python3)}"; N=0; BAD=0
mk() { rm -rf "$W/root" "$W/stub" "$W/tmpw"; mkdir -p "$W/root/assetapp" "$W/root/shared" "$W/root/deploy" "$W/stub" "$W/tmpw"
  cp -p "$AST"/*.py "$AST"/*.js "$W/root/assetapp/" 2>/dev/null; cp -p "$SHR"/*.py "$W/root/shared/"
  printf '#!/bin/bash\nexit 0\n' > "$W/stub/systemctl"; printf '#!/bin/bash\ncase "$1" in /healthz) echo 200;; *) echo 302;; esac\n' > "$W/stub/health"
  chmod +x "$W/stub/systemctl" "$W/stub/health"; }
run() { (cd /tmp && env ROOT="$W/root" APY="$PY" LOCK="$W/root/deploy/.lock" SYSTEMCTL="$W/stub/systemctl" JOURNALCTL=none HEALTH_CMD="$W/stub/health" NAP=0 TMPW="$W/tmpw" "$@" bash "$KIT/install_S826_TWIN_AMOUNT_RESTORE.sh" 2>&1); }
pin() { md5sum "$W/root/$1" | cut -c1-8; }
ck() { N=$((N+1)); if eval "$2"; then echo "  ok   $1"; else echo "  RED  $1"; BAD=$((BAD+1)); fi; }
mk; O=$(run DRY=1); ck "dry: ends DRY RUN, nothing written" '[[ "$O" == *"-- DRY RUN: every gate"* ]] && [ "$(pin shared/scan_checks_s441.py)" = 59d5cb1c ] && [ "$(pin assetapp/asset_register.py)" = 74043cdb ] && ! ls "$W/root/shared/"*.bak_S826_* >/dev/null 2>&1'
O=$(run); ck "real: DONE, both files at the TO pins, backups beside them" '[[ "$O" == *"S826_TWIN_AMOUNT_RESTORE: DONE."* ]] && [ "$(pin shared/scan_checks_s441.py)" = 5c934bdb ] && [ "$(pin assetapp/asset_register.py)" = 63eba920 ] && [ -f "$W/root/shared/scan_checks_s441.py.bak_S826_59d5cb1c" ] && [ -f "$W/root/assetapp/asset_register.py.bak_S826_74043cdb" ] && [ ! -d "$W/root/deploy/.lock" ]'
UNDO=$(printf '%s\n' "$O" | sed -n 's/^\[6\/6\] undo (one line): //p')
O=$(run); ck "again: ALREADY INSTALLED" '[[ "$O" == *"ALREADY INSTALLED"* ]]'
(eval "${UNDO//systemctl/true}") >/dev/null 2>&1; ck "the printed undo line puts the FROM bytes back" '[ "$(pin shared/scan_checks_s441.py)" = 59d5cb1c ] && [ "$(pin assetapp/asset_register.py)" = 74043cdb ]'
mk; O=$(run REHEARSE_RED_AT=5); ck "red at [5/6]: both FROM files back, the lock released" '[[ "$O" == *"RED after placing"* ]] && [ "$(pin shared/scan_checks_s441.py)" = 59d5cb1c ] && [ "$(pin assetapp/asset_register.py)" = 74043cdb ] && [ ! -d "$W/root/deploy/.lock" ]'
mk; O=$(run REHEARSE_RED_AT=4); ck "red at [4/6]: both FROM files back" '[[ "$O" == *"RED after placing"* ]] && [ "$(pin shared/scan_checks_s441.py)" = 59d5cb1c ] && [ "$(pin assetapp/asset_register.py)" = 74043cdb ]'
mk; echo "# changed" >> "$W/root/assetapp/asset_register.py"; O=$(run); ck "a live file not at its FROM pin: stopped, nothing placed" '[[ "$O" == *"it changed after this kit was built: STOP"* ]] && [ "$(pin shared/scan_checks_s441.py)" = 59d5cb1c ] && [ ! -d "$W/root/deploy/.lock" ]'
mk; mkdir -p "$W/root/deploy/.lock"; O=$(run); ck "another build holds the lock: nothing installed" '[[ "$O" == *"another build holds the lock"* ]] && [ "$(pin assetapp/asset_register.py)" = 74043cdb ]'
rm -rf "$W/root" "$W/stub" "$W/tmpw"
echo "REHEARSAL S826: $((N-BAD)) of $N ok"
