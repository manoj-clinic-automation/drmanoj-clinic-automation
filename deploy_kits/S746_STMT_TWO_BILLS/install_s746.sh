#!/bin/bash
# install_s746.sh -- S746_STMT_TWO_BILLS (board _numbers v1031 -> v1032; the Scan App chat, session 398, 07-Nov-2026; D845 (4) part A,
#   the owner's FINAL 07:49 IST on the mock-up https://claude.ai/artifact/TnmxQxuSGQ48ggNVrPgBfQ; two bills, NK pays its own -- 07:40;
#   an estimate paid stays out of the accountants' packs -- 07:47). The Stationery page's monthly statement holds two bills, the
#   Clinic's and NK Pathology's, each joined with its own side's rates and paid on its own; NK's paper sits on the NK Pathology lane
#   (the join moves it there, audited) and so reaches NK's accountants' pack 8.1 by itself. ONE file: /root/assetapp/stationery.py
#   (S743's TO) -> TO, rebuilt on the box by make_s746.py (15 counted edits) and checked against the kit's whole file. Five additive
#   columns on stationery_stmt (nk_*): the module's own ensure adds them at mount; the installer checks them after the restart and,
#   only if a locked database kept them out, adds them itself after a backup of the database. Restarts assetapp only.
# Run as root on the VPS: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S746_STMT_TWO_BILLS/install_s746.sh
set -u
KIT="S746_STMT_TWO_BILLS"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP="${S746_APP_DIR:-/root/assetapp}"
SERVICE="${S746_SERVICE:-assetapp}"
HEALTH="${S746_HEALTH_URL:-http://127.0.0.1:8030/healthz}"
PY="${S746_PYTHON:-python3}"
RESTART="${S746_RESTART_CMD:-systemctl restart $SERVICE}"
LOCK="${S746_LOCK:-/root/deploy/.claude_code_build.lock}"
HOSTPAT="${S746_HOST:-srv1746119}"
REH="${S746_REHEARSAL:-}"
if [ -z "${S746_DB:-}" ]; then
  SVC_ENV="$(systemctl show "$SERVICE" -p Environment --value 2>/dev/null || true)"
  DB0="$(printf '%s' "$SVC_ENV" | tr ' ' '\n' | sed -n 's/^ASSETS_DB=//p' | head -1)"
  unset SVC_ENV
