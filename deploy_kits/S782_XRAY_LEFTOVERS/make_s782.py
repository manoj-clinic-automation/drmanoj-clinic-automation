#!/usr/bin/python3
# make_s782.py -- kit S782_XRAY_LEFTOVERS (S427, 11-Nov-2026, the parent). Usage: make_s782.py <live records.py> <output records.py>
# Builds the new records.py from the live bae45d82 bytes by exact replacement (every anchor must occur once).
import hashlib, sys
src, dst = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("bae45d82"), "not the live records.py (bae45d82)"
t = b.decode("utf-8")
R = []
R.append(("""    feed = []
    c772, s772_why, s772_day = {}, {}, {}                # S772: the planned day and its reason, per picture
    for f in files:
        f2 = dict(f)
""", """    feed = []
    c772, s772_why, s772_day = {}, {}, {}                # S772: the planned day and its reason, per picture
    o782 = {f.get("id"): f.get("name") or "" for f in files}
    files, s782_why = _s782_files(con, files, rows, c772)   # S782 (a): photo numbers out of the names, for every rule below
    s782_dup = {}                                        # S782 (b): second uploads of a photo already filed -- never filed again
    for f in files:
        dd = _s782_second(con, f.get("id") or "", f.get("name") or "", c772, o782.get(f.get("id")) or "")
        if dd[0]:                                        # never planned to file; a row planned before goes back to the list below,
            r0 = rows.get(f.get("id")) or {}               # and is sent to duplicates on the next run; one already sent there is
            if r0.get("state") == "check" or (r0.get("state") == "planned" and r0.get("action") == "dup"   # asked again until done
                                              and str(r0.get("verdict") or "").startswith(S782_MARK)):
                s782_dup[f.get("id")] = dd
            continue
        f2 = dict(f)
"""))
R.append(("""        if not cid:
            continue
        if sid in s772_why:                              # S772: say why this day
""", """        if not cid:
            continue
        if _s782_film_other(con, sid, cid, day, cache):   # S782 (c): the film prints another patient of that day -- a person decides
            continue
        if sid in s772_why:                              # S772: say why this day
"""))
R.append(("""        if sid in s772_why:                              # S772: say why this day
            how = s772_why[sid] + " -- " + how
""", """        if sid in s772_why:                              # S772: say why this day
            how = s772_why[sid] + " -- " + how
        if sid in s782_why:                              # S782 (a): say the number was a photo number
            how = s782_why[sid] + " -- " + how
"""))
R.append(("""    now_ids = {i["id"] for i in out}
    in_folder = {f.get("id") for f in files}
""", """    for sid, (dcid, dday) in sorted(s782_dup.items()):   # S782 (b): to "X-ray inbox / _filed / duplicates", never deleted
        cur = con.execute("UPDATE xray_filing SET action='dup', state='planned', verdict=?, planned_at=? WHERE src_id=? AND (state='check' "
                          "OR (state='planned' AND action='dup' AND verdict LIKE 'S782%'))",
                          (S782_MARK + "a second upload of the photo already filed for ID %s on %s -- the same name, and the same "
                           "date and ID printed on the film" % (dcid, _dmy(dday)), stamp, sid))
        if cur.rowcount == 1:
            out.append({"id": sid, "action": "dup"})
    now_ids = {i["id"] for i in out}
    in_folder = {f.get("id") for f in files}
"""))
R.append(("""                            "WHERE src_id=? AND state='planned'", (r["src_id"],))
    out.extend(_s772_tidy(con, files, rows, stamp, c772))   # S772: the clean-up
""", """                            "WHERE src_id=? AND state='planned'", (r["src_id"],))
        for r in _rows(con, "SELECT src_id FROM xray_filing WHERE state='planned' AND action='dup' AND verdict LIKE 'S782%' "
                            "AND planned_at<?", (cut,)):   # S782 (b): sent to duplicates and gone from the folder a day ago
            if r["src_id"] not in in_folder:
                con.execute("UPDATE xray_filing SET state='dup', done_at=? WHERE src_id=? AND state='planned'", (stamp, r["src_id"]))
    out.extend(_s772_tidy(con, files, rows, stamp, c772))   # S772: the clean-up
"""))
R.append(("""        ds = [d for d in json.loads(r["dates"] or "[]") if re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", str(d))]
""", """        ds = [d for d in json.loads(r["dates"] or "[]") if re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", str(d)) and _s782_real_day(d)]   # S782
"""))
R.append(("""        if sid and sid not in now_ids and row.get("state") == "planned" and str(row.get("verdict") or "").startswith("S752"):
""", """        if sid and sid not in now_ids and row.get("state") == "planned" and (str(row.get("verdict") or "").startswith("S752") or (
                row.get("action") == "dup" and str(row.get("verdict") or "").startswith(S782_MARK))):   # S782: a duplicate no longer one
"""))
TAIL = '''

# ---------------------------------------------------------------- S782: the photo number and the second upload (F-1236)
# S782_XRAY_LEFTOVERS (the parent, S427, 11-Nov-2026). The owner, 13:01 IST 10-Nov: "I do not want to leave any work for staff in
# Check karein as much as possible." The re-try above (S752 / S772 / S776) now also knows two things:
#   (a) a 1-3-digit number in a picture's name ("NAME 2.jpg", "NAME 1234 2.jpg") is the photo's own sequence number, not a clinic
#       ID, when nobody who came on the picture's first-seen day, or on a date printed on its film (a day either side), has that
#       ID, and the picture's name is not that ID's patient -- the re-try reads the name without it; every rule above then decides
#       exactly as before (a number that IS such a patient is kept: an old patient's short ID still files);
#   (b) a parked picture whose film prints the same date(s) and the same clinic ID as a copy of the SAME NAME already filed on that
#       very ID under the very same file name -- whose X-rays of that day all have their photos -- is a second upload: it goes to "X-ray inbox / _filed /
#       duplicates" (never deleted) and is never filed a second time. A picture with no film read, no ID printed, two IDs in its
#       name, or its own ID another patient's, is never touched by (b);
#   (c) a picture is never filed by itself on one patient while its film prints the clinic ID of ANOTHER patient who came that
#       day (X-rayed or only seen) -- the staff's typing and the machine's print disagree on two real people: a person decides.
#       (Before S782 a name-only picture could be filed on its name's patient whatever the film printed.)
S782_MARK = "S782 \\u00b7 "


def _s782_real_day(d):
    """A calendar date (xray_filmdate.py checks this when it reads a film; a row written another way could carry 2026-02-30,
    which would stop every re-try)."""
    try:
        dt.date.fromisoformat(str(d))
        return True
    except ValueError:
        return False


def _s782_days(con, sid, first):
    """The first-seen day and every date printed on the film within S772_FILM_WINDOW before it, each with the day either side --
    None while the film has not been read (nothing is stripped before it is). A date that is no calendar date is skipped."""
    fr = _s772_film(con, sid)
    if fr is None:
        return None
    days = set()
    for d in [first] + list(fr[0]):
        try:
            if d != first and not (_s772_shift(first, -S772_FILM_WINDOW) <= d <= first):
                continue
            days |= {d, _s772_shift(d, -1), _s772_shift(d, 1)}
        except ValueError:                               # an OCR misread such as 2026-02-30 -- never stops the re-try
            continue
    return days or None


def _s782_strip(con, sid, name, first, cache):
    """(the name without its photo numbers, why) -- or ('', '') when no number is dropped (a)."""
    stem = IMG.sub("", name or "")
    short = [n for n in _NUM.findall(stem) if len(n) <= 3]
    if not short or not re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", first or ""):
        return "", ""
    days = _s782_days(con, sid, first)
    if not days:
        return "", ""
    who = set()
    for d in days:
        who |= set(_s752_day(con, d, cache)[0]) | _s776_visitors(con, d)
    drop = [n for n in short if n not in who and not _s772_strict(con, n, name)]
    if not drop:
        return "", ""
    for n in drop:
        stem = re.sub(r"(?<!\\d)%s(?!\\d)" % n, " ", stem, count=1)
    ext = name[len(IMG.sub("", name)):]
    return stem + ext, S782_MARK + "%s in the name is the photo's number (no patient of that day has the ID)" % " and ".join(drop)


def _s782_files(con, files, rows, cache):
    """(files with the photo numbers taken out of their names, {picture id: why}) -- (a). The originals are not changed."""
    out, why = [], {}
    for f in files:
        row = rows.get(f.get("id")) or {}
        first = str(row.get("file_time") or row.get("day") or "")[:10]
        nm, w = _s782_strip(con, f.get("id") or "", f.get("name") or "", first, cache)
        if nm:
            f = dict(f, name=nm)
            why[f.get("id")] = w
        out.append(f)
    return out, why


def _s782_film_other(con, sid, cid, day, cache):
    """True when the film prints a clinic ID other than cid that is a patient who came that day (X-rayed or only seen): the
    staff's name and the machine's ID disagree on two real patients -- never filed by itself (c)."""
    fr = _s772_film(con, sid)
    if not fr or not fr[1]:
        return False
    who = set(_s752_day(con, day, cache)[0]) | _s776_visitors(con, day)
    return any(x != cid and x in who for x in fr[1])


def _s782_second(con, sid, name, cache, orig=""):
    """(clinic ID, day) of the one copy of this picture already filed -- (b) -- or ('', ''). The filed copy must carry the very
    same file name (a second view is always named apart: "NAME 1234 2"), and the picture's own name must be unchanged by (a)."""
    if orig and orig != name:
        return "", ""
    st = xray_stem(name)
    if not sid or not st or not _s752_tokens(st):
        return "", ""
    fr = _s772_film(con, sid)
    if not fr or not fr[0] or not fr[1]:
        return "", ""
    own, how = xray_id(name)
    if how == "many":
        return "", ""
    key = (sorted(set(fr[0])), sorted(set(fr[1])))
    hits = set()
    for x in _rows(con, "SELECT x.src_id, x.orig_name, x.clinic_id, x.day FROM xray_filing x JOIN record_file f ON f.id=x.file_id "
                        "WHERE x.state='done' AND x.action='file' AND f.state='ok' AND f.kind='xray' AND x.src_id<>? "
                        "AND x.clinic_id IN (%s)" % ",".join("?" * len(key[1])), (sid,) + tuple(key[1])):
        if (x["orig_name"] or "").strip().upper() != (name or "").strip().upper() or (own and own != x["clinic_id"]) or not x["day"]:
            continue
        fx = _s772_film(con, x["src_id"])
        if not fx or (sorted(set(fx[0])), sorted(set(fx[1]))) != key:
            continue
        n_st = len(_day_studies(con, x["day"], x["clinic_id"])[0])
        if not n_st or _s752_day(con, x["day"], cache)[1].get(x["clinic_id"], 0) < n_st:
            continue                                     # a film of that day still has no photo: this could be it -- a person decides
        hits.add((x["clinic_id"], x["day"]))
    return sorted(hits)[0] if len(hits) == 1 else ("", "")
'''
for old, new in R:
    assert t.count(old) == 1, "anchor not once: " + old[:60]
    t = t.replace(old, new)
t = t.rstrip("\n") + "\n" + TAIL
open(dst, "wb").write(t.encode("utf-8"))
print("written", dst, hashlib.md5(t.encode("utf-8")).hexdigest()[:8])
