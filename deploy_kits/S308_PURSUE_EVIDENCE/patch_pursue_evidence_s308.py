#!/usr/bin/env python3
"""S308_PURSUE_EVIDENCE -- step 8 of the stock check asks Darpan with the evidence already gathered.

The owner marks a line "to pursue" and Darpan is asked whether it was sold without a bill. The server holds the
sale lines and the purchase lines, so for each pursued line it now says first: how much sold in the 30 days before
the count and on how many bills, when it last sold, whether anything has sold since the count, when it was last
bought, and the item's own open question for Marg's ledger. An item that never sells is a different question from
one that sells every day. Reads only -- no table, no decision.

stock_app.py (anchored edits over S304 b997aa35)
  1. _pursue_sales / _pursue_card / _pursue_cards before _hub_data;
  2. the hub's step 8 carries `cards`.
stock_hub.html is shipped whole by the installer (over S304 3f548592): step 8 lists them.

    python3 -B patch_pursue_evidence_s308.py --app stock_app.py [--app-from M] [--dry-run]
"""
from __future__ import print_function
import argparse
import hashlib
import io
import shutil
import sys

PURSUE_BLOCK = '# ---------------------------------------------------------------------------\n# S308 WHAT DARPAN IS ASKED, WITH THE EVIDENCE ALREADY GATHERED -- step 8 of the stock check.\n# The owner marks a line "to pursue" and Darpan is asked whether it was sold without a bill. Until now\n# the question went to him bare. The server already holds the sale lines and the purchase lines, so for\n# each pursued line it says, before he is asked: how much of this item sold in the 30 days before the\n# count and on how many bills, when it last sold, whether anything has sold since the count, and when it\n# was last bought. An item that never sells is a different question from one that sells every day.\n# Reads only -- no table, no decision. His answer is still evidence and the owner\'s tap still decides.\n# ---------------------------------------------------------------------------\nPURSUE_WINDOW_DAYS = 30\n\n\ndef _pursue_sales(con, item, ps, a_iso, b_iso):\n    """(units, bills, last date) sold in [a, b]; returns are netted off the units."""\n    sk = _sale_key(item)\n    units = 0\n    bills = set()\n    last = ""\n    for r in con.execute("SELECT bill_no, is_return, qty_raw, business_date FROM sale_line_item "\n                         "WHERE unit=? AND item_key IN (?, ?) AND business_date>=? AND business_date<=?",\n                         (_unit, item, sk, a_iso, b_iso)):\n        u = _sale_units(r[2], ps)\n        if r[1]:\n            units -= u\n        else:\n            units += u\n            bills.add(r[0])\n            last = max(last, str(r[3] or ""))\n    return units, len(bills), last\n\n\ndef _pursue_card(con, d, x):\n    """S308: the evidence that rides with one pursued line. Never raises."""\n    out = dict(item=x["item"], short_text=_qw(-int(x["diff"] or 0), x.get("pack")), before_units=0, before_bills=0,\n               before_text="", since_units=0, since_text="", last_sale="", last_buy="", last_buy_qty="", lines=[])\n    try:\n        day_iso = _dmy_to_iso(d.get("day")) or ""\n        if not day_iso:\n            return out\n        ps = int(x.get("pack") or 1)\n        a = (dt.date(int(day_iso[:4]), int(day_iso[5:7]), int(day_iso[8:10])) - dt.timedelta(days=PURSUE_WINDOW_DAYS)).isoformat()\n        bu, bb, bl = _pursue_sales(con, x["item"], ps, a, day_iso)\n        today = dt.date.today().isoformat()\n        su, _sb, sl = _pursue_sales(con, x["item"], ps, day_iso, today)\n        out.update(before_units=bu, before_bills=bb, before_text=_qw(bu, ps), since_units=su,\n                   since_text=_qw(su, ps), last_sale=(sl or bl or ""))\n        r = con.execute("SELECT bill_date, qty, free, packing FROM purchase_line WHERE item=? AND bill_date<=? "\n                        "ORDER BY bill_date DESC LIMIT 1", (x["item"], today)).fetchone()\n        if r:\n            out["last_buy"] = r[0] or ""\n            try:\n                out["last_buy_qty"] = _qw(int(float(r[1] or 0)) * ps + int(float(r[2] or 0)) * ps, ps)\n            except (TypeError, ValueError):\n                out["last_buy_qty"] = ""\n        lines = []\n        if bb:\n            lines.append("sold %s on %d bill%s in the %d days before the count (last %s)"\n                         % (out["before_text"], bb, "" if bb == 1 else "s", PURSUE_WINDOW_DAYS, _r_dmy(bl)))\n        else:\n            lines.append("NOT SOLD ONCE in the %d days before the count -- a shortage here is not a counter sale"\n                         % PURSUE_WINDOW_DAYS)\n        lines.append(("sold %s since the count (last %s)" % (out["since_text"], _r_dmy(sl))) if su\n                     else "nothing sold since the count")\n        if out["last_buy"]:\n            lines.append("last bought %s%s" % (_r_dmy(out["last_buy"]), (" -- " + out["last_buy_qty"]) if out["last_buy_qty"] else ""))\n        for q in (x.get("lookups") or [])[:2]:\n            lines.append(q)\n        out["lines"] = lines\n    except Exception:                                         # noqa: BLE001 -- evidence is never worth a broken page\n        return out\n    return out\n\n\ndef _pursue_cards(con, d):\n    """Every line the owner has marked to pursue, with its evidence, worst first."""\n    xs = [x for x in d["differences"] if (x.get("word") or {}).get("action") == "RECOVER"]\n    xs.sort(key=lambda x: (-(abs(int(x.get("mrp_p") or 0))), x["item"]))\n    return [_pursue_card(con, d, x) for x in xs[:40]]\n'

APP_EDITS = [
    ('def _hub_data(con, cid):\n', PURSUE_BLOCK + '\n\ndef _hub_data(con, cid):\n'),
    ('                pursue=dict(lines=tot["pursue"], state=("wait" if not tot["pursue"] else "now")),\n',
     '                pursue=dict(lines=tot["pursue"], cards=_pursue_cards(con, d),   # S308: the evidence rides with the question\n'
     '                            state=("wait" if not tot["pursue"] else "now")),\n'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_one(path, edits, from_md5, marker, dry):
    raw = io.open(path, "rb").read()
    cur = md5(raw)
    text = raw.decode("utf-8")
    if marker in text:
        print("ALREADY PATCHED: %s is %s" % (path, cur))
        return cur
    if from_md5 and cur != from_md5.lower():
        sys.exit("REFUSING: %s is %s, expected %s" % (path, cur, from_md5))
    for old, new in edits:
        if text.count(old) != 1:
            sys.exit("REFUSING: anchor not found exactly once in %s: %r" % (path, old[:80]))
        text = text.replace(old, new)
    new = text.encode("utf-8")
    if dry:
        print("would write %s : %s -> %s" % (path, cur, md5(new)))
        return md5(new)
    shutil.copy2(path, "%s.bak_S308_%s" % (path, cur[:8]))
    with io.open(path, "wb") as fh:
        fh.write(new)
    back = md5(io.open(path, "rb").read())
    print("patched %s : %s -> %s" % (path, cur, back))
    if back != md5(new):
        sys.exit(4)
    return back


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--app-from", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    patch_one(a.app, APP_EDITS, a.app_from, "def _pursue_cards(con, d):", a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
