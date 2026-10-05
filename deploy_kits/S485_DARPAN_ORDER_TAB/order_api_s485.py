

# ---- S485_DARPAN_ORDER_TAB (05-Oct-2026, D677): "आज का ऑर्डर" -- Darpan reviews the system's order list on his own page ------------------
# The engine's list (order_proposal, prepared 09:00 by order_rules.tick) was shown to nobody while Darpan's Marg sheet decided the order.
# On order.source = darpan it opens on this page's second tab from order.darpan_list_time (09:30); he holds a line, adds a medicine,
# changes a quantity and taps Pakka per supplier -- nothing typed but three letters of a name. A Pakka'd supplier (status darpan_ok)
# is what reception's "Order karna hai" cards show; everything after that is S454's, untouched. Nothing new is computed here: the lines
# are the engine's; a held line carries held=true and an added one added=true in the proposal's own `lines`; every tap is one row of
# order_darpan_edit. The tab fetches this API by itself -- the page's own day payload is not changed, and a failure here never breaks
# कल का हिसाब. On any other order.source the list is shown read-only and no tap is taken.
S485_ACTIONS = ("hold", "unhold", "qty", "add", "pakka")
S485_SHOWN = ("open", "darpan_ok", "sent")
_S485_INPUTS = {"key": None, "val": None}


def _s485_or():
    import order_rules                                       # noqa: PLC0415
    return order_rules


def _s485_source(con):
    try:
        import order_sheet                                   # noqa: PLC0415
        return order_sheet.source(con)
    except Exception:                                        # noqa: BLE001
        return "marg_sheet"


def _s485_hhmm(ts):
    s = str(ts or "")
    return s[11:16] if len(s) >= 16 else ""


def _s485_unit(l):
    return "strip" if str(l.get("unit") or "").startswith("strip") else "unit"


