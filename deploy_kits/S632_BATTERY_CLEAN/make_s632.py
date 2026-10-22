#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s632.py -- S632_BATTERY_CLEAN (D766): rebuilds batteries.py's TO bytes from the pinned FROM bytes by exact, counted edits.

    python3 -B make_s632.py <FROM folder> <TO folder>

Each edit's anchor must occur exactly ONCE in the FROM file; the FROM md5 must equal the pin; the TO md5 is printed (the kit's
PIN_TO_batteries.txt holds the expected one and the installer compares). Nothing else is touched.

What the edits do (the owner's word, 19:51-19:52 IST 22-Oct-2026: "a clean battery page which has all the relevant scans and fields
filled in properly"):
  E1  the docstring names S632;
  E2  a fifth group, "Machine batteries" (a battery inside a machine, e.g. the X-ray detector's) -- its note and kind;
  E3  'B.L.Computers' (written without a space) is B.L. Computers -- its papers are offered and linked like the others;
  E4  one paper may be the bill of more than one battery (a supplier's statement holding several invoices, B-0104);
  E5  the place page: the fittings' own ids and values for the correction card; the scans kept on the linked machine record;
  E6  the place page's header prints "yours only" once; the cost of a fitting with no price says "(the whole bill)";
  E7  "Correct a battery entry" (owner only): change a saved fitting, or remove one entered by mistake (kept, never deleted);
  E8  the history's bill cell for the battery in use points to the scan on the machine record when no paper is linked;
  E9  "Change this place" takes the group and the upkeep (none / UPS backup check / inverter water / generator start, every N months);
  E10 post_place saves them (a form without those fields keeps what the place had);
  E11 the new door POST /batteries/fitfix (owner only, server-side), mounted beside the others.
"""
import hashlib
import os
import sys

FROM_PIN = {"batteries.py": "b2cbb41eedde0e0efed6d3adbd5a31dc"}

EDITS = {"batteries.py": [
    # ---------------------------------------------------------------------------------------------- E1 the docstring
    ('''    the places with no battery recorded, one line each (date required).
"""''',
     '''    the places with no battery recorded, one line each (date required).

S632_BATTERY_CLEAN (D766; the owner, 19:51-19:52 IST 22-Oct-2026: "a clean battery page which has all the relevant scans and fields
filled in properly")
    "Correct a battery entry" on a place's page (the owner only, POST /batteries/fitfix): a saved fitting's dates, supplier, make,
    Ah, set, warranty months, price and old-battery amount can be changed; an entry made by mistake is removed by voided_at (kept,
    never deleted) and the battery before it is in use again. One paper may be the bill of more than one battery (a supplier's
    statement). 'B.L.Computers' is B.L. Computers. A fifth group, "Machine batteries". "Change this place" takes the group and the
    upkeep. The place page lists the scans kept on its linked machine record (the owner only) and prints "yours only" once.
"""'''),
    # ---------------------------------------------------------------------------------------------- E2 the fifth group
    ('''GROUPS = (("online_ups", "Online UPS"), ("small_ups", "Small UPS"), ("gen_inv", "Generator and inverters"), ("vehicles", "Vehicles"))''',
     '''GROUPS = (("online_ups", "Online UPS"), ("small_ups", "Small UPS"), ("gen_inv", "Generator and inverters"), ("vehicles", "Vehicles"),
          ("machine", "Machine batteries"))                                              # S632: a battery inside a machine'''),
    ('''              "vehicles": "Jasoria · bill and warranty card · yours only"}''',
     '''              "vehicles": "Jasoria · bill and warranty card · yours only",
              "machine": "the machine's own supplier · warranty from its bill or card"}      # S632'''),
    ('''GROUP_KIND = {"online_ups": "UPS place", "small_ups": "UPS place", "gen_inv": "Generator / inverter place", "vehicles": "Vehicle place"}''',
     '''GROUP_KIND = {"online_ups": "UPS place", "small_ups": "UPS place", "gen_inv": "Generator / inverter place", "vehicles": "Vehicle place",
              "machine": "Machine battery place"}                                                # S632'''),
    # ---------------------------------------------------------------------------------------------- E3 B.L.Computers
    ('''    k = _supplier_key(v).split()
    return k[0] if k else ""''',
     '''    k = _supplier_key(v).split()
    if k and k[0].startswith("blcomputer"):                           # S632: 'B.L.Computers' (no space) is B.L. Computers
        return "bl"
    return k[0] if k else ""'''),
    # ---------------------------------------------------------------------------------------------- E4 one paper, several batteries
    ('''    if as_ == "bill":
        held = db.execute("SELECT id FROM battery_fit WHERE voided_at='' AND id<>? AND bill_id=? AND bill_created_at=?",
                          (fr["id"], b["id"], b["created_at"] or "")).fetchone()
        if held:
            raise ValueError("%s is already the bill of another battery." % _stamp(b))
    old = (fr[as_ + "_id"], fr[as_ + "_created_at"])''',
     '''    # S632 (D766): one paper may be the bill of more than one battery -- a supplier's statement holds several invoices (B-0104)
    old = (fr[as_ + "_id"], fr[as_ + "_created_at"])'''),
    # ---------------------------------------------------------------------------------------------- E5 the place page's data
    ('''                     "nobill": b is None and no_bill(h), "nocard": c is None and no_paper(h, "card")})''',
     '''                     "nobill": b is None and no_bill(h), "nocard": c is None and no_paper(h, "card"),
                     "id": h["id"], "raw": h, "current": r is None, "nopaper": b is None})                     # S632 (D766)'''),
    ('''    return AR.page(PLACE_TPL, p=p, v=v, hist=hist, grp=GROUP_WORD.get(p["grp"], p["grp"]), reorder=_reorder(db, p), dmy=dmy,''',
     '''    mfiles = []                                                       # S632 (D766): the scans kept on the linked machine record -- the owner only
    if owner and mach is not None:
        try:
            mfiles = [(x["id"], x["orig_name"]) for x in db.execute("SELECT id, orig_name FROM attachments WHERE entity='asset' AND entity_id=? "
                                                                       "ORDER BY id", (mach["id"],))]
        except sqlite3.Error:
            mfiles = []
    return AR.page(PLACE_TPL, p=p, v=v, hist=hist, grp=GROUP_WORD.get(p["grp"], p["grp"]), reorder=_reorder(db, p), dmy=dmy,
                   mfiles=mfiles, grps=GROUPS, upks=[(k, UPKEEP[k][0]) for k in UPKEEP], numv=_numv, fix_open=request.args.get("fix") == "1",'''),
    # ---------------------------------------------------------------------------------------------- E6 header and cost words
    ('''<p class=muted style="margin-top:0">{{grp}} · {{p.sub}}{% if p.owner_only %} · yours only{% endif %}{% if mach %}''',
     '''<p class=muted style="margin-top:0">{{grp}} · {{p.sub}}{% if p.owner_only and 'yours only' not in (p.sub or '') %} · yours only{% endif %}{% if mach %}'''),
    ('''            cost = rs(b["total_amount"]) + " (the bill)"''',
     '''            cost = rs(b["total_amount"]) + " (the whole bill)"                # S632: the paper's total, not this battery's price'''),
    # ---------------------------------------------------------------------------------------------- E7 + E8 the correction card, the machine's scans
    ('''{% elif h.nobill %}<span class=muted>no bill (old battery)</span>''',
     '''{% elif h.current and h.nopaper and mfiles %}<a href="{{url_for('asset_view', aid=mach['id'])}}">scan on the machine record</a>{% elif h.nobill %}<span class=muted>no bill (old battery)</span>'''),
    ('''{% else %}<tr><td colspan=7 class=muted>No battery recorded here yet — “New battery fitted” records the one in place now.</td></tr>{% endfor %}</table></div>''',
     '''{% else %}<tr><td colspan=7 class=muted>No battery recorded here yet — “New battery fitted” records the one in place now.</td></tr>{% endfor %}</table></div>
{% if mfiles %}<div class=card id=s632scans><b>Scans on the machine record</b> <a href="{{url_for('asset_view', aid=mach['id'])}}">{{mach['name']}}</a>:{% for fid, nm in mfiles %} <a href="{{url_for('file_get', fid=fid)}}">scan {{loop.index}}</a>{% endfor %} <span class=muted>(the bill or card photographed when the machine was added)</span></div>{% endif %}
{% if is_owner and hist %}<details class=card id=s632fix{{' open' if fix_open}}><summary style="cursor:pointer;font-weight:600">Correct a battery entry</summary>
<p class=muted style="margin:6px 0;font-size:14px">Change what was saved for a battery, or remove an entry made by mistake — it is kept in the records, never deleted. Linked papers stay as they are.</p>
{% for h in hist %}<form method=post action="{{url_for('s632_fitfix')}}" class=s632f data-fit="{{h.id}}" style="display:flex;flex-wrap:wrap;gap:6px 10px;align-items:flex-end;padding:8px 0 4px;border-top:1px solid #ECECE6"><input type=hidden name=fit value="{{h.id}}"><input type=hidden name=do value=fix>
<b style="flex-basis:100%;font-size:14px">Fitted {{dmy(h.fitted_on)}}{{' — in use' if h.current else ''}}</b>
<label style="margin:0">Fitted on<input name=fitted_on value="{{dmy(h.fitted_on)}}" style="width:110px"></label>
{% if not h.current %}<label style="margin:0">Taken out<input name=removed_on value="{{dmy(h.removed_on)}}" style="width:110px"></label>{% endif %}
<label style="margin:0">Supplier<input name=supplier value="{{h.raw.supplier}}" style="width:160px"></label>
<label style="margin:0">Battery (make · type)<input name=brand value="{{h.raw.brand}}" style="width:190px"></label>
<label style="margin:0">Ah<input name=ah value="{{h.raw.ah}}" style="width:60px"></label>
<label style="margin:0">Set of<input name=set_n inputmode=numeric value="{{h.raw.set_n if h.raw.set_n is not none else ''}}" style="width:50px"></label>
<label style="margin:0">Warranty (months)<input name=warranty_months inputmode=numeric value="{{h.raw.warranty_months if h.raw.warranty_months is not none else ''}}" style="width:60px"></label>
<label style="margin:0">Price ₹<input name=price inputmode=decimal value="{{numv(h.raw.price)}}" style="width:90px"></label>
<label style="margin:0">Old battery ₹<input name=old_amount inputmode=decimal value="{{numv(h.raw.old_amount)}}" style="width:90px"></label>
<button class="btn small">Save</button></form>
<form method=post action="{{url_for('s632_fitfix')}}" class=s632v style="margin:0 0 8px" data-d="{{dmy(h.fitted_on)}}" onsubmit="return confirm('Remove the entry fitted '+this.dataset.d+'? It is kept in the records as entered by mistake.')"><input type=hidden name=fit value="{{h.id}}"><input type=hidden name=do value=void><button class="btn small" style="background:#fff;color:#8F2D0E;border:1px solid #8F2D0E">Entered by mistake — remove</button></form>
{% endfor %}</details>{% endif %}'''),
    # ---------------------------------------------------------------------------------------------- E9 the place form: group and upkeep
    ('''<label style="margin:0">V<input name=volts value="{{p.volts}}" style="max-width:60px"></label><label style="margin:0">Set of<input name=set_n value="{{p.set_n if p.set_n is not none else ''}}" style="max-width:60px"></label>''',
     '''<label style="margin:0">V<input name=volts value="{{p.volts}}" style="max-width:60px"></label><label style="margin:0">Set of<input name=set_n value="{{p.set_n if p.set_n is not none else ''}}" style="max-width:60px"></label>
<label style="margin:0">Group<select name=grp>{% for k, w in grps %}<option value="{{k}}"{{' selected' if k == p.grp}}>{{w}}</option>{% endfor %}</select></label>
<label style="margin:0">Upkeep<select name=upkeep><option value=""{{' selected' if not p.upkeep}}>none</option>{% for k, w in upks %}<option value="{{k}}"{{' selected' if k == p.upkeep}}>{{w}}</option>{% endfor %}</select></label>
<label style="margin:0">every (months)<input name=upkeep_months inputmode=numeric value="{{p.upkeep_months if p.upkeep_months is not none else ''}}" style="max-width:50px"></label>'''),
    # ---------------------------------------------------------------------------------------------- E10 saving them
    ('''                   "owner_only": 1 if f.get("owner_only") else 0}
            ch = {k: v for k, v in new.items() if v != p[k]}''',
     '''                   "owner_only": 1 if f.get("owner_only") else 0}
            if "grp" in f:                                            # S632 (D766): the group and the upkeep; a form without them keeps the place's
                new["grp"] = f.get("grp") if f.get("grp") in GROUP_WORD else p["grp"]
            if "upkeep" in f:
                u = (f.get("upkeep") or "").strip()
                new["upkeep"] = u if (u == "" or u in UPKEEP) else (p["upkeep"] or "")
                um = _int(f.get("upkeep_months"), 1, 24) if "upkeep_months" in f else p["upkeep_months"]
                new["upkeep_months"] = None if not new["upkeep"] else (um or {"water": 3, "backup": 3, "start": 1}[new["upkeep"]])
            ch = {k: v for k, v in new.items() if v != p[k]}'''),
    # ---------------------------------------------------------------------------------------------- E7 the door's logic, before renewals_card
    ('''def renewals_card(show_all=False):''',
     '''# ---------------------------------------------------------------------------------------------- S632: correct or remove a saved battery
FIX_WORDS = {"fitted_on": "fitted on", "removed_on": "taken out", "supplier": "supplier", "brand": "make · type", "ah": "Ah",
             "set_n": "set of", "warranty_months": "warranty months", "price": "price", "old_amount": "old-battery amount"}


def _numv(x):
    """A stored amount as the form shows it: 6750.0 -> '6750', 12.5 -> '12.5', None -> ''."""
    if x is None:
        return ""
    try:
        return ("%.2f" % float(x)).rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return ""


def _amount(v, word):
    s = str(v or "").strip()
    if not s:
        return None
    x = _num(s)
    if x is None:
        raise ValueError("'%s' is not an amount (the %s)." % (s[:12], word))
    if x < 0:
        raise ValueError("The %s cannot be below zero." % word)
    return x


def fix_fit(db, fid, f, owner):
    """S632 (D766): the owner corrects a battery entry already saved, or removes one entered by mistake -- voided_at, kept, never
    deleted; when the battery in use is removed, the one before it (taken out the day it went in) is in use again. A change of the
    fitted date keeps the entries' order and moves the previous battery's taken-out date with it. Linked papers are never written
    (D664). No commit. PermissionError / ValueError in plain words. Returns (place, message)."""
    if not owner:
        raise PermissionError("Yeh sirf Dr Manoj ke liye hai.")
    try:
        fr = db.execute("SELECT * FROM battery_fit WHERE id=? AND voided_at=''", (int(fid),)).fetchone()
    except (TypeError, ValueError):
        fr = None
    if fr is None:
        raise ValueError("There is no such battery entry.")
    fr = dict(fr)
    p = place(db, fr["place_id"])
    if p is None:
        raise ValueError("There is no such battery place.")
    others = [x for x in fits(db, p["id"]) if x["id"] != fr["id"]]
    if (f.get("do") or "") == "void":
        db.execute("UPDATE battery_fit SET voided_at=?, voided_by=? WHERE id=?", (_now(), _who(), fr["id"]))
        back = None
        allf = sorted(others + [fr], key=lambda x: (x["fitted_on"], x["id"]), reverse=True)     # K1 B1: the page's own order (fits()), never by date alone
        i = next((k for k, x in enumerate(allf) if x["id"] == fr["id"]), None)
        older = allf[i + 1:] if i is not None else []
        if older:                                                     # K1 B1: the one before it takes over its time -- in use again, or to its end
            back = older[0]
            db.execute("UPDATE battery_fit SET removed_on=? WHERE id=?", (fr["removed_on"], back["id"]))
        _audit(db, "battery_fit_voided", {"place": p["id"], "fit": fr["id"], "fitted_on": fr["fitted_on"], "in_use_again": back["id"] if back else None})
        return p, "Removed: the entry fitted %s at %s — kept in the records as entered by mistake.%s" % (
            dmy(fr["fitted_on"]), p["name"], " The battery before it shows as in use again." if (back and fr["removed_on"] is None) else "")
    today = _today()
    d = typed_date(f.get("fitted_on"))
    if d is None:
        raise ValueError("Type the date this battery was fitted (dd-mm-yyyy).")
    if d > today:
        raise ValueError("The fitted date %s is after today." % dmy(d))
    if d < add_months(today, -FLOOR_MONTHS):
        raise ValueError("The fitted date %s is more than 15 years back." % dmy(d))
    old = _iso(fr["fitted_on"])
    for x in others:
        xf = _iso(x["fitted_on"])
        if xf is None or old is None:
            continue
        if xf < old and d < xf:
            raise ValueError("A battery fitted on %s is recorded before this one — this one cannot be older." % dmy(xf))
        if xf > old and d > xf:
            raise ValueError("A battery fitted on %s is recorded after this one — this one cannot be newer." % dmy(xf))
    allf = fits(db, p["id"])                                          # K1 B1: the entries just before and just after, by the page's own order
    i = next((k for k, x in enumerate(allf) if x["id"] == fr["id"]), 0)
    prv = allf[i + 1] if i + 1 < len(allf) else None
    nxt = allf[i - 1] if i > 0 else None
    if prv is not None and prv["removed_on"] and prv["removed_on"] != fr["fitted_on"] and d < _iso(prv["removed_on"]):
        raise ValueError("The battery before it was taken out on %s — this one cannot be fitted earlier." % dmy(prv["removed_on"]))
    new = {"fitted_on": d.isoformat()}
    if fr["removed_on"] is not None:
        rm = typed_date(f.get("removed_on"))
        if rm is None:
            raise ValueError("Type the date this battery was taken out (dd-mm-yyyy).")
        if rm < d:
            raise ValueError("The date taken out, %s, is before the date fitted, %s." % (dmy(rm), dmy(d)))
        if rm > today:
            raise ValueError("The date taken out, %s, is after today." % dmy(rm))
        if nxt is not None and rm > _iso(nxt["fitted_on"]):
            raise ValueError("The next battery was fitted on %s — this one cannot be taken out later." % dmy(nxt["fitted_on"]))
        new["removed_on"] = rm.isoformat()
    clean = lambda k, n: re.sub(r"\\s+", " ", str(f.get(k) or "")).strip()[:n]
    more = {"supplier": lambda: clean("supplier", 80) or fr["supplier"], "brand": lambda: clean("brand", 80), "ah": lambda: clean("ah", 20),
            "set_n": lambda: _int(f.get("set_n"), 1, 50), "warranty_months": lambda: _int(f.get("warranty_months"), 0, 120),
            "price": lambda: _amount(f.get("price"), "price"), "old_amount": lambda: _amount(f.get("old_amount"), "old-battery amount")}
    new.update({k: fn() for k, fn in more.items() if k in f})        # K1 C2: a field the form did not send keeps its value
    ch = {k: v for k, v in new.items() if v != fr[k]}
    if not ch:
        return p, "Unchanged: the battery fitted %s at %s." % (dmy(d), p["name"])
    db.execute("UPDATE battery_fit SET %s WHERE id=?" % ",".join("%s=?" % k for k in ch), tuple(ch.values()) + (fr["id"],))
    if "fitted_on" in ch and prv is not None and prv["removed_on"] == fr["fitted_on"]:     # the one before was taken out the day this went in
        db.execute("UPDATE battery_fit SET removed_on=? WHERE id=?", (new["fitted_on"], prv["id"]))
    _audit(db, "battery_fit_corrected", {"place": p["id"], "fit": fr["id"], "from": {k: fr[k] for k in ch}, "to": ch})
    return p, "Saved: the battery fitted %s at %s — %s changed." % (dmy(d), p["name"], ", ".join(FIX_WORDS.get(k, k) for k in ch))


def post_fitfix():
    db = AR.get_db()
    f = request.form
    try:
        p, msg = fix_fit(db, f.get("fit"), f, _owner())
        db.commit()
        flash(msg)
        return redirect(url_for("s571_place", pid=p["id"], fix=1, _anchor="s632fix"))
    except PermissionError as e:
        db.rollback()
        return str(e), 403
    except ValueError as e:
        db.rollback()
        flash(str(e) + " Nothing was saved.")
        try:
            pid = db.execute("SELECT place_id FROM battery_fit WHERE id=?", (int(f.get("fit")),)).fetchone()[0]
        except (TypeError, ValueError, sqlite3.Error):
            return redirect(url_for("s571_page"))
        return redirect(url_for("s571_place", pid=pid, fix=1, _anchor="s632fix"))


def renewals_card(show_all=False):'''),
    # ---------------------------------------------------------------------------------------------- K1 C4: a new Machine-batteries place
    ('''            sup = re.sub(r"\\s+", " ", f.get("supplier") or "").strip()[:80] or (BL if ups else JAS)''',
     '''            sup = re.sub(r"\\s+", " ", f.get("supplier") or "").strip()[:80] or (BL if ups else ("" if grp == "machine" else JAS))     # S632'''),
    ('''            life = LIFE["ups"] if ups else (LIFE["car"] if grp == "vehicles" else LIFE["inverter"])
            upk, every = ("backup", 3) if ups else (("water", 3) if grp == "gen_inv" else ("", None))
            cur = db.execute("INSERT INTO battery_place(grp, name, sub, payer, supplier, warranty_months, life_months, owner_only, set_n, upkeep, "''',
     '''            life = LIFE["ups"] if ups else (LIFE["car"] if grp == "vehicles" else (None if grp == "machine" else LIFE["inverter"]))     # S632
            upk, every = ("backup", 3) if ups else (("water", 3) if grp == "gen_inv" else ("", None))
            cur = db.execute("INSERT INTO battery_place(grp, name, sub, payer, supplier, warranty_months, life_months, owner_only, set_n, upkeep, "'''),
    # ---------------------------------------------------------------------------------------------- K1 C5: a shared paper pre-selects only one payer
    ('''        pre = DESK_DEST.get(p["payer"], "")
        if pre and not cur_dest and (b["status"] or "") in ("draft", "captured"):''',
     '''        pre = DESK_DEST.get(p["payer"], "")
        pays = {(place(db, x["place_id"]) or {}).get("payer") for x in fit_of_paper(db, b)}      # S632 (K1 C5): one paper, places of two payers -- no pre-select
        if len(pays) > 1:
            pre = ""
        if pre and not cur_dest and (b["status"] or "") in ("draft", "captured"):'''),
    # ---------------------------------------------------------------------------------------------- K1 C3: the place's name kept out of the script
    ('''<form method=post action="{{url_for('s571_place_post')}}" style="margin-top:10px" onsubmit="return confirm('Take {{p.name}} off the list? Its history is kept.')">''',
     '''<form method=post action="{{url_for('s571_place_post')}}" style="margin-top:10px" data-n="{{p.name}}" onsubmit="return confirm('Take '+this.dataset.n+' off the list? Its history is kept.')">'''),
    # ---------------------------------------------------------------------------------------------- E11 the mount
    ('''    app.add_url_rule("/batteries/place", "s571_place_post", cr(_gate(post_place)), methods=["POST"])''',
     '''    app.add_url_rule("/batteries/place", "s571_place_post", cr(_gate(post_place)), methods=["POST"])
    app.add_url_rule("/batteries/fitfix", "s632_fitfix", cr(_gate(post_fitfix)), methods=["POST"])          # S632 (D766), the owner only'''),
]}


def md5b(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    total = 0
    for f, edits in EDITS.items():
        raw = open(os.path.join(src, f), "rb").read()
        if md5b(raw) != FROM_PIN[f]:
            out("%s: FROM is %s, not the pin %s -- STOP" % (f, md5b(raw)[:8], FROM_PIN[f][:8]))
            return 1
        t = raw.decode("utf-8")
        for i, (a, b) in enumerate(edits, 1):
            n = t.count(a)
            if n != 1:
                out("%s: edit %d anchor found %d times (must be 1) -- STOP" % (f, i, n))
                return 1
            t = t.replace(a, b)
        data = t.encode("utf-8")
        open(os.path.join(dst, f), "wb").write(data)
        total += len(edits)
        out("%s: %d counted edit(s), %s -> %s" % (f, len(edits), FROM_PIN[f][:8], md5b(data)))
    out("make_s632: %d counted edits in all" % total)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
