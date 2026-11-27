#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s972.py -- S972_EVENING_WIDENED (the parent, S539, 27-Nov-2026; D1099, D1100; K1 of S537_MORNING_CHECK_FINAL_BUILD_PLAN).
Remakes /root/finance/evening_check.py's TO from its live bytes (FROM b3c5bebb): every anchor must occur exactly once, or nothing
is written.     python3 make_s972.py <live evening_check.py> <out_dir>
No patient name, number or clinic ID in this file (F-185)."""
import hashlib
import os
import sys

FROM_MD5 = "b3c5bebb"

EDITS = []


def edit(old, new):
    EDITS.append((old, new))


# 1 -- the docstring: what S972 adds
edit('''"""evening_check.py -- kit S960_EVENING_CHECK (session S527, 26-Nov-2026; D1080, the Morning Match kit A). PARENT. NEW.
''', '''"""evening_check.py -- kit S960_EVENING_CHECK (session S527, 26-Nov-2026; D1080, the Morning Match kit A). PARENT. NEW.
S972_EVENING_WIDENED (session S539, 27-Nov-2026; D1099, D1100 -- K1 of S537_MORNING_CHECK_FINAL_BUILD_PLAN): the evening also
compares the MONEY of each patient's X-ray / procedure slip lines with the same export (X-ray = Laboratory + Radiology, net =
amount - discount, as revenue.py), for patients who have a slip today, and names four Docterz shapes on the same push and the
same desk box -- the owner's words 14:31 27-Nov: "only same-day Docterz edits should be there":
    chhoot   Docterz billed the full rate, the slip carries a chhoot      -> "Docterz mein chhoot lagaiye"
    kam      the slip carries more than Docterz (not a repeated line)    -> "Docterz bill mein jodiye" (or, when Docterz holds a
             chhoot the slip does not, "chhoot sahi hai to parchi par bhi, nahi to Docterz mein hataiye")
    tdoc     Docterz billed one slip line twice                            -> "dono taraf hua tha?"  [Haan, parchi theek karo]
             (writes the slip's second line -- offered only for a line with no chhoot) / Nahi: Docterz se ek hataiye
    tslip    the slip carries a line twice, Docterz once (day_check's pdup) -> "dono taraf hua tha?"  [Nahi, parchi se ek hataiye]
             (removes exactly the repeat -- not when a chhoot waits on it) / Haan: Docterz mein doosra jodiye
    more     Docterz has more than the slip (or a kind the slip lacks)     -> "kaunsa sahi?" (Docterz, or Shavez's parchi)
A line clears by itself when the next export (or the slip) agrees -- every line is worked out afresh from the stored export and
the slips as they stand. Payment mode is NOT compared (D1099). A patient with a radd today, a pair already answered on his
"Slips not in Docterz" list (nid_mark), and a kind the export lacks altogether (the S960 missing line) are left out.
EVCHK_SHAPES=0 turns the four shapes off (the S960 check as it was). The table gains one additive column, shapes (keys, no names).
''')

# 2 -- the version
edit('VERSION = "S960 1"\n', 'VERSION = "S972 1"\n')

# 3 -- the table: one additive column (created on first use, as before)
edit('''def ensure(con):
    con.executescript(DDL)
    con.commit()
''', '''def ensure(con):
    con.executescript(DDL)
    try:                                                  # S972: one additive column, the shape keys of the export's lines
        cols = [r[1] for r in con.execute("PRAGMA table_info(evening_check_push)")]
        if "shapes" not in cols:
            con.execute("ALTER TABLE evening_check_push ADD COLUMN shapes TEXT NOT NULL DEFAULT ''")
    except sqlite3.Error:
        pass
    con.commit()
''')

# 4 -- the switch
edit('''def is_on():
    return cfg("EVCHK_ON", "1").lower() not in ("0", "off", "no", "false")
''', '''def is_on():
    return cfg("EVCHK_ON", "1").lower() not in ("0", "off", "no", "false")


def shapes_on():
    """S972: the four money shapes (EVCHK_SHAPES=0 -> the S960 check as it was)."""
    return cfg("EVCHK_SHAPES", "1").lower() not in ("0", "off", "no", "false")
''')

# 5 -- the money reader, beside read_export
edit('''def current_export(con, day):
''', '''def read_amounts(raw, day):
    """S972: {clinic_id: {'xray'|'proc': [net_p, gross_p, disc_p]}} -- the money of `day`'s rows, read as revenue.py reads it
    (X-ray = Laboratory + Radiology; net = amount - discount, never below 0 per row), in paise. The same rows read_export
    counts (a UID-shaped row of the day). None if not readable."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError:
            return None
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return None
    if not rows:
        return None
    idx = {h.strip(): i for i, h in enumerate(rows[0])}
    if "Consultation Date" not in idx or "Clinic Specific Id" not in idx:
        return None

    def get(r, k):
        i = idx.get(k)
        return r[i] if i is not None and len(r) > i else ""

    cols = (("xray", (("Laboratory Amount", "Laboratory Discount"), ("Radiology Amount", "Radiology Discount"))),
            ("proc", (("Procedure Amount", "Procedure Discount"),)))
    out = {}
    for r in rows[1:]:
        d = _parse_date(get(r, "Consultation Date"))
        if d is None or d.isoformat() != day:
            continue
        c = _cid(get(r, "Clinic Specific Id"))
        if not c or not UID_OK.fullmatch(str(get(r, "Patient UID") or "").strip()):
            continue
        for kind, pairs in cols:
            g = int(round(sum(_num(get(r, a)) for a, _b in pairs) * 100))
            dd = int(round(sum(_num(get(r, b)) for _a, b in pairs) * 100))
            if g <= 0 and dd <= 0:
                continue
            v = out.setdefault(c, {}).setdefault(kind, [0, 0, 0])
            v[0] += max(0, g - dd)
            v[1] += g
            v[2] += dd
    return out