def _s485_shelf(l):
    """The shelf as Marg says it: strips:tabs for a strip item (236 of 1*10 -> '23:6'), the plain count otherwise; '' when not known."""
    try:
        oh = int(round(float(l.get("on_hand"))))
    except (TypeError, ValueError):
        return ""
    ps = int(l.get("pack_size") or 1)
    if _s485_unit(l) == "strip" and ps > 1:
        return "%d:%d" % (oh // ps, oh % ps) if oh >= 0 else str(oh)
    return str(oh)


def _s485_days_left(l):
    """About how many days the shelf lasts at the line's own pace (on_hand / per_day); None when there is no pace."""
    try:
        oh, pd = float(l.get("on_hand")), float(l.get("per_day"))
    except (TypeError, ValueError):
        return None
    if oh <= 0:
        return 0
    return int(round(oh / pd)) if pd > 0 else None


def _s485_line(pid, l):
    return dict(pid=pid, item=l.get("item") or "", packing=l.get("packing") or "", unit=_s485_unit(l), qty=int(l.get("qty") or 0),
                on_hand_text=_s485_shelf(l), cover_days=l.get("cover_days"), days_left=_s485_days_left(l),
                held=bool(l.get("held")), added=bool(l.get("added")), why=list(l.get("why") or []))


def _s485_rows(con, day, statuses=S485_SHOWN):
    out = []
    for p in con.execute("SELECT * FROM order_proposal WHERE day=? AND status IN (%s) ORDER BY vendor, kind DESC, id" % ",".join("?" * len(statuses)),
                         (day,) + tuple(statuses)).fetchall():
        p = dict(p)
        try:
            p["lines"] = json.loads(p["lines"] or "[]")
        except ValueError:
            p["lines"] = []
        out.append(p)
    return out


def _s485_pakka_at(con, day, sn):
    r = con.execute("SELECT at FROM order_darpan_edit WHERE day=? AND supplier_norm=? AND action='pakka' ORDER BY id DESC LIMIT 1", (day, sn)).fetchone()
    return r[0] if r else ""


def _s485_yesterday(con, today):
    """The previous order day's suppliers and what reception did: ordered (when), arrived or not; a Pakka'd supplier still not ordered."""
    t = today.isoformat()
    days = [r[0] for r in con.execute("SELECT MAX(substr(created_at,1,10)) FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') "
                                      "AND substr(created_at,1,10) < ?", (t,)) if r[0]] if _has(con, "purchase_order") else []
    days += [r[0] for r in con.execute("SELECT MAX(day) FROM order_darpan_edit WHERE action='pakka' AND day < ?", (t,)) if r[0]]
    if not days:
        return "", []
    d = max(days)
    OR = _s485_or()
    out, seen = [], set()
    if _has(con, "purchase_order"):
        for o in con.execute("SELECT vendor, supplier_norm, status, created_at, received_at FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') "
                             "AND substr(created_at,1,10)=? ORDER BY vendor, id", (d,)).fetchall():
            sn = o[1] or o[0]
            if sn in seen:
                continue
            seen.add(sn)
            out.append(dict(display=OR._short(o[0]), vendor=o[0], state="arrived" if o[2] == "received" else "ordered", at=_s485_hhmm(o[3])))
    for r in con.execute("SELECT DISTINCT p.supplier_norm, p.vendor FROM order_proposal p JOIN order_darpan_edit e ON e.day=p.day AND e.supplier_norm=p.supplier_norm "
                         "AND e.action='pakka' WHERE p.day=? AND p.status IN ('darpan_ok','merged') ORDER BY p.vendor", (d,)).fetchall():
        if r[0] in seen:
            continue
        seen.add(r[0])
        called = False
        try:
            called = bool(con.execute("SELECT 1 FROM purchase_audit WHERE action='s454_call' AND ref=? AND substr(at,1,10)=? LIMIT 1", (r[0], d)).fetchone())
        except sqlite3.Error:
            called = False
        out.append(dict(display=OR._short(r[1]), vendor=r[1], state="no_answer" if called else "not_ordered", at=""))
    return d, out


def _s485_payload(con, who):
    OR = _s485_or()
    today = OR._today()
    day = today.isoformat()
    src = _s485_source(con)
    lt = OR.darpan_list_time(con)
    opened = OR.darpan_list_open(con)
    frozen = bool(OR._frozen(con))
    by, order = {}, []
    if opened and not frozen:
        for p in _s485_rows(con, day):
            r = OR.rule_for(con, p["supplier_norm"])
            if int(r.get("paused") or 0):
                continue
            b = by.get(p["supplier_norm"])
            if b is None:
                b = by[p["supplier_norm"]] = dict(supplier_norm=p["supplier_norm"], vendor=p["vendor"], display=OR._short(p["vendor"]),
                                                  order_day=bool(OR.is_order_day(con, r, today)), status=p["status"], pakka_at="", sent_at="", lines=[])
                order.append(b)
            if p["status"] == "open":
                b["status"] = "open"                           # one of its rows still waits for him: the block is open
            elif p["status"] == "darpan_ok" and b["status"] == "sent":
                b["status"] = "darpan_ok"
            if p["status"] == "sent":
                b["sent_at"] = _s485_hhmm(p.get("sent_at"))
            b["lines"].extend(_s485_line(p["id"], l) for l in p["lines"])
        for b in order:
            b["pakka_at"] = _s485_hhmm(_s485_pakka_at(con, day, b["supplier_norm"]))
            b["n"] = sum(1 for l in b["lines"] if not l["held"])
    yd, ylist = _s485_yesterday(con, today)
    live = [l for b in order for l in b["lines"] if not l["held"]]
    return dict(ok=True, date=day, list_time=lt, opened=opened, source=src, frozen=frozen, me=who[0],
                editable=bool(src == "darpan" and who[0] in ("staff", "owner") and opened and not frozen),
                suppliers=order, n_suppliers=len(order), n_lines=len(live), order_day_names=[b["display"] for b in order if b["order_day"]],
                all_pakka=bool(order) and all(b["status"] != "open" for b in order), yesterday_date=yd, yesterday=ylist)


def _s485_edit(con, day, sn, item, action, qty, by):
    con.execute("INSERT INTO order_darpan_edit (day, supplier_norm, item, action, qty, at, by) VALUES (?,?,?,?,?,?,?)",
                (day, sn, item or "", action, qty, now_iso(), by or ""))


def _s485_gate():
    """(u, con, who, OR, err) for a tap: the page's own door; staff or owner; the list is Darpan's only on order.source = darpan, after
    its time, and while medicine ordering is not frozen."""
    u, con, who, err = _auth()
    if err:
        return None, None, None, None, err
    if who[0] not in ("staff", "owner"):
        return None, None, None, None, (jsonify(ok=False, error="not_permitted"), 403)
    OR = _s485_or()
    if _s485_source(con) != "darpan":
        return None, None, None, None, (jsonify(ok=False, error="not_darpan", message="अभी मार्ग की शीट से ऑर्डर हो रहा है"), 409)
    if OR._frozen(con):
        return None, None, None, None, (jsonify(ok=False, error="frozen", message="दवा का ऑर्डर अभी बंद है"), 423)
    if not OR.darpan_list_open(con):
        return None, None, None, None, (jsonify(ok=False, error="not_open", message="आज की सूची %s बजे आएगी।" % OR.darpan_list_time(con).lstrip("0")), 409)
    return u, con, who, OR, None


def _s485_find(con, day, pid, item):
    """(proposal row as dict with parsed lines, the line) of an OPEN proposal of today -- else (None, None)."""
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return None, None
    p = con.execute("SELECT * FROM order_proposal WHERE id=? AND day=? AND status='open'", (pid, day)).fetchone()
    if not p:
        return None, None
    p = dict(p)
    try:
        p["lines"] = json.loads(p["lines"] or "[]")
    except ValueError:
        p["lines"] = []
    return p, next((l for l in p["lines"] if l.get("item") == item), None)


def _s485_save(con, p):
    total = sum(int(l.get("value_p") or 0) for l in p["lines"] if not l.get("held"))
    con.execute("UPDATE order_proposal SET lines=?, total_p=? WHERE id=?", (json.dumps(p["lines"], ensure_ascii=False), total, p["id"]))


def _s485_step(l, up):
    """− / + : 10 strips at 20 or more, else 5; 1 for a unit item; never below one step."""
    q = int(l.get("qty") or 0)
    if _s485_unit(l) != "strip":
        return max(1, q + (1 if up else -1))
    step = 10 if q >= 20 else 5
    return max(5, q + (step if up else -step))


@bp.route("/finance/darpan/kal/api/order")
def api_s485_order():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):                     # a cash recipient's view of this page has no order tab
        return jsonify(ok=False, error="not_permitted"), 403
    return jsonify(**_s485_payload(con, who))


