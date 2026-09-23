#!/usr/bin/env python3
"""make_s379.py -- kit S379_PARCHI_TIDY (session 279, 23-Sep-2026). Anchored edits on the LIVE bytes:
    slip_log.py            0b3195d2 (S330)
    finance_clinic_day.py  738308b3 (S372)
    clinic_day_pdf.py      ce843733 (S372)
slip_lookup.py (S372, 06e06cd0) is replaced whole by the kit's own copy (it is this project's file, one function added).

THE OWNER, 23-Sep-2026:
  "In the Parchi system, doctor's upload is no longer relevant, but it is still there. Please remove it."
  "the slips numbering in the ... day statement should come in an incremental order and not randomly. That is how
   the physical register is designed. If any number is skipped, mention it there."
  "for the Naya Mareez, the overnight report gives you the name of that patient so you can populate the name"
  "few x rays need to be added, and procedures get a discount sometimes, build what's needed"
  python3 make_s379.py <dir with the four live files> <out dir>
"""
import hashlib, os, sys
SRC, OUT = sys.argv[1], sys.argv[2]
PIN = {"slip_log.py": "0b3195d2610e64a4b637e0ed89eb8454", "finance_clinic_day.py": "738308b3af38db09d98b25a450d98bef",
       "clinic_day_pdf.py": "ce843733539bb091d86abf1f664c43d7"}
T = {}
for f, m in PIN.items():
    T[f] = open(os.path.join(SRC, f), encoding="utf-8").read()
    assert hashlib.md5(T[f].encode("utf-8")).hexdigest() == m, "%s is not %s" % (f, m[:8])


def rep(f, old, new, n=1):
    assert T[f].count(old) == n, "%s: anchor count %d != %d: %r" % (f, T[f].count(old), n, old[:80])
    T[f] = T[f].replace(old, new)


S = "slip_log.py"
# ---- the header
rep(S, '''S330: blood tests: new = above the highest ID issued before the day.''',
    '''S330: blood tests: new = above the highest ID issued before the day. S379 (23-Sep-2026): the Docterz upload screen retired (X-rays are filed by themselves now), a new patient's name filled from the overnight Docterz report, a discount on a procedure.''')

# ---- (5) the discount column, added once
rep(S, '''    con.executescript(SCHEMA)
    for s, (a, b) in BOOKS.items():''', '''    con.executescript(SCHEMA)
    try:                                                  # S379: a procedure can carry a discount (the owner)
        if "discount_p" not in {r[1] for r in con.execute("PRAGMA table_info(slip_item)")}:
            con.execute("ALTER TABLE slip_item ADD COLUMN discount_p INTEGER NOT NULL DEFAULT 0")
    except Exception:                                    # noqa: BLE001 -- the slip still saves without it
        pass
    for s, (a, b) in BOOKS.items():''')
rep(S, '''        con.execute("INSERT INTO slip_item(slip_id, kind, service_id, name, side, price_p, sort) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (sid, it["kind"], it.get("service_id"), it["name"], it.get("side", ""),
                     int(it.get("price_p") or 0), i))''', '''        con.execute("INSERT INTO slip_item(slip_id, kind, service_id, name, side, price_p, sort, discount_p) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (sid, it["kind"], it.get("service_id"), it["name"], it.get("side", ""),
                     int(it.get("price_p") or 0), i, int(it.get("discount_p") or 0)))''')
rep(S, '''            s = byid.get(_int(v))
            if s is None or (s in xr) != (kind == "xray"):
                raise SlipError("List mein se chunein.")
            out.append({"kind": kind, "service_id": s["id"], "name": s["name"], "side": side,
                        "price_p": s["price_p"]})
    return out''', '''            s = byid.get(_int(v))
            if s is None or (s in xr) != (kind == "xray"):
                raise SlipError("List mein se chunein.")
            disc = 0
            if kind == "proc":                            # S379: "procedures get a discount sometimes" (the owner)
                dv = (form.get("%s%d_disc" % (kind, i)) or "").strip().replace(",", "")
                if dv:
                    d = _int(dv)
                    if d is None or d < 0:
                        raise SlipError("Chhoot mein sirf rupaye likhein.")
                    disc = d * 100
                    if s["price_p"] and disc > s["price_p"]:
                        raise SlipError("%s: chhoot %s rate %s se zyada nahi ho sakti." % (s["name"], _rs(disc), _rs(s["price_p"])))
            out.append({"kind": kind, "service_id": s["id"], "name": s["name"], "side": side,
                        "price_p": s["price_p"], "discount_p": disc})
    return out''')
