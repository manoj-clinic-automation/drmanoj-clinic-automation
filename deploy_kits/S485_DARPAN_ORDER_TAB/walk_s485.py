#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s485.py -- kit S485_DARPAN_ORDER_TAB: the walk (the brief's section 3), on the server, on scratch copies only.

    python -B walk_s485.py --work /tmp/... --fin-new DIR --fin-old DIR --db scratch_finance.db --adb scratch_assets.db
                           --spine scratch_spine.db --duty-map FILE

  fin-new / fin-old   scratch copies of /root/finance (the *.py, *.html, *.json, *.sql, finance_ui, spine/*.py and spine/*.json):
                      NEW carries the six built files, OLD is the box as it is.
  db / adb / spine    backup-API copies of finance.db, assets.db and the spine -- each probe works on its OWN copies of them.

Each side runs in its own process: the finance app itself (finance_app.app's test client; FINANCE_ALLOW_HEADER_AUTH=1 with X-Clinic-User /
X-Clinic-Role, so unit_role decides who may do what, as on the box), ORDER_PUSH_STUB for notices, ORDER_CLOCK for the hour. The scratch
day is TODAY: the copy's own proposals of today are set aside and the six real proposal rows of 03-Oct are copied in as today's, open.
Sections 1-8 and 10 are here; section 9's reading of the rendered page by eye is done at build time (the report), its machine half here.
Nothing is imported from inside deploy_kits (CLAUDE.md rule 11).
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from urllib.parse import quote

TAG = "W485JSON "
SRC_DAY = "2026-10-03"                    # the six real proposal rows the scratch day is made of
ROLE = {"darpan": "staff", "manoj": "doctor", "shavez": "manager", "shivani": "staff", "alisha": "staff", "bhati": "staff"}
KAL = "/finance/darpan/kal"
API = KAL + "/api/order"
WORDS = ("आज का ऑर्डर", "सप्लायर", "दवा", "का दिन", "बजे आएगी।", "आज कोई ऑर्डर नहीं बनता।", "सब पक्का — रिसेप्शन ऑर्डर करेगी।", "आज का दिन", "शेल्फ", "दिन", "खत्म",
         "पत्ता", "नग", "नहीं चाहिए", "इस बार नहीं", "वापस लो", "जोड़ी", "पक्का", "✓ पक्का — रिसेप्शन को गया", "+ दवा जोड़ो", "सब पक्का", "दवा जोड़ो",
         "नाम के पहले 3 अक्षर", "जैसे मार्ग में लिखते हैं", "सप्लायर चुनिए", "बंद करो", "कल के ऑर्डर — क्या हुआ", "अभी मार्ग की शीट से ऑर्डर हो रहा है",
         "सूची अभी नहीं खुली — थोड़ी देर में फिर देखिए", "Darpan ने पक्का किया", "ऑर्डर हो गया", "माल आया ✓", "अभी नहीं आया", "फ़ोन नहीं उठा — रिसेप्शन फिर करेगी")
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + re.sub(r"\d{10,}", "##########", str(got))[:700] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


# ============================================================================================================================ the probe
def probe():
    FIN, WORK, SIDE = os.environ["FINDIR"], os.environ["WORKDIR"], os.environ["SIDE"]
    NEW = SIDE == "new"
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import order_rules as OR                                            # noqa: E402
    import order_sheet as OS                                            # noqa: E402
    import purchase_app as pa                                           # noqa: E402
    assert OR.__file__.startswith(FIN) and OS.__file__.startswith(FIN) and fa.__file__.startswith(FIN), (OR.__file__, fa.__file__)
    DB = os.environ["FINANCE_DB"]
    today = OR._today()
    T = today.isoformat()
    out = dict(side=SIDE, today=T)
    cl = fa.app.test_client()

    def H(user):
        return {"X-Clinic-User": user, "X-Clinic-Role": ROLE[user]}

    def get(path, user="darpan"):
        r = cl.get(path, headers=H(user))
        try:
            j = r.get_json(silent=True)
        except Exception:                                               # noqa: BLE001
            j = None
        return r.status_code, j, (r.get_data(as_text=True) if j is None else "")

    def post(path, body, user="darpan"):
        r = cl.post(path, json=body, headers=H(user))
        return r.status_code, (r.get_json(silent=True) or {})

    def conn(path=DB):
        c = sqlite3.connect(path, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def sheet_back(c, sid):
        """One line of the Marg sheet is 'still to be ordered' (the walk's own: found by its id) -- the Marg-sheet road's card."""
        c.execute("UPDATE order_sheet_line SET state='to_order', order_id=NULL, line_date=?, marg_date=NULL, marg_bill=NULL, marg_seen_at=NULL, lapsed_at=NULL, "
                  "updated_at=? WHERE id=?", (T, T + "T09:00:00", sid))
        c.commit()

    def setup(c, source):
        """The scratch day: today's own proposals set aside, the six rows of 03-Oct copied in as today's, open; one order-sheet line put
        back 'to_order' (the Marg sheet road's own card); the source set."""
        OR.ensure(c)
        OS.ensure(c)
        c.execute("DELETE FROM order_proposal WHERE day=?", (T,))
        rows = c.execute("SELECT supplier_norm, vendor, kind, lines, total_p, reason FROM order_proposal WHERE day=? ORDER BY id", (SRC_DAY,)).fetchall()
        for r in rows:
            c.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at) VALUES (?,?,?,?,?,?,?,?,?)",
                      (T, r[0], r[1], r[2], "open", r[3], r[4], r[5], T + "T09:00:07"))
        c.execute("DELETE FROM order_notice WHERE day=?", (T,))
        mine = [r[0] for r in rows] + [OR._ortho_norm(c)]
        sl = c.execute("SELECT id, supplier_norm, item FROM order_sheet_line WHERE state IN ('ordered','to_order') AND supplier_norm NOT IN (%s) ORDER BY id DESC LIMIT 1"
                       % ",".join("?" * len(mine)), mine).fetchone()
        if sl:
            sheet_back(c, sl[0])
        c.execute("INSERT INTO setting (key, value, note) VALUES ('order.source', ?, 'W485') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (source,))
        c.execute("DELETE FROM purchase_order WHERE status='draft' AND order_src='s454'")
        c.commit()
        return len(rows), (dict(sl) if sl else None)

    def src(c, v):
        c.execute("UPDATE setting SET value=? WHERE key='order.source'", (v,))
        c.commit()

    def prop(c, sn, day=None):
        r = c.execute("SELECT * FROM order_proposal WHERE day=? AND supplier_norm=? ORDER BY id", (day or T, sn)).fetchall()
        return [dict(x, lines=json.loads(x["lines"] or "[]")) for x in r]

    def cards(user="shivani"):
        """reception's 'Order karna hai' page: the supplier cards it draws, and its 'whose list' heading."""
        r = cl.get("/finance/porders/s454/order?all=1", headers=H(user))
        h = r.get_data(as_text=True)
        import html as _h                                               # noqa: PLC0415
        m = re.search(r'id="whose">([^<]*)<', h)
        return dict(code=r.status_code, sns=sorted(set(_h.unescape(x) for x in re.findall(r'<div class="card" data-sn="([^"]*)"', h))),
                    whose=_h.unescape(m.group(1)) if m else "")

    def sup_lines(sn, user="shivani"):
        r = cl.get("/finance/porders/s454/order/" + quote(sn, safe=""), headers=H(user))
        import html as _h                                               # noqa: PLC0415
        return [_h.unescape(x) for x in re.findall(r'<div class="li"><span class="i">([^<]*)</span>', r.get_data(as_text=True))]

    def edits(c, sn=None, item=None):
        q, a = "SELECT action, item, qty, by FROM order_darpan_edit WHERE day=?", [T]
        if sn:
            q, a = q + " AND supplier_norm=?", a + [sn]
        if item is not None:
            q, a = q + " AND item=?", a + [item]
        try:
            return [tuple(r) for r in c.execute(q + " ORDER BY id", a)]
        except sqlite3.Error:
            return None

    con = conn()
    n6, sheet_line = setup(con, "marg_sheet")
    ortho = OR._ortho_norm(con)
    out.update(rows6=n6, sheet_line=sheet_line and sheet_line["supplier_norm"], ortho=ortho)
    KED, SHI, JAN, MAN, AAP, DEE = ("KEDAR PHARMACEUTICAL", "SHIVAAZ FORMULATIONS", "JANTA PHARMACEUTICALS", "MANNAT PHARMA", "A.A. PHARMACEUTICALS", "DEEPAM PHARMA")

    # ---- 10 (first: nothing touched yet)  कल का हिसाब as it is, on the Marg-sheet source
    yest = (today - dt.timedelta(days=1)).isoformat()
    code, j, _t = get(KAL + "/api/day?date=" + yest)
    out["api_day"] = dict(code=code, json=json.dumps(j, sort_keys=True, ensure_ascii=False))
    r = cl.get(KAL, headers=H("darpan"))
    page = r.get_data(as_text=True)
    out["page"] = dict(code=r.status_code, has_tab='id="tabOrder"' in page, viewport='name="viewport" content="width=device-width, initial-scale=1"' in page,
                       words_missing=[w for w in WORDS if w not in page], pad="#order{padding-bottom:96px}" in page,
                       owner_reads='ro=OWNER_RO||j.me==="owner"' in page and "OOPEN[sn]=open||ro" in page,
                       thumb=page.count("min-height:44px") >= 3 and "body.otab #msg{bottom:66px}" in page and ".oln.held .oit{opacity" in page
                       and ".ochips .btn.sm{margin:10px" in page and "if(this.isConnected)OOPEN" in page and 'if(j){OOPEN[sn]=false; renderOrder();' in page,
                       fixed_bar="#obar{position:fixed" in page, latin_in_tab=sorted(set(re.findall(r">([A-Za-z][A-Za-z ]{3,})<", page[page.find('id="order"'):page.find('id="msg"')] if 'id="order"' in page else ""))))
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    marks = {}
    for du in dm.get("duties") or []:
        if du.get("person") == "darpan" and du.get("door") == KAL:
            marks[du["id"]] = (du.get("door_marker") or "") in page
    out["markers"] = marks
    # ---- 8 (first half)  on the Marg-sheet source the tab is read-only and says so; reception's cards are the sheet's
    os.environ["ORDER_CLOCK"] = "09:31"
    code, j, _t = get(API)
    out["fallback_before"] = dict(code=code, source=(j or {}).get("source"), editable=(j or {}).get("editable"), n=(j or {}).get("n_suppliers"), cards=cards())
    if NEW:
        code, jj = post(API + "/hold", dict(pid=prop(con, KED)[0]["id"], item="PATOPAN DSR", hold=True))
        out["fallback_before"]["tap"] = (code, jj.get("error"), jj.get("message"))

    OR._set_setting(con, "order.source", "darpan", "W485")
    con.commit()
    out["source_read"] = OS.source(con)

    # ---- 1  the door
    door = {}
    for u in ("darpan", "manoj", "shavez", "shivani", "alisha", "bhati"):
        door[u] = dict(page=cl.get(KAL, headers=H(u)).status_code, api=cl.get(API, headers=H(u)).status_code)
    out["door"] = door
    if not NEW:
        # the OLD file has no tab: the rest of the OLD probe is the controls the brief names
        con.execute("UPDATE order_proposal SET status='darpan_ok' WHERE day=? AND supplier_norm=?", (T, KED))
        con.commit()
        out["old_cards_on_darpan"] = cards()                            # the unknown value falls back to the Marg sheet's lines
        con.execute("UPDATE order_proposal SET status='open' WHERE day=? AND supplier_norm=?", (T, KED))
        p = prop(con, SHI)[0]
        for l in p["lines"]:
            if l["item"] == "DEFVAX 6":
                l["held"] = True
        con.execute("UPDATE order_proposal SET lines=? WHERE id=?", (json.dumps(p["lines"], ensure_ascii=False), p["id"]))
        con.commit()
    else:
        # ---- 2  the list
        os.environ["ORDER_CLOCK"] = "09:00"
        _c, j0, _t = get(API)
        os.environ["ORDER_CLOCK"] = "09:31"
        _c, j1, _t = get(API)
        flat = {l["item"]: l for b in j1["suppliers"] for l in b["lines"]}
        out["list"] = dict(at0900=dict(opened=j0["opened"], n=len(j0["suppliers"]), list_time=j0["list_time"]),
                           at0931=dict(opened=j1["opened"], source=j1["source"], editable=j1["editable"], n_suppliers=j1["n_suppliers"], n_lines=j1["n_lines"],
                                       blocks=[(b["supplier_norm"], b["display"], b["status"], len(b["lines"]), b["order_day"]) for b in j1["suppliers"]],
                                       patopan=flat.get("PATOPAN DSR"), mecovixr=flat.get("MECOVIXR FORTE INJ"), all_pakka=j1["all_pakka"],
                                       keys=sorted(j1.keys()), line_keys=sorted(flat["PATOPAN DSR"].keys())))
        # ---- 1 (the owner may tap)
        kp = prop(con, AAP)[0]["id"]
        c1, _j = post(API + "/hold", dict(pid=kp, item="XYCAL K2", hold=True), "manoj")
        c2, _j = post(API + "/hold", dict(pid=kp, item="XYCAL K2", hold=False), "manoj")
        out["owner_taps"] = (c1, c2, edits(con, AAP, "XYCAL K2"))
        out["viewer_tap"] = [post(API + "/pakka", dict(supplier_norm=AAP), u)[0] for u in ("shavez", "shivani", "bhati")]
        # ---- 3  hold / unhold / qty
        pid = prop(con, KED)[0]["id"]
        e0 = len(edits(con, KED))
        _c, jh = post(API + "/hold", dict(pid=pid, item="PATOPAN DSR", hold=True))
        held_line = next(l for l in prop(con, KED)[0]["lines"] if l["item"] == "PATOPAN DSR")
        _c, ju = post(API + "/hold", dict(pid=pid, item="PATOPAN DSR", hold=False))
        back_line = next(l for l in prop(con, KED)[0]["lines"] if l["item"] == "PATOPAN DSR")
        steps = []
        for d_ in (-1, -1, -1, 1, 1, 1, 1):
            _c, jq = post(API + "/qty", dict(pid=pid, item="PATOPAN DSR", dir=d_))
            steps.append(next(l["qty"] for b in jq["suppliers"] for l in b["lines"] if l["item"] == "PATOPAN DSR"))
        jp = prop(con, JAN)[0]
        usteps = []
        for d_ in (-1, -1, 1):
            _c, jq = post(API + "/qty", dict(pid=jp["id"], item="NUPTACH 200", dir=d_))
            usteps.append(next(l["qty"] for b in jq["suppliers"] for l in b["lines"] if l["item"] == "NUPTACH 200"))
        out["hold"] = dict(held_in_api=[l["held"] for b in jh["suppliers"] for l in b["lines"] if l["item"] == "PATOPAN DSR"], held_in_db=bool(held_line.get("held")),
                           back_in_db=("held" not in back_line), strip_steps=steps, unit_steps=usteps,
                           edit_rows=edits(con, KED)[e0:], engine_qty_kept=next(l for l in prop(con, KED)[0]["lines"] if l["item"] == "PATOPAN DSR").get("qty_engine"))
        # ---- 4  add
        _c, ji, _t = get(API + "/items?q=ROS")
        ros = next((h for h in (ji or {}).get("hits", []) if h["item"] == "ROSIKA FORTE"), None)
        _as_on, snap, pace, purch, _tr, _or = OR._s470_inputs(con, today)
        ros_e = purch.get(pa.norm("ROSIKA FORTE")) or {}
        ca, ja = post(API + "/add", dict(item="ROSIKA FORTE"))
        ros_rows = prop(con, ros_e.get("vendor") or DEE)
        ked_items = {l["item"] for l in prop(con, KED)[0]["lines"]}
        usual = next((s_["item"] for k, s_ in sorted(snap.items()) if (purch.get(k) or {}).get("vendor") == KED and (purch.get(k) or {}).get("lot")
                      and s_["item"] not in ked_items), None)
        cu, ju2 = post(API + "/add", dict(item=usual)) if usual else (0, {})
        ue = purch.get(pa.norm(usual)) if usual else {}
        ul = next((l for l in prop(con, KED)[0]["lines"] if l["item"] == usual), None)
        never = next((s_["item"] for k, s_ in sorted(snap.items()) if k not in purch and k not in _or and int(s_.get("pack_size") or 1) > 1), None)
        cn0, jn0 = post(API + "/add", dict(item=never))                 # no supplier known, none tapped
        cn1, jn1 = post(API + "/add", dict(item=never, supplier_norm=MAN))
        nl = next((l for l in prop(con, MAN)[0]["lines"] if l["item"] == never), None)
        cd, jd = post(API + "/add", dict(item=never, supplier_norm=MAN))  # a second time
        cx, jx = post(API + "/add", dict(item="W485 NO SUCH MEDICINE"))
        out["add"] = dict(q_hit=ros, q_n=len((ji or {}).get("hits", [])), q_short=len((get(API + "/items?q=RO")[1] or {}).get("hits", [1])), chips=len((ji or {}).get("chips", [])),
                          ros=dict(code=ca, vendor=ros_e.get("vendor"), lot_units=ros_e.get("lot"), pack=(snap.get(pa.norm("ROSIKA FORTE")) or {}).get("pack_size"),
                                   rows=[(r_["kind"], r_["status"], [(l["item"], l["qty"], l.get("added"), l.get("why")) for l in r_["lines"]]) for r_ in ros_rows]),
                          usual=dict(item=usual, code=cu, lot_units=(ue or {}).get("lot"), pack=(snap.get(pa.norm(usual)) or {}).get("pack_size") if usual else None,
                                     line=ul and dict(qty=ul["qty"], unit=ul["unit"], added=ul.get("added"), vendor_norm=ul.get("vendor_norm"))),
                          never=dict(item=never, no_chip=(cn0, jn0.get("error")), code=cn1, line=nl and dict(qty=nl["qty"], unit=nl["unit"], why=nl.get("why"), added=nl.get("added")),
                                     again=(cd, jd.get("error")), unknown=(cx, jx.get("error"))),
                          edit_rows=[e for e in edits(con) if e[0] == "add"])
        # ---- 6  the notice (while proposals are still open)
        stub = os.environ["ORDER_PUSH_STUB"]
        open(stub, "w").close()
        os.environ.pop("ORDER_TICK", None)
        t0930 = dt.datetime(today.year, today.month, today.day, 9, 30)
        r1 = OR.tick(con, now=t0930)
        pushed = [json.loads(x) for x in open(stub, encoding="utf-8").read().splitlines() if x.strip()]
        r2 = OR.tick(con, now=t0930 + dt.timedelta(minutes=10))
        os.environ["ORDER_TICK"] = "0930"
        r3 = OR.tick(con, now=t0930 + dt.timedelta(minutes=10))
        os.environ.pop("ORDER_TICK", None)
        pushed2 = [x for x in open(stub, encoding="utf-8").read().splitlines() if x.strip()]
        out["notice"] = dict(first=dict(slot=r1.get("slot"), notice=r1.get("notice")), pushed=[(p_["user"], p_["payload"].get("body"), p_["payload"].get("url"), p_["payload"].get("title")) for p_ in pushed],
                             second=dict(slot=r2.get("slot"), n_pushed=len(pushed2)), forced_again=(r3.get("notice") or {}).get("already"),
                             row=[tuple(r_) for r_ in con.execute("SELECT slot, text, sent FROM order_notice WHERE day=? AND slot='0930'", (T,))])
        # ---- 5  पक्का: Kedar (a held line, an added one), Janta (untouched)
        post(API + "/hold", dict(pid=pid, item="PATOPAN DSR", hold=True))
        before_cards = cards()
        cp, jk = post(API + "/pakka", dict(supplier_norm=KED))
        kb = next(b for b in jk["suppliers"] if b["supplier_norm"] == KED)
        after_cards = cards()
        ked_page = sup_lines(KED)
        ent = {e["sn"]: [l["item"] for l in e["lines"]] for e in OS.entries(con)}
        cp2, _j = post(API + "/pakka", dict(supplier_norm=JAN))
        co, jo = post("/finance/porders/api/s454/ordered", dict(sn=JAN), "shivani")
        po_ = con.execute("SELECT * FROM purchase_order WHERE id=?", (jo.get("order_id") or 0,)).fetchone()
        pl_ = [tuple(r_) for r_ in con.execute("SELECT item, packs, pack_size, units, rate_p FROM purchase_order_line WHERE order_id=? ORDER BY id", (jo.get("order_id") or 0,))]
        jr = prop(con, JAN)[0]
        _c, jv, _t = get(API)
        jb = next(b for b in jv["suppliers"] if b["supplier_norm"] == JAN)
        out["pakka"] = dict(code=cp, kedar=dict(status=kb["status"], pakka_at=kb["pakka_at"], db=prop(con, KED)[0]["status"], edit=[e for e in edits(con, KED) if e[0] == "pakka"]),
                            cards_before=before_cards, cards_after=after_cards, kedar_page=ked_page, entries=ent, tyro="TYRO BR" in ked_page, usual=usual,
                            ordered=dict(code=co, ok=jo.get("ok"), order=po_ and {k: po_[k] for k in ("vendor", "status", "total_p", "section", "supplier_norm", "ext_ref", "order_src", "order_via", "note", "created_by", "sent_by")},
                                         lines=pl_, proposal=dict(status=jr["status"], sent_by=jr["sent_by"], sent_order_id_is_order=(jr["sent_order_id"] == jo.get("order_id")), sent_at=bool(jr["sent_at"])),
                                         tab=dict(status=jb["status"], sent_at=bool(jb["sent_at"]))),
                            cards_after_order=cards())
        # the same order by the system road, on a copy of its own (field for field)
        twin = os.path.join(WORK, "w485_system_twin.db")
        copydb(os.environ["W485_DB0"], twin)
        tc = conn(twin)
        setup(tc, "system")
        tb, tcode = OS.order_supplier(tc, "shivani", JAN, "call")
        to_ = tc.execute("SELECT * FROM purchase_order WHERE id=?", (tb.get("order_id") or 0,)).fetchone()
        tr = prop(tc, JAN)[0]
        out["twin"] = dict(code=tcode, order=to_ and {k: to_[k] for k in ("vendor", "status", "total_p", "section", "supplier_norm", "ext_ref", "order_src", "order_via", "note", "created_by", "sent_by")},
                           lines=[tuple(r_) for r_ in tc.execute("SELECT item, packs, pack_size, units, rate_p FROM purchase_order_line WHERE order_id=? ORDER BY id", (tb.get("order_id") or 0,))],
                           proposal=dict(status=tr["status"], sent_by=tr["sent_by"], sent_order_id_is_order=(tr["sent_order_id"] == tb.get("order_id")), sent_at=bool(tr["sent_at"])))
        tc.close()
        # a held line, and send_proposal (the old wa.me road): what it would send
        sp_ = prop(con, SHI)[0]
        post(API + "/hold", dict(pid=sp_["id"], item="DEFVAX 6", hold=True))
    # ---- 3 / 5 (both sides)  send_proposal's own lines, captured (no order is made: purchase_app._staff_send is stood in for)
    sent_lines = []

    def capture(c_, u_, b_):
        sent_lines.append([l["item"] for l in b_.get("lines") or []])
        from flask import jsonify                                       # noqa: PLC0415
        return jsonify(ok=False, error="w485_captured"), 409
    real_send = pa._staff_send
    pa._staff_send = capture
    with fa.app.test_request_context("/"):
        body, code = OR.send_proposal(con, dict(user="shivani"), prop(con, SHI)[0]["id"], None)
    pa._staff_send = real_send
    out["send_proposal"] = dict(code=code, error=body.get("error"), lines=sent_lines[0] if sent_lines else None)
    if NEW:
        # सब पक्का
        ca_, jall = post(API + "/pakka", dict(all=True))
        out["pakka_all"] = dict(code=ca_, all_pakka=jall.get("all_pakka"), statuses=sorted({b["status"] for b in jall.get("suppliers", [])}), pakka=jall.get("pakka"))
        os.environ["ORDER_TICK"] = "0930"
        con.execute("DELETE FROM order_notice WHERE day=? AND slot='0930'", (T,))
        con.commit()
        r4 = OR.tick(con, now=dt.datetime(today.year, today.month, today.day, 9, 30))
        os.environ.pop("ORDER_TICK", None)
        out["notice"]["none_open"] = r4.get("notice")
        # the duty map's new row, on this copy
        nd = next((du for du in dm["duties"] if du["id"] == "darpan.order_review"), None)
        if nd:
            con.execute("UPDATE order_proposal SET status='open' WHERE day=? AND supplier_norm=?", (T, AAP))
            con.commit()
            rr = con.execute(nd["due_sql"]).fetchone()
            now_hm = dt.datetime.now().strftime("%H:%M")
            src(con, "marg_sheet")
            rr2 = con.execute(nd["due_sql"]).fetchone()
            src(con, "darpan")
            out["duty"] = dict(row={k: nd.get(k) for k in ("id", "person", "tile", "door", "door_marker", "allowed_days", "coded")}, due=tuple(rr), due_on_sheet=tuple(rr2),
                               clock=now_hm, list_time=OR.darpan_list_time(con), marker_on_page=(nd.get("door_marker") or "~") in page)
            con.execute("UPDATE order_proposal SET status='darpan_ok' WHERE day=? AND supplier_norm=?", (T, AAP))
            con.commit()
    # ---- 6 (both sides)  the 09:30 tick on the Marg-sheet source; the 09:00 slot on each source, each on a copy of its own
    src(con, "marg_sheet")
    os.environ["ORDER_TICK"] = "0930"
    r5 = OR.tick(con, now=dt.datetime(today.year, today.month, today.day, 9, 30))
    os.environ.pop("ORDER_TICK", None)
    out.setdefault("notice", {})["on_sheet"] = dict(slot=r5.get("slot"), notice=r5.get("notice"))
    nine = {}
    for s_ in ("marg_sheet", "system", "darpan"):
        p9 = os.path.join(WORK, "w485_0900_%s.db" % s_)
        copydb(os.environ["W485_DB0"], p9)
        c9 = conn(p9)
        OR.ensure(c9)
        c9.execute("DELETE FROM order_notice WHERE day=?", (T,))
        c9.execute("INSERT INTO setting (key, value, note) VALUES ('order.source', ?, 'W485') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (s_,))
        c9.commit()
        stub9 = os.environ["ORDER_PUSH_STUB"] + "." + s_
        open(stub9, "w").close()
        os.environ["ORDER_PUSH_STUB"], keep = stub9, os.environ["ORDER_PUSH_STUB"]
        r9 = OR.tick(c9, now=dt.datetime(today.year, today.month, today.day, 9, 0))
        os.environ["ORDER_PUSH_STUB"] = keep
        n9 = r9.get("notice") or {}
        nine[s_] = dict(slot=r9.get("slot"), silent=n9.get("silent"), why=n9.get("why"), text=n9.get("text"), to=sorted((n9.get("sent") or {}).keys()),
                        pushed=len([x for x in open(stub9, encoding="utf-8").read().splitlines() if x.strip()]))
        c9.close()
    out["nine"] = nine
    # ---- 7  nightly: yesterday's rows, the walk's own supplier
    src(con, "darpan")
    yl = json.dumps([dict(item="W485 ITEM", qty=10, unit="strip", pack_size=10, packing="1*10", rate_p=100, value_p=1000)])
    for sn_, st_ in (("W485 SUPPLIER OK", "darpan_ok"), ("W485 SUPPLIER OPEN", "open"), ("W485 SUPPLIER SENT", "sent")):
        con.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (yest, sn_, sn_, "fixed", st_, yl, 1000, "W485", yest + "T09:00:00"))
    con.commit()
    OR.nightly(con, today)
    ng = {r_[0]: (r_[1], r_[2]) for r_ in con.execute("SELECT supplier_norm, status, merged_into FROM order_proposal WHERE day=? AND supplier_norm LIKE 'W485 %'", (yest,))}
    carried = {}
    for sn_, (st_, mi) in ng.items():
        carried[sn_] = [x[0] for x in con.execute("SELECT day FROM order_proposal WHERE supplier_norm=? AND status='merged' AND merged_into=? ORDER BY day", (sn_, mi or ""))]
    out["nightly"] = dict(rows=ng, carried=carried, needs_you=[x["text"] for x in OR.needs_you_lines(con) if "W485" in x.get("text", "")])
    # ---- 8 (second half)  back to the Marg sheet
    if sheet_line:
        sheet_back(con, sheet_line["id"])                               # the ticks above ran the sheet's own passes; the walk's line is put back
    src(con, "marg_sheet")
    os.environ["ORDER_CLOCK"] = "09:31"
    code, j, _t = get(API)
    fb = dict(code=code, source=(j or {}).get("source"), editable=(j or {}).get("editable"), n=(j or {}).get("n_suppliers"), cards=cards(),
              summary_keys=sorted((OR.day_summary(con) or {}).keys()))
    if NEW:
        any_open = next((p_ for p_ in con.execute("SELECT id, lines FROM order_proposal WHERE day=? ORDER BY id", (T,))), None)
        c_, j_ = post(API + "/pakka", dict(all=True))
        fb["tap"] = (c_, j_.get("error"), j_.get("message"))
    out["fallback_after"] = fb
    src(con, "darpan")
    out["summary_darpan"] = OR.day_summary(con)
    ro.close()
    con.close()
    print(TAG + json.dumps(out, default=str, ensure_ascii=False))


# ============================================================================================================================ the walk
def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe":
        return probe()
    ap = argparse.ArgumentParser()
    for k in ("--work", "--fin-new", "--fin-old", "--db", "--adb", "--spine", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    W = os.path.abspath(a.work)
    assert W.startswith("/tmp/"), "refusing a non-scratch path: %s" % W
    os.makedirs(W)

    def run(side, fin):
        wd = os.path.join(W, side)
        os.makedirs(os.path.join(wd, "nosso"))
        os.makedirs(os.path.join(wd, "nomarg"))
        dbp, adbp, spp = [os.path.join(wd, "w485_%s.db" % x) for x in ("fin", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W485_DB0=a.db, FINANCE_ALLOW_HEADER_AUTH="1",
                   FINANCE_SSO_DIR=os.path.join(wd, "nosso"), MARG_INGEST_DIR=os.path.join(wd, "nomarg"), ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"),
                   DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, RING_PORTAL_DIR=os.path.join(wd, "nosso"))
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE", "FINANCE_CRON_TOKEN"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           universal_newlines=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s probe did not finish (exit %s); its last lines:" % (side, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + re.sub(r"\d{10,}", "##########", l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    NW, OL = run("new", a.fin_new), run("old", a.fin_old)
    if not check("both probes ran to the end (NEW = the box + S485, OLD = the box as it is), each on its own copies; the scratch day is today (%s) "
                 "with the six real proposal rows of %s copied in, open" % ((NW or {}).get("today"), SRC_DAY),
                 NW is not None and OL is not None and NW["rows6"] == 6 and OL["rows6"] == 6):
        return finish()
    KED, SHI, JAN, MAN, AAP = ("KEDAR PHARMACEUTICAL", "SHIVAAZ FORMULATIONS", "JANTA PHARMACEUTICALS", "MANNAT PHARMA", "A.A. PHARMACEUTICALS")
    ortho, sheet_sn = NW["ortho"], NW["sheet_line"]
    six = sorted([KED, SHI, JAN, MAN, AAP, "YOGENDRA AGENCIES"])
    prop_cards = lambda c: sorted(x for x in c["sns"] if x in six and x != sheet_sn)

    print("-- 1  the door")
    d, do = NW["door"], OL["door"]
    check("darpan (maker on medical -> staff): the page 200, the tab's API 200; manoj (checker -> owner): 200 / 200",
          d["darpan"] == dict(page=200, api=200) and d["manoj"] == dict(page=200, api=200), (d["darpan"], d["manoj"]))
    check("shavez, shivani, alisha (viewer, no recipient party): the page itself is 403 as today, and the API with it; a login with no role on "
          "the unit (bhati) never reaches the page -- the app's own gate turns it away (%s), as today" % d["bhati"]["page"],
          all(d[u] == dict(page=403, api=403) for u in ("shavez", "shivani", "alisha")) and d["bhati"]["page"] in (302, 403) and d["bhati"]["api"] in (302, 403)
          and all(d[u]["page"] == do[u]["page"] for u in d), {u: d[u] for u in ("shavez", "shivani", "alisha", "bhati")})
    check("the owner may tap (hold, then take back: 200, 200, two audit rows by manoj); a viewer's or a stranger's tap is refused (%s)" % NW["viewer_tap"],
          NW["owner_taps"][:2] == [200, 200] and [e[0] for e in NW["owner_taps"][2]] == ["hold", "unhold"] and {e[3] for e in NW["owner_taps"][2]} == {"manoj"}
          and NW["viewer_tap"][:2] == [403, 403] and NW["viewer_tap"][2] in (302, 403), (NW["owner_taps"], NW["viewer_tap"]))
    check("negative control, OLD darpan_kal.py: api/order is 404 for Darpan (the page itself 200)", do["darpan"] == dict(page=200, api=404), do["darpan"])
    check("order_sheet.source() reads the new value: NEW 'darpan'; OLD falls back to 'marg_sheet' for it", NW["source_read"] == "darpan" and OL["source_read"] == "marg_sheet")

    print("-- 2  the list")
    l0, l1 = NW["list"]["at0900"], NW["list"]["at0931"]
    check("before the list time (the clock at 09:00, order.darpan_list_time %s): opened false, no supplier shown" % l0["list_time"],
          l0["opened"] is False and l0["n"] == 0 and l0["list_time"] == "09:30")
    check("at 09:31: opened true, source darpan, editable; 6 blocks, 10 lines -- %s" % [(b[1], b[3]) for b in l1["blocks"]],
          l1["opened"] is True and l1["source"] == "darpan" and l1["editable"] is True and l1["n_suppliers"] == 6 and l1["n_lines"] == 10
          and sorted(b[0] for b in l1["blocks"]) == six and all(b[2] == "open" for b in l1["blocks"]) and l1["all_pakka"] is False)
    pt, mv = l1["patopan"], l1["mecovixr"]
    check("PATOPAN DSR (236 of 1*10): on_hand_text '23:6', 20 strips, ~4 days left; MECOVIXR FORTE INJ (a unit item): on_hand_text '11', unit",
          pt["on_hand_text"] == "23:6" and pt["unit"] == "strip" and pt["qty"] == 20 and pt["days_left"] == 4 and pt["packing"] == "1*10"
          and mv["on_hand_text"] == "11" and mv["unit"] == "unit" and mv["qty"] == 11, (pt, mv))
    check("the payload's shape: %s; a line: %s" % (l1["keys"], l1["line_keys"]),
          {"date", "list_time", "opened", "source", "suppliers", "yesterday"} <= set(l1["keys"])
          and {"item", "packing", "unit", "qty", "on_hand_text", "cover_days", "held", "added", "why"} <= set(l1["line_keys"]))

    print("-- 3  hold / unhold / quantity")
    h = NW["hold"]
    check("नहीं चाहिए on PATOPAN DSR: held in the answer and in the proposal's own lines; वापस लो: the flag is gone",
          h["held_in_api"] == [True] and h["held_in_db"] is True and h["back_in_db"] is True)
    check("− − − + + + + from 20 strips: %s (10 at 20 or more, else 5, never below 5); a unit item from 2: − − + -> %s (never below 1)"
          % (h["strip_steps"], h["unit_steps"]), h["strip_steps"] == [10, 5, 5, 10, 15, 20, 30] and h["unit_steps"] == [1, 1, 2])
    check("every tap is one order_darpan_edit row carrying who: %s; the engine's own figure is kept beside his (qty_engine %s)"
          % ([(e[0], e[2]) for e in h["edit_rows"]], h["engine_qty_kept"]),
          [e[0] for e in h["edit_rows"]] == ["hold", "unhold"] + ["qty"] * 7 and {e[3] for e in h["edit_rows"]} == {"darpan"} and h["engine_qty_kept"] == 20)
    sp_n, sp_o = NW["send_proposal"], OL["send_proposal"]
    check("a held line (DEFVAX 6, Shivaaz) is absent from send_proposal's lines: NEW would send %s" % sp_n["lines"],
          sp_n["lines"] is not None and "DEFVAX 6" not in sp_n["lines"] and len(sp_n["lines"]) == 2, sp_n)
    check("negative control, OLD order_rules.py: the same held line IS sent (%s)" % sp_o["lines"], sp_o["lines"] is not None and "DEFVAX 6" in sp_o["lines"], sp_o)

    print("-- 4  add")
    ad = NW["add"]
    r = ad["ros"]
    check("api/order/items?q=ROS: ROSIKA FORTE among %d hits, with its usual supplier and lot (%s); two letters return nothing; %d supplier chips"
          % (ad["q_n"], ad["q_hit"], ad["chips"]), bool(ad["q_hit"]) and ad["q_hit"]["supplier_norm"] == r["vendor"] and ad["q_hit"]["unit"] == "strip"
          and ad["q_short"] == 0 and ad["chips"] >= 6, ad["q_hit"])
    lot_strips = -(-int(r["lot_units"] or 0) // int(r["pack"] or 1)) if r["lot_units"] else None
    check("adding ROSIKA FORTE: its usual supplier %s had no proposal today -> a row kind 'darpan', open, is made for it; usual lot %s units of "
          "1*%s -> %s strips shown; added, why ['Darpan ne joda']" % (r["vendor"], r["lot_units"], r["pack"], lot_strips),
          r["code"] == 200 and len(r["rows"]) == 1 and r["rows"][0][0] == "darpan" and r["rows"][0][1] == "open"
          and r["rows"][0][2] == [["ROSIKA FORTE", lot_strips, True, ["Darpan ne joda"]]], r["rows"])
    u = ad["usual"]
    u_strips = (-(-int(u["lot_units"]) // int(u["pack"] or 1))) if u.get("lot_units") else None
    check("adding %s (usually from Kedar, lot %s units of pack %s): it lands in Kedar's open list with %s, added" % (u["item"], u["lot_units"], u["pack"], u_strips),
          bool(u["item"]) and u["code"] == 200 and u["line"] == dict(qty=u_strips, unit="strip" if int(u["pack"] or 1) > 1 else "unit", added=True, vendor_norm=KED), u)
    nv = ad["never"]
    check("adding %s (never bought): with no supplier tapped -> 409 need_supplier; with the Mannat chip -> under Mannat, 10 strips, why "
          "['Darpan ne joda']; a second time -> 409 already; a name not in Marg's list -> 404" % nv["item"],
          bool(nv["item"]) and nv["no_chip"] == [409, "need_supplier"] and nv["code"] == 200 and nv["line"] == dict(qty=10, unit="strip", why=["Darpan ne joda"], added=True)
          and nv["again"] == [409, "already"] and nv["unknown"] == [404, "unknown_item"], nv)
    check("three add rows in order_darpan_edit, by darpan", [e[1] for e in ad["edit_rows"]] == ["ROSIKA FORTE", u["item"], nv["item"]] and {e[3] for e in ad["edit_rows"]} == {"darpan"})

    print("-- 5  पक्का")
    pk = NW["pakka"]
    check("पक्का on Kedar: 200, status darpan_ok in the answer and in the table, pakka_at %s, one audit row" % pk["kedar"]["pakka_at"],
          pk["code"] == 200 and pk["kedar"]["status"] == "darpan_ok" and pk["kedar"]["db"] == "darpan_ok" and re.match(r"^\d\d:\d\d$", pk["kedar"]["pakka_at"] or "")
          and len(pk["kedar"]["edit"]) == 1 and pk["kedar"]["edit"][0][3] == "darpan", pk["kedar"])
    check("reception's 'Order karna hai' (as shivani) on order.source = darpan: NO proposal card before any Pakka (%s); after it exactly Kedar's (%s) "
          "-- heading '%s'" % (prop_cards(pk["cards_before"]), prop_cards(pk["cards_after"]), pk["cards_after"]["whose"]),
          pk["cards_before"]["code"] == 200 and prop_cards(pk["cards_before"]) == [] and prop_cards(pk["cards_after"]) == [KED]
          and pk["cards_after"]["whose"].startswith("Darpan ki pakki list"), (pk["cards_before"]["sns"], pk["cards_after"]["sns"]))
    check("Kedar's card holds its live lines only: the held PATOPAN DSR absent, TYRO BR and the added %s present (%s); entries() agrees"
          % (pk["usual"], pk["kedar_page"]), "PATOPAN DSR" not in pk["kedar_page"] and pk["tyro"] and pk["usual"] in pk["kedar_page"]
          and sorted(pk["entries"].get(KED, [])) == sorted(pk["kedar_page"]) and sheet_sn not in pk["entries"], pk["entries"])
    od, tw = pk["ordered"], NW["twin"]
    check("'Order ho gaya' on Janta (api/s454/ordered, as shivani): make_order writes the purchase_order (%s) and _mark_sources sets the proposal "
          "sent with its order id; the tab shows it" % ((od["order"] and (od["order"]["status"], od["order"]["order_src"], od["order"]["order_via"])),),
          od["code"] == 200 and od["ok"] and od["proposal"] == dict(status="sent", sent_by="shivani", sent_order_id_is_order=True, sent_at=True)
          and od["tab"] == dict(status="sent", sent_at=True) and JAN not in prop_cards(pk["cards_after_order"]), od)
    check("the same rows the system road produces (the same six rows on a copy with order.source = system, the same tap): the order, its "
          "lines and the proposal are equal field for field", tw["code"] == 200 and od["order"] == tw["order"] and od["lines"] == tw["lines"]
          and od["proposal"] == tw["proposal"] and len(od["lines"]) == 2, (od["order"], tw["order"]))
    oc = OL["old_cards_on_darpan"]
    check("negative control, OLD order_sheet.py with order.source = darpan and Kedar's row darpan_ok: reception sees the Marg sheet's lines "
          "(%s) -- the fallback of an unknown value -- and never the proposals" % [x for x in oc["sns"] if x != ortho],
          prop_cards(oc) == [] and sheet_sn in oc["sns"], oc)
    pa_ = NW["pakka_all"]
    check("सब पक्का: every block is pakka or sent, all_pakka true", pa_["code"] == 200 and pa_["all_pakka"] is True and set(pa_["statuses"]) <= {"darpan_ok", "sent"}, pa_)

    print("-- 6  the notice")
    nt = NW["notice"]
    f = nt["first"]["notice"] or {}
    check("tick at 09:30 with source darpan and proposals open: slot 0930, ONE notice, to darpan only -- '%s' -> %s"
          % ((nt["pushed"] or [[None, None, None]])[0][1], (nt["pushed"] or [[None, None, None]])[0][2]),
          nt["first"]["slot"] == "0930" and len(nt["pushed"]) == 1 and nt["pushed"][0][0] == "darpan"
          and nt["pushed"][0][1] == "आज का ऑर्डर तैयार है — कल का हिसाब पेज पर देखिए" and nt["pushed"][0][2] == "/finance/darpan/kal#order"
          and list((f.get("sent") or {}).keys()) == ["darpan"] and len(nt["row"]) == 1, (nt["first"], nt["row"]))
    check("once: the tick at 09:40 sends nothing (slot %s, still 1 push); the slot forced again answers 'already'" % nt["second"]["slot"],
          nt["second"]["slot"] == "none" and nt["second"]["n_pushed"] == 1 and nt["forced_again"] is True)
    check("silent with no open proposal (%s); silent on the Marg-sheet source (%s)" % ((nt["none_open"] or {}).get("why"), (nt["on_sheet"]["notice"] or {}).get("why")),
          (nt["none_open"] or {}).get("silent") is True and (nt["none_open"] or {}).get("why") == "no open proposal"
          and (nt["on_sheet"]["notice"] or {}).get("silent") is True and (nt["on_sheet"]["notice"] or {}).get("why") == "order.source = marg_sheet")
    n9, o9 = NW["nine"], OL["nine"]
    check("the 09:00 slot (each on a copy of its own): on darpan silent, why '%s'; on marg_sheet silent, why '%s' -- the OLD words; on system "
          "the same notice as the OLD file sends, word for word, to the same logins" % (n9["darpan"]["why"], n9["marg_sheet"]["why"]),
          n9["darpan"]["silent"] is True and n9["darpan"]["why"] == "order.source = darpan" and n9["darpan"]["pushed"] == 0
          and n9["marg_sheet"] == o9["marg_sheet"] and n9["marg_sheet"]["why"] == "order.source = marg_sheet"
          and n9["system"] == o9["system"] and bool(n9["system"]["text"]) and n9["system"]["pushed"] >= 1, (n9["system"], o9["system"]))
    check("negative control, OLD order_rules.py: its tick knows no 0930 slot (slot '%s' at 09:30, no notice of that kind); on darpan its 09:00 "
          "why still says marg_sheet" % OL["notice"]["on_sheet"]["slot"], OL["notice"]["on_sheet"]["slot"] != "0930" and o9["darpan"]["why"] == "order.source = marg_sheet")

    print("-- 7  nightly")
    ng, ngo = NW["nightly"], OL["nightly"]
    check("yesterday's rows of the walk's own suppliers: darpan_ok -> %s, open -> %s, sent -> %s; the merged ones are found by the next order "
          "day's 'carried' read" % (ng["rows"]["W485 SUPPLIER OK"], ng["rows"]["W485 SUPPLIER OPEN"], ng["rows"]["W485 SUPPLIER SENT"]),
          ng["rows"]["W485 SUPPLIER OK"][0] == "merged" and ng["rows"]["W485 SUPPLIER OK"] == ng["rows"]["W485 SUPPLIER OPEN"]
          and ng["rows"]["W485 SUPPLIER SENT"] == ["sent", None] and len(ng["carried"]["W485 SUPPLIER OK"]) == 1, ng)
    check("negative control, OLD: a darpan_ok row of yesterday is left as it is (%s), never merged" % ngo["rows"]["W485 SUPPLIER OK"],
          ngo["rows"]["W485 SUPPLIER OK"] == ["darpan_ok", None] and ngo["rows"]["W485 SUPPLIER OPEN"][0] == "merged")

    print("-- 8  the way back to the Marg sheet")
    fb, fa_ = NW["fallback_before"], NW["fallback_after"]
    check("order.source = marg_sheet (before the switch and after going back): reception's cards are the Marg sheet's lines again (%s), no "
          "proposal card; Darpan's tab shows the list read-only (source marg_sheet, editable false, %s blocks) and a tap is refused -- '%s'"
          % ([x for x in fa_["cards"]["sns"] if x != ortho], fa_["n"], fa_["tap"][2]),
          fb["source"] == fa_["source"] == "marg_sheet" and fb["editable"] is False and fa_["editable"] is False and fb["n"] == 6 and (fa_["n"] or 0) >= 6
          and prop_cards(fb["cards"]) == [] and prop_cards(fa_["cards"]) == [] and sheet_sn in fb["cards"]["sns"] and sheet_sn in fa_["cards"]["sns"]
          and fb["tap"][:2] == [409, "not_darpan"] and fa_["tap"][:2] == [409, "not_darpan"] and fa_["tap"][2] == "अभी मार्ग की शीट से ऑर्डर हो रहा है", (fb, fa_["tap"]))
    sd = NW["summary_darpan"]
    check("Darpan's count line on darpan counts open + pakka as still to go: %s" % sd.get("text"), sd.get("ok") and sd["n"] == sd["sent"] + sd["unsent"] and sd["sent"] >= 1)

    print("-- 9  the page (the machine half; the rendered page is read by eye at build time)")
    pg, pgo = NW["page"], OL["page"]
    check("the page carries the tab (id tabOrder), the viewport line, every word of the brief's section 2 in Devanagari (%d checked), the "
          "bottom padding under the fixed bar; nothing between the tab's own tags is a Latin word" % len(WORDS),
          pg["code"] == 200 and pg["has_tab"] and pg["viewport"] and pg["words_missing"] == [] and pg["pad"] and pg["fixed_bar"] and pg["latin_in_tab"] == [],
          (pg["words_missing"], pg["latin_in_tab"]))
    check("found by eye at build time, held here: the owner's view decides 'no buttons' from the answer's own me=owner (not from which fetch "
          "lands first) and opens every block for him; every tap on the tab is 44 px or more, with room between + and नहीं चाहिए and "
          "between the supplier chips; वापस लो is not greyed with its line; the message strip sits above the fixed bar; a block folds "
          "after its पक्का whatever event lands while the tap is in flight",
          pg["owner_reads"] and pg["thumb"], (pg["owner_reads"], pg["thumb"]))
    check("negative control, OLD page: no tab", pgo["has_tab"] is False and "आज का ऑर्डर" in pgo["words_missing"] and not pgo["owner_reads"] and not pgo["thumb"])

    print("-- 10  everything else on कल का हिसाब")
    check("api/day for yesterday, on the same copy before any tap: the same JSON from the NEW file as from the OLD (%d bytes)" % len(NW["api_day"]["json"]),
          NW["api_day"]["code"] == 200 and NW["api_day"]["json"] == OL["api_day"]["json"])
    mk, mko = NW["markers"], OL["markers"]
    old_ids = sorted(k for k in mk if k != "darpan.order_review")
    check("the duty map's existing darpan rows on this page still find their markers (%s), as on the OLD page" % old_ids,
          len(old_ids) >= 3 and all(mk[k] for k in old_ids) and all(mko.get(k) for k in old_ids), mk)
    du = NW.get("duty") or {}
    check("the new row darpan.order_review: its marker '%s' is on the NEW page (not on the OLD); its due_sql on the copy -> %s on darpan with the "
          "list time passed (clock %s, list time %s), %s on the Marg sheet" % ((du.get("row") or {}).get("door_marker"), du.get("due"), du.get("clock"), du.get("list_time"), du.get("due_on_sheet")),
          mk.get("darpan.order_review") is True and mko.get("darpan.order_review") is False and du.get("marker_on_page") is True
          and (du["due"][0] == 1 if du["clock"] >= du["list_time"] else du["due"][0] == 0) and du["due_on_sheet"][0] == 0, du)
    return finish()


def finish():
    if FAILS:
        print("WALK_S485 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + f[:200])
        return 1
    print("WALK_S485 GREEN -- %d checks" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
