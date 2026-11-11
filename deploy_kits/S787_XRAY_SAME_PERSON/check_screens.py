#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""check_screens.py -- kit S757_XRAY_LAB_CHECK (the parent; session 413, 09-Nov-2026). D875, F-1205, F-1206.

THE OWNER'S FINAL, 06:39 IST 09-Nov-2026, on mock-up YBLGcgEAGi18QB9PL1bRL4 (v9, four artboards -- Main, PC, Shavez, Owner):
  * STAFF CHECK KAREIN (one address, phone and PC by width): each X-ray picture parked in Drive's "X-ray check" folder with the
    PHOTO INLINE, the reason it was parked, and that day's patients from every slip and Docterz line (the day before and after
    too), the likely one on top; tap the patient + "Haan, daalein" files it through the S373 road (an 'id_fixed' answer: the next
    mailbox run files it -- the mailbox script stays the only Drive writer, D574); "Inmein nahi hai? Clinic ID likhiye",
    "Yeh X-ray nahi hai", "Baad mein". A patient with no X-ray slip and no Docterz X-ray: a warning, and once filed the picture
    is on his "X-ray taken, no X-ray slip" list.
  * SHAVEZ'S PC: X-ray photos and lab reports in ONE queue, newest first by month, chips Sab / X-ray photo / Lab report.
  * LAB REPORT, NO BLOOD SLIP (F-1206): a lab-report day with no blood slip that week. The report inline (the lab's PDF from
    record_file); "Blood parchi bana di" opens the Parchi desk with the blood slip filled and comes back (a saved blood slip
    closes the item by itself); "Seedha lab gaye the"; a likely wrong ID (no visit on the ID that week, the lab's name the
    name of ONE other visitor of the week) -> "Haan, ID ... hai" (the report moves) / "Nahi".
  * HIS CONSOLE (English): four tiles -- filed by themselves since 8-Nov, waiting for staff, X-ray taken with no X-ray slip,
    lab report came with no blood slip -- each opening its list on the same page, grouped by month, newest first, the photo or
    the report inline, the staff's buttons his too; "Wrong patient? Move" on a filed one; "Charged elsewhere" /
    "Missed -- tell Shavez" on the no-slip X-rays (the second puts the X-ray on Shavez's list until a slip is made).
  * The ways in: Shavez's Aaj ka kaam line (a 'fetch' line asking GET /finance/checks/api/mine), a strip on the Parchi desk,
    the Check karein tile as it is. All lists newest first; his pages group by month (his word, 05:53 09-Nov).
  * His FINAL mock shows September on the staff screens: these two queues carry no 01-Oct floor (the other Check karein items
    keep S495's floor exactly as before).

STRICT FILING STANDS (F-1203): nothing here files a picture or moves a record without a person's tap. A suggestion is only an
order and a tag on the list; the person picks and confirms.

WHAT IT WRITES. record_check rows only (the S340 table, same columns), and two record_file corrections a person confirms
(a lab report moved to the ID it names; a filed X-ray moved by the owner), each with a note saying who, when and from what.
Every open of a parked picture is logged in record_open with file_id 0 (no index row yet) -- the picture is named in 'who'.
Keys: xf:<drive id> (the S373 key) · ln:<day>:<id> lab report, no blood slip · nx:<day>:<id> X-ray, no X-ray slip ·
xb:<day>:<id> sent to Shavez to bill · mv:<file id> a filed X-ray moved.

WHO SEES WHAT (F-1179, "can one login read another's"): these are shared work queues -- every permitted login reads the same
list; nothing here is one staff member's own data. The X-ray queue: any login of unit 'checks' (as the old list). The lab
queue and the X-ray-to-bill items: Shavez (record_setting lab_check_logins, default 'shavez') and the doctors. A picture is
served only while it is an open parked picture; a report only while it is an open lab item; the owner's doors are the doctors'
(unit 'records'). Mounted on the records blueprint by records.attach (S757). No patient name, number or secret in this file.
"""
import datetime as dt
import json
import re
from urllib.parse import quote

from flask import Response, jsonify, request

R = None                                   # the records module (set by attach)
VERSION = "S787 1"
STAFF_DAYS = 7                              # S782 (the owner 05:15 IST 11-Nov): a parked picture older than this leaves the other
                                            # staff's Check karein; the owner and the lab logins (Shavez) keep every one
FILED_SINCE = "2026-11-08"                 # S752 went live (installed 17:08 IST 08-Nov): "filed by themselves since 8-Nov"
LAB_FROM = "2026-09-19"                    # the day blood orders began (records.CHECK_FROM)
LAB_WEEK = 7                               # "no blood slip that week": the report day and the seven days before it
LAB_LOGINS = ("shavez",)                   # who answers the lab queue besides the doctors (record_setting lab_check_logins)
SEP = " · "


def _rec():
    global R
    if R is None:
        import records                     # noqa: PLC0415 -- importing it attaches this module
        R = records
    return R


# ---------------------------------------------------------------- small helpers
def _d(day, n):
    return (dt.date.fromisoformat(day[:10]) + dt.timedelta(days=n)).isoformat()


def _ok_day(s):
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s or "")))


def _month(day):
    try:
        return dt.date.fromisoformat(day[:10]).strftime("%B %Y")
    except (ValueError, TypeError):
        return ""


def _short(day):
    try:
        return dt.date.fromisoformat(day[:10]).strftime("%d-%b")
    except (ValueError, TypeError):
        return day or ""


def _roles(u):
    return set((u or {}).get("roles") or [])


def _doctor(u):
    return "checker" in _roles(u)


def _lab_logins(con):
    v = R.setting(con, "lab_check_logins")
    got = tuple(x.strip().lower() for x in (v or "").split(",") if x.strip())
    return got or LAB_LOGINS


def _lab_ok(con, u):
    _rec()
    return _doctor(u) or R._who(u).lower() in _lab_logins(con)


def _lab_name(file_name):
    """The lab's name for the patient: the third part of 'YYYY-MM-DD · ID · NAME · Blood Report.pdf'."""
    parts = [p.strip() for p in str(file_name or "").split(SEP)]
    return parts[2] if len(parts) >= 4 else ""


def _tidy(name):
    return re.sub(r"\s+", " ", str(name or "")).strip()


# ---------------------------------------------------------------- who came, from every slip and Docterz line
def _people(con, d0, d1, cache, cid=None):
    """{clinic ID: {names, lines: [(day, text)], xdays, vdays, name}} for the days d0..d1 -- every slip (OPD, X-ray / Proc) and
    every Docterz line with a clinic ID (only that ID's, when cid is given). Read once per window per request."""
    key = (d0, d1, cid)
    if key in cache:
        return cache[key]
    out = {}
    one_id = " AND s.clinic_id=?" if cid else ""
    arg = (d0, d1) + ((cid,) if cid else ())

    def one(cid):
        return out.setdefault(cid, {"names": [], "lines": [], "xdays": set(), "vdays": set()})
    items = {}
    for it in R._rows(con, "SELECT i.slip_id, i.kind, i.name, i.side FROM slip_item i JOIN slip s ON s.id=i.slip_id "
                           "WHERE s.state='ok' AND s.clinic_id<>'' AND s.day>=? AND s.day<=?" + one_id + " ORDER BY i.sort, i.id", arg):
        items.setdefault(it["slip_id"], []).append(it)
    for s in R._rows(con, "SELECT id, day, series, clinic_id, name_seen FROM slip s WHERE state='ok' AND clinic_id<>'' "
                          "AND day>=? AND day<=?" + one_id + " ORDER BY day, id", arg):
        p = one(s["clinic_id"])
        if s["name_seen"]:
            p["names"].append(s["name_seen"])
        p["vdays"].add(s["day"])
        xr = [i for i in items.get(s["id"], []) if i["kind"] == "xray"]
        if s["series"] == "xp" and xr:
            p["xdays"].add(s["day"])
            p["lines"].append((s["day"], "X-ray parchi" + SEP + ", ".join(
                _tidy((i["name"] or "X-ray") + (" " + i["side"] if i["side"] else "")) for i in xr)))
        elif s["series"] == "xp":
            p["lines"].append((s["day"], "Proc parchi"))
        else:
            p["lines"].append((s["day"], "OPD parchi"))
    for d in R._rows(con, "SELECT business_date d, clinic_id, patient, section FROM clinic_day_line WHERE clinic_id<>'' "
                          "AND business_date>=? AND business_date<=?" + (" AND clinic_id=?" if cid else "") + " ORDER BY business_date", arg):
        p = one(d["clinic_id"])
        if d["patient"]:
            p["names"].append(d["patient"])
        p["vdays"].add(d["d"])
        if d["section"] == "xray":
            p["xdays"].add(d["d"])
            p["lines"].append((d["d"], "Docterz X-ray"))
        else:
            p["lines"].append((d["d"], "Docterz " + R.SECTION_WORD.get(d["section"], d["section"] or "")))
    ids, ref = sorted(out), {}
    for k in range(0, len(ids), 400):                    # the patient list's names, in one read per 400 IDs
        part = ids[k:k + 400]
        for r in R._rows(con, "SELECT clinic_id, name FROM patient_ref WHERE name<>'' AND clinic_id IN (%s) "
                              "ORDER BY (merged_into IS NULL OR merged_into='') ASC, id DESC" % ",".join("?" * len(part)), tuple(part)):
            ref[r["clinic_id"]] = r["name"]              # the last row wins: unmerged first, then the oldest row
    for c, p in out.items():
        if ref.get(c):
            p["names"].insert(0, ref[c])
        p["name"] = _tidy(p["names"][0]) if p["names"] else ""
    cache[key] = out
    return out


def _name_of(con, cid):
    p = R.person(con, cid) or {}
    return _tidy(p.get("name") or "")


def _xdays(con, cid, d0, d1):
    """The days d0..d1 on which this ID has an X-ray on a slip or a Docterz X-ray line."""
    got = {r["day"] for r in R._rows(con, "SELECT DISTINCT s.day FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.series='xp' "
                                          "AND s.state='ok' AND i.kind='xray' AND s.clinic_id=? AND s.day>=? AND s.day<=?", (cid, d0, d1))}
    got |= {r["d"] for r in R._rows(con, "SELECT DISTINCT business_date d FROM clinic_day_line WHERE section='xray' AND clinic_id=? "
                                         "AND business_date>=? AND business_date<=?", (cid, d0, d1))}
    return got


# ---------------------------------------------------------------- 1 · the parked X-ray pictures
DONE_ANS = ("not_xray", "id_fixed", "no_docterz")      # S787: + 'no_docterz' -- the patient is not registered in Docterz


def _parked(con, recent=False, nodz=False):
    """The open parked pictures (xray_filing state 'check', nobody's answer yet), newest first. recent=True: only those first seen
    in the last STAFF_DAYS days (the reception's list -- S782). nodz=True (S787): ALSO those marked 'not in Docterz' -- they wait
    on his page until an ID exists, and can still be given one."""
    _rec()
    R.xray_ensure(con)
    answers = R._answers(con)
    out = []
    for r in R._rows(con, "SELECT * FROM xray_filing WHERE state='check'"):
        a = answers.get("xf:" + r["src_id"])
        if a and a["answer"] in DONE_ANS and not (nodz and a["answer"] == "no_docterz"):
            continue
        r["day"] = r["day"] if _ok_day(r["day"]) else str(r["planned_at"] or "")[:10]
        if recent and r["day"] < _d(R._today(), -STAFF_DAYS):
            continue                                     # S782: older -- the owner's and Shavez's only
        out.append(r)
    out.sort(key=lambda r: (r["day"], r["file_time"] or "", r["orig_name"] or ""), reverse=True)
    return out


def _alike_rows(a, b):
    """S787: two parked pictures of the same person -- the names alike but for the usual spelling (records._s782_alike, either
    way; a child's 'BABY OF ...' never) and their days at most a week apart."""
    sa, sb = R.xray_stem(a["orig_name"] or ""), R.xray_stem(b["orig_name"] or "")
    ta, tb = R._s752_tokens(sa), R._s752_tokens(sb)
    if not ta or not tb or R._s752_child(sa) or R._s752_child(sb) or not (_ok_day(a["day"]) and _ok_day(b["day"])):
        return False
    if abs((dt.date.fromisoformat(a["day"]) - dt.date.fromisoformat(b["day"])).days) > 7:
        return False
    return R._s782_alike(ta, tb) or R._s782_alike(tb, ta)


def _groups(rows):
    """S787 (the owner 08:38 IST 11-Nov: the same patient's photos entered several times): the parked pictures in groups of one
    person each, in the order given (newest first); the first of a group is the one shown, the answer goes to all of them."""
    out = []
    for r in rows:
        g = next((g for g in out if _alike_rows(g[0], r)), None)
        if g is None:
            out.append([r])
        else:
            g.append(r)
    return out


def group_of(con, sid, nodz=False):
    """The group (list of rows) the picture sid is in, or []."""
    for g in _groups(_parked(con, nodz=nodz)):
        if any(r["src_id"] == sid for r in g):
            return g
    return []


S787_BY = {"user": "system · S787: another photo of this patient was filed that day"}


def s787_auto(con):
    """S787 (the owner 08:38 IST 11-Nov): a parked picture whose name is -- but for the usual spelling -- the name of the patient
    whose X-ray photo was FILED on the picture's day (the film's printed date when it was read, else its own day; +-1 day) is that
    patient's other photo (a second view, or the same film added again): it is given his ID as a person's answer is, and the next
    filing run files it. Only when exactly ONE such patient, nobody else who came those days has a name like it, the name carries
    no second number, and the film or the name prints no ID of another real patient. Called by records' /api/xray-plan before
    each plan. Returns how many were given."""
    _rec()
    R.ensure(con)
    cache, n = {}, 0
    for r in _parked(con):
        stem = R.xray_stem(r["orig_name"] or "")
        toks = R._s752_tokens(stem)
        if not toks or R._s752_child(stem):
            continue
        own, how = R.xray_id(r["orig_name"] or "")
        if how == "many":
            continue
        fr = R._s772_film(con, r["src_id"])
        day = fr[0][0] if fr and fr[0] else r["day"]
        if not _ok_day(day):
            continue
        d0, d1 = _d(day, -1), _d(day, 1)

        def alike(names):
            return any(R._s782_alike(toks, R._s752_tokens(nm)) for nm in names or [])
        filed = [x["clinic_id"] for x in R._rows(con, "SELECT DISTINCT clinic_id FROM record_file WHERE kind='xray' AND state='ok' "
                                                     "AND clinic_id<>'' AND day>=? AND day<=? ORDER BY clinic_id", (d0, d1))]
        hits = [c for c in filed if alike(R._s782_names(con, c, cache))]
        if len(hits) != 1:
            continue
        cid = hits[0]
        if any(c != cid and alike(p["names"]) for c, p in _people(con, d0, d1, cache).items()):
            continue                                     # someone else who came those days could be the picture's: a person decides
        ids = set(fr[1]) if fr else set()
        if how == "one" and own:
            ids.add(own)
        if any(x != cid and R._known_id(con, x) for x in ids):
            continue
        _write(con, "xf:" + r["src_id"], "xray_file", r["clinic_id"] or "", "id_fixed", cid, S787_BY)
        n += 1
    if n:
        con.commit()
    return n


def _reason(con, row, people):
    """(Hindi, English) -- why the picture was parked."""
    cid, how = R.xray_id(row["orig_name"])
    if not row.get("file_time"):
        return "Photo ka samay nahi mila — din andaaze se hai", "The picture carries no time — the day is a guess"
    if how == "none":
        return "Photo par clinic ID nahi likha", "No clinic ID on the photo"
    if how == "many":
        return "Photo ke naam mein do number hain — kaun sa clinic ID hai?", "Two numbers in the photo's name — which is the clinic ID?"
    if cid in people and row["day"] in people[cid]["xdays"]:
        return ("Photo par ID %s hai — aaj ki list mein aa gaya, agle run mein file ho jayegi" % cid,
                "ID %s is now on that day's X-ray list — the next run files it" % cid)
    return ("Photo par ID %s hai — us din ki X-ray list mein nahi" % cid,
            "ID %s is not on that day's X-ray list" % cid)


def pick_list(con, row, cache=None):
    """That day's patients for one parked picture, the likely one first. Each: id, name, src, tag, tag_en, top, nox, near, filed."""
    cache = {} if cache is None else cache
    day = row["day"]
    people = _people(con, _d(day, -1), _d(day, 1), cache)
    cid_on, how = R.xray_id(row["orig_name"])
    stem = R.xray_stem(row["orig_name"])
    ft, fs = R._s752_tokens(stem), R._s752_strict_tokens(stem)
    child = R._s752_child(stem)
    filed = {r["clinic_id"] for r in R._rows(con, "SELECT DISTINCT clinic_id FROM record_file WHERE kind='xray' AND state='ok' AND day=?", (day,))}
    near_d = {_d(day, -1): "Ek din pehle", _d(day, 1): "Ek din baad"}
    near_en = {_d(day, -1): "the day before", _d(day, 1): "the day after"}
    out = []
    for cid, p in people.items():
        toks = [R._s752_strict_tokens(n) for n in p["names"]]
        loose = [R._s752_tokens(n) for n in p["names"]]
        tag, tag_en, rank = "", "", 9
        if how == "one" and cid_on == cid:
            tag, tag_en, rank = "ID milta hai", "ID matches", 0
        elif how == "one" and R._s752_one_off(cid_on, cid):
            tag, tag_en, rank = "Ek ank alag", "One digit off", 1
        elif fs and not child and any(R._s752_name_match(fs, t) for t in toks if t):
            tag, tag_en, rank = "Naam milta hai", "Name matches", 1
        elif ft and any(R._s752_name_loose(ft, t) for t in loose if t):
            tag, tag_en, rank = "Naam thoda milta hai", "Name partly matches", 2
        same = day in p["vdays"]
        xr = any(x in p["xdays"] for x in (_d(day, -1), day, _d(day, 1)))
        if rank == 9:
            rank = (3 if day in p["xdays"] else 4) if same else (5 if xr else 6)
        lines = [t for d_, t in p["lines"] if d_ == day] or \
                ["%s: %s" % (near_d.get(d_, _short(d_)), t) for d_, t in p["lines"]]
        lines_en = [t for d_, t in p["lines"] if d_ == day] or \
                   ["%s: %s" % (near_en.get(d_, _short(d_)), t) for d_, t in p["lines"]]
        seen, src, src_en = set(), [], []
        for a, b in zip(lines, lines_en):
            if a not in seen:
                seen.add(a)
                src.append(a)
                src_en.append(b)
        if not xr and same:
            src.append("X-ray nahi likha")
            src_en.append("no X-ray written")
        out.append({"id": cid, "name": p["name"] or "—", "src": SEP.join(src[:3]), "src_en": SEP.join(src_en[:3]),
                    "tag": tag, "tag_en": tag_en, "rank": rank, "top": rank <= 2, "nox": not xr, "near": rank >= 5,
                    "filed": cid in filed})
    # S782 (the owner 05:18 IST 11-Nov): the closest names first -- X-rayed and only seen together: a name that is the picture's
    # but for the spelling (records._s782_alike) is tagged and listed with the matches; the rest by letter likeness
    # (records._s782_sp); the three best on top, everyone else folded under one button when the day is long.
    for x in out:
        x["sp"] = R._s782_sp(ft, people[x["id"]]["names"]) if ft and not child else 0.0
        if x["rank"] > 2 and ft and not child and any(R._s782_alike(ft, R._s752_tokens(n)) for n in people[x["id"]]["names"]):
            x["tag"], x["tag_en"], x["rank"] = "Naam milta-julta", "Similar name", 2
    out.sort(key=lambda x: (min(x["rank"], 3), -round(x["sp"], 2), x["rank"], x["name"].lower(), x["id"]))
    for i, x in enumerate(out):
        x["top"] = x["rank"] <= 2
        x["near"] = len(out) > 5 and i >= 3
    return out


def xray_queue(con, with_people=False, recent=False, nodz_only=False):
    """S787: one item per person (the same person's photos together, 'N photos' in the title); nodz_only=True -- the ones marked
    'not in Docterz' (his page's tile)."""
    cache = {}
    out = []
    answers = R._answers(con) if nodz_only else {}
    rows = _parked(con, recent, nodz=nodz_only)
    if nodz_only:
        rows = [r for r in rows if (answers.get("xf:" + r["src_id"]) or {}).get("answer") == "no_docterz"]
    for g in _groups(rows):
        r = g[0]
        people = _people(con, _d(r["day"], -1), _d(r["day"], 1), cache)
        hi, en = _reason(con, r, people)
        if nodz_only:
            a = answers.get("xf:" + r["src_id"]) or {}
            hi = en = "Not in Docterz \u2014 marked by %s on %s" % (a.get("answered_by") or "?", _short(str(a.get("answered_at") or "")[:10]))
        it = {"key": "xf:" + r["src_id"], "kind": "xray", "sid": r["src_id"], "day": r["day"], "dshort": _short(r["day"]),
              "month": _month(r["day"]), "time": str(r["file_time"] or "")[11:16],
              "title": (r["orig_name"] or "(no name)") + (SEP + "%d photos" % len(g) if len(g) > 1 else ""),
              "n": len(g), "copies": [x["src_id"] for x in g[1:]], "reason": hi, "reason_en": en}
        if with_people:
            it["pats"] = pick_list(con, r, cache)
        out.append(it)
    return out


# ---------------------------------------------------------------- 2 · lab report came, no blood slip (F-1206)
def lab_items(con):
    """One item per patient per report day: a lab report filed (record_file, kind blood, from the lab's mail, with its PDF) with
    no blood slip (blood_order) on that ID in the report day or the seven days before it, and nobody's answer. Newest first."""
    _rec()
    R.ensure(con)
    answers = R._answers(con)
    cache = {}
    out = []
    for r in R._rows(con, "SELECT clinic_id, day, MIN(id) fid, COUNT(*) n FROM record_file WHERE kind='blood' "
                          "AND source='lab_mail' AND state='ok' AND drive_id<>'' AND day>=? GROUP BY clinic_id, day "
                          "ORDER BY day DESC, clinic_id", (LAB_FROM,)):
        cid, day = r["clinic_id"], r["day"]
        if not _ok_day(day):
            continue
        key = "ln:%s:%s" % (day, cid)
        if key in answers:
            continue
        if R._rows(con, "SELECT 1 FROM blood_order WHERE state='ok' AND clinic_id=? AND day>=? AND day<=? LIMIT 1",
                   (cid, _d(day, -LAB_WEEK), day)):
            continue
        fn = R._rows(con, "SELECT file_name FROM record_file WHERE id=?", (r["fid"],))   # R2: the name of the very report shown
        lab = _tidy(_lab_name(fn[0]["file_name"] if fn else ""))
        mine = _people(con, _d(day, -LAB_WEEK), day, cache, cid=cid).get(cid)
        it = {"key": key, "kind": "lab", "cid": cid, "day": day, "dshort": _short(day), "month": _month(day), "fid": r["fid"],
              "n": r["n"], "lab": lab, "name": (mine or {}).get("name") or _name_of(con, cid) or lab or "—",
              "wrong": False, "sug": "", "sug_name": "", "slip_day": day}
        vd = sorted(d_ for d_ in (mine or {}).get("vdays", set()) if d_ >= _d(day, -1))
        if vd:
            last = vd[-1]
            how = [t for d_, t in mine["lines"] if d_ == last]
            word = how[0].split(SEP)[0] if how else "visit"
            if last == day:
                it["note"] = "Isi din clinic aaye (%s) — blood parchi nahi bani" % word
                it["note_en"] = "Came to the clinic the same day (%s) · no blood slip" % word
            else:
                it["note"] = "Ek din pehle clinic aaye (%s) — blood parchi nahi bani" % word
                it["note_en"] = "Came the day before (%s) · no blood slip" % word
            it["slip_day"] = last
        elif mine:
            last = sorted(mine["vdays"])[-1]
            it["note"] = "%s ko clinic aaye — blood parchi nahi bani" % _short(last)
            it["note_en"] = "Came on %s · no blood slip" % _short(last)
            it["slip_day"] = last                          # the slip goes on the day the patient was seen
        else:
            # no visit that week: the slip, if made, goes on the report day (the day the sample reached the lab).
            # A WRONG ID is offered only when the ID's own registered name is NOT the lab's name (cold review R1: a patient who went
            # straight to the lab must never be offered a move to a namesake who visited), only for a single report (R2: a move
            # carries exactly the report the person saw), and only when exactly one visitor of the week has the lab's name.
            fs = R._s752_strict_tokens(lab)
            own = [n for n in (_name_of(con, cid),) if n]
            own_match = bool(fs) and any(R._s752_name_match(fs, R._s752_strict_tokens(n)) for n in own)
            week = _people(con, _d(day, -LAB_WEEK), day, cache)
            hits = [c for c, p in week.items() if c != cid and fs and any(R._s752_name_match(fs, R._s752_strict_tokens(n)) for n in p["names"])]
            if len(hits) == 1 and not R._s752_child(lab) and not own_match and r["n"] == 1:
                s = hits[0]
                it.update(wrong=True, sug=s, sug_name=week[s]["name"] or "—")
                it["note"] = ("Is ID par koi visit nahi. Lab ka naam is hafte ke ek marij se milta hai: %s (%s) — shayad ID galat"
                              % (it["sug_name"], s))
                it["note_en"] = ("No visit on this ID that week · the lab's name matches %s (%s) — the ID is probably wrong"
                                 % (it["sug_name"], s))
            else:
                it["note"] = "Is ID par is hafte koi visit nahi — blood parchi nahi bani"
                it["note_en"] = "No visit on this ID that week · no blood slip"
        it["desk"] = "/finance/slips/desk?lab=" + quote(key, safe="")
        out.append(it)
    return out


def lab_item(con, key):
    return next((i for i in lab_items(con) if i["key"] == key), None)


def lab_slip_day(con, key, cid):
    """For the Parchi desk: the day a blood slip for this open lab item is written on (the visit day), or None."""
    it = lab_item(con, str(key or "")[:80])
    if not it or it["wrong"] or str(cid or "") != it["cid"]:
        return None
    return it["slip_day"]


# ---------------------------------------------------------------- 3 · X-ray taken, no X-ray slip
def nox_items(con):
    """A filed X-ray picture (since the live filing began) on a patient with no X-ray on any slip and no Docterz X-ray line the day
    before, that day or the day after: possibly not charged. One per patient per day. Newest first."""
    answers = R._answers(con)
    live = R.setting(con, "xray_live_from") or R.XRAY_LIVE_FROM
    files = R._rows(con, "SELECT id, clinic_id, day, file_name, source_ref FROM record_file WHERE kind='xray' AND state='ok' "
                         "AND day>=? ORDER BY day DESC, id", (live,))
    if not files:
        return []
    d0 = min(f["day"] for f in files)
    xs = {(r["clinic_id"], r["day"]) for r in R._rows(con, "SELECT DISTINCT s.clinic_id, s.day FROM slip s JOIN slip_item i ON i.slip_id=s.id "
                                                            "WHERE s.series='xp' AND s.state='ok' AND i.kind='xray' AND s.day>=?", (_d(d0, -1),))}
    xs |= {(r["clinic_id"], r["d"]) for r in R._rows(con, "SELECT DISTINCT clinic_id, business_date d FROM clinic_day_line "
                                                           "WHERE section='xray' AND business_date>=?", (_d(d0, -1),))}
    seen, out, cache = set(), [], {}
    for f in files:
        cid, day = f["clinic_id"], f["day"]
        if (cid, day) in seen or not _ok_day(day):
            continue
        seen.add((cid, day))
        if any((cid, x) in xs for x in (_d(day, -1), day, _d(day, 1))):
            continue
        key = "nx:%s:%s" % (day, cid)
        if key in answers:
            continue
        p = _people(con, _d(day, -1), _d(day, 1), cache).get(cid)
        if p and p["lines"]:
            what = "; ".join(sorted({t for d_, t in p["lines"]}))
            detail = "Photo filed on the patient · %s only · no X-ray on a slip or Docterz" % what
        else:
            detail = "Photo filed on the patient · no slip and no Docterz line that day"
        out.append({"key": key, "kind": "nox", "cid": cid, "day": day, "dshort": _short(day), "month": _month(day), "fid": f["id"],
                    "name": (p or {}).get("name") or _name_of(con, cid) or "—", "study": (f["file_name"] or "").split(SEP)[-1],
                    "detail": detail})
    return out


def xbill_items(con):
    """The no-slip X-rays the owner sent to Shavez ('Missed -- tell Shavez'), until Shavez says the slip is made, or an X-ray slip
    for that ID dated that day or later exists. Newest first."""
    answers = R._answers(con)
    out = []
    for k, a in answers.items():
        if not k.startswith("nx:") or a["answer"] != "tell_shavez":
            continue
        _, day, cid = (k.split(":", 2) + ["", ""])[:3]
        if not _ok_day(day):
            continue
        key = "xb:%s:%s" % (day, cid)
        if key in answers:
            continue
        if R._rows(con, "SELECT 1 FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.series='xp' AND s.state='ok' AND i.kind='xray' "
                        "AND s.clinic_id=? AND s.day>=? LIMIT 1", (cid, _d(day, -1))):
            continue
        f = R._rows(con, "SELECT id, file_name FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? AND day=? ORDER BY id LIMIT 1",
                    (cid, day))
        out.append({"key": key, "kind": "xbill", "cid": cid, "day": day, "dshort": _short(day), "month": _month(day),
                    "fid": f[0]["id"] if f else None, "name": _name_of(con, cid) or "—",
                    "study": ((f[0]["file_name"] or "").split(SEP)[-1]) if f else "",
                    "note": "X-ray hua (photo file hai), X-ray parchi nahi bani — Doctor sahab ne bheja (%s)" % _short(a["answered_at"]),
                    "note_en": "X-ray taken, no X-ray slip — sent by the doctor on %s" % _short(a["answered_at"])})
    out.sort(key=lambda i: (i["day"], i["cid"]), reverse=True)
    return out


# ---------------------------------------------------------------- 4 · filed by themselves since 8-Nov
def _filed_how(verdict):
    v = str(verdict or "")
    m = re.match(r"ID \S+ given by (\S+)", v)
    if m:
        return "filed by %s from Check karein" % m.group(1).capitalize()
    if v.startswith("S752 re-try: ID"):
        return "filed by itself — its ID came on the day's X-ray slip"
    if v.startswith("S752 re-try: no ID"):
        return "filed by itself — the name matched, the day over"
    return "filed by itself"


def filed_items(con):
    R.xray_ensure(con)
    out = []
    for r in R._rows(con, "SELECT x.src_id, x.orig_name, x.verdict, x.done_at, x.day, f.id fid, f.clinic_id cid, f.file_name, f.note "
                          "FROM xray_filing x JOIN record_file f ON f.id=x.file_id WHERE x.state='done' AND x.done_at>=? AND f.state='ok' "
                          "AND (x.verdict LIKE 'S752 re-try%' OR x.verdict LIKE 'ID % given by %') ORDER BY x.day DESC, x.done_at DESC",
                     (FILED_SINCE,)):
        day = r["day"] if _ok_day(r["day"]) else str(r["done_at"])[:10]
        detail = "%s · %s" % ((r["file_name"] or "").split(SEP)[-1] or "X-ray", _filed_how(r["verdict"]))
        if "moved from" in (r["note"] or ""):
            detail += " · " + r["note"].split(" | ")[-1]
        out.append({"key": "mv:%d" % r["fid"], "kind": "filed", "cid": r["cid"], "day": day, "dshort": _short(day), "month": _month(day),
                    "fid": r["fid"], "name": _name_of(con, r["cid"]) or "—", "orig": r["orig_name"] or "", "detail": detail})
    return out


def counts(con):
    """For his console's line: the four tiles' numbers."""
    _rec()
    return {"filed": len(filed_items(con)), "wait": len(_groups(_parked(con))), "nox": len(nox_items(con)), "lab": len(lab_items(con)),
            "xbill": len(xbill_items(con))}


# ---------------------------------------------------------------- the answers (staff and owner alike)
def _write(con, key, kind, cid, a, note, u):
    con.execute("INSERT INTO record_check(key, kind, clinic_id, answer, note, answered_by, answered_at) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET kind=excluded.kind, clinic_id=excluded.clinic_id, answer=excluded.answer, "
                "note=excluded.note, answered_by=excluded.answered_by, answered_at=excluded.answered_at",
                (key, kind, cid or "", a, note or "", R._who(u), R._stamp()))


def _id_ok(con, nid):
    return bool(nid and re.fullmatch(r"\d{1,8}", nid) and R._known_id(con, nid))


def answer(con, u, body, en=False):
    """{key, a, new_id, check} -> (status, dict). 'check' asks only: who is this ID, and is there an X-ray slip (nothing written)."""
    R.ensure(con)
    key = str(body.get("key") or "")[:80]
    a = str(body.get("a") or "")[:20]
    nid = R._clean_id(body.get("new_id"))
    W = (lambda hi, e: e) if en else (lambda hi, e: hi)
    done = W("Yeh pehle hi ho chuka hai.", "This was already answered.")
    if key.startswith("xf:"):
        sid = key[3:]
        g = group_of(con, sid, nodz=(a == "id_fixed"))    # S787: the same person's other photos go with it
        row = next((r for r in g if r["src_id"] == sid), None)
        if not row:
            return 409, {"ok": False, "err": done}
        many = W(" · %d photo" % len(g), " · %d photos" % len(g)) if len(g) > 1 else ""
        if a == "no_docterz":
            for x in g:
                _write(con, "xf:" + x["src_id"], "xray_file", x["clinic_id"] or "", "no_docterz", "", u)
            con.commit()
            return 200, {"ok": True, "msg": W("Theek hai: Docterz mein nahi \u2014 Doctor sahab ki list mein gayi", "Moved to 'Not in Docterz'") + many}
        if a == "id_fixed":
            if not _id_ok(con, nid):
                return 400, {"ok": False, "err": W("Yeh ID list mein nahi hai — dobara dekhein.", "That ID is not known — check it again.")}
            name = _name_of(con, nid)
            nox = not _xdays(con, nid, _d(row["day"], -1), _d(row["day"], 1))
            if body.get("check"):
                return 200, {"ok": True, "check": True, "id": nid, "name": name or "—", "nox": nox}
            for x in g:                                  # S787: every photo of the group
                _write(con, "xf:" + x["src_id"], "xray_file", x["clinic_id"] or "", "id_fixed", nid, u)
            con.commit()
            msg = W("File ho gayi: %s (ID %s)" % (name or "—", nid), "Filed: %s (%s)" % (name or "—", nid))
            if nox:
                msg += W(" · Doctor sahab ko dikhega: X-ray hua, parchi nahi", " · it will show under 'X-ray taken, no X-ray slip'")
            return 200, {"ok": True, "msg": msg + many}
        if a == "not_xray":
            _write(con, key, "xray_file", row["clinic_id"] or "", "not_xray", "", u)
            con.commit()
            return 200, {"ok": True, "msg": W("Theek hai: yeh X-ray nahi.", "Marked: not an X-ray.")}
        return 400, {"ok": False, "err": W("Jawab samajh nahi aaya.", "Unknown answer.")}
    if key.startswith(("ln:", "xb:")) and not _lab_ok(con, u):
        return 403, {"ok": False, "err": W("Yeh aapke login ke liye nahi hai.", "Not for this login.")}
    if key.startswith("ln:"):
        it = lab_item(con, key)
        if not it:
            return 409, {"ok": False, "err": done}
        if a == "direct_lab":
            _write(con, key, "lab_noslip", it["cid"], "direct_lab", "", u)
            con.commit()
            return 200, {"ok": True, "msg": W("Note: seedha lab — %s" % it["name"], "Noted, went straight to the lab: %s" % it["name"])}
        if a == "id_ok" and it["wrong"]:
            _write(con, key, "lab_noslip", it["cid"], "id_ok", "", u)
            con.commit()
            return 200, {"ok": True, "msg": W("ID %s sahi maana: %s" % (it["cid"], it["name"]), "ID %s kept: %s" % (it["cid"], it["name"]))}
        if a == "moved" and it["wrong"] and nid == it["sug"] and _id_ok(con, nid):
            note = "moved from %s to %s by %s at %s (lab report, no blood slip: the lab's name)" % (it["cid"], nid, R._who(u), R._stamp())
            n = con.execute("UPDATE record_file SET clinic_id=?, note=CASE WHEN note='' THEN ? ELSE note || ' | ' || ? END "
                            "WHERE id=? AND kind='blood' AND source='lab_mail' AND state='ok' AND clinic_id=? AND day=?",
                            (nid, note, note, it["fid"], it["cid"], it["day"])).rowcount   # R2: exactly the report shown
            if n != 1:
                con.rollback()
                return 409, {"ok": False, "err": W("Report badal gayi hai \u2014 page dobara kholiye.", "The report changed \u2014 reload the page.")}
            _write(con, key, "lab_noslip", it["cid"], "moved", "%s -> %s (%d file%s)" % (it["cid"], nid, n, "" if n == 1 else "s"), u)
            con.commit()
            return 200, {"ok": True, "msg": W("Report %s par daal di: %s" % (nid, it["sug_name"]), "Report moved to %s: %s" % (nid, it["sug_name"]))}
        return 400, {"ok": False, "err": W("Jawab samajh nahi aaya.", "Unknown answer.")}
    if key.startswith("xb:"):
        it = next((i for i in xbill_items(con) if i["key"] == key), None)
        if not it:
            return 409, {"ok": False, "err": done}
        if a == "slip_made":
            _write(con, key, "xray_bill", it["cid"], "slip_made", "", u)
            con.commit()
            return 200, {"ok": True, "msg": W("Parchi ho gayi: %s" % it["name"], "Slip made: %s" % it["name"])}
        return 400, {"ok": False, "err": W("Jawab samajh nahi aaya.", "Unknown answer.")}
    if key.startswith(("nx:", "mv:")) and not _doctor(u):
        return 403, {"ok": False, "err": W("Yeh Doctor sahab ka hai.", "For the doctors only.")}
    if key.startswith("nx:"):
        it = next((i for i in nox_items(con) if i["key"] == key), None)
        if not it:
            return 409, {"ok": False, "err": done}
        if a in ("charged_elsewhere", "tell_shavez"):
            _write(con, key, "xray_noslip", it["cid"], a, "", u)
            con.commit()
            return 200, {"ok": True, "msg": ("Marked: charged elsewhere — %s" if a == "charged_elsewhere" else "Sent to Shavez to bill: %s")
                         % ("%s · %s" % (it["name"], it["cid"]))}
        return 400, {"ok": False, "err": "Unknown answer."}
    if key.startswith("mv:"):
        try:
            fid = int(key[3:])
        except ValueError:
            return 400, {"ok": False, "err": "Bad key."}
        f = con.execute("SELECT * FROM record_file WHERE id=? AND kind='xray' AND state='ok'", (fid,)).fetchone()
        if not f:
            return 409, {"ok": False, "err": "That picture is no longer filed."}
        if not _id_ok(con, nid) or nid == f["clinic_id"]:
            return 400, {"ok": False, "err": "Type the right clinic ID (a known ID, not the same one)."}
        name = _name_of(con, nid)
        if body.get("check"):
            return 200, {"ok": True, "check": True, "id": nid, "name": name or "—"}
        note = "moved from %s to %s by %s at %s" % (f["clinic_id"], nid, R._who(u), R._stamp())
        con.execute("UPDATE record_file SET clinic_id=?, note=CASE WHEN note='' THEN ? ELSE note || ' | ' || ? END WHERE id=?",
                    (nid, note, note, fid))
        _write(con, key, "xray_move", nid, "moved", "%s -> %s" % (f["clinic_id"], nid), u)
        con.commit()
        return 200, {"ok": True, "msg": "Moved to %s (%s). The record moves; the Drive copy keeps its first name." % (name or "—", nid)}
    return 400, {"ok": False, "err": W("Jawab samajh nahi aaya.", "Unknown answer.")}


# ---------------------------------------------------------------- the doors
def _json_gate():
    u, err = R._require("maker", "checker", unit=R.CHECK_UNIT)
    if not u:
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return u, None


def _doc_gate():
    u, err = R._require("checker", unit=R.UNIT)
    if not u:
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return u, None


def _body():
    try:
        return request.get_json(force=True, silent=True) or {}
    except Exception:                                    # noqa: BLE001
        return {}


def api_mine():
    """The count of this login's Check karein photo and lab work (Aaj ka kaam's fetch line, the Parchi desk's strip)."""
    u, err = _json_gate()
    if err:
        return err
    con = R._db()
    lab = _lab_ok(con, u)
    x = len(_groups(_parked(con, recent=not lab)))     # S787: one per person               # S782: reception -- the last STAFF_DAYS days; Shavez and doctors -- all
    l = len(lab_items(con)) if lab else 0
    b = len(xbill_items(con)) if lab else 0
    en = _doctor(u)
    parts = []
    if x:
        parts.append(("%d X-ray photo%s" % (x, "" if x == 1 else "s")) if en else "X-ray photo %d" % x)
    if l:
        parts.append(("%d lab report%s with no blood slip" % (l, "" if l == 1 else "s")) if en else "Lab report %d" % l)
    if b:
        parts.append(("%d X-ray to bill" % b) if en else "X-ray parchi %d" % b)
    text = ("Check karein: " + SEP.join(parts) + ("" if en else " baaki")) if parts else ""
    return jsonify(ok=True, open=x + l + b, xray=x, lab=l, xbill=b, text=text)


def api_answer_staff():
    u, err = _json_gate()
    if err:
        return err
    code, d = answer(R._db(), u, _body(), en=False)
    return jsonify(**d), code


def api_answer_owner():
    u, err = _doc_gate()
    if err:
        return err
    code, d = answer(R._db(), u, _body(), en=True)
    return jsonify(**d), code


def _pats_for(sid):
    con = R._db()
    row = next((r for r in _parked(con, nodz=True) if r["src_id"] == sid), None)
    if not row:
        return jsonify(ok=False, err="gone"), 404
    return jsonify(ok=True, pats=pick_list(con, row))


def _mobile(con, cid):
    """The patient's mobile number as the clinic holds it (the owner: full numbers); the last four when only those are kept."""
    r = R._rows(con, "SELECT mobile, phone_last4 FROM patient_ref WHERE clinic_id=? ORDER BY (merged_into IS NULL OR merged_into='') DESC, "
                     "id LIMIT 1", (cid,))
    if not r:
        return ""
    m = re.sub(r"\D", "", str(r[0].get("mobile") or ""))
    return m[-10:] if len(m) >= 10 else ("\u2026" + r[0]["phone_last4"] if r[0].get("phone_last4") else "")


def find_people(con, q, day=""):
    """Up to 8 patients for what was typed: a clinic ID; a mobile number (10 digits); or a name -- the name's spelling variants first
    (records._s782_alike), then by likeness; those who came that day (or a day either side) ahead. Each: id, name, mobile, came."""
    q = str(q or "").strip()[:60]
    digits = re.sub(r"\D", "", q)
    found = []
    if re.fullmatch(r"\d{1,8}", q):
        found = [q] if R._known_id(con, q) else []
    elif len(digits) >= 10 and not re.search(r"[A-Za-z]", q):
        m10 = digits[-10:]
        found = [r["clinic_id"] for r in R._rows(con, "SELECT DISTINCT clinic_id, mobile FROM patient_ref WHERE phone_last4=? AND clinic_id<>''",
                                                  (m10[-4:],)) if re.sub(r"\D", "", str(r["mobile"] or ""))[-10:] == m10]
        if not found:                                    # a number the clinic keeps only as its fingerprint
            fp = R._fp_of(m10)[0]
            if fp:
                found = [r["clinic_id"] for r in R._rows(con, "SELECT DISTINCT clinic_id FROM patient_ref WHERE mobile_fp=? AND clinic_id<>''", (fp,))]
    else:
        toks = R._s752_tokens(q)
        if toks:
            near = set(_people(con, _d(day, -1), _d(day, 1), {}).keys()) if _ok_day(day) else set()
            cands = set(near)                            # everyone who came that day, whatever the spelling
            for w in toks[:3]:                           # and anyone whose name shares a word's first four letters
                like = "%" + w[:4] + "%"
                cands |= {r["c"] for r in R._rows(con, "SELECT DISTINCT clinic_id c FROM patient_ref WHERE name LIKE ? AND clinic_id<>'' LIMIT 600", (like,))}
                cands |= {r["c"] for r in R._rows(con, "SELECT DISTINCT clinic_id c FROM slip WHERE name_seen LIKE ? AND clinic_id<>'' LIMIT 300", (like,))}
                cands |= {r["c"] for r in R._rows(con, "SELECT DISTINCT clinic_id c FROM clinic_day_line WHERE patient LIKE ? AND clinic_id<>'' LIMIT 300", (like,))}
            sc = []
            for c in cands:
                names = R._s772_names(con, c)
                s = 1.0 if any(R._s782_alike(toks, R._s752_tokens(n)) for n in names) else R._s782_sp(toks, names)
                if s >= 0.5:
                    sc.append((-(s + (0.2 if c in near else 0)), c))
            found = [c for _, c in sorted(sc)]
    near = set(_people(con, _d(day, -1), _d(day, 1), {}).keys()) if _ok_day(day) else set()
    out, seen = [], set()
    for c in found:
        p = R.person(con, c) or {}
        if c in seen or p.get("merged"):
            continue
        seen.add(c)
        out.append({"id": c, "name": p.get("name") or "\u2014", "mobile": _mobile(con, c), "came": c in near})
        if len(out) >= 8:
            break
    return out


def _find_for(sid, q):
    con = R._db()
    row = next((r for r in _parked(con) if r["src_id"] == sid), None)
    if not row:                                          # only for a picture that is waiting -- never a patient directory
        return jsonify(ok=False, err="gone"), 404
    return jsonify(ok=True, pats=find_people(con, q, row.get("day") or ""))


def api_find_staff():
    u, err = _json_gate()
    if err:
        return err
    return _find_for(str(request.args.get("sid") or "")[:200], request.args.get("q") or "")


def api_find_owner():
    u, err = _doc_gate()
    if err:
        return err
    return _find_for(str(request.args.get("sid") or "")[:200], request.args.get("q") or "")


def api_pats_staff():
    u, err = _json_gate()
    if err:
        return err
    return _pats_for(str(request.args.get("sid") or "")[:200])


def api_pats_owner():
    u, err = _doc_gate()
    if err:
        return err
    return _pats_for(str(request.args.get("sid") or "")[:200])


def _photo(u, sid):
    con = R._db()
    if not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", sid or ""):
        return Response("No such picture.", status=404, mimetype="text/plain")
    row = next((r for r in _parked(con, nodz=True) if r["src_id"] == sid), None)
    if not row:
        return Response("This picture is no longer waiting.", status=404, mimetype="text/plain")
    data, why = R.drive_media(sid)
    con.execute("INSERT INTO record_open(file_id, who, at, ok) VALUES (?,?,?,?)",
                (0, "%s · parked xf:%s" % (R._who(u), sid[:40]), R._stamp(), 1 if data else 0))
    con.commit()
    if data is None:
        return Response("Drive did not give the picture: %s" % why, status=502, mimetype="text/plain")
    return Response(data, mimetype=R._MIME.get(R._xray_ext(row["orig_name"]), "image/jpeg"),
                    headers={"Cache-Control": "private, max-age=900", "X-Content-Type-Options": "nosniff",
                             "Content-Disposition": "inline"})


def photo_staff(sid):
    u, err = R._check_gate()
    if err:
        return err
    return _photo(u, sid)


def photo_owner(sid):
    u, err = R._gate()
    if err:
        return err
    return _photo(u, sid)


def report_staff(fid):
    u, err = R._check_gate()
    if err:
        return err
    con = R._db()
    if not _lab_ok(con, u):
        return Response("Not for this login.", status=403, mimetype="text/plain")
    f = con.execute("SELECT * FROM record_file WHERE id=? AND kind='blood' AND state='ok' AND drive_id<>''", (fid,)).fetchone()
    if not f or not any(i["cid"] == f["clinic_id"] and i["day"] == f["day"] for i in lab_items(con)):
        return Response("This report is no longer waiting.", status=404, mimetype="text/plain")
    data, why = R.drive_media(f["drive_id"])
    con.execute("INSERT INTO record_open(file_id, who, at, ok) VALUES (?,?,?,?)", (fid, R._who(u), R._stamp(), 1 if data else 0))
    con.commit()
    if data is None:
        return Response("Drive did not give the report: %s" % why, status=502, mimetype="text/plain")
    return Response(data, mimetype=f["mime"] or "application/pdf",
                    headers={"Content-Disposition": "inline", "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


def _boot(d):
    return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")


def staff_page(con, u, others, ok=""):
    """Check karein: the photo and lab-report screens; the other open items (blood test with no report, lab ID, no PDF,
    WhatsApp, X-ray with no file) below, exactly as the old list draws them."""
    lab = _lab_ok(con, u)
    items = xray_queue(con, recent=not lab)             # S782: older pictures -- the owner's and Shavez's only
    if lab:
        items += lab_items(con) + xbill_items(con)
    items.sort(key=lambda i: (i["day"], i.get("time") or "", i["key"]), reverse=True)
    old = "".join(R._old_item_html(i) for i in others)
    boot = {"items": items, "lab": lab, "ok": ok, "others": len(others), "me": R._who(u), "doctor": _doctor(u)}
    fill = {"__BOOT__": _boot(boot), "__OTHERS__": old or '<div class="okb">Aur koi sawaal nahi.</div>'}
    html = re.sub(r"__BOOT__|__OTHERS__", lambda m: fill[m.group(0)], STAFF_PAGE)   # R9: one pass
    return Response(html, mimetype="text/html")


def owner_page():
    u, err = R._gate()
    if err:
        return err
    con = R._db()
    R.ensure(con)
    data = {"filed": filed_items(con), "wait": xray_queue(con), "nox": nox_items(con), "lab": lab_items(con),
            "nodz": xray_queue(con, nodz_only=True),                                     # S787
            "xbill": len(xbill_items(con)), "since": _short(FILED_SINCE)}
    tab = request.args.get("tab") or ("wait" if data["wait"] else "lab")
    html = OWNER_PAGE.replace("__BOOT__", _boot(dict(data, tab=tab if tab in ("filed", "wait", "nox", "lab", "nodz") else "wait")))
    return Response(html, mimetype="text/html")


def attach(rec):
    """Called once by records.py at import, before its blueprint is registered: the doors above go on records' blueprint."""
    global R
    R = rec
    bp, CP, P = rec.bp, rec.CP, rec.P
    bp.add_url_rule(CP + "/api/mine", "s757_mine", api_mine)
    bp.add_url_rule(CP + "/api/answer", "s757_answer", api_answer_staff, methods=["POST"])
    bp.add_url_rule(CP + "/api/pats", "s757_pats", api_pats_staff)
    bp.add_url_rule(CP + "/api/find", "s782_find", api_find_staff)              # S782: ID / name / mobile
    bp.add_url_rule(P + "/xray-check/api/find", "s782_owner_find", api_find_owner)
    bp.add_url_rule(CP + "/photo/<sid>", "s757_photo", photo_staff)
    bp.add_url_rule(CP + "/report/<int:fid>", "s757_report", report_staff)
    bp.add_url_rule(P + "/xray-check", "s757_owner", owner_page)
    bp.add_url_rule(P + "/xray-check/api/pats", "s757_owner_pats", api_pats_owner)
    bp.add_url_rule(P + "/xray-check/api/answer", "s757_owner_answer", api_answer_owner, methods=["POST"])
    bp.add_url_rule(P + "/xray-check/photo/<sid>", "s757_owner_photo", photo_owner)
    rec.ANS_EN.update({"direct_lab": "went straight to the lab", "moved": "moved", "charged_elsewhere": "charged elsewhere",
                       "tell_shavez": "sent to Shavez to bill", "slip_made": "slip made"})


# ================================================================ the pages
STAFF_PAGE = r"""<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5"><meta name="robots" content="noindex,nofollow">
<title>Check karein</title><style>
:root{--g:#0F5E57;--gd:#0A4540;--gl:#E6F4F1;--gt:#F0FAF8;--gb:#7CC4B8;--ink:#17202A;--mut:#4B5563;--mu2:#6B7280;--line:#E5E8EC;
 --l2:#DDE2E7;--bg:#F6F7F9;--or:#9A3412;--orb:#FFF4E5;--nx:#7C2D12;--nxb:#FFEDD5;--bl:#1D4ED8;--blb:#EEF2FF;--blt:#1E3A8A;--ok:#14532D;--okb:#E6F4EA;--dk:#0B0F14}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.4 Inter,"Segoe UI",system-ui,-apple-system,sans-serif}
button{font-family:inherit;cursor:pointer}a{color:var(--g)}
.hd{background:var(--g);color:#fff;padding:12px 16px;display:flex;flex-direction:column;gap:10px}
.hd .r1{display:flex;align-items:center;justify-content:space-between;gap:12px}
.hd .bk{color:#fff;text-decoration:none;border:2px solid rgba(255,255,255,.7);border-radius:8px;padding:6px 10px;font-weight:600;font-size:14px;white-space:nowrap}
.hd .t{display:flex;flex-direction:column;gap:2px;flex:1;min-width:0}.hd .t small{font-size:13px;opacity:.85}.hd .t b{font-size:19px}
.badge{background:#fff;color:var(--g);font-weight:700;font-size:15px;padding:6px 12px;border-radius:999px;white-space:nowrap}
.chips{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.chip{min-height:36px;padding:0 14px;display:inline-flex;align-items:center;border-radius:999px;font-size:14px;border:0;background:rgba(255,255,255,.18);color:#fff}
.chip.on{background:#fff;color:var(--g);font-weight:700}.chips .hint{font-size:13px;opacity:.85}
.done{margin:12px 16px 0;background:var(--okb);color:var(--ok);border-radius:10px;padding:12px 14px;font-size:15px;font-weight:600}
.err{margin:12px 16px 0;background:#FADBD8;color:#7f1d1d;border-radius:10px;padding:12px 14px;font-size:15px;font-weight:600}
.card{margin:12px 16px 0;background:#fff;border-radius:14px;box-shadow:0 1px 3px rgba(16,24,40,.1);overflow:hidden;display:flex;flex-direction:column}
.ch{padding:12px 14px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);font-size:14px;color:var(--mut)}
.ch b{color:var(--ink)}
.ph{background:var(--dk);height:240px;display:flex;align-items:center;justify-content:center;position:relative}
.ph.big{height:420px}.ph img{max-width:100%;max-height:100%;object-fit:contain;display:block}
.ph .fn{position:absolute;left:10px;bottom:8px;color:#C9D3DD;font-size:12px;max-width:60%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ph .bb{position:absolute;right:10px;bottom:8px;background:rgba(255,255,255,.16);color:#fff;border:0;border-radius:8px;padding:8px 12px;font-size:13px;min-height:36px}
.ph .ld{color:#C9D3DD;font-size:13px}
.why{font-size:14px;color:var(--or);background:var(--orb);border-radius:8px;padding:8px 10px;margin:12px 14px 0}
.ask{font-size:15px;font-weight:600;padding:10px 14px 4px}
.pl{padding:4px 10px 10px;display:flex;flex-direction:column;gap:8px}
.pr{width:100%;display:flex;justify-content:space-between;align-items:center;gap:10px;min-height:60px;padding:10px 12px;border-radius:10px;background:#fff;border:1px solid var(--l2);text-align:left}
.pr.top{background:var(--gt);border:1px solid var(--gb)}.pr.sel{background:var(--gl);border:2px solid var(--g)}
.pr .nm{font-size:16px;font-weight:600;color:var(--ink);display:block}.pr .sr{font-size:13px;color:var(--mut);display:block;margin-top:2px}
.tag{font-size:12px;font-weight:600;padding:4px 8px;border-radius:999px;white-space:nowrap;background:var(--g);color:#fff}.tag.nx{background:var(--nxb);color:var(--nx)}
.more{margin:0 10px 10px;min-height:42px;background:#fff;border:1px dashed #C7CDD4;border-radius:10px;color:var(--mut);font-size:14px}
.cf{margin:0 10px 12px;border:2px solid var(--g);border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:10px;background:var(--gt)}
.cf .qq{font-size:16px;font-weight:600}.cf .w{font-size:14px;color:var(--nx);background:var(--nxb);border-radius:8px;padding:8px 10px}
.row2{display:flex;gap:10px}.row2>*{flex:1}
.b1{min-height:48px;background:var(--g);color:#fff;border:0;border-radius:10px;font-size:16px;font-weight:700}
.b2{min-height:48px;background:#fff;color:var(--ink);border:1px solid #C7CDD4;border-radius:10px;font-size:16px}
.b3{min-height:44px;background:#fff;color:var(--or);border:1px solid #F3C9A3;border-radius:10px;font-size:15px}
.bb1{min-height:48px;background:var(--bl);color:#fff;border:0;border-radius:10px;font-size:15px;font-weight:700}
.ft{border-top:1px solid var(--line);padding:12px 14px;display:flex;flex-direction:column;gap:10px}
@media (max-width:420px){.row2 .bb1,.row2 .b2,.row2 .b1,.row2 .b3{font-size:14px;padding:0 6px}}
.ft label{font-size:14px;color:var(--mut)}.ft input{flex:1;min-height:44px;border:1px solid #C7CDD4;border-radius:10px;padding:0 12px;font-size:16px;min-width:0}
.ft .go{min-height:44px;padding:0 14px;background:var(--g);color:#fff;border:0;border-radius:10px;font-size:15px;font-weight:600;flex:0 0 auto}
.note{font-size:13px;border-radius:8px;padding:8px 10px;background:var(--blb);color:var(--blt)}.note.w{background:var(--orb);color:var(--or)}
.lc{background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(16,24,40,.1);padding:12px 14px;display:flex;flex-direction:column;gap:8px;margin:0 16px 10px}
.lc .h{display:flex;justify-content:space-between;align-items:baseline;gap:8px}.lc .h b{font-size:16px}.lc .h span{font-size:13px;color:var(--mut)}
.lc .s{font-size:13px;color:var(--mut)}.see{min-height:40px;background:#fff;color:var(--bl);border:1px solid #BFCCF5;border-radius:10px;font-size:14px;font-weight:600}
.rep{width:100%;height:70vh;border:1px solid var(--l2);border-radius:10px;background:#fff}
.mh{padding:12px 18px 4px;font-size:12px;font-weight:700;color:var(--mu2);text-transform:uppercase;letter-spacing:.05em}
.empty{margin:16px;background:var(--okb);color:var(--ok);border-radius:10px;padding:14px;font-size:16px;font-weight:600}
.foot{margin:14px 16px 24px;font-size:13px;color:var(--mu2);line-height:1.5}
/* the old list's forms (Aur sawaal) */
.oldw{padding:8px 16px 24px}
form.ck{background:#fff;border:2px solid #9fb0bb;border-radius:10px;padding:10px 12px;margin:0 0 10px}
.ckh{font-size:15px}.age{color:#9c2a20;font-weight:700}.ckb{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.ckb button{min-height:48px;padding:0 14px;border:2px solid #14456e;background:#fff;color:#14456e;border-radius:9px;font-size:16px;font-weight:600}
.ckb input{min-height:48px;font-size:17px;padding:0 10px;border:2px solid #6b7b86;border-radius:9px;width:150px}
.pks{display:flex;flex-direction:column;gap:6px;margin-top:8px}.pk{font-size:16px;display:flex;gap:8px;align-items:center;min-height:40px}
.pk input{width:22px;height:22px}.sm{font-size:13px;color:#46525b}.okb{background:#dff0d8;border-left:6px solid #2c6e2f;padding:10px 12px;margin:0 0 10px;border-radius:6px}
a.view{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:9px;background:#14456e;color:#fff;text-decoration:none;font-weight:600}
/* PC */
.pc{display:flex;gap:16px;padding:16px 24px;height:calc(100vh - 64px);min-height:560px}
.pc .q{width:310px;flex-shrink:0;background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(16,24,40,.1);overflow:auto}
.pc .q .qh{padding:10px 14px;font-size:13px;color:var(--mut);border-bottom:1px solid var(--line)}
.pc .q .mh{padding:10px 14px 6px;background:var(--bg);border-bottom:1px solid var(--line)}
.qi{width:100%;display:flex;gap:10px;align-items:center;padding:10px 14px;border:0;border-bottom:1px solid #F0F2F4;background:#fff;text-align:left}
.qi.on{background:var(--gl);box-shadow:inset 4px 0 0 var(--g)}
.qi .ic{width:40px;height:40px;border-radius:8px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;background:var(--dk);color:#C9D3DD}
.qi .ic.b{background:#DBEAFE;color:var(--bl)}.qi .tx{display:flex;flex-direction:column;gap:2px;min-width:0}
.qi .tx b{font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.qi .tx span{font-size:12px;color:var(--mut)}
.pc .mid{flex:1;min-width:0;border-radius:12px;display:flex;flex-direction:column;position:relative;overflow:hidden}
.pc .mid.x{background:var(--dk);align-items:center;justify-content:center}.pc .mid.x img{max-width:100%;max-height:100%;object-fit:contain}
.pc .mid.l{background:#E9ECF0;padding:12px}.pc .mid.l iframe{flex:1;width:100%;border:0;border-radius:6px;background:#fff}
.pc .mid .cap{position:absolute;left:0;right:0;top:0;padding:10px 16px;background:rgba(0,0,0,.6);display:flex;flex-direction:column;gap:4px}.pc .mid .cap b{color:#fff;font-size:16px}.pc .mid .cap span{color:#C9D3DD;font-size:13px}
.pc .mid .rs{position:absolute;left:16px;bottom:14px;right:16px;color:#FDE7D2;background:rgba(154,52,18,.45);border-radius:8px;padding:8px 12px;font-size:14px}
.pc .side{width:400px;flex-shrink:0;background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(16,24,40,.1);overflow:auto;display:flex;flex-direction:column}
.pc .oldpc{flex:1;overflow:auto;background:#fff;border-radius:12px;padding:16px}
</style></head><body>
<header class="hd"><div class="r1"><a class="bk" href="/portal">&larr; Portal</a><div class="t"><small>Check karein</small><b id="ttl">X-ray photo &mdash; kiski hai?</b></div><span class="badge" id="left"></span></div>
<div class="chips" id="chips"></div></header>
<div id="msg"></div><main id="app"></main>
<template id="oldt"><div class="oldw"><p class="sm">Baaki sawaal &mdash; pehle jaise (blood report, lab ID, WhatsApp, X-ray file nahi aayi). <a href="/finance/checks/add">+ Kagaz jodein</a></p>__OTHERS__</div></template>
<script>
(function(){
var B=__BOOT__, IT=B.items, F='all', CUR=null, PICK=-1, BIG=false, MSG=B.ok||'', ERR='', PATS={}, LATER=[], CF=null, OPEN={}, FOUND={}, FQ={};
function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function wide(){return window.innerWidth>=1000;}
function isX(i){return i.kind==='xray'||i.kind==='xbill';}
function live(){var a=IT.filter(function(i){return F==='all'||(F==='xray'?isX(i):F==='lab'?i.kind==='lab':(F.indexOf('mon:')===0?isX(i)&&i.dshort.slice(3)===F.slice(4):false));});
 a.sort(function(p,q){var lp=LATER.indexOf(p.key),lq=LATER.indexOf(q.key);if(lp!==lq)return lp-lq;return 0;});return a;}
function nX(){return IT.filter(isX).length;} function nL(){return IT.filter(function(i){return i.kind==='lab';}).length;}
function post(body){return fetch('/finance/checks/api/answer',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(r){return r.json();}).catch(function(){return {ok:false,err:'Internet / server nahi mila — dobara dabayein.'};});}
function gone(key,m){IT=IT.filter(function(i){return i.key!==key;});MSG=m||'';ERR='';PICK=-1;CF=null;BIG=false;CUR=null;draw();}
function loadPats(it,cb){if(PATS[it.sid]){cb();return;}fetch('/finance/checks/api/pats?sid='+encodeURIComponent(it.sid),{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.json();}).then(function(d){PATS[it.sid]=d.ok?d.pats:[];cb();}).catch(function(){PATS[it.sid]=[];cb();});}
function chips(){var h='';
 if(B.lab){[['all','Sab',IT.length],['xray','X-ray photo',nX()],['lab','Lab report',nL()]].forEach(function(c){h+='<button class="chip'+(F===c[0]?' on':'')+'" data-f="'+c[0]+'">'+c[1]+' · '+c[2]+'</button>';});}
 else{var ms={};IT.forEach(function(i){ms[i.dshort.slice(3)]=(ms[i.dshort.slice(3)]||0)+1;});var mk=Object.keys(ms);if(mk.length>1)h+='<button class="chip'+(F==='all'?' on':'')+'" data-f="all">Sab '+IT.length+'</button>';mk.forEach(function(m){h+='<button class="chip'+((F==='mon:'+m||mk.length===1&&F==='all')?' on':'')+'" data-f="mon:'+esc(m)+'">'+esc(m)+' '+ms[m]+'</button>';});if(IT.length)h+='<span class="hint">· naya pehle</span>';}
 if(B.others)h+='<button class="chip'+(F==='old'?' on':'')+'" data-f="old">Aur sawaal · '+B.others+'</button>';
 $('chips').innerHTML=h;[].forEach.call($('chips').querySelectorAll('button[data-f]'),function(b){b.onclick=function(){F=b.getAttribute('data-f');CUR=null;PICK=-1;CF=null;draw();};});
 $('left').textContent=(B.lab?IT.length:nX())+' baaki';
 $('ttl').innerHTML=B.lab?'X-ray photo aur lab report &mdash; ek jagah':'X-ray photo &mdash; kiski hai?';}
function msgs(){$('msg').innerHTML=(MSG?'<div class="done">'+esc(MSG)+'</div>':'')+(ERR?'<div class="err">'+esc(ERR)+'</div>':'');}
function oldHtml(){return $('oldt').innerHTML;}
// ---- one X-ray picture: the picker and the confirm (shared by phone and PC)
function pickerHtml(it){var ps=PATS[it.sid];if(!ps)return '<div class="pl"><span class="sm">Marij la rahe hain…</span></div>';
 var main=ps.filter(function(p){return !p.near;}),near=ps.filter(function(p){return p.near;}),h='<div class="pl">';
 function row(p,k){var tg=p.tag?'<span class="tag">'+esc(p.tag)+'</span>':(p.nox?'<span class="tag nx">X-ray parchi nahi</span>':'');
  return '<button class="pr'+(PICK===k?' sel':(p.top?' top':''))+'" data-k="'+k+'"><span><span class="nm">'+esc(p.name)+'</span><span class="sr">ID '+esc(p.id)+' · '+esc(p.src)+(p.filed?' · photo pehle se':'')+'</span></span>'+tg+'</button>';}
 main.forEach(function(p){h+=row(p,ps.indexOf(p));});
 if(!main.length)h+='<span class="sm">Us din ki koi parchi / Docterz line nahi mili.</span>';
 if(near.length){h+=OPEN[it.key]?near.map(function(p){return row(p,ps.indexOf(p));}).join(''):'<button class="more" data-more="1">Baaki marij ('+near.length+')</button>';}
 return h+'</div>';}
function confirmHtml(){if(!CF)return '';
 return '<div class="cf"><span class="qq">Yeh photo <b>'+esc(CF.name)+'</b> (ID '+esc(CF.id)+') ke record mein daalein?</span>'+(CF.nox?'<span class="w">Is marij ki X-ray parchi nahi bani hai. Photo file ho jayegi, aur Doctor sahab ko dikhega: “X-ray hua, parchi nahi”.</span>':'')+
 '<div class="row2"><button class="b1" id="yes">Haan, daalein'+(wide()?' (Enter)':'')+'</button><button class="b2" id="no">Nahi</button></div></div>';}
function foundHtml(it){var fs=FOUND[it.key];if(!fs)return '';if(!fs.length)return '<span class="sm">Is naam / number ka koi marij nahi mila.</span>';
 return fs.map(function(p,k){return '<button class="pr" data-f="'+k+'"><span><span class="nm">'+esc(p.name)+'</span><span class="sr">ID '+esc(p.id)+(p.mobile?' · '+esc(p.mobile):'')+'</span></span>'+(p.came?'<span class="tag">Us din aaye the</span>':'')+'</button>';}).join('');}
function footHtml(it){return '<div class="ft"><label for="cid">Inmein nahi hai? Clinic ID, naam ya mobile likhiye</label><div class="row2" style="gap:8px"><input id="cid" placeholder="Clinic ID / naam / mobile" autocomplete="off" value="'+esc(FQ[it.key]||'')+'"><button class="go" id="cidgo">Dhoondhein</button></div>'+foundHtml(it)+
 '<div class="row2" style="gap:8px"><button class="b3" id="notx">Yeh X-ray nahi hai</button><button class="b3" id="nodz">Docterz mein nahi</button><button class="b2" id="later" style="min-height:44px;font-size:15px">Baad mein</button></div></div>';}
function wireX(it,root){
 [].forEach.call(root.querySelectorAll('.pr'),function(b){b.onclick=function(){var p=PATS[it.sid][+b.getAttribute('data-k')];PICK=+b.getAttribute('data-k');CF={id:p.id,name:p.name,nox:p.nox};MSG='';ERR='';draw();var y=$('yes');if(y)y.scrollIntoView({block:'nearest'});};});
 var m=root.querySelector('[data-more]');if(m)m.onclick=function(){OPEN[it.key]=1;draw();};
 var y=$('yes');if(y)y.onclick=function(){y.disabled=true;post({key:it.key,a:'id_fixed',new_id:CF.id}).then(function(r){if(r.ok)gone(it.key,r.msg);else{ERR=r.err;y.disabled=false;msgs();}});};
 var n=$('no');if(n)n.onclick=function(){PICK=-1;CF=null;draw();};
 var cg=$('cidgo');if(cg)cg.onclick=function(){var v=($('cid').value||'').trim();if(!v){$('cid').focus();return;}
  FQ[it.key]=v;if(!/^\d{1,8}$/.test(v)){fetch('/finance/checks/api/find?sid='+encodeURIComponent(it.sid)+'&q='+encodeURIComponent(v),{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.ok?r.json():{ok:false};}).then(function(d){if(d.ok){FOUND[it.key]=d.pats;ERR='';draw();}else{ERR='Dhoondh nahi paaye — page dobara kholiye';msgs();}}).catch(function(){ERR='Internet / server nahi mila — dobara dabaiye';msgs();});return;}
  post({key:it.key,a:'id_fixed',new_id:v,check:1}).then(function(r){if(r.ok){PICK=-1;CF={id:r.id,name:r.name,nox:r.nox};MSG='';ERR='';draw();}else{ERR=r.err;msgs();}});};
 [].forEach.call(root.querySelectorAll('[data-f]'),function(b){b.onclick=function(){var p=FOUND[it.key][+b.getAttribute('data-f')];post({key:it.key,a:'id_fixed',new_id:p.id,check:1}).then(function(r){if(r.ok){PICK=-1;CF={id:r.id,name:r.name,nox:r.nox};MSG='';ERR='';draw();var y=$('yes');if(y)y.scrollIntoView({block:'nearest'});}else{ERR=r.err;msgs();}});};});
 var ci=$('cid');if(ci)ci.onkeydown=function(e){if(e.key==='Enter'){e.preventDefault();cg.click();}};
 var nx=$('notx');if(nx)nx.onclick=function(){post({key:it.key,a:'not_xray'}).then(function(r){if(r.ok)gone(it.key,r.msg);else{ERR=r.err;msgs();}});};
 var nd=$('nodz');if(nd)nd.onclick=function(){nd.disabled=true;post({key:it.key,a:'no_docterz'}).then(function(r){if(r.ok)gone(it.key,r.msg);else{ERR=r.err;nd.disabled=false;msgs();}});};
 var lt=$('later');if(lt)lt.onclick=function(){LATER=LATER.filter(function(k){return k!==it.key;});LATER.push(it.key);MSG='';CUR=null;PICK=-1;CF=null;var a=live();CUR=a.length?a[0].key:null;draw();};
 var bb=root.querySelector('.bb');if(bb)bb.onclick=function(){BIG=!BIG;draw();};}
// ---- a lab report and an X-ray to bill: the buttons
function labActs(it){if(it.kind==='xbill')return '<div class="row2"><button class="bb1" data-a="slip_made">Parchi bana di</button><a class="b2" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="/finance/slips/desk">Parchi desk kholiye</a></div>';
 if(it.wrong)return '<span style="font-size:15px;font-weight:600">Kya yeh report ID '+esc(it.sug)+' ki hai?</span><div class="row2"><button class="bb1" data-a="moved">Haan, ID '+esc(it.sug)+' hai</button><button class="b2" data-a="id_ok">Nahi, '+esc(it.cid)+' sahi hai</button></div>';
 return '<span style="font-size:15px;font-weight:600">Blood parchi nahi bani. Ab bana di?</span><div class="row2"><a class="bb1" style="display:flex;align-items:center;justify-content:center;text-decoration:none" href="'+esc(it.desk)+'">Blood parchi bana di</a><button class="b2" data-a="direct_lab">Seedha lab gaye the</button></div>';}
function wireL(it,root){[].forEach.call(root.querySelectorAll('[data-a]'),function(b){b.onclick=function(){b.disabled=true;var a=b.getAttribute('data-a');
 post({key:it.key,a:a,new_id:a==='moved'?it.sug:''}).then(function(r){if(r.ok)gone(it.key,r.msg);else{ERR=r.err;b.disabled=false;msgs();}});};});}
// ---- PHONE
function drawPhone(){var a=live(),h='';
 if(F==='old'){$('app').innerHTML=oldHtml();return;}
 if(!a.length){$('app').innerHTML='<div class="empty">Sab ho gaya — kuch dekhna baaki nahi.</div>'+(B.others&&F!=='old'?'<div class="foot">Aur sawaal upar “Aur sawaal” mein.</div>':'');return;}
 var xs=a.filter(function(i){return i.kind==='xray';}),rest=a.filter(function(i){return i.kind!=='xray';});
 if(xs.length&&F!=='lab'){if(!CUR||!xs.some(function(i){return i.key===CUR;}))CUR=xs[0].key;var it=xs.filter(function(i){return i.key===CUR;})[0];
  h+='<div class="card"><div class="ch"><span>Photo '+(xs.indexOf(it)+1)+' / '+xs.length+' · <b>'+esc(it.dshort)+'</b></span><span>'+esc(it.time)+'</span></div>'+
   '<div class="ph'+(BIG?' big':'')+'"><img src="/finance/checks/photo/'+encodeURIComponent(it.sid)+'" alt="X-ray photo" onerror="this.outerHTML=\'<span class=ld>Photo Drive se nahi aayi — baad mein dekhein</span>\'"><span class="fn">'+esc(it.title)+'</span><button class="bb">'+(BIG?'Chhota':'Bada dekhein')+'</button></div>'+
   '<span class="why">'+esc(it.reason)+'</span><span class="ask">'+esc(it.dshort)+' ke marij — sahi naam dabaiye</span>'+pickerHtml(it)+confirmHtml()+footHtml(it)+'</div>';
  if(F!=='xray'&&!rest.length)h+='<div class="foot">Har photo ke saath us din ke sab marij: X-ray parchi, Docterz X-ray, aur OPD parchi wale bhi. Jo naam ya ID milta hai, woh sabse upar.</div>';}
 if(rest.length){var last='';h+='<div style="height:8px"></div>';
  rest.forEach(function(it){if(it.month!==last){h+='<div class="mh">'+esc(it.month)+'</div>';last=it.month;}
   h+='<div class="lc" data-key="'+esc(it.key)+'"><div class="h"><b>'+esc(it.name)+'</b><span>'+esc(it.dshort)+'</span></div><span class="s">ID '+esc(it.cid)+' · '+(it.kind==='lab'?'Lab report'+(it.lab&&it.lab.toLowerCase()!==String(it.name).toLowerCase()?' ('+esc(it.lab)+')':''):'X-ray'+(it.study?' · '+esc(it.study):''))+'</span>'+
   '<span class="note'+(it.wrong||it.kind==='xbill'?' w':'')+'">'+esc(it.note)+'</span>'+
   (it.kind==='lab'?'<button class="see" data-see="1">'+(OPEN[it.key]?'Report band karein':'Report dekhein')+'</button>'+(OPEN[it.key]?'<iframe class="rep" src="/finance/checks/report/'+it.fid+'"></iframe><a href="/finance/checks/report/'+it.fid+'" target="_blank" rel="noopener" class="s">Pura kholiye ↗</a>':''):'')+labActs(it)+'</div>';});}
 $('app').innerHTML=h;
 var c=$('app').querySelector('.card');if(c)wireX(xs.filter(function(i){return i.key===CUR;})[0],c);
 [].forEach.call($('app').querySelectorAll('.lc'),function(el){var it=IT.filter(function(i){return i.key===el.getAttribute('data-key');})[0];wireL(it,el);
  var s=el.querySelector('[data-see]');if(s)s.onclick=function(){OPEN[it.key]=!OPEN[it.key];draw();};});
 if(c){var it2=xs.filter(function(i){return i.key===CUR;})[0];if(!PATS[it2.sid])loadPats(it2,draw);var nx=xs[xs.indexOf(it2)+1];if(nx)loadPats(nx,function(){});}}
// ---- PC
function drawPC(){var a=live();
 if(F==='old'){$('app').innerHTML='<div class="pc"><div class="oldpc">'+oldHtml()+'</div></div>';return;}
 if(!a.length){$('app').innerHTML='<div class="empty">Sab ho gaya — kuch dekhna baaki nahi.</div>';return;}
 if(!CUR||!a.some(function(i){return i.key===CUR;}))CUR=a[0].key;var it=a.filter(function(i){return i.key===CUR;})[0];
 var q='<div class="q"><div class="qh">Naya pehle · mahine ke hisaab se</div>',last='';
 a.forEach(function(i){if(i.month!==last){q+='<div class="mh">'+esc(i.month)+'</div>';last=i.month;}
  var t=i.kind==='xray'?i.title:(i.name+' · '+i.cid),s=i.kind==='xray'?'X-ray · '+(i.reason.indexOf('ID nahi')>=0?'naam, ID nahi':'ID list mein nahi'):(i.kind==='xbill'?'X-ray · parchi banani hai':'Blood · '+(i.wrong?'ID galat?':'parchi nahi'));
  q+='<button class="qi'+(i.key===CUR?' on':'')+'" data-key="'+esc(i.key)+'"><span class="ic'+(i.kind==='lab'?' b':'')+'">'+(i.kind==='lab'?'B':'X')+'</span><span class="tx"><b>'+esc(t)+'</b><span>'+esc(i.dshort)+' · '+esc(s)+'</span></span></button>';});
 q+='</div>';var mid='',side='';
 if(it.kind==='xray'){mid='<div class="mid x"><img src="/finance/checks/photo/'+encodeURIComponent(it.sid)+'" alt="X-ray photo" onerror="this.outerHTML=\'<span class=ld>Photo Drive se nahi aayi</span>\'"><div class="cap"><b>'+esc(it.title)+'</b><span>X-ray photo · '+esc(it.dshort)+' · '+esc(it.time)+' · <a style="color:#C9D3DD" target="_blank" rel="noopener" href="/finance/checks/photo/'+encodeURIComponent(it.sid)+'">pura dekhein ↗</a></span></div><span class="rs">'+esc(it.reason)+'</span></div>';
  side='<div class="side"><div class="ask" style="padding:14px 16px 8px">'+esc(it.dshort)+' ke marij — sahi naam dabaiye</div>'+pickerHtml(it)+confirmHtml()+footHtml(it)+'</div>';}
 else{mid=it.kind==='lab'?'<div class="mid l"><a style="font-size:13px;margin:0 0 8px" target="_blank" rel="noopener" href="/finance/checks/report/'+it.fid+'">Report pura kholiye ↗</a><iframe src="/finance/checks/report/'+it.fid+'" title="Lab report"></iframe></div>':(it.fid?'<div class="mid x"><span class="ld" style="color:#C9D3DD">X-ray photo file ho chuki hai (Doctor sahab ke record mein)</span></div>':'<div class="mid x"></div>');
  side='<div class="side"><div style="padding:16px;display:flex;flex-direction:column;gap:12px" class="lside"><span style="font-size:16px;font-weight:600">'+esc(it.name)+' · ID '+esc(it.cid)+'</span><span class="s" style="font-size:13px;color:#4B5563">'+(it.kind==='lab'?'Lab report'+(it.lab?' ('+esc(it.lab)+')':''):'X-ray'+(it.study?' · '+esc(it.study):''))+' · '+esc(it.dshort)+'</span><span class="note'+(it.wrong||it.kind==='xbill'?' w':'')+'">'+esc(it.note)+'</span>'+labActs(it)+'<button class="b2" id="later2" style="min-height:42px;font-size:14px">Baad mein</button></div></div>';}
 $('app').innerHTML='<div class="pc">'+q+mid+side+'</div>';
 [].forEach.call($('app').querySelectorAll('.qi'),function(b){b.onclick=function(){CUR=b.getAttribute('data-key');PICK=-1;CF=null;MSG='';ERR='';draw();};});
 var sd=$('app').querySelector('.side');if(it.kind==='xray'){wireX(it,sd);if(!PATS[it.sid])loadPats(it,draw);var nx=a[a.indexOf(it)+1];if(nx&&nx.kind==='xray')loadPats(nx,function(){});}
 else{wireL(it,sd);var l2=$('later2');if(l2)l2.onclick=function(){LATER=LATER.filter(function(k){return k!==it.key;});LATER.push(it.key);CUR=null;draw();};}
 var pc=$('app').querySelector('.pc');if(pc)pc.style.height=Math.max(520,window.innerHeight-pc.getBoundingClientRect().top-window.scrollY-4)+'px';
 var on=$('app').querySelector('.qi.on');if(on)on.scrollIntoView({block:'nearest'});}
function draw(){chips();msgs();if(wide())drawPC();else drawPhone();}
document.addEventListener('keydown',function(e){var ae=document.activeElement;if(e.key==='Enter'&&!e.repeat&&CF&&wide()&&(!ae||ae===document.body||ae.id==='yes')){var y=$('yes');if(y&&!y.disabled){e.preventDefault();y.click();}}});
try{if(sessionStorage.getItem('s757old')){sessionStorage.removeItem('s757old');if(B.others)F='old';}}catch(e){}
document.addEventListener('submit',function(e){if(e.target&&e.target.classList&&e.target.classList.contains('ck')){try{sessionStorage.setItem('s757old','1');}catch(x){}}},true);
var rw=wide();window.addEventListener('resize',function(){if(wide()!==rw){rw=wide();draw();}});
draw();
})();
</script></body></html>"""

OWNER_PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5"><meta name="robots" content="noindex,nofollow">
<title>X-ray photos</title><style>
:root{--g:#0F5E57;--ink:#17202A;--mut:#4B5563;--mu2:#6B7280;--line:#E5E8EC;--l2:#DDE2E7;--bg:#EEF1F4;--bl:#1D4ED8;--am:#B45309;--dk:#0B0F14;--okb:#E6F4EA;--ok:#14532D}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 Inter,"Segoe UI",system-ui,-apple-system,sans-serif}
button{font-family:inherit;cursor:pointer}a{color:var(--g)}
.wrap{max-width:1180px;margin:0 auto;padding:16px}
.top{display:flex;justify-content:space-between;align-items:flex-end;gap:12px;flex-wrap:wrap;margin-bottom:14px}
.top small{font-size:13px;color:var(--mut)}.top h1{margin:2px 0 0;font-size:24px}.top .r{font-size:13px;color:var(--mut)}
.bk{display:inline-block;margin-bottom:8px;font-size:14px;font-weight:600;text-decoration:none}
.tiles{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:16px}
@media (max-width:820px){.tiles{grid-template-columns:repeat(2,1fr)}}
.tile{display:flex;flex-direction:column;gap:4px;align-items:flex-start;background:#fff;border-radius:12px;padding:14px;box-shadow:0 1px 3px rgba(16,24,40,.08);border:2px solid transparent;text-align:left}
.tile .l{font-size:13px;color:var(--mut);font-weight:600}.tile .n{font-size:30px;font-weight:700}.tile .s{font-size:12px;color:var(--mu2)}
.list{background:#fff;border-radius:12px;box-shadow:0 1px 3px rgba(16,24,40,.08);overflow:hidden}
.lh{padding:14px 16px;border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:2px}.lh b{font-size:17px}.lh span{font-size:13px;color:var(--mut)}
.msg{margin:10px 16px;background:var(--okb);color:var(--ok);border-radius:8px;padding:10px 12px;font-weight:600}
.err{margin:10px 16px;background:#FADBD8;color:#7f1d1d;border-radius:8px;padding:10px 12px;font-weight:600}
.mh{padding:10px 16px 6px;font-size:12px;font-weight:700;color:var(--mu2);text-transform:uppercase;letter-spacing:.05em;background:#F6F7F9;border-bottom:1px solid var(--line)}
.it{border-bottom:1px solid #F0F2F4}
.ir{display:flex;align-items:center;gap:12px;padding:10px 16px;flex-wrap:wrap}
.th{width:44px;height:44px;border-radius:8px;background:var(--dk);border:0;display:flex;align-items:center;justify-content:center;color:#C9D3DD;font-weight:700;flex-shrink:0}
.th.b{background:#DBEAFE;color:var(--bl)}
.dy{font-size:13px;color:var(--mut);width:56px;flex-shrink:0}
.tt{flex:1;min-width:220px;display:flex;flex-direction:column;gap:2px}.tt b{font-size:15px}.tt span{font-size:13px;color:var(--mut)}
.acts{display:flex;gap:8px;flex-wrap:wrap}
.b1{min-height:40px;padding:0 14px;border-radius:8px;font-size:14px;background:var(--g);color:#fff;border:0;font-weight:600}
.b2{min-height:40px;padding:0 14px;border-radius:8px;font-size:14px;background:#fff;color:var(--ink);border:1px solid #C7CDD4}
.bbl{background:var(--bl)}
.op{padding:4px 16px 16px 72px;display:flex;gap:16px;flex-wrap:wrap}
@media (max-width:700px){.op{padding:4px 12px 14px}}
.pv{background:var(--dk);border-radius:10px;min-height:260px;flex:1 1 360px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.pv img{max-width:100%;max-height:520px;object-fit:contain}
.rp{flex:1 1 460px;min-height:520px;border:1px solid var(--l2);border-radius:10px;background:#fff}
.pk{flex:1 1 360px;display:flex;flex-direction:column;gap:8px}
.pk .h{font-size:14px;font-weight:600}.pk .f{font-size:12px;color:var(--mu2)}
.pr{display:flex;justify-content:space-between;align-items:center;gap:10px;min-height:52px;padding:8px 12px;border-radius:10px;border:1px solid var(--l2);background:#fff;text-align:left}
.pr.top{background:#F0FAF8;border-color:#7CC4B8}.pr.sel{border:2px solid var(--g);background:#E6F4F1}
.pr b{display:block}.pr span.s{font-size:12px;color:var(--mut)}.tag{font-size:12px;font-weight:600;padding:3px 8px;border-radius:999px;background:var(--g);color:#fff;white-space:nowrap}.tag.nx{background:#FFEDD5;color:#7C2D12}
.cf{border:2px solid var(--g);border-radius:10px;padding:10px;background:#F0FAF8;display:flex;flex-direction:column;gap:8px}
.cf .w{font-size:13px;color:#7C2D12;background:#FFEDD5;border-radius:8px;padding:6px 8px}
.idb{display:flex;gap:8px}.idb input{flex:1;min-height:40px;border:1px solid #C7CDD4;border-radius:8px;padding:0 10px;font-size:15px;min-width:0}
.more{min-height:38px;background:#fff;border:1px dashed #C7CDD4;border-radius:8px;color:var(--mut)}
.empty{padding:20px 16px;color:var(--mut)}
</style></head><body><div class="wrap">
<a class="bk" href="/finance/records">&larr; Patient records</a>
<div class="top"><div><small>Your console &middot; Patients</small><h1>X-ray photos &amp; lab reports</h1></div><span class="r">Newest first &middot; grouped by month &middot; tap a tile</span></div>
<div class="tiles" id="tiles"></div><div class="list" id="list"></div></div>
<script>
(function(){
var B=__BOOT__, TAB=B.tab, OPEN=null, PICK=-1, CF=null, MSG='', ERR='', PATS={}, MORE={}, FOUND={}, FQ={};
function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
var T=[['filed','Filed by themselves since '+B.since,'tap to see each photo and where it went','#0F5E57'],['wait','Waiting to be filed','staff see the last 7 days · older ones: you and Shavez','#17202A'],
 ['nox','X-ray taken, no X-ray slip','possibly not charged — check these'+(B.xbill?' · '+B.xbill+' with Shavez':''),'#B45309'],['lab','Lab report came, no blood slip','also on Shavez’s list','#1D4ED8'],['nodz','Not in Docterz','X-rayed, not registered · file once an ID exists','#7C3AED']];
var HEAD={filed:['Filed by themselves','each photo, the patient it went to, and how'],wait:['Waiting to be filed','tap a photo to see it and pick the patient · older than 7 days: only you and Shavez see it'],
 nox:['X-ray taken, no X-ray slip','a photo filed on a patient with no X-ray on a slip or in Docterz (the day before to the day after)'],
 lab:['Lab report came, no blood slip','matched by the report’s clinic ID against the slips and Docterz · Shavez answers these too — whoever answers first closes it for both'],
 nodz:['Not in Docterz','patients X-rayed but not registered in Docterz · once they are, find them by name or mobile here and file the photo']};
function post(b){return fetch('/finance/records/xray-check/api/answer',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(function(r){return r.json();}).catch(function(){return{ok:false,err:'The server did not answer — try again.'};});}
function drop(key,m){B[TAB]=B[TAB].filter(function(i){return i.key!==key;});OPEN=null;PICK=-1;CF=null;MSG=m;ERR='';draw();}
function tiles(){$('tiles').innerHTML=T.map(function(t){return '<button class="tile" data-t="'+t[0]+'" style="'+(TAB===t[0]?'border-color:'+t[3]:'')+'"><span class="l">'+esc(t[1])+'</span><span class="n" style="color:'+t[3]+'">'+B[t[0]].length+'</span><span class="s">'+esc(t[2])+'</span></button>';}).join('');
 [].forEach.call($('tiles').querySelectorAll('.tile'),function(b){b.onclick=function(){TAB=b.getAttribute('data-t');OPEN=null;PICK=-1;CF=null;MSG='';ERR='';draw();};});}
function title(i){if(TAB==='wait'||TAB==='nodz')return i.title;if(TAB==='lab')return i.name+' · '+i.cid+(i.lab&&i.lab.toLowerCase()!==String(i.name).toLowerCase()?' (lab: '+i.lab+')':'');return i.name+' · '+i.cid;}
function detail(i){if(TAB==='wait'||TAB==='nodz')return i.reason_en;if(TAB==='lab')return i.note_en;if(TAB==='nox')return (i.study?i.study+' · ':'')+i.detail;return i.detail;}
function photo(i){return (TAB==='wait'||TAB==='nodz')?'/finance/records/xray-check/photo/'+encodeURIComponent(i.sid):'/finance/records/file/'+i.fid;}
function picker(i){var ps=PATS[i.sid];if(!ps)return '<div class="pk"><span class="f">Loading that day’s patients…</span></div>';
 var h='<div class="pk"><span class="h">Patients of '+esc(i.dshort)+' — pick the right one</span>',main=ps.filter(function(p){return !p.near;}),near=ps.filter(function(p){return p.near;});
 function row(p){var k=ps.indexOf(p),tg=p.tag_en?'<span class="tag">'+esc(p.tag_en)+'</span>':(p.nox?'<span class="tag nx">no X-ray slip</span>':'');
  return '<button class="pr'+(PICK===k?' sel':(p.top?' top':''))+'" data-k="'+k+'"><span><b>'+esc(p.name)+'</b><span class="s">ID '+esc(p.id)+' · '+esc(p.src_en)+(p.filed?' · already has a photo':'')+'</span></span>'+tg+'</button>';}
 main.forEach(function(p){h+=row(p);});if(!main.length)h+='<span class="f">No slip or Docterz line that day.</span>';
 if(near.length)h+=MORE[i.key]?near.map(row).join(''):'<button class="more" data-more="1">All other patients ('+near.length+')</button>';
 if(CF)h+='<div class="cf"><b>File this photo on '+esc(CF.name)+' ('+esc(CF.id)+')?</b>'+(CF.nox?'<span class="w">No X-ray slip for this patient — it will show under “X-ray taken, no X-ray slip”.</span>':'')+'<div class="acts"><button class="b1" id="yes">Yes, file it</button><button class="b2" id="no">No</button></div></div>';
 h+='<div class="idb"><input id="nid" placeholder="Not here? Clinic ID, name or mobile" value="'+esc(FQ[i.key]||'')+'"><button class="b2" id="nidgo">Find</button></div>'+(FOUND[i.key]?(FOUND[i.key].length?FOUND[i.key].map(function(p,k){return '<button class="pr" data-f="'+k+'"><span><b>'+esc(p.name)+'</b><span class="s">ID '+esc(p.id)+(p.mobile?' · '+esc(p.mobile):'')+'</span></span>'+(p.came?'<span class="tag">came that day</span>':'')+'</button>';}).join(''):'<span class="f">No patient found for that name or number.</span>'):'')+'<div class="acts"><button class="b2" id="notx">Not an X-ray</button>'+(TAB==='wait'?'<button class="b2" id="nodz">Not in Docterz (not registered)</button>':'')+'</div>';
 h+='<span class="f">The same picker the staff use — a tap here files it (on the next filing run).</span></div>';return h;}
function opened(i){var h='<div class="op">';
 if(TAB==='lab'){h+='<iframe class="rp" src="/finance/records/file/'+i.fid+'" title="Lab report"></iframe><div class="pk"><b>'+(i.wrong?'Is this report for '+esc(i.sug)+' ('+esc(i.sug_name)+')?':'A blood slip was not made for this test. Has it been made now?')+'</b><div class="acts">'+
  (i.wrong?'<button class="b1 bbl" data-a="moved">Yes, it is '+esc(i.sug)+'</button><button class="b2" data-a="id_ok">No, '+esc(i.cid)+' is right</button>':'<a class="b1 bbl" style="display:inline-flex;align-items:center;text-decoration:none" href="'+esc(i.desk)+'">Make the blood slip (Parchi desk) →</a><button class="b2" data-a="direct_lab">Went straight to the lab</button>')+
  '</div><span class="f">The same buttons Shavez has — whoever answers first closes it for both.</span></div>';}
 else{h+='<div class="pv"><a href="'+photo(i)+'" target="_blank" rel="noopener"><img src="'+photo(i)+'" alt="X-ray photo"></a></div>';
  if(TAB==='wait'||TAB==='nodz')h+=picker(i);
  if(TAB==='filed')h+='<div class="pk"><span class="h">Wrong patient? Type the right clinic ID</span><div class="idb"><input id="mid" inputmode="numeric" placeholder="Clinic ID"><button class="b2" id="midgo">Check</button></div>'+(CF?'<div class="cf"><b>Move this photo to '+esc(CF.name)+' ('+esc(CF.id)+')?</b><div class="acts"><button class="b1" id="mvyes">Yes, move it</button><button class="b2" id="no">No</button></div></div>':'')+'<span class="f">From: '+esc(i.orig)+'. The record moves; the Drive copy keeps its first name.</span></div>';}
 return h+'</div>';}
function list(){var a=B[TAB],h='<div class="lh"><b>'+esc(HEAD[TAB][0])+'</b><span>'+esc(HEAD[TAB][1])+'</span></div>'+(MSG?'<div class="msg">'+esc(MSG)+'</div>':'')+(ERR?'<div class="err">'+esc(ERR)+'</div>':''),last='';
 if(!a.length)h+='<div class="empty">Nothing here.</div>';
 a.forEach(function(i){if(i.month!==last){h+='<div class="mh">'+esc(i.month)+'</div>';last=i.month;}var on=OPEN===i.key,acts='';
  if(TAB==='wait'||TAB==='nodz')acts='<button class="'+(on?'b2':'b1')+'" data-o="1">'+(on?'Close':'See &amp; file')+'</button>';
  if(TAB==='filed')acts='<button class="b2" data-o="1">'+(on?'Close':'See photo')+'</button><button class="b2" data-o="1">Wrong patient? Move</button>';
  if(TAB==='lab')acts='<button class="'+(on?'b2':'b1 bbl')+'" data-o="1">'+(on?'Close':'See report &amp; answer')+'</button>';
  if(TAB==='nox')acts='<button class="b2" data-o="1">'+(on?'Close':'See photo')+'</button><button class="b2" data-a="charged_elsewhere">Charged elsewhere</button><button class="b1" data-a="tell_shavez">Missed — tell Shavez</button>';
  h+='<div class="it" data-key="'+esc(i.key)+'"><div class="ir"><button class="th'+(TAB==='lab'?' b':'')+'" data-o="1" aria-label="See">'+(TAB==='lab'?'B':'X')+'</button><span class="dy">'+esc(i.dshort)+'</span><span class="tt"><b>'+esc(title(i))+'</b><span>'+esc(detail(i))+'</span></span><span class="acts">'+acts+'</span></div>'+(on?opened(i):'')+'</div>';});
 $('list').innerHTML=h;
 [].forEach.call($('list').querySelectorAll('.it'),function(el){var key=el.getAttribute('data-key'),i=B[TAB].filter(function(x){return x.key===key;})[0];
  [].forEach.call(el.querySelectorAll('[data-o]'),function(b){b.onclick=function(){OPEN=OPEN===key?null:key;PICK=-1;CF=null;MSG='';ERR='';draw();if(OPEN&&(TAB==='wait'||TAB==='nodz')&&!PATS[i.sid])fetch('/finance/records/xray-check/api/pats?sid='+encodeURIComponent(i.sid),{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.json();}).then(function(d){PATS[i.sid]=d.ok?d.pats:[];draw();});};});
  [].forEach.call(el.querySelectorAll('[data-a]'),function(b){b.onclick=function(){b.disabled=true;var a=b.getAttribute('data-a');post({key:key,a:a,new_id:a==='moved'?i.sug:''}).then(function(r){if(r.ok)drop(key,r.msg);else{ERR=r.err;b.disabled=false;draw();}});};});
  [].forEach.call(el.querySelectorAll('.pr'),function(b){b.onclick=function(){var p=PATS[i.sid][+b.getAttribute('data-k')];PICK=+b.getAttribute('data-k');CF={id:p.id,name:p.name,nox:p.nox};draw();};});
  var m=el.querySelector('[data-more]');if(m)m.onclick=function(){MORE[key]=1;draw();};
  var y=el.querySelector('#yes');if(y)y.onclick=function(){y.disabled=true;post({key:key,a:'id_fixed',new_id:CF.id}).then(function(r){if(r.ok)drop(key,r.msg);else{ERR=r.err;draw();}});};
  var n=el.querySelector('#no');if(n)n.onclick=function(){PICK=-1;CF=null;draw();};
  [].forEach.call(el.querySelectorAll('[data-f]'),function(b){b.onclick=function(){var p=FOUND[key][+b.getAttribute('data-f')];post({key:key,a:'id_fixed',new_id:p.id,check:1}).then(function(r){if(r.ok){PICK=-1;CF={id:r.id,name:r.name,nox:r.nox};ERR='';}else ERR=r.err;draw();});};});
  var ni=el.querySelector('#nid');if(ni)ni.onkeydown=function(e){if(e.key==='Enter'){e.preventDefault();el.querySelector('#nidgo').click();}};
  var ng=el.querySelector('#nidgo');if(ng)ng.onclick=function(){var v=(el.querySelector('#nid').value||'').trim();if(!v)return;FQ[key]=v;if(!/^\d{1,8}$/.test(v)){fetch('/finance/records/xray-check/api/find?sid='+encodeURIComponent(i.sid)+'&q='+encodeURIComponent(v),{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.ok?r.json():{ok:false};}).then(function(d){if(d.ok){FOUND[key]=d.pats;ERR='';}else ERR='The search did not answer — reload the page and try again.';draw();}).catch(function(){ERR='The server did not answer — try again.';draw();});return;}post({key:key,a:'id_fixed',new_id:v,check:1}).then(function(r){if(r.ok){PICK=-1;CF={id:r.id,name:r.name,nox:r.nox};ERR='';}else ERR=r.err;draw();});};
  var nx=el.querySelector('#notx');if(nx)nx.onclick=function(){post({key:key,a:'not_xray'}).then(function(r){if(r.ok)drop(key,r.msg);else{ERR=r.err;draw();}});};
  var nd=el.querySelector('#nodz');if(nd)nd.onclick=function(){nd.disabled=true;post({key:key,a:'no_docterz'}).then(function(r){if(r.ok){B.nodz.unshift(i);drop(key,r.msg);}else{ERR=r.err;nd.disabled=false;draw();}});};
  var mg=el.querySelector('#midgo');if(mg)mg.onclick=function(){var v=(el.querySelector('#mid').value||'').trim();if(!v)return;post({key:key,a:'moved',new_id:v,check:1}).then(function(r){if(r.ok){CF={id:r.id,name:r.name};ERR='';}else ERR=r.err;draw();});};
  var mv=el.querySelector('#mvyes');if(mv)mv.onclick=function(){mv.disabled=true;post({key:key,a:'moved',new_id:CF.id}).then(function(r){if(r.ok)drop(key,r.msg);else{ERR=r.err;draw();}});};});}
function draw(){tiles();list();}
draw();
})();
</script></body></html>"""
