"""apply_s836.py -- builds the S836 files from the live bytes (the 13-Nov bundle; check_screens a8a3552c, owner_console 16ebd73d).
usage: python3 -I apply_s836.py <in_dir> <out_dir>   Every anchor must occur exactly once, else it stops and writes nothing."""
import hashlib, os, sys
IN, OUT = sys.argv[1], sys.argv[2]
FROM = {"check_screens.py": "a8a3552c4dd14f4a01848b063d9cefef", "owner_console.py": "16ebd73dd12abb9afaf9a69bae0cb686"}
R = []  # (file, old, new)
def rep(f, old, new):
    R.append((f, old, new))
CS = "check_screens.py"
rep(CS, r'''     line (the card says the photo's date may be wrong).
"""
import datetime as dt''', r'''     line (the card says the photo's date may be wrong).

S836_CHECK_KAREIN (the parent, session 465, 14-Nov-2026; D979 item 3, the approved mock-up W5TAwHRWP5zFBpN9HtqFhB):
  * THE DATE STRIP ("Din ke hisaab se", Shavez's first chip; "Last 7 days" on the doctors' page): the last 7 days -- X-rays (slip
    or Docterz) filed / baaki / abhi samay hai / dikkat, blood tests report aayi / baaki / abhi samay hai; a date opens its
    patients. The words come from records' own lists: 'baaki' is records.xray_items' open 'xray_missing' (S834's due rule, never
    copied here) and check_items' open 'blood'; 'abhi samay hai' is records.XRAY_DUE not yet reached.
  * KAL KI X-RAY (reception, from 09:30): the newest X-ray day before today -- how many, how many filed, the rest by name -- and
    what is still baaki from the days before it.
  * THE PAIR (S450 sec I point 7): once a day's upload window is over (every X-ray of it due), a day with exactly ONE X-ray without
    a photo and exactly ONE unplaced picture asks "Kya yeh photo inki hai?" (Haan -> the S373 id_fixed road; Nahi -> ep:<drive id>
    'not_pair', never asked again). It files by itself ("system · S836 P", on "Filed by themselves" with Move) only when nobody has
    answered the picture, it is not a child's, its day is not a guess and is over, its name fits no other patient who came that day
    +-1, no number on it is another known patient's, AND it carries a positive sign -- the name fits him, or the ID read on the
    film is his or one keystroke off it. Otherwise it only asks.
  * "NOT IN DOCTERZ" IS COMPLIMENTARY (the owner 19:27-19:34 IST 13-Nov, replacing his word of 09:45 11-Nov and rule G's payment
    gap): one tap "Muft X-ray" (or "Parchi bana di") by him or Shavez closes it; no red, no 'paisa' line; his console's red line goes.
"""
import datetime as dt''')
rep(CS, 'VERSION = "S791 1"', 'VERSION = "S836 1"')
rep(CS, r'''            "G": "not registered anywhere -- a possible payment gap"}
PG_WHY = {"staff": "staff", "family": "family / own", "free": "free (no charge)", "billed": "billed another way"}''',
    r'''            "G": "not registered anywhere -- not in Docterz (a complimentary X-ray?)"}             # S836: no longer a 'payment gap'
PG_WHY = {"staff": "staff", "family": "family / own", "free": "free (no charge)", "billed": "billed another way",
          "muft": "complimentary (Muft X-ray)", "slip": "slip made"}                              # S836: the two taps of today''')
rep(CS, r'''            _write(con, "xf:" + r["src_id"], "xray_file", r["clinic_id"] or "", "id_fixed", cid, _s791_by(rule))
            n += 1
    if n:
        con.commit()
    return n''', r'''            _write(con, "xf:" + r["src_id"], "xray_file", r["clinic_id"] or "", "id_fixed", cid, _s791_by(rule))
            n += 1
    n += s836_pairs(con, cache)                          # S836: a day's only X-ray without a photo and only unplaced picture
    if n:
        con.commit()
    return n''')
rep(CS, r'''def xray_queue(con, with_people=False, recent=False, nodz_only=False):
    """S787: one item per person (the same person's photos together, 'N photos' in the title); nodz_only=True -- the ones marked
    'not in Docterz' (his page's tile)."""
    cache = {}
    out = []
    answers = R._answers(con) if nodz_only else {}
    rows = _parked(con, recent, nodz=nodz_only)
    if nodz_only:
        rows = [r for r in rows if (answers.get("xf:" + r["src_id"]) or {}).get("answer") == "no_docterz"]''',
    r'''def xray_queue(con, with_people=False, recent=False, nodz_only=False, pairs=True):
    """S787: one item per person (the same person's photos together, 'N photos' in the title); nodz_only=True -- the ones marked
    'not in Docterz' (his page's tile). S836: each item carries 'pair' (the day's only X-ray without a photo, or None)."""
    cache = {}
    out = []
    answers = R._answers(con) if nodz_only else {}
    rows = _parked(con, recent, nodz=nodz_only)
    if nodz_only:
        rows = [r for r in rows if (answers.get("xf:" + r["src_id"]) or {}).get("answer") == "no_docterz"]
    pm = _pairs(con, cache) if pairs else {}             # S836''')
rep(CS, r'''            else:
                pg = True
                en += " · POSSIBLE PAYMENT GAP: X-ray taken, no registration, no slip, no Docterz line — bill it (file the photo once an ID exists) or explain"
                hi = ("Docterz mein registered nahi — X-ray ka paisa? Parchi banaiye aur ID daaliye, ya batayein kyon (staff / ghar ka / free)")''',
    r'''            else:
                pg = True                                # S836: open until one tap -- Muft X-ray / Parchi bana di; no red
                en += " · complimentary? One tap: 'Complimentary (Muft X-ray)', or 'Slip made' if it was billed after all"
                hi = "Docterz mein entry nahi — muft X-ray?"''')
