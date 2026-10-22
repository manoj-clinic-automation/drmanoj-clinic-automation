# S628 anchored edits for /root/finance/stock_figure.py (FROM 8c66b6b1)
EDITS = []

EDITS.append(("""VERSION = "1.4"
KIT = "S613_S605_FOLLOWUP"                               # v1.4 S613 (after S602)""", """VERSION = "1.5"
KIT = "S628_ONE_NAME_LIST"                               # v1.5 S628 (the one name list: Marg partners read by printed_forms / _carried), v1.4 S613 (after S602)"""))

EDITS.append(("""    out = [str(name)]
    if gi is not None:
        for f in groups[gi]:
            if norm(f) != norm(name):
                out.append(f)
    return out


def key_of(""", """    out = [str(name)]
    if gi is not None:
        for f in groups[gi]:
            if norm(f) != norm(name):
                out.append(f)
    return out


def arrival_forms(con, name, ctx=None):
    \"\"\"S628 (D761): printed_forms PLUS the name's Marg partners from the one name list (med_names: THIO Q AP TAB for THIO Q AP) -- read ONLY
    where a bill line is matched to an order line (_line_forms: carried, rule b, the family's bill). printed_forms itself is unchanged, so a
    stock figure, a count, a closing and a split are per Marg item exactly as before.\"\"\"
    ctx = _ctx(con, None, ctx)
    out = list(printed_forms(ctx.con, name, ctx))
    for f in _same(ctx, name):
        if norm(f) not in {norm(x) for x in out}:
            out.append(f)
    return out


def _same(ctx, name):
    \"\"\"S628: med_names.same_items(name) read once per name and Ctx -- the other Marg items that are this medicine; [] when the list is absent
    or unreadable (fail-soft: the estate reads as before S628). Plain SQL -- it never calls key_of (no recursion).\"\"\"
    ck = ("same", norm(name))
    if ck not in ctx.c:
        try:
            import med_names                                  # noqa: PLC0415 -- beside this file (S628); it never imports stock_figure at import
            ctx.c[ck] = list(med_names.same_items(ctx.con, name)) if ctx.con is not None else []
        except Exception:                                     # noqa: BLE001
            ctx.c[ck] = []
    return ctx.c[ck]


def _same_keys(sp, name, k, ctx):
    \"\"\"S628: the spine keys of the name's Marg partners other than its own key k (each read by key_of: the partner's own sp_item key).\"\"\"
    out = []
    for f in _same(ctx, name):
        try:
            k2 = key_of(sp, f, ctx)
        except Exception:                                     # noqa: BLE001
            continue
        if k2 and k2 != k and k2 not in out:
            out.append(k2)
    return out


def key_of("""))

EDITS.append(("""    fs = list(printed_forms(ctx.con, name, ctx))
    if len(name.strip()) >= 27:""", """    fs = list(arrival_forms(ctx.con, name, ctx))             # S628: the Marg partners too (arrival matching only)
    if len(name.strip()) >= 27:"""))

EDITS.append(("""            rows = sp.q("SELECT l.supkey AS supkey, l.bill AS bill, l.date AS date, l.seq AS seq, l.name27 AS name27, l.qty AS qty, l.free AS free, l.units AS units, "
                        "MAX(b.supplier) AS supplier FROM""", """            rows = sp.q("SELECT l.supkey AS supkey, l.bill AS bill, l.date AS date, l.seq AS seq, l.name27 AS name27, l.qty AS qty, l.free AS free, l.units AS units, "
                        "l.packing AS packing, MAX(b.supplier) AS supplier FROM"""))

EDITS.append(("""            rows = sp.q("SELECT supkey, bill, date, seq, name27, qty, free, units, supkey AS supplier FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' \"""",
              """            rows = sp.q("SELECT supkey, bill, date, seq, name27, qty, free, units, packing, supkey AS supplier FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' \""""))

