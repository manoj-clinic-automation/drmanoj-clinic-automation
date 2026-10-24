#!/usr/bin/python3
"""make_s640.py -- kit S640_DAY_CHECK_LISTS: counted edits on the REAL bytes (F-472) of
    /root/finance/day_check.py f223cbf6 (S636, live; = the kit's own read-back), /root/finance/aaj_seed.py a97cd07b,
    /root/finance/aaj_kaam.html b58d8f76, /root/finance/aaj_duties.json fa5cfac5 (the 24-Oct bundle).
python make_s640.py <dir holding the four files> <out_dir>. Every anchor must occur exactly once or nothing is written."""
import hashlib, os, sys

FROM = {"day_check.py": "f223cbf68450fe2043068d6698d68a3a", "aaj_seed.py": "a97cd07bfc7270184c62c16dff4dff48",
        "aaj_kaam.html": "b58d8f76880b08ff94edeb2f76e01e55", "aaj_duties.json": "fa5cfac53ee1cd3dc1721a00a9cc3dde"}

DC = [
 # 1 -- a tick older than the next Docterz export that still shows the line is no tick: 'not fixed'; the re-export state
 ('''    ticks = _ticks(con, d)
    for c in cards:
        c["tick"] = ticks.get(c["key"])
    out["state"] = "checked"
''', '''    ticks = _ticks(con, d)
    exported = _export_at(con, d)                        # S640 (D776 stage 3): when Docterz's file for the day last came in
    for c in cards:
        t = ticks.get(c["key"])
        c["tick"], c["not_fixed"] = t, None
        if t and exported and str(t["at"]) < str(exported):
            c["tick"], c["not_fixed"] = None, t          # the export after the tick still shows the line: back to staff
    dcs = [c for c in cards if c["who"] == "docterz"]
    out["reexport"] = bool(dcs) and all(c["tick"] for c in dcs) and any(c["tick"]["act"] in ("added", "changed", "found") for c in dcs)
    out["notright"] = sum(1 for c in dcs if c["tick"] and c["tick"]["act"] == "notright")
    out["not_fixed"] = sum(1 for c in cards if c.get("not_fixed"))
    out["state"] = "checked"
'''),
 # 2 -- his line: 'Re-export <day> from Docterz' once the day's Docterz lines are all ticked
 ('''    c = chk["counts"]
    parts = []
    if c["missing_p"]:
        parts.append("%s Docterz entry missing" % rs(c["missing_p"]))
    if c["modes"]:
        parts.append("%d payment mode%s wrong" % (c["modes"], "" if c["modes"] == 1 else "s"))
    if c["notbilled"]:
        parts.append("%s on parchis not billed or collected" % rs(c["notbilled_p"]))
    if c["parchi"]:
        parts.append("%d parchi to fix" % c["parchi"] if c["parchi"] == 1 else "%d parchis to fix" % c["parchi"])
    if c["hand"]:
        parts.append("%d to check by hand" % c["hand"])
    return "%s: %s" % (d, " · ".join(parts) if parts else "all correct")
''', '''    c = chk["counts"]
    parts = []
    if chk.get("reexport"):                              # S640: staff have ticked every Docterz line -- his re-export is next
        parts.append("Re-export %s from Docterz" % d)
        if chk.get("notright"):
            parts.append("%d marked not right by staff" % chk["notright"])
    else:
        if c["missing_p"]:
            parts.append("%s Docterz entry missing" % rs(c["missing_p"]))
        if c["modes"]:
            parts.append("%d payment mode%s wrong" % (c["modes"], "" if c["modes"] == 1 else "s"))
        if c["notbilled"]:
            parts.append("%s on parchis not billed or collected" % rs(c["notbilled_p"]))
    if c["parchi"]:
        parts.append("%d parchi to fix" % c["parchi"] if c["parchi"] == 1 else "%d parchis to fix" % c["parchi"])
    if c["hand"]:
        parts.append("%d to check by hand" % c["hand"])
    if chk.get("not_fixed"):
        parts.append("%d not fixed after the re-export" % chk["not_fixed"])
    return "%s: %s" % (d, " · ".join(parts) if parts else "all correct")
'''),
 # 3 -- a line the re-export did not fix says so on its card, and its buttons are back
 ('''    elif c["who"] == "docterz" and can_docterz(u):
        if c["kind"] in ("missing", "notbilled"):''', '''    elif c["who"] == "docterz" and can_docterz(u):
        if c.get("not_fixed"):                           # S640: ticked, re-exported, still there
            nf = c["not_fixed"]
            status = "<span class='tk' style='color:#9c2a20'>%s</span>" % _esc(
                ("Not fixed — the Docterz export after %s's tick (%s) still shows it" if english else
                 "Theek nahi hua — %s ke tick (%s) ke baad ke Docterz export mein bhi hai") % ((nf["who"] or "").title(), (nf["at"] or "")[5:16]))
        if c["kind"] in ("missing", "notbilled"):'''),
 # 4 -- the door the staff's Aaj ka kaam asks, the page it opens, and when the day's Docterz file last came in
 ('''def _late_ok(d):''', '''def _export_at(con, d):
    try:
        r = con.execute("SELECT taken_at FROM clinic_day_revenue WHERE business_date=?", (d,)).fetchone()
        return (r[0] or "") if r else ""
    except Exception:                                    # noqa: BLE001
        return ""


STAFF_DAYS = 7                                           # the staff see a week of days: the parchi's own late window


def staff_lines(con, u):
    """S640 (D776 stage 3): what one login has to correct, the day before today back STAFF_DAYS days (never before the lists'
    floor): the Docterz lines for Shivani, Alisha, Shavez; the parchi lines for Shavez and Bhati. A line ticked and waiting for
    the re-export is not theirs to do; a line the re-export did not fix is, again. {open, text, days} -- text names them."""
    who = _user(u)
    want = set()
    if who in DOCTERZ_USERS:
        want.add("docterz")
    if who in PARCHI_USERS:
        want.add("parchi")
    if not want:
        return dict(open=0, text="", days=[])
    floor = "2026-10-01"
    try:
        import aaj_floor                                 # noqa: PLC0415 -- the lists' own floor, when it says one
        floor = aaj_floor.floor_for(con, _require, u) or floor
    except Exception:                                    # noqa: BLE001
        pass
    today = dt.date.today()
    n, bits, days = 0, [], []
    for i in range(1, STAFF_DAYS + 1):
        d = (today - dt.timedelta(days=i)).isoformat()
        if d < str(floor):
            break
        chk = check_day(con, d)
        if chk.get("state") != "checked":
            continue
        mine = [c for c in chk["cards"] if c["who"] in want and not c.get("tick")]
        if not mine:
            continue
        days.append(d)
        n += len(mine)
        bits.append("%s: %s" % (dm(d), " | ".join(("Phir se — " if c.get("not_fixed") else "") + c["hi"] for c in mine)))
    text = ""
    if n:
        text = "Din ki galtiyan (%d) — %s" % (n, " ;  ".join(bits))
        if len(text) > 600:
            text = text[:590].rsplit(" ", 1)[0] + " …"
    return dict(open=n, text=text, days=days)


@bp.route("/finance/clinic/check/api/mine")
def api_mine():
    u, english, err = _gate()
    if err:
        return err
    con = _db()
    _CR()._ensure(con)
    ensure(con)
    from flask import jsonify                            # noqa: PLC0415
    return jsonify(ok=True, **staff_lines(con, u))


@bp.route("/finance/clinic/check/mine")
def mine():
    """The page a staff line opens: the oldest day that still has lines for this login (else yesterday)."""
    u, english, err = _gate()
    if err:
        return redirect("/finance/clinic/register", code=302)
    con = _db()
    _CR()._ensure(con)
    ensure(con)
    s = staff_lines(con, u)
    d = s["days"][-1] if s["days"] else (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return redirect("/finance/clinic/check/%s#check" % d, code=302)


def _late_ok(d):'''),
]