rep(S, '''    for it in items:
        s = it["name"] + ((" " + it["side"]) if it.get("side") else "")
        out.append(s)
    return ", ".join(out)''', '''    for it in items:
        s = it["name"] + ((" " + it["side"]) if it.get("side") else "")
        if int(it.get("discount_p") or 0):                # S379
            s += " (chhoot %s)" % _rs(it["discount_p"])
        out.append(s)
    return ", ".join(out)''')
rep(S, '''    tot = sum(int(it.get("price_p") or 0) for it in items)
    unpriced''', '''    tot = sum(int(it.get("price_p") or 0) - int(it.get("discount_p") or 0) for it in items)   # S379: after discount
    unpriced''')
rep(S, '''                if want != got:
                    why.append("X-ray: slip rates %s, Docterz %s" % (_rs(want), _rs(got)))''', '''                if want != got:
                    why.append("X-ray: slip rates %s, Docterz %s" % (_rs(want), _rs(got)))
            if sp and dp and all(it["price_p"] > 0 for it in sp):        # S379: procedures, after any discount
                disc = sum(int(it.get("discount_p") or 0) for it in sp)
                want = sum(it["price_p"] for it in sp) - disc
                got = sum(ln["amount_p"] for ln in dp)
                if want != got:
                    why.append("procedure: slip %s%s, Docterz %s" % (
                        _rs(want), (" after %s discount" % _rs(disc)) if disc else "", _rs(got)))''')
rep(S, '''            '<input name="%s%d_other" class="oth" placeholder="naam (zaroori nahi)" maxlength="60" hidden></div>'
            % (kind, "" if i == 0 else " hidden", kind, i, _opts(rows, label), kind, i, kind, i))''',
    '''            '<input name="%s%d_other" class="oth" placeholder="naam (zaroori nahi)" maxlength="60" hidden>%s</div>'
            % (kind, "" if i == 0 else " hidden", kind, i, _opts(rows, label), kind, i, kind, i,
               ('<input name="%s%d_disc" class="disc" inputmode="numeric" placeholder="chhoot ₹ (ho to)" '
                'maxlength="6" hidden>' % (kind, i)) if kind == "proc" else ""))''')
rep(S, '''      var s=r.querySelector('.svc'),sd=r.querySelector('.side'),o=r.querySelector('.oth');
      s.addEventListener('change',function(){var op=s.options[s.selectedIndex];''', '''      var s=r.querySelector('.svc'),sd=r.querySelector('.side'),o=r.querySelector('.oth'),ds=r.querySelector('.disc');
      s.addEventListener('change',function(){var op=s.options[s.selectedIndex];
        if(ds){ds.hidden=(!s.value||s.value==='other');if(ds.hidden)ds.value='';}''')

# ---- (3) a new patient's name from the overnight Docterz report
rep(S, '''def _who_label(r):
    if r.get("no_id_name"):
        return "%s (ID nahi)" % r["no_id_name"]
    if r.get("name_seen"):
        return "%s · %s" % (r["clinic_id"], r["name_seen"])''', '''def fill_new_names(con):
    """S379, the owner 23-Sep-2026: "for the Naya Mareez, the overnight report gives you the name of that patient".
    A new patient's slip carries the ID only; once the Docterz export of that day has arrived, the name it gives
    for that ID is written into the slip (name_seen), once. The slip table only; never a guess."""
    try:
        rows = con.execute("SELECT id, clinic_id, day FROM slip WHERE is_new=1 AND name_seen='' AND clinic_id<>'' "
                           "AND state='ok'").fetchall()
        n = 0
        for r in rows:
            d = con.execute("SELECT patient FROM clinic_day_line WHERE clinic_id=? AND patient<>'' "
                            "ORDER BY (business_date=?) DESC, business_date DESC LIMIT 1", (r["clinic_id"], r["day"])).fetchone()
            if d and (d["patient"] or "").strip():
                con.execute("UPDATE slip SET name_seen=? WHERE id=? AND name_seen=''", (d["patient"].strip()[:80], r["id"]))
                n += 1
        if n:
            con.commit()
        return n
    except Exception:                                    # noqa: BLE001 -- no Docterz table: the ID alone, as before
        return 0


def _who_label(r):
    if r.get("no_id_name"):
        return "%s (ID nahi)" % r["no_id_name"]
    if r.get("name_seen") and r.get("is_new"):
        return "%s · %s · naya" % (r["clinic_id"], r["name_seen"])
    if r.get("name_seen"):
        return "%s · %s" % (r["clinic_id"], r["name_seen"])''')