def current_export(con, day):
''')

# 6 -- the four shapes, after missing_slips
edit('''def check(con, day, export=None):
''', '''SHAPES = ("chhoot", "kam", "tdoc", "tslip", "more", "head")


def _word(it):
    return ("%s %s" % (it.get("name") or "", it.get("side") or "")).strip()


def _twice(its, extra):
    """day_check._duplicate's rule: (slip, [items]) when lines written twice on the slip come to exactly `extra`."""
    seen, rep = set(), []
    for s, it in its:
        k = ((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower())
        if k in seen:
            rep.append((s, it))
        seen.add(k)
    if not rep or extra <= 0:
        return None
    for s, it in rep:
        if it["expect_p"] == extra:
            return s, [it]
    if sum(it["expect_p"] for _s, it in rep) == extra:
        return rep[0][0], [it for _s, it in rep]
    return None


def shape_lines(con, day, carried, amounts):
    """S972: the day's money shapes, patient by patient and kind by kind, for patients with a slip of the day:
    [{key, shape, cid, name, kind, p, d, gross, disc, extra, slip_id, slip_no, items (ids), what, can}] -- `can` says whether
    the one slip-side write is offered (tdoc: the line has no chhoot and no adjustment; tslip: no adjustment on the repeat).
    The slip's money is day_check's: rate - chhoot, a REJECTED chhoot puts the full rate back (the newest entry not replaced)."""
    if not _has(con, "slip"):
        return []
    slips = [dict(r) for r in con.execute("SELECT * FROM slip WHERE state='ok' AND day=? ORDER BY series, slip_no", (day,))]
    slips = [s for s in slips if not s.get("no_id_name") and re.fullmatch(r"\\d{1,12}", str(s.get("clinic_id") or "").strip())]
    if not slips:
        return []
    radd, marks, adj, its = set(), set(), {}, {}
    if _has(con, "slip_adjust"):
        radd = {r[0] for r in con.execute("SELECT slip_id FROM slip_adjust WHERE kind='cancel' AND state IN ('pending','approved')")}
    if _has(con, "nid_mark"):
        marks = {(r[0], r[1]) for r in con.execute("SELECT slip_id, kind FROM nid_mark WHERE state='live' AND day=?", (day,))}
    ids = [s["id"] for s in slips if s["series"] == "xp"]
    if ids and _has(con, "slip_item"):
        for it in con.execute("SELECT * FROM slip_item WHERE slip_id IN (%s) ORDER BY slip_id, sort, id" % ",".join("?" * len(ids)), ids):
            its.setdefault(it["slip_id"], []).append(dict(it))
        iids = [it["id"] for v in its.values() for it in v]
        if iids and _has(con, "slip_adjust"):
            for a in con.execute("SELECT * FROM slip_adjust WHERE item_id IN (%s) AND state<>'replaced' ORDER BY id"
                                 % ",".join("?" * len(iids)), iids):
                adj[a["item_id"]] = dict(a)
    by = {}
    for s in slips:
        c = str(s["clinic_id"]).strip()
        b = by.setdefault(c, dict(slips=[], radd=False, name=""))
        b["slips"].append(s)
        b["radd"] = b["radd"] or s["id"] in radd
        b["name"] = b["name"] or (s.get("name_seen") or "").strip()
    out = []
    for c in sorted(by, key=lambda x: (len(x), x)):
        b = by[c]
        if b["radd"]:                                     # a radd today: the morning matches its refund (S962)
            continue
        have = carried.get(c, set())
        money = amounts.get(c, {})
        lines_of = {}
        for kind in ("xray", "proc"):
            mine = []
            for s in b["slips"]:
                for it in its.get(s["id"], []):
                    if it["kind"] != kind:
                        continue
                    a = adj.get(it["id"])
                    disc = 0 if (a and a.get("state") == "rejected") else int(it.get("discount_p") or 0)
                    it = dict(it, expect_p=max(0, int(it.get("price_p") or 0) - disc), adjusted=a is not None)
                    mine.append((s, it))
            lines_of[kind] = mine
        if not any((s["id"], k) in marks for s in b["slips"] for k in ("xray", "proc")):
            pk = {k: sum(it["expect_p"] for _s, it in lines_of[k]) for k in ("xray", "proc")}
            dk = {k: (money.get(k, [0, 0, 0])[0] if k in have else 0) for k in ("xray", "proc")}
            reps = [((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower()) for k in ("xray", "proc") for _s, it in lines_of[k]]
            if sum(pk.values()) == sum(dk.values()) > 0 and pk != dk and len(reps) == len(set(reps)):   # re-look: not with a repeat
                # second look MUST: the money agrees, the head does not (an X-ray billed as a procedure, or the other way) --
                # ONE line, no tap; the per-kind lines would ask for a wrong edit or a phantom slip line
                s0 = (lines_of["xray"] or lines_of["proc"])[0][0] if (lines_of["xray"] or lines_of["proc"]) else b["slips"][0]
                out.append(dict(cid=c, name=b["name"], kind="both", shape="head", p=sum(pk.values()), d=sum(dk.values()), gross=0, disc=0,
                                extra=0, px=pk["xray"], pp=pk["proc"], dx=dk["xray"], dp=dk["proc"], slip_id=s0["id"], slip_no=s0["slip_no"],
                                series=s0["series"], items=[], what="", can=False, key="ev:head:%s:both" % c))
                continue
        for kind in ("xray", "proc"):
            if any((s["id"], kind) in marks for s in b["slips"]):
                continue                                  # already answered on his list
            mine = lines_of[kind]
            in_doc = kind in have
            if not in_doc:
                continue                                  # the S960 missing line (or nothing at all on either side)
            d, gross, ddisc = money.get(kind, [0, 0, 0])
            p = sum(it["expect_p"] for _s, it in mine)
            pg = sum(int(it.get("price_p") or 0) for _s, it in mine)
            if p == d or (not mine and d <= 0):
                continue
            s0 = mine[0][0] if mine else b["slips"][0]
            ln = dict(cid=c, name=b["name"], kind=kind, p=p, d=d, gross=gross, disc=ddisc, slip_id=s0["id"],
                      slip_no=s0["slip_no"], series=s0["series"], items=[], what=", ".join(_word(it) for _s, it in mine)[:120], can=False)
            if p > d:
                tw = _twice(mine, p - d)
                if tw is not None:
                    ln.update(shape="tslip", extra=p - d, slip_id=tw[0]["id"], slip_no=tw[0]["slip_no"],
                              items=[it["id"] for it in tw[1]], what=" + ".join(_word(it) for it in tw[1])[:120],
                              can=not any(it["adjusted"] for it in tw[1]) and all(it["slip_id"] == tw[0]["id"] for it in tw[1]))
                else:
                    ln.update(shape="kam", extra=p - d)
            elif mine and pg - p > 0 and d == pg:
                ln.update(shape="chhoot", extra=pg - p)
            else:
                once = []
                if mine:
                    cnt = {}
                    for _s, it in mine:
                        k = ((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower())
                        cnt[k] = cnt.get(k, 0) + 1
                    once = [(s, it) for s, it in mine if it["expect_p"] == d - p and it["expect_p"] > 0
                            and cnt[((it.get("name") or "").strip().lower(), (it.get("side") or "").strip().lower())] == 1]
                if len(once) == 1:                      # cold review M1: two lines at the same price -> which one is unknown
                    s1, it1 = once[0]
                    ln.update(shape="tdoc", extra=d - p, slip_id=s1["id"], slip_no=s1["slip_no"], items=[it1["id"]], what=_word(it1)[:120],
                              can=(int(it1.get("discount_p") or 0) == 0 and not it1["adjusted"]
                                   and (it1.get("side") or "").strip().upper() in ("R", "L")))   # second look 3: the copy is the other side
                else:
                    ln.update(shape="more", extra=d - p)
            ln["key"] = "ev:%s:%s:%s" % (ln["shape"], c, kind)
            out.append(ln)
    for r in out:
        if not r["name"]:
            r["name"] = _name_of(con, r["cid"])
    return out


def _sk(kind, eng=False):
    return {"xray": "X-ray", "proc": "Procedure", "both": "X-ray/Procedure"}.get(kind, kind)


def shape_text(ln, eng=False):
    """One line's words: (the sentence, the instruction beside its button). No number but the money."""
    nm, k = ln["name"] or ("ID " + ln["cid"]), _sk(ln["kind"], eng)
    w = (" (%s)" % ln["what"]) if ln["what"] else ""
    P, Dz, X = _rs(ln["p"]), _rs(ln["d"]), _rs(ln["extra"])
    sh = ln["shape"]
    if sh == "head":
        return ((("%s: slip X-ray %s + Procedure %s, Docterz X-ray %s + Procedure %s — the total agrees, the head does not: "
                  "move it to the right head in Docterz" if eng else
                  "%s: parchi X-ray %s + Procedure %s, Docterz X-ray %s + Procedure %s — jod barabar, head galat: "
                  "Docterz mein sahi head mein daaliye") % (nm, _rs(ln["px"]), _rs(ln["pp"]), _rs(ln["dx"]), _rs(ln["dp"]))), "")
    if sh == "chhoot":
        return ((("%s: %s%s slip %s (discount %s), Docterz %s — apply the discount %s in Docterz" if eng else
                  "%s: %s%s parchi %s (chhoot %s), Docterz %s — Docterz mein chhoot %s lagaiye") % (nm, k, w, P, X, Dz, X)), "")
    if sh == "kam":
        if ln["disc"] > 0 and ln["gross"] >= ln["p"]:
            return ((("%s: %s%s slip %s, Docterz has a discount %s (%s) — if the discount is right, have it written on the slip too; "
                      "if not, remove it in Docterz" if eng else
                      "%s: %s%s parchi %s, Docterz mein chhoot %s (%s) — chhoot sahi hai to parchi par bhi likhwayein, "
                      "nahi to Docterz mein hataiye") % (nm, k, w, P, _rs(ln["disc"]), Dz)), "")
        return ((("%s: %s%s slip %s, Docterz %s — add %s to the Docterz bill" if eng else
                  "%s: %s%s parchi %s, Docterz %s — Docterz bill mein %s jodiye") % (nm, k, w, P, Dz, X)), "")
    if sh == "tdoc":
        if ln["can"]:
            return ((("%s: %s %s — twice in Docterz (%s), once on the slip (%s). Was the other side (R and L) done too?" if eng else
                      "%s: %s %s — Docterz mein do baar (%s), parchi par ek (%s). Doosri taraf (R aur L dono) bhi hua tha?") % (nm, k, ln["what"], Dz, P)),
                    ("No: remove one in Docterz, then export again." if eng else "Nahi: Docterz se ek hataiye, phir dobara export."))
        return ((("%s: %s %s — Docterz has %s more (%s), the slip one (%s). Done twice, or another view?" if eng else
                  "%s: %s %s — Docterz mein %s zyada (%s), parchi par ek (%s). Do baar / doosra view hua tha?") % (nm, k, ln["what"], X, Dz, P)),
                ("Yes: Shavez writes it on the slip. No: remove it in Docterz, then export again." if eng else
                 "Haan: Shavez parchi par likhein. Nahi: Docterz se hataiye, phir dobara export."))
    if sh == "tslip":
        return ((("%s: %s %s — twice on the slip (%s), once in Docterz (%s). Were both sides done?" if eng else
                  "%s: %s %s — parchi par do baar (%s), Docterz mein ek (%s). Dono taraf hua tha?") % (nm, k, ln["what"], P, Dz)),
                ("Yes: add the second in Docterz, then export again." if eng else "Haan: Docterz mein doosra jodiye, phir dobara export."))
    if ln["p"] <= 0:
        return ((("%s: Docterz %s %s, no %s on the slip — which is right?" if eng else
                  "%s: Docterz %s %s, parchi par %s nahi — kaunsa sahi?") % (nm, k, Dz, k)),
                ("Docterz wrong: correct it and export again. Slip wrong: Shavez writes the slip." if eng else
                 "Docterz galat: theek karke dobara export. Parchi galat: Shavez parchi likhein."))
    return ((("%s: %s%s Docterz %s, slip %s — which is right?" if eng else "%s: %s%s Docterz %s, parchi %s — kaunsa sahi?") % (nm, k, w, Dz, P)),
            ("Docterz wrong: correct it and export again. Slip wrong: Shavez corrects the slip." if eng else
             "Docterz galat: theek karke dobara export. Parchi galat: Shavez parchi theek karein."))


def _short(ln):
    """The push's few words for one line (Hindi; staff)."""
    k = _sk(ln["kind"])
    return {"chhoot": "%s chhoot %s lagaiye" % (k, _rs(ln["extra"])), "kam": "%s %s jodiye" % (k, _rs(ln["extra"])),
            "tdoc": "%s do baar — dono taraf?" % k, "tslip": "%s parchi par do baar — dono taraf?" % k,
            "more": "%s kaunsa sahi?" % k, "head": "head galat (jod barabar)"}.get(ln["shape"], k)


def check(con, day, export=None):
''')

# 7 -- check(): the shapes beside the rows
edit('''    out = dict(day=day, export_id=e["id"], export_at=t.strftime("%H:%M") if t else "", taken_at=str(e.get("taken_at") or "")[11:16],
               road="direct" if str(e.get("drive_id") or "").startswith("reception:") else "drive", err="", rows=[])
''', '''    out = dict(day=day, export_id=e["id"], export_at=t.strftime("%H:%M") if t else "", taken_at=str(e.get("taken_at") or "")[11:16],
               road="direct" if str(e.get("drive_id") or "").startswith("reception:") else "drive", err="", rows=[], shapes=[])
''')
edit('''    out["rows"] = missing_slips(con, day, carried)
    return out
''', '''    out["rows"] = missing_slips(con, day, carried)
    if shapes_on():                                       # S972: the four money shapes on the same export
        amounts = read_amounts(raw, day)
        out["shapes"] = shape_lines(con, day, carried, amounts or {}) if amounts is not None else []
        out["rows"], out["shapes"] = merge_lines(out["rows"], out["shapes"])
    return out


def merge_lines(rows, shapes):
    """One fault, one line (cold review 7, second look 1): a patient named 'head' leaves the missing list for X-ray / procedure;
    a 'more' with nothing on the slip for a patient on the missing list is not named twice; a patient still on the missing list
    gets no slip-side tap (its money is not settled yet)."""
    head = {x["cid"] for x in shapes if x["shape"] == "head"}
    rows = [r for r in rows if not (r["cid"] in head and r["kind"] in ("xray", "proc"))]
    miss = {r["cid"] for r in rows}
    shapes = [x for x in shapes if not (x["shape"] == "more" and x["p"] <= 0 and x["cid"] in miss)]
    for x in shapes:
        if x["cid"] in miss:
            x["can"] = False
    return rows, shapes
''')

# 8 -- the push: one per export, the shapes on it
edit('''    rows = chk["rows"]
    t_at = chk["export_at"] or at.strftime("%H:%M")
    title = body = ""
    if rows:
        outcome = "missing"
        title = "%d parchi Docterz mein nahi" % len(rows)
        body = "%s — abhi Docterz mein daalein, phir dobara export" % _names(rows)
    elif prev is None:
        outcome = "clean"
        title = "✓ %s: sab parchi Docterz mein" % dm(day)
        body = "Kuch nahi karna — PC band kar sakte hain" if at.time() >= closing(day) else "Kuch nahi karna"
    elif prev == "missing":
        outcome = "cleared"
        title = "✓ Sab parchi Docterz mein"
        body = ("Dobara export %s — kaam poora, PC band kar sakte hain" if at.time() >= closing(day) else "Dobara export %s — kaam poora") % t_at
    else:
        outcome = "quiet"
''', '''    rows = chk["rows"]
    shp = chk.get("shapes") or []                         # S972
    t_at = chk["export_at"] or at.strftime("%H:%M")
    title = body = ""
    if rows or shp:
        outcome = "missing"
        sl = " · ".join("%s: %s" % (x["name"] or ("ID " + x["cid"]), _short(x)) for x in shp[:4]) + ((" +%d" % (len(shp) - 4)) if len(shp) > 4 else "")
        if rows and not shp:
            title = "%d parchi Docterz mein nahi" % len(rows)
            body = "%s — abhi Docterz mein daalein, phir dobara export" % _names(rows)
        elif shp and not rows:
            title = "%d farq — Docterz aur parchi" % len(shp)
            body = "%s — desk par dekhein, theek karke dobara export" % sl
        else:
            title = "%d parchi Docterz mein nahi · %d farq" % (len(rows), len(shp))
            body = "%s — Docterz mein daalein · farq: %s — phir dobara export" % (_names(rows), sl)
    elif prev is None:
        outcome = "clean"
        title = ("✓ %s: Docterz aur parchi sab mile" if shapes_on() else "✓ %s: sab parchi Docterz mein") % dm(day)
        body = "Kuch nahi karna — PC band kar sakte hain" if at.time() >= closing(day) else "Kuch nahi karna"
    elif prev == "missing":
        outcome = "cleared"
        title = "✓ Docterz aur parchi sab mile" if shapes_on() else "✓ Sab parchi Docterz mein"
        body = ("Dobara export %s — kaam poora, PC band kar sakte hain" if at.time() >= closing(day) else "Dobara export %s — kaam poora") % t_at
    else:
        outcome = "quiet"
''')
edit('''    con.execute("UPDATE evening_check_push SET outcome=?, missing=?, slips=?, sent=? WHERE export_id=?",
                (outcome, len(rows), ",".join("%d:%s" % (r["slip_id"], r["kind"]) for r in rows), sent, e["id"]))
''', '''    con.execute("UPDATE evening_check_push SET outcome=?, missing=?, slips=?, sent=?, shapes=? WHERE export_id=?",
                (outcome, len(rows), ",".join("%d:%s" % (r["slip_id"], r["kind"]) for r in rows), sent,
                 ",".join("%s:%d:%s" % (x["shape"], x["slip_id"], x["kind"]) for x in shp), e["id"]))
''')
edit('''    return "%s %d (%s)" % (outcome, len(rows), sent or "nothing to send")
''', '''    return "%s %d shapes %d (%s)" % (outcome, len(rows), len(shp), sent or "nothing to send")
''')

# 9 -- the desk box: the shapes under the missing list
edit('''    elif not chk["rows"]:
        head, color = (("✓ Every slip of today is in Docterz" if eng else "✓ Aaj ki sab parchi Docterz mein")), "#1f6b3a"
''', '''    elif not chk["rows"] and not chk.get("shapes"):
        head, color = (("✓ Every slip of today is in Docterz, the money agrees" if eng else "✓ Aaj ki sab parchi Docterz mein, paise mile")
                       if shapes_on() else ("✓ Every slip of today is in Docterz" if eng else "✓ Aaj ki sab parchi Docterz mein")), "#1f6b3a"
''')
edit('''    else:
        rows = chk["rows"]
        tot = sum(r["amount_p"] for r in rows)
        head, color = (("Slips of today not in Docterz: %d · %s" if eng else "Aaj ki parchi jo Docterz mein nahi: %d · %s")
                       % (len(rows), _rs(tot))), "#9c2a20"
''', '''    elif not chk["rows"]:
        head, color = (("Docterz and the slips differ: %d" if eng else "Docterz aur parchi mein farq: %d") % len(chk["shapes"])), "#9c2a20"
        body = _shapes_html(chk["shapes"], eng)
    else:
        rows = chk["rows"]
        tot = sum(r["amount_p"] for r in rows)
        head, color = (("Slips of today not in Docterz: %d · %s" if eng else "Aaj ki parchi jo Docterz mein nahi: %d · %s")
                       % (len(rows), _rs(tot))), "#9c2a20"
''')
edit('''        body = "".join(trs) + '<p style="margin:8px 0 0;font-size:14px;color:#3b4a55">%s</p>' % steps
''', '''        body = "".join(trs) + '<p style="margin:8px 0 0;font-size:14px;color:#3b4a55">%s</p>' % steps
        if chk.get("shapes"):                             # S972
            body += ('<div style="font-size:17px;font-weight:700;color:#9c2a20;margin-top:12px">%s</div>'
                     % E(("Docterz and the slips differ: %d" if eng else "Docterz aur parchi mein farq: %d") % len(chk["shapes"]))
                     + _shapes_html(chk["shapes"], eng))
''')
edit("""'wire();vis();document.addEventListener("DOMContentLoaded",vis);setInterval(function(){load();vis();},30000);})();</script>')""",
     """'window.s960load=load;wire();vis();document.addEventListener("DOMContentLoaded",vis);setInterval(function(){load();vis();},30000);})();</script>')""")
edit('''PANEL_JS = (''', '''def _shapes_html(shapes, eng=False):
    """S972: the money lines, each with its words and -- for tdoc / tslip -- its one slip-side tap."""
    E = _h.escape
    out = []
    for ln in shapes:
        txt, alt = shape_text(ln, eng)
        btn = ""
        if ln["shape"] == "tdoc" and ln["can"]:
            btn = ('<button type="button" class="s972a" data-key="%s" data-items="%s" data-act="addline" style="min-height:44px;padding:0 14px;border:1px solid #14456e;'
                   'border-radius:10px;background:#fff;color:#14456e;font-size:15px">%s</button>' % (E(ln["key"]), E(",".join(str(i) for i in ln["items"])),
                                                                                    "Yes, correct the slip" if eng else "Haan, parchi theek karo"))
        elif ln["shape"] == "tslip" and ln["can"]:
            btn = ('<button type="button" class="s972a" data-key="%s" data-items="%s" data-act="dropdup" style="min-height:44px;padding:0 14px;border:1px solid #14456e;'
                   'border-radius:10px;background:#fff;color:#14456e;font-size:15px">%s</button>' % (E(ln["key"]), E(",".join(str(i) for i in ln["items"])),
                                                                                    "No, remove one from the slip" if eng else "Nahi, parchi se ek hataiye"))
        out.append('<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:8px 0;border-top:1px solid #e1e7eb">'
                   '<div style="flex:1 1 320px">%s%s</div>%s</div>'
                   % (E(txt), ('<div style="font-size:14px;color:#3b4a55;margin-top:2px">%s</div>' % E(alt)) if alt else "", btn))
    steps = ("Docterz is corrected the same evening; the line clears by itself about a minute after the export agrees." if eng else
             "Docterz aaj shaam hi theek karein; export milte hi lagbhag 1 minute mein line apne aap hat jayegi.")
    return "".join(out) + '<p style="margin:8px 0 0;font-size:14px;color:#3b4a55">%s</p>' % steps


SHAPE_JS = ('<script>(function(){var A=%s;document.addEventListener("click",function(ev){var b=ev.target&&ev.target.closest?ev.target.closest(".s972a"):null;'
            'if(!b)return;b.disabled=true;fetch(A+"/answer",{method:"POST",credentials:"same-origin",headers:{"Content-Type":"application/json"},'
            'body:JSON.stringify({key:b.getAttribute("data-key"),act:b.getAttribute("data-act"),items:b.getAttribute("data-items")||""})})'
            '.then(function(r){return r.json();})'
            '.then(function(r){if(r.ok){if(window.s960load){window.s960load();}else{location.reload();}}else{b.disabled=false;var m=document.getElementById("s960m");if(m)m.textContent=r.err||"";}})'
            '.catch(function(){b.disabled=false;var m=document.getElementById("s960m");if(m)m.textContent="Nahi hua — dobara koshish karein.";});});})();</script>')


PANEL_JS = (''')
edit('''    return '<div id="s960w" data-today="%s">%s</div>%s' % (at.date().isoformat(), panel_html(con, eng, at),
                                                            PANEL_JS % (json.dumps(API), json.dumps(at.date().isoformat())))
''', '''    return '<div id="s960w" data-today="%s">%s</div>%s%s' % (at.date().isoformat(), panel_html(con, eng, at),
                                                              PANEL_JS % (json.dumps(API), json.dumps(at.date().isoformat())),
                                                              SHAPE_JS % json.dumps(API))
''')

# 10 -- the two slip-side writes
edit('''def init(app, db_getter, require_fn, audit_fn=None, unit="slips"):
''', '''def _audit_w(con, table, row_id, action, before, after, who):
    if _U["audit"]:
        try:
            _U["audit"](con, table, row_id, action, before=before, after=after, who=who)
        except Exception:                                 # noqa: BLE001 -- the audit never blocks the work
            pass


def answer(con, who, key, act, at=None, items=None):
    """S972: the slip-side answer of one money line of TODAY's evening list -- 'addline' (tdoc: both sides were done; the slip's
    second line is written, a copy of the first, no chhoot) or 'dropdup' (tslip: one side only; exactly the repeat is removed).
    Each row audited whole. Returns the words to show. `items` (the ids the box showed) must be the line's ids now (cold review 2);
    the check and the write run in ONE immediate transaction, so two taps cannot both write (cold review 3)."""
    con.commit()
    con.execute("BEGIN IMMEDIATE")
    try:
        return _answer(con, who, key, act, at, items)
    except BaseException:
        con.rollback()
        raise


def _answer(con, who, key, act, at=None, items=None):
    at = at or now_ist()
    day = at.date().isoformat()
    e = evening_export(con, day, at)
    chk = check(con, day, e) if e is not None else None
    ln = next((x for x in (chk or {}).get("shapes", []) if x["key"] == key), None)
    if ln is None:
        raise FreeError("Yeh line ab list mein nahi — page taaza hai.")
    want = {"addline": "tdoc", "dropdup": "tslip"}.get(act)
    if want is None or ln["shape"] != want or not ln["can"] or not ln["items"]:
        raise FreeError("Yeh jawab is line ke liye nahi.")
    if items is not None and sorted(str(i) for i in ln["items"]) != sorted(x for x in str(items).split(",") if x):
        raise FreeError("Parchi badal chuki — page taaza hai.")
    s = con.execute("SELECT * FROM slip WHERE id=? AND state='ok' AND day=?", (ln["slip_id"], day)).fetchone()
    if s is None:
        raise FreeError("Parchi badal chuki — page taaza hai.")
    stamp = _stamp(at)
    if act == "addline":
        it = con.execute("SELECT * FROM slip_item WHERE id=? AND slip_id=?", (ln["items"][0], s["id"])).fetchone()
        if it is None or int(it["discount_p"] or 0) != 0:
            raise FreeError("Yeh line badal chuki — page taaza hai.")
        it = dict(it)
        srt = con.execute("SELECT COALESCE(MAX(sort),0)+1 FROM slip_item WHERE slip_id=?", (s["id"],)).fetchone()[0]
        side = {"R": "L", "L": "R"}.get((it.get("side") or "").strip().upper())
        if side is None:
            raise FreeError("Is line par taraf (R/L) nahi — Shavez desk par theek karein.")
        cur = con.execute("INSERT INTO slip_item (slip_id, kind, service_id, name, side, price_p, sort, discount_p) VALUES (?,?,?,?,?,?,?,0)",
                          (s["id"], it["kind"], it.get("service_id"), it.get("name") or "", side, int(it["price_p"] or 0), srt))
        con.execute("UPDATE slip SET updated_by=?, updated_at=? WHERE id=?", (who, stamp, s["id"]))
        _audit_w(con, "slip_item", cur.lastrowid, "slip_item_added_evening_s972", None,
                 json.dumps({"slip": s["id"], "copy_of": it["id"], "side": side, "why": "the other side too (evening check)"}), who)
        con.commit()
        return "Parchi %d par doosri taraf (%s) likh di." % (int(s["slip_no"]), side)
    n = 0
    for iid in ln["items"]:
        row = con.execute("SELECT * FROM slip_item WHERE id=? AND slip_id=?", (iid, s["id"])).fetchone()
        if row is None:
            continue
        if _has(con, "slip_adjust") and con.execute("SELECT 1 FROM slip_adjust WHERE item_id=? AND state<>'replaced'", (iid,)).fetchone():
            raise FreeError("Is line par chhoot ki entry hai — Shavez desk par theek karein.")
        con.execute("DELETE FROM slip_item WHERE id=?", (iid,))
        _audit_w(con, "slip_item", iid, "slip_item_removed_duplicate_s972", json.dumps(dict(row)), None, who)
        n += 1
    if n != len(ln["items"]):
        raise FreeError("Pehle hi hat chuki — page taaza hai.")
    con.execute("UPDATE slip SET updated_by=?, updated_at=? WHERE id=?", (who, stamp, s["id"]))
    con.commit()
    return "Parchi %d se doosri line hata di." % int(s["slip_no"])


def init(app, db_getter, require_fn, audit_fn=None, unit="slips"):
''')
edit('''    app.add_url_rule(API, "s960_evening", api_evening, methods=["GET"])
    app.add_url_rule(API + "/free", "s960_evening_free", api_free, methods=["POST"])
    return True
''', '''    def api_answer():                                     # S972: the money line's one slip-side tap
        u, err = _gate()
        if err:
            return jsonify(ok=False, err="not allowed"), 403
        j = request.get_json(silent=True) or {}
        key, act = str(j.get("key") or "")[:80], str(j.get("act") or "")
        if not key.startswith("ev:") or act not in ("addline", "dropdup"):
            return jsonify(ok=False, err="Samajh nahi aaya."), 200
        try:
            msg = answer(db_getter(), str((u or {}).get("user", "") or ""), key, act, items=str(j.get("items") or "")[:200])
        except FreeError as ex:
            return jsonify(ok=False, err=str(ex)), 200
        return jsonify(ok=True, msg=msg)

    app.add_url_rule(API, "s960_evening", api_evening, methods=["GET"])
    app.add_url_rule(API + "/free", "s960_evening_free", api_free, methods=["POST"])
    app.add_url_rule(API + "/answer", "s972_evening_answer", api_answer, methods=["POST"])
    return True
''')

# 11 -- --status: the shapes counted
edit('''        print("EVENING %s %s: export %s (%s) taken %s; missing %d%s; pushes %d" % (VERSION, day, chk["export_at"], chk["road"], chk["taken_at"],
                                                                               len(chk["rows"]), (" -- " + chk["err"]) if chk["err"] else "", pushes))
''', '''        print("EVENING %s %s: export %s (%s) taken %s; missing %d; shapes %d%s; pushes %d" % (
            VERSION, day, chk["export_at"], chk["road"], chk["taken_at"], len(chk["rows"]), len(chk.get("shapes") or []),
            (" -- " + chk["err"]) if chk["err"] else "", pushes))
''')


def main():
    src, out_dir = sys.argv[1], sys.argv[2]
    raw = open(src, "rb").read()
    h = hashlib.md5(raw).hexdigest()
    if not h.startswith(FROM_MD5):
        print("REFUSED: %s is %s, not the FROM %s" % (src, h[:8], FROM_MD5))
        return 2
    text = raw.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = text.count(old)
        if n != 1:
            print("REFUSED: anchor %d occurs %d times" % (i, n))
            return 3
        text = text.replace(old, new, 1)
    os.makedirs(out_dir, exist_ok=True)
    dst = os.path.join(out_dir, "evening_check.py")
    with open(dst, "wb") as fh:
        fh.write(text.encode("utf-8"))
    print("MADE evening_check.py %s (%d edits)" % (hashlib.md5(text.encode("utf-8")).hexdigest()[:8], len(EDITS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
