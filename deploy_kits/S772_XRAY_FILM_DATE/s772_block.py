

# ---------------------------------------------------------------- S772: the film's own date and ID, the ID's one open day, the clean-up
# S772_XRAY_FILM_DATE (the parent, S422, 10-Nov-2026; the owner 10:56-11:13 IST, "do all thats possible"). A picture prepared
# afresh on the X-ray PC carries no picture time, so its day was its file time -- the day it was re-added -- and its ID was
# never on that day's X-ray list: parked for ever (18 on 09-Nov). The S752 re-try now plans such a picture on another day ONLY
# after xray_filmdate.py has read its film, and only when the patient is confirmed -- the ID printed on the film is the file's
# ID, or the picture's name matches the ID's patient STRICTLY (the S752 rule for filing; a loose match never files):
#   (1) the date printed on the film, when it is one of that ID's X-ray days (or its one open day within 2 days of it);
#   (2) the ID printed on the film when the file's name has none or another: that ID's X-ray day, its patient's name strict;
#   (3) with no date on the film: the ID's ONE X-ray day with no photo in the S772_BACK_DAYS before it was first seen.
# Anything else stays for a person. The clean-up runs only AFTER the mailbox has filed the corrected copy (state 'done'), and
# moves to "X-ray inbox / _filed / duplicates" (never deletes):
#   (a) the older parked copies of the same name -- ID none or not on that day's list, never the same ID, first seen within 3
#       days, their own film read agreeing (a date within 2 days, no other ID printed) -- only when the corrected copies
#       already cover the study's films and there are no more old copies than corrected ones (held out of the plan meanwhile,
#       so they are not filed beside it as its 'sisters');
#   (b) a copy filed to ANOTHER patient that day under a mistyped ID, when that patient shares no word of the name and has
#       more photos that day than films (so it is not his own X-ray), while the corrected copy's own film printed its ID (or its
#       patient's name is the picture's, strictly) -- its record made 'void' with the reason.
S772_BACK_DAYS = 60
S772_FILM_WINDOW = 120
S772_MARK = "S772 · "
S772_TIDY_DAYS = 14


def _s772_film(con, sid):
    """([iso dates], [clinic IDs]) read from the film by xray_filmdate.py; None when the film has not been read yet."""
    try:
        r = con.execute("SELECT * FROM xray_filmdate WHERE src_id=?", (sid,)).fetchone()
    except Exception:                                    # noqa: BLE001 -- no table yet (xray_filmdate.py not run)
        return None
    if not r:
        return None
    try:
        ds = [d for d in json.loads(r["dates"] or "[]") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d))]
    except ValueError:
        ds = []
    try:
        ids = [str(x) for x in json.loads(r["ids"] or "[]") if re.fullmatch(r"\d{4,6}", str(x))] if "ids" in r.keys() else []
    except ValueError:
        ids = []
    return ds, ids


def _s772_xray_days(con, cid):
    s = {r["day"] for r in _rows(con, "SELECT DISTINCT s.day FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.clinic_id=? "
                                      "AND s.series='xp' AND s.state='ok' AND i.kind='xray'", (cid,))}
    s |= {r["d"] for r in _rows(con, "SELECT DISTINCT business_date d FROM clinic_day_line WHERE clinic_id=? AND section='xray'", (cid,))}
    return s


def _s772_open_days(con, cid):
    filed = {r["day"] for r in _rows(con, "SELECT DISTINCT day FROM record_file WHERE clinic_id=? AND kind='xray' AND state='ok'", (cid,))}
    return {d for d in _s772_xray_days(con, cid) if d not in filed}


def _s772_shift(iso, days):
    return (dt.date.fromisoformat(iso) + dt.timedelta(days=days)).isoformat()


def _s772_near(d, dates, k=2):
    return any(_s772_shift(x, -k) <= d <= _s772_shift(x, k) for x in dates)


def _s772_names(con, cid):
    out = [(person(con, cid) or {}).get("name") or ""]
    out += [r["n"] for r in _rows(con, "SELECT DISTINCT name_seen n FROM slip WHERE clinic_id=? AND name_seen<>''", (cid,))]
    out += [r["n"] for r in _rows(con, "SELECT DISTINCT patient n FROM clinic_day_line WHERE clinic_id=? AND patient<>''", (cid,))]
    return [n for n in out if n]


def _s772_strict(con, cid, orig):
    """The picture's name is, word for word, the ID's patient (the S752 filing rule). False when the picture has no name or is a
    child's picture."""
    st = xray_stem(orig)
    fs = _s752_strict_tokens(st)
    if not fs or _s752_child(st):
        return False
    return any(_s752_name_match(fs, _s752_strict_tokens(n)) for n in _s772_names(con, cid))