rep(S, '''    con = _db()
    ensure(con)
    if "checker" in _roles(u) and "maker" not in _roles(u) and not request.args.get("tile"):''', '''    con = _db()
    ensure(con)
    fill_new_names(con)                                   # S379
    if "checker" in _roles(u) and "maker" not in _roles(u) and not request.args.get("tile"):''')
rep(S, '''    return _shell("Parchi & upload", _tile_html(con, u), "hi")''', '''    return _shell("Parchi", _tile_html(con, u), "hi")''')
rep(S, '''    if not _iso_ok(day):
        return redirect("/finance/slips/report", code=302)
    return _shell''', '''    if not _iso_ok(day):
        return redirect("/finance/slips/report", code=302)
    fill_new_names(con)                                   # S379
    return _shell''')

# ---- (1) the Docterz upload screen retired: menu, report section, routes; the blood questions move to Blood test
rep(S, '''    try:
        emr_n, _old = emr_pending_count(con)
        emr_n += len([o for o in blood_state(con)[0] if not o["outcome"]])
    except Exception:                                    # noqa: BLE001
        emr_n = 0
    user = _who(u).lower()''', '''    try:                                                  # S379: the Docterz upload screen is retired (the owner);
        blood_n = len([o for o in blood_state(con)[0] if not o["outcome"]])   # its blood questions live on Blood test
    except Exception:                                    # noqa: BLE001
        blood_n = 0
    user = _who(u).lower()''')
rep(S, '''        "emr": ('<a class="mi" href="/finance/slips/emr"><b>Docterz upload</b><span class="%s">%d baaki</span></a>'
                % ("hot" if emr_n else "", emr_n)),
        "blood": '<a class="mi" href="/finance/slips/blood"><b>Blood test</b><span>chamber se</span></a>',''',
    '''        "blood": ('<a class="mi" href="/finance/slips/blood"><b>Blood test</b><span class="%s">%s</span></a>'
                  % ("hot" if blood_n else "", ("%d report nahi aaye" % blood_n) if blood_n else "chamber se")),''')
rep(S, '''    if user == "awdhesh":
        order = ["room", "xp", "opd", "blood", "emr", "list"]
    elif user in ("alisha", "shivani"):
        order = ["emr", "opd", "xp", "blood", "room", "list"]
    else:
        order = ["opd", "xp", "blood", "room", "emr", "list"]''', '''    if user == "awdhesh":
        order = ["room", "xp", "opd", "blood", "list"]
    elif user in ("alisha", "shivani"):
        order = ["opd", "xp", "blood", "room", "list"]
    else:
        order = ["opd", "xp", "blood", "room", "list"]''')
rep(S, '''    try:
        n_emr, old_emr = emr_pending_count(con)
    except Exception:                                    # noqa: BLE001
        n_emr, old_emr = 0, None
    if n_emr:''', '''    n_emr, old_emr = 0, None                              # S379: the Docterz upload list is retired (the owner)
    if n_emr:''')
rep(S, '''    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return _shell("EMR upload", _denied(), "en")
    con = _db()
    items = emr_items(con)''', '''    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return _shell("EMR upload", _denied(), "en")
    return redirect("/finance/slips/blood", code=303)     # S379: retired -- X-rays are filed by themselves (S374)
    con = _db()
    items = emr_items(con)''')
rep(S, '''    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    con = _db()
    ensure(con)
    emr_ensure(con)
    who, now = _who(u), _stamp()''', '''    u, err = _require("maker", unit=UNIT)
    if err:
        return err
    return redirect("/finance/slips", code=303)           # S379: retired
    con = _db()
    ensure(con)
    emr_ensure(con)
    who, now = _who(u), _stamp()''')
rep(S, '''    body.append(_sec("bl", "Aaj ke blood test", "%d" % len(mine), li or '<p class="sm">Abhi koi nahi.</p>'))
    body.append(_TILE_JS)''', '''    body.append(_sec("bl", "Aaj ke blood test", "%d" % len(mine), li or '<p class="sm">Abhi koi nahi.</p>'))
    try:                                                  # S379: moved here from the retired Docterz upload screen
        body.append(_blood_open_html(blood_state(con)[0]))
    except Exception:                                    # noqa: BLE001
        pass
    body.append(_TILE_JS)''')
