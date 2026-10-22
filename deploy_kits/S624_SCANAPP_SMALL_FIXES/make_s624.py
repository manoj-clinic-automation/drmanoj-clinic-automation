#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s624.py -- S624_SCANAPP_SMALL_FIXES: rebuilds the three TO files from the pinned FROM bytes by exact, counted edits.

    python3 -B make_s624.py <FROM folder> <TO folder>

Each edit's anchor must occur exactly ONCE in its FROM file; the FROM md5 must equal the pin; the TO md5 is printed (the kit's
PIN_TO_*.txt hold the expected ones and the installer compares). Nothing else is touched.
"""
import hashlib
import os
import sys

FROM_PIN = {"batteries.py": "775471e6f7f4b8356142aafccdccfddd",
            "asset_machine.py": "7d4fdffce01a28fd7e5cc2c4f2aeeb74",
            "stationery.py": "18268ff04b37af8143be1e3395ec5854"}

EDITS = {
    # ------------------------------------------------------------------ F-977: a battery past its warranty no longer shows OK
    "batteries.py": [
        ('''        elif v["upkeep_next"] is not None and (v["upkeep_next"] - today).days <= 0:
            v["badge"] = (UPKEEP[upk][1], "amber")
        else:
            v["badge"] = ("OK", "ok")''',
         '''        elif v["upkeep_next"] is not None and (v["upkeep_next"] - today).days <= 0:
            v["badge"] = (UPKEEP[upk][1], "amber")
        elif war_dd is not None and war_dd < 0:                     # S624 (F-977): past its warranty is not "OK"
            v["badge"] = ("Out of warranty since %s" % dmy(v["till"]), "none")
        else:
            v["badge"] = ("OK", "ok")'''),
    ],
    # ------------------------------------------------------------------ F-978: link a cover's / a part's paper after it is added
    "asset_machine.py": [
        ('''             "removed": dmy(p["removed_on"]) if p["removed_on"] else "", "removed_by": p["removed_by"],
             "paper": _paper_view(db, p["bill_id"], p["bill_created_at"], owner, show_price)}''',
         '''             "removed": dmy(p["removed_on"]) if p["removed_on"] else "", "removed_by": p["removed_by"],
             "bill_id": p["bill_id"] if paper_ok(db, p["bill_id"], p["bill_created_at"]) else None,             # S624 (F-978)
             "paper": _paper_view(db, p["bill_id"], p["bill_created_at"], owner, show_price)}'''),
        ('''               "current": cur.get(c["kind"]) == c["id"], "paper": _paper_view(db, c["bill_id"], c["bill_created_at"], owner, show_price)} for c in rows]''',
         '''               "current": cur.get(c["kind"]) == c["id"], "paper": _paper_view(db, c["bill_id"], c["bill_created_at"], owner, show_price),
               "bill_id": c["bill_id"] if paper_ok(db, c["bill_id"], c["bill_created_at"]) else None} for c in rows]      # S624 (F-978)'''),
        ('''<td>{% if p.paper %}<a href="{{p.paper.href}}">{{p.paper.stamp}}</a>{% else %}<span class=muted>—</span>{% endif %}</td>''',
         '''<td>{% if p.paper %}<a href="{{p.paper.href}}">{{p.paper.stamp}}</a>{% elif can_write and not p.bill_id %}<form method=post action="{{url_for('s624_part_paper',aid=aid,pid=p.id)}}" style="display:flex;gap:4px;margin:0"><input name=paper placeholder="B-____" style="max-width:90px;margin:0"><button class="btn small">link</button></form>{% else %}<span class=muted>—</span>{% endif %}</td>'''),
        ('''<td>{% if c.paper %}<a href="{{c.paper.href}}">{{c.paper.stamp}}</a>{% else %}<span class=muted>—</span>{% endif %}</td>''',
         '''<td>{% if c.paper %}<a href="{{c.paper.href}}">{{c.paper.stamp}}</a>{% elif can_write and not c.bill_id and not c.voided %}<form method=post action="{{url_for('s624_cover_paper',aid=aid,cid=c.id)}}" style="display:flex;gap:4px;margin:0"><input name=paper placeholder="B-____" style="max-width:90px;margin:0"><button class="btn small">link</button></form>{% else %}<span class=muted>—</span>{% endif %}</td>'''),
        ('''        return "Paper linked."
    return _act(a["id"], "s557spends", go)
''',
         '''        return "Paper linked."
    return _act(a["id"], "s557spends", go)


def _row_paper(a, table, rid, what, anchor, audit_as):
    """S624 (F-978): link a paper to a part / a cover AFTER it was added -- as the spends' link box does. Refuses a voided cover, a
    row that already has its paper, and every paper paper_from_box refuses (pharmacy, a patient's, a copy, a page)."""
    def go(db):
        r = db.execute("SELECT * FROM %s WHERE id=? AND asset_id=? AND asset_created_at=?" % table, (rid, a["id"], a["created_at"])).fetchone()
        if r is None:
            raise Refused("There is no such %s on this machine." % what)
        if table == "asset_cover" and r["voided_at"]:
            raise Refused("That cover is voided — add the paper to the cover that stands.")
        if table == "asset_part" and r["removed_on"]:
            raise Refused("That part is marked removed — its paper stays as it was.")
        if paper_ok(db, r["bill_id"], r["bill_created_at"]):
            raise Refused("That %s already has its paper." % what)
        bid = paper_from_box(db, request.form.get("paper"), _owner())
        if not bid:
            raise Refused("Type the paper's number (B-____).")
        db.execute("UPDATE %s SET bill_id=?, bill_created_at=? WHERE id=?" % table, (bid, bill_fp(db, bid), rid))
        _audit(db, "machine_%s_paper" % audit_as, {"asset": a["id"], audit_as: rid, "bill": bid})
        AR._audit_bill(db, bid, "machine_link", {"asset": a["id"], "as": audit_as, audit_as: rid})
        return "Paper linked."
    return _act(a["id"], anchor, go)


def part_paper(a, pid):
    return _row_paper(a, "asset_part", pid, "part", "s557parts", "part")


def cover_paper(a, cid):
    return _row_paper(a, "asset_cover", cid, "cover", "s557covers", "cover")
'''),
        ('''    app.add_url_rule("/assets/<int:aid>/spends/<int:sid>/paper", "s557_spend_paper", lr(_writer(spend_paper)), methods=["POST"])''',
         '''    app.add_url_rule("/assets/<int:aid>/spends/<int:sid>/paper", "s557_spend_paper", lr(_writer(spend_paper)), methods=["POST"])
    app.add_url_rule("/assets/<int:aid>/parts/<int:pid>/paper", "s624_part_paper", lr(_writer(part_paper)), methods=["POST"])      # S624 (F-978)
    app.add_url_rule("/assets/<int:aid>/covers/<int:cid>/paper", "s624_cover_paper", lr(_writer(cover_paper)), methods=["POST"])   # S624 (F-978)'''),
    ],
    # ------------------------------------------------------------------ F-979: a quantity in single pieces of an item counted in packets
    "stationery.py": [
        ('''def rate_flag(line_rate, line_unit, item):''',
         '''def pack_of(unit):
    """S624 (F-979): N when a unit names a count ('packet of 100', 'box of 50'), else None."""
    m = re.search(r"\\bof\\s+(\\d+)\\b", str(unit or "").lower())
    n = int(m.group(1)) if m else 0
    return n if n > 1 else None


def pack_check(qty, line_unit, item):
    """S624 (F-979): '' -- or a plain line when an item is counted in packets of N and the line's quantity is N or a whole multiple
    of N while the line does not itself say packets: the paper may mean single pieces (B-0013: 'Token 100' = 1 packet of 100)."""
    q = _num(qty)
    if item is None or q is None:
        return ""
    n = pack_of(item["unit"])
    if not n or q < n or abs(q / n - round(q / n)) > 1e-9 or unit_key(line_unit) not in ("", "piece"):
        return ""                                                    # only a line in pieces (or with no unit) is questioned
    return ("%s: %s saved, and the list counts it in '%s' — if the paper means %s single pieces, type %s instead and Save again."
            % (item["name"], _plain(q), item["unit"], _plain(q), _plain(q / n)))


def rate_flag(line_rate, line_unit, item):'''),
        ('''    if old:
        msg += " Its earlier lines are replaced, never counted twice."
    return [msg]''',
         '''    if old:
        msg += " Its earlier lines are replaced, never counted twice."
    chk = [pack_check(t[2], t[3], items.get(t[5])) for t in new if t[5] and not t[6]]          # S624 (F-979)
    chk = [c for c in chk if c]
    if chk:
        msg += " Check: " + " ".join(chk)
    return [msg]'''),
        ('''                     "used": item_used(db, i)})''',
         '''                     "used": item_used(db, i),
                     "pack": sorted({x["stamp"] or ("#%d" % x["bill_id"]) for x in recv if x["item_id"] == i and (x["day"] or "")[:7] == ym
                                     and pack_check(x["qty"], x["unit"], it)})})                                   # S624 (F-979): this month's'''),
        ('''{% if r.over %} <span class="badge amber">issued above stock</span>{% endif %}</td>''',
         '''{% if r.over %} <span class="badge amber">issued above stock</span>{% endif %}{% if r.pack %} <span class="badge amber" id=s624pack{{r.id}} title="a line of {{r.pack|join(', ')}} may be in single pieces, not {{r.unit}}">check the quantity ({{r.pack|join(', ')}})</span>{% endif %}</td>'''),
    ],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    total = 0
    for f, edits in EDITS.items():
        raw = open(os.path.join(src, f), "rb").read()
        if md5(raw) != FROM_PIN[f]:
            raise SystemExit("REFUSED: %s is %s, not the pinned %s" % (f, md5(raw)[:8], FROM_PIN[f][:8]))
        s = raw.decode("utf-8")
        for k, (a, b) in enumerate(edits, 1):
            n = s.count(a)
            if n != 1:
                raise SystemExit("REFUSED: %s edit %d -- its anchor occurs %d times (want 1)" % (f, k, n))
            s = s.replace(a, b)
            total += 1
        data = s.encode("utf-8")
        open(os.path.join(dst, f), "wb").write(data)
        out("%s: %d counted edit(s), %s -> %s" % (f, len(edits), FROM_PIN[f][:8], md5(data)))
    out("make_s624: %d counted edits in all" % total)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
