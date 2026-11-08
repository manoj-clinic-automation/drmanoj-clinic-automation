#!/bin/bash
# rehearse_s754.sh -- the installer rehearsed on a MADE-UP root (never the box): assetapp/ (the live bytes: the 08-Nov bundle + S750's two
# files), shared/ (the bundle's), a made-up assets.db the scan app makes itself with nine made-up papers shaped like today's, a made-up
# finance.db, made-up stored files; stubs for systemctl and the health probe; a stub reader on 127.0.0.1 (no paid call, nothing sent out).
#   bash rehearse_s754.sh setup <kit dir> <assetapp dir> <shared dir> <scratch dir>
#   bash rehearse_s754.sh dry   <kit dir> <scratch dir>     # must end '-- DRY RUN ...'; nothing written
#   bash rehearse_s754.sh real  <kit dir> <scratch dir>     # the TO pins placed; the data step DONE; the rows put right
#   bash rehearse_s754.sh again <kit dir> <scratch dir>     # the code step skipped, the data ALREADY DONE
#   bash rehearse_s754.sh red   <kit dir> <scratch dir> <assetapp dir> <shared dir>   # a forced red at [6/7]: the FROM files back, no data step
# Each phase prints 'REHEARSAL S754 <phase>: ok' or 'RED'.
set -u
PHASE="$1"; KIT="$2"
PY="$(command -v python3)"
mkroot() {
  local AST="$1" SHR="$2" W="$3"
  rm -rf "$W/root" "$W/stub" "$W/tmpw" && mkdir -p "$W/root/assetapp/uploads" "$W/root/shared" "$W/root/finance" "$W/root/wa/venv/bin" "$W/root/deploy" "$W/stub" "$W/tmpw" "$W/key"
  cp -p "$AST"/*.py "$W/root/assetapp/"; cp -p "$AST"/*.js "$AST"/*.json "$W/root/assetapp/" 2>/dev/null
  cp -p "$SHR"/*.py "$W/root/shared/"
  ln -sf "$PY" "$W/root/wa/venv/bin/python3"
  echo "made-up-rehearsal-key" > "$W/key/anthropic.key"
  ( cd "$W/root/assetapp" && ASSETS_DB="$W/root/assetapp/assets.db" ASSETS_UPLOADS="$W/root/assetapp/uploads" SHARED_LIB_DIR="$W/root/shared" \
    SCANAPP_ANTHROPIC_KEY_FILE="$W/key/anthropic.key" CLINIC_PORTAL_DIR="$W/noportal" FINANCE_LOCAL_URL="http://127.0.0.1:9" FINANCE_DB_FOR_SCANS="$W/nofin.db" \
    "$PY" -W ignore -B - "$W" <<'EOF'
import json, os, sqlite3, sys
W = sys.argv[1]
import asset_register as ar, claude_reader as CR
d = sqlite3.connect(os.environ["ASSETS_DB"]); CR.ensure(d); ar.S441.ensure(d)
UP = os.environ["ASSETS_UPLOADS"]
SEED = [(291, "B-0291", "clinic", "Consumable", "draft", "SANJEEVNI MEDICOS", 2453, None, None, None, None),
        (292, "B-0292", "clinic", "Consumable", "draft", "DRUG DEALS", 1557, None, None, None, None),
        (293, "B-0293", "clinic", "Consumable", "draft", "A.A.PHARMACEUTICALS", 12818, None, None, None, None),
        (295, "B-0295", "pharmacy", "Summary", "captured", "JANTA PHARMACEUTICALS", 13146, "summary", None, None, None),
        (296, "B-0296", "pharmacy", "Pharmacy", "rejected", None, 3656, None, 295, "page 2 of B-0295 (joined automatically)", "server (S441 forgotten page)"),
        (297, "B-0297", "pharmacy", "Pharmacy", "captured", "MANNAT PHARMA", 24212, None, None, None, None),
        (298, "B-0298", "pharmacy", "Pharmacy", "captured", "GUNINA PHARMACEUTICALS PVT. LTD.", 60682, None, None, None, None),
        (299, "B-0299", "pharmacy", "Pharmacy", "captured", "DEEPAM PHARMA", 32114, None, None, None, None),
        (303, "B-0303", "pharmacy", "Summary", "captured", "SANJEEVNI MEDICOS", 8603, "summary", None, None, None)]
for (i, st, lane, kind, status, vendor, amt, dk, po, rr, ab) in SEED:
    fn = "bill_reh754_%d.pdf" % i
    open(os.path.join(UP, fn), "wb").write(b"%PDF-1.4 made-up rehearsal " + st.encode())
    d.execute("INSERT INTO bills(id, stamp_no, kind, lane, status, vendor, total_amount, doc_kind, page_of, reject_reason, approved_by, submitted_by, submitted_at, "
              "source_stored, ocr_status, bill_month) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (i, st, kind, lane, status, vendor, amt, dk, po, rr, ab, "Alisha", "2026-11-08 15:%02d:00" % (i - 290), fn, "read", "2026-11"))
    d.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)", (i, "2026-11-08 15:00:00", "reh", dk or "bill", "{}"))
    d.execute("INSERT OR REPLACE INTO scan_check_s441(bill_id, verdict, other_id, detail, at) VALUES(?,?,?,?,?)", (i, "page" if i == 296 else "clear", None, "", "2026-11-08 15:30:00"))
open(os.path.join(UP, "bill_reh754_merged.pdf"), "wb").write(b"%PDF-1.4 made-up merged")
d.execute("UPDATE bills SET source_stored='bill_reh754_merged.pdf' WHERE id=295")
d.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(295, '2026-11-08 15:13', 'server (S441)', 's441_page_merged', ?)",
          (json.dumps({"page": 296, "before": "bill_reh754_295.pdf", "after": "bill_reh754_merged.pdf"}),))
d.commit()
f = sqlite3.connect(os.path.join(W, "root", "finance", "finance.db"))
for s in ("CREATE TABLE purchase_scan_link(asset_bill_id INTEGER)", "CREATE TABLE purchase_scan_state(asset_bill_id INTEGER, confirmed_by TEXT, chosen_vendor TEXT, dup_ok INTEGER)",
          "CREATE TABLE s736_decision(asset_bill_id INTEGER)", "CREATE TABLE s749_act(scan INTEGER)", "CREATE TABLE s750_dealer_of(scan INTEGER)"):
    f.execute(s)
f.commit()
EOF
  ) >/dev/null 2>&1
  printf '#!/bin/bash\ncase "$1" in show) echo "";; *) exit 0;; esac\n' > "$W/stub/systemctl"
  printf '#!/bin/bash\ncase "$1" in /healthz) echo 200;; *) echo 302;; esac\n' > "$W/stub/health"
  chmod +x "$W/stub/systemctl" "$W/stub/health"
  [ -f "$W/root/assetapp/assets.db" ] && [ -f "$W/root/finance/finance.db" ]
}
stub_reader() {   # a stub of the Messages API on 127.0.0.1: the summary answer for the summary prompt, an upright answer for the page check
  local W="$1"
  cat > "$W/stub/reader.py" <<'EOF'
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        b = json.loads(self.rfile.read(int(self.headers.get("content-length") or 0)) or b"{}")
        t = b["messages"][0]["content"][-1]["text"]
        if "MONTHLY" in t:
            a = {"is_summary": True, "dealer": "REHEARSAL DEALER", "period_from": None, "period_to": "2026-11-02", "as_on": "2026-11-02", "continued": False,
                 "lines": [{"kind": "bill", "no": "R-1", "date": "2026-10-20", "amount": 999}], "total_bills": 999, "closing": 999, "handwritten": False}
        else:
            a = {"pages": [{"text_top": "top"}], "whole_bill": True, "totals_visible": True, "legible": True, "note": ""}
        out = json.dumps({"content": [{"type": "text", "text": json.dumps(a)}], "stop_reason": "end_turn"}).encode()
        self.send_response(200); self.send_header("content-type", "application/json"); self.send_header("content-length", str(len(out))); self.end_headers(); self.wfile.write(out)
    def log_message(self, *a):
        pass
s = HTTPServer(("127.0.0.1", 0), H)
open(sys.argv[1], "w").write(str(s.server_address[1]))
s.serve_forever()
EOF
  rm -f "$W/stub/port"; "$PY" "$W/stub/reader.py" "$W/stub/port" & echo $! > "$W/stub/pid"
  for _i in 1 2 3 4 5 6 7 8 9 10; do [ -s "$W/stub/port" ] && break; sleep 0.3; done
}
envline() { local W="$1"; echo "ROOT=$W/root APY=$PY VPY=$W/root/wa/venv/bin/python3 FDB=$W/root/finance/finance.db LOCK=$W/root/deploy/.lock HEALTH_CMD=$W/stub/health SYSTEMCTL=$W/stub/systemctl JOURNALCTL=/bin/false TMPW=$W/tmpw TMPDIR=$W/tmpw SKIP_WINDOW=1 NO_PROXY=127.0.0.1,localhost no_proxy=127.0.0.1,localhost SCANAPP_ANTHROPIC_KEY_FILE=$W/key/anthropic.key SCANAPP_ANTHROPIC_URL=http://127.0.0.1:$(cat "$W/stub/port")/v1/messages"; }
rows() { "$PY" - "$1/root/assetapp/assets.db" <<'EOF'
import sqlite3, sys
d = sqlite3.connect(sys.argv[1])
print(" ".join("%d:%s/%s/%s/%s" % r for r in d.execute("SELECT id, lane, kind, status, COALESCE(page_of,'-') FROM bills WHERE id>=291 ORDER BY id")))
EOF
}
case "$PHASE" in
setup)
  AST="$3"; SHR="$4"; W="$5"
  mkroot "$AST" "$SHR" "$W" && echo "REHEARSAL S754 setup: ok ($W/root: assetapp $(ls "$W/root/assetapp" | wc -l) files, nine made-up papers)" || { echo "REHEARSAL S754 setup: RED"; exit 1; }
  ;;
dry|real|again)
  W="$3"; ok=1; stub_reader "$W"
  case "$PHASE" in
  dry)
    B="$(rows "$W")"
    env $(envline "$W") DRY=1 bash "$KIT/install_S754_SUMMARY_RECOGNISE.sh" > "$W/reh_dry.txt" 2>&1
    grep -q -- "-- DRY RUN: every gate" "$W/reh_dry.txt" || { ok=0; grep -E '!!|FAIL|REFUSED' "$W/reh_dry.txt" | head -8; }
    [ "$(rows "$W")" = "$B" ] || { ok=0; echo "   !! the DRY run changed a row"; }
    ls "$W/root/assetapp" | grep -q bak_S754 && { ok=0; echo "   !! the DRY run made a backup"; }
    ;;
  real)
    env $(envline "$W") bash "$KIT/install_S754_SUMMARY_RECOGNISE.sh" > "$W/reh_real.txt" 2>&1
    grep -q "S754_SUMMARY_RECOGNISE: DONE" "$W/reh_real.txt" || { ok=0; grep -E '!!|FAIL|REFUSED|still to do' "$W/reh_real.txt" | head -8; }
    for f in assetapp/asset_register.py assetapp/claude_reader.py shared/scan_checks_s441.py; do
      want="$(awk -v f="$f" '$2==f{print $1}' "$KIT/TO_PINS.md5")"; have="$(md5sum "$W/root/$f" | awk '{print $1}')"
      [ "$want" = "$have" ] || { ok=0; echo "   !! after the real run $f is ${have:0:8}, not the TO ${want:0:8}"; }
    done
    R="$(rows "$W")"; echo "   rows: $R"
    [ "$R" = "291:pharmacy/Summary/captured/- 292:pharmacy/Summary/captured/- 293:pharmacy/Summary/captured/- 295:pharmacy/Summary/captured/- 296:pharmacy/Summary/captured/- 297:pharmacy/Summary/captured/- 298:pharmacy/Summary/captured/- 299:pharmacy/Summary/captured/- 303:pharmacy/Summary/captured/-" ] || { ok=0; echo "   !! the rows are not as the data step should leave them"; }
    ls "$W/root/assetapp" | grep -q "assets.db.bak_S754_" || { ok=0; echo "   !! no backup of assets.db"; }
    ;;
  again)
    env $(envline "$W") bash "$KIT/install_S754_SUMMARY_RECOGNISE.sh" > "$W/reh_again.txt" 2>&1
    grep -q "already the kit's" "$W/reh_again.txt" && grep -q "now: ALREADY DONE" "$W/reh_again.txt" && grep -q "S754_SUMMARY_RECOGNISE: DONE" "$W/reh_again.txt" || { ok=0; tail -4 "$W/reh_again.txt"; }
    ;;
  esac
  kill "$(cat "$W/stub/pid")" 2>/dev/null
  [ "$ok" = 1 ] && echo "REHEARSAL S754 $PHASE: ok" || { echo "REHEARSAL S754 $PHASE: RED"; exit 1; }
  ;;
red)
  W="$3"; AST="$4"; SHR="$5"; ok=1
  mkroot "$AST" "$SHR" "$W" || { echo "REHEARSAL S754 red: RED (setup)"; exit 1; }
  stub_reader "$W"
  B="$(rows "$W")"
  env $(envline "$W") REHEARSE_RED_AT=6 bash "$KIT/install_S754_SUMMARY_RECOGNISE.sh" > "$W/reh_red.txt" 2>&1
  grep -q "RED after placing" "$W/reh_red.txt" || { ok=0; tail -4 "$W/reh_red.txt"; }
  for f in assetapp/asset_register.py assetapp/claude_reader.py shared/scan_checks_s441.py; do
    have="$(md5sum "$W/root/$f" | awk '{print $1}')"; want="$(md5sum "$( [ "${f%%/*}" = assetapp ] && echo "$AST" || echo "$SHR")/$(basename "$f")" | awk '{print $1}')"
    [ "$want" = "$have" ] || { ok=0; echo "   !! after the red $f is ${have:0:8}, not the FROM ${want:0:8}"; }
  done
  [ "$(rows "$W")" = "$B" ] || { ok=0; echo "   !! the data step ran after a red"; }
  kill "$(cat "$W/stub/pid")" 2>/dev/null
  [ "$ok" = 1 ] && echo "REHEARSAL S754 red: ok (the FROM files back, no row changed)" || { echo "REHEARSAL S754 red: RED"; exit 1; }
  ;;
esac
