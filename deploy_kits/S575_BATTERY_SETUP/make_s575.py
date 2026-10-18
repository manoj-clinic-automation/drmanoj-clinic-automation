#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s575.py -- S575_BATTERY_SETUP: batteries.py rebuilt from the pinned live bytes (S571's TO, 9a0054ac) with exact counted edits.
sorting_desk.py and asset_register.py are read, never edited (everything is done inside batteries.py); clinic_papers.py, stationery.py,
asset_machine.py, scanner_widget.js, packs.py and every finance / Sanjeevni file are never touched.

    python3 make_s575.py <dir with the live batteries.py> <out dir>

Refuses when the input is not at its FROM pin or an anchor is not found exactly the counted number of times. Every byte of the built
file comes from the live file plus these edits (BUILD_NORM_v1). The brief: claude_code_briefs/S575_BATTERY_SETUP.md (v2) with its
review S575_BRIEF_R1.md (md5 99057249...) -- C1..C8 are named on the edits that carry them."""
import hashlib, os, sys

FROM = {"batteries.py": "9a0054ac073ccaa1252b426c5a9d408f"}

BT_EDITS = [
    # BT1 -- the docstring: what S575 adds
    ('''    owner-only place -- its fittings, links, history and reminders -- is refused to anyone but the owner, server-side.
"""
''',
     '''    owner-only place -- its fittings, links, history and reminders -- is refused to anyone but the owner, server-side.