SEED = [
 ('''            {'id': 'shavez.mahine_ka_kaam',
             'hi': 'Mahine ka kaam: checklist poori kijiye',
             'en': 'The month-end checklist for the accountant pack.',
             'when': 'month',
             'on': True,
             'opens': 'Mahine ka kaam'}]},''', '''            {'id': 'shavez.mahine_ka_kaam',
             'hi': 'Mahine ka kaam: checklist poori kijiye',
             'en': 'The month-end checklist for the accountant pack.',
             'when': 'month',
             'on': True,
             'opens': 'Mahine ka kaam'},
            {'id': 'shavez.day_check',
             'hi': 'Din ki galtiyan: Docterz aur parchi theek kijiye',
             'en': "S640 (D776): the day's corrections -- Docterz lines and parchi lines, each named; shown only when there are some.",
             'when': 'first',
             'on': True,
             'opens': 'Day check'}]},'''),
 ('''            {'id': 'reception.month_new_register',
             'hi': 'Naya register 1 tareekh ko shuru kijiye',
             'en': 'New physical register started on the 1st.',
             'when': 'month',
             'on': True,
             'opens': ''}]},''', '''            {'id': 'reception.month_new_register',
             'hi': 'Naya register 1 tareekh ko shuru kijiye',
             'en': 'New physical register started on the 1st.',
             'when': 'month',
             'on': True,
             'opens': ''},
            {'id': 'reception.day_check',
             'hi': 'Din ki galtiyan: Docterz mein theek kijiye',
             'en': "S640 (D776): the day's corrections in Docterz (add, payment mode, patient not found), each named; shown only when there are some.",
             'when': 'first',
             'on': True,
             'opens': 'Day check'}]},'''),
]

