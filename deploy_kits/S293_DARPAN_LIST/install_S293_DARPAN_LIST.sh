#!/bin/bash
# install_S293_DARPAN_LIST.sh -- Darpan's paper list asks for the REASON against the
# count-day figures (Marg given just before the count | shelf counted | difference),
# not for a recount. Two files, patched ON THE BOX from their exact live bytes:
#   /root/finance/pad_receipt.py   (the list's columns, header, instruction, footer)
#   /root/finance/stock_amir.html  (one label: "Note / recount" -> "Note")
# No table, no route, no data. clinic-finance is restarted (pad_receipt is imported).
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S293_DARPAN_LIST/install_S293_DARPAN_LIST.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PR_FROM="49ced28771a84f02f6276bbbe297443c"; PR_TO="a224e7b406dc2133048d9bff1523bc42"
AM_FROM="adf206b54cc55e88626089a7f3482fd0"; AM_TO="32aa7d45fc93f19d4526a5bca3a3743a"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S293_DARPAN_LIST installer =="; echo "python : $PY"
for f in pad_receipt.py stock_amir.html; do [ -f "$FIN/$f" ] || { echo "REFUSED: $FIN/$f not found"; exit 1; }; done
PR="$(md5of "$FIN/pad_receipt.py")"; AM="$(md5of "$FIN/stock_amir.html")"
echo "pad_receipt.py  : from $PR_FROM -> to $PR_TO ; live $PR"
echo "stock_amir.html : from $AM_FROM -> to $AM_TO ; live $AM"
if [ "$PR" = "$PR_TO" ] && [ "$AM" = "$AM_TO" ]; then echo "ALREADY INSTALLED (both live md5s == to-pins)."; exit 0; fi
[ "$PR" = "$PR_FROM" ] || { echo "REFUSED: pad_receipt.py is $PR, expected $PR_FROM"; exit 1; }
[ "$AM" = "$AM_FROM" ] || { echo "REFUSED: stock_amir.html is $AM, expected $AM_FROM"; exit 1; }

BPR="$FIN/pad_receipt.py.bak_S293_${PR_FROM:0:8}"; BAM="$FIN/stock_amir.html.bak_S293_${AM_FROM:0:8}"
\cp -p "$FIN/pad_receipt.py" "$BPR"; \cp -p "$FIN/stock_amir.html" "$BAM"; echo "backup : $BPR"; echo "backup : $BAM"
restore() { echo "!! restoring both files byte-identically"; \cp -p "$BPR" "$FIN/pad_receipt.py"; \cp -p "$BAM" "$FIN/stock_amir.html"
  rm -f "$FIN"/pad_receipt.py.S293new* "$FIN"/stock_amir.html.S293new*
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/pad_receipt.py" "$FIN/stock_amir.html"; exit 1; }

\cp -p "$FIN/pad_receipt.py" "$FIN/pad_receipt.py.S293new"; \cp -p "$FIN/stock_amir.html" "$FIN/stock_amir.html.S293new"
"$PY" -B "$KIT_DIR/patch_darpan_list_s293.py" --receipt "$FIN/pad_receipt.py.S293new" --amir "$FIN/stock_amir.html.S293new" \
      --receipt-from "$PR_FROM" --amir-from "$AM_FROM" || restore
[ "$(md5of "$FIN/pad_receipt.py.S293new")" = "$PR_TO" ] || { echo "!! pad_receipt.py patched to an unpredicted md5"; restore; }
[ "$(md5of "$FIN/stock_amir.html.S293new")" = "$AM_TO" ] || { echo "!! stock_amir.html patched to an unpredicted md5"; restore; }
"$PY" -m py_compile "$FIN/pad_receipt.py.S293new" || restore; echo "smoke  : py_compile OK"
mv "$FIN/pad_receipt.py.S293new" "$FIN/pad_receipt.py" || restore
mv "$FIN/stock_amir.html.S293new" "$FIN/stock_amir.html" || restore
rm -f "$FIN"/pad_receipt.py.S293new.bak_S293_* "$FIN"/stock_amir.html.S293new.bak_S293_* 2>/dev/null || true
( cd "$FIN" && "$PY" -B -c "import pad_receipt as P; d=dict(count_id=1, day='06-09-2026', reasons=[(1,'count error','')], tranche=dict(no=1,kind='med',issued_text='x'), rows=[dict(item='TEST',packing='1*10',pack=10,marg=20,counted=12,diff=-8)]); b=P.render_tranche(d); assert b[:5]==b'%PDF-' and len(b)>800; print('smoke  : a test list renders (%d bytes)' % len(b))" ) || restore

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  echo "service: clinic-finance active after restart"
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/stock/page/amir || true)
  echo "page   : HTTP $code (302/401 = the login gate, as before)"
fi
echo "md5sum of the installed files:"; md5sum "$FIN/pad_receipt.py" "$FIN/stock_amir.html"
echo "S293_DARPAN_LIST: DONE"
echo "read next: https://followup.dr-manoj.in/finance/stock/page/amir?count=1"