@bp.route("/finance/darpan/kal/api/order/hold", methods=["POST"])
def api_s485_hold():
    u, con, who, OR, err = _s485_gate()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    day = OR._today().isoformat()
    item = str(b.get("item") or "")
    p, l = _s485_find(con, day, b.get("pid"), item)
    if not l:
        return jsonify(ok=False, error="gone", message="यह लाइन अब सूची में नहीं है।"), 409
    hold = bool(b.get("hold"))
    if hold:
        l["held"] = True
    else:
        l.pop("held", None)
    _s485_save(con, p)
    _s485_edit(con, day, p["supplier_norm"], item, "hold" if hold else "unhold", int(l.get("qty") or 0), u["user"])
    con.commit()
    return jsonify(**_s485_payload(con, who))


@bp.route("/finance/darpan/kal/api/order/qty", methods=["POST"])
def api_s485_qty():
    u, con, who, OR, err = _s485_gate()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    day = OR._today().isoformat()
    item = str(b.get("item") or "")
    p, l = _s485_find(con, day, b.get("pid"), item)
    if not l or l.get("held"):
        return jsonify(ok=False, error="gone", message="यह लाइन अब सूची में नहीं है।"), 409
    try:
        up = int(b.get("dir") or 0) > 0
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    q = _s485_step(l, up)
    l.setdefault("qty_engine", int(l.get("qty") or 0))         # the engine's own figure, kept beside his
    l["qty"] = q
    l["value_p"] = int(q * int(l.get("rate_p") or 0))
    _s485_save(con, p)
    _s485_edit(con, day, p["supplier_norm"], item, "qty", q, u["user"])
    con.commit()
    return jsonify(**_s485_payload(con, who))