HTML = [
 ('''      if((!r.fetch.only_if||d[r.fetch.only_if])&&Number(d[r.fetch.field]||0)>0){
        w.hidden=false; EXTRA+=1;''', '''      if((!r.fetch.only_if||d[r.fetch.only_if])&&Number(d[r.fetch.field]||0)>0){
        w.hidden=false; EXTRA+=1;
        /* S640: a door may name the work itself (the day's corrections, patient by patient) */
        if(r.fetch.text_field&&d[r.fetch.text_field]){ var tx=w.querySelector('.tx'); if(tx)tx.textContent=String(d[r.fetch.text_field]); }'''),
]

DUT = [
 ('''   "id": "reception.month_new_register",
   "person": "alisha",
   "kind": "tick",
   "period": "month",
   "group": "month",
   "hi": "Naya register 1 tareekh ko shuru kiya",
   "en": "Reception: new physical register started on the 1st (monthly)",
   "tile": null,
   "door": null
  }
 ]
}''', '''   "id": "reception.month_new_register",
   "person": "alisha",
   "kind": "tick",
   "period": "month",
   "group": "month",
   "hi": "Naya register 1 tareekh ko shuru kiya",
   "en": "Reception: new physical register started on the 1st (monthly)",
   "tile": null,
   "door": null
  },
  {
   "id": "reception.day_check",
   "person": "alisha",
   "kind": "fetch",
   "group": "open",
   "hi": "Din ki galtiyan: Docterz mein theek kijiye",
   "en": "Reception: the day's Docterz corrections, named (S640, D776; read on the page from the day check's own door)",
   "tile": "Day check",
   "door": "/finance/clinic/check/mine",
   "fetch": {"url": "/finance/clinic/check/api/mine", "field": "open", "text_field": "text"}
  },
  {
   "id": "shavez.day_check",
   "person": "shavez",
   "kind": "fetch",
   "group": "open",
   "hi": "Din ki galtiyan: Docterz aur parchi theek kijiye",
   "en": "Shavez: the day's Docterz and parchi corrections, named (S640, D776; read on the page from the day check's own door)",
   "tile": "Day check",
   "door": "/finance/clinic/check/mine",
   "fetch": {"url": "/finance/clinic/check/api/mine", "field": "open", "text_field": "text"}
  }
 ]
}'''),
]

PLAN = (("day_check.py", DC), ("aaj_seed.py", SEED), ("aaj_kaam.html", HTML), ("aaj_duties.json", DUT))


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    built = {}
    for name, edits in PLAN:
        p = os.path.join(src, name)
        h = hashlib.md5(open(p, "rb").read()).hexdigest()
        if h != FROM[name]:
            sys.exit("STOP: %s is %s, not %s" % (p, h[:8], FROM[name][:8]))
        s = open(p, encoding="utf-8", newline="").read()
        for i, (a, b) in enumerate(edits, 1):
            n = s.count(a)
            if n != 1:
                sys.exit("STOP: %s edit %d anchor found %d times" % (name, i, n))
            s = s.replace(a, b)
        built[name] = s
    for name, s in built.items():
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(s)
        print("%s: %d counted edit(s) -> %s" % (name, len(dict(PLAN)[name]), hashlib.md5(s.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    main()
