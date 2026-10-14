#!/usr/bin/env python3
"""make_s551.py -- S551_SORTING_DESK (D722): the two edited files rebuilt from the pinned live bytes, and the new module.

    python3 make_s551.py <dir with the live asset_register.py and clinic_papers.py> <out dir>

Exact counted edits (BUILD_NORM_v1): refuses when an input is not at its FROM pin or an anchor is not found exactly the
counted number of times. sorting_desk.py is a new file, copied from the kit as it is."""
import hashlib, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"asset_register.py": "3d5a36e3f9dc398a948f70a87f12d513", "clinic_papers.py": "5b197fb5718f8d28ed8de6c0cafc9ab0"}

AR_EDITS = [
    # A1 (s3.0 5a) -- the guarded mount, after clinic_papers'
    ("# --- S464_CLINIC_PAPERS end ---\n",
     "# --- S464_CLINIC_PAPERS end ---\n"
     "\n\n"
     "# --- S551_SORTING_DESK begin -- D722: the sorting desk, Bills awaited by supplier, the implant ledger, The month (14-Oct-2026) ---\n"
     "# Guarded: if sorting_desk.py is absent or cannot load, this app runs exactly as before -- its links are behind 'is defined'.\n"
     "try:\n"
     "    import sorting_desk as _sorting_desk\n"
     "    _sorting_desk.init(_sys.modules[__name__])\n"
     "except Exception as _ex_s551:                                  # noqa: BLE001\n"
     "    print(\"sorting_desk NOT mounted: %s\" % _ex_s551, file=_sys.stderr)\n"
     "# --- S551_SORTING_DESK end ---\n", 1),
    # A2, A3 (5b) -- the header: Scan app & assets (page title and top bar)
    ("<title>Asset Register</title>", "<title>Scan app &amp; assets</title>", 1),
    ('Asset Register</b> <span class=muted style="color:#9fb3d9">v{{version}}</span>',
     'Scan app &amp; assets</b> <span class=muted style="color:#9fb3d9">v{{version}}</span>', 1),
    # A4 (5c) -- the bills list's instant lane drop-down removed: the row links to the paper
    (r"""{% else %}<form method=post action="{{url_for('bill_lane',bid=b['id'])}}" style="display:inline"><input type=hidden name=back value="{{url_for('bills_list')}}"><select name=lane style="width:auto;max-width:130px" onchange="this.form.submit()">{% for k in lane_order %}<option value="{{k}}" {{'selected' if (b['lane'] or 'clinic')==k}}>{{lanes[k][0].split(' \u2014 ')[0]}}</option>{% endfor %}</select></form>{% endif %}</td>""",
     r"""{% else %}<a href="{{url_for('bill_view',bid=b['id'])}}" title="open the paper to change its lane">{{lanes[b['lane'] or 'clinic'][0].split(' \u2014 ')[0]}}</a>{% endif %}</td>""", 1),
    # A5-A10 (5d) -- the edit page reads "Edit bill" and keeps a lane's own kind
    ('BILLFORM_TPL = """<h2>New bill</h2>', 'BILLFORM_TPL = """<h2>{{\'Edit bill\' if editing else \'New bill\'}}</h2>', 1),
    (r"""<label>Kind</label><select name=kind style="width:auto"><option {{'selected' if hdr.get('kind') not in ('Asset','Pharmacy')}}>Consumable</option><option {{'selected' if hdr.get('kind')=='Asset'}}>Asset</option><option {{'selected' if hdr.get('kind')=='Pharmacy'}}>Pharmacy</option></select>""",
     r"""{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan') %}<label>Kind</label><p style="margin:3px 0"><b>{{hdr.get('kind')}}</b> <span class=muted>kept \u2014 the paper's lane decides it</span></p>{% else %}<label>Kind</label><select name=kind style="width:auto"><option {{'selected' if hdr.get('kind') not in ('Asset','Pharmacy')}}>Consumable</option><option {{'selected' if hdr.get('kind')=='Asset'}}>Asset</option><option {{'selected' if hdr.get('kind')=='Pharmacy'}}>Pharmacy</option></select>{% endif %}""", 1),
    ("def _bill_form_page(hdr=None, items=None, src=None):", "def _bill_form_page(hdr=None, items=None, src=None, editing=False):", 1),
    ("vendors=vendors, today=today().isoformat(), sarvam_on=_sarvam_on())",
     "vendors=vendors, today=today().isoformat(), sarvam_on=_sarvam_on(), editing=editing)", 1),
    ('        kind = f.get("kind") if f.get("kind") in ("Asset", "Consumable", "Pharmacy", "Lab", "Expense", "Document") else (b["kind"] if b["kind"] in ("Lab", "Expense", "Document") else "Consumable")\n',
     '        kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan") else (f.get("kind") if f.get("kind") in ("Asset", "Consumable", "Pharmacy", "Lab", "Expense", "Document") else "Consumable")   # S551: a lane\'s own kind is kept; Consumable / Asset stays the clinic lane\'s choice\n', 1),
    ('    return _bill_form_page(hdr, items, {"stored": b["source_stored"] or "",\n                                        "orig": b["source_orig"] or ""})\n',
     '    return _bill_form_page(hdr, items, {"stored": b["source_stored"] or "",\n                                        "orig": b["source_orig"] or ""}, editing=True)     # S551: "Edit bill"\n', 1),
    # A11-A13 (5e) -- the Month list on a paper's page, and bill_month_set accepting 2015-01 .. this month
    ("        months=_month_choices(), month_label=_month_label,                                # S435\n",
     "        months=_bill_months_s551(b), month_label=_month_label,                            # S435; S551: + its own month and the 12 before\n", 1),
    ("def _good_bill_month(ym):\n",
     'def _bill_months_s551(b, today=None):\n'
     '    """S551: the Month list on a paper\'s page -- the four months of the intake, the paper\'s own month (bill_month, else its\n'
     '    bill date\'s) and the 12 months before it, never later than this month; newest first. The intake\'s list is unchanged."""\n'
     '    t = (today or datetime.date.today()).strftime("%Y-%m")\n'
     '    out = set(_month_choices(today))\n'
     '    own = (b["bill_month"] or "") or (b["bill_date"] or "")[:7]\n'
     '    if re.fullmatch(r"\\d{4}-(0[1-9]|1[0-2])", own or ""):\n'
     '        y, m = int(own[:4]), int(own[5:7])\n'
     '        for _ in range(13):\n'
     '            ym = "%04d-%02d" % (y, m)\n'
     '            if "2015-01" <= ym <= t:\n'
     '                out.add(ym)\n'
     '            m -= 1\n'
     '            if m == 0:\n'
     '                y, m = y - 1, 12\n'
     '    return sorted(out, reverse=True)\n'
     '\n\n'
     'def _any_bill_month_s551(ym, today=None):\n'
     '    """S551: the month a person sets on a paper\'s page -- any YYYY-MM from 2015-01 to this month (the intake keeps _good_bill_month)."""\n'
     '    if not ym or not re.fullmatch(r"\\d{4}-(0[1-9]|1[0-2])", ym):\n'
     '        return None\n'
     '    return ym if "2015-01" <= ym <= (today or datetime.date.today()).strftime("%Y-%m") else None\n'
     '\n\n'
     'def _good_bill_month(ym):\n', 1),
    ('    ym = _good_bill_month((request.form.get("bill_month") or "").strip())\n    if not ym:\n        flash("Choose a month from the list.")\n',
     '    ym = _any_bill_month_s551((request.form.get("bill_month") or "").strip())       # S551: any month from 2015-01 to this month\n    if not ym:\n        flash("Choose a month from the list.")\n', 1),
    # A14 (5h) -- the re-read refuses a patient's paper
    ('    b = db.execute("SELECT id, source_stored, status FROM bills WHERE id=?", (bid,)).fetchone()\n    if not b:\n        abort(404)\n    if not b["source_stored"]:\n',
     '    b = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()\n    if not b:\n        abort(404)\n'
     '    if "subgroup" in b.keys() and (b["subgroup"] or "") == "patient_paper":          # S551: a patient\'s paper is never read again\n'
     '        flash("A patient\'s paper is not read again: it belongs to the surgical case pack.")\n'
     '        return redirect(url_for("bill_view", bid=bid))\n'
     '    if not b["source_stored"]:\n', 1),
    # A15, A16 (5f, 5g) -- the dashboard tile points to The month; the Switches card on the front page
    ("""{% if is_owner %}<a class=card style="text-decoration:none;color:inherit" href="{{url_for('purchases')}}">""",
     """{% if is_owner %}<a class=card style="text-decoration:none;color:inherit" href="{{url_for('s551_month') if s551_on is defined else url_for('purchases')}}">""", 1),
    ("""<span class=muted>tap for consumption &amp; rate history</span></a>{% endif %}</div>""",
     """<span class=muted>{{'tap for the month, section by section' if s551_on is defined else 'tap for consumption & rate history'}}</span></a>{% endif %}</div>\n{% if is_owner and s551_switches_card is defined %}{{ s551_switches_card() }}{% endif %}""", 1),
    # A17, A18 (5g) -- the bills list's two history links point to The month
    ("""<a class="btn small" href="{{url_for('d664_month')}}">Clinic consumables by month</a>{% endif %}""",
     """{% if s551_month_href is defined %}<a class="btn small" href="{{s551_month_href()}}">The month</a>{% else %}<a class="btn small" href="{{url_for('d664_month')}}">Clinic consumables by month</a>{% endif %}{% endif %}""", 1),
    (r"""{% if is_owner %}<a class="btn small" href="{{url_for('purchases')}}">\U0001F4C8 Consumption &amp; rate history</a>""",
     r"""{% if is_owner %}<a class="btn small" href="{{url_for('s551_month') if s551_on is defined else url_for('purchases')}}">\U0001F4C8 {{'Consumption \u2014 now The month' if s551_on is defined else 'Consumption & rate history'}}</a>""", 1),
    # A19 (5g) -- /purchases carries one banner line
    ("Consumption &amp; spend</h2>\n",
     "Consumption &amp; spend</h2>\n"
     r"""{% if s551_on is defined %}<p class=flash>Replaced by The month \u2014 <a href="{{url_for('s551_month')}}">open it</a></p>{% endif %}""" "\n", 1),
]

