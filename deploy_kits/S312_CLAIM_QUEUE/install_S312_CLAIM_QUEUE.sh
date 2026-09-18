#!/bin/bash
# install_S312_CLAIM_QUEUE.sh -- Darpan's claim queue (D471) and the door hub step 8 never had (D544).
#
# A stock line the owner marks "to pursue" becomes a CLAIM: open -> contacted -> settled.
# Darpan is asked WITH THE EVIDENCE S308 already gathered and taps one of five answers
# (open -> contacted); the owner settles, and only he does -- his own rule on the hub is
# "His answer is evidence; your tap decides."  Hub step 8 could reach only waiting/now
# before this, because there was nowhere to record an answer; it can now reach DONE.
#
#   /root/finance/claim_queue.py    NEW      -> a61744ee   (the queue: schema, states, sweep)
#   /root/finance/stock_app.py      a8f98cda -> f313f3d3   (step 8's state + the settle door)
#   /root/finance/darpan_app.py     f98004c9 -> df3224c5   (his two doors)
#   /root/finance/darpan_card.html  572fb019 -> 8510c9cb   (section 8, Hinglish, five taps)
#   /root/finance/stock_hub.html    936677b8 -> c4f3280b   (the answers come back; the settle tap)
#
# THE SELF-CLOSE, HONESTLY.  D471 asks the queue to close itself on a matching purchase return.
# No purchase return is stored on this box -- purchase_line.direction is 'PURCHASE' on every row
# and there is no return table -- so that rule is WRITTEN AND ASLEEP, and wakes by itself the day
# one is stored.  What does self-close today is real: a later count that finds the item agreeing.
# A credit note is shown as a candidate and closes nothing; it names no item.
#
# New table claim_line only, created additively by claim_queue.ensure(). amir_claim is NOT touched:
# it is Amir's bill-keyed supplier claim and its counters keep their meaning.
# clinic-finance restarted.  Before anything is placed: the patched modules walk a SCRATCH copy of
# the live database, and the hub payload must be IDENTICAL to the live one on every key but step 8.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S312_CLAIM_QUEUE/install_S312_CLAIM_QUEUE.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOWALK=1
set -u
KIT="S312_CLAIM_QUEUE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DBF="${FINANCE_DB:-$FIN/finance.db}"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s312_walk_$STAMP"

