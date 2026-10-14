#!/usr/bin/env python3
"""make_s555.py -- S555_DESK_CORRECTIONS: the three edited files rebuilt from the pinned live bytes.

    python3 make_s555.py <dir with the live sorting_desk.py, asset_register.py and claude_reread.py> <out dir>

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the
counted number of times. No file is copied from the kit: every byte comes from the live file plus these edits."""
import hashlib, os, sys

FROM = {"sorting_desk.py": "bb28d8c8d95435b4a566d2929f473587",
        "asset_register.py": "c107c6bbb3e6c0c0d0535c5ed094b6e4",
        "claude_reread.py": "47548ab97c55a1f4fb8d5d1a608a1681"}

SD_EDITS = [
    # SD1 -- the corrections' marker (VERSION stays "S551.2": S551's own walk reads it and must stay green)
    ('VERSION = "S551.2"             # S551.2 = fix round 1 (S551_FIX1: C2, C3, C4, N4, N5, N6)\n',
     'VERSION = "S551.2"             # S551.2 = fix round 1 (S551_FIX1: C2, C3, C4, N4, N5, N6)\n'
     'CORRECTIONS = "S555"          # S555_DESK_CORRECTIONS: Save always on screen, dd-mm-yyyy, the misread-date rule, the own name,\n'
     '#                               Claude\'s reading beside each box (VERSION is kept: S551\'s walk reads it)\n', 1),
    # SD2 (item 2) -- every date shown reads dd-mm-yyyy; a typed date is understood in four forms or refused
    ('def _dmy(s):\n    d = _iso(s)\n    return d.strftime("%d-%b-%Y") if d else (s or "")\n\n\n'
     'def _dm(s):\n    d = _iso(s)\n    return d.strftime("%d-%b") if d else (s or "")\n',
     'def _dmy(s):\n'
     '    """S555 item 2: every date the desk and its three pages show reads dd-mm-yyyy."""\n'
     '    d = _iso(s)\n    return d.strftime("%d-%m-%Y") if d else (s or "")\n\n\n'
     'def _dm(s):\n    d = _iso(s)\n    return d.strftime("%d-%m-%Y") if d else (s or "")\n\n\n'
     '_DMY = re.compile(r"(\\d{1,2})[-/.](\\d{1,2})[-/.](\\d{4}|\\d{2})")\n'
     '_YMD = re.compile(r"(\\d{4})-(\\d{1,2})-(\\d{1,2})")\n\n\n'
     'def parse_date(s):\n'
     '    """S555 item 2: a typed date -> datetime.date, or None when it cannot be understood. Accepts dd-mm-yyyy, d-m-yy and\n'
     '    dd/mm/yyyy (day first, as the clinic writes; a two-digit year is 20yy) and yyyy-mm-dd."""\n'
     '    t = str(s if s is not None else "").strip()\n'
     '    try:\n'
     '        m = _YMD.fullmatch(t)\n'
     '        if m:\n'
     '            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))\n'
     '        m = _DMY.fullmatch(t)\n'
     '        if m:\n'
     '            y = int(m.group(3)) + (2000 if len(m.group(3)) == 2 else 0)\n'
     '            return datetime.date(y, int(m.group(2)), int(m.group(1)))\n'
     '    except ValueError:\n'
     '        return None\n'
     '    return None\n\n\n'
     'def typed_date(v, stored=None):\n'
     '    """A date typed in a box -> ISO yyyy-mm-dd for the database (\'\' -> None). A value left as it was shown stays as it\n'
     '    is; anything else that cannot be understood is refused with one plain line, and nothing is saved."""\n'
     '    t = str(v if v is not None else "").strip()\n'
     '    if not t:\n'
     '        return None\n'
     '    if stored and t in (str(stored).strip(), _dmy(stored)):\n'
     '        return stored\n'
     '    d = parse_date(t)\n'
     '    if d is None:\n'
     '        raise DeskError("The date \u201c%s\u201d is not understood \u2014 type it as dd-mm-yyyy. Nothing was saved." % t[:20])\n'
     '    return d.isoformat()\n', 1),
    # SD3 (item 5) -- reading() also returns Claude's supplier, number, date and amount (claude_reader.clean's keys)
    ('    return {"doc_kind": r[0] or data.get("doc_kind"), "made_out_to": data.get("made_out_to"), "items": items}\n',
     '    amt = data.get("total_amount")\n'
     '    try:\n'
     '        amt = float(amt) if (amt not in (None, "") and not isinstance(amt, bool)) else None\n'
     '    except (TypeError, ValueError):\n'
     '        amt = None\n'
     '    dt = parse_date(data.get("bill_date")) or parse_date(data.get("date_as_read"))\n'
     '    return {"doc_kind": r[0] or data.get("doc_kind"), "made_out_to": data.get("made_out_to"), "items": items,\n'
     '            # S555 item 5: Claude\'s supplier, number, date and amount (vendor, bill_no, bill_date / date_as_read, total_amount)\n'
     '            "supplier": str(data.get("vendor") or "").strip(), "number": str(data.get("bill_no") or "").strip(),\n'
     '            "date": dt.isoformat() if dt else "", "amount": amt}\n', 1),
    # SD4 (item 3) -- the misread-date flag: before 2015, more than 7 days after the scan day, or more than 400 days before it
    ('def misread_date(b, today=None):\n'
     '    """A bill_date before 2015, after 31-Dec of next year, or more than 60 days from the scan."""\n'
     '    bd = (b["bill_date"] or "").strip()\n'
     '    if not bd:\n'
     '        return False\n'
     '    d = _iso(bd) if re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", bd) else None\n'
     '    if d is None:\n'
     '        return True\n'
     '    today = today or _today()\n'
     '    if d < datetime.date(2015, 1, 1) or d > datetime.date(today.year + 1, 12, 31):\n'
     '        return True\n'
     '    c = _iso(b["created_at"])\n'
     '    return bool(c and abs((d - c).days) > 60)\n',
     'def misread_date(b, today=None):\n'
     '    """S555 item 3: a bill_date before 2015-01-01, more than 7 days after the scan day, or more than 400 days before it.\n'
     '    The scan day is the paper\'s created_at, else `today` (a year-old bill scanned late is a real paper, not a misread)."""\n'
     '    bd = (b["bill_date"] or "").strip()\n'
     '    if not bd:\n'
     '        return False\n'
     '    d = _iso(bd) if re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", bd) else None\n'
     '    if d is None:\n'
     '        return True\n'
     '    today = today or _today()\n'
     '    if d < datetime.date(2015, 1, 1):\n'
     '        return True\n'
     '    scan = _iso(b["created_at"]) or today\n'
     '    return d > scan + datetime.timedelta(days=7) or (scan - d).days > 400\n', 1),
    # SD5 (items 4, 5) -- the own-name line and Claude's value beside each box
    ('def paper_json(db, b, owner, today=None):\n',
     'OWN_LINE = ("This is your own name \u2014 the reader took the buyer. Type the supplier, or choose Miscellaneous if it is "\n'
     '            "the clinic\u2019s own paper.")\n\n\n'
     'def own_name(db, vendor):\n'
     '    """S555 item 4: the supplier box holds the owner\'s / clinic\'s own name -- the SAME own-name words clinic_papers.suggest()\n'
     '    uses for its \'addressed to you\' note (CP._words(db, \'own_name\'), matched as suggest() matches them). No second list."""\n'
     '    v = re.sub(r"\\s+", " ", (vendor or "").lower()).strip()\n'
     '    return bool(v and CP._hits(v, CP._words(db, "own_name"), whole=False))\n\n\n'
     'def _numkey(s):\n'
     '    return re.sub(r"\\s+", "", str(s or "")).lower()\n\n\n'
     'def claude_lines(db, b, rd, owner):\n'
     '    """S555 items 4, 5: under each of the four boxes, Claude\'s value when it DIFFERS from the stored one (supplier: first two\n'
     '    words; number: spaces and case ignored; date: as typed dates are read; amount: to the rupee) -- shown as "Claude read:\n'
     '    <value> -- use it"; one tap fills the box and nothing is saved until Save. And the own-name line for the supplier box.\n'
     '    Never for a pharmacy paper or a Personal paper to a manager; made_out_to is never shown here."""\n'
     '    if _lane(b) == "pharmacy" or ((b["subgroup"] or "") == "personal" and not owner):\n'
     '        return {}, ""\n'
     '    own = own_name(db, b["vendor"])\n'
     '    out = {}\n'
     '    if rd:\n'
     '        sup = rd.get("supplier") or ""\n'
     '        if sup and not own_name(db, sup) and _key(sup) != _key(b["vendor"]):\n'
     '            out["vendor"] = {"show": sup, "fill": sup}\n'
     '        no = rd.get("number") or ""\n'
     '        if no and _numkey(no) != _numkey(b["bill_no"]):\n'
     '            out["bill_no"] = {"show": no, "fill": no}\n'
     '        cd = parse_date(rd.get("date"))\n'
     '        if cd and cd != parse_date(b["bill_date"]):\n'
     '            out["date"] = {"show": cd.strftime("%d-%m-%Y"), "fill": cd.strftime("%d-%m-%Y")}\n'
     '        ca = rd.get("amount")\n'
     '        if ca is not None:\n'
     '            sa = b["total_amount"]\n'
     '            if sa is None or int(round(float(ca))) != int(round(float(sa))):\n'
     '                out["amount"] = {"show": _inr(ca), "fill": _plain(ca)}\n'
     '    return out, (OWN_LINE if own else "")\n\n\n'
     'def paper_json(db, b, owner, today=None):\n', 1),
    ('    name = b["vendor"] or ""\n'
     '    return {"ok": True, "id": b["id"], "stamp": _stamp(b), "supplier": name, "bill_no": b["bill_no"] or "",\n'
     '            "date": b["bill_date"] or "", "amount": _plain(b["total_amount"]),\n',
     '    name = b["vendor"] or ""\n'
     '    claude, own_line = claude_lines(db, b, rd, owner)                # S555 items 4, 5\n'
     '    return {"ok": True, "id": b["id"], "stamp": _stamp(b), "supplier": name, "bill_no": b["bill_no"] or "",\n'
     '            "date": _dmy(b["bill_date"]) if b["bill_date"] else "", "amount": _plain(b["total_amount"]),\n'
     '            "claude": claude, "own_line": own_line,\n', 1),
    # SD6 (item 2) -- the Save reads the typed date in the four forms, or refuses it
    ('        new["bill_date"] = AR._norm_date(p.get("bill_date"))\n',
     '        new["bill_date"] = typed_date(p.get("bill_date"), b["bill_date"])          # S555 item 2: refused if not understood\n', 1),
    # SD7 (item 2) -- Bills awaited's Note payment
    ('    d = AR._norm_date(day)\n'
     '    if not (d and re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", d) and _iso(d)):\n'
     '        raise DeskError("Type the day it was paid.")\n',
     '    if not str(day or "").strip():\n'
     '        raise DeskError("Type the day it was paid.")\n'
     '    d = typed_date(day)                                              # S555 item 2: refused with one plain line\n', 1),
    # SD8 (item 2) -- the implant ledger's Note payment
    ('    d = AR._norm_date(request.form.get("day"))\n'
     '    try:\n'
     '        amt = _amount(request.form.get("amount"))\n',
     '    try:\n'
     '        d = typed_date(request.form.get("day"))                      # S555 item 2: dd-mm-yyyy, d-m-yy, dd/mm/yyyy, yyyy-mm-dd\n'
     '        amt = _amount(request.form.get("amount"))\n', 1),
    # SD9 (item 1) -- the right-hand panel: fields scroll inside it; Save, its line and the page/blank row in a footer
    ('#right{width:400px;flex:none;background:#fff;border-left:1px solid #d6dde6;overflow:auto;padding:12px 14px;display:flex;flex-direction:column;gap:12px}\n',
     '#right{width:400px;flex:none;background:#fff;border-left:1px solid #d6dde6;display:flex;flex-direction:column;min-height:0;overflow:hidden}\n'
     '#empty{padding:12px 14px}\n'
     '#panel{flex:1 1 auto;min-height:0;display:flex;flex-direction:column}\n'
     '#fields{overflow:auto;flex:1;min-height:0;padding:12px 14px;display:flex;flex-direction:column;gap:12px}\n'
     '#foot{flex:none;padding:10px 14px 12px;border-top:1px solid #d6dde6;background:#fff;display:flex;flex-direction:column;gap:8px}\n'
     '.cr{font-size:12px;color:#5b6878;margin-top:2px}.cr b{font-weight:600;color:#3d4a57}\n'
     '.use{border:0;background:none;color:#2b5d8a;text-decoration:underline;cursor:pointer;font-size:12px;padding:0;font-family:inherit}\n', 1),
    ('<div id=panel style="display:flex;flex-direction:column;gap:12px">\n',
     '<div id=panel><div id=fields>\n', 1),
    ('<div id=pagebox style=', '</div><div id=foot><div id=pagebox style=', 1),
    ('<div class=muted style="font-size:12px" id=savednote>Save files it, accepts it and opens the next paper.</div>\n</div></div></div></div>',
     '<div class=muted style="font-size:12px" id=savednote>Save files it, accepts it and opens the next paper.</div></div>\n</div></div></div></div>', 1),
    # SD10 (items 4, 5) -- a grey line under each box; the own-name line under the supplier
    ('<div class=grid2><label>Supplier<input id=f_vendor></label><label>Bill / challan no<input id=f_no></label><label>Date<input id=f_date placeholder="dd-mm-yyyy"></label><label>Amount<input id=f_amt inputmode=decimal></label></div>',
     '<div class=grid2><div><label>Supplier<input id=f_vendor></label><div class=cr id=cr_vendor></div></div><div><label>Bill / challan no<input id=f_no></label><div class=cr id=cr_bill_no></div></div>'
     '<div><label>Date<input id=f_date placeholder="dd-mm-yyyy"></label><div class=cr id=cr_date></div></div><div><label>Amount<input id=f_amt inputmode=decimal></label><div class=cr id=cr_amount></div></div></div>'
     '<div class=cr id=ownline style="display:none"></div>', 1),
    ("$('f_vendor').value=j.supplier;$('f_no').value=j.bill_no;$('f_date').value=j.date;$('f_amt').value=j.amount;",
     "$('f_vendor').value=j.supplier;$('f_no').value=j.bill_no;$('f_date').value=j.date;$('f_amt').value=j.amount;crs(j);", 1),
    ("function paint(){var j=S.cur;if(!j){return;}",
     "function useb(x,k){return 'Claude read: <b>'+esc(x.show)+'</b> \u2014 <button type=button class=use data-f=\"'+k+'\" data-v=\"'+esc(x.fill)+'\">use it</button>';}\n"
     "function crs(j){var c=j.claude||{};['vendor','bill_no','date','amount'].forEach(function(k){var x=c[k];if(k=='vendor'&&j.own_line){x=null;}$('cr_'+k).innerHTML=x?useb(x,k):'';});\n"
     " var o=j.own_line?esc(j.own_line):'';if(j.own_line&&c.vendor){o+=' '+useb(c.vendor,'vendor');}$('ownline').innerHTML=o;$('ownline').style.display=o?'block':'none';}\n"
     "function paint(){var j=S.cur;if(!j){return;}", 1),
    ("e.target.closest('[data-id],[data-d],[data-k],[data-who]')",
     "e.target.closest('[data-id],[data-d],[data-k],[data-who],[data-f]')", 1),
    (" else if(t.hasAttribute('data-who')){S.who=t.getAttribute('data-who');paint();}});",
     " else if(t.hasAttribute('data-who')){S.who=t.getAttribute('data-who');paint();}\n"
     " else if(t.hasAttribute('data-f')){var F={vendor:'f_vendor',bill_no:'f_no',date:'f_date',amount:'f_amt'};$(F[t.getAttribute('data-f')]).value=t.getAttribute('data-v');}});", 1),
]