CP_EDITS = [
    ('VERSION = "S544.1"\n', 'VERSION = "S551"\n', 1),
    # C2, C3 -- three more places a paper can be put, set by the desk only; APART_KEYS (not added to SECTIONS)
    ('    "personal":     "Personal",\n}\n',
     '    "personal":     "Personal",\n'
     '    # S551 (D722): set by the sorting desk only -- kept apart from the consumables everywhere they are counted.\n'
     '    "implant_stock":    "Implant stock",\n'
     '    "clinic_equipment": "Clinic equipment",\n'
     '    "patient_paper":    "A patient\'s paper",\n'
     '}\n', 1),
    ("SECTION_KEYS = tuple(k for k, _n, _h in SECTIONS)\n",
     "SECTION_KEYS = tuple(k for k, _n, _h in SECTIONS)\n"
     "APART_KEYS = SECTION_KEYS + (\"implant_stock\", \"clinic_equipment\", \"patient_paper\")     # S551: never a consumable\n", 1),
    # C4 -- month(): a paper kept apart is not a consumable
    ('    rows = [b for b in rows if (b["subgroup"] or "") not in SECTION_KEYS]',
     '    rows = [b for b in rows if (b["subgroup"] or "") not in APART_KEYS]', 1),
    # C5 -- stand(): the same
    ("""        cx = n("SELECT COUNT(*) " + base + " AND COALESCE(b.lane,'clinic')='clinic' AND b.subgroup IN ('construction','resume','misc','personal')")""",
     """        cx = n("SELECT COUNT(*) " + base + " AND COALESCE(b.lane,'clinic')='clinic' AND b.subgroup IN (" + ",".join("'%s'" % k for k in APART_KEYS) + ")")""", 1),
    # C6 -- _accept: a challan waits for its bill (so it can still be joined), unless it is the final paper
    ('    if not b or (b["lane"] or "clinic") != "clinic" or b["status"] != "draft":\n        return False\n    try:\n        exact, _near = AR._dup_by_triple(db, bid, approved_only=True)\n',
     '    if not b or (b["lane"] or "clinic") != "clinic" or b["status"] != "draft":\n        return False\n'
     '    if "doc_kind" in b.keys() and (b["doc_kind"] or "bill") == "challan" and (b["challan_state"] or "") != "final":\n'
     '        return False                                                 # S551: a challan waits for its bill; it can still be joined\n'
     '    try:\n        exact, _near = AR._dup_by_triple(db, bid, approved_only=True)\n', 1),
    # C7 -- heal(): the same, and a manager's Clinic-equipment Save waits for the owner's own Save
    ("""                          "AND COALESCE(b.subgroup,'')<>'' ORDER BY b.id").fetchall()""",
     """                          "AND COALESCE(b.subgroup,'')<>'' AND COALESCE(b.subgroup,'')<>'clinic_equipment' "        # S551
                          "AND (COALESCE(b.doc_kind,'bill')<>'challan' OR b.challan_state='final') ORDER BY b.id").fetchall()""", 1),
    # C8 -- the join is shared, not copied: join_page's per-page loop moves into join_pages (no commit, no flash)
    ("def join_page(bid):\n",
     'def join_pages(db, head, pages, who):\n'
     '    """S551: the join itself -- shared by the papers page\'s Join (join_page) and the sorting desk. Exactly the loop join_page\n'
     '    ran: each page that may become a page (_page_ok: never an approved paper) is merged into the head\'s PDF by S441 (a NEW\n'
     '    file; the originals stay), recorded in d664_join, marked a page and audited; a challan becomes \'joined\'. No commit and\n'
     '    no flash: the caller commits once. Returns (the pages joined, the stamps left out of the one PDF)."""\n'
     '    pages = [pg for pg in pages if _page_ok(db, pg, head)]\n'
     '    if not pages:\n'
     '        return [], []\n'
     '    bid = head["id"]\n'
     '    batch, now = secrets.token_hex(6), AR._now_ist()\n'
     '    cur, total_before, copied, loose = head["source_stored"], head["total_amount"], False, []\n'
     '    for pg in pages:\n'
     '        merged = None\n'
     '        if AR.S441 is not None and cur and pg["source_stored"]:\n'
     '            try:\n'
     '                merged = AR.S441._merge_pdf(AR.UPLOAD_DIR, {"source_stored": cur}, {"source_stored": pg["source_stored"]})\n'
     '            except Exception:                                    # noqa: BLE001\n'
     '                merged = None\n'
     '        copy = (not copied and total_before is None and pg["total_amount"] is not None)\n'
     '        db.execute("INSERT INTO d664_join(batch, head_id, page_id, at, who, head_before, head_after, merged, "\n'
     '                   "head_total_before, total_copied, page_status, page_reject_reason, page_approved_by, page_approved_at) "\n'
     '                   "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",\n'
     '                   (batch, bid, pg["id"], now, who, cur, merged or cur, 1 if merged else 0, total_before,\n'
     '                    1 if copy else 0, pg["status"], pg["reject_reason"], pg["approved_by"], pg["approved_at"]))\n'
     '        if merged:\n'
     '            db.execute("UPDATE bills SET source_stored=? WHERE id=?", (merged, bid))\n'
     '            cur = merged\n'
     '        else:\n'
     '            loose.append(_stamp(pg))\n'
     '        if copy:                                                 # the total often sits on the last page\n'
     '            db.execute("UPDATE bills SET total_amount=? WHERE id=?", (pg["total_amount"], bid))\n'
     '            copied = True\n'
     '        db.execute("UPDATE bills SET status=\'rejected\', page_of=?, reject_reason=?, approved_by=?, approved_at=? WHERE id=?",\n'
     '                   (bid, "joined into %s" % _stamp(head), who, now, pg["id"]))\n'
     '        AR._audit_bill(db, pg["id"], "d664_joined_into", {"to": bid, "to_stamp": head["stamp_no"], "merged": bool(merged)})\n'
     '        _challan_mark_joined(db, pg, head)                                                          # S531\n'
     '    AR._audit_bill(db, bid, "d664_join", {"pages": [_stamp(x) for x in pages], "after": cur, "batch": batch})\n'
     '    return pages, loose\n'
     '\n\n'
     'def join_page(bid):\n', 1),
    ('        batch, who, now = secrets.token_hex(6), _who(), AR._now_ist()\n'
     '        cur, total_before, copied, loose = head["source_stored"], head["total_amount"], False, []\n'
     '        for pg in pages:\n'
     '            merged = None\n'
     '            if AR.S441 is not None and cur and pg["source_stored"]:\n'
     '                try:\n'
     '                    merged = AR.S441._merge_pdf(AR.UPLOAD_DIR, {"source_stored": cur}, {"source_stored": pg["source_stored"]})\n'
     '                except Exception:                                    # noqa: BLE001\n'
     '                    merged = None\n'
     '            copy = (not copied and total_before is None and pg["total_amount"] is not None)\n'
     '            db.execute("INSERT INTO d664_join(batch, head_id, page_id, at, who, head_before, head_after, merged, "\n'
     '                       "head_total_before, total_copied, page_status, page_reject_reason, page_approved_by, page_approved_at) "\n'
     '                       "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",\n'
     '                       (batch, bid, pg["id"], now, who, cur, merged or cur, 1 if merged else 0, total_before,\n'
     '                        1 if copy else 0, pg["status"], pg["reject_reason"], pg["approved_by"], pg["approved_at"]))\n'
     '            if merged:\n'
     '                db.execute("UPDATE bills SET source_stored=? WHERE id=?", (merged, bid))\n'
     '                cur = merged\n'
     '            else:\n'
     '                loose.append(_stamp(pg))\n'
     '            if copy:                                                 # the total often sits on the last page\n'
     '                db.execute("UPDATE bills SET total_amount=? WHERE id=?", (pg["total_amount"], bid))\n'
     '                copied = True\n'
     '            db.execute("UPDATE bills SET status=\'rejected\', page_of=?, reject_reason=?, approved_by=?, approved_at=? WHERE id=?",\n'
     '                       (bid, "joined into %s" % _stamp(head), who, now, pg["id"]))\n'
     '            AR._audit_bill(db, pg["id"], "d664_joined_into", {"to": bid, "to_stamp": head["stamp_no"], "merged": bool(merged)})\n'
     '            _challan_mark_joined(db, pg, head)                                                          # S531\n'
     '        AR._audit_bill(db, bid, "d664_join", {"pages": [_stamp(x) for x in pages], "after": cur, "batch": batch})\n',
     '        _joined_now, loose = join_pages(db, head, pages, _who())                                   # S551: the shared join\n', 1),
    # C9-C11 -- banners pointing to the new pages; the papers page's links to them
    ("<h2>Clinic consumables</h2>\n",
     "<h2>Clinic consumables</h2>\n"
     r"""{% if s551_month_href is defined and s551_month_href()!=url_for('d664_month') %}<p class="d6say other">Replaced by <a href="{{url_for('s551_month', ym=ym)}}">The month</a> \u2014 section by section, with Implant stock, Construction work and Clinic equipment.</p>{% endif %}""" "\n", 1),
    ('CHALLANS_TPL = CSS + """<div class=d6><h2>Bills awaited <span class=muted>({{rows|length}})</span></h2>\n',
     'CHALLANS_TPL = CSS + """<div class=d6><h2>Bills awaited <span class=muted>({{rows|length}})</span></h2>\n'
     r"""{% if s551_month_href is defined and s551_month_href()!=url_for('d664_month') %}<p class="d6say other">Now by supplier: <a href="{{url_for('s551_awaited')}}">Bills awaited \u2014 challans by supplier</a>, each supplier set once to how it bills.</p>{% endif %}""" "\n", 1),
    (""" &nbsp;<a href="{{url_for('d664_month')}}">This month by group →</a> &nbsp;<a href="{{url_for('d664_challans')}}">Bills awaited{% if nch %} ({{nch}}){% endif %} →</a></p>\n""",
     """ &nbsp;<a href="{{url_for('d664_month')}}">This month by group →</a> &nbsp;<a href="{{url_for('d664_challans')}}">Bills awaited{% if nch %} ({{nch}}){% endif %} →</a></p>\n"""
     """{% if s551_month_href is defined %}<p class=lead><a href="{{url_for('s551_desk')}}"><b>Sorting desk →</b></a> &nbsp;<a href="{{s551_month_href()}}">The month →</a> &nbsp;<a href="{{url_for('s551_awaited')}}">Bills awaited by supplier →</a> &nbsp;<a href="{{url_for('s551_implants')}}">Implant stock ledger →</a></p>{% endif %}\n""", 1),
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
    for name, edits in (("asset_register.py", AR_EDITS), ("clinic_papers.py", CP_EDITS)):
        raw = open(os.path.join(src, name), "rb").read()
        new = build(name, raw, edits)
        open(os.path.join(out, name), "wb").write(new)
        print("%s %s -> %s (%d counted edits)" % (name, FROM[name][:8], md5(new), len(edits)))
    shutil.copy(os.path.join(HERE, "sorting_desk.py"), os.path.join(out, "sorting_desk.py"))
    print("sorting_desk.py new -> %s" % md5(open(os.path.join(out, "sorting_desk.py"), "rb").read()))


if __name__ == "__main__":
    main()
