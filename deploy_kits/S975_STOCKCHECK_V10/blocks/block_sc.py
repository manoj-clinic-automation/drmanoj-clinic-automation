

# ---- S975 (28-Nov-2026, Sanjeevni session 542, kit S975_STOCKCHECK_V10; D1106 -- mock-up v10, his 'OK' 11:52 IST) --------------------
#  The one page in three bands: 1 his write-offs waiting for Amir (the loss register's open lines) . 2 today's counts, one plain verdict
#  each (and any earlier count still waiting for his call) . 3 waiting on others (the existing boxes, folded). desk() keeps every box as
#  before -- the desk's writes and the earlier walks read them -- and ADDS band1, band2, earlier, week, way3 and v10 totals. A row is shown
#  once: an item of band 1 leaves way3 (box 2 as drawn) unless it waits on another correction too. F-1738: a fresh surplus is told
#  'more than Marg -- noted, never a loss' in box 3 (voucher_judge's 'surplus'). CCM (the whole-unit list) is told in its bottles.
KIT_S975 = "S975_STOCKCHECK_V10"
VERSION = "1.9"                                              # v1.9 S975: the three bands (band1 . band2 . earlier . week . way3)
WEEK_DAYS = 7
_desk_before_s975 = desk


def _s975_dm(iso):
    s = str(iso or "")[:10]
    return "%s-%s" % (s[8:10], s[5:7]) if len(s) == 10 else s


def _s975_whole(con, item):
    """The whole-unit word of an item ('bottle' for CCM, the desk's stock.whole_unit_items), or None."""
    try:
        import loss_piles as LP                               # noqa: PLC0415 -- loads the whole-unit map into qty_words
        LP.settings(con)
        import qty_words as QW                                # noqa: PLC0415
        return QW.whole_unit_of(item)
    except Exception:                                         # noqa: BLE001
        return None


def _s975_q(units, pack, whole=None, signed=False):
    """A count's figure in the record's own unit: strips:tabs; for an item Marg counts whole ('CCM = bottle') whole packs read as that
    word (the count screen stores a pack of the record's size for each one)."""
    if units is None:
        return "—"
    u = float(units)
    if whole and pack > 1 and abs(u - round(u / pack) * pack) < 0.5:
        n = int(round(u / pack))
        w = "%d %s%s" % (abs(n), whole, "" if abs(n) == 1 else "s")
        return (("−" if n < 0 else ("+" if n > 0 else "")) + w) if signed else w
    return st(u, pack, signed=signed)