S575_BATTERY_SETUP (the owner, 06:02 IST 18-Oct-2026: "for the initial setup, that functionality is also required")
    An old battery with only a date: "Fitted on" takes any past date up to 15 years back; the Bill choice "Old battery — no bill"
    (and, on the Jasoria form, "Old battery — no card") is stored as the id NULL and the created_at 'none:old-battery' -- no new
    column, no data step; such a battery is never "bill awaited" (badge, reminder, total, history, the desk's offer). Older / other
    papers: "Show older / other papers" (every paper the person may see, newest first) and "Find by stamp" on the fitted form and in
    "The battery now — its papers"; candidates() and _pickable() are unchanged. An online UPS with no count shows the owner "How many
    batteries? — set"; "set of N" shows before a battery is recorded. "First setup": an owner-only fold on the Batteries page listing
    the places with no battery recorded, one line each (date required).
"""
''', 1),
    # BT2 -- the mark and the constants
    ('''VERSION = "S571"
''',
     '''VERSION = "S571"
SETUP = "S575"                # S575_BATTERY_SETUP: old battery with only a date, older / other papers, find by stamp, the set count, First setup
NO_PAPER = "none:old-battery" # S575 (R1 C1): bill_created_at / card_created_at of "Old battery — no bill / no card" (its id NULL)
WIDE_LIMIT = 300              # S575 (R1 C4): "Show older / other papers" -- newest first, at most this many
FLOOR_MONTHS = 180            # S575 (R1 N4): a fitted date at most 15 years back
''', 1),
    # BT3 (C1, C4, C5) -- the helpers: no paper, the wider list, the wide check, the stamp; after fit_of_paper()
    ('''                                        "(card_id=? AND card_created_at=?))", (b["id"], b["created_at"] or "", b["id"], b["created_at"] or ""))]
''',
     '''                                        "(card_id=? AND card_created_at=?))", (b["id"], b["created_at"] or "", b["id"], b["created_at"] or ""))]


# ---------------------------------------------------------------------------------------------- S575: no paper, older papers, find by stamp
def no_paper(fr, k="bill"):
    """S575 (R1 C1): the fitting was saved with "Old battery — no bill" (k='bill') or "— no card" (k='card'): its id NULL and its
    created_at the marker. A later link writes both columns, so the marker goes by itself."""
    try:
        return bool(fr) and not fr[k + "_id"] and (fr[k + "_created_at"] or "") == NO_PAPER
    except (KeyError, IndexError, TypeError):
        return False


def no_bill(fr):
    return no_paper(fr, "bill")


def _col(b, k):
    try:
        return b[k]
    except (KeyError, IndexError):
        return None


def _wide_ok(b, owner):
    """S575 (R1 C4 / N5): a paper that may be linked from the wider list -- not a second scan, not set aside, not a page of another
    paper, and one this person may see by the desk's rules (never pharmacy or a patient's paper; Personal to the owner only). Any
    supplier, any date. Linking never changes it (D664)."""
    return (b is not None and not _col(b, "dup_of") and (_col(b, "status") or "") != "rejected" and not _col(b, "page_of")
            and paper_visible(b, owner))


def _paper_text(b):
    return "%s · %s · %s · %s" % (_stamp(b), re.sub(r"\\s+", " ", b["vendor"] or "").strip()[:40] or "no supplier",
                                  dmy(b["bill_date"] or b["created_at"]), rs(b["total_amount"]) if b["total_amount"] is not None else "no amount")


def wide_candidates(db, owner):
    """S575 (R1 C4): "Show older / other papers" -- every paper this person may see, any supplier, any date, newest first, at most
    WIDE_LIMIT: (id, 'stamp · supplier · date · amount'). candidates() and _pickable() stay as they are (S571's walk I7)."""
    try:
        rows = db.execute("SELECT * FROM bills WHERE dup_of IS NULL AND status<>'rejected' AND page_of IS NULL ORDER BY created_at DESC, id DESC")
    except sqlite3.OperationalError:
        rows = db.execute("SELECT * FROM bills WHERE dup_of IS NULL AND status<>'rejected' ORDER BY created_at DESC, id DESC")
    out = []
    for b in rows:
        if not _wide_ok(b, owner):
            continue
        out.append({"id": b["id"], "text": _paper_text(b)})
        if len(out) >= WIDE_LIMIT:
            break
    return out


def _pickable_wide(db, bid, owner):
    """S575 (R1 C4): the wider list's check -- the same rules, no supplier and no date test."""
    try:
        bid = int(bid)
    except (TypeError, ValueError):
        return None
    b = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
    return b if _wide_ok(b, owner) else None


def stamp_form(v):
    """S575 (R1 C5): the typed stamp in the desk's own form -- sorting_desk._s566_stamp_form (B-0162, b-0162, B-162, B162, b162 ->
    'B-0162'), spaces removed; a number alone is read as B-nnnn, as the desk's own stamp search does."""
    s = re.sub(r"\\s+", "", str(v or ""))[:24]
    sd = sys.modules.get("sorting_desk")
    if sd is not None and hasattr(sd, "_s566_stamp_form"):
        s = sd._s566_stamp_form(s)
    else:
        m = re.fullmatch(r"[Bb]-?0*(\\d{1,6})", s)
        s = ("B-%04d" % int(m.group(1))) if m else s
    if s.isdigit():
        s = "B-%04d" % int(s)
    return s.upper()


def by_stamp(db, typed, owner):
    """S575 (R1 C5): the paper with this stamp when this person may link it (the wide rules); else ONE line for every case -- not
    found, set aside, a second scan, a page, pharmacy, a patient's paper, or (to a manager) Personal. It never says which, so it
    never tells a manager that a Personal paper exists."""
    no = stamp_form(typed)
    b = db.execute("SELECT * FROM bills WHERE upper(stamp_no)=? ORDER BY id LIMIT 1", (no,)).fetchone() if no else None
    if not _wide_ok(b, owner):
        raise ValueError("No paper %s that you may link here." % (no or "with that stamp"))
    return b


def _choice(db, p, f, k, owner, today):
    """S575 (R1 C1 / C4): the fitted form's choice for k ('bill' / 'card'), in this order: the stamp box (k_stamp), the wider list
    (k_any), then the usual select (k). Returns a paper, 'none' (Old battery — no bill / no card) or None (awaited / later). Two
    pickers filled with different papers: refused."""
    word = "bill" if k == "bill" else "warranty card"
    st, wd, v = (str(f.get(x) or "").strip() for x in (k + "_stamp", k + "_any", k))
    got = []
    if st:
        got.append(by_stamp(db, st, owner))
    if wd:
        b = _pickable_wide(db, wd, owner)
        if b is None:
            raise ValueError("That paper cannot be linked here.")
        got.append(b)
    if v and v not in ("awaited", "none"):
        b = _pickable(db, p, v, owner, today)
        if b is None and not got:
            raise ValueError("That paper cannot be linked here — pick one of %s's papers from the list." % (p["supplier"] or "the supplier"))
        got.append(b)
    if len({(x["id"] if x is not None else None) for x in got}) > 1:
        raise ValueError("Pick the %s in one place only." % word)
    if got:
        return got[0]
    return "none" if v == "none" else None
''', 1),
    # BT4 (C1) -- place_view: the count, "set of N" before a battery is recorded (C7), and the old battery's "no bill"
    ('''         "badge": ("Not recorded yet", "none"), "battery": "—"}