rep(CS, r'''              "n": len(g), "copies": [x["src_id"] for x in g[1:]], "reason": hi, "reason_en": en, "pg": pg, "pg_note": pg_note}
        if with_people:''', r'''              "n": len(g), "copies": [x["src_id"] for x in g[1:]], "reason": hi, "reason_en": en, "pg": pg, "pg_note": pg_note,
              "pair": pm.get(r["src_id"])}                                                       # S836
        if with_people:''')
rep(CS, r'''def pgap_items(con):
    """S791 (the owner 09:45 IST 11-Nov: "such cases indicate that there could be a payment gap"): every 'Not in Docterz' X-ray --
    marked by a person or by rule G -- until it is billed (given an ID: it leaves the list) or explained (pg:<drive id>)."""
    return [i for i in xray_queue(con, nodz_only=True) if i["pg"]]''',
    r'''def pgap_items(con):
    """S791, as S836 words it (the owner 13-Nov: "Not in Docterz" is a complimentary X-ray, not a payment gap): every 'Not in
    Docterz' X-ray -- marked by a person or by rule G -- until it is filed (given an ID: it leaves the list) or closed by one tap
    (pg:<drive id> -- Muft X-ray / Parchi bana di; the older staff / family / free / billed answers close it too)."""
    return [i for i in xray_queue(con, nodz_only=True, pairs=False) if i["pg"]]''')
