"""spine_read.py -- S272 / kit S331 (Sanjeevni). The ONE read door onto the spine. Read-only, always.

    from spine_read import Spine
    sp = Spine()                          # /root/finance/spine/spine.db, opened read-only
    sp.item("KNEE SUPPORT HINGED")        # any spelling -> the item(s) it reaches, or a family
    sp.stock("TYRO BR")                   # Marg's stock at the latest closing, and the spine's figure today
    sp.stock("TYRO BR", "2026-09-05")     # ... as on a date
    sp.sales("TYRO BR", "2026-09-01", "2026-09-17")
    sp.fact("TYRO BR", "mrp")             # mrp / salt / p_rate / s_rate / category / company, latest
    sp.bills("2026-09-17")                # the sale bills of a day, money only
    sp.purchases("2026-09")               # purchase bills of a month, with direction
    sp.gate()                             # the last build's gate rows
    sp.status()                           # one line for a health page

Command line: python3 spine_read.py status | item NAME | stock NAME [DATE] | fact NAME | gate

No screen reads the spine yet (rung 3 of S272_SPINE_ARCHITECTURE). This module is what rung 4 will import.
"""
import datetime as dt
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DB_DEFAULT = os.path.join(HERE, "spine.db")


def K(n):
    return re.sub(r'\s+', ' ', (n or "").strip())[:20].strip()


class Spine:
    def __init__(self, db=DB_DEFAULT):
        self.path = db
        self.con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        self.con.row_factory = sqlite3.Row
        self._alias = {r["alias"]: r["k20"] for r in self.con.execute("SELECT alias, k20 FROM sp_alias")}

    def q(self, s, *a):
        return [dict(r) for r in self.con.execute(s, a).fetchall()]

    def key(self, name):
        k = K(name)
        return self._alias.get(k, k)

    def meta(self):
        return {r["key"]: r["value"] for r in self.con.execute("SELECT key, value FROM sp_meta")}

    # ---------------------------------------------------------------- items
    def item(self, name):
        k = self.key(name)
        rows = self.q("SELECT k20, name, packing, unit_kind, first_seen, last_seen FROM sp_item WHERE k20=? ORDER BY name, packing", k)
        return dict(key=k, items=rows, family=len(rows) > 1)

    def fact(self, name, fact=None, as_on=None):
        k = self.key(name)
        facts = ("salt", "mrp", "p_rate", "s_rate", "category", "company") if fact is None else (fact,)
        out = {}
        for f in facts:
            rows = self.q("SELECT f.name, f.packing, f.value, f.as_on FROM sp_item_fact f JOIN sp_item i "
                          "ON i.name=f.name AND i.packing=f.packing WHERE i.k20=? AND f.fact=? AND (? IS NULL OR f.as_on<=?) "
                          "ORDER BY f.as_on DESC", k, f, as_on, as_on)
            seen = {}
            for r in rows:
                seen.setdefault((r["name"], r["packing"]), r)
            out[f] = list(seen.values())
        return out if fact is None else out[fact]

    # ---------------------------------------------------------------- stock
    def stock(self, name, as_on=None):
        k = self.key(name)
        d = as_on or dt.date.today().isoformat()
        spine = self.q("SELECT COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND date<=?", k, d)[0]["u"]
        marg = self.q("SELECT as_on, units FROM sp_close WHERE k20=? AND as_on<=? ORDER BY as_on DESC LIMIT 1", k, d)
        return dict(key=k, as_on=d, spine_units=spine, marg_units=marg[0]["units"] if marg else None,
                    marg_as_on=marg[0]["as_on"] if marg else None,
                    unit="packs" if self.q("SELECT 1 FROM sp_item WHERE k20=? AND unit_kind='WHOLE' LIMIT 1", k) else "units")

    def movements(self, name, date_from, date_to):
        return self.q("SELECT date, kind, units, ref FROM sp_move WHERE k20=? AND date BETWEEN ? AND ? ORDER BY date", self.key(name), date_from, date_to)

    # ---------------------------------------------------------------- sales / purchases
    def sales(self, name, date_from, date_to):
        k = self.key(name)
        r = self.q("SELECT COUNT(DISTINCT bill) AS bills, COALESCE(SUM(units),0) AS units, "
                   "COALESCE(SUM(rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS amount_p "
                   "FROM sp_sale_line WHERE k20=? AND date BETWEEN ? AND ?", k, date_from, date_to)[0]
        return dict(key=k, **r)

    def bills(self, day):
        return self.q("SELECT date, bill, gross_p, disc_p, tax_p, drcr_p, net_p, cash_p, credit_note FROM sp_sale_bill WHERE date=? ORDER BY bill", day)

    def purchases(self, month):
        return self.q("SELECT supplier, bill, date, amount_p, direction FROM sp_purchase_bill WHERE date LIKE ? ORDER BY date, supplier", month + "%")

    # ---------------------------------------------------------------- health
    def gate(self):
        return self.q("SELECT n, name, blocking, ok, detail FROM sp_gate ORDER BY n")

    def findings(self, open_only=True):
        return self.q("SELECT as_on, k20, diff, note FROM sp_finding WHERE (? = 0 OR note LIKE 'OPEN%') ORDER BY as_on, k20", 0 if not open_only else 1)

    def status(self):
        m = self.meta()
        g = self.gate()
        bad = [r["name"] for r in g if r["blocking"] and not r["ok"]]
        latest = m.get("checkable", "").split(",")[-1]
        op = self.findings()
        return "spine built %s · gate %d/%d blocking checks green%s · stock = Marg at %s%s · pending closings: %s" % (
            m.get("built", "?")[:16], sum(1 for r in g if r["blocking"] and r["ok"]), sum(1 for r in g if r["blocking"]),
            "" if not bad else " -- RED: " + "; ".join(bad), latest or "?",
            "" if not op else " EXCEPT %d item(s): %s" % (len(op), ", ".join("%s %+g" % (f["k20"], f["diff"]) for f in op[:6])),
            m.get("pending") or "none")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    sp = Spine(os.environ.get("SPINE_DB", DB_DEFAULT))
    cmd, rest = argv[0], argv[1:]
    if cmd == "status":
        print(sp.status())
    elif cmd == "item":
        print(sp.item(" ".join(rest)))
    elif cmd == "stock":
        print(sp.stock(rest[0], rest[1] if len(rest) > 1 else None))
    elif cmd == "fact":
        print(sp.fact(" ".join(rest)))
    elif cmd == "gate":
        for r in sp.gate():
            print("  %-4s %s%s" % ("ok" if r["ok"] else ("FAIL" if r["blocking"] else "note"), r["name"],
                                   ("  -- " + r["detail"][:300]) if not r["ok"] or not r["blocking"] else ""))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