''',
     '''         "badge": ("Not recorded yet", "none"), "battery": "—"}
    v["set_n"] = (cur["set_n"] if cur else None) or p.get("set_n")                       # S575 (R1 C7): the count, the battery's or the place's
    v["ask_n"] = p.get("grp") == "online_ups" and not v["set_n"]                         # S575 (R1 C7): an online UPS with no count
    v["nobill"] = bool(cur) and no_bill(cur)                                             # S575 (R1 C1)
    if not cur and (v["set_n"] or 0) > 1:
        v["battery"] = "set of %d" % v["set_n"]                                          # S575 (R1 C7): "set of N" before a battery is recorded
''', 1),
    # BT5 (C1) -- place_view: an old battery with no bill is never "bill awaited" (no badge, no reminder, no total)
    ('''        if is_bl(p) and paper_of(db, cur["bill_id"], cur["bill_created_at"]) is None:
''',
     '''        if is_bl(p) and not no_bill(cur) and paper_of(db, cur["bill_id"], cur["bill_created_at"]) is None:      # S575 (R1 C1)
''', 1),
    # BT6 (N4, C6) -- save_fit: the date -- required in First setup, never in the future, at most 15 years back
    ('''    d = typed_date(f.get("fitted_on")) or today
    if d > today:
        raise ValueError("The fitted date %s is after today." % dmy(d))
''',
     '''    d = typed_date(f.get("fitted_on"))
    if d is None and f.get("back") == "first":                        # S575 (R1 C6): First setup -- the date is required, never read as today
        raise ValueError("Type the date this battery was fitted (dd-mm-yyyy).")
    d = d or today
    if d > today:
        raise ValueError("The fitted date %s is after today." % dmy(d))
    if d < add_months(today, -FLOOR_MONTHS):                          # S575 (R1 N4): at most 15 years back
        raise ValueError("The fitted date %s is more than 15 years back." % dmy(d))
''', 1),
    # BT7 (C1, C4) -- save_fit: 'none' before _pickable; the stamp, the wider list, then the select
    ('''    links = {}
    for k in ("bill", "card"):
        v = str(f.get(k) or "").strip()
        if v and v != "awaited":
            b = _pickable(db, p, v, owner, today)
            if b is None:
                raise ValueError("That paper cannot be linked here — pick one of %s's papers from the list." % (p["supplier"] or "the supplier"))
            links[k] = b
''',
     '''    links, none = {}, set()
    for k in ("bill", "card"):
        c = _choice(db, p, f, k, owner, today)                        # S575 (R1 C1 / C4): 'none' first; the stamp, the wider list, the select
        if c == "none":
            none.add(k)
        elif c is not None:
            links[k] = c
''', 1),
    # BT8 (C1) -- save_fit: stored as the id NULL and the marker
    ('''                      links["bill"]["id"] if "bill" in links else None, (links["bill"]["created_at"] or "") if "bill" in links else "",
                      links["card"]["id"] if "card" in links else None, (links["card"]["created_at"] or "") if "card" in links else "",
''',
     '''                      links["bill"]["id"] if "bill" in links else None, (links["bill"]["created_at"] or "") if "bill" in links else (NO_PAPER if "bill" in none else ""),
                      links["card"]["id"] if "card" in links else None, (links["card"]["created_at"] or "") if "card" in links else (NO_PAPER if "card" in none else ""),
''', 1),
    # BT9 (C1) -- the audit line carries no_bill / no_card
    ('''                                  "bill": links["bill"]["id"] if "bill" in links else None, "card": links["card"]["id"] if "card" in links else None})
''',
     '''                                  "bill": links["bill"]["id"] if "bill" in links else None, "card": links["card"]["id"] if "card" in links else None,
                                  "no_bill": "bill" in none, "no_card": "card" in none})                                  # S575 (R1 C1)