rep(CS, r'''# ---------------------------------------------------------------- 2 · lab report came, no blood slip (F-1206)''',
    r'''# ---------------------------------------------------------------- S836: the pair, the date strip, yesterday's X-rays (D979 item 3)
S836_TAG = "system · S836 P"
S836_WHY = "the only X-ray of that day without a photo, and the only photo of that day without a patient"
STRIP_DAYS = 7                                     # the date strip: today and the six days before it
KAL_FROM = "09:30"                                 # reception's 'Kal ki X-ray' shows from 9:30 am (the mock-up)


def _nows():
    return R._now().strftime("%Y-%m-%d %H:%M:%S")


def _pic_day(con, r):
    """(the picture's day -- the film's printed date when it was read, else its own day -- , the film reading)."""
    fr = R._s772_film(con, r["src_id"])
    day = fr[0][0] if fr and fr[0] else r["day"]
    return (day if _ok_day(day) else ""), fr


def _window_over(day, nows):
    """Every X-ray of this day is due: S834's latest due is an evening X-ray's, 15:00 the next day (records.XRAY_DUE)."""
    return _ok_day(day) and nows >= _d(day, 1) + " 15:00:00"


def _xray_days(con, d0, d1):
    """{(day, clinic ID): due} -- every X-ray on a slip (due from records.XRAY_DUE, S834's own SQL) or on a Docterz X-ray line
    (due '' -- records.xray_items judges those) of the days d0..d1."""
    out = {}
    for s in R._rows(con, "SELECT s.day, s.clinic_id, MIN(" + R.XRAY_DUE + ") AS due FROM slip s JOIN slip_item i ON i.slip_id=s.id "
                          "WHERE s.series='xp' AND s.state='ok' AND i.kind='xray' AND s.clinic_id<>'' AND s.day>=? AND s.day<=? "
                          "GROUP BY s.day, s.clinic_id", (d0, d1)):
        out[(s["day"], s["clinic_id"])] = str(s.get("due") or "")
    for d in R._rows(con, "SELECT DISTINCT business_date day, clinic_id FROM clinic_day_line WHERE section='xray' AND clinic_id<>'' "
                          "AND business_date>=? AND business_date<=?", (d0, d1)):
        out.setdefault((d["day"], d["clinic_id"]), "")
    return out


def _photos(con, d0, d1):
    """{clinic ID: {days}} -- X-ray photos filed d0..d1 + 2 (S834: a photo filed that day or the two days after counts)."""
    out = {}
    for f in R._rows(con, "SELECT clinic_id, day FROM record_file WHERE kind='xray' AND state='ok' AND day>=? AND day<=?", (d0, _d(d1, 2))):
        out.setdefault(f["clinic_id"], set()).add(f["day"])
    return out


def _has_photo(ph, cid, day):
    return any(day <= x <= _d(day, 2) for x in ph.get(cid, ()))


def _no_photo(con, day, answers):
    """The X-ray patients of this day with no photo: none filed that day or the two after, not answered 'X-ray nahi hua', no picture
    of theirs on its way -- planned, or a waiting picture of those days already given his ID by a person or a rule (the filing run
    files it next; cold review R1)."""
    ph = _photos(con, day, day)
    plan = {r["clinic_id"] for r in R._rows(con, "SELECT clinic_id FROM xray_filing WHERE state='planned' AND clinic_id<>'' "
                                                 "AND day>=? AND day<=?", (day, _d(day, 2)))}
    for r in R._rows(con, "SELECT src_id FROM xray_filing WHERE state='check' AND day>=? AND day<=?", (_d(day, -1), _d(day, 2))):
        a = answers.get("xf:" + r["src_id"])
        if a and a["answer"] == "id_fixed" and a.get("note"):
            plan.add(a["note"])
    out = []
    for (d_, cid) in sorted(_xray_days(con, day, day)):
        a = answers.get("xm:%s:%s" % (d_, cid))
        if _has_photo(ph, cid, d_) or cid in plan or (a and a["answer"] == "not_done"):
            continue
        out.append(cid)
    return out


def _unplaced(con, answers):
    """The waiting pictures in groups of one person: the open ones, and those marked 'not in Docterz' that no tap has closed."""
    rows = [r for r in _parked(con, nodz=True)
            if (answers.get("xf:" + r["src_id"]) or {}).get("answer") != "no_docterz" or ("pg:" + r["src_id"]) not in answers]
    return _groups(rows)


def _pairs(con, cache, answers=None):
    """S836 (S450 sec I point 7): {drive id: {id, name, day, dshort, auto}} for every picture of a group that is the ONLY unplaced
    picture of its day (the film's date when read), the day's upload window over, the day holding exactly ONE X-ray without a photo,
    and nobody said 'Nahi' (ep:<drive id>). auto: nobody has answered the picture, it is not a child's, its name fits no other
    patient who came that day +-1, and no number on it is another known patient's -- then it may file itself. Cold review (R3, R4):
    never on a picture whose day is a guess (no time and no film date); 'auto' also needs the day itself over (S791's rules F / G
    have had their turn) and a POSITIVE sign -- the name fits this patient, or the ID read on the FILM is his or one keystroke off
    it (a number in the file name is never the sign: it may be the camera's counter -- second review)."""
    answers = R._answers(con) if answers is None else answers
    nows, today = _nows(), R._today()
    byday = {}
    for g in _unplaced(con, answers):
        day, fr = _pic_day(con, g[0])
        byday.setdefault(day, []).append((g, fr))
    out = {}
    for day, gs in byday.items():
        if len(gs) != 1 or not _window_over(day, nows):
            continue
        g, fr = gs[0]
        if any(("ep:" + x["src_id"]) in answers for x in g):
            continue
        if not (fr and fr[0]) and not all(x.get("file_time") for x in g):
            continue                                     # R4: the picture's day is a guess -- never paired
        miss = _no_photo(con, day, answers)
        if len(miss) != 1:
            continue
        cid, r = miss[0], g[0]
        stem = R.xray_stem(r["orig_name"] or "")
        toks, fs = R._s752_tokens(stem), R._s752_strict_tokens(stem)
        ppl = _people(con, _d(day, -1), _d(day, 1), cache)
        others = [c for c, p in ppl.items() if c != cid and toks and any(_s791_name(toks, fs, stem, n) for n in p["names"])]
        nums = {x for x in (fr[1] if fr else []) if x} | set(R._NUM.findall(R.IMG.sub("", r["orig_name"] or "")))
        alien = [x for x in nums if x != cid and not _s791_near(x, cid) and R._known_id(con, x)]
        sign = bool(toks) and any(_s791_name(toks, fs, stem, n) for n in (ppl.get(cid) or {}).get("names", [])) or \
            any(x == cid or _s791_near(x, cid) for x in (fr[1] if fr else []) if x)   # the FILM's ID -- never a camera counter
        auto = (not any(answers.get("xf:" + x["src_id"]) or answers.get("pg:" + x["src_id"]) for x in g) and not R._s752_child(stem)
                and not others and not alien and sign and _d(day, 1) < today)
        name = (ppl.get(cid) or {}).get("name") or _name_of(con, cid) or "—"
        for x in g:
            out[x["src_id"]] = {"id": cid, "name": name, "day": day, "dshort": _short(day), "auto": bool(auto),
                                "group": [y["src_id"] for y in g]}
    return out


def s836_pairs(con, cache=None):
    """Called by s787_auto before each filing plan: a pair that may file itself is given its ID as a person's answer is
    ('system · S836 P'), every photo of the group; the next filing run files it. Returns how many pictures were given."""
    cache = {} if cache is None else cache
    n, done = 0, set()
    answers = R._answers(con)                            # read after the rules above wrote theirs (cold review R1)
    rows = {r["src_id"]: r for r in _parked(con, nodz=True)}
    for sid, p in _pairs(con, cache, answers).items():
        if not p["auto"] or sid in done:
            continue
        g = p["group"]                                   # R2: exactly the pictures _pairs judged, none a person answered
        done.update(g)
        if any(answers.get("xf:" + x) or answers.get("pg:" + x) or x not in rows for x in g):
            continue
        for x in g:
            _write(con, "xf:" + x, "xray_file", rows[x]["clinic_id"] or "", "id_fixed", p["id"], {"user": S836_TAG + ": " + S836_WHY})
            n += 1
    return n


_XORD = {"issue": 0, "pending": 1, "notdue": 2, "filing": 3, "filed": 4, "in": 4, "notdone": 5, "answered": 5}


def _summ(rows, unplaced=0):
    def c(*s):
        return sum(1 for r in rows if r["st"] in s)
    rows.sort(key=lambda r: (_XORD.get(r["st"], 9), r["name"].lower(), r["cid"]))
    return {"n": len(rows), "filed": c("filed", "filing", "in"), "pending": c("pending"), "notdue": c("notdue"),
            "issue": c("issue") + unplaced, "other": c("notdone", "answered"), "unplaced": unplaced, "rows": rows}


def day_strip(con, days=STRIP_DAYS):
    """S836: the last `days` days, newest first -- per day the X-rays (slip or Docterz) and the blood tests, each patient with his
    state, and the day's unplaced pictures. X-ray: filed (a photo that day or the two after) / filing (on its way) / issue (a picture
    of his parked) / pending (records.xray_items' open 'xray_missing') / notdue (records.XRAY_DUE not reached) / notdone (answered
    'X-ray nahi hua'). Blood: in (a lab report that day or the 7 after) / pending (records.check_items' open 'blood') / answered /
    notdue."""
    _rec()
    R.ensure(con)
    today, nows = R._today(), _nows()
    d0 = _d(today, -(days - 1))
    answers = R._answers(con)
    cache = {}
    ppl = _people(con, _d(d0, -1), _d(today, 1), cache)
    ck = R.check_items(con)
    openx = {i["key"] for i in ck if i["kind"] == "xray_missing"}
    openb = {i["key"] for i in ck if i["kind"] == "blood"}
    xd, ph = _xray_days(con, d0, today), _photos(con, d0, today)
    park = {}
    for r in R._rows(con, "SELECT clinic_id, day, state FROM xray_filing WHERE state IN ('planned','check') AND clinic_id<>'' AND day>=?", (d0,)):
        park.setdefault(r["clinic_id"], []).append((r["day"], r["state"]))
    unpl = {}
    for g in _unplaced(con, answers):
        dd = _pic_day(con, g[0])[0] or g[0]["day"]
        unpl[dd] = unpl.get(dd, 0) + 1
    lr = {}
    for r in R._rows(con, "SELECT clinic_id, substr(received_at, 1, 10) d FROM lab_report WHERE received_at>=?", (d0,)):
        lr.setdefault(r["clinic_id"], set()).add(r["d"])
    bo = R._rows(con, "SELECT day, clinic_id, MAX(name_seen) nm, MAX(outcome) oc FROM blood_order WHERE state='ok' AND clinic_id<>'' "
                      "AND day>=? AND day<=? GROUP BY day, clinic_id", (d0, today))

    def nm(cid, alt=""):
        return (ppl.get(cid) or {}).get("name") or _tidy(alt) or _name_of(con, cid) or "—"

    def near(cid, day, state):
        return any(day <= d_ <= _d(day, 2) and s_ == state for d_, s_ in park.get(cid, []))

    def xst(day, cid, due):
        key = "xm:%s:%s" % (day, cid)
        a = answers.get(key)
        if _has_photo(ph, cid, day):
            return "filed"
        if near(cid, day, "planned"):
            return "filing"
        if near(cid, day, "check"):
            return "issue"
        if key in openx:
            return "pending"
        if due and due > nows:
            return "notdue"
        if a and a["answer"] == "not_done":
            return "notdone"
        return "pending" if a else "notdue"         # 'asked' (comes back after 3 days) / a Docterz line not yet due

    def bst(day, cid, oc):
        key = "bo:%s:%s" % (day, cid)
        if any(day <= x <= _d(day, 7) for x in lr.get(cid, ())):
            return "in"
        if key in openb:
            return "pending"
        return "answered" if (oc or key in answers) else "notdue"
    out = []
    for k in range(days):
        day = _d(today, -k)
        xr = []
        for (d_, cid), due in xd.items():
            if d_ == day:
                sh = ("subah" if due[:10] == day else "shaam") if due else ""
                xr.append({"cid": cid, "name": nm(cid), "st": xst(day, cid, due), "sh": sh,
                           "sh_en": {"subah": "morning", "shaam": "evening"}.get(sh, "")})
        br = [{"cid": b["clinic_id"], "name": nm(b["clinic_id"], b["nm"]), "st": bst(day, b["clinic_id"], b["oc"]), "sh": "", "sh_en": ""}
              for b in bo if b["day"] == day]
        out.append({"day": day, "dshort": _short(day), "today": day == today, "x": _summ(xr, unpl.get(day, 0)), "b": _summ(br)})
    return out


def kal_card(strip):
    """Reception's 'Kal ki X-ray': the newest X-ray day before today in the strip -- how many, how many filed, the rest by name --
    and what is still pending from the days before it. None when the week has no X-ray before today."""
    days = [s for s in strip or [] if not s["today"] and s["x"]["n"]]
    if not days:
        return None
    k = days[0]
    rows = [r for r in k["x"]["rows"] if r["st"] in ("pending", "notdue", "issue")]
    older = [dict(r, dshort=s["dshort"]) for s in strip if s["day"] < k["day"] for r in s["x"]["rows"] if r["st"] == "pending"]
    return {"day": k["day"], "dshort": k["dshort"], "n": k["x"]["n"], "filed": k["x"]["filed"], "rows": rows, "older": older,
            "late": R._now().strftime("%H:%M") >= "15:00"}


# ---------------------------------------------------------------- 2 · lab report came, no blood slip (F-1206)''')
rep(CS, r'''    if key.startswith("pg:"):                            # S791: a possible payment gap explained (staff / family / free / billed)''',
    r'''    if key.startswith("ep:"):                            # S836: "Kya yeh photo inki hai?" -- Nahi: this pair is never asked again
        sid = key[3:]
        g = group_of(con, sid, nodz=True)
        if not g:
            return 409, {"ok": False, "err": done}
        if a != "not_pair":
            return 400, {"ok": False, "err": W("Jawab samajh nahi aaya.", "Unknown answer.")}
        for x in g:
            _write(con, "ep:" + x["src_id"], "xray_pair", "", "not_pair", nid or "", u)
        con.commit()
        return 200, {"ok": True, "msg": W("Theek hai — yeh sujhav hata diya. Sahi marij neeche se chuniye.",
                                          "Noted — the suggestion is withdrawn; pick the right patient below.")}
    if key.startswith("pg:"):                            # S791: 'Not in Docterz' closed by one tap (S836: Muft X-ray / Parchi bana di)''')
