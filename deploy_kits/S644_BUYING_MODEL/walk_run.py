#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_run.py -- one step of the S644 walk, in its own process, against ONE app folder (old or new bytes), ONE scratch finance.db (FINANCE_DB)
and ONE spine (SPINE_DB). walk_s644.py drives it. Prints one JSON line. Never touches a live store: every path comes from the environment."""
import datetime as dt
import json
import os
import sqlite3
import sys

APP = os.path.abspath(sys.argv[1])
CMD = sys.argv[2]
ARG = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
sys.path.insert(0, APP)
os.chdir(APP)
import order_rules as OR  # noqa: E402


def con():
    c = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
    c.row_factory = sqlite3.Row
    return c


def set_model(c, v):
    OR.ensure(c)
    c.execute("INSERT INTO setting (key, value, note) VALUES ('order.model', ?, 'walk') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (v,))
    c.commit()


def today():
    return OR._today()


def strip(v):
    """plan() output with its rule object made plain."""
    out = {}
    for vn, x in (v or {}).items():
        out[vn] = dict(vendor=x["vendor"], total_p=x["total_p"], held=x.get("held", ""), paused=x.get("paused"), lines=x["lines"])
    return out


def main():
    c = con()
    if CMD == "plan":
        if ARG.get("model"):
            set_model(c, ARG["model"])
        p = OR.plan(c, today())
        ip = OR.interim_plan(c, today())
        print(json.dumps(dict(engine=p.get("engine"), as_on=p.get("as_on"), vendors=strip(p["vendors"]), no_supplier=p.get("no_supplier"), held_items=p.get("held_items"),
                              inputs=p.get("inputs"), interim=strip(ip.get("vendors")), interim_off=ip.get("off")), default=str))
        return
    if CMD == "prepare":
        if ARG.get("model"):
            set_model(c, ARG["model"])
        made = OR.prepare_day(c, today())
        rows = [dict(r) for r in c.execute("SELECT id, supplier_norm, kind, status, total_p, reason, lines FROM order_proposal WHERE day=? ORDER BY supplier_norm, kind", (today().isoformat(),))]
        for r in rows:
            r["lines"] = json.loads(r["lines"])
        st = c.execute("SELECT slot, text FROM order_notice WHERE day=? ORDER BY slot", (today().isoformat(),)).fetchall()
        print(json.dumps(dict(made=made, rows=rows, notices=[tuple(x) for x in st]), default=str))
        return
    if CMD == "rhythm":
        set_model(c, "levels")
        t = today()
        out = []
        for r in OR.rules(c):
            lb = OR.last_buy(c, r, t)
            e = OR._s644_rhythm(c, t).get(r["supplier_norm"]) or {}
            out.append(dict(supplier=r["supplier_norm"], mode=r.get("rhythm_mode"), cadence=r["cadence"], order_days=r["order_days"], bill_days90=e.get("bill_days90"), median=e.get("gap"),
                            rhythm_days=r.get("rhythm_days"), interval=OR.review_interval(c, r, t), last_buy=lb.isoformat() if lb else None,
                            due_today=OR.is_order_day(c, r, t), next=OR.next_order_day(c, r, t - dt.timedelta(days=1)).isoformat(),
                            gap=OR.gap_days(r, c, t), cap=OR.cap_days(c, r, t), cover=OR.cover_days(c, r, False, t), words=r["words"]))
        print(json.dumps(out, default=str))
        return
    if CMD == "has":
        print(json.dumps(dict(model_rate=hasattr(OR, "model_rate"), relist=hasattr(OR, "_s644_relist"), review_interval=hasattr(OR, "review_interval"), kit=OR.KIT)))
        return
    if CMD == "lastbuy":
        # ARG: supplier, inject: list of dicts(kind='order'|'proposal'|'interim', day)
        set_model(c, "levels")
        t = today()
        r = OR.rule_for(c, ARG["supplier"])
        res = {}
        res["before"] = (OR.last_buy(c, r, t) or dt.date(1970, 1, 1)).isoformat()
        for inj in ARG.get("inject", []):
            d = inj["day"]
            if inj["kind"] in ("order", "interim"):
                c.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, total_p, supplier_norm, order_src) VALUES (?,?,?,?,?,?,?)",
                          (d + "T10:00:00", "walk", r.get("supplier") or ARG["supplier"], "sent", 1, ARG["supplier"], "walk"))
                oid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
                if inj["kind"] == "interim":
                    c.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, prepared_at, sent_order_id, sent_at) VALUES (?,?,?,?,?,?,?,?,?,?) "
                              "ON CONFLICT(day, supplier_norm, kind) DO UPDATE SET status='sent', sent_order_id=excluded.sent_order_id, sent_at=excluded.sent_at",
                              (d, ARG["supplier"], r.get("supplier") or ARG["supplier"], "interim", "sent", "[]", 1, d + "T09:00:00", oid, d + "T10:00:00"))
            elif inj["kind"] == "proposal":
                c.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, prepared_at, sent_at) VALUES (?,?,?,?,?,?,?,?,?) "
                          "ON CONFLICT(day, supplier_norm, kind) DO UPDATE SET status='sent', sent_at=excluded.sent_at",
                          (d, ARG["supplier"], r.get("supplier") or ARG["supplier"], "fixed", "sent", "[]", 1, d + "T09:00:00", d + "T10:00:00"))
            c.commit()
            res["after_" + inj["kind"] + "_" + d] = (OR.last_buy(c, r, t) or dt.date(1970, 1, 1)).isoformat()
        if not c.execute("SELECT 1 FROM order_supplier_rule WHERE supplier_norm=?", (ARG["supplier"],)).fetchone() and (ARG.get("review_days") is not None or ARG.get("mode") or ARG.get("bad")):
            c.execute("INSERT INTO order_supplier_rule (supplier_norm, supplier, cadence, order_days, seeded_at, updated_at) VALUES (?,?,?,?,?,?)", (ARG["supplier"], ARG["supplier"], "weekly", "MON", "walk", "walk"))
            c.commit()
        res["interval"] = OR.review_interval(c, r, t)
        res["due_today"] = OR.is_order_day(c, r, t)
        res["next"] = OR.next_order_day(c, r, t - dt.timedelta(days=1)).isoformat()
        if ARG.get("review_days") is not None:
            body, code = OR.set_rule(c, "walk", ARG["supplier"], "review_days", ARG["review_days"])
            res["set_review_days"] = (code, body.get("changed"), body.get("message"))
            r = OR.rule_for(c, ARG["supplier"])
            res["interval_after_override"] = OR.review_interval(c, r, t)
            res["words_after_override"] = OR.rule_words(c, r)
        if ARG.get("mode"):
            body, code = OR.set_rule(c, "walk", ARG["supplier"], "rhythm_mode", ARG["mode"])
            res["set_mode"] = (code, body.get("changed"))
            r = OR.rule_for(c, ARG["supplier"])
            res["due_today_after_mode"] = OR.is_order_day(c, r, t)
            res["next_after_mode"] = OR.next_order_day(c, r, t - dt.timedelta(days=1)).isoformat()
        for bad in ARG.get("bad", []):
            body, code = OR.set_rule(c, "walk", ARG["supplier"], bad[0], bad[1])
            res["bad_%s_%s" % (bad[0], bad[1])] = code
        print(json.dumps(res, default=str))
        return
    if CMD == "onorder":
        # ARG: supplier, ages: [days]
        set_model(c, ARG.get("model", "levels"))
        t = today()
        r = OR.rule_for(c, ARG["supplier"])
        out = {"interval": OR.review_interval(c, r, t) if hasattr(OR, "review_interval") else None, "on_order_days": OR._s470_days(c, "order.on_order_days")}
        item = "WALK ITEM S644"
        for age in ARG["ages"]:
            d = (t - dt.timedelta(days=age)).isoformat()
            c.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, total_p, supplier_norm, order_src) VALUES (?,?,?,?,?,?,?)",
                      (d + "T10:00:00", "walk", r.get("supplier") or ARG["supplier"], "sent", 1, ARG["supplier"], "walk"))
            oid = c.execute("SELECT last_insert_rowid()").fetchone()[0]
            c.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units) VALUES (?,?,?,?,?)", (oid, item + " %d" % age, 2, 10, 20))
            c.commit()
        u = OR._on_order_units(c, t, "count")
        out["counted_ages"] = sorted(int(k.rsplit(" ", 1)[1]) for k in u if k.startswith(OR._pa().norm(item)))
        print(json.dumps(out))
        return
    if CMD == "relist":
        set_model(c, ARG.get("model", "levels"))
        t = today()
        res = {}
        res["prepare"] = OR.prepare_day(c, t)
        ids0 = {(r[0], r[1]): r[2] for r in c.execute("SELECT supplier_norm, kind, id FROM order_proposal WHERE day=?", (t.isoformat(),))}
        st = c.execute("SELECT text FROM order_notice WHERE day=? AND slot='made_through'", (t.isoformat(),)).fetchone()
        res["stamp"] = st[0] if st else None
        now = dt.datetime.combine(t, dt.time(9, 40))
        if not hasattr(OR, "_s644_relist"):
            print(json.dumps(dict(res, relist="absent")))
            return
        res["tick_same"] = OR._s644_relist(c, t, now)
        if st:
            old = json.loads(st[0])
            old["sales_through"] = "2000-01-01"                      # as if the list had been made before the sale report landed
            c.execute("UPDATE order_notice SET text=? WHERE day=? AND slot='made_through'", (json.dumps(old, sort_keys=True), t.isoformat()))
            c.commit()
        res["tick_moved"] = OR._s644_relist(c, t, now)
        ids1 = {(r[0], r[1]): r[2] for r in c.execute("SELECT supplier_norm, kind, id FROM order_proposal WHERE day=?", (t.isoformat(),))}
        res["ids_kept"] = all(ids1.get(k) == v for k, v in ids0.items())
        res["rows_before_after"] = (len(ids0), len(ids1))
        res["tick_again"] = OR._s644_relist(c, t, now)
        res["notices"] = [tuple(x) for x in c.execute("SELECT slot, substr(text,1,60) FROM order_notice WHERE day=? ORDER BY slot", (t.isoformat(),))]
        # touched: a Darpan edit today -> stale, no rebuild
        c.execute("UPDATE order_notice SET text=? WHERE day=? AND slot='made_through'", (json.dumps(old, sort_keys=True), t.isoformat()))
        c.execute("INSERT INTO order_darpan_edit (day, supplier_norm, item, action, qty, at, by) VALUES (?,?,?,?,?,?,?)", (t.isoformat(), "X", "Y", "hold", 0, "now", "walk"))
        c.commit()
        res["tick_touched"] = OR._s644_relist(c, t, now)
        res["stale"] = bool(c.execute("SELECT 1 FROM order_notice WHERE day=? AND slot='stale'", (t.isoformat(),)).fetchone())
        c.execute("DELETE FROM order_darpan_edit WHERE by='walk'")
        c.commit()
        res["tick_late"] = OR._s644_relist(c, t, dt.datetime.combine(t, dt.time(13, 5)))
        set_model(c, "fixed")
        res["tick_fixed"] = OR._s644_relist(c, t, now)
        print(json.dumps(res, default=str))
        return
    if CMD == "owner":
        set_model(c, ARG.get("model", "levels"))
        d = OR.owner_state(c, today())
        m = d.get("model") or {}
        print(json.dumps(dict(keys=sorted(m.keys()), value=m.get("value"), n_settings=len(m.get("settings") or []), rhythm_n=len(m.get("rhythm") or []), error=m.get("error"),
                              a_word=next((r["words"] for r in d["rules"] if r["supplier_norm"] == "KEDAR PHARMACEUTICAL"), None),
                              b_word=next((r["words"] for r in d["rules"] if r["supplier_norm"] == "GUNINA PHARMACEUTICALS PVT LTD"), None)), default=str))
        return
    if CMD == "settings":
        import porders_s454 as PS                                   # noqa: E402
        from flask import Flask
        app = Flask("walk")
        out = {}
        with app.app_context():
            for key, val in ARG["tries"]:
                r = PS._s470_set(c, {"user": "walk"}, key, val)
                code = r[1] if isinstance(r, tuple) else 200
                out["%s=%s" % (key, val)] = code
        out["model_now"] = OR._setting(c, "order.model", "fixed")
        out["keys_on_card"] = len(PS._s470_keys())
        print(json.dumps(out))
        return
    print(json.dumps(dict(error="unknown command %s" % CMD)))


if __name__ == "__main__":
    main()
