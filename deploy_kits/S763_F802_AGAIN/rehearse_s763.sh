#!/bin/bash
# rehearse_s763.sh -- kit S763's installer rehearsed on a MADE-UP root (never /root, never the box's finance.db):
#   bash rehearse_s763.sh <a root holding finance/ and marg_ingest/ code (the nightly bundle's root/)>
# Six runs: DRY (nothing written) · a changed live file (STOP at [2/7]) · the map not pulled (STOP at [2/7]) · INSTALL · ALREADY INSTALLED ·
# a forced red at [7/7] after a fresh root (the three files put back). The last line: 'REHEARSAL S763: 6 of 6 as expected'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$1"
PY="${PY:-python3}"
W="$(mktemp -d /tmp/s763reh_XXXX)"
OKN=0
mkfake() {
  rm -rf "$W/root" && mkdir -p "$W/root" "$W/repo" "$W/bin"
  for d in finance finance/spine finance/finance_ui marg_ingest marg_ingest/lib shared; do [ -d "$SRC/$d" ] && mkdir -p "$W/root/$d" && cp -p "$SRC/$d"/*.* "$W/root/$d/" 2>/dev/null; done
  "$PY" - "$W/root" <<'E'
import sqlite3, sys
sys.path.insert(0, sys.argv[1] + "/marg_ingest")
import marg_take as MT
con = MT._connect(sys.argv[1] + "/finance/finance.db")
con.execute("INSERT OR REPLACE INTO mi_file (md5,type,verdict,stamp,received_at) VALUES (?,?,?,?,?)",
            ("a" * 32, "SALT_WISE_ITEM_LIST", "VERIFIED", "20261108-092800", "2026-11-08T09:28:00+05:30"))
con.execute("CREATE TABLE IF NOT EXISTS purchase_salt_task (id INTEGER PRIMARY KEY, done INTEGER, done_at TEXT)")
con.execute("INSERT INTO purchase_salt_task (done, done_at) VALUES (1, '2026-11-09T10:00:00+05:30')")
con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
con.commit()
E
  printf '#!/bin/bash\ncase "$1" in show) echo 0;; *) exit 0;; esac\n' > "$W/bin/systemctl"; chmod +x "$W/bin/systemctl"
  printf '#!/bin/bash\ncase "$1" in */marg-file) echo 401;; *) echo 200;; esac\n' > "$W/bin/health"; chmod +x "$W/bin/health"
}
run() {   # $1 = what is expected (a grep pattern on the output), the rest = env
  local want="$1"; shift
  local out
  out="$(env ROOT="$W/root" DB="$W/root/finance/finance.db" REPOMAP="$W/repo/DUTY_MAP.json" LOCK="$W/lock" APY="$(command -v "$PY")" VPY="$(command -v "$PY")" \
         SYSTEMCTL="$W/bin/systemctl" JOURNALCTL=none-here HEALTH_CMD="$W/bin/health" SKIP_WINDOW=1 REHEARSE_EARLIER=none TMPW="$W" "$@" \
         bash "$KDIR/install_S763_F802_AGAIN.sh" 2>&1)"
  if printf '%s\n' "$out" | grep -q -E "$want"; then OKN=$((OKN+1)); echo "  as expected: $want"; else echo "  NOT as expected ($want):"; printf '%s\n' "$out" | tail -8 | sed 's/^/      /'; fi
  printf '%s\n' "$out" > "$W/last.txt"
}
m5() { md5sum "$1" | awk '{print $1}'; }

mkfake; cp "$KDIR/from/DUTY_MAP.json" "$W/repo/DUTY_MAP.json"
B0="$(m5 "$W/root/finance/finance.db")"
run '^-- DRY RUN: every gate' DRY=1
[ "$(m5 "$W/root/finance/finance.db")" = "$B0" ] && [ ! -e "$W/root/finance/marg_door.py.bak_S763_565ad9c8" ] && echo "  ... and the DRY wrote nothing (the db's bytes the same, no backup)" || { echo "  !! the DRY wrote something"; OKN=$((OKN-1)); }
echo "# changed" >> "$W/root/finance/reports_tile.py"
run 'reports_tile.py is .*expected f44fe768.* STOP' DRY=1
mkfake; cp "$KDIR/from/DUTY_MAP.json" "$W/repo/DUTY_MAP.json"
run 'the publish has not reached this box: STOP'
cp "$KDIR/to/DUTY_MAP.json" "$W/repo/DUTY_MAP.json"
run 'S763_F802_AGAIN: DONE \(the server half\)'
run '^-- ALREADY INSTALLED'
mkfake; cp "$KDIR/to/DUTY_MAP.json" "$W/repo/DUTY_MAP.json"
run 'RED after placing \(the walk on the placed files: rehearsal: a forced red at \[7/7\]\)' REHEARSE_RED_AT=7
for f in marg_door.py amir_day.py reports_tile.py; do echo "      after the forced red: $f $(m5 "$W/root/finance/$f" | cut -c1-8)"; done
[ "$(m5 "$W/root/finance/marg_door.py")" = 565ad9c811ecb74a29340abd73c26f12 ] || { echo "  !! marg_door was not put back"; OKN=$((OKN-1)); }
[ -d "$W/lock" ] && { echo "  !! the lock was left behind"; OKN=$((OKN-1)); }
[ "${KEEPW:-0}" = 1 ] || rm -rf "$W"
echo "REHEARSAL S763: $OKN of 6 as expected"
[ "$OKN" = 6 ]