AR_EDITS = [
    # A1 (item 8) -- Claude never reads a patient's paper
    ("    Not sent to Claude: the Other-document lane and the Personal and Resumes sections (a person's papers; Sarvam as before).\n",
     "    Not sent to Claude: the Other-document lane and the Personal and Resumes sections (a person's papers; Sarvam as before),\n"
     "    and a patient's paper (S555: belt and braces -- it sits on Other document already).\n", 1),
    ('        if _lane == "other_doc" or (_r["subgroup"] or "") in ("personal", "resume"):\n',
     '        if _lane == "other_doc" or (_r["subgroup"] or "") in ("personal", "resume", "patient_paper"):     # S555 item 8\n', 1),
    # A3 (item 6) -- the bills list's Lane column: one short word per lane, for a live row and a rejected row alike
    (r"""{% elif b['status']=='rejected' %}<span class=muted>{{lanes[b['lane'] or 'clinic'][0].split(' ')[0]}}</span>
{% else %}<a href="{{url_for('bill_view',bid=b['id'])}}" title="open the paper to change its lane">{{lanes[b['lane'] or 'clinic'][0].split(' \u2014 ')[0]}}</a>{% endif %}</td>""",
     r"""{% elif b['status']=='rejected' %}<span class=muted>{{lane_word(b)}}</span>
{% else %}<a href="{{url_for('bill_view',bid=b['id'])}}" title="open the paper to change its lane">{{lane_word(b)}}</a>{% endif %}</td>""", 1),
    ('        bills=bills, q=q, fk=fk, fs=fs, npend=npend, lanes=LANES, lane_order=LANE_ORDER, flow=_flow("Purchases"),\n',
     '        bills=bills, q=q, fk=fk, fs=fs, npend=npend, lanes=LANES, lane_order=LANE_ORDER, flow=_flow("Purchases"), lane_word=_lane_word_s555,\n', 1),
    ('KIND_LANE = {"Pharmacy": "pharmacy", "Lab": "lab_purchase", "Expense": "owner_expense", "Document": "other_doc"}\n',
     'KIND_LANE = {"Pharmacy": "pharmacy", "Lab": "lab_purchase", "Expense": "owner_expense", "Document": "other_doc"}\n'
     '# S555 item 6: one short word per lane -- the one place the bills list\'s Lane column reads (it showed "Clinic" for a rejected\n'
     '# row and "Clinic bill" for a live one: the label was cut at the first space in one branch and at the dash in the other).\n'
     'LANE_WORD = {"clinic": "Clinic", "pharmacy": "Pharmacy", "lab_purchase": "NK Pathology", "owner_expense": "Personal expense",\n'
     '             "other_doc": "Other document"}\n'
     '\n\n'
     'def _lane_word_s555(b):\n'
     '    """S555: the lane of a bills-list row in one word -- a live or a rejected row alike; an old row with no lane by its kind."""\n'
     '    try:\n'
     '        ln = b["lane"] or KIND_LANE.get(b["kind"], "clinic")\n'
     '    except (IndexError, KeyError):\n'
     '        ln = "clinic"\n'
     '    return LANE_WORD.get(ln) or LANES.get(ln, (ln or "",))[0].split(" \\u2014 ")[0]\n', 1),
]