rep(CS, r'''        parts.append(("%d X-ray%s of someone not registered" % (p, "" if p == 1 else "s")) if en else "X-ray bina registration %d" % p)''',
    r'''        parts.append(("%d X-ray%s not in Docterz -- complimentary?" % (p, "" if p == 1 else "s")) if en else "Muft X-ray? %d" % p)   # S836''')
rep(CS, r'''    boot = {"items": items, "lab": lab, "ok": ok, "others": len(others), "me": R._who(u), "doctor": _doctor(u)}''',
    r'''    try:
        strip = day_strip(con)                           # S836: Shavez's and the doctors' date strip; reception's 'Kal ki X-ray'
    except Exception:                                    # noqa: BLE001 -- the page stands without it
        strip = []
    boot = {"items": items, "lab": lab, "ok": ok, "others": len(others), "me": R._who(u), "doctor": _doctor(u),
            "strip": strip if lab else [], "kal": None if lab else kal_card(strip),
            "kal_show": R._now().strftime("%H:%M") >= KAL_FROM}''')
rep(CS, r'''            "xbill": len(xbill_items(con)), "since": _short(FILED_SINCE)}
    tab = request.args.get("tab")''', r'''            "xbill": len(xbill_items(con)), "since": _short(FILED_SINCE)}
    try:
        data["strip"] = day_strip(con)                   # S836: the last 7 days by date
    except Exception:                                    # noqa: BLE001 -- the page stands without it
        data["strip"] = []
    tab = request.args.get("tab")''')
rep(CS, r'''                       "tell_shavez": "sent to Shavez to bill", "slip_made": "slip made"})''',
    r'''                       "tell_shavez": "sent to Shavez to bill", "slip_made": "slip made",
                       "not_pair": "not this patient (the day's only X-ray without a photo)"})          # S836''')