''', 1),
    # BT10 (C3, C4, C5) -- link_paper: the stamp and the wider list (the 90-day wording unchanged on the usual path)
    ('''def link_paper(db, fit_id, bid, as_, owner):
''',
     '''def link_paper(db, fit_id, bid, as_, owner, stamp="", wide=""):
''', 1),
    ('''    b = _pickable(db, p, bid, owner)
    if b is None:
        raise ValueError("That paper cannot be linked here — it is not %s's, not of the last %d days, or not yours to see." % (p["supplier"] or "the supplier", PICK_DAYS))
''',
     '''    got = []                                                          # S575 (R1 C4 / C5): the stamp, then the wider list, then the select
    if str(stamp or "").strip():
        got.append(by_stamp(db, stamp, owner))
    if str(wide or "").strip():
        w = _pickable_wide(db, wide, owner)
        if w is None:
            raise ValueError("That paper cannot be linked here.")
        got.append(w)
    if not got:
        b = _pickable(db, p, bid, owner)
        if b is None:
            raise ValueError("That paper cannot be linked here — it is not %s's, not of the last %d days, or not yours to see." % (p["supplier"] or "the supplier", PICK_DAYS))
    else:
        if str(bid or "").strip():
            got.append(_pickable(db, p, bid, owner))
        if len({(x["id"] if x is not None else None) for x in got}) > 1:
            raise ValueError("Pick the paper in one place only.")
        b = got[0]
''', 1),
    # BT11 (C1) -- desk_offer: an old battery with no bill is not offered a new paper as "this bill?"
    ('''        if fr is None or paper_of(db, fr["bill_id"], fr["bill_created_at"]) is not None:
''',
     '''        if fr is None or no_bill(fr) or paper_of(db, fr["bill_id"], fr["bill_created_at"]) is not None:      # S575 (R1 C1)
