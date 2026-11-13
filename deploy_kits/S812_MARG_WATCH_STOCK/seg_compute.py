def _factor_map(sp):
    """Units per Marg quantity, per item, from the spine's own purchase lines (units / (qty + free)); else the packing '1*N' of a LOOSE item; else 1."""
    seen = collections.defaultdict(collections.Counter)
    for k, q, f, u in sp.execute("SELECT k20, qty, free, units FROM sp_purchase_line"):
        qf = float(q or 0) + float(f or 0)
        if qf > 0 and u:
            seen[k][round(float(u) / qf, 3)] += 1
    out = {k: c.most_common(1)[0][0] for k, c in seen.items()}
    for k, pk, uk in sp.execute("SELECT k20, packing, unit_kind FROM sp_item"):
        if k in out:
            continue
        m = re.search(r"\*\s*(\d+)", str(pk or ""))
        out[k] = float(m.group(1)) if (str(uk or "").upper() == "LOOSE" and m) else 1.0
    return out


def _rate_map(sp):
    """S812: the item's newest purchase net rate per unit, in paise (sp_purchase_line); an item never bought has none -- shown 'no rate', never Rs 0."""
    out = {}
    for k, d, u, n in sp.execute("SELECT k20, date, units, net_amount_p FROM sp_purchase_line WHERE COALESCE(direction,'PURCHASE')='PURCHASE' "
                                 "AND units > 0 AND net_amount_p > 0 ORDER BY date"):
        out[k] = int(round(float(n) / float(u)))
    return out


def _tk(stamp):
    try:
        return dt.datetime.strptime(str(stamp or "")[:15], "%Y%m%d-%H%M%S")
    except ValueError:
        return None


def _b_records(finance_db, sp, Z, factor):
    """S812 matcher 1 -- the bills changed after their day, from the Marg watch's own compare (marg_billwatch, no paper), as stock per item:
    [dict(k, delta, side, kind, ref, note, bill_day, was_day, now_day)].  delta = what the change did to Marg's stock, in the spine's units.
    A removed sale bill: the units the spine still holds for it (it gives them back).  A changed or removed purchase bill: now - was, per item,
    (quantity + free) x the item's units.  -> (records, None) or ([], why) -- fail-soft: without them matcher 1 simply finds nothing."""
    if not finance_db:
        return [], "no finance database"
    path = list(sys.path)
    try:
        if HERE not in sys.path:
            sys.path.insert(0, HERE)
        import marg_billwatch as BW                               # noqa: PLC0415
        con = sqlite3.connect("file:%s?mode=ro" % finance_db, uri=True, timeout=30)
        try:
            pur, _p = BW.compare(BW.purchase_exports(con), "purchase", BW.stock_names(con))
            sal, _s = BW.compare(BW.sale_exports(con), "sale", None, part_rule=False, record_kinds=BW.RECORD_KINDS + ("amount",))
            try:
                acts = BW.acts(con)
            except Exception:                                     # noqa: BLE001 -- his decisions are words on the row, never a gate
                acts = {}
        finally:
            con.close()
    except Exception as e:                                        # noqa: BLE001
        return [], ("%s: %s" % (e.__class__.__name__, e))[:120]
    finally:
        sys.path[:] = path

    def day(x):
        t = _tk(x)
        return t.date() if t else None
    out = []
    for f in sal:
        if f.get("kind") != "gone":
            continue
        per = collections.defaultdict(float)
        for k, u in sp.execute("SELECT k20, units FROM sp_move WHERE kind='SALE' AND ref=? AND date=?", (f["no"], f["date"])):
            per[k] += float(u or 0)
        a = acts.get(BW.fkey(f)) or {}
        said = {"stands": " You decided: the sale stands (the bill goes back into Marg).",
                "cancelled": " You decided: the sale was cancelled (the goods came back)."}.get(a.get("decision") if a.get("action") == "close" else "", "")
        for k, u in per.items():
            if abs(u) >= TOL:
                out.append(dict(k=k, delta=round(-u, 3), side="sale", kind="gone", ref="sale bill %s" % f["no"],
                                note="Sale bill %s (%s) was removed in Marg after its day; its %s came back into Marg's stock.%s"
                                % (f["no"], dmon(f["date"]), num(-u), said),
                                bill_day=f["date"], was_day=day(f.get("was_stamp")), now_day=day(f.get("now_stamp"))))
    for f in pur:
        if f.get("kind") not in ("changed", "gone"):
            continue
        per = collections.defaultdict(float)
        for side, sign in (("was", -1), ("now", 1)):
            b = f.get(side) or {}
            for l in b.get("lines") or []:
                k = Z(l["item"])
                per[k] += sign * (float(l["qty"] or 0) + float(l["free"] or 0)) * factor.get(k, 1.0)
        who = " ".join(str(f["sup"]).split()).title()
        for k, u in per.items():
            if abs(u) >= TOL:
                out.append(dict(k=k, delta=round(u, 3), side="purchase", kind=f["kind"], ref="%s bill %s" % (who, f["no"]),
                                note="%s bill %s (%s) was %s in Marg after its day: %s %s on this item." % (
                                    who, f["no"], dmon(f["date"]), "removed" if f["kind"] == "gone" else "changed", snum(u),
                                    "units" if abs(u) != 1 else "unit"),
                                bill_day=f["date"], was_day=day(f.get("was_stamp")), now_day=day(f.get("now_stamp"))))
    return out, None