CQ="$FIN/claim_queue.py";      CQ_TO="a61744ee8845b6f718af852edcac5eb0"
SA="$FIN/stock_app.py";        SA_FROM="a8f98cdae47bd23bef3ede5c5fd48d07"; SA_TO="f313f3d337818cf07612507c58bf60f4"
DA="$FIN/darpan_app.py";       DA_FROM="f98004c922837f4f8ac41daa153f79b3"; DA_TO="df3224c5fb45964d8b53df660ff60def"
DC="$FIN/darpan_card.html";    DC_FROM="572fb019c3f8a090a3a69153d471b3da"; DC_TO="8510c9cbadffa42a7d4c49baff1e2aae"
SH="$FIN/stock_hub.html";      SH_FROM="936677b8d90a694ba26e9ac7b9de9732"; SH_TO="c4f3280b2d005b39c02d3f6eed13c3ec"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
BAK_SA=""; BAK_DA=""; BAK_DC=""; BAK_SH=""; CQ_PLACED=0
restore() {
  echo "!! restoring -- nothing of S312 stays"
  [ -n "$BAK_SA" ] && [ -f "$BAK_SA" ] && \cp -p "$BAK_SA" "$SA"
  [ -n "$BAK_DA" ] && [ -f "$BAK_DA" ] && \cp -p "$BAK_DA" "$DA"
  [ -n "$BAK_DC" ] && [ -f "$BAK_DC" ] && \cp -p "$BAK_DC" "$DC"
  [ -n "$BAK_SH" ] && [ -f "$BAK_SH" ] && \cp -p "$BAK_SH" "$SH"
  [ "$CQ_PLACED" = "1" ] && rm -f "$CQ"
  rm -f "$SA.S312new" "$DA.S312new" "$DC.S312new" "$SH.S312new" 2>/dev/null
  rm -f "$FIN"/*.bak_S312_* 2>/dev/null
  [ "${NORESTART:-0}" != "1" ] && systemctl restart clinic-finance >/dev/null 2>&1
  echo "   stock_app.py  $(m5 "$SA")"; echo "   darpan_app.py $(m5 "$DA")"
  echo "   darpan_card   $(m5 "$DC")"; echo "   stock_hub     $(m5 "$SH")"
  exit 1
}

echo "== $KIT installer =="
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
echo "[1/8] kit sums green"

c_sa="$(m5 "$SA")"; c_da="$(m5 "$DA")"; c_dc="$(m5 "$DC")"; c_sh="$(m5 "$SH")"; c_cq="$(m5 "$CQ")"
echo "stock_app.py    : $SA_FROM -> $SA_TO ; live $c_sa"
echo "darpan_app.py   : $DA_FROM -> $DA_TO ; live $c_da"
echo "darpan_card.html: $DC_FROM -> $DC_TO ; live $c_dc"
echo "stock_hub.html  : $SH_FROM -> $SH_TO ; live $c_sh"
echo "claim_queue.py  : NEW -> $CQ_TO ; live ${c_cq:-absent}"
if [ "$c_sa" = "$SA_TO" ] && [ "$c_da" = "$DA_TO" ] && [ "$c_dc" = "$DC_TO" ] \
   && [ "$c_sh" = "$SH_TO" ] && [ "$c_cq" = "$CQ_TO" ]; then
  echo "ALREADY INSTALLED (every live md5 == its to-pin)."; exit 0
fi
for pair in "$c_sa:$SA_FROM:stock_app.py" "$c_da:$DA_FROM:darpan_app.py" \
            "$c_dc:$DC_FROM:darpan_card.html" "$c_sh:$SH_FROM:stock_hub.html"; do
  cur="${pair%%:*}"; rest="${pair#*:}"; want="${rest%%:*}"; name="${rest#*:}"
  [ "$cur" = "$want" ] || { echo "!! [2/8] $name is $cur, expected $want - nothing installed"; exit 1; }
done
if [ -n "$c_cq" ] && [ "$c_cq" != "$CQ_TO" ]; then
  echo "!! [2/8] $CQ already exists at $c_cq and is not this kit's - nothing installed"; exit 1
fi
echo "[2/8] every live pin is exact"

rm -f "$SA.S312new" "$DA.S312new" "$DC.S312new" "$SH.S312new"
\cp -p "$SA" "$SA.S312new"; \cp -p "$DA" "$DA.S312new"
mkdir -p "$WALK/stage" "$WALK/new" "$WALK/live" || { echo "!! [3/8] scratch failed"; exit 1; }
\cp -p "$DC" "$WALK/stage/darpan_card.html"; \cp -p "$SH" "$WALK/stage/stock_hub.html"
fail3() { rm -f "$SA.S312new"* "$DA.S312new"*; rm -rf "$WALK"; echo "!! [3/8] $1 - nothing placed"; exit 1; }
"$PY" -B patch_stock_claims_s312.py  --file "$SA.S312new" --from "$SA_FROM" --expect "$SA_TO" || fail3 "stock_app patch refused"
"$PY" -B patch_darpan_claims_s312.py --file "$DA.S312new" --from "$DA_FROM" --expect "$DA_TO" || fail3 "darpan_app patch refused"
"$PY" -B patch_cards_s312.py --dir "$WALK/stage" --card-from "$DC_FROM" --card-expect "$DC_TO" \
      --hub-from "$SH_FROM" --hub-expect "$SH_TO" || fail3 "the screens' patch refused"
rm -f "$SA.S312new.bak_S312_"* "$DA.S312new.bak_S312_"* "$WALK/stage/"*.bak_S312_*
[ "$(m5 "$SA.S312new")" = "$SA_TO" ] || fail3 "stock_app patched to an unpredicted md5"
[ "$(m5 "$DA.S312new")" = "$DA_TO" ] || fail3 "darpan_app patched to an unpredicted md5"
[ "$(m5 "$WALK/stage/darpan_card.html")" = "$DC_TO" ] || fail3 "darpan_card patched to an unpredicted md5"
[ "$(m5 "$WALK/stage/stock_hub.html")" = "$SH_TO" ] || fail3 "stock_hub patched to an unpredicted md5"
[ "$(m5 "$KDIR/claim_queue.py")" = "$CQ_TO" ] || fail3 "the kit's claim_queue.py is not $CQ_TO"
for f in "$SA.S312new" "$DA.S312new" "$KDIR/claim_queue.py"; do
  "$PY" -c "import sys, os, tempfile, py_compile; py_compile.compile(sys.argv[1], cfile=os.path.join(tempfile.mkdtemp(), 'x.pyc'), doraise=True)" "$f" \
    || fail3 "$(basename "$f") does not compile"
done
echo "[3/8] all five patched/staged to their predicted md5; the three modules compile"

"$PY" -B "$KDIR/selftest_s312.py" | tail -1 | grep -q ', 0 failed' || fail3 "the queue's own selftest is red"
echo "[4/8] selftest green"

if [ "${NOWALK:-0}" != "1" ]; then
  for f in stock_app.py stock_hub.html pad_receipt.py padwriter.py padreader.py stock_schema.sql \
           stock_check_live.html stock_diffs.html; do
    [ -f "$FIN/$f" ] && \cp -p "$FIN/$f" "$WALK/live/$f"
  done
  \cp -p "$WALK/live/"* "$WALK/new/" 2>/dev/null
  \cp -p "$SA.S312new" "$WALK/new/stock_app.py"
  \cp -p "$KDIR/claim_queue.py" "$WALK/new/claim_queue.py"
  \cp -p "$WALK/stage/stock_hub.html" "$WALK/new/stock_hub.html"
  "$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
    || { rm -rf "$WALK"; rm -f "$SA.S312new" "$DA.S312new"; echo "!! [5/8] scratch copy of the database failed - nothing placed"; exit 1; }
  WOUT="$( cd "$FIN" && timeout 170 "$PY" -B "$KDIR/walk_s312.py" "$WALK/live" "$WALK/new" "$WALK/walk.db" 2>&1 | tail -2 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q '^WALK OK' || { rm -rf "$WALK"; rm -f "$SA.S312new" "$DA.S312new"; echo "!! [5/8] the walk is red - nothing placed"; exit 1; }
  echo "[5/8] walked green on a scratch copy of the live database"
else echo "[5/8] walk skipped (NOWALK=1, test only)"; fi

BAK_SA="$SA.bak_S312_${SA_FROM:0:8}"; \cp -p "$SA" "$BAK_SA"
BAK_DA="$DA.bak_S312_${DA_FROM:0:8}"; \cp -p "$DA" "$BAK_DA"
BAK_DC="$DC.bak_S312_${DC_FROM:0:8}"; \cp -p "$DC" "$BAK_DC"
BAK_SH="$SH.bak_S312_${SH_FROM:0:8}"; \cp -p "$SH" "$BAK_SH"
\cp -p "$KDIR/claim_queue.py" "$CQ" && CQ_PLACED=1
mv -f "$SA.S312new" "$SA"; mv -f "$DA.S312new" "$DA"
\cp -p "$WALK/stage/darpan_card.html" "$DC"; \cp -p "$WALK/stage/stock_hub.html" "$SH"
[ "$(m5 "$SA")" = "$SA_TO" ] || restore
[ "$(m5 "$DA")" = "$DA_TO" ] || restore
[ "$(m5 "$DC")" = "$DC_TO" ] || restore
[ "$(m5 "$SH")" = "$SH_TO" ] || restore
[ "$(m5 "$CQ")" = "$CQ_TO" ] || restore
echo "[6/8] placed; every md5 read back == its to-pin (backups .bak_S312_*)"

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance >/dev/null 2>&1; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  # F-525: the gate hits a route that IS in PUBLIC_PATHS. The login-gated pages are probed
  # for information only -- 302/401 there is the login gate doing its job, never a fault.
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
  c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/hub)
  c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/darpan)
  c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/darpan/api/claims)
  echo "health : finance $c1 · hub $c2 · Darpan $c3 · his claims $c4 (302/401 = the login gate, expected)"
  [ "$c1" = 200 ] || restore
  for c in "$c2" "$c3" "$c4"; do case "$c" in 200|302|401) : ;; *) restore ;; esac; done
  echo "[7/8] clinic-finance active and answering"
else echo "[7/8] restart skipped (NORESTART=1, test only)"; fi

rm -rf "$WALK"
echo "[8/8] $KIT: DONE"
echo "   claim_queue.py   $(m5 "$CQ")"
echo "   stock_app.py     $(m5 "$SA")"
echo "   darpan_app.py    $(m5 "$DA")"
echo "   darpan_card.html $(m5 "$DC")"
echo "   stock_hub.html   $(m5 "$SH")"