def _s975_band1(con, VJ, VI, J, RR, day):
    """Band 1: every write-off of his that Marg's report does not hold yet -- the loss register's open lines (not withdrawn)."""
    if not _has(con, "stock_desk_action") or VI is None:
        return [], None, {}
    jst = {}
    for a in J.get("asks") or []:
        for k in (a.get("jobs") or [a.get("ref")]):
            if str(k or "").startswith("S969:wo:"):
                jst[k] = a
    L = VI.losses(con, J)
    lines = {ln["id"]: ln for m in L.get("months") or [] for ln in m["lines"]}
    month = next((m for m in L.get("months") or [] if m["month"] == str(day)[:7]), None)
    foot = dict(label=month["label"], n=month["n"], cost_t=month["cost_t"], mrp_t=month["mrp_t"]) if month else None
    out, WS = [], {}                                          # WS: the counts he wrote off -> 'above' (band 1) . 'withdrawn' . 'in Marg' . 'closed'
    d0 = dt.date.fromisoformat(day)
    for (i, item, pack, units, key, dday, at, by, batch, pat, pid) in con.execute(
            "SELECT id, item, pack, units, job_key, day, at, by, batch, point_at, point_id FROM stock_desk_action WHERE kind='writeoff' ORDER BY at, id").fetchall():
        ln = lines.get(i)
        pid_ = int(pid) if pid else None
        def mark(w):
            if pid_ is not None:
                WS[pid_] = w
        if ln is None:
            mark("closed"); continue
        if ln.get("withdrawn"):
            mark("withdrawn"); continue
        a = jst.get(key)
        if a and a.get("state") == "in_marg" and a.get("match"):
            mark("in Marg"); continue                         # in Marg: closed, the loss register keeps it
        if a and a.get("state") not in VJ.WAY_STATES + ("not_in_marg",):
            mark("closed"); continue                          # (cold review 4) fixed otherwise / in Marg not as asked: never twice
        jr = con.execute("SELECT done_at, done_how FROM amir_job WHERE key=?", (key,)).fetchone() if key else None
        if jr and jr[1] == "withdrawn":
            mark("withdrawn"); continue
        mark("above")
        done = bool(jr and jr[0])
        try:
            days = (d0 - dt.date.fromisoformat(str(dday)[:10])).days
        except ValueError:
            days = 0
        stt = (a or {}).get("state") or ""
        card = "STOCK ISSUE · %s" % _s975_dm(dday)
        if done:
            cs = "Kar diya %s — %s" % (_s975_dm(jr[0]), "Marg's newer report lacks it" if stt == "not_in_marg" else
                                       ("a report of that period decides" if stt == "gap" else "the next report decides"))
            tags = [["red" if stt == "not_in_marg" else "amb", cs]]
        else:
            cs = ("today" if days <= 0 else "%d day%s" % (days, "" if days == 1 else "s")) + " — not done"
            tags = [["red" if days >= 2 else "blu", "on Amir's card, " + cs]]
        R = VJ.record_for(RR, {norm(item)})
        path = [["ok", "The count: %s." % ln["count"]] if ln.get("count") not in (None, "", "—") else ["ok", "The count this write-off acts on is not named."],
                ["ok", "Your tap %s: Write off %s (%s)%s." % (stamp(at), ln["q"], ln["group"], (" by " + str(by).title()) if by else "")],
                ["ok" if done else "now", "On Amir's card: %s — %s %s%s; %s." % (card, item, ln["q"], (" · batch " + batch) if batch else "", cs)],
                ["now", "It closes by itself when Marg's Stock Issue report shows the voucher (the voucher judge). The loss register keeps "
                        "it either way, its value fixed on the day of your tap."]]
        out.append(dict(item=item, key=(R or {}).get("k20") or "", pack=int(pack or 1), q=ln["q"], booked=_s975_dm(dday), card=card, card_state=cs,
                        done=done, track=[["ok", "Booked " + _s975_dm(dday)], ["ok" if done else "now", "Amir keys it" + ((" · Kar diya " + _s975_dm(jr[0])) if done else "")],
                                          ["now" if done else "wait", "In Marg"]],
                        cost_t=ln.get("cost_t") or "", mrp_t=ln.get("mrp_t") or "", tags=tags, path=path, acts=[], ref=None, box="band1",
                        job=key or "", pat=str(pat or ""), day=str(dday or "")[:10], at=str(at or "").replace(" ", "T")[:19],
                        fig="written off %s · booked %s · %s" % (ln["q"], _s975_dm(dday), (ln.get("cost_t") or "")),
                        vlines=_vlines_for(VJ, con, item, J)))
    return out, foot, WS


def _s975_point_rows(con, d1, d2):
    """stock_point rows of the spot mornings and Darpan with d1 <= day <= d2, newest first; a count replaced by a later one is left out."""
    cols = {r[1] for r in con.execute("PRAGMA table_info(stock_point)")}
    jw = "judge_words" if "judge_words" in cols else "NULL"
    return [dict(id=r[0], item=r[1], at=str(r[2]), qty=r[3], expected=r[4], gap=r[5], source=r[6], status=str(r[7] or ""), words=str(r[8] or ""),
                 by=str(r[9] or "")) for r in con.execute(
        "SELECT id, item, at, qty_units, expected_units, gap_units, source, status, %s, by FROM stock_point WHERE substr(at,1,10)>=? AND "
        "substr(at,1,10)<=? AND source IN ('spot','darpan') AND COALESCE(status,'') NOT IN ('superseded') ORDER BY at DESC, id DESC" % jw, (d1, d2))]