SIBLING_NOTES = {"CAST SHOE L TYNOR", "ENZOMAC OINTMENT"}   # the owner's 05-Nov notes that name a voucher filed on a sibling (3c)
VOUCHER_BACK_DAYS = 14   # S812: a filed voucher carries the day it was filed; Amir may key it into Marg up to two weeks later


def _stem(name):
    w = re.findall(r"[A-Z0-9]+", str(name or "").upper())
    if not w:
        return ""
    return w[0] if len(w[0]) >= 4 else " ".join(w[:2])


def compute(spine_path=SPINE_DB, finance_db=LIVE_DB, from_day="2026-10-16", rules_path=RULES):
    """-> (rows, info).  Reads only.  rows: dicts k20, item, kind ('hand' | 'rename'), day_from, day_to, marg_from, marg_to, system_moved,
    shift, pair_item, settled -- and (S812) rec_kind, rec_ref, rec_note (the record behind the move, when there is one: such a row is
    'explained after all', D914 -- listed, never counted, never told), owed_paid, rate_p, value_p.
    info['explain'] = {(k20, day): (rec_kind, rec_ref, rec_note)} for steps a record absorbed whole, so a stored row that vanishes is named.
    Raises RuntimeError when Amir's filed vouchers cannot be read (nothing may be judged without them).
    A closing step is JUDGED only when: the sale exports cover every day of its window (an accepted SALE_BILLWISE range -- Sundays too);
    for a RISE, and for a FALL whose window holds an Amir day (only he keys purchases and returns), the purchase exports (bill-wise AND
    item-wise) cover the window and the week before it -- and (S812, F-1278) for a RISE an item-wise purchase export TAKEN AFTER that
    closing was printed exists.  A closing printed with under 90% of its neighbours' items is skipped (a partial print).  Unjudged steps
    still pair renames, so a rename's falling half is never told alone; and (S812, F-1279) still note a purchase Marg has not taken in yet,
    so Marg's later catch-up is paid from it."""
    sp = sqlite3.connect("file:%s?mode=ro" % spine_path, uri=True, timeout=30)
    try:
        meta = {r[0]: r[1] for r in sp.execute("SELECT key, value FROM sp_meta")}
        names = {}
        for k, n in sp.execute("SELECT k20, name FROM sp_item ORDER BY last_seen"):
            names[k] = n or k
        alias = {a: t for a, t, kind in sp.execute("SELECT alias, k20, kind FROM sp_alias") if kind != "rename_family"}
        try:
            fam = json.load(open(rules_path)).get("families", {}) or {}
        except (OSError, ValueError):
            fam = {}

        def Z(n):
            k = K(n)
            k = alias.get(k, k)
            t = fam.get(k, k)
            return t if isinstance(t, str) else k
        op = sp.execute("SELECT MIN(date) FROM sp_move WHERE kind='OPENING'").fetchone()[0] or "0000"
        cnt = {d: n for d, n in sp.execute("SELECT as_on, COUNT(*) FROM sp_close WHERE as_on > ? GROUP BY as_on", (op,))}
        allc = sorted(cnt)
        closings = []
        for i, d in enumerate(allc):                               # the cold review's S4: a partial print is not a closing
            nb = sorted(cnt[x] for x in allc[max(0, i - 3):i] + allc[i + 1:i + 4])
            med = nb[len(nb) // 2] if nb else 0
            if med and cnt[d] < 0.9 * med:
                continue
            closings.append(d)
        M = collections.defaultdict(dict)
        keep = set(closings)
        cmd5 = {}
        for d, k, u, sm in sp.execute("SELECT as_on, k20, units, source_md5 FROM sp_close WHERE as_on > ?", (op,)):
            if d in keep:
                M[k][d] = float(u or 0)
                cmd5.setdefault(d, sm)
        stamps = {m: s for m, s in sp.execute("SELECT md5, stamp FROM sp_export")}
        ctaken = {d: _tk(stamps.get(m)) for d, m in cmd5.items()}    # when each closing was printed (S812, F-1278): the print the spine used
        moves = collections.defaultdict(list)
        purch = collections.defaultdict(list)
        rets = collections.defaultdict(list)
        sales = collections.defaultdict(list)
        for k, d, kind, u, ref in sp.execute("SELECT k20, date, kind, units, ref FROM sp_move"):
            moves[k].append((d, float(u or 0)))
            if kind == "PURCHASE" and (u or 0) > 0:
                purch[k].append((d, float(u)))
            elif kind == "PURCHASE_RETURN" and (u or 0) < 0:
                rets[k].append((d, -float(u)))
            elif kind == "SALE" and (u or 0) < 0:
                sales[k].append((d, float(u), ref))

        def cover(fams):
            out = set()
            for a, b in sp.execute("SELECT date_from, date_to FROM sp_export WHERE ok=1 AND family IN (%s)" % ",".join("?" * len(fams)), fams):
                out.update(_days(a, b))
            return out
        sale_cov = cover(("SALE_BILLWISE",))
        pur_cov = cover(("PURCHASE_BILLWISE",)) & cover(("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE"))
        pur_taken = [t for t in (_tk(s) for s, in sp.execute(
            "SELECT stamp FROM sp_export WHERE ok=1 AND family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')")) if t]
        last_pur_taken = max(pur_taken) if pur_taken else None
        factor = _factor_map(sp)
        rate = _rate_map(sp)
        frees = collections.defaultdict(list)
        for k, d, fr, b in sp.execute("SELECT k20, date, free, bill FROM sp_purchase_line WHERE COALESCE(direction,'PURCHASE')='PURCHASE' AND free > 0"):
            frees[k].append((d, float(fr) * factor.get(k, 1.0), b))
        brecs, b_why = _b_records(finance_db, sp, Z, factor)
        for nm, val, ason in sp.execute("SELECT name, value, as_on FROM sp_item_fact WHERE fact='p_rate' ORDER BY as_on"):
            k = Z(nm)                                              # else Marg's own purchase rate per pack (its newest Item list), per unit
            if k in rate:
                continue
            try:
                v = float(val)
            except (TypeError, ValueError):
                continue
            if v > 0:
                rate["~" + k] = int(round(v * 100 / max(factor.get(k, 1.0), 1.0)))
    finally:
        sp.close()
    B = collections.defaultdict(list)
    for r in brecs:
        B[r["k"]].append(r)
    filed = _filed_count(finance_db) if finance_db else 0
    vraw = _vouchers(finance_db)
    if filed < 0 or (filed > 0 and not vraw):
        raise RuntimeError("Amir's filed vouchers could not be read (%s batches on file) -- nothing judged" % filed)
    V = collections.defaultdict(list)
    for vname, rows in vraw.items():
        for vd, vu in rows:
            if vd and vd > op:
                V[Z(vname)].append((vd, float(vu or 0)))
    amir = _amir_days(finance_db)
    n = len(closings)
    win = [[]] + [_days((dt.date.fromisoformat(closings[i - 1]) + dt.timedelta(days=1)).isoformat(), closings[i]) for i in range(1, n)]
    sales_ok = [False] + [bool(win[i]) and all(x in sale_cov for x in win[i]) for i in range(1, n)]
    pur_ok = [False] + [all(x in pur_cov for x in _days((dt.date.fromisoformat(closings[i - 1]) - dt.timedelta(days=7)).isoformat(), closings[i]))
                        for i in range(1, n)]
    pur_after = [False] + [bool(last_pur_taken) and (ctaken.get(closings[i]) is None or last_pur_taken > ctaken[closings[i]])
                           for i in range(1, n)]
    amir_in = [True] + [amir is None or any(x in amir for x in win[i]) for i in range(1, n)]
    explain = {}

    def _iso(d, plus=0):
        return (d + dt.timedelta(days=plus)).isoformat() if d else ""

    def brec_for(k, i, dlt, used, exact_only=False):
        """matcher 1: (record, exact?) for the step i of item k -- the same units, in the edit's window; or, for a purchase bill, the
        opposite units at the bill's own entry; or (a part) a record inside a larger move, in the edit's window."""
        lo, hi = closings[i - 1], closings[i]
        part = None
        for x, r in enumerate(B.get(k, [])):
            try:
                bd = dt.date.fromisoformat(str(r["bill_day"])[:10])
            except ValueError:
                continue                                           # a bill with no readable date explains nothing (never raises)
            wd = r["was_day"] or bd
            nd = r["now_day"] or wd
            edit_ok = hi >= _iso(wd, -1) and lo <= _iso(nd)
            orig_ok = r["side"] == "purchase" and hi >= _iso(bd, -1) and lo <= _iso(wd)
            if edit_ok and (x, "e") not in used and abs(dlt - r["delta"]) < TOL:
                used.add((x, "e"))
                return r, True
            if orig_ok and not exact_only and (x, "o") not in used and abs(dlt + r["delta"]) < TOL:
                used.add((x, "o"))
                return dict(r, note=r["note"] + " The move here is its first entry, before the change."), True
            if part is None and edit_ok and (x, "e") not in used and abs(r["delta"]) < abs(dlt) - TOL and abs(r["delta"]) <= max(2.0, 0.2 * abs(dlt)):
                part = (x, r)
        if part is not None and not exact_only:
            used.add((part[0], "e"))
            return part[1], False
        return None, False
    cand = []
    for k in set(M) | {k for k in moves if any(d > op for d, _u in moves[k])}:
        mv = sorted(moves.get(k, []))
        vv = sorted(V.get(k, []))
        mvd, mvc = [d for d, _u in mv], list(itertools.accumulate(u for _d, u in mv))
        vvd, vvc = [d for d, _u in vv], list(itertools.accumulate(u for _d, u in vv))
        E, m_, s_ = [], [], []
        for d in closings:
            i_m, i_v = bisect.bisect_right(mvd, d), bisect.bisect_right(vvd, d)
            s = mvc[i_m - 1] if i_m else 0.0
            v = vvc[i_v - 1] if i_v else 0.0
            m = M.get(k, {}).get(d, 0.0)
            E.append(m - s - v)
            m_.append(m)
            s_.append(s + v)
        steps = [(i, round(E[i] - E[i - 1], 3)) for i in range(1, n) if abs(E[i] - E[i - 1]) >= TOL]
        skip = set()
        for x, (i, dlt) in enumerate(steps):                      # a step undone within the next three closings
            if i in skip:
                continue
            for j, dj in steps[x + 1:]:
                if j > i + 3:
                    break
                if j not in skip and abs(dlt + dj) < TOL:
                    skip.update((i, j))
                    explain[(k, closings[i])] = explain[(k, closings[j])] = (
                        "undone", "", "Undone by %s: %s, then %s (a voucher or a bill keyed a day late)." % (
                            dmon(closings[j]), snum(dlt), snum(dj)))
                    break
        owed = owed_r = 0.0
        res = []                                                   # the residual of each step once purchase / return timing is paid
        used = set()
        for i, dlt in steps:
            if i in skip:
                continue
            d1 = closings[i]
            lo = (dt.date.fromisoformat(closings[i - 1]) - dt.timedelta(days=7)).isoformat()

            def hit(lst):
                pl = [u for pd, u in lst if lo < pd <= d1]
                return len(pl) <= 12 and any(abs(abs(dlt) - sum(c)) < TOL for r in (1, 2, 3) for c in itertools.combinations(pl, r))
            rec, exact = brec_for(k, i, dlt, used, exact_only=True)   # S812 matcher 1 FIRST, the edit itself: its units never pay a late bill
            if rec is not None:
                res.append(dict(i=i, dlt=dlt, adj=dlt, judged=True, paid=0.0, rec=("bill", rec["ref"], rec["note"]), part=[]))
                continue
            if not sales_ok[i]:                                    # S812 (F-1279): not judged, but a bill Marg has not taken in yet is
                if dlt < 0 and hit(purch.get(k, [])):              # still noted, so Marg's catch-up is paid from it
                    owed += -dlt
                continue
            paid = 0.0
            if dlt < 0:
                pay = min(owed_r, -dlt)                            # Marg takes a return in later than its bill date
                owed_r -= pay
                paid = -pay
                dlt = round(dlt + pay, 3)
                if dlt > -TOL:
                    explain[(k, d1)] = ("timing", "", "A purchase return Marg took in later than its date (%s)." % snum(-pay))
                    continue
                if hit(purch.get(k, [])):                          # a bill the system holds that Marg's closing did not have yet
                    owed += -dlt
                    explain[(k, d1)] = ("timing", "", "A purchase bill the system holds that Marg had not taken in yet (%s)." % num(-dlt))
                    continue
                judged = pur_ok[i] or not amir_in[i]
            else:
                pay = min(owed, dlt)
                owed -= pay
                paid = pay
                dlt = round(dlt - pay, 3)
                if dlt < TOL:
                    explain[(k, d1)] = ("timing", "", "Marg took in a purchase bill late: %s paid from a bill the system already held." % num(pay))
                    continue
                if hit(rets.get(k, [])):                           # a return the system holds that Marg has not taken yet
                    owed_r += dlt
                    continue
                judged = pur_ok[i] and pur_after[i]
            res.append(dict(i=i, dlt=dlt, adj=dlt, judged=judged, paid=paid, rec=None, part=[]))
        for r in res:                                              # S812 matcher 1, the parts: a changed bill inside a larger move
            if r["rec"]:
                continue
            rec, exact = brec_for(k, r["i"], r["dlt"], used)
            if rec is None:
                continue
            if exact:
                r["rec"] = ("bill", rec["ref"], rec["note"])
            else:
                r["part"].append(rec)
                r["adj"] = round(r["dlt"] - rec["delta"], 3)
        gone = set()                                               # S706 R3: residuals that undo each other within three closings
        for x, r in enumerate(res):
            if r["i"] in gone or r["rec"]:
                continue
            for r2 in res[x + 1:]:
                if r2["i"] > r["i"] + 3:
                    break
                if r2["i"] not in gone and not r2["rec"] and abs(r["adj"] + r2["adj"]) < TOL:
                    gone.update((r["i"], r2["i"]))
                    note = "A bill Marg took in at another closing: %s here, %s on %s." % (snum(r["adj"]), snum(r2["adj"]), dmon(closings[r2["i"]]))
                    for z in (r, r2):
                        z["rec"] = ("timing", "", note + "".join(" " + p["note"] for p in z["part"]))
                        z["keep"] = bool(z["part"]) or bool(r["part"]) or bool(r2["part"])
                    break
        for r in res:
            i, dlt = r["i"], r["dlt"]
            d1 = closings[i]
            if d1 < from_day and not (K(names.get(k, k)) in NOTES and d1 <= NOTES_TO):   # the owner's table stays whole
                continue
            if r["i"] in gone and not r.get("keep"):
                explain[(k, d1)] = r["rec"]
                continue
            rk = r["rec"]
            if rk is None and r["part"]:                           # a record inside a larger move: the move is still counted, its sum said
                rk = (None, "", "Inside it: " + " ".join(p["note"] for p in r["part"]))
            cand.append(dict(k20=k, item=names.get(k, k), day_from=closings[i - 1], day_to=d1, marg_from=m_[i - 1], marg_to=m_[i],
                             system_moved=round(s_[i] - s_[i - 1], 3), shift=dlt, e_before=E[i - 1], e_now=E[-1] if E else 0.0,
                             kind="hand" if (r["judged"] or (rk and rk[0])) else "wait", pair_item="", owed_paid=round(r["paid"], 3),
                             rec_kind=(rk or (None,))[0], rec_ref=(rk or (None, ""))[1] if rk else "", rec_note=(rk[2] if rk else ""), _i=i))
    by_day = collections.defaultdict(list)
    for c in cand:
        by_day[c["day_to"]].append(c)
    for d, cs in by_day.items():
        if len(cs) > 400:
            continue
        for a, b in itertools.combinations(cs, 2):
            if a["kind"] != "rename" and b["kind"] != "rename" and abs(a["shift"] + b["shift"]) < TOL and _anagram(a["item"], b["item"]):
                a["kind"] = b["kind"] = "rename"
                a["pair_item"], b["pair_item"] = b["item"], a["item"]
                a["rec_kind"] = b["rec_kind"] = None
    cand = [c for c in cand if c["kind"] != "wait"]
    stems = collections.defaultdict(set)                           # S812 matchers 3 - 6, in the plan's order, on what is still counted
    for k in set(names) | set(V):
        stems[_stem(names.get(k, k))].add(k)
    left = {}                                                      # each filed voucher explains at most its own units (the review's MUST 1, 3)
    for k, vs in V.items():
        for x, (vd, vu) in enumerate(vs):
            left[(k, x)] = vu

    def take(k, x, units):
        left[(k, x)] = round(left[(k, x)] - units, 3)

    def free_c(c):
        return c["kind"] == "hand" and not c["rec_kind"]
    for c in cand:
        if not free_c(c):
            continue
        k, i, s = c["k20"], c["_i"], c["shift"]
        wlo, whi = closings[max(0, i - 4)], closings[min(n - 1, i + 3)]
        early = (dt.date.fromisoformat(c["day_to"]) - dt.timedelta(days=VOUCHER_BACK_DAYS)).isoformat()
        pre = c["day_to"] < from_day                               # a move from before the page's first day (the owner's table of 05-Nov)

        def inw(vd):
            """A voucher in the move's window: three closings either side; or filed up to VOUCHER_BACK_DAYS before it (count #1's vouchers
            carry 15-Oct and were keyed into Marg days later); or, for a move from before from_day, any voucher up to from_day (count #1
            reconciled that period)."""
            return (wlo < vd <= whi) or (early < vd <= c["day_to"]) or (pre and c["day_from"] < vd <= from_day)
        st = _stem(c["item"])
        sib = [y for y in stems.get(st, ()) if y != k] if st else []
        hit3 = None
        # 3 a voucher filed on the wrong size or form: the SIBLING shows the opposite move on the same closing, unexplained, and one filed
        #   voucher of these units -- on the sibling (= this move) or on this item (= minus this move) -- is used up by the pair.
        for o in cand:
            if o is c or not free_c(o) or o["k20"] not in sib or o["day_to"] != c["day_to"] or abs(o["shift"] + s) >= TOL:
                continue
            vx = next((("o", x) for x, (vd, vu) in enumerate(V.get(o["k20"], [])) if inw(vd) and abs(left[(o["k20"], x)] - s) < TOL), None) or \
                next((("c", x) for x, (vd, vu) in enumerate(V.get(k, [])) if inw(vd) and abs(left[(k, x)] + s) < TOL), None)
            if vx is None:
                continue
            on, x = (o["k20"], vx[1]) if vx[0] == "o" else (k, vx[1])
            vd, vu = V[on][x]
            take(on, x, vu)
            note = ("Amir's voucher of %s (%s) was filed on %s; in Marg the stock moved on %s (%s) and %s (%s)."
                    % (snum(vu), dmon(vd), names.get(on, on), c["item"], snum(s), o["item"], snum(o["shift"])))
            for z, other in ((c, o), (o, c)):
                z["rec_kind"], z["rec_ref"], z["rec_note"] = "sibling", other["item"], note
            hit3 = True
            break
        if hit3:
            continue
        if K(c["item"]) in SIBLING_NOTES and (pre or c["day_to"] == NOTES_DAY.get(K(c["item"]))):
            for y in sib:                                          # 3c only where the owner's table itself names the sibling's voucher
                sv = [(vd, vu) for vd, vu in V.get(y, []) if inw(vd)]
                if sv:
                    c["rec_kind"], c["rec_ref"] = "sibling", names.get(y, y)
                    c["rec_note"] = ("Amir's voucher of %s (%s) was filed on %s, not on this item (your table of 5-Nov); Marg moved %s here."
                                     % (", ".join(snum(vu) for _d, vu in sv), ", ".join(dmon(vd) for vd, _u in sv), names.get(y, y), snum(s)))
                    hit3 = True
                    break
        if hit3:
            continue
        # 4 a voucher of another quantity on the same item: the same direction, within three closings (or count #1's for a move before
        #   from_day), and only as far as the voucher's units are not used up
        own = [(x, vd, vu) for x, (vd, vu) in enumerate(V.get(k, [])) if ((wlo < vd <= whi) or (pre and c["day_from"] < vd <= from_day))
               and vu * s > 0 and abs(s) <= abs(left[(k, x)]) + TOL]
        if own:
            x, vd, vu = own[0]
            take(k, x, s)
            c["rec_kind"], c["rec_ref"] = "voucher_qty", ""
            c["rec_note"] = "Amir's voucher here says %s (%s); Marg moved %s — part of it, the same way." % (snum(vu), dmon(vd), snum(s))
            continue
        lo_d = c["day_from"]
        if s > 0:                                                  # 5 a sale Marg did not take off: the window's ONE sale, or all of them
            ws = [(d, u, ref) for d, u, ref in sales.get(k, []) if lo_d < d <= c["day_to"]]
            one = ws[0] if (len(ws) == 1 and abs(ws[0][1] + s) < TOL) else None
            if one or (len(ws) > 1 and abs(sum(u for _d, u, _r in ws) + s) < TOL):
                c["rec_kind"], c["rec_ref"] = "sale_not_off", (str(one[2] or "") if one else "%d sales" % len(ws))
                c["rec_note"] = ("The sale %s (%s) of %s did not come off Marg's stock." % (one[2], dmon(one[0]), num(-one[1])) if one else
                                 "The window's %d sales (%s) did not come off Marg's stock." % (len(ws), num(s)))
                continue
            lo7 = (dt.date.fromisoformat(lo_d) - dt.timedelta(days=7)).isoformat()
            frs = [(d, u, b) for d, u, b in frees.get(k, []) if lo7 < d <= c["day_to"]]
            if len(frs) == 1 and abs(frs[0][1] - s) < TOL:        # 6 free goods counted in Marg: the window's ONE free line, of these units
                d, u, b = frs[0]
                c["rec_kind"], c["rec_ref"] = "free", "bill %s" % b
                c["rec_note"] = "Equal to the free goods on bill %s (%s): Marg counted %s free." % (b, dmon(d), num(u))
                continue
    for c in cand:
        c["settled"] = abs(c.pop("e_now") - c.pop("e_before")) < TOL
        c.pop("_i", None)
        rp = rate.get(c["k20"], rate.get("~" + c["k20"]))
        c["rate_p"] = rp
        c["value_p"] = int(round(c["shift"] * rp)) if rp is not None else None
    cand.sort(key=lambda c: (c["day_to"], c["item"]))
    judged_to = max([closings[i] for i in range(1, n) if sales_ok[i]] or [""])
    return cand, dict(built=meta.get("built", ""), closings=len(closings), skipped=len(allc) - len(closings), judged_to=judged_to,
                      last_pur=max(pur_cov) if pur_cov else "", op=op, amir_days=("unreadable: every day counts as his" if amir is None
                                                                                   else len(amir)), vouchers=filed, explain=explain,
                      bills=len(brecs), bills_why=b_why or "",
                      pur_after_to=max([closings[i] for i in range(1, n) if pur_after[i]] or [""]),
                      last_pur_taken=last_pur_taken.strftime("%Y-%m-%d %H:%M") if last_pur_taken else "")