# ---- the staff page (Hindi)
rep(CS, r'''/* the old list's forms (Aur sawaal) */''', r'''/* S836: the date strip, Kal ki X-ray, the pair */
.sg{display:grid;grid-template-columns:76px 1fr 1fr;gap:8px;padding:9px 14px;border:0;border-top:1px solid var(--line);background:#fff;font-size:13px;text-align:left;align-items:start;width:100%;color:var(--ink)}
.sg.sgh{font-size:11px;font-weight:700;color:var(--mu2);text-transform:uppercase;border-top:0}.sg.on{background:#F7F9FB}
.sd{display:flex;flex-direction:column;gap:5px;padding:6px 14px 10px 24px;background:#F7F9FB;font-size:13px}
.okc{color:#14532D;font-weight:600}.pdc{color:#9A3412;font-weight:600}.isc{color:#B91C1C;font-weight:600}.wtc{color:#6B7280}
.kal{border:2px solid #F0B46A}.kb{display:flex;flex-direction:column;gap:6px;padding:10px 14px 12px;font-size:14px}
.kr{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px solid var(--line)}
.cf.pair{margin:12px 10px 4px;border-color:#F0B46A;background:#FFFAF2}
/* the old list's forms (Aur sawaal) */''')
rep(CS, r'''var B=__BOOT__, IT=B.items, F='all', CUR=null,''', r'''var B=__BOOT__, IT=B.items, F=B.lab&&(B.strip||[]).length?'days':'all', DOPEN={}, CUR=null,''')
rep(CS, r'''function live(){var a=IT.filter(function(i){return F==='all'||''', r'''function live(){var a=IT.filter(function(i){return F==='all'||F==='days'||''')
rep(CS, r''' if(B.lab){[['all','Sab',IT.length],['xray','X-ray photo',nX()],['lab','Lab report',nL()]].forEach(function(c){h+='<button class="chip'+(F===c[0]?' on':'')+'" data-f="'+c[0]+'">'+c[1]+' · '+c[2]+'</button>';});}''',
    r''' if(B.lab){((B.strip||[]).length?[['days','Din ke hisaab se',-1]]:[]).concat([['all','Sab',IT.length],['xray','X-ray photo',nX()],['lab','Lab report',nL()]]).forEach(function(c){h+='<button class="chip'+(F===c[0]?' on':'')+'" data-f="'+c[0]+'">'+c[1]+(c[2]>=0?' · '+c[2]:'')+'</button>';});}''')
rep(CS, r'''function oldHtml(){return $('oldt').innerHTML;}''', r'''function oldHtml(){return $('oldt').innerHTML;}
// ---- S836: the date strip (Shavez, doctors), Kal ki X-ray (reception), the pair question
var STW={filed:['file','ok'],filing:['file ho rahi hai','ok'],pending:['baaki','pd'],notdue:['abhi samay hai','wt'],issue:['dikkat','is'],notdone:['X-ray nahi hua','wt'],'in':['aayi','ok'],answered:['jawab diya','wt']};
function cnt(o,b){if(!o.n&&!o.issue)return '<span class="wtc">&mdash;</span>';if(o.n&&o.filed===o.n&&!o.issue)return o.n+' · <span class="okc">sab '+(b?'aayi':'file')+' ✓</span>';
 var p=[];if(o.filed)p.push('<span class="okc">'+o.filed+(b?' aayi':' file')+'</span>');if(o.pending)p.push('<span class="pdc">'+o.pending+' baaki</span>');if(o.issue)p.push('<span class="isc">'+o.issue+' dikkat</span>');if(o.notdue)p.push('<span class="wtc">'+o.notdue+' abhi samay hai</span>');if(o.other)p.push('<span class="wtc">'+o.other+' jawab diya</span>');
 return o.n+' · '+p.join('<br>');}
function sRow(r,what){var w=STW[r.st]||[r.st,'wt'];return '<span><span class="'+w[1]+'c">'+w[0]+'</span> · '+what+' · '+esc(r.name)+' (ID '+esc(r.cid)+')'+(r.sh?' · '+esc(r.sh):'')+'</span>';}
function stripHtml(){var S=B.strip||[];if(!S.length)return '';var h='<div class="card"><div class="ch"><b>Pichhle 7 din</b><span>din dabaiye</span></div><div class="sg sgh"><span>Din</span><span>X-ray</span><span>Blood</span></div>';
 S.forEach(function(s){var o=DOPEN[s.day];h+='<button class="sg'+(o?' on':'')+'" data-day="'+esc(s.day)+'"><span><b>'+esc(s.dshort)+'</b> '+(o?'▴':'▾')+(s.today?'<br>aaj':'')+'</span><span>'+cnt(s.x,0)+'</span><span>'+cnt(s.b,1)+'</span></button>';
  if(o){h+='<div class="sd">';s.x.rows.forEach(function(r){h+=sRow(r,'X-ray');});
   if(s.x.unplaced)h+='<span><span class="isc">dikkat</span> · '+s.x.unplaced+' photo bina marij ke &mdash; neeche ke card</span>';
   s.b.rows.forEach(function(r){h+=sRow(r,'Blood');});
   if(!s.x.rows.length&&!s.b.rows.length&&!s.x.unplaced)h+='<span class="wtc">Is din koi X-ray / blood test nahi.</span>';h+='</div>';}});
 return h+'<div class="foot" style="margin:8px 14px 12px">“Abhi samay hai” = abhi due nahi (subah ki X-ray usi din 3 baje, shaam ki agle din 3 baje). Dikkat wale card neeche hain.</div></div>';}
function kalHtml(){var k=B.kal;if(!k||!B.kal_show)return '';
 var h='<div class="card kal"><div class="ch"><b>Kal ki X-ray &mdash; '+esc(k.dshort)+'</b><span>'+k.n+' X-ray</span></div><div class="kb"><span>'+k.n+' X-ray · <span class="okc">'+k.filed+' ki photo aa gayi ✓</span>'+(k.rows.length?' · <span class="pdc">'+k.rows.length+' baaki</span>':'')+'</span>';
 if(k.rows.length){h+='<span class="wtc">'+(k.late?'Abhi upload kar dijiye:':'Aaj dopahar 3 baje tak upload kar dijiye:')+'</span>';k.rows.forEach(function(r){h+='<span class="kr"><span>'+esc(r.name)+' (ID '+esc(r.cid)+')</span><span class="'+(r.st==='issue'?'isc':'pdc')+'">'+(r.sh?esc(r.sh)+' · ':'')+(r.st==='issue'?'dikkat':'baaki')+'</span></span>';});}
 else h+='<span class="okc">Sab photo aa gayi ✓</span>';
 if(k.older.length){h+='<span class="wtc" style="margin-top:6px">Pichhle 7 din se aur baaki: '+k.older.length+'</span>';k.older.forEach(function(r){h+='<span class="kr"><span>'+esc(r.name)+' (ID '+esc(r.cid)+') · '+esc(r.dshort)+'</span><span class="pdc">baaki</span></span>';});}
 return h+'<span class="wtc" style="font-size:12px">Photo file hote hi line apne aap hat jaati hai.</span></div></div>';}
function pairHtml(it){var p=it.pair;if(!p)return '';
 return '<div class="cf pair"><span class="qq">Kya yeh photo inki hai?</span><span style="font-size:14px">'+esc(p.dshort)+' ko sirf ek X-ray bina photo hai: <b>'+esc(p.name)+'</b> (ID '+esc(p.id)+'). Aur us din sirf yahi photo bina jagah ki hai.</span><div class="row2"><button class="b1" id="pyes">Haan, inki hai</button><button class="b2" id="pno">Nahi</button></div></div>';}
function topHtml(){return (F==='days'?stripHtml():'')+(!B.lab?kalHtml():'');}
function wireTop(){[].forEach.call($('app').querySelectorAll('.sg[data-day]'),function(b){b.onclick=function(){var d=b.getAttribute('data-day');DOPEN[d]=!DOPEN[d];draw();};});}''')
rep(CS, r''' (it.pg?'<span class="w" style="font-size:14px;color:#7C2D12;background:#FFEDD5;border-radius:8px;padding:8px 10px">Registered nahi &mdash; paisa liya? Register karke ID upar daaliye. Bill nahi banna tha to batayein:</span><div class="row2" style="gap:8px;flex-wrap:wrap"><button class="b3" data-pg="staff">Staff</button><button class="b3" data-pg="family">Ghar / apne</button><button class="b3" data-pg="free">Free</button><button class="b3" data-pg="billed">Paisa alag se liya</button></div></div>':''',
    r''' (it.pg?'<span style="font-size:14px;color:#4B5563;background:#F3F4F6;border-radius:8px;padding:8px 10px">Docterz mein entry nahi &mdash; muft X-ray? Ek tap se band:</span><div class="row2" style="gap:8px"><button class="b1" data-pg="muft">Muft X-ray</button><button class="b2" data-pg="slip">Parchi bana di</button></div></div>':''')
