#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s532.py -- S532_AUTO_HOME (the flow proposal's K3): the system sends a scan home from the scan app's own history.

    python3 make_s532.py <live_dir> <out_dir>

Reads  <live_dir>/asset_register.py  (must be 4e924b80e8b8a8615f3bdd54726fd305, after S531)
       <live_dir>/clinic_papers.py   (must be 93d23481faacc1417a484fda529eef04, S531.1)
Writes both to <out_dir> and prints each md5. Every anchor must occur EXACTLY once or the build refuses."""
import hashlib, os, sys

FROM = {"asset_register.py": "4e924b80e8b8a8615f3bdd54726fd305", "clinic_papers.py": "93d23481faacc1417a484fda529eef04"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(t, anchor, new, name, where="replace"):
    n = t.count(anchor)
    if n != 1:
        raise SystemExit("REFUSED: anchor for %s found %d times (need 1)" % (name, n))
    return t.replace(anchor, (anchor + new) if where == "after" else (new + anchor) if where == "before" else new)


def build_app(t):
    # the one guarded call at the end of the background reading, after S441's pass
    t = edit(t, '''            if S441 is not None:                             # S441: a forgotten page joined, a sure double set aside, a question asked
                try:
                    S441.run_pass(db, only=bid, upload_dir=UPLOAD_DIR)
                except Exception:
                    pass
            return status''',
             '''            if S441 is not None:                             # S441: a forgotten page joined, a sure double set aside, a question asked
                try:
                    S441.run_pass(db, only=bid, upload_dir=UPLOAD_DIR)
                except Exception:
                    pass
            _cp = globals().get("_clinic_papers")           # S532: the system sends the scan home from its own history (fail-soft)
            if _cp is not None and hasattr(_cp, "auto_home"):
                try:
                    _cp.auto_home(db, bid)
                except Exception:
                    pass
            return status''', "H1 the hook")
    assert t.count("S532") == 1
    return t


BLOCK = '''

# ---------------------------------------------------------------------------------------------- S532: the system sends a scan home
AUTO_MIN = 2                      # earlier clinic papers of the supplier, all sorted into one group by a person, before the system decides the group
AUTO_MIN_LANE = 3                 # earlier papers of the supplier, all on the pharmacy lane, before the system sends one there
AUTO_WHO = "system \\u2014 from %d earlier paper%s of this supplier"


def _audit_marks(db, bid):
    """What the record says about a paper: did the system decide it (auto_lane / auto_group), did a person move or sort it after."""
    m = dict(auto_lane=None, auto_group=None, person_lane=None, person_group=None)
    try:
        for r in db.execute("SELECT id, who, action FROM bill_audit WHERE bill_id=? ORDER BY id", (bid,)):
            a, who = r["action"], (r["who"] or "")
            if a == "auto_lane":
                m["auto_lane"] = r["id"]
            elif a == "auto_group":
                m["auto_group"] = r["id"]
            elif a == "relane" and who:
                m["person_lane"] = r["id"]
            elif a == "subgroup" and who and not who.startswith("system"):
                m["person_group"] = r["id"]
    except sqlite3.Error:
        pass
    return m


def supplier_history(db, key, exclude_id):
    """The supplier's earlier papers that a PERSON placed: by lane, and on the clinic lane by consumable group. A paper the
    system placed counts only once a person has moved or sorted it afterwards (so the system never feeds itself)."""
    lanes, groups = {}, {}
    if not key:
        return lanes, groups
    for r in db.execute("SELECT b.id, b.vendor, b.lane, b.status, b.subgroup, b.doc_kind FROM bills b WHERE b.id<>? AND b.status<>'rejected' "
                        "AND b.dup_of IS NULL AND b.vendor IS NOT NULL AND b.vendor<>''", (exclude_id,)):
        if _supplier_key(r["vendor"]) != key or (r["doc_kind"] or "") == "challan":
            continue
        m = _audit_marks(db, r["id"])
        lane = r["lane"] or "clinic"
        if not (m["auto_lane"] and not (m["person_lane"] and m["person_lane"] > m["auto_lane"])):
            lanes[lane] = lanes.get(lane, 0) + 1
        g = r["subgroup"] or ""
        if lane == "clinic" and g in CONSUMABLE and not (m["auto_group"] and not (m["person_group"] and m["person_group"] > m["auto_group"])):
            groups[g] = groups.get(g, 0) + 1
    return lanes, groups


def auto_home(db, bid):
    """Called once, after a scan is read (asset_register._bg_extract), and by the heal at start for papers still waiting.
    Rule 1 -- the lane: this paper live (draft or captured), not a challan, not moved by a person; the supplier's earlier
    papers ALL on the pharmacy lane (three or more) -> it goes there; ALL on the clinic lane and sorted by a person into
    one group (two or more) -> it goes there and Rule 2 sorts it. Never out of, or into, the lab and Dr MK expense lanes.
    Rule 2 -- the group: on the clinic lane, a draft with no group, the supplier's earlier clinic papers, two or more, ALL
    in one consumable group -> that group, and accepted (D710). A supplier seen on two lanes or in two groups decides
    nothing; a section (construction, resume, misc, personal) is never guessed (D664). Returns what it did."""
    did = []
    b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if not b or b["status"] not in ("draft", "captured") or b["dup_of"] or (b["doc_kind"] if "doc_kind" in b.keys() else None) == "challan":
        return did
    if "page_of" in b.keys() and b["page_of"]:
        return did
    key = _supplier_key(b["vendor"])
    if not key:
        return did
    marks = _audit_marks(db, bid)
    lanes, groups = supplier_history(db, key, bid)
    lane = b["lane"] or "clinic"
    # Rule 1 moves a paper INTO the pharmacy lane (three or more earlier papers, all there) or INTO the clinic lane (all
    # there, and sorted by a person into one group, two or more); never out of the lab or Dr MK expense lanes (the
    # owner's and NK Pathology's own), never into them, never into Other document -- a scanner's default lane is weak
    # evidence, a person's sorting is strong.
    if not marks["person_lane"] and not marks["auto_lane"] and len(lanes) == 1 and lane not in ("lab_purchase", "owner_expense"):
        to, n = next(iter(lanes.items()))
        strong = (to == "pharmacy" and n >= AUTO_MIN_LANE) or (to == "clinic" and len(groups) == 1 and next(iter(groups.values())) >= AUTO_MIN)
        if strong and to != lane and to in AR.LANES:
            kind, status = AR._lane_kind_status(to)
            db.execute("UPDATE bills SET lane=?, kind=?, status=? WHERE id=?", (to, kind, status, bid))
            AR._audit_bill(db, bid, "auto_lane", {"from": lane, "to": to, "evidence": n, "status": status})
            db.commit()
            did.append("lane:%s" % to)
            lane = to
            b = db.execute("SELECT b.* FROM bills b WHERE b.id=?", (bid,)).fetchone()
    if len(lanes) > 1:                                               # a supplier of two lanes (Yuvika): the supplier alone never decides
        return did
    if lane == "clinic" and b["status"] == "draft" and not (b["subgroup"] or "") and not marks["auto_group"] and not marks["person_group"] and len(groups) == 1:
        g, n = next(iter(groups.items()))
        if n >= AUTO_MIN and g in CONSUMABLE:
            db.execute("UPDATE bills SET subgroup=? WHERE id=?", (g, bid))
            AR._audit_bill(db, bid, "auto_group", {"to": g, "evidence": n})
            who = AUTO_WHO % (n, "" if n == 1 else "s")
            acc = _accept(db, bid, who)
            db.commit()
            did.append("group:%s%s" % (g, ",accepted" if acc else ""))
    return did


def auto_note(db, bid):
    """For the paper page: 'Sorted by the system from N earlier papers -- change if wrong', or ''."""
    try:
        r = db.execute("SELECT detail FROM bill_audit WHERE bill_id=? AND action IN ('auto_group','auto_lane') ORDER BY id DESC LIMIT 1", (bid,)).fetchone()
        if not r:
            return ""
        import json as _json
        d = _json.loads(r["detail"] or "{}")
        return "Placed by the system from %d earlier paper%s of this supplier \\u2014 change it here if wrong." % (int(d.get("evidence", 0)), "" if int(d.get("evidence", 0)) == 1 else "s")
    except Exception:                                                # noqa: BLE001
        return ""


def heal_auto(db):
    """At start, idempotently: every live paper still waiting (read by the OCR, no group) gets the same one look."""
    n = 0
    try:
        ids = [r[0] for r in db.execute("SELECT b.id FROM bills b WHERE b.status IN ('draft','captured') AND b.dup_of IS NULL "
                                        "AND COALESCE(b.ocr_status,'')='read' AND COALESCE(b.subgroup,'')='' AND COALESCE(b.doc_kind,'bill')<>'challan' ORDER BY b.id").fetchall()]
        for i in ids:
            if auto_home(db, i):
                n += 1
    except Exception:                                                # noqa: BLE001
        pass
    return n
'''


def build_papers(t):
    t = edit(t, '\n\ndef init(ar):', BLOCK + '\n\ndef init(ar):', "C1 block")
    t = edit(t, '''        acc, held = heal(db)                                         # S530: sorted = accepted, the backlog, idempotent
        if acc or held:
            print("clinic_papers S530 heal: %d accepted, %d held (a same-vendor-number-amount double)" % (acc, held), file=sys.stderr)''',
             '''        acc, held = heal(db)                                         # S530: sorted = accepted, the backlog, idempotent
        if acc or held:
            print("clinic_papers S530 heal: %d accepted, %d held (a same-vendor-number-amount double)" % (acc, held), file=sys.stderr)
        na = heal_auto(db)                                           # S532: the waiting papers get the system's one look
        if na:
            print("clinic_papers S532 auto-home: %d paper(s) placed from the supplier's history" % na, file=sys.stderr)''', "C2 heal at init")
    t = edit(t, '''                   challan_html=challan_card(db, b, _back()),                                           # S531''',
             '''                   challan_html=challan_card(db, b, _back()),                                           # S531
                   auto_note=auto_note(db, bid),                                                            # S532''', "C3 paper ctx")
    t = edit(t, '''{% if p.s and p.s.kind!='sub' %}<div class="d6say other">{% if p.s.kind=='lane' %}Looks like <b>{{p.s.label}}</b>, not a clinic consumable — from {{p.s.why}}.{% else %}{{p.s.why[0]|upper}}{{p.s.why[1:]}}.{% endif %}</div>{% endif %}''',
             '''{% if auto_note %}<div class=d6say>{{auto_note}}</div>{% endif %}
{% if p.s and p.s.kind!='sub' %}<div class="d6say other">{% if p.s.kind=='lane' %}Looks like <b>{{p.s.label}}</b>, not a clinic consumable — from {{p.s.why}}.{% else %}{{p.s.why[0]|upper}}{{p.s.why[1:]}}.{% endif %}</div>{% endif %}''', "C4 paper tpl")
    t = edit(t, 'VERSION = "S531.1"', 'VERSION = "S532.1"', "C5 version")
    assert t.count("S532") >= 5, t.count("S532")
    return t


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    live, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    srcs = {}
    for name, want in FROM.items():
        b = open(os.path.join(live, name), "rb").read()
        if md5(b) != want:
            raise SystemExit("REFUSED: %s is %s, not the pinned %s" % (name, md5(b)[:8], want[:8]))
        srcs[name] = b.decode("utf-8")
    outs = {"asset_register.py": build_app(srcs["asset_register.py"]), "clinic_papers.py": build_papers(srcs["clinic_papers.py"])}
    for name, text in outs.items():
        nb = text.encode("utf-8")
        open(os.path.join(out, name), "wb").write(nb)
        print("%s  %s  %d bytes" % (md5(nb), name, len(nb)))
    print("BUILT")


if __name__ == "__main__":
    main()