rep(S, '''    return redirect("/finance/slips/emr?ok=" + _q("Theek."), code=303)''',
    '''    return redirect("/finance/slips/blood", code=303)     # S379: the questions live on Blood test now''')

# ---- (2) the day statement in slip order, skipped numbers named -- finance_clinic_day.py
F = "finance_clinic_day.py"
rep(F, '''    for key, title in SECTIONS:
        rows = sorted(by.get(key, []),
                      key=lambda l: (_SHIFT_ORDER.get((l["shift"] or "").strip().lower(), 9),
                                     l["sn"]))
        if not rows:
            continue
        out.append(_section(title, rows, slips, key))''', '''    if slip_lookup and hasattr(slip_lookup, "book_check"):             # S379: skipped slip numbers, named
        out.append(_books_card(slip_lookup.book_check(con, date)))
    for key, title in SECTIONS:
        rows = sorted(by.get(key, []),
                      key=lambda l: (_SHIFT_ORDER.get((l["shift"] or "").strip().lower(), 9),
                                     l["sn"]))
        if slip_lookup and hasattr(slip_lookup, "slip_order"):         # S379: the register's order (the owner)
            rows = slip_lookup.slip_order(rows, slips, key)
        if not rows:
            continue
        out.append(_section(title, rows, slips, key))''')
rep(F, '''def _section(title, rows, slips=None, key=""):''', '''def _books_card(books):
    """S379, the owner 23-Sep-2026: "the slips numbering ... should come in an incremental order ... If any number is
    skipped, mention it there." One line per book: the day's numbers, and every number skipped with its reason."""
    if not books:
        return ""
    li = []
    for b in books:
        sk = b["skipped"]
        txt = ("%s book: slips %d–%d · %d written" % (_esc(b["label"]), b["first"], b["last"], b["written"]))
        if sk:
            txt += " · <b>skipped: %s</b>" % ", ".join("%d (%s)" % (n, _esc(w)) for n, w in sk)
        else:
            txt += " · no number skipped"
        li.append("<li>%s</li>" % txt)
    return ('<div class="card"><h2>Slip books</h2><ul class="books">%s</ul>'
            '<p class="sub">Each section below runs in slip-number order, as the register does; '
            'a Docterz entry with no slip comes at the end of its section.</p></div>' % "".join(li))


def _section(title, rows, slips=None, key=""):''')

# ---- the PDF: the same order and the same skipped line
P = "clinic_day_pdf.py"
rep(P, '''    for key, title in SECTIONS:
        rows = sorted(by.get(key, []),
                      key=lambda l: (_SHIFT_ORDER.get((l["shift"] or "").strip().lower(), 9),
                                     l["sn"]))
        if rows:
            sections.append((title, rows, key))''', '''    for key, title in SECTIONS:
        rows = sorted(by.get(key, []),
                      key=lambda l: (_SHIFT_ORDER.get((l["shift"] or "").strip().lower(), 9),
                                     l["sn"]))
        if slip_lookup and hasattr(slip_lookup, "slip_order"):         # S379: the register's order
            rows = slip_lookup.slip_order(rows, slips, key)
        if rows:
            sections.append((title, rows, key))
    books = []
    if slip_lookup and hasattr(slip_lookup, "book_check"):             # S379: skipped slip numbers
        books = slip_lookup.book_check(con, date)''')
rep(P, '''            "tender": _tender(day), "splits": sorted(sby.items()), "slips": slips}''',
    '''            "tender": _tender(day), "splits": sorted(sby.items()), "slips": slips, "books": books}''')
rep(P, '''    slips = d.get("slips") or {}
    for title, rows, key in d["sections"]:''', '''    slips = d.get("slips") or {}
    for b in d.get("books") or []:                                    # S379: every skipped slip number, named
        t = "%s book: slips %d-%d, %d written - " % (b["label"], b["first"], b["last"], b["written"])
        t += ("skipped: " + ", ".join("%d (%s)" % (n, w) for n, w in b["skipped"])) if b["skipped"] else "no number skipped"
        for ln in _wrap(_latin(t), 9, _R - _L):
            doc.line_text(ln, 9, bold=bool(b["skipped"]))
    for title, rows, key in d["sections"]:''')

os.makedirs(OUT, exist_ok=True)
for f in PIN:
    open(os.path.join(OUT, f), "w", encoding="utf-8").write(T[f])
    print(f, "->", hashlib.md5(T[f].encode("utf-8")).hexdigest())