rep(CS, r''' var bb=root.querySelector('.bb');if(bb)bb.onclick=function(){BIG=!BIG;draw();};}''',
    r''' var py=root.querySelector('#pyes');if(py)py.onclick=function(){py.disabled=true;post({key:it.key,a:'id_fixed',new_id:it.pair.id}).then(function(r){if(r.ok)gone(it.key,r.msg);else{ERR=r.err;py.disabled=false;msgs();}});};
 var pn=root.querySelector('#pno');if(pn)pn.onclick=function(){pn.disabled=true;post({key:'ep:'+it.sid,a:'not_pair',new_id:it.pair.id}).then(function(r){if(r.ok){it.pair=null;MSG=r.msg;ERR='';draw();}else{ERR=r.err;pn.disabled=false;msgs();}});};
 var bb=root.querySelector('.bb');if(bb)bb.onclick=function(){BIG=!BIG;draw();};}''')
rep(CS, r''' if(!a.length){$('app').innerHTML='<div class="empty">Sab ho gaya — kuch dekhna baaki nahi.</div>'+(B.others&&F!=='old'?'<div class="foot">Aur sawaal upar “Aur sawaal” mein.</div>':'');return;}''',
    r''' if(!a.length){$('app').innerHTML=topHtml()+'<div class="empty">Sab ho gaya — kuch dekhna baaki nahi.</div>'+(B.others&&F!=='old'?'<div class="foot">Aur sawaal upar “Aur sawaal” mein.</div>':'');return;}''')
rep(CS, r'''  h+='<div class="card"><div class="ch"><span>Photo '+(xs.indexOf(it)+1)''', r'''  h+='<div class="card xc"><div class="ch"><span>Photo '+(xs.indexOf(it)+1)''')
rep(CS, r'''   '<span class="why">'+esc(it.reason)+'</span><span class="ask">''', r'''   '<span class="why">'+esc(it.reason)+'</span>'+pairHtml(it)+'<span class="ask">''')
rep(CS, r''' $('app').innerHTML=h;
 var c=$('app').querySelector('.card');if(c)wireX(''', r''' $('app').innerHTML=topHtml()+h;
 var c=$('app').querySelector('.card.xc');if(c)wireX(''')
rep(CS, r'''s=i.kind==='xray'?'X-ray · '+(i.pg?'registered nahi':''', r'''s=i.kind==='xray'?'X-ray · '+(i.pg?'Docterz mein nahi':''')
rep(CS, r''' if(!a.length){$('app').innerHTML='<div class="empty">Sab ho gaya — kuch dekhna baaki nahi.</div>';return;}''',
    r''' if(!a.length){$('app').innerHTML=topHtml()+'<div class="empty">Sab ho gaya — kuch dekhna baaki nahi.</div>';return;}''')
