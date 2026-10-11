#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s530.py -- S530_PAPERS_SECTIONS (D710, D689 item 1): exact, counted edits on the md5-pinned live clinic_papers.py.

    python3 make_s530.py <live_dir> <out_dir>

Reads  <live_dir>/clinic_papers.py  (must be 5e21f4916272270d5e1a54366b43c5ad, S466.1)
Writes <out_dir>/clinic_papers.py (S530.1) and prints its md5. Every anchor must occur EXACTLY once or the build refuses.
asset_register.py is NOT edited by this kit (the hooks it already carries -- is defined -- are enough)."""
import hashlib, os, sys

FROM = "5e21f4916272270d5e1a54366b43c5ad"


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(t, anchor, new, name, where="replace"):
    n = t.count(anchor)
    if n != 1:
        raise SystemExit("REFUSED: anchor for %s found %d times (need 1)" % (name, n))
    return t.replace(anchor, (anchor + new) if where == "after" else (new + anchor) if where == "before" else new)


def build(t):
    # ---------------------------------------------------------------- C1 the head
    t = edit(t, '    Owner and manager only (the asset app\'s own checker_required). Staff are asked nothing new and see nothing new.\n',
             '''    S530 -- EVERY SCAN FINDS ITS HOME (D710, D689 item 1; the owner's rulings of 11-Oct-2026):
        FOUR SECTIONS beside the clinic consumables: Construction work, Resumes, Miscellaneous documents, Personal.
        A section lives in the same column, bills.subgroup, as the three consumable groups. The papers-to-sort list
        now also shows the "Other document" lane (a resume reaches it); a paper on the Clinic, Other-document or Dr MK
        expense lane can take a section; the consumable groups stay the clinic lane's own. Construction work is
        counted on its own, outside Clinic consumables, and is never called a clinic or an MK expense by the system
        (D664 stands). Personal is the OWNER's: set, seen and counted by him only.
        SORTED = ACCEPTED: a clinic paper that gets its group is accepted there and then, by the app's own approve
        rules (the same-vendor-number-amount duplicate check, the vendor book, the asset back-fill) -- no separate
        approve tap. The backlog is healed at every start, idempotently: a clinic draft that already has a group is
        accepted the same way. The approve / reject doors stay for a paper to refuse.
        WHERE EACH PAPER STANDS: one collapsed fold at the top of the papers page, the owner only -- this month's
        scans by lane: handed on, sorted, waiting (with the oldest age).
''', "C1 head", "after")
    # ---------------------------------------------------------------- C2 version and the vocabulary
    t = edit(t, 'VERSION = "S466.1"', 'VERSION = "S530.1"', "C2 version")
    t = edit(t, '''    "others":     "Others",
}
GROUP_OF = {"procedure": "procedure", "xray": "xray", "xray_small": "xray", "xray_11x14": "xray", "others": "others"}
''', '''    "others":     "Others",
    # S530: the four sections (D689 item 1). Same column, kept apart from the consumables everywhere they are counted.
    "construction": "Construction work",
    "resume":       "Resumes",
    "misc":         "Miscellaneous documents",
    "personal":     "Personal",
}
GROUP_OF = {"procedure": "procedure", "xray": "xray", "xray_small": "xray", "xray_11x14": "xray", "others": "others"}
CONSUMABLE = ("procedure", "xray", "xray_small", "xray_11x14", "others")
SECTIONS = (("construction", "Construction work", "cement, paint, wiring, plumbing, labour \\u2014 bills, estimates, slips"),
            ("resume", "Resumes", "CVs and job applications"),
            ("misc", "Miscellaneous documents", "letters, notices, forms \\u2014 not a bill, fits nowhere else"),
            ("personal", "Personal", "your own papers \\u2014 shown to you only"))
SECTION_KEYS = tuple(k for k, _n, _h in SECTIONS)
SORT_LANES = ("clinic", "other_doc", "owner_expense")      # a paper on these lanes can take a section; groups: clinic only
''', "C2 vocabulary")
    t = edit(t, '''    "medicine_supplier": ["pharma", "pharmaceutical", "pharmaceuticals", "drug house", "drugs", "medical agencies",
                          "medical agency", "medicine", "medicines"],
}''', '''    "medicine_supplier": ["pharma", "pharmaceutical", "pharmaceuticals", "drug house", "drugs", "medical agencies",
                          "medical agency", "medicine", "medicines"],
    # S530: the sections' words
    "resume":    ["resume", "curriculum vitae", "cv", "bio-data", "biodata", "bio data", "qualification", "qualifications",
                  "experience", "applied for", "application for the post", "post of", "career objective", "objective",
                  "b.sc", "bsc", "gnm", "anm", "dnb", "mbbs", "bpt", "mpt", "d.pharm", "b.pharm", "hobbies", "declaration",
                  "father's name", "fathers name", "marital status"],
    "construction": ["cement", "sand", "bajri", "gitti", "brick", "bricks", "eent", "tiles", "tile", "marble", "granite", "paint",
                     "paints", "putty", "primer", "wiring", "wire", "wires", "switch", "switches", "mcb", "electrician", "plumber",
                     "plumbing", "pipe", "pipes", "cpvc", "upvc", "tap", "taps", "labour", "labor", "mazdoor", "mistri", "mason",
                     "contractor", "estimate", "quotation", "steel", "saria", "tmt", "ply", "plywood", "sunmica", "laminate",
                     "hinges", "hardware", "fitting", "fittings", "door", "window", "glass", "false ceiling", "pop sheet"],
    "construction_supplier": ["hardware", "paints", "paint", "electricals", "electric", "sanitary", "sanitaryware", "tiles",
                              "timber", "plywood", "glass", "builders", "construction", "steel", "cement"],
    "own_name":  ["manoj", "agarwal clinic", "agrawal clinic", "aggarwal clinic", "advanced orthop", "ortho surgery centre",
                  "orthopaedic surgery centre"],
}''', "C2b words")
    # ---------------------------------------------------------------- C3 the suggestion: the sections
    t = edit(t, '''    if xr and len(xr) >= len(pr):
        size = ("xray_11x14" if _hits(t, _words(db, "xray_11x14")) else''', '''    # S530: a resume, a construction paper, a paper addressed to the owner
    rs = _hits(t, _words(db, "resume"))
    if len(rs) >= 2 and not has_bill_no and not has_total and not xr and not pr:
        return dict(kind="sub", value="resume", label=SUB["resume"], why="the words read on it: " + ", ".join(rs[:3]))
    cons = _hits(t, _words(db, "construction"))
    consup = _hits(v, _words(db, "construction_supplier"), whole=False)
    if (len(cons) >= 2 or (cons and consup) or (consup and not pr and not xr and not st)) and len(cons) >= len(pr):
        return dict(kind="sub", value="construction", label=SUB["construction"],
                    why=("the words read on it: " + ", ".join(cons[:3])) if cons else "the supplier's name (" + ", ".join(consup[:2]) + ")")
    if _hits(v, _words(db, "own_name"), whole=False) and not xr and not pr and not st and not orth:
        return dict(kind="note", why="it is addressed to you, not a supplier's bill \\u2014 Personal or Miscellaneous documents, your call")
    if xr and len(xr) >= len(pr):
        size = ("xray_11x14" if _hits(t, _words(db, "xray_11x14")) else''', "C3 suggest")
    # ---------------------------------------------------------------- C4 the live rows: the to-sort list widens to the Other-document lane
    t = edit(t, '''def _words(db, name):''', '''def _live_sort(db, alias="b"):
    """S530: the papers to SORT -- the clinic lane's live bills and the Other-document lane's captured papers;
    never a rejected paper, a duplicate or a page joined into another."""
    w = ("((COALESCE(%s.lane,'clinic')='clinic' AND %s.status IN ('draft','approved')) OR (%s.lane='other_doc' AND %s.status='captured'))"
         " AND %s.dup_of IS NULL" % (alias, alias, alias, alias, alias))
    if "page_of" in _cols(db):
        w += " AND %s.page_of IS NULL" % alias
    return w


def _live_sections(db, alias="b"):
    """S530: the papers that can carry a section (clinic, other document, Dr MK expense), live."""
    w = ("COALESCE(%s.lane,'clinic') IN ('clinic','other_doc','owner_expense') AND %s.status IN ('draft','approved','captured')"
         " AND %s.dup_of IS NULL" % (alias, alias, alias))
    if "page_of" in _cols(db):
        w += " AND %s.page_of IS NULL" % alias
    return w


''', "C4 live_sort", "before")
    # ---------------------------------------------------------------- C5 to_sort_count follows the widened list
    t = edit(t, '''        return db.execute("SELECT COUNT(*) FROM bills b WHERE " + _live(db) + " AND COALESCE(b.subgroup,'')=''"
                          ).fetchone()[0]''', '''        return db.execute("SELECT COUNT(*) FROM bills b WHERE " + _live_sort(db) + " AND COALESCE(b.subgroup,'')=''"
                          ).fetchone()[0]''', "C5 to_sort_count")
    # ---------------------------------------------------------------- C6 the papers page: the fold, the title, the widened list
    t = edit(t, '''PAPERS_TPL = CSS + """<div class=d6><h2>Clinic papers to sort{% if total %} <span class="badge amber">{{total}} paper{{'' if total==1 else 's'}}</span>{% endif %}</h2>
