#!/usr/bin/env python3
"""make_s845.py -- S845_ITEM_LEDGER: the two live files rebuilt from their LIVE bytes (each checked against its FROM pin first), every anchor
exactly once; item_ledger.py is new. Writes into OUT. Usage: python3 make_s845.py <live finance dir> <OUT dir>"""
import hashlib, os, sys

FROM = {"sanjeevni_approvals.py": "cd5174d6bfb9d62b55dd037e903e1d74", "finance_ui/finance_approvals.html": "9f6295856e36f93a00028de7cc3fe769"}

A1 = '''        print("marg_billwatch NOT mounted: %s" % _e803, file=_sys803.stderr)
    return bp
'''
B1 = '''        print("marg_billwatch NOT mounted: %s" % _e803, file=_sys803.stderr)
    try:                                                      # S845 (16-Nov-2026): the Item ledger -- read only (item_ledger.py; D992)
        import item_ledger                                    # noqa: PLC0415 -- beside this file
        item_ledger.init(app, db_getter, require_fn)
    except Exception as _e845:                                # noqa: BLE001 -- these pages keep working without it
        import sys as _sys845                                 # noqa: PLC0415
        print("item_ledger NOT mounted: %s" % _e845, file=_sys845.stderr)
    return bp
'''
A2 = '''    <div class="goto-grid">
'''
B2 = '''    <form method="get" action="/finance/sanjeevni/ledger" style="display:flex;gap:8px;margin-top:10px"><!-- S845 (D992): the Item ledger, straight from Go to -->
      <input name="q" autocomplete="off" placeholder="Item ledger — type a medicine or orthotic, press Enter" style="flex:1;padding:8px 10px;border:1px solid #c9ced6;border-radius:8px;font-size:14px;min-height:36px">
      <button type="submit" class="ghost">Open</button></form>
    <div class="goto-grid">
'''
A3 = '''        <a href="/finance/stock/page/now">Stock now</a>
'''
B3 = '''        <a href="/finance/sanjeevni/ledger"><b>Item ledger</b> — any item's stock, bills and vouchers</a>
        <a href="/finance/stock/page/now">Stock now</a>
'''
EDITS = {"sanjeevni_approvals.py": [(A1, B1)], "finance_ui/finance_approvals.html": [(A2, B2), (A3, B3)]}


def main(live, out):
    for rel, pin in FROM.items():
        b = open(os.path.join(live, rel), "rb").read()
        got = hashlib.md5(b).hexdigest()
        if got != pin:
            sys.exit("STOP: %s is %s, not the FROM pin %s -- nothing built" % (rel, got, pin))
        s = b.decode("utf-8")
        for a, n in EDITS[rel]:
            c = s.count(a)
            if c != 1:
                sys.exit("STOP: %s anchor found %d times -- nothing built" % (rel, c))
            s = s.replace(a, n)
        p = os.path.join(out, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(s.encode("utf-8"))
        print("built %s %s" % (rel, hashlib.md5(s.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