rep(CS, r'''  side='<div class="side"><div class="ask" style="padding:14px 16px 8px">''', r'''  side='<div class="side">'+pairHtml(it)+'<div class="ask" style="padding:14px 16px 8px">''')
rep(CS, r''' $('app').innerHTML='<div class="pc">'+q+mid+side+'</div>';''', r''' $('app').innerHTML=topHtml()+'<div class="pc">'+q+mid+side+'</div>';''')
rep(CS, r'''function draw(){chips();msgs();if(wide())drawPC();else drawPhone();}''', r'''function draw(){chips();msgs();if(wide())drawPC();else drawPhone();wireTop();}''')
rep(CS, r'''            "xbill": len(xbill_items(con)), "pgap": len(pgap_items(con))}                    # S791: possible payment gaps''',
    r'''            "xbill": len(xbill_items(con)), "pgap": len(pgap_items(con))}                    # S791: 'Not in Docterz' open (S836: complimentary?)''')
# ---- his page (English)
rep(CS, r''' ['nox','X-ray taken, no X-ray slip','possibly not charged — check these'+(B.xbill?' · '+B.xbill+' with Shavez':''),'#B45309'],['lab','Lab report — wrong ID?','needs an answer · '+B.lab.filter(function(i){return !i.wrong;}).length+' more filed with no blood slip, for information only','#1D4ED8'],['nodz','Not in Docterz','X-rayed, not registered · file once an ID exists','#7C3AED']];''',
    r''' ['nox','X-ray taken, no X-ray slip','possibly not charged — check these'+(B.xbill?' · '+B.xbill+' with Shavez':''),'#B45309'],['lab','Lab report — wrong ID?','needs an answer · '+B.lab.filter(function(i){return !i.wrong;}).length+' more filed with no blood slip, for information only','#1D4ED8'],['nodz','Not in Docterz','X-rayed, not registered · complimentary? one tap closes it','#7C3AED']];''')
rep(CS, r''' nodz:['Not in Docterz','patients X-rayed but not registered in Docterz · each is a possible payment gap until it is billed (once registered, find them by name or mobile here and file the photo) or explained']};''',
    r''' nodz:['Not in Docterz','patients X-rayed but not registered in Docterz · usually a complimentary X-ray: one tap “Complimentary (Muft X-ray)” closes it, or “Slip made” if it was billed after all · once registered, find them by name or mobile here and file the photo']};''')
rep(CS, r'''function tiles(){var PG=B.nodz.filter(function(i){return i.pg;}).length;
 $('tiles').innerHTML=T.map(function(t){var l=t[1],s=t[2],c=t[3],bg='';if(t[0]==='nodz'&&PG){l='Not in Docterz — possible payment gap';s=PG+' to bill or explain · X-rayed, not registered, no slip, no Docterz line';c='#B91C1C';bg='background:#FEF2F2;';}''',
    r'''function tiles(){
 $('tiles').innerHTML=T.map(function(t){var l=t[1],s=t[2],c=t[3],bg='';''')
rep(CS, r'''  if(TAB==='wait'||TAB==='nodz')h+=picker(i);
  if(TAB==='nodz'&&i.pg)h+='<div class="pk"><span class="h" style="color:#B91C1C">Possible payment gap — bill it (file the photo above once registered), or explain:</span><div class="acts"><button class="b2" data-pg="staff">Staff</button><button class="b2" data-pg="family">Family / own</button><button class="b2" data-pg="free">Free</button><button class="b2" data-pg="billed">Billed another way</button></div><span class="f">The same buttons Shavez has — whoever answers first closes it for both.</span></div>';''',
    r'''  if(TAB==='wait'||TAB==='nodz')h+=pairBox(i)+picker(i);
  if(TAB==='nodz'&&i.pg)h+='<div class="pk"><span class="h">Not in Docterz — complimentary? One tap closes it:</span><div class="acts"><button class="b1" data-pg="muft">Complimentary (Muft X-ray)</button><button class="b2" data-pg="slip">Slip made</button></div><span class="f">The same buttons Shavez has — whoever answers first closes it for both.</span></div>';''')
rep(CS, r'''<span class="tt"><b>'+esc(title(i))+'</b><span'+(TAB==='nodz'&&i.pg?' style="color:#B91C1C;font-weight:600"':'')+'>'+esc(detail(i))+'</span></span>''',
    r'''<span class="tt"><b>'+esc(title(i))+'</b><span>'+esc(detail(i))+(i.pair?' · asks: is it '+esc(i.pair.name)+'?':'')+'</span></span>''')
rep(CS, r'''i.reason_en=i.reason_en.split(' · POSSIBLE PAYMENT GAP')[0]+' · '+r.msg;''', r'''i.reason_en=i.reason_en.split(' · complimentary?')[0]+' · '+r.msg;''')
rep(CS, r'''  var mv=el.querySelector('#mvyes');''', r'''  var py=el.querySelector('#pyes');if(py)py.onclick=function(){py.disabled=true;post({key:key,a:'id_fixed',new_id:i.pair.id}).then(function(r){if(r.ok)drop(key,r.msg);else{ERR=r.err;py.disabled=false;draw();}});};
  var pn=el.querySelector('#pno');if(pn)pn.onclick=function(){pn.disabled=true;post({key:'ep:'+i.sid,a:'not_pair',new_id:i.pair.id}).then(function(r){if(r.ok){i.pair=null;MSG=r.msg;ERR='';draw();}else{ERR=r.err;pn.disabled=false;draw();}});};
  var mv=el.querySelector('#mvyes');''')