def _s485_inputs(con, OR, today):
    """The engine's own inputs (order_rules._s470_inputs: the spine's purchase lines, the snapshot, the pace), kept two minutes."""
    import time                                              # noqa: PLC0415
    key = (today.isoformat(), int(time.time() // 120))
    if _S485_INPUTS["key"] != key:
        _S485_INPUTS["val"] = OR._s470_inputs(con, today)
        _S485_INPUTS["key"] = key
    return _S485_INPUTS["val"]


def _s485_known(con, OR, today, item):
    """What the engine knows of one item of Marg's list: (snapshot row, purchase facts or None, pace or None) -- (None, None, None) when
    the item is not in the newest stock list."""
    pa = OR._pa()
    k = pa.norm(item)
    try:
        _as_on, snap, pace, purch, _transit, _ortho = _s485_inputs(con, OR, today)
        s = snap.get(k)
        if s and s.get("item") == item:
            return s, purch.get(k), pace.get(k)
    except Exception:                                        # noqa: BLE001 -- the spine could not be read: Marg's list alone
        pass
    _a, snap2 = pa._latest_snapshot(con)
    s = snap2.get(k)
    if s and s.get("item") == item:
        return dict(item=s["item"], qty=s.get("qty"), packing=s.get("packing") or "", pack_size=max(1, int(s.get("pack_size") or OR._s470_pack(s.get("packing"))))), None, None
    return None, None, None


def _s485_usual(s, e):
    """(strip?, quantity) an added line starts with: the usual lot (in units) / pack size, rounded up to a strip -- or 10 strips / 1."""
    ps = max(1, int(s.get("pack_size") or 1))
    strip = ps > 1
    lot = (e or {}).get("lot")
    if lot:
        import math                                          # noqa: PLC0415
        return strip, max(1, int(math.ceil(float(lot) / ps)))
    return strip, (10 if strip else 1)


def _s485_chips(con, OR, day):
    """The suppliers Darpan may tap: those with a proposal today, then the other suppliers that have a rule, by name."""
    out, seen = [], set()
    for p in _s485_rows(con, day):
        if p["supplier_norm"] not in seen:
            seen.add(p["supplier_norm"])
            out.append(dict(supplier_norm=p["supplier_norm"], display=OR._short(p["vendor"]), today=True))
    for r in con.execute("SELECT supplier_norm, supplier FROM order_supplier_rule WHERE COALESCE(paused,0)=0 ORDER BY supplier_norm").fetchall():
        if r[0] not in seen and r[0] != OR._ortho_norm(con):
            seen.add(r[0])
            out.append(dict(supplier_norm=r[0], display=OR._short(r[1] or r[0]), today=False))
    return out


@bp.route("/finance/darpan/kal/api/order/items")
def api_s485_items():
    u, con, who, err = _auth()
    if err:
        return err
    if who[0] not in ("staff", "owner"):
        return jsonify(ok=False, error="not_permitted"), 403
    OR = _s485_or()
    q = str(request.args.get("q") or "").strip()
    today = OR._today()
    hits = []
    if len(q) >= 3:
        for h in OR.item_names(con, q):
            s, e, _p = _s485_known(con, OR, today, h["item"])
            strip, qty = _s485_usual(s or dict(pack_size=OR._s470_pack(h.get("packing"))), e)
            hits.append(dict(item=h["item"], packing=h.get("packing") or "", supplier_norm=(e or {}).get("vendor") or "",
                             supplier=OR._short((e or {}).get("vendor_disp") or (e or {}).get("vendor") or "") if (e or {}).get("vendor") else "",
                             unit="strip" if strip else "unit", qty=qty, usual=bool((e or {}).get("lot"))))
    return jsonify(ok=True, q=q, hits=hits, chips=_s485_chips(con, OR, today.isoformat()))


@bp.route("/finance/darpan/kal/api/order/add", methods=["POST"])
def api_s485_add():
    u, con, who, OR, err = _s485_gate()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    today = OR._today()
    day = today.isoformat()
    item = str(b.get("item") or "").strip()
    s, e, pace = _s485_known(con, OR, today, item)
    if not s:
        return jsonify(ok=False, error="unknown_item", message="यह नाम मार्ग की सूची में नहीं मिला।"), 404
    sn = (e or {}).get("vendor") or ""
    vendor = (e or {}).get("vendor_disp") or sn
    if not sn:                                               # never bought: the supplier is the one he tapped
        sn = str(b.get("supplier_norm") or "").strip()
        chip = next((c for c in _s485_chips(con, OR, day) if c["supplier_norm"] == sn), None)
        if not chip:
            return jsonify(ok=False, error="need_supplier", message="सप्लायर चुनिए"), 409
        r = con.execute("SELECT vendor FROM order_proposal WHERE day=? AND supplier_norm=? ORDER BY id LIMIT 1", (day, sn)).fetchone()
        r2 = con.execute("SELECT supplier FROM order_supplier_rule WHERE supplier_norm=?", (sn,)).fetchone()
        vendor = (r[0] if r else None) or (r2[0] if r2 and r2[0] else None) or sn
    if int(OR.rule_for(con, sn).get("paused") or 0):
        return jsonify(ok=False, error="paused", message="इस सप्लायर का ऑर्डर अभी रुका हुआ है।"), 409
    rows = [dict(r) for r in con.execute("SELECT * FROM order_proposal WHERE day=? AND supplier_norm=? AND status IN ('open','darpan_ok','sent') ORDER BY id", (day, sn))]
    for r in rows:
        try:
            r["lines"] = json.loads(r["lines"] or "[]")
        except ValueError:
            r["lines"] = []
    if any(l.get("item") == item for r in rows for l in r["lines"]):
        return jsonify(ok=False, error="already", message="यह दवा सूची में पहले से है।"), 409
    strip, qty = _s485_usual(s, e)
    ps = max(1, int(s.get("pack_size") or 1))
    rate_p = int((e or {}).get("rate_p") or 0)
    try:
        on_hand = int(round(float(s.get("qty"))))
    except (TypeError, ValueError):
        on_hand = None
    line = dict(item=item, on_hand=on_hand, qty=qty, unit="strip" if strip else "unit", pack_size=ps, packing=s.get("packing") or "", rate_p=rate_p,
                per_day=(round(float(pace["rate_per_day"]), 2) if pace and pace.get("rate_per_day") is not None else None), cover_after=None, cover_days=None,
                value_p=int(qty * rate_p), confirm=False, why=["Darpan ne joda"], vendor_norm=sn, added=True, lot=(e or {}).get("lot"), free=(e or {}).get("free"))
    tgt = next((r for r in rows if r["status"] == "open"), None)
    if tgt is not None:
        tgt["lines"].append(line)
        _s485_save(con, tgt)
    elif any(r["kind"] == "darpan" for r in rows):
        return jsonify(ok=False, error="closed", message="इस सप्लायर की सूची पक्की हो चुकी है।"), 409
    else:                                                    # no open list for this supplier today: one of his own
        con.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (day, sn, vendor, "darpan", "open", json.dumps([line], ensure_ascii=False), line["value_p"], "Darpan ne joda", now_iso()))
    _s485_edit(con, day, sn, item, "add", qty, u["user"])
    con.commit()
    return jsonify(**dict(_s485_payload(con, who), added=dict(item=item, supplier_norm=sn, qty=qty)))


@bp.route("/finance/darpan/kal/api/order/pakka", methods=["POST"])
def api_s485_pakka():
    u, con, who, OR, err = _s485_gate()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    day = OR._today().isoformat()
    if not OR._rules_ok(con):
        return jsonify(ok=False, error="rules_pending", message="डॉक्टर साहब के नियम अभी बाकी हैं।"), 403
    rows = [p for p in _s485_rows(con, day, ("open",)) if not int(OR.rule_for(con, p["supplier_norm"]).get("paused") or 0)]
    if not b.get("all"):
        sn = str(b.get("supplier_norm") or "")
        rows = [p for p in rows if p["supplier_norm"] == sn]
    if not rows:
        return jsonify(ok=False, error="nothing", message="पक्का करने को कुछ नहीं है।"), 409
    done = {}
    for p in rows:
        n = con.execute("UPDATE order_proposal SET status='darpan_ok' WHERE id=? AND status='open'", (p["id"],)).rowcount
        if n:
            done[p["supplier_norm"]] = done.get(p["supplier_norm"], 0) + sum(1 for l in p["lines"] if not l.get("held"))
    for sn, n in done.items():
        _s485_edit(con, day, sn, "", "pakka", n, u["user"])
    con.commit()
    return jsonify(**dict(_s485_payload(con, who), pakka=sorted(done)))
# ---- S485_DARPAN_ORDER_TAB end ----------------------------------------------------------------------------------------------------------