<p class=lead>For you or Shavez. Staff are asked nothing new when they scan.
 &nbsp;<a href="{{url_for('d664_month')}}">This month by group →</a></p>''',
             '''PAPERS_TPL = CSS + """<div class=d6><h2>Papers to sort{% if total %} <span class="badge amber">{{total}} paper{{'' if total==1 else 's'}}</span>{% endif %}</h2>
<p class=lead>For you or Shavez. Staff are asked nothing new when they scan. One tap sorts a paper and accepts it.
 &nbsp;<a href="{{url_for('d664_month')}}">This month by group →</a></p>
{% if stand %}<details class="d6x d6card" style="padding:10px 14px"><summary class=d6opt style="margin:0;border:0;padding:4px 36px 4px 0">Where each paper stands — {{stand.label}}<small>{{stand.total}} scan{{'' if stand.total==1 else 's'}} this month · {{stand.waiting}} waiting</small></summary>
<table class=d6t style="margin-top:8px">{% for r in stand.rows %}<tr><td>{% if r.href %}<a href="{{r.href}}" style="text-decoration:none"><b>{{r.name}}</b></a>{% else %}<b>{{r.name}}</b>{% endif %}<br><span class=muted style="font-size:13px">{{r.text}}</span></td><td class=r>{{r.n}}</td></tr>{% endfor %}</table>
<p class=muted style="font-size:13px;margin:8px 0 2px">Pharmacy scans are handed to the Sanjeevni side, which pairs each with its Marg bill; lab and Dr MK expense scans go into the accountants' pack. A paper counts in the month set on its bill, else its bill date, else the month it was scanned.</p></details>{% endif %}''',
             "C6 papers head")
    t = edit(t, '''<div style="flex:1;min-width:0"><div class=d6top><b><a href="{{url_for('bill_view',bid=p.b['id'])}}" style="text-decoration:none">{{p.stamp}}</a> · {{p.b['vendor'] or 'supplier not read'}}</b>''',
             '''<div style="flex:1;min-width:0"><div class=d6top><b><a href="{{url_for('bill_view',bid=p.b['id'])}}" style="text-decoration:none">{{p.stamp}}</a> · {{p.b['vendor'] or ('a document — not a bill' if p.b['lane']=='other_doc' else 'supplier not read')}}</b>''',
             "C6b card head")
    t = edit(t, '''{% if p.s and p.s.kind=='sub' %}<div class=d6say>Looks like <b>Clinic consumables · {{p.s.label}}</b> — from {{p.s.why}}.{% if p.s.value=='xray' %} Which film?{% endif %}</div>''',
             '''{% if p.s and p.s.kind=='sub' %}<div class=d6say>Looks like <b>{{'Clinic consumables · ' if p.s.value in cons else ''}}{{p.s.label}}</b> — from {{p.s.why}}.{% if p.s.value=='xray' %} Which film?{% endif %}</div>''',
             "C6c suggestion line")
    t = edit(t, '''<p class=muted>Skip leaves the paper here for later. Nothing is lost by not sorting: an unsorted paper still counts under Clinic consumables.</p></div>"""''',
             '''<p class=muted>Skip leaves the paper here for later. Nothing is lost by not sorting: an unsorted clinic paper still counts under Clinic consumables, not sorted.</p></div>"""''',
             "C6d foot")
    # ---------------------------------------------------------------- C7 the paper page: the section picker
    old_pick_start = '''{% if on_clinic %}<div class=d6card>
{% if p.s and p.s.kind!='sub' %}'''
    t = edit(t, old_pick_start, '''{% if on_sort %}<div class=d6card>
{% if p.s and p.s.kind!='sub' %}''', "C7a picker open")
    old_pick = t[t.index('''<b style="font-size:16px">{{'If it is a clinic consumable after all, which one?' if (p.s and p.s.kind=='lane') else 'Which clinic consumable?'}}</b>'''):
                 t.index('''{% elif p.b['page_of'] %}<div class=d6card><b>This paper is a page of another paper.</b>''')]
    new_pick = '''<b style="font-size:16px">{{'If it is ours after all, which section?' if (p.s and p.s.kind=='lane') else 'Which section?'}}</b>
<p class=muted style="font-size:13px;margin:4px 0 10px">One tap saves it{% if accepts %} and accepts the paper{% endif %}. Optional — leave it and the paper waits here{% if on_clinic %} under Clinic consumables, not sorted{% endif %}.</p>
<form method=post action="{{url_for('d664_set',bid=p.b['id'])}}"><input type=hidden name=back value="{{back}}">
{% if on_clinic %}<details class=d6x {{'open' if (cur in cons or sug in cons or (not cur and sug not in secs))}}><summary class="d6opt {{'on' if cur in cons}}">Clinic consumables{% if sug in cons %} <span style="font-weight:400">— suggested</span>{% endif %}<small>then one tap: Procedure room · X-ray films · Others</small></summary>
<div class=in style="display:block;padding-left:12px">
<button class="d6opt {{'on' if cur=='procedure'}}" name=subgroup value=procedure>Procedure room{% if sug=='procedure' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>fibre cast, roller bandage, cotton, tape, betadine</small></button>
<details class=d6x {{'open' if (cur.startswith('xray') or sug.startswith('xray'))}}><summary class="d6opt {{'on' if cur.startswith('xray')}}">X-ray films{% if sug.startswith('xray') %} <span style="font-weight:400">— suggested</span>{% endif %}<small>then one more tap: small film or 11 x 14</small></summary>
<div class=in><button class="d6b {{'yes' if cur=='xray_small' else 'alt'}}" name=subgroup value=xray_small>Small film</button>
<button class="d6b {{'yes' if cur=='xray_11x14' else 'alt'}}" name=subgroup value=xray_11x14>11 x 14</button>
<button class="d6b {{'yes' if cur=='xray' else 'skip'}}" name=subgroup value=xray>size not known</button></div></details>
<button class="d6opt {{'on' if cur=='others'}}" name=subgroup value=others>Others{% if sug=='others' %} <span style="font-weight:400">— suggested</span>{% endif %}<small>stationery and the rest</small></button>
</div></details>{% endif %}
{% for k, nm, hint in sections %}{% if k!='personal' or owner %}<button class="d6opt {{'on' if cur==k}}" name=subgroup value="{{k}}">{{nm}}{% if sug==k %} <span style="font-weight:400">— suggested</span>{% endif %}<small>{{hint}}</small></button>{% endif %}{% endfor %}
{% if cur %}<button class="d6b skip" name=subgroup value="">Clear it</button>{% endif %}
<a class="d6b skip" href="{{back}}">{{'Done' if cur else 'Skip for now'}}</a></form>
{% if cur=='construction' %}<p class=muted style="font-size:13px;margin:10px 0 0">Construction work is counted on its own. Whether it is a clinic expense or an MK expense is not decided by the system.</p>{% endif %}</div>
'''
    t = t.replace(old_pick, new_pick)
    t = edit(t, '''{% else %}<div class=d6card><b>This paper is not on the clinic lane.</b><br><span class=muted>Groups belong to clinic consumables only.</span></div>{% endif %}''',
             '''{% else %}<div class=d6card><b>This paper takes no section.</b><br><span class=muted>Sections belong to papers on the Clinic, Other-document and Dr MK expense lanes; a pharmacy or lab scan is kept by its own side.</span></div>{% endif %}''',
             "C7b no-section branch")
    t = edit(t, '''{% if on_clinic %}<p class=muted>The suggestion comes from the supplier and the words read on the paper. The supplier alone never decides: Yuvika sells orthotics to the pharmacy too.</p>{% endif %}</div>"""''',
             '''{% if on_sort %}<p class=muted>The suggestion comes from the supplier and the words read on the paper. The supplier alone never decides: Yuvika sells orthotics to the pharmacy too.</p>{% endif %}</div>"""''',
             "C7c foot")
    # ---------------------------------------------------------------- C8 the month page: the sections card
    t = edit(t, '''{% if unsorted %}<p><a class=btn href="{{url_for('d664_papers')}}">Sort the {{unsorted}} unsorted paper{{'' if unsorted==1 else 's'}}</a></p>{% endif %}''',
             '''{% if secs %}<div class=d6card style="padding:2px 14px"><table class=d6t>
<tr><td colspan=2 style="border-top:0"><b style="font-size:16px">Other sections</b><br><span class=muted style="font-size:13px">kept apart from Clinic consumables</span></td></tr>
{% for r in secs %}<tr><td><a href="{{url_for('d664_month',ym=ym,g=r.key)}}" style="text-decoration:none"><b>{{r.name}}</b></a><br><span class=muted style="font-size:13px">{{r.n}} paper{{'' if r.n==1 else 's'}}{% if r.vendors %} · {{r.vendors}}{% endif %}{% if r.key=='construction' %} · clinic / MK not decided{% endif %}{% if r.key=='personal' %} · you only{% endif %}</span></td>
<td class=r>{% if r.money %}<b>{{inr(r.total)}}</b>{% else %}<span class=muted>—</span>{% endif %}</td></tr>{% endfor %}</table></div>{% endif %}
{% if unsorted %}<p><a class=btn href="{{url_for('d664_papers')}}">Sort the {{unsorted}} unsorted paper{{'' if unsorted==1 else 's'}}</a></p>{% endif %}''',
             "C8 month sections card")
    # ---------------------------------------------------------------- C9 papers(): the widened list and the fold
    t = edit(t, '''def papers():
    db = AR.get_db()
    where = _live(db) + " AND COALESCE(b.subgroup,'')=''"
    total = db.execute("SELECT COUNT(*) FROM bills b WHERE " + where).fetchone()[0]
    rows = db.execute("SELECT b.* FROM bills b WHERE " + where + " ORDER BY b.id DESC LIMIT ?", (PAGE_N,)).fetchall()
    return AR.page(PAPERS_TPL, papers=[_paper(db, b) for b in rows], total=total, more=(total > len(rows)),
                   inr=_inr, flow=AR._flow("Clinic papers to sort", url_for("bills_list")))''',
             '''def papers():
    db = AR.get_db()
    where = _live_sort(db) + " AND COALESCE(b.subgroup,'')=''"
    total = db.execute("SELECT COUNT(*) FROM bills b WHERE " + where).fetchone()[0]
    rows = db.execute("SELECT b.* FROM bills b WHERE " + where + " ORDER BY b.id DESC LIMIT ?", (PAGE_N,)).fetchall()
    return AR.page(PAPERS_TPL, papers=[_paper(db, b) for b in rows], total=total, more=(total > len(rows)),
                   inr=_inr, cons=CONSUMABLE, stand=(stand(db) if AR.is_owner() else None),
                   flow=AR._flow("Papers to sort", url_for("bills_list")))


def stand(db, today=None):
    """S530: where each paper stands this month -- the owner's one fold. Never raises (the page must not fail for it)."""
    try:
        today = today or datetime.date.today()
        ym = today.strftime("%Y-%m")
        extra = " AND b.page_of IS NULL" if "page_of" in _cols(db) else ""
        base = "FROM bills b WHERE b.status<>'rejected' AND b.dup_of IS NULL" + extra + " AND " + MONTH_OF + "=?"
        def n(sql, *a):
            return db.execute(sql, (ym,) + a).fetchone()[0]
        rows = []
        ph = n("SELECT COUNT(*) " + base + " AND b.lane='pharmacy'")
        rows.append(dict(name="Pharmacy purchases \\u2014 Sanjeevni", n=ph, text="handed to the Sanjeevni side; its register pairs each with its Marg bill", href=url_for("bills_list")))
        cl = n("SELECT COUNT(*) " + base + " AND COALESCE(b.lane,'clinic')='clinic'")
        cs = n("SELECT COUNT(*) " + base + " AND COALESCE(b.lane,'clinic')='clinic' AND b.subgroup IN ('procedure','xray','xray_small','xray_11x14','others')")
        cx = n("SELECT COUNT(*) " + base + " AND COALESCE(b.lane,'clinic')='clinic' AND b.subgroup IN ('construction','resume','misc','personal')")
        cw = n("SELECT COUNT(*) " + base + " AND COALESCE(b.lane,'clinic')='clinic' AND COALESCE(b.subgroup,'')=''")
        oldest = db.execute("SELECT MIN(b.created_at) FROM bills b WHERE " + _live_sort(db) + " AND COALESCE(b.subgroup,'')=''").fetchone()[0]
        age = ""
        if oldest:
            try:
                age = " \\u00b7 the oldest %d days" % (today - datetime.date.fromisoformat(str(oldest)[:10])).days
            except Exception:                                        # noqa: BLE001
                age = ""
        rows.append(dict(name="Clinic papers", n=cl, text="%d sorted as consumables, %d in a section, %d waiting%s" % (cs, cx, cw, age if cw else ""), href=None))
        od = n("SELECT COUNT(*) " + base + " AND b.lane='other_doc'")
        ow = n("SELECT COUNT(*) " + base + " AND b.lane='other_doc' AND COALESCE(b.subgroup,'')=''")
        rows.append(dict(name="Other documents", n=od, text="%d in a section, %d waiting" % (od - ow, ow), href=None))
        lb = n("SELECT COUNT(*) " + base + " AND b.lane='lab_purchase'")
        rows.append(dict(name="Lab purchases \\u2014 NK Pathology", n=lb, text="to the accountants' pack (8.1)" if lb else "none this month \\u2014 Sukhveer's duty", href=None))
        me = n("SELECT COUNT(*) " + base + " AND b.lane='owner_expense'")
        mw = 0
        try:
            mw = db.execute("SELECT COUNT(*) FROM d664_warranty w JOIN bills b ON b.id=w.bill_id WHERE " + MONTH_OF + "=?", (ym,)).fetchone()[0]
        except sqlite3.Error:
            mw = 0
        rows.append(dict(name="Dr MK expense", n=me, text="to the accountants' pack (8.2); %d with a warranty noted" % mw, href=None))
        total = n("SELECT COUNT(*) " + base)
        waiting = db.execute("SELECT COUNT(*) FROM bills b WHERE " + _live_sort(db) + " AND COALESCE(b.subgroup,'')=''").fetchone()[0]
        return dict(label=AR._month_label(ym), rows=rows, total=total, waiting=waiting)
    except Exception:                                                # noqa: BLE001
        return None''', "C9 papers()")
    # ---------------------------------------------------------------- C10 paper(): the picker's context
    t = edit(t, '''    return AR.page(PAPER_TPL, p=p, of_stamp=(_stamp(of) if of else ""), cur=p["group"], sug=(p["s"]["value"] if (p["s"] and p["s"]["kind"] == "sub") else ""),
                   on_clinic=((b["lane"] or "clinic") == "clinic" and b["status"] != "rejected"),''',
             '''    if (b["subgroup"] or "") == "personal" and not AR.is_owner():
        abort(403)                                                   # S530: a Personal paper is the owner's alone
    return AR.page(PAPER_TPL, p=p, of_stamp=(_stamp(of) if of else ""), cur=p["group"], sug=(p["s"]["value"] if (p["s"] and p["s"]["kind"] == "sub") else ""),
                   on_clinic=((b["lane"] or "clinic") == "clinic" and b["status"] != "rejected"),
                   on_sort=((b["lane"] or "clinic") in SORT_LANES and b["status"] != "rejected"),           # S530
                   sections=SECTIONS, secs=SECTION_KEYS, cons=CONSUMABLE, owner=AR.is_owner(),
                   accepts=((b["lane"] or "clinic") == "clinic" and b["status"] == "draft"),''', "C10 paper ctx")
    # ---------------------------------------------------------------- C11 set_group(): sections, lanes, the owner's Personal, sorted = accepted
    old_set = t[t.index('def set_group(bid):'):t.index('def _ym_ok(ym):')]
    new_set = '''def set_group(bid):
    db = AR.get_db()
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b:
        abort(404)
    to = (request.form.get("subgroup") or "").strip().lower()
    back = _back()
    stamp = b["stamp_no"] or ("#%d" % bid)
    if to and to not in SUB:
        abort(400)
    lane = b["lane"] or "clinic"
    if lane not in SORT_LANES or b["status"] == "rejected":
        flash("%s is not a live paper on the Clinic, Other-document or Dr MK expense lane \\u2014 it takes no section." % stamp)
        return redirect(back)
    if to in CONSUMABLE and lane != "clinic":
        flash("%s is not on the clinic lane \\u2014 the consumable groups belong to clinic bills; move it there first." % stamp)
        return redirect(back)
    if (to == "personal" or (b["subgroup"] or "") == "personal") and not AR.is_owner():
        flash("Personal papers are the owner's alone.")
        return redirect(back)
    frm = b["subgroup"] or ""
    accepted = False
    if to != frm:
        db.execute("UPDATE bills SET subgroup=? WHERE id=?", (to or None, bid))
        AR._audit_bill(db, bid, "subgroup", {"from": frm, "to": to})
        if to and lane == "clinic" and b["status"] == "draft":
            accepted = _accept(db, bid, _who())                      # S530: sorted = accepted
        db.commit()
    if to:
        flash("%s is under %s.%s" % (stamp, SUB[to], " Accepted." if accepted else ""))
    else:
        flash("%s has no section now." % stamp)
    return redirect(back)


def _accept(db, bid, who):
    """S530 (D710): sorted = accepted, by the app's own approve rules -- the same-vendor-number-amount duplicate check
    (refused and said, as the approve door says it), the vendor book, the asset back-fill. Returns True when accepted."""
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b or (b["lane"] or "clinic") != "clinic" or b["status"] != "draft":
        return False
    try:
        exact, _near = AR._dup_by_triple(db, bid, approved_only=True)
    except Exception:                                                # noqa: BLE001
        exact = None
    if exact:
        AR._audit_bill(db, bid, "d710_not_accepted", {"same_as": exact["stamp_no"] or ("#%d" % exact["id"])})
        try:
            flash("%s is sorted but NOT accepted: the same vendor, bill number and amount are already accepted as %s. Mark it Duplicate, or correct it."
                  % (b["stamp_no"] or ("#%d" % bid), exact["stamp_no"] or ("#%d" % exact["id"])))
        except Exception:                                            # noqa: BLE001 -- outside a request (the heal at start)
            pass
        return False
    db.execute("UPDATE bills SET status='approved', approved_by=?, approved_at=? WHERE id=?", (who, AR._now_ist(), bid))
    try:
        AR.upsert_vendor(db, b["vendor"], b["vendor_phone"], b["vendor_email"])
        for r in db.execute("SELECT id FROM assets WHERE bill_id=?", (bid,)).fetchall():
            AR._backfill_asset_from_bill(db, r["id"], bid)
    except Exception:                                                # noqa: BLE001
        pass
    AR._audit_bill(db, bid, "d710_accepted", {"by": who, "group": b["subgroup"]})
    return True


def heal(db):
    """S530 (BUILD_NORM s1): the code heals the data it governs, at every start, idempotently -- a clinic draft that
    already has its group is accepted the way a tap would accept it now. Returns (accepted, held)."""
    acc = held = 0
    try:
        rows = db.execute("SELECT b.id FROM bills b WHERE COALESCE(b.lane,'clinic')='clinic' AND b.status='draft' AND b.dup_of IS NULL "
                          "AND COALESCE(b.subgroup,'')<>'' ORDER BY b.id").fetchall()
        for r in rows:
            if _accept(db, r[0], "system \\u2014 sorted = accepted (D710)"):
                acc += 1
            else:
                held += 1
        db.commit()
    except Exception:                                                # noqa: BLE001
        pass
    return acc, held


'''
    t = t.replace(old_set, new_set)
    # ---------------------------------------------------------------- C12 month(): sections and the rows of the consumables
    t = edit(t, '''    rows = db.execute("SELECT b.* FROM bills b WHERE " + live + " AND " + MONTH_OF + "=? ORDER BY b.bill_date, b.id",
                      (ym,)).fetchall()''', '''    rows = db.execute("SELECT b.* FROM bills b WHERE " + live + " AND " + MONTH_OF + "=? ORDER BY b.bill_date, b.id",
                      (ym,)).fetchall()
    srows = db.execute("SELECT b.* FROM bills b WHERE " + _live_sections(db) + " AND b.subgroup IN ('construction','resume','misc','personal') AND "
                       + MONTH_OF + "=? ORDER BY b.bill_date, b.id", (ym,)).fetchall()        # S530: the sections, any of their lanes
    rows = [b for b in rows if (b["subgroup"] or "") not in SECTION_KEYS]                        # a sectioned paper is not a consumable
    if not AR.is_owner():
        srows = [b for b in srows if (b["subgroup"] or "") != "personal"]''', "C12a month rows")
    t = edit(t, '''    if g_ in ("procedure", "xray", "others", "unsorted"):
        a = agg((lambda s: s == "") if g_ == "unsorted" else (lambda s: GROUP_OF.get(s) == g_))''',
             '''    if g_ in SECTION_KEYS and not (g_ == "personal" and not AR.is_owner()):                   # S530: one section's papers
        sel = [b for b in srows if (b["subgroup"] or "") == g_]
        return AR.page(MONTH_TPL, ym=ym, prev=_ym_shift(ym, -1), nxt=(_ym_shift(ym, 1) if ym < today else None),
                       label=AR._month_label, inr=_inr, g=g_, rows=sel, sub=SUB, gname=SUB[g_],
                       here=AR._here(full=True), flow=AR._flow("Papers \\u2014 " + SUB[g_], url_for("bills_list")))
    if g_ in ("procedure", "xray", "others", "unsorted"):
        a = agg((lambda s: s == "") if g_ == "unsorted" else (lambda s: GROUP_OF.get(s) == g_))''', "C12b month section list")
    t = edit(t, '''    return AR.page(MONTH_TPL, ym=ym, prev=_ym_shift(ym, -1), nxt=(_ym_shift(ym, 1) if ym < today else None),
                   label=AR._month_label, inr=_inr, g="", table=table, alln=len(rows),''',
             '''    secs = []
    for k, nm, _h in SECTIONS:
        if k == "personal" and not AR.is_owner():
            continue
        sel = [b for b in srows if (b["subgroup"] or "") == k]
        if not sel:
            continue
        ven = []
        for b in sel:
            vv = (b["vendor"] or "").strip()
            if vv and vv not in ven:
                ven.append(vv)
        secs.append(dict(key=k, name=nm, n=len(sel), total=sum(b["total_amount"] or 0 for b in sel), money=(k in ("construction", "personal")),
                         vendors=", ".join(ven[:3]) + (" and %d more" % (len(ven) - 3) if len(ven) > 3 else "")))
    return AR.page(MONTH_TPL, ym=ym, prev=_ym_shift(ym, -1), nxt=(_ym_shift(ym, 1) if ym < today else None),
                   label=AR._month_label, inr=_inr, g="", table=table, alln=len(rows), secs=secs,''', "C12c month secs")
    # ---------------------------------------------------------------- C13 init(): the heal
    t = edit(t, '''    db = sqlite3.connect(ar.DB_PATH, timeout=20)
    try:
        ensure(db)
    finally:
        db.close()''', '''    db = sqlite3.connect(ar.DB_PATH, timeout=20)
    db.row_factory = sqlite3.Row
    try:
        ensure(db)
        acc, held = heal(db)                                         # S530: sorted = accepted, the backlog, idempotent
        if acc or held:
            print("clinic_papers S530 heal: %d accepted, %d held (a same-vendor-number-amount double)" % (acc, held), file=sys.stderr)
    finally:
        db.close()''', "C13 init heal")
    t = edit(t, 'import datetime\nimport re\nimport secrets\nimport sqlite3\n', 'import datetime\nimport re\nimport secrets\nimport sqlite3\nimport sys\n', "C13b import")
    assert t.count("S530") >= 12, t.count("S530")
    return t


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    live, out = sys.argv[1], sys.argv[2]
    b = open(os.path.join(live, "clinic_papers.py"), "rb").read()
    if md5(b) != FROM:
        raise SystemExit("REFUSED: clinic_papers.py is %s, not the pinned %s" % (md5(b)[:8], FROM[:8]))
    t = build(b.decode("utf-8"))
    os.makedirs(out, exist_ok=True)
    nb = t.encode("utf-8")
    open(os.path.join(out, "clinic_papers.py"), "wb").write(nb)
    print("%s  clinic_papers.py  %d bytes" % (md5(nb), len(nb)))
    print("BUILT")


if __name__ == "__main__":
    main()