def _s772_match(con, cid, film):
    """The ONE X-ray day of this ID the film's dates point to: a film date that is one of its X-ray days; else its one day with
    no photo within 2 days of a film date (the slip is sometimes written the next day). '' when none or more than one."""
    xd = _s772_xray_days(con, cid)
    hit = sorted({d for d in film if d in xd})
    if len(hit) == 1:
        return hit[0]
    if hit:
        return ""
    near = sorted(d for d in _s772_open_days(con, cid) if _s772_near(d, film))
    return near[0] if len(near) == 1 else ""


def _s772_day(con, f, row, cache):
    """(day, why) -- the day a parked picture is planned on instead of its first-seen day -- or ('', '')."""
    sid, orig = f.get("id") or "", f.get("name") or ""
    first = str(row.get("file_time") or row.get("day") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", first):
        return "", ""
    fr = _s772_film(con, sid)
    if fr is None:
        return "", ""                                    # the film not read yet: wait for xray_filmdate.py
    fd, fids = fr
    film = sorted({d for d in fd if _s772_shift(first, -S772_FILM_WINDOW) <= d <= first})
    cid, how = xray_id(orig)
    if how == "many":
        return "", ""
    for x in fids:                                       # (2) the film prints another ID than the file's name
        if x != cid and film and _s772_strict(con, x, orig):
            d = _s772_match(con, x, film)
            if d and d != first:
                if how == "one" and cid in _s752_day(con, d, cache)[0]:
                    return "", ""                        # the file's own (other) ID is an X-ray patient that day too: a person decides
                return d, S772_MARK + "the date and the ID %s printed on the film give its X-ray day %s" % (x, _dmy(d))
    if how == "one":
        if fids and cid not in fids:
            return "", ""                                # the film prints another ID: a person decides
        if cid not in fids and not _s772_strict(con, cid, orig):
            return "", ""                                # the patient not confirmed: a person decides
        if film:                                         # (1)
            d = _s772_match(con, cid, film)
            return ((d, S772_MARK + "the date printed on the film (%s) gives ID %s's X-ray day %s"
                     % (", ".join(_dmy(x) for x in film), cid, _dmy(d))) if d and d != first else ("", ""))
        if cid in _s752_day(con, first, cache)[0]:
            return "", ""                                # on the first-seen day's list: the S752 path as before
        open_ = sorted(d for d in _s772_open_days(con, cid) if _s772_shift(first, -S772_BACK_DAYS) <= d <= first)   # (3)
        if len(open_) == 1:
            return open_[0], S772_MARK + "ID %s's only X-ray day with no photo in the %d days before (%s)" % (cid, S772_BACK_DAYS, _dmy(open_[0]))
        return "", ""
    if len(film) == 1 and film[0] != first:              # no ID: the day only; the S752 strict name rule (or the film's ID) decides
        return film[0], S772_MARK + "the date printed on the film, %s" % _dmy(film[0])
    return "", ""


def _s772_film_id(con, sid, orig, day, cache):
    """The clinic ID printed on the film when the film's date is this day (within 2) and the ID is ONE X-ray patient of the day
    whose name is the picture's, strictly -- for a parked picture whose name gives no ID or one not on that day's list."""
    fr = _s772_film(con, sid)
    if not fr or not fr[0] or not _s772_near(day, fr[0]):
        return ""
    pats = _s752_day(con, day, cache)[0]
    got = sorted({x for x in fr[1] if x in pats and _s772_strict(con, x, orig)})
    return got[0] if len(got) == 1 else ""


def _s772_old(con, day, cid, st, n_new, files, rows, skip):
    """The older parked copies of a corrected picture (see the head of this section, (a)); [] unless every rule holds."""
    if not cid or not st or n_new < 1:
        return []
    studies = _day_studies(con, day, cid)[0]
    if n_new < max(1, len(studies)):
        return []                                        # the corrected copies do not cover the study's films: an old one may be a view
    pats = _s752_day(con, day, {})[0]
    old = []
    for f in files:
        sid = f.get("id") or ""
        r = rows.get(sid) or {}
        if not sid or sid in skip or r.get("state") != "check" or xray_stem(f.get("name")) != st:
            continue
        oc, how = xray_id(f.get("name") or "")
        if how == "many" or oc == cid or (oc and oc in pats):
            continue
        od = str(r.get("file_time") or r.get("day") or "")[:10]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", od) or not _s772_near(od, [day], 3):
            continue
        fr = _s772_film(con, sid)
        if not fr or not fr[0] or not _s772_near(day, fr[0]) or (fr[1] and cid not in fr[1]):
            continue                                     # its own film must agree: the day, and no other ID
        old.append(sid)
    return old if len(old) <= n_new else []


def _s772_done_groups(con):
    """{(day, ID, name): [picture ids]} of the corrected copies the mailbox has FILED on an S772 day in the last S772_TIDY_DAYS."""
    since = (_now() - dt.timedelta(days=S772_TIDY_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    groups = {}
    for r in _rows(con, "SELECT src_id, clinic_id, day, orig_name FROM xray_filing WHERE state='done' AND action='file' AND verdict LIKE ? "
                        "AND done_at>=?", ("S752 re-try: " + S772_MARK + "%", since)):
        st = xray_stem(r["orig_name"])
        if st and r["clinic_id"] and r["day"]:
            groups.setdefault((r["day"], r["clinic_id"], st), []).append(r["src_id"])
    return groups


def _s772_hold(con, feed, files, rows, days, cache):
    """(feed without the older copies of pictures planned on an S772 day this run, the held ids) -- so they are not filed beside
    the corrected copy as its 'sisters'. They stay parked (Check karein) until the corrected copy is filed, then go to duplicates."""
    groups = {}
    for f in files:
        sid = f.get("id") or ""
        cid, how = xray_id(f.get("name") or "")
        if sid in days and how == "one":
            groups.setdefault((days[sid], cid, xray_stem(f.get("name"))), []).append(sid)
    held = set()
    for (day, cid, st), new in groups.items():
        held |= set(_s772_old(con, day, cid, st, len(new), files, rows, set(days)))
    for (day, cid, st), done in _s772_done_groups(con).items():     # filed already: its old copies wait for the clean-up below
        held |= set(_s772_old(con, day, cid, st, len(done), files, rows, set(days)))
    return [x for x in feed if x.get("id") not in held], held


def _s772_tidy(con, files, rows, stamp, cache):
    """The mailbox items of the clean-up (action 'dup'): every S772 one still waiting, and new ones for the corrected copies the
    mailbox has FILED (state 'done') in the last S772_TIDY_DAYS days."""
    res = [{"id": r["src_id"], "action": "dup"} for r in
           _rows(con, "SELECT src_id FROM xray_filing WHERE state='planned' AND action='dup' AND verdict LIKE 'S772%'")]
    planned = {i["id"] for i in res}
    for (day, cid, st), srcs in sorted(_s772_done_groups(con).items()):
        n = len(srcs)
        for sid in _s772_old(con, day, cid, st, n, files, rows, planned):
            cur = con.execute("UPDATE xray_filing SET action='dup', state='planned', verdict=?, planned_at=? WHERE src_id=? AND state='check'",
                              ("S772: replaced by the corrected copy filed for ID %s on %s" % (cid, _dmy(day)), stamp, sid))
            if cur.rowcount == 1:
                res.append({"id": sid, "action": "dup"})
                planned.add(sid)
        film_says = any(cid in ((_s772_film(con, s) or ([], []))[1]) for s in srcs)
        if not film_says and not any(_s752_name_match(_s752_strict_tokens(st), _s752_strict_tokens(nm)) for nm in _s772_names(con, cid)):
            continue                                     # the corrected copy's patient not confirmed (film ID or strict name): no judgement
        wrong = []
        for fr in _rows(con, "SELECT f.id, f.clinic_id, f.drive_id, x.orig_name FROM record_file f JOIN xray_filing x ON x.file_id=f.id "
                             "WHERE f.kind='xray' AND f.state='ok' AND f.day=? AND f.clinic_id<>? AND f.source='xray_inbox' "
                             "AND x.state='done'", (day, cid)):
            if xray_stem(fr["orig_name"]) != st or not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", fr["drive_id"] or ""):
                continue
            theirs = [_s752_tokens(nm) for nm in _s772_names(con, fr["clinic_id"])]
            if not theirs or any(_s752_name_loose(_s752_tokens(st), t) for t in theirs):
                continue                                 # that patient could be the picture's: never moved by itself
            photos = _rows(con, "SELECT COUNT(*) n FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? AND day=?",
                           (fr["clinic_id"], day))[0]["n"]
            if photos <= max(1, len(_day_studies(con, day, fr["clinic_id"])[0])):
                continue                                 # no more photos than films: it may be his own X-ray, a person decides
            wrong.append(fr)
        if wrong and len(wrong) <= n:
            for fr in wrong:
                con.execute("UPDATE record_file SET state='void', note=? WHERE id=? AND state='ok'",
                            ("S772: filed under a mistyped ID; the corrected copy is filed for ID %s" % cid, fr["id"]))
                con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, clinic_id, day, new_name, state, verdict, planned_at) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(src_id) DO NOTHING",
                            (fr["drive_id"], fr["orig_name"], "", "dup", fr["clinic_id"], day, "", "planned",
                             "S772: filed to ID %s by a mistyped ID -- the corrected copy is filed for ID %s" % (fr["clinic_id"], cid), stamp))
                if fr["drive_id"] not in planned:
                    res.append({"id": fr["drive_id"], "action": "dup"})
                    planned.add(fr["drive_id"])
    return res