EDITS.append(("""    sx = split_of(sp, line.get("item"), ctx)                  # S613 (F-951): a split size reads its new key's lines and its old key's by name (R1-B3)

    def lines_of(since):
        if sx is not None:
            return _split_lines(sp, sx, since, ctx)
        return [(p, k, sib) for p in _purchase_lines_of(sp, k, since, ctx)]""", """    sx = split_of(sp, line.get("item"), ctx)                  # S613 (F-951): a split size reads its new key's lines and its old key's by name (R1-B3)
    same_k = _same_keys(sp, line.get("item"), k, ctx)         # S628 (D761): the keys of the Marg items that are this medicine (med_names)

    def lines_of(since):
        if sx is not None:
            rows = list(_split_lines(sp, sx, since, ctx))
        else:
            rows = [(p, k, sib) for p in _purchase_lines_of(sp, k, since, ctx)]
        if same_k:                                            # S628: a partner's lines join, each matched under its own key's sib, one order
            rows += [(p, k2, _siblings(sp, k2, ctx)) for k2 in same_k for p in _purchase_lines_of(sp, k2, since, ctx)]
            rows.sort(key=lambda t: (str(t[0]["date"] or ""), str(t[0]["bill"] or ""), _seqkey(t[0]["seq"])))
        return rows"""))

EDITS.append(("""                    seq=(p.get("seq") if hit else None), name27=(str(p.get("name27") or "") if hit else ""), how="a")""",
              """                    seq=(p.get("seq") if hit else None), name27=(str(p.get("name27") or "") if hit else ""), how="a",
                    packing=(str(p.get("packing") or "") if hit else ""))"""))

EDITS.append(("""    taken = _taken_split(sp, sx, lid, ctx) if sx is not None else _taken_lines(sp, k, lid, ctx)
    hit, hkey = None, None""", """    taken = _taken_split(sp, sx, lid, ctx) if sx is not None else _taken_lines(sp, k, lid, ctx)
    for k2 in same_k:                                         # S628: rule (b) over every key of the medicine -- one bill line, one order line
        taken = list(taken) + [t for t in _taken_lines(sp, k2, lid, ctx) if t not in taken]
    hit, hkey = None, None"""))

EDITS.append(("""            hit = dict(supplier=str(p.get("supplier") or sk), supkey=sk, bill=str(p["bill"] or ""), date=d, units=float(p["units"] or 0),
                       qty=float(p["qty"] or 0), free=float(p["free"] or 0), seq=p["seq"], name27=str(p["name27"] or ""), how=how)""",
              """            hit = dict(supplier=str(p.get("supplier") or sk), supkey=sk, bill=str(p["bill"] or ""), date=d, units=float(p["units"] or 0),
                       qty=float(p["qty"] or 0), free=float(p["free"] or 0), seq=p["seq"], name27=str(p["name27"] or ""), how=how,
                       packing=str(p.get("packing") or ""))"""))

EDITS.append(("""    ck = ("carried", line.get("line_id"), norm(line.get("item")), _sw().supkey(line.get("vendor")), str(line.get("order_at") or "")[:10], _bill(line.get("billed_bill_no")))""",
              """    ck = ("carried", line.get("line_id"), norm(line.get("item")), _sw().supkey(line.get("vendor")), str(line.get("order_at") or "")[:10], _bill(line.get("billed_bill_no")),
          bool(line.get("own_only")))                         # S628: own_only -- only the order's own dealer's bills (porders.detect_supplies)"""))

EDITS.append(("""        old_line = sx is not None and pk == sx["old_k"]       # S613: an old-key line is matched by printed name only, whoever matches it""",
              """        if line.get("own_only") and not (own and sk == own):
            continue                                          # S628: the own dealer's bill first -- an older other-dealer line never hides it
        old_line = sx is not None and pk == sx["old_k"]       # S613: an old-key line is matched by printed name only, whoever matches it"""))

EDITS.append(("""                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''"):
                    if key_of(sp, item, ctx) == k20:""", """                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''").fetchall() + _other_taken(ctx):
                    if key_of(sp, item, ctx) == k20:"""))

EDITS.append(("""                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''"):
                    kk = key_of(sp, item, ctx)""", """                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''").fetchall() + _other_taken(ctx):
                    kk = key_of(sp, item, ctx)"""))

EDITS.append(("""def _taken_split(sp, sx, line_id, ctx):""", """def _other_taken(ctx):
    \"\"\"S628 (F-991): the order lines credited with ANOTHER dealer's bill line (other_bill_no) as rule (b) entries (id, item, bill, that dealer) --
    so one bill line is never credited twice. [] before S628's columns exist.\"\"\"
    if "othtaken" not in ctx.c:
        try:
            ctx.c["othtaken"] = [tuple(r) for r in ctx.con.execute("SELECT id, item, other_bill_no, other_supplier FROM purchase_order_line "
                                                                    "WHERE COALESCE(other_bill_no,'')<>''")] if ctx.con is not None else []
        except sqlite3.Error:
            ctx.c["othtaken"] = []
    return list(ctx.c["othtaken"])


def _taken_split(sp, sx, line_id, ctx):"""))