def _s975_count_row(con, VJ, J, RR, P, rowmap, WOP, b1items):
    """One count, one plain verdict: dict(item, key, fig, tags, acts, path, verdict, surplus, day, time, by)."""
    R = VJ.record_for(RR, {norm(P["item"])})
    pack = int((R or {}).get("pack") or 1) or 1
    whole = _s975_whole(con, P["item"]) if pack > 1 else None
    g = P["gap"]
    unclear = bool(whole and P["qty"] is not None and abs(float(P["qty"]) - round(float(P["qty"]) / pack) * pack) >= 0.5)   # second look 4
    exp_t = (("%d %s%s" % (int(round(float(P["expected"]))), whole, "" if int(round(float(P["expected"]))) == 1 else "s")) if whole and P["expected"] is not None
             else st(P["expected"], pack))
    if unclear:
        gap_t = "not compared"
    elif whole and P["qty"] is not None and P["expected"] is not None and abs(float(P["qty"]) - round(float(P["qty"]) / pack) * pack) < 0.5:
        g = round(float(P["qty"]) / pack) - float(P["expected"])   # CCM: the screen's packs are bottles, Marg's figure already is
        gap_t = ("+" if g > 0 else ("−" if g < 0 else "")) + "%d %s%s" % (abs(int(round(g))), whole, "" if abs(int(round(g))) == 1 else "s") if abs(g) >= 0.5 else "0"
    else:
        gap_t = st(g, pack, signed=True) if g is not None else "—"
    r = rowmap.get(int(P["id"]))
    src = "Darpan" if P["source"] == "darpan" else "The spot morning"
    base = ["ok", "%s's count at %s: %s counted, Marg %s at the time%s." % (src, stamp(P["at"]), _s975_q(P["qty"], pack, whole), exp_t,
                                                                          (" -- Marg counts %s by the %s" % (P["item"], whole)) if whole else "")]
    d = dict(item=P["item"], key=(R or {}).get("k20") or "", pack=pack, day=P["at"][:10], time=P["at"][11:16], by=(P["by"] or "").title(), src=src.replace("The spot", "Spot"),
             fig="counted %s · Marg %s · %s" % (_s975_q(P["qty"], pack, whole), exp_t, gap_t), tags=[], acts=[], path=[base], surplus=False,
             verdict="", vlines=_vlines_for(VJ, con, P["item"], J), pid=int(P["id"]), box="band2")
    if P["words"]:
        d["path"].append(["ok", "Judged: " + P["words"]])
    box = (r or {}).get("box") or ""
    b1a = [x.get("at") or (x.get("day", "") + "T23:59:59") for x in b1items.get(norm(P["item"])) or []]
    w_ = (WOP.get(int(P["id"]), "above") if isinstance(WOP, dict) else "above") if int(P["id"]) in WOP else None
    if w_ == "above":
        d.update(verdict="wo", tags=[["grn", "written off by you — above"]])
        d["path"].append(["now", "Written off from this desk: band 1 above follows it to Marg."])
    elif w_:
        d.update(verdict="wo_" + w_.split()[0].lower(), tags=[["gry", "your write-off of it was withdrawn"] if w_ == "withdrawn" else
                                                                ["grn", "written off by you — in Marg" if w_ == "in Marg" else "written off by you — closed"]])
    elif P["status"] in ("recounted", "recount"):
        d.update(verdict="recounted", tags=[["gry", "recounted — see the next count"] if P["status"] == "recounted" else ["amb", "held for a recount"]])
    elif unclear:
        d.update(verdict="unit", tags=[["amb", "stored %s — its unit is unclear (Marg counts %s by the %s); see the item ledger" % (st(P["qty"], pack), P["item"], whole)]])
    elif not r and b1a and g is not None and float(g) <= -0.5 and P["at"].replace(" ", "T")[:19] < max(b1a):
        d.update(verdict="before_wo", tags=[["gry", "before your write-off of %s — band 1 above" % _s975_dm(max(b1a))]])
        d["path"].append(["ok", "A count before your write-off of %s; band 1 above follows that write-off to Marg." % _s975_dm(max(b1a))])
    elif whole and not r and g is not None and float(g) <= -0.5:
        d.update(verdict="unit_loss", tags=[["amb", "%s short — the stock record cannot judge this item yet (its pack); see the item ledger" % gap_t.lstrip("−")]])
        d["path"].append(["now", "Marg counts %s by the %s, the stock record by a pack of %d: no Write off is offered until the record's pack is put right." % (P["item"], whole, pack)])
    elif r and box == "allow":
        d.update(verdict="allow", tags=list(r.get("tags") or []) or [["amb", "within your allowance"]], wo_ok=r.get("wo_ok"))
        d["tags"] = [["amb", t[1]] if t[0] == "gry" else t for t in d["tags"]]
        d["path"] = list(r.get("path") or d["path"])
    elif r and box == "short":
        d.update(verdict="loss", acts=list(r.get("acts") or []), short_t=r.get("short_t") or "", tags=list(r.get("tags") or []))
        if d["acts"]:
            d["tags"].insert(0, ["red", "a loss since the last count — your call"])
        d["path"] = list(r.get("path") or d["path"])
    elif r and box == "way":
        d.update(verdict="way", tags=list(r.get("tags") or []), acts=list(r.get("acts") or []), ref=r.get("ref"))
        d["path"] = list(r.get("path") or d["path"])
    elif r and box == "noted":
        d.update(verdict="noted", tags=list(r.get("tags") or []))
        d["path"] = list(r.get("path") or d["path"])
    elif P["status"] == "awaits_sales":
        d.update(verdict="awaits", tags=[["amb", "waits for the day's sales"]])
        d["path"].append(["now", "An evening count: judged when that day's sale report is in."])
    elif g is None:
        d.update(verdict="none", tags=[["gry", "not judged yet"]])
    elif abs(float(g)) < 0.5:
        d.update(verdict="agree", tags=[["grn", "agrees with Marg"]])
    elif float(g) > 0:
        d.update(verdict="surplus", surplus=True, tags=[["gry", "more than Marg — never a loss"]])
        d["path"].append(["ok", "More on the shelf than in Marg: noted, never a loss; nothing waits for your call."])
    elif "within the allowance" in P["words"]:
        d.update(verdict="allow", tags=[["amb", "within your allowance"]])
    else:
        d.update(verdict="short", tags=[["gry", "short — its row is in the boxes below"]])
        d["path"].append(["now", "The stock of record stands on a later figure now; the boxes below tell what is left of it."])
    return d


