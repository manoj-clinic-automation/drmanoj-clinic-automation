# -*- coding: utf-8 -*-
"""spine_read_block_s470.py -- kit S470_ORDER_ON_SPINE, part A: the methods the read door gains for the order engine.
make_s470.py copies the lines between the two marker comments into class Spine of /root/finance/spine/spine_read.py, above its
"health" block. This file is the methods' home in the kit; the class around them here only lets it compile and be read.
Read-only, like every method there. Nothing existing changes."""
import datetime as dt
import re


class Spine:                                                   # the frame only -- the real class is spine_read.Spine
    # >>> S470 methods
    # ---------------------------------------------------------------- S470 (D672): what the order engine reads
    def sales_daily(self, name, date_from, date_to):
        """[{date, units, bills}] -- one row per day with a sale; RETURNS DEDUCTED: a line of a credit-note bill counts negative."""
        return self.q("SELECT l.date AS date, SUM(CASE WHEN COALESCE(b.credit_note,0)=1 THEN -l.units ELSE l.units END) AS units, "
                      "COUNT(DISTINCT l.bill) AS bills FROM sp_sale_line l LEFT JOIN sp_sale_bill b ON b.date=l.date AND b.bill=l.bill "
                      "WHERE l.k20=? AND l.date BETWEEN ? AND ? GROUP BY l.date ORDER BY l.date", self.key(name), date_from, date_to)

    def stock_series(self, name, date_from, date_to):
        """[{date, units}] -- the spine's figure at the END of every day in the range (cumulative sp_move to that day; a day with no
        movement repeats the day before)."""
        k = self.key(name)
        bal = self.q("SELECT COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND date<?", k, date_from)[0]["u"] or 0.0
        by = {r["date"]: r["u"] for r in self.q("SELECT date, COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND date BETWEEN ? AND ? "
                                                "GROUP BY date", k, date_from, date_to)}
        out = []
        d, d1 = dt.date.fromisoformat(date_from), dt.date.fromisoformat(date_to)
        while d <= d1:
            bal += by.get(d.isoformat(), 0.0)
            out.append(dict(date=d.isoformat(), units=round(bal, 3)))
            d += dt.timedelta(days=1)
        return out

    def purchase_lines(self, name=None, supplier=None, date_from=None, date_to=None):
        """[{supkey, supplier, bill, date, name27, qty, free, units, amount_p, net_amount_p, direction}] -- sp_purchase_line with the
        supplier's printed name from its bill; oldest first. name: the item (by key). supplier: a supplier's name, matched on the spine's
        own supplier key (its first eight letters). direction as stored: PURCHASE / RETURN."""
        w, a = [], []
        if name is not None:
            w.append("l.k20=?")
            a.append(self.key(name))
        if supplier is not None:
            w.append("l.supkey=?")
            a.append(re.sub(r'[^A-Z]', '', str(supplier).upper())[:8])
        if date_from is not None:
            w.append("l.date>=?")
            a.append(date_from)
        if date_to is not None:
            w.append("l.date<=?")
            a.append(date_to)
        return self.q("SELECT l.supkey AS supkey, b.supplier AS supplier, l.bill AS bill, l.date AS date, l.name27 AS name27, l.qty AS qty, "
                      "l.free AS free, l.units AS units, l.amount_p AS amount_p, l.net_amount_p AS net_amount_p, l.direction AS direction "
                      "FROM sp_purchase_line l LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date "
                      + ("WHERE " + " AND ".join(w) if w else "") + " ORDER BY l.date, l.bill, l.seq", *a)

    def family(self, name):
        """{key, members: [{name, packing, unit_kind, first_seen, last_seen}], n} -- the rows of sp_item under the key (item() reshaped).
        n counts ROWS, every one ever seen under the key: an older packing, and the same item where two reports spell its packing
        differently ('1*10' and '1*10.'), are rows too -- so n is not the number of items Marg lists today."""
        it = self.item(name)
        mem = [dict(name=r["name"], packing=r["packing"], unit_kind=r["unit_kind"], first_seen=r["first_seen"], last_seen=r["last_seen"])
               for r in it["items"]]
        return dict(key=it["key"], members=mem, n=len(mem))

    def last_sale(self, name):
        """{date} of the latest sale line of the key over all history, or None."""
        d = self.q("SELECT MAX(date) AS d FROM sp_sale_line WHERE k20=?", self.key(name))[0]["d"]
        return dict(date=d) if d else None

    def closing(self, name, as_on=None):
        """{as_on, units} -- Marg's own closing figure (sp_close) at or before the date (today when none); None when Marg never listed it.
        The same read stock() carries as marg_units / marg_as_on."""
        d = as_on or dt.date.today().isoformat()
        r = self.q("SELECT as_on, units FROM sp_close WHERE k20=? AND as_on<=? ORDER BY as_on DESC LIMIT 1", self.key(name), d)
        return dict(as_on=r[0]["as_on"], units=r[0]["units"]) if r else None
    # <<< S470 methods