''', 1),
    # BT12 -- CSS: the folds and the First setup lines
    ('''@media (max-width:640px){ #s571 form.fit{grid-template-columns:1fr} }
''',
     '''@media (max-width:640px){ #s571 form.fit{grid-template-columns:1fr} }
#s571 details.s575more summary{cursor:pointer;color:#0B5F5F;font-size:14px}
#s571 details.s575more .s575grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px;margin-top:6px}
#s571 #s571first form.s575line{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:flex-end;padding:8px 0;border-top:1px solid #ECECE6}
#s571 #s571first form.s575line label{display:flex;flex-direction:column;gap:2px;font-size:13px;margin:0}
#s571 #s571first form.s575line input,#s571 #s571first form.s575line select{margin:0;padding:5px 6px}
#s571 #s571first .s575nm{flex:0 0 240px;align-self:center}
#s571 a.s575ask{color:#8A5A00;font-weight:500}
''', 1),
    # BT13 (C7) -- the list: "How many batteries? — set" for an online UPS with no count (the owner; it opens the place's edit form)
    ('''<td>{{v.battery}}</td><td style="white-space:nowrap">{{dmy(v.fitted) if v.fitted else '—'}}</td>''',
     '''<td>{{v.battery}}{% if v.ask_n and is_owner %}<div class=sub><a class=s575ask href="{{url_for('s571_place', pid=v.p.id, edit=1, _anchor='s571edit')}}">How many batteries? — set</a></div>{% endif %}</td><td style="white-space:nowrap">{{dmy(v.fitted) if v.fitted else '—'}}</td>''', 1),
    # BT14 (C6) -- the Batteries page: the owner-only fold "First setup", before "+ Add a battery place"
    ('''<details class=card id=s571add>''',
     '''{% if is_owner %}<details class=card id=s571first{{' open' if first_open}}><summary style="cursor:pointer;font-weight:600">First setup <span class=muted style="font-weight:400">— {{first|length}} place{{'' if first|length == 1 else 's'}} with no battery recorded yet</span></summary>
<p class=muted style="margin:6px 0;font-size:14px">One line per place: the date its battery was fitted (any past date, dd-mm-yyyy) and Save. For an old battery without its bill, leave “Old battery — no bill”. “New battery fitted” on each row is the full form.</p>
{% if first_open %}{% for fm in get_flashed_messages() %}<div class="note {{'green' if fm.startswith('Saved') else 'amber'}}" style="margin:4px 0">{{fm}}</div>{% endfor %}{% endif %}
{% for v, cs in first %}<form method=post class=s575line data-place="{{v.p.id}}" action="{{url_for('s571_fit', pid=v.p.id)}}"><input type=hidden name=back value=first><input type=hidden name=supplier value="{{v.p.supplier}}"><input type=hidden name=warranty_months value="{{v.p.warranty_months if v.p.warranty_months is not none else ''}}">
<span class=s575nm><b>{{v.p.name}}</b> <span class=sub>{{grpw.get(v.p.grp, '')}}</span></span>
<label>Fitted on<input name=fitted_on required placeholder="dd-mm-yyyy" style="width:110px"></label>
{% if v.p.grp == 'online_ups' %}<label>Batteries in the set<input name=set_n inputmode=numeric value="{{v.p.set_n if v.p.set_n is not none else ''}}" placeholder="N" style="width:60px"></label>{% endif %}
<label>Bill<select name=bill style="max-width:300px"><option value=none>Old battery — no bill</option>{% for c in cs %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<label>or find by stamp<input name=bill_stamp placeholder="B-0162" style="width:90px"></label><button class="btn small">Save</button></form>
{% else %}<p class=muted>Every place has a battery recorded.</p>{% endfor %}</details>{% endif %}
<details class=card id=s571add>''', 1),
    # BT15 (C3, C4) -- "The battery now — its papers": Show older / other papers and Find by stamp
    ('''<label style="margin:0">as<select name=as><option value=bill>the bill</option><option value=card>the warranty card</option></select></label><button class="btn small">Link</button></form>
''',
     '''<details class=s575more style="flex-basis:100%"><summary>Show older / other papers</summary><div style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin-top:6px">
<label style="margin:0">Older / other papers<select name=paper_any style="max-width:560px"><option value="">— every paper you may see, newest first —</option>{% for c in wide %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<label style="margin:0">Find by stamp<input name=paper_stamp placeholder="B-0162" style="max-width:110px"></label></div></details>
<label style="margin:0">as<select name=as><option value=bill>the bill</option><option value=card>the warranty card</option></select></label><button class="btn small">Link</button></form>
''', 1),
    # BT16 (C1) -- the history: "no bill (old battery)" / "no card (old battery)"
    ('''{% elif h.awaited %}<span style="color:#8A5A00">Bill awaited ({{h.awaited}} day{{'' if h.awaited == 1 else 's'}})</span>{% else %}<span class=muted>none linked</span>{% endif %}</td>''',
     '''{% elif h.awaited %}<span style="color:#8A5A00">Bill awaited ({{h.awaited}} day{{'' if h.awaited == 1 else 's'}})</span>{% elif h.nobill %}<span class=muted>no bill (old battery)</span>{% else %}<span class=muted>none linked</span>{% endif %}</td>''', 1),
    ('''{% elif h.card %}{{h.card}}{% else %}<span class=muted>—</span>{% endif %}</td></tr>''',
     '''{% elif h.card %}{{h.card}}{% elif h.nocard %}<span class=muted>no card (old battery)</span>{% else %}<span class=muted>—</span>{% endif %}</td></tr>''', 1),
    # BT17 (C7) -- "How many batteries? — set" opens the edit form
    ('''{% if is_owner %}<details class=card id=s571edit>''',
     '''{% if is_owner %}<details class=card id=s571edit{{' open' if edit_open}}>''', 1),
    # BT18 (C7) -- New battery fitted: "Batteries in the set" first for an online UPS; "Fitted on" any past date
    ('''<label>Fitted on<input name=fitted_on value="{{today}}"></label>
''',
     '''{% if online %}<label>Batteries in the set<input name=set_n inputmode=numeric value="{{p.set_n if p.set_n is not none else ''}}" placeholder="N"></label>{% endif %}
<label>Fitted on<input name=fitted_on value="{{today}}" title="any past date, dd-mm-yyyy (up to 15 years back)"></label>
''', 1),
    ('''<label>Batteries in the set<input name=set_n inputmode=numeric value="{{p.set_n if p.set_n is not none else ''}}" placeholder="N"></label>
''',
     '''{% if not online %}<label>Batteries in the set<input name=set_n inputmode=numeric value="{{p.set_n if p.set_n is not none else ''}}" placeholder="N"></label>{% endif %}
''', 1),
    ('''<label>Batteries in the set<input name=set_n inputmode=numeric value="{{p.set_n if p.set_n is not none else ''}}"></label>
''',
     '''{% if not online %}<label>Batteries in the set<input name=set_n inputmode=numeric value="{{p.set_n if p.set_n is not none else ''}}"></label>{% endif %}
''', 1),
    # BT19 (C1, C4) -- the B.L. form: "Old battery — no bill"; Show older / other papers; Find by stamp
    ('''<label class=full>Bill<select name=bill><option value=awaited>Bill awaited — not scanned yet</option>{% for c in cands %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
''',
     '''<label class=full>Bill<select name=bill><option value=awaited>Bill awaited — not scanned yet</option><option value=none>Old battery — no bill</option>{% for c in cands %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<details class="full s575more"><summary>Show older / other papers</summary><div class=s575grid>
<label>Bill — older / other papers<select name=bill_any><option value="">— every paper you may see, newest first —</option>{% for c in wide %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<label>Bill — find by stamp<input name=bill_stamp placeholder="B-0162"></label></div></details>
''', 1),
    # BT20 (C1, C2, C4) -- the Jasoria form: "Old battery — no bill" / "— no card"; Show older / other papers; Find by stamp
    ('''<label>Bill<select name=bill><option value=awaited>Not scanned yet — link it later</option>{% for c in cands %}''',
     '''<label>Bill<select name=bill><option value=awaited>Not scanned yet — link it later</option><option value=none>Old battery — no bill</option>{% for c in cands %}''', 1),
    ('''<label>Warranty card<select name=card><option value="">Not scanned yet — link it later</option>{% for c in cands %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
''',
     '''<label>Warranty card<select name=card><option value="">Not scanned yet — link it later</option><option value=none>Old battery — no card</option>{% for c in cands %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<details class="full s575more"><summary>Show older / other papers</summary><div class=s575grid>
<label>Bill — older / other papers<select name=bill_any><option value="">— every paper you may see, newest first —</option>{% for c in wide %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<label>Bill — find by stamp<input name=bill_stamp placeholder="B-0162"></label>
<label>Warranty card — older / other papers<select name=card_any><option value="">— every paper you may see, newest first —</option>{% for c in wide %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<label>Warranty card — find by stamp<input name=card_stamp placeholder="B-0162"></label></div></details>
''', 1),
    # BT21 (C6, N7) -- page_main: the First setup lines (places with no battery recorded: current_fit is None), the supplier's candidates
    ('''    tot, groups = overview(db, owner)
    return AR.page(PAGE_TPL, tot=tot, groups=groups, dmy=dmy, grps=GROUPS, payers=PAYERS, made=made,
                   flow=AR._flow("Batteries", url_for("assets_list")))
''',
     '''    tot, groups = overview(db, owner)
    first, cache = [], {}
    if owner:                                                         # S575 (R1 C6 / N7): by current_fit, never by the badge's words
        for _k, _w, _n, rows in groups:
            for v in rows:
                if v["cur"] is None:
                    k = sup1(v["p"]["supplier"])
                    if k not in cache:
                        cache[k] = candidates(db, v["p"], owner)
                    first.append((v, cache[k]))
    return AR.page(PAGE_TPL, tot=tot, groups=groups, dmy=dmy, grps=GROUPS, payers=PAYERS, made=made, first=first, grpw=GROUP_WORD,
                   first_open=request.args.get("first") == "1", flow=AR._flow("Batteries", url_for("assets_list")))
''', 1),
    # BT22 (C1) -- page_place: the history's old-battery words; the links box's wider list; the edit form opened by ?edit=1 (C7)
    ('''                     "awaited": ((today - f).days if (b is None and not r and is_bl(p) and f) else None)})
''',
     '''                     "awaited": ((today - f).days if (b is None and not r and is_bl(p) and f and not no_bill(h)) else None),     # S575 (R1 C1)
                     "nobill": b is None and no_bill(h), "nocard": c is None and no_paper(h, "card")})
''', 1),
    ('''                   cands=candidates(db, p, owner, today) if v["cur"] else [], upk=upk, last_done=last_done, mach=mach, machines=machines,
''',
     '''                   cands=candidates(db, p, owner, today) if v["cur"] else [], upk=upk, last_done=last_done, mach=mach, machines=machines,
                   wide=wide_candidates(db, owner) if v["cur"] else [], edit_open=request.args.get("edit") == "1",       # S575 (R1 C4 / C7)
''', 1),
    # BT23 (C6) -- page_fit: First setup's save and refusal both go back to the fold, with the flash
    ('''        try:
            save_fit(db, p, request.form, owner)
            db.commit()
            flash("Saved: a new battery at %s, fitted %s. The one before is in the history." % (p["name"], dmy(typed_date(request.form.get("fitted_on")) or _today())))
            return redirect(url_for("s571_place", pid=p["id"]))
        except ValueError as e:
            db.rollback()
            flash(str(e) + " Nothing was saved.")
            return redirect(url_for("s571_fit", pid=p["id"]))
''',
     '''        first = request.form.get("back") == "first"                  # S575 (R1 C6): First setup -- back to the fold, the save and the refusal
        had = current_fit(db, p["id"]) is not None                     # S575: "The one before ..." only when there was one
        try:
            save_fit(db, p, request.form, owner)
            db.commit()
            flash("Saved: a new battery at %s, fitted %s.%s" % (p["name"], dmy(typed_date(request.form.get("fitted_on")) or _today()),
                                                                 " The one before is in the history." if had else ""))
            return redirect(url_for("s571_page", first=1, _anchor="s571first") if first else url_for("s571_place", pid=p["id"]))
        except ValueError as e:
            db.rollback()
            flash(("%s: " % p["name"] if first else "") + str(e) + " Nothing was saved.")
            return redirect(url_for("s571_page", first=1, _anchor="s571first") if first else url_for("s571_fit", pid=p["id"]))
''', 1),
    # BT24 (C4, C7) -- page_fit: the wider list and the online UPS's order
    ('''                   cands=candidates(db, p, owner), scan_href=scan, flow=AR._flow("New battery fitted", url_for("s571_place", pid=p["id"])))
''',
     '''                   cands=candidates(db, p, owner), scan_href=scan, online=p["grp"] == "online_ups", wide=wide_candidates(db, owner),     # S575
                   flow=AR._flow("New battery fitted", url_for("s571_place", pid=p["id"])))
''', 1),
    # BT25 (C3, C5) -- post_link: the stamp box and the wider list of "The battery now — its papers"
    ('''        p, fr, b = link_paper(db, fit_id, d.get("paper"), str(d.get("as") or "bill"), owner)
''',
     '''        p, fr, b = link_paper(db, fit_id, d.get("paper"), str(d.get("as") or "bill"), owner,
                              stamp=d.get("paper_stamp") or "", wide=d.get("paper_any") or "")         # S575 (R1 C3 / C5)
''', 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(name, text, edits):
    n = 0
    for i, (old, new, cnt) in enumerate(edits, 1):
        got = text.count(old)
        if got != cnt:
            raise SystemExit("REFUSED: %s edit %d: the anchor is found %d times, not %d:\n  %s" % (name, i, got, cnt, old[:160]))
        text = text.replace(old, new)
        n += 1
    return text, n


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        raise SystemExit(__doc__)
    src, out = a
    os.makedirs(out, exist_ok=True)
    f = "batteries.py"
    raw = open(os.path.join(src, f), "rb").read()
    if md5(raw) != FROM[f]:
        raise SystemExit("REFUSED: %s is %s, not the pinned FROM %s" % (f, md5(raw)[:8], FROM[f][:8]))
    text, n = apply(f, raw.decode("utf-8"), BT_EDITS)
    b = text.encode("utf-8")
    with open(os.path.join(out, f), "wb") as fh:
        fh.write(b)
    print("%-18s %s -> %s  (%d counted edits, each anchor exactly once)" % (f, FROM[f][:8], md5(b)[:8], n))


if __name__ == "__main__":
    main()