def _s975_bands(con, v, day):
    import voucher_judge as VJ                                # noqa: PLC0415
    RR = VJ.record_rows(con)
    try:
        J = VJ.judge(con, day)
    except Exception:                                         # noqa: BLE001
        J = dict(ok=False, asks=[], lines=[], vouchers=[])
    try:
        VI = _VI()
    except Exception:                                         # noqa: BLE001
        VI = None
    band1, foot, WS = _s975_band1(con, VJ, VI, J, RR, day)
    b1 = {}
    for x in band1:                                           # (cold review 5) every open write-off of an item, oldest first
        b1.setdefault(norm(x["item"]), []).append(x)
    # a row is shown once: box 2's rows of a band-1 item leave way3 -- unless the item waits on another correction too;
    # a Withdraw (a later count agrees with Marg, not to be keyed) moves onto the band-1 row
    other = set()
    for a in J.get("asks") or []:
        if a.get("state") not in VJ.WAY_STATES + ("not_in_marg",):
            continue
        if str(a.get("ref") or "").startswith("S969:wo:") or any(str(k or "").startswith("S969:wo:") for k in (a.get("jobs") or [])):
            continue
        for k in b1:
            if VJ.name_match(set(a.get("forms") or {norm(a["item"])}), b1[k][0]["item"]):
                other.add(k)
    way3 = []
    for r in v.get("way") or []:
        k = norm(r.get("item") or "")
        if r.get("claim") or k not in b1:
            way3.append(r)
            continue
        x = next((y for y in b1[k] if y["job"] and y["job"] == r.get("ref")), b1[k][-1])
        moved = False
        if "wd" in (r.get("acts") or []) and not x["acts"]:
            x.update(acts=["wd"], ref=r.get("ref")); moved = True
        for t in r.get("tags") or []:
            if t not in x["tags"] and "already asked" not in t[1]:
                x["tags"].append(t)
        for p in r.get("path") or []:
            if p[0] == "now" and p not in x["path"] and "On Amir's card" not in p[1]:
                x["path"].insert(len(x["path"]) - 1, p)
        if k in other:
            way3.append(dict(r, tags=list(r.get("tags") or []) + [["gry", "your write-off: band 1 above"]],
                             acts=[q for q in (r.get("acts") or []) if not (moved and q == "wd")]))   # second look 5: Withdraw once
    for r in v.get("old") or []:                              # box 3: today's gap of an item he wrote off is told as band 1's, never red
        k = norm(r.get("item") or "")
        Rb = VJ.record_for(RR, {k})                           # (cold review 3) only when today's gap stands on the very count he wrote off
        if k in b1 and r.get("verdict") == "fresh_gap" and Rb and any(y["pat"] and y["pat"][:16].replace(" ", "T") == str(Rb.get("base_at") or "")[:16].replace(" ", "T") for y in b1[k]):
            r["tags"] = [["blu", "your write-off — band 1 above"]] + list(r.get("tags") or [])[1:]
            r["path"] = [(["ok", "Today's gap is your write-off -- band 1 above follows it to Marg."] if "Today's gap" in p[1] else p) for p in r.get("path") or []]
    rowmap = {}
    for name in ("box1", "allow", "way", "noted"):
        for r in v.get(name) or []:
            if r.get("pid") is not None:
                rowmap.setdefault(int(r["pid"]), r)
    WOP = dict(WS)                                           # second look 1: what became of each count he wrote off
    for p_ in _wo_points(con):
        WOP.setdefault(int(p_), "closed")
    today_rows = [_s975_count_row(con, VJ, J, RR, P, rowmap, WOP, b1) for P in _s975_point_rows(con, day, day)]
    shown = {x["pid"] for x in today_rows}
    # (cold review 1) every box-1 / allowance row not drawn as today's count stays visible here -- with or without its buttons
    # (a Pursue waiting on Darpan, an evening count waiting for its sales), whatever the count's age; it never repeats in the week fold
    earlier = [r for r in (v.get("box1") or []) + (v.get("allow") or []) if r.get("pid") is None or int(r["pid"]) not in shown]
    held = {int(r["pid"]) for r in earlier if r.get("pid") is not None}
    d7 = (dt.date.fromisoformat(day) - dt.timedelta(days=WEEK_DAYS)).isoformat()
    d1 = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
    week = [_s975_count_row(con, VJ, J, RR, P, rowmap, WOP, b1) for P in _s975_point_rows(con, d7, d1) if int(P["id"]) not in held]
    counters = sorted({x["by"] or x["src"] for x in today_rows})
    aw = [r["item"] for r in (v.get("allow") or []) if r.get("wo_ok")]
    tot = dict(band1=len(band1), today=len(today_rows), way3=len(way3), recount=sum(1 for r in v.get("recount") or [] if not r.get("on_list")),
               earlier=len(earlier), week=len(week), allow_wo=len(aw), b1_done=sum(1 for x in band1 if x["done"]))
    return dict(v10=True, kit_v10=KIT_S975, band1=band1, band1_foot=foot, band2=today_rows, earlier=earlier, week=week, way3=way3,
                counters=counters, day_word=day_word(day), allow_items=aw, v10_totals=tot, version=VERSION)


def desk(con, day=None):                                      # noqa: F811 -- S975: the boxes as before, plus the three bands
    _s975_whole(con, "")                                     # the whole-unit map loaded before the judge reads it (second look 3)
    v = _desk_before_s975(con, day)
    if not v.get("ok"):
        return v
    try:
        v.update(_s975_bands(con, v, v.get("day") or day or today().isoformat()))
    except Exception as e:                                    # noqa: BLE001
        v.update(v10=False, v10_reason="The new layout could not be built just now (%s) -- the boxes as before." % type(e).__name__)
        print("stock_check: S975 bands stopped: %s" % str(e)[:200], file=sys.stderr)
    return v
# ---- S975 end ---------------------------------------------------------------------------------------------------------------------------
