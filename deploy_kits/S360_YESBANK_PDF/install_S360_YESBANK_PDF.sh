#!/bin/bash
# =============================================================================
#  install_S360_YESBANK_PDF.sh · kit S360_YESBANK_PDF (session 280, Sanjeevni, 21-Sep-2026) · F-603
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S360_YESBANK_PDF/install_S360_YESBANK_PDF.sh
#
#  THE FAULT (F-603): the Yes Bank statement could not be loaded at all. The page's file picker
#  accepted only .csv, so the PDF could not even be chosen, and the CSV the bank gives today has no
#  'Statement Period' line, which the S186 reader requires (F-112) -- so it was refused, every time.
#  Meanwhile the bank holds two cash deposits the books never saw (03-Sep and 15-Sep, Rs 4,00,000).
#
#    /root/finance/finance_yesbank.py   5dcbdd3a (S186 v1.0) -> TO below, FULL FILE (v1.1):
#        reads the statement PDF through pdftotext (text layer only), and PROVES it before storing
#        a row -- every running balance, the printed opening / closing, the printed totals, every
#        date inside the printed period; a CSV without a period is still refused, now with a message
#        that names the rule and points at the PDF; the 'Cheque No/Reference No' column is read;
#        a long digit run in a file name keeps its last four digits only.
#    /root/finance/finance_ui/finance_workbench.html  420f82c2 (S187) -> TO below -- THE PARENT'S
#        FILE, DECLARED: the picker accepts a PDF, the card says which file to give it, the file name
#        is masked in the browser before it is sent, and a refusal is shown in full.
#    finance.db (data repair, backed up first with the sqlite backup API): the rejection flag the
#        owner's 21-Sep attempt left carries the account number from the bank's file name; the long
#        digit run is cut to its last four digits (F-607). Nothing else in the database is touched.
#    clinic-finance RESTARTED -- DECLARED TO THE PARENT. finance_app.py is NOT touched.
# =============================================================================
set -u
KIT="S360_YESBANK_PDF"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s360_walk_$STAMP"
declare -A FROM=( [finance_yesbank.py]=5dcbdd3a41360c96310929083524fc93 [finance_workbench.html]=420f82c2846bc49d0d12ab5040d8c542 )
declare -A TO=( [finance_yesbank.py]=cc55b5f4bae367de3c194808da9dfdbc [finance_workbench.html]=601d5a7765ffd3cf7f413b64b6e41813 )
declare -A LIVE=( [finance_yesbank.py]="$FIN/finance_yesbank.py" [finance_workbench.html]="$FIN/finance_ui/finance_workbench.html" )
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in finance_yesbank.py finance_workbench.html; do [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [1/8] kit $f is not its pin - nothing installed"; exit 1; }; done
say "[1/8] kit gates green"
if [ "$(m5 "${LIVE[finance_yesbank.py]}")" = "${TO[finance_yesbank.py]}" ] && [ "$(m5 "${LIVE[finance_workbench.html]}")" = "${TO[finance_workbench.html]}" ]; then
  say "-- ALREADY INSTALLED"; exit 0; fi
for f in finance_yesbank.py finance_workbench.html; do
  [ "$(m5 "${LIVE[$f]}")" = "${FROM[$f]}" ] || { say "!! [2/8] ${LIVE[$f]} is not its pin ${FROM[$f]:0:8} - nothing installed"; exit 1; }; done
command -v pdftotext >/dev/null 2>&1 || { say "!! [2/8] pdftotext is not on this box (apt install poppler-utils) - nothing installed"; exit 1; }
[ -s "$FIN/finance.db" ] && [ -f "$FIN/finance_app.py" ] || { say "!! [2/8] finance.db or finance_app.py missing - nothing installed"; exit 1; }
say "[2/8] live files at their pins (S186 reader, S187 page); pdftotext present: $(pdftotext -v 2>&1 | head -1)"
mkdir -p "$WALK/kit" "$WALK/app/finance_ui" || exit 1
cp -p finance_yesbank.py finance_workbench.html selftest_s360.py fixtures_s360.py walk_s360.py "$WALK/kit/" || exit 1
( cd "$WALK/kit" && "$SPY" -m py_compile finance_yesbank.py selftest_s360.py fixtures_s360.py walk_s360.py ) \
  || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green with the service's python (on copies in /tmp, never in the kit folder)"
SOUT="$( cd "$WALK/kit" && "$SPY" -B selftest_s360.py "$WALK/kit/finance_yesbank.py" 2>&1 )"
echo "$SOUT" | grep -E 'FAILED|selftest_s360:' | sed 's/^/   /'
echo "$SOUT" | grep -q "^SELFTEST_S360 GREEN" || { say "!! [4/8] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] selftest green: the S186 checks, the PDF reader and its eight deliberate failures, a real PDF through pdftotext"
# the walk: the REAL upload route of the live finance_app.py, with the new reader and page, on a scratch copy of finance.db
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
cp -p "$WALK/kit/finance_yesbank.py" "$WALK/app/finance_yesbank.py" && cp -p "$WALK/kit/finance_workbench.html" "$WALK/app/finance_ui/finance_workbench.html" || exit 1
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [5/8] could not copy the database for the walk - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
src = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); dst = sqlite3.connect(sys.argv[2])
src.backup(dst); dst.close(); src.close()
PYEOF
WOUT="$( cd "$WALK/kit" && "$SPY" -B walk_s360.py --app-dir "$WALK/app" --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | grep -vE '^\s*$' | tail -16 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S360 GREEN" || { say "!! [5/8] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[5/8] walk green: the live app's own upload route took a PDF, refused a period-less CSV by name, refused a broken PDF"
\cp -p "${LIVE[finance_yesbank.py]}" "$FIN/finance_yesbank.py.bak_S360_${FROM[finance_yesbank.py]:0:8}" || exit 1
\cp -p "${LIVE[finance_workbench.html]}" "$FIN/finance_ui/finance_workbench.html.bak_S360_${FROM[finance_workbench.html]:0:8}" || exit 1
"$SPY" - "$FIN/finance.db" "$FIN/finance.db.bak_S360_$STAMP" <<'PYEOF' || { say "!! [6/8] database backup failed - nothing placed"; exit 1; }
import sqlite3, sys
src = sqlite3.connect(sys.argv[1]); dst = sqlite3.connect(sys.argv[2]); src.backup(dst); dst.close(); src.close()
PYEOF
say "[6/8] backups: finance_yesbank.py.bak_S360_5dcbdd3a · finance_workbench.html.bak_S360_420f82c2 · finance.db.bak_S360_$STAMP"
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$FIN/finance_yesbank.py.bak_S360_${FROM[finance_yesbank.py]:0:8}" "${LIVE[finance_yesbank.py]}"
  \cp -p "$FIN/finance_ui/finance_workbench.html.bak_S360_${FROM[finance_workbench.html]:0:8}" "${LIVE[finance_workbench.html]}"
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   finance_yesbank.py $(m5 "${LIVE[finance_yesbank.py]}") · finance_workbench.html $(m5 "${LIVE[finance_workbench.html]}") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
\cp -p finance_yesbank.py "${LIVE[finance_yesbank.py]}" && \cp -p finance_workbench.html "${LIVE[finance_workbench.html]}" || restore
for f in finance_yesbank.py finance_workbench.html; do [ "$(m5 "${LIVE[$f]}")" = "${TO[$f]}" ] || restore; done
say "[7/8] placed; md5 read back = the kit"
# the data repair (F-607): the account number carried in by the bank's file name, cut to its last four digits
"$SPY" - "$FIN/finance.db" <<'PYEOF' | sed 's/^/   /'
import re, sqlite3, sys
con = sqlite3.connect(sys.argv[1]); cut = lambda s: re.sub(r"\d{6,}", lambda m: "x" + m.group(0)[-4:], s or "")
rows = con.execute("SELECT rowid, detail FROM data_flag WHERE code='YESBANK_STATEMENT_REJECTED'").fetchall()
n = 0
for rid, d in rows:
    if d and re.search(r"\d{6,}", d):
        con.execute("UPDATE data_flag SET detail=? WHERE rowid=?", (cut(d), rid)); n += 1
con.commit()
left = sum(1 for _, d in con.execute("SELECT rowid, detail FROM data_flag WHERE code='YESBANK_STATEMENT_REJECTED'") if re.search(r"\d{6,}", d or ""))
print("rejection flags masked: %d of %d; left with a long digit run: %d" % (n, len(rows), left))
PYEOF
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
# F-525 / F-573: the workbench page and the upload route are behind the login gate, so curl proves nothing
# about them; the placed reader is proven by IMPORTING it with the service's python.
IMP="$( cd "$FIN" && "$SPY" -B -c "import finance_yesbank as y; print('reader', y.VERSION, hasattr(y, 'parse_pdf'))" 2>&1 )"
echo "$IMP" | grep -q "reader 1.1 True" || restore
WB=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/workbench)
say "[8/8] clinic-finance up, healthz $HC, the placed reader imports as v1.1 with its PDF path; workbench $WB (302/401 = the login gate, expected)"
md5sum "${LIVE[finance_yesbank.py]}" "${LIVE[finance_workbench.html]}"
say "$KIT: DONE -- the Yes Bank statement PDF now loads at https://followup.dr-manoj.in/finance/workbench (card 'Yes Bank cash deposits')."