fi
DB="${S746_DB:-${DB0:-$APP/assets.db}}"
TRIES="${S746_HEALTH_TRIES:-20}"
FILES="stationery.py"
READONLY="asset_register.py clinic_papers.py asset_machine.py procroom.py batteries.py xray_costs.py claude_reader.py claude_reread.py sorting_desk.py"
STEP=0; log(){ STEP=$((STEP+1)); echo "[$STEP] $*"; }
die(){ echo "REFUSED: $*"; echo "$KIT: NOT INSTALLED (nothing was placed)"; exit 1; }
md5(){ md5sum "$1" | cut -c1-32; }
pin(){ tr -d ' \r\n' < "$HERE/$1" 2>/dev/null; }
base(){ echo "${1%.py}"; }
HAVE_LOCK=0; WORK=""
cleanup(){ [ -n "$WORK" ] && rm -rf "$WORK"; for f in $FILES; do rm -f "$APP/$f.s746tmp"; done; [ "$HAVE_LOCK" = 1 ] && { rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; }; }
trap cleanup EXIT
hc(){ if [ -n "${S746_FAKE_HEALTH:-}" ]; then echo "$S746_FAKE_HEALTH"; else curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$1" 2>/dev/null || true; fi; }

log "gates (the box, root, the kit, the files)"
case "$(hostname)" in *$HOSTPAT*) ;; *) die "this is not $HOSTPAT";; esac
[ -n "$REH" ] || [ "$(id -u)" = "0" ] || die "run as root"
for k in make_s746.py edits_s746.py walk_s746_app.py stationery.py KIT_ID.txt; do [ -f "$HERE/$k" ] || die "kit file $k missing"; done
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; T="$(pin PIN_TO_$(base $f).txt)"
  [ ${#FR} -eq 32 ] && [ ${#T} -eq 32 ] || die "the kit's pins for $f are missing"
  [ "$(md5 "$HERE/$f")" = "$T" ] || die "the kit's $f is not at its TO pin"
  [ -f "$APP/$f" ] || die "$APP/$f missing"; done
for f in $READONLY; do v="$(pin PIN_READ_$(base $f).txt)"; [ ${#v} -eq 32 ] || die "PIN_READ_$(base $f).txt is missing in the kit"; [ -f "$APP/$f" ] || die "$APP/$f missing"; done
[ -f "$DB" ] || die "no database at the service's path"
command -v "$PY" >/dev/null || die "no $PY"; "$PY" -c "import flask" 2>/dev/null || die "$PY has no flask"
echo "    the kit and $APP ok"

log "the server-wide build lock (one build at a time on the shared server)"
mkdir -p "$(dirname "$LOCK")"
if mkdir "$LOCK" 2>/dev/null; then HAVE_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; else
  die "another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) -- paste the line again when it is free"; fi
echo "    the build lock is ours"

log "pins -- the live bytes"
NTO=0
for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] && NTO=$((NTO+1)); done
if [ "$NTO" = 1 ]; then echo "$KIT: ALREADY INSTALLED (the file at the kit's TO pin)"; exit 0; fi
for f in $FILES; do L="$(md5 "$APP/$f")"; FR="$(pin PIN_FROM_$(base $f).txt)"
  [ "$L" = "$FR" ] || die "$f is ${L:0:8}, not the pinned ${FR:0:8} -- another kit moved it; S746 is to be rebuilt on the new bytes"
  echo "    $f ${L:0:8} = the FROM pin"; done
for f in $READONLY; do L="$(md5 "$APP/$f")"; P="$(pin PIN_READ_$(base $f).txt)"
  [ "$L" = "$P" ] || die "$f is ${L:0:8}, not the pinned ${P:0:8} (read only for this kit) -- stop and re-check"
  echo "    $f ${L:0:8} = the pin (read only)"; done

WORK="$(mktemp -d /tmp/s746work.XXXXXX)" || die "no scratch folder"; chmod 700 "$WORK"
mkdir -p "$WORK/from" "$WORK/to"
for f in $FILES; do cp -p "$APP/$f" "$WORK/from/$f"; done

log "the kit's file rebuilt on the pinned FROM bytes, equal to the kit's TO"
"$PY" -B "$HERE/make_s746.py" "$WORK/from/stationery.py" "$WORK/to/stationery.py" --expect | sed 's/^/    /'
for f in $FILES; do [ "$(md5 "$WORK/to/$f" 2>/dev/null)" = "$(pin PIN_TO_$(base $f).txt)" ] || die "the rebuilt $f is not its TO pin"; done
echo "    the TO file = its pin and compiles"

log "the walk on the REAL app (every part it mounts, from a scratch folder) on a COPY of the live database -- made-up rows only"
"$PY" -B "$HERE/walk_s746_app.py" --live "$APP" --files "$WORK/to" --db "$DB" > "$WORK/wapp.txt" 2>&1; WA=$?
sed 's/^/    /' "$WORK/wapp.txt" | cut -c1-170
[ "$WA" = 0 ] || die "the walk on the real app is not all green"
"$PY" -B "$HERE/walk_s746_app.py" --live "$APP" --files "$WORK/from" --db "$DB" --expect-red > "$WORK/capp.txt" 2>&1 || { sed 's/^/    /' "$WORK/capp.txt" | cut -c1-170; die "the control on the live files is not red where it must be"; }
echo "    $(tail -1 "$WORK/capp.txt")"

if [ -n "${DRY:-}" ]; then echo "$KIT: DRY RUN -- stopped before the backup; nothing placed"; exit 0; fi

log "the backup beside the live file"
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f" "$APP/$f.bak_S746_${FR:0:8}" || die "backup of $f failed"; echo "    $f.bak_S746_${FR:0:8}"; done

restore(){
  echo "RESTORING the file from its backup"
  for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; cp -p "$APP/$f.bak_S746_${FR:0:8}" "$APP/$f"; done
  $RESTART >/dev/null 2>&1
  RH=""; for i in $(seq 1 "$TRIES"); do sleep "${S746_SLEEP:-2}"; RH="$(hc "$HEALTH")"; [ "$RH" = "200" ] && break; done
  BACK=0; for f in $FILES; do [ "$(md5 "$APP/$f")" = "$(pin PIN_FROM_$(base $f).txt)" ] && BACK=$((BACK+1)); done
  echo "    the file back: $BACK of 1 · healthz $RH after the restore"
  [ "$BACK" = 1 ] && echo "$KIT: NOT INSTALLED (restored)" || echo "$KIT: NOT INSTALLED -- AND THE RESTORE IS INCOMPLETE: the .bak_S746_ files in $APP are the way back"
  exit 1
}

log "the five NK-bill columns on stationery_stmt and any statement billed before S746 -- BEFORE the new file is placed (the old code ignores them)"
if true; then                                                      # in the rehearsal too (its made-up database has no statement table)
  "$PY" - "$DB" > "$WORK/cols.txt" 2>&1 <<'PYCOLS'
import sqlite3, sys, time
db = sys.argv[1]
want = (("nk_bill_id", "INTEGER"), ("nk_bill_created_at", "TEXT NOT NULL DEFAULT ''"), ("nk_billed_at", "TEXT NOT NULL DEFAULT ''"),
        ("nk_paid_at", "TEXT NOT NULL DEFAULT ''"), ("nk_paid_ref", "TEXT NOT NULL DEFAULT ''"))
con = sqlite3.connect(db, timeout=30)
have = {r[1] for r in con.execute("PRAGMA table_info(stationery_stmt)")}
miss = [w for w in want if w[0] not in have]
if not have:
    print("stationery_stmt not there -- the app makes it at its start; nothing to add")
elif not miss:
    print("all five present")
else:
    bak = db + ".bak_S746_" + time.strftime("%Y%m%d_%H%M%S")
    dst = sqlite3.connect(bak)
    con.backup(dst)
    dst.close()
    for c, spec in miss:
        con.execute("ALTER TABLE stationery_stmt ADD COLUMN %s %s" % (c, spec))
    con.commit()
    print("added %d (the database backed up first: %s)" % (len(miss), bak))
if have:                                                             # a statement billed before S746: ONE bill covered both sides
    leg = [r[0] for r in con.execute("SELECT s.id FROM stationery_stmt s WHERE s.bill_id IS NOT NULL AND s.nk_bill_id IS NULL "
                                       "AND COALESCE(s.voided_at,'')='' AND EXISTS (SELECT 1 FROM stationery_line l WHERE l.stmt_id=s.id "
                                       "AND l.side='nk' AND COALESCE(l.voided_at,'')='')")]
    if leg:
        bak2 = db + ".bak_S746_legacy_" + time.strftime("%Y%m%d_%H%M%S")
        dst = sqlite3.connect(bak2)
        con.backup(dst)
        dst.close()
        con.execute("UPDATE stationery_stmt SET nk_bill_id=bill_id, nk_bill_created_at=bill_created_at, nk_billed_at=billed_at, "
                    "nk_paid_at=paid_at, nk_paid_ref=paid_ref WHERE id IN (%s)" % ",".join("?" * len(leg)), leg)
        con.commit()
        print("%d statement(s) billed before S746 with one bill for both sides: their NK lines read that same bill and payment "
              "(the database backed up first: %s)" % (len(leg), bak2))
    else:
        print("no statement billed before S746 with NK lines -- nothing to carry over")
con.close()
PYCOLS
  RC=$?; sed 's/^/    /' "$WORK/cols.txt"; [ "$RC" = 0 ] || die "the columns / carry-over step failed -- the new file was NOT placed"
fi

log "place (through a temporary file) and read back"
for f in $FILES; do cp -p "$WORK/to/$f" "$APP/$f.s746tmp" && mv -f "$APP/$f.s746tmp" "$APP/$f" || restore
  [ "$(md5 "$APP/$f")" = "$(pin PIN_TO_$(base $f).txt)" ] || restore
  echo "    $f $(md5 "$APP/$f" | cut -c1-8) = the TO pin"; done

log "restart $SERVICE only, then its health and the desk"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
$RESTART || restore
HC=""; for i in $(seq 1 "$TRIES"); do sleep "${S746_SLEEP:-2}"; HC="$(hc "$HEALTH")"; [ "$HC" = "200" ] && break; done
[ "$HC" = "200" ] || { echo "    healthz answered ${HC:-nothing}"; restore; }
echo "    healthz 200"
X=""; for i in $(seq 1 "$TRIES"); do X="$(hc "${HEALTH%/healthz}/desk")"; [ -n "${S746_FAKE_HEALTH:-}" ] && X=302; [ "$X" = "302" ] && break; sleep "${S746_SLEEP:-2}"; done
[ "$X" = "302" ] || { echo "    /desk answered ${X:-nothing}, not 302"; restore; }
echo "    /desk 302 (the login door: mounted)"
if [ -z "$REH" ]; then
  NM="$(journalctl -u "$SERVICE" --since "$T0" --no-pager 2>/dev/null | grep -cE 'NOT mounted|NOT wrapped')"
  [ "${NM:-0}" = 0 ] || { echo "    the scan app's log says a part is NOT mounted / NOT wrapped since the restart"; restore; }
  echo "    no part reported NOT mounted since the restart"
fi

echo

echo
echo "WHAT THE STATIONERY PAGE NOW SHOWS (your login):"
echo "  - Section 5, Monthly statement: two boxes -- the Clinic's bill and NK Pathology's bill. Each joins Variety's bill for that side"
echo "    with its own lines' rates, and is marked paid on its own; NK's says 'paid by NK'. NK's bill is put on the NK Pathology lane,"
echo "    so it goes into NK's accountants' pack (8.1) by itself. The statement reads paid once both are paid."
echo "  - Section 2, the NK ledger: each NK line shows its own bill's state (on statement / billed / paid)."
echo "  - An estimate given instead of a bill is joined and paid the same way; it does not go to an accountants' pack (your rule)."
echo "UNDO (puts the file back and restarts the scan app):"
for f in $FILES; do FR="$(pin PIN_FROM_$(base $f).txt)"; echo "  \\cp $APP/$f.bak_S746_${FR:0:8} $APP/$f"; done
echo "  systemctl restart $SERVICE"
echo "$KIT: DONE"
