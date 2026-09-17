#!/bin/bash
# install_S294_DARPAN_RECONCILED.sh -- Darpan's list comes only after reconciliation, and
# carries only the count-day figures: Shelf counted | Marg stock | Difference.
# Three files, patched ON THE BOX from their exact live bytes:
#   /root/finance/stock_app.py     (which lines may go on the list; no list while a swap waits)
#   /root/finance/pad_receipt.py   (the list's columns and header line; no paragraph)
#   /root/finance/stock_desk.html  (footer links: "your copy (not for Darpan)" + "Darpan's list")
# No table, no route, no data. clinic-finance is restarted.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S294_DARPAN_RECONCILED/install_S294_DARPAN_RECONCILED.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
SA_FROM="8615d64dbeda516e6efb6f025ec777b3"; SA_TO="bb7df8d78b0f1ff8cfd86a5c260f301c"
PR_FROM="a224e7b406dc2133048d9bff1523bc42"; PR_TO="239a81fb7f637663092424c20974ca01"
DK_FROM="6b6636bfbcec022169532042ba6b7d53"; DK_TO="aac7f96c73f879dba557310d207d064f"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S294_DARPAN_RECONCILED installer =="; echo "python : $PY"
for f in stock_app.py pad_receipt.py stock_desk.html; do [ -f "$FIN/$f" ] || { echo "REFUSED: $FIN/$f not found"; exit 1; }; done
SA="$(md5of "$FIN/stock_app.py")"; PR="$(md5of "$FIN/pad_receipt.py")"; DK="$(md5of "$FIN/stock_desk.html")"
echo "stock_app.py    : from $SA_FROM -> to $SA_TO ; live $SA"
echo "pad_receipt.py  : from $PR_FROM -> to $PR_TO ; live $PR"
echo "stock_desk.html : from $DK_FROM -> to $DK_TO ; live $DK"
if [ "$SA" = "$SA_TO" ] && [ "$PR" = "$PR_TO" ] && [ "$DK" = "$DK_TO" ]; then echo "ALREADY INSTALLED (all three live md5s == to-pins)."; exit 0; fi
[ "$SA" = "$SA_FROM" ] || { echo "REFUSED: stock_app.py is $SA, expected $SA_FROM"; exit 1; }
[ "$PR" = "$PR_FROM" ] || { echo "REFUSED: pad_receipt.py is $PR, expected $PR_FROM"; exit 1; }
[ "$DK" = "$DK_FROM" ] || { echo "REFUSED: stock_desk.html is $DK, expected $DK_FROM"; exit 1; }

BSA="$FIN/stock_app.py.bak_S294_${SA_FROM:0:8}"; BPR="$FIN/pad_receipt.py.bak_S294_${PR_FROM:0:8}"; BDK="$FIN/stock_desk.html.bak_S294_${DK_FROM:0:8}"
\cp -p "$FIN/stock_app.py" "$BSA"; \cp -p "$FIN/pad_receipt.py" "$BPR"; \cp -p "$FIN/stock_desk.html" "$BDK"
echo "backup : $BSA"; echo "backup : $BPR"; echo "backup : $BDK"
restore() { echo "!! restoring all three files byte-identically"
  \cp -p "$BSA" "$FIN/stock_app.py"; \cp -p "$BPR" "$FIN/pad_receipt.py"; \cp -p "$BDK" "$FIN/stock_desk.html"
  rm -f "$FIN"/stock_app.py.S294new* "$FIN"/pad_receipt.py.S294new* "$FIN"/stock_desk.html.S294new*
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/stock_app.py" "$FIN/pad_receipt.py" "$FIN/stock_desk.html"; exit 1; }

\cp -p "$FIN/stock_app.py" "$FIN/stock_app.py.S294new"; \cp -p "$FIN/pad_receipt.py" "$FIN/pad_receipt.py.S294new"; \cp -p "$FIN/stock_desk.html" "$FIN/stock_desk.html.S294new"
"$PY" -B "$KIT_DIR/patch_darpan_reconciled_s294.py" --app "$FIN/stock_app.py.S294new" --receipt "$FIN/pad_receipt.py.S294new" --desk "$FIN/stock_desk.html.S294new" \
      --app-from "$SA_FROM" --receipt-from "$PR_FROM" --desk-from "$DK_FROM" || restore
[ "$(md5of "$FIN/stock_app.py.S294new")" = "$SA_TO" ] || { echo "!! stock_app.py patched to an unpredicted md5"; restore; }
[ "$(md5of "$FIN/pad_receipt.py.S294new")" = "$PR_TO" ] || { echo "!! pad_receipt.py patched to an unpredicted md5"; restore; }
[ "$(md5of "$FIN/stock_desk.html.S294new")" = "$DK_TO" ] || { echo "!! stock_desk.html patched to an unpredicted md5"; restore; }
"$PY" -m py_compile "$FIN/stock_app.py.S294new" "$FIN/pad_receipt.py.S294new" || restore; echo "smoke  : py_compile OK"
mv "$FIN/stock_app.py.S294new" "$FIN/stock_app.py" || restore
mv "$FIN/pad_receipt.py.S294new" "$FIN/pad_receipt.py" || restore
mv "$FIN/stock_desk.html.S294new" "$FIN/stock_desk.html" || restore
rm -f "$FIN"/*.S294new.bak_S294_* 2>/dev/null || true
( cd "$FIN" && "$PY" -B -c "import pad_receipt as P; d=dict(count_id=1, day='06-09-2026', reasons=[(1,'count error','')], tranche=dict(no=1,kind='med',issued_text='x'), rows=[dict(item='TEST',packing='1*10',pack=10,marg=20,counted=12,diff=-8)]); b=P.render_tranche(d); assert b[:5]==b'%PDF-' and len(b)>800; print('smoke  : a test list renders (%d bytes)' % len(b))" ) || restore

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  echo "service: clinic-finance active after restart"
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/stock/page/desk || true)
  echo "page   : HTTP $code (302/401 = the login gate, as before)"
fi
echo "md5sum of the installed files:"; md5sum "$FIN/stock_app.py" "$FIN/pad_receipt.py" "$FIN/stock_desk.html"
echo "S294_DARPAN_RECONCILED: DONE"
echo "read next: https://followup.dr-manoj.in/finance/stock/page/desk?count=1"