RR_EDITS = [
    # R1-R3 (item 8) -- the re-read of older scans never selects a patient's paper
    ("  Personal and Resumes sections (a person's papers are never sent in bulk).\n",
     "  Personal and Resumes sections (a person's papers are never sent in bulk), and a patient's paper (S555).\n", 1),
    ('''        "AND " + KIND_LANE_SQL + "<>'other_doc' AND COALESCE(b.subgroup,'') NOT IN ('personal','resume') "\n''',
     '''        "AND " + KIND_LANE_SQL + "<>'other_doc' AND COALESCE(b.subgroup,'') NOT IN ('personal','resume','patient_paper') "\n''', 1),
    ('            and r["sg"] not in ("personal", "resume") and ',
     '            and r["sg"] not in ("personal", "resume", "patient_paper") and ', 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, raw, edits):
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not the pinned %s" % (name, md5(raw)[:8], FROM[name][:8]))
    s = raw.decode("utf-8")
    for i, (old, new, n) in enumerate(edits, 1):
        c = s.count(old)
        if c != n:
            sys.exit("REFUSED: %s edit %d anchor found %d times, expected %d" % (name, i, c, n))
        s = s.replace(old, new)
    return s.encode("utf-8")


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for name, edits in (("sorting_desk.py", SD_EDITS), ("asset_register.py", AR_EDITS), ("claude_reread.py", RR_EDITS)):
        raw = open(os.path.join(src, name), "rb").read()
        new = build(name, raw, edits)
        open(os.path.join(out, name), "wb").write(new)
        print("%s %s -> %s (%d counted edits)" % (name, FROM[name][:8], md5(new), len(edits)))


if __name__ == "__main__":
    main()