rep(CS, r'''<div class="tiles" id="tiles"></div><div class="list" id="list"></div></div>''', r'''<div class="list" id="strip" style="margin-bottom:16px"></div><div class="tiles" id="tiles"></div><div class="list" id="list"></div></div>''')
rep(CS, r'''function draw(){tiles();list();}''', r'''// ---- S836: the last 7 days by date, and the pair question
var DOPEN={},STE={filed:['filed','#14532D'],filing:['being filed','#14532D'],pending:['pending','#9A3412'],notdue:['not due yet','#6B7280'],issue:['issue','#B91C1C'],notdone:['X-ray not done','#6B7280'],'in':['report in','#14532D'],answered:['answered','#6B7280']};
function cntO(o,b){if(!o.n&&!o.issue)return '<span style="color:#6B7280">—</span>';var p=[];if(o.filed)p.push('<span style="color:#14532D;font-weight:600">'+o.filed+(b?' in':' filed')+'</span>');if(o.pending)p.push('<span style="color:#9A3412;font-weight:600">'+o.pending+' pending</span>');if(o.issue)p.push('<span style="color:#B91C1C;font-weight:600">'+o.issue+' issue</span>');if(o.notdue)p.push('<span style="color:#6B7280">'+o.notdue+' not due yet</span>');if(o.other)p.push('<span style="color:#6B7280">'+o.other+' answered</span>');return o.n+' · '+p.join(' · ');}
function sRowO(r,what){var w=STE[r.st]||[r.st,'#6B7280'];return '<span><b style="color:'+w[1]+'">'+w[0]+'</b> · '+what+' · '+esc(r.name)+' ('+esc(r.cid)+')'+(r.sh_en?' · '+esc(r.sh_en):'')+'</span>';}
function stripO(){var S=B.strip||[];if(!S.length){$('strip').hidden=true;return;}
 var h='<div class="lh"><b>Last 7 days</b><span>X-rays (slip or Docterz) and blood tests by date · tap a date for its patients · “not due yet”: a morning X-ray is due at 3 pm, an evening one at 3 pm the next day</span></div>';
 S.forEach(function(s){var o=DOPEN[s.day];h+='<div class="it"><button class="ir" data-day="'+esc(s.day)+'" style="width:100%;background:'+(o?'#F6F7F9':'#fff')+';border:0;text-align:left"><span class="dy"><b>'+esc(s.dshort)+'</b>'+(s.today?'<br>today':'')+'</span><span class="tt"><span>X-ray: '+cntO(s.x,0)+'</span><span>Blood: '+cntO(s.b,1)+'</span></span></button>';
  if(o){h+='<div class="op" style="flex-direction:column;gap:4px;font-size:13px">';s.x.rows.forEach(function(r){h+=sRowO(r,'X-ray');});
   if(s.x.unplaced)h+='<span><b style="color:#B91C1C">issue</b> · '+s.x.unplaced+' photo(s) of this day without a patient — see “Waiting to be filed”</span>';
   s.b.rows.forEach(function(r){h+=sRowO(r,'Blood');});
   if(!s.x.rows.length&&!s.b.rows.length&&!s.x.unplaced)h+='<span style="color:#6B7280">No X-ray or blood test this day.</span>';h+='</div>';}
  h+='</div>';});
 $('strip').innerHTML=h;[].forEach.call($('strip').querySelectorAll('[data-day]'),function(b){b.onclick=function(){var d=b.getAttribute('data-day');DOPEN[d]=!DOPEN[d];stripO();};});}
function pairBox(i){var p=i.pair;if(!p)return '';return '<div class="pk"><div class="cf"><b>Is this photo '+esc(p.name)+' ('+esc(p.id)+')?</b><span class="f">'+esc(p.dshort)+' has only one X-ray without a photo, and this is the only photo of that day without a patient.</span><div class="acts"><button class="b1" id="pyes">Yes, it is</button><button class="b2" id="pno">No</button></div></div></div>';}
function draw(){stripO();tiles();list();}''')
# ---- his console: the S791 red line goes (S836)
OC = "owner_console.py"
rep(OC, r'''def _s791_pgap_line(con):
    """S791 (D906 -- the owner, 11-Nov-2026 09:45 IST: an X-ray of someone not registered "could be a payment gap, so it should also
    be highlighted"): a RED Needs-you line while an X-ray on the 'Not in Docterz' list is neither billed (the photo given an ID)
    nor explained (staff / family / free). None when there are none, or anything fails."""
    try:
        import check_screens as CS                                     # noqa: PLC0415
        n = len(CS.pgap_items(con))
    except Exception:                                                  # noqa: BLE001 -- the section stands without it
        return None
    if n <= 0:
        return None
    return L("b", "X-ray taken for someone not registered -- no slip, no Docterz entry: %d (a possible payment gap; bill or explain, "
             "Shavez has it too)" % n, href="/finance/records/xray-check?tab=nodz", link="X-ray photos")


''', r'''''')
rep(OC, r'''    pl = _s791_pgap_line(con)                                          # S791: X-rays of someone not registered -- payment gaps
    if pl:
        lines.insert(0, pl)
    n, late = len(mine) + (1 if xl else 0) + (1 if bl else 0) + (1 if pl else 0), sum(1 for i in mine if i["late"]) + (1 if pl else 0)''',
    r'''    # S836 (the owner 13-Nov: 'Not in Docterz' is a complimentary X-ray, not a payment gap): S791's red line is gone; the X-ray page
    # and Shavez's Check karein close each one with one tap (Muft X-ray / Parchi bana di).
    n, late = len(mine) + (1 if xl else 0) + (1 if bl else 0), sum(1 for i in mine if i["late"])''')

# ---- apply: in order, each anchor exactly once in the text as it stands
os.makedirs(OUT, exist_ok=True)
text = {}
for f, h in FROM.items():
    b = open(os.path.join(IN, f), "rb").read()
    got = hashlib.md5(b).hexdigest()
    if got != h:
        sys.exit("STOP: %s is %s, not the live %s" % (f, got[:8], h[:8]))
    text[f] = b.decode("utf-8")
for k, (f, old, new) in enumerate(R, 1):
    c = text[f].count(old)
    if c == 0:                                           # the file writes some characters as \\uXXXX escapes
        e = "".join(ch if ord(ch) < 128 else "\\u%04x" % ord(ch) for ch in old)
        if text[f].count(e) == 1:
            old, new, c = e, "".join(ch if ord(ch) < 128 else "\\u%04x" % ord(ch) for ch in new), 1
    if c != 1:
        sys.exit("STOP: anchor %d in %s found %d times: %r" % (k, f, c, old[:90]))
    text[f] = text[f].replace(old, new)
for f, t in text.items():
    open(os.path.join(OUT, f), "wb").write(t.encode("utf-8"))
    print("%s %s -> %s (%d anchors)" % (f, FROM[f][:8], hashlib.md5(t.encode("utf-8")).hexdigest()[:8], sum(1 for x in R if x[0] == f)))
