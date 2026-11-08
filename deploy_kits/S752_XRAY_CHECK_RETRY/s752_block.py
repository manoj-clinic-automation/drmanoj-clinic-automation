

# ---------------------------------------------------------------- S752: the X-ray check folder RE-TRIED (S404, 08-Nov-2026)
# THE OWNER, 08-Nov-2026 14:46 IST ("build it"), after Alisha found 41 October X-rays 'photo baaki': the pictures had come --
# 33 of last night's 38 sat in Drive's "X-ray check" folder, parked once and never looked at again (100 parked since 20-Sep;
# no Check karein answer ever given). Three ways they got there: (1) the right ID on the picture, but the filing run (~17:40)
# came before the evening's X-ray slip (~19:30) -- "ID not in the day's X-ray list"; (2) the picture saved with the
# patient's name and no clinic ID; (3) the ID typed one digit wrong on the X-ray PC.
# NOW, on every run, each picture in the check folder that nobody has answered is planned again:
#   (1) its ID is now on that day's X-ray list (slip or Docterz)                -> filed, as the inbox files it;
#   (2) no number in its name, the day is OVER (its slips are all in), and its name is, word for word, the name of exactly
#       one X-ray patient of that day while NO other patient of that day shares even one word of it -> filed;
#       a 'baby of / master' picture is never filed by name;
#   (3) anything weaker -- an ID one keystroke off an unfiled patient of the day, a looser name match -> NEVER filed by
#       itself. Check karein shows "Shayad ID ..."; for an ID one keystroke off or a strict name match the ID is already in
#       the box (one tap on 'Sahi ID lagayein'); for a looser match it is shown as words only.
# A picture a person has answered is never touched. A re-try that no longer places goes back to the check list; a re-try
# whose picture has left the check folder by another road for a day is swept to 'gone'. The cold review's findings (S404):
# the run's own inbox rows are committed BEFORE the re-try, so a failing re-try can never take them back; numbering counts
# the rows still on their way; the day is the stored one; one read per day per page.
# The Drive side is unchanged: the mailbox script already files any picture id the plan names (VPS_Lab_Files.gs _fileXray).
S752_STOP = {"mr", "mrs", "smt", "shri", "sri", "ms", "miss", "dr", "km", "kumari", "md", "mohd",
             "mohammad", "mohammed", "devi", "kumar", "singh", "bee", "begum", "khan", "lal", "ram", "prasad", "chand", "kr",
             "jpg", "jpeg", "png", "img", "image", "xray", "ray", "scan", "copy", "new", "old", "film",
             "knee", "knees", "ankle", "wrist", "hip", "hips", "spine", "lat", "lateral", "both", "left", "right", "view",
             "views", "chest", "foot", "feet", "hand", "hands", "shoulder", "elbow", "pelvis", "lumbar", "cervical",
             "dorsal", "skull", "leg", "legs", "thigh", "arm", "standing", "side", "back", "neck", "oblique", "joint",
             "forearm", "femur", "tibia", "fibula", "humerus", "heel", "toe", "toes", "finger", "fingers", "thumb",
             "clavicle", "scapula", "sacrum", "coccyx", "lspine", "cspine", "dspine", "pbh", "lsp", "csp", "dsp", "lss",
             "ext", "flex", "flexion", "extension", "stress", "weight", "bearing", "axial", "skyline", "mortise"}
S752_CHILD = {"baby", "master", "bby", "child", "of", "putra", "putri", "son", "daughter", "putr", "beti", "beta", "wo", "do", "so"}
S752_SWEEP_HOURS = 24


def _s752_words(s):
    return re.findall(r"[a-z]+", str(s or "").lower())


def _s752_tokens(s):
    return [w for w in _s752_words(s) if len(w) >= 3 and w not in S752_STOP and w not in S752_CHILD]


S752_TITLES = {"mr", "mrs", "smt", "shri", "sri", "ms", "miss", "dr", "km", "kumari", "md", "mohd", "mohammad", "mohammed"}


def _s752_strict_tokens(s):
    """For a decision to FILE (and a pre-filled box): only titles, file and body-part words are dropped -- the name-part
    words (kumar, devi, begum, ram, lal, khan, singh, prasad ...) count, and so do two-letter words ('Om'). The cold
    review R2: 'KAMLESH KUMAR' must never become Kamlesh Devi, nor 'SITA RAM' Sita Devi, nor 'RAM PRAKASH' Om Prakash."""
    return [w for w in _s752_words(s) if len(w) >= 2 and w not in S752_TITLES and w not in S752_CHILD
            and (w not in S752_STOP or w in S752_NAMEPART)]


S752_NAMEPART = {"devi", "kumar", "singh", "bee", "begum", "khan", "lal", "ram", "prasad", "chand", "kr"}


def _s752_child(s):
    """'BABY OF REKHA', 'MASTER ...', 'S/O', 'D/O': never filed by a name match."""
    w = set(_s752_words(s))
    return bool(w & {"baby", "master", "bby", "child", "putra", "putri", "son", "daughter", "beti", "beta"}) or \
        bool(re.search(r"\b[sdwb]\s*/\s*o\b", str(s or "").lower())) or (" of " in " %s " % " ".join(_s752_words(s)))


def _s752_name_match(a, b):
    """STRICT -- a wrong match files a picture on the wrong patient. Whole words only (no prefixes): every word of the
    shorter name is a word of the other; a one-word name matches only a one-word name; or the two written together are
    the same."""
    if not a or not b:
        return False
    if "".join(a) == "".join(b):
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    if not all(x in long_ for x in short):
        return False
    return len(short) >= 2 or len(long_) == 1


def _s752_name_loose(a, b):
    """For a SUGGESTION only (a person confirms), and as the guard on (2): one word in common, or the same first four letters."""
    return any(x == y or (len(x) >= 4 and len(y) >= 4 and x[:4] == y[:4]) for x in a for y in b)


def _s752_one_off(a, b):
    """Two IDs one keystroke apart: one digit changed, two neighbours swapped, one digit added or left out."""
    a, b = str(a or ""), str(b or "")
    if a == b or not a or not b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        d = [i for i in range(len(a)) if a[i] != b[i]]
        if len(d) == 1:
            return True
        return len(d) == 2 and d[1] == d[0] + 1 and a[d[0]] == b[d[1]] and a[d[1]] == b[d[0]]
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def _s752_day(con, day, cache):
    """({clinic ID: [names]} of every X-ray patient of the day, {clinic ID: pictures filed that day}) -- read once per day."""
    if day in cache:
        return cache[day]
    pats = {}
    for s in _rows(con, "SELECT DISTINCT s.clinic_id, s.name_seen FROM slip s JOIN slip_item i ON i.slip_id=s.id "
                        "WHERE s.series='xp' AND s.state='ok' AND i.kind='xray' AND s.day=? AND s.clinic_id<>''", (day,)):
        pats.setdefault(s["clinic_id"], [])
        if s.get("name_seen"):
            pats[s["clinic_id"]].append(s["name_seen"])
    for d in _rows(con, "SELECT DISTINCT clinic_id, patient FROM clinic_day_line WHERE section='xray' AND business_date=? "
                        "AND clinic_id<>''", (day,)):
        pats.setdefault(d["clinic_id"], [])
        if d.get("patient"):
            pats[d["clinic_id"]].append(d["patient"])
    for cid, names in pats.items():
        r = _rows(con, "SELECT name FROM patient_ref WHERE clinic_id=? AND name<>'' LIMIT 1", (cid,))
        if r:
            names.append(r[0]["name"])
    filed = {r["clinic_id"]: r["n"] for r in _rows(con, "SELECT clinic_id, COUNT(*) n FROM record_file WHERE kind='xray' "
                                                        "AND state='ok' AND day=? GROUP BY clinic_id", (day,))}
    cache[day] = (pats, filed)
    return cache[day]


def _s752_by_name(con, day, orig, cache):
    """The ONE X-ray patient of the day whose name is the picture's name (strict), when no OTHER patient of that day shares
    even one word of it (loose) -- else ''. Never for a child's picture."""
    if _s752_child(xray_stem(orig)):
        return ""
    ft, fs = _s752_tokens(xray_stem(orig)), _s752_strict_tokens(xray_stem(orig))
    if not ft or not fs:
        return ""
    pats = _s752_day(con, day, cache)[0]
    strict = [c for c, names in pats.items() if any(_s752_name_match(fs, _s752_strict_tokens(n)) for n in names)]
    loose = [c for c, names in pats.items() if any(_s752_name_loose(ft, _s752_tokens(n)) for n in names)]
    return strict[0] if len(strict) == 1 and loose == strict else ""


def _s752_utc(t):
    try:
        u = dt.datetime.fromisoformat(str(t or "")[:19]) - dt.timedelta(hours=5, minutes=30)
        return u.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except ValueError:
        return ""


def _s752_retry(con, files, stamp, listed=True):
    """Plan again every unanswered picture in the check folder. Returns the mailbox items (action 'file')."""
    out = []
    rows = {}
    if files:
        rows = {r["src_id"]: r for r in _rows(con, "SELECT * FROM xray_filing WHERE src_id IN (%s)" % ",".join("?" * len(files)),
                                             tuple(f.get("id") or "" for f in files))}
    feed = []
    for f in files:
        f2 = dict(f)
        u = _s752_utc((rows.get(f.get("id")) or {}).get("file_time"))
        if u:                                              # the day first seen, not a time Drive may have moved
            f2.pop("imageMediaMetadata", None)
            f2["modifiedTime"] = u
        feed.append(f2)
    cache, placed = {}, {}
    today = _today()
    plan = [r for r in (xray_plan(con, feed) if feed else []) if r.get("id") and r.get("time")]
    plan.sort(key=lambda r: (r["time"], r["orig"]))
    for r in plan:
        sid = r["id"]
        row = rows.get(sid) or {}
        if row and row.get("state") not in ("check", "planned"):
            continue
        if row.get("state") == "planned" and not str(row.get("verdict") or "").startswith("S752"):
            continue                                       # planned by another road (a person's answer)
        day = r["time"].date().isoformat()
        cid, how, use_proposed = "", "", False
        if r["kind"] in ("ok", "differ") and r.get("cid") and r.get("proposed"):
            cid, how, use_proposed = r["cid"], "ID %s is now on %s's X-ray list" % (r["cid"], _dmy(day)), True
        elif r["kind"] == "check" and xray_id(r["orig"])[1] == "none" and day < today:
            cid = _s752_by_name(con, day, r["orig"], cache)
            how = ("no ID on the picture; its name is that of %s's one X-ray patient %s" % (_dmy(day), cid)) if cid else ""
        if not cid:
            continue
        filed = _s752_day(con, day, cache)[1].get(cid, 0)
        onway = _rows(con, "SELECT COUNT(*) n FROM xray_filing WHERE state='planned' AND action='file' AND clinic_id=? AND day=? "
                           "AND src_id<>? AND NOT (verdict LIKE 'S752%%' AND src_id IN (%s))" % ",".join("?" * len(files)),
                      (cid, day, sid) + tuple(f.get("id") or "" for f in files))
        onway = onway[0]["n"] if onway else 0
        k = placed.get((day, cid), 0)
        placed[(day, cid)] = k + 1
        if use_proposed and not filed and not onway:
            name = r["proposed"]                           # the inbox's own name: the study, or 'X-ray k' of the group
        else:
            nm = _safe((person(con, cid) or {}).get("name") or "")
            name = " · ".join(x for x in (day, cid, nm, "X-ray %d" % (filed + onway + k + 1)) if x) + _xray_ext(r["orig"])
        cur = con.execute("UPDATE xray_filing SET action='file', clinic_id=?, day=?, new_name=?, state='planned', verdict=?, planned_at=? "
                          "WHERE src_id=? AND state IN ('check','planned')", (cid, day, name, "S752 re-try: " + how, stamp, sid))
        if cur.rowcount == 1:
            out.append({"id": sid, "action": "file", "name": name, "path": _xray_path(day)})
    now_ids = {i["id"] for i in out}
    in_folder = {f.get("id") for f in files}
    for f in files:                                        # planned before, does not place now -> back to the check list
        sid = f.get("id") or ""
        row = rows.get(sid) or {}
        if sid and sid not in now_ids and row.get("state") == "planned" and str(row.get("verdict") or "").startswith("S752"):
            con.execute("UPDATE xray_filing SET action='check', clinic_id=?, new_name='', state='check', "
                        "verdict='S752: no longer placed -- back in the check list' WHERE src_id=? AND state='planned'",
                        (xray_id(row.get("orig_name") or "")[0], sid))
    if listed:                                             # planned here, left the folder by another road a day ago -> gone
        cut = (_now() - dt.timedelta(hours=S752_SWEEP_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
        for r in _rows(con, "SELECT src_id FROM xray_filing WHERE state='planned' AND verdict LIKE 'S752%' AND planned_at<?", (cut,)):
            if r["src_id"] not in in_folder:
                con.execute("UPDATE xray_filing SET state='gone', verdict='S752: left the check folder by another road' "
                            "WHERE src_id=? AND state='planned'", (r["src_id"],))
    con.commit()
    return out


def _s752_retry_safe(con, files, stamp, notes, listed=True):
    """The re-try never stops, and never undoes, the filing it rides on: this run's inbox rows and a person's answers are
    COMMITTED first; then any error in the re-try is a note, its own half-work rolled back, and the run goes on as before."""
    con.commit()
    try:
        return _s752_retry(con, files, stamp, listed)
    except Exception as ex:                              # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                # noqa: BLE001
            pass
        notes.append("S752 re-try skipped: %s" % type(ex).__name__)
        return []


def _s752_suggest(con, row, cache):
    """(clinic ID, words, prefill) for a parked picture a person must look at, or ('', '', False). prefill only for an ID
    one keystroke off, or a strict name match."""
    day = str(row.get("day") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        return "", "", False
    pats, filed = _s752_day(con, day, cache)
    if not pats:
        return "", "", False
    unfiled = [c for c in pats if not filed.get(c)]
    orig = row.get("orig_name") or ""

    def nm(c):
        return (pats.get(c) or [""])[-1] or "—"
    cid, how = xray_id(orig)
    if how == "one" and cid and cid not in pats:
        near = [c for c in unfiled if _s752_one_off(cid, c)]
        if len(near) == 1:
            return near[0], "Shayad ID %s (%s) — photo par %s likha hai, ek ank alag" % (near[0], nm(near[0]), cid), True
    ft = _s752_tokens(xray_stem(orig))
    if ft:
        fs = _s752_strict_tokens(xray_stem(orig))
        strict = [c for c in pats if fs and any(_s752_name_match(fs, _s752_strict_tokens(n)) for n in pats[c])]
        loose = [c for c in pats if any(_s752_name_loose(ft, _s752_tokens(n)) for n in pats[c])]
        if len(loose) == 1 and loose[0] in unfiled:
            strong = strict == loose and not _s752_child(xray_stem(orig))
            return loose[0], ("Shayad ID %s (%s) — naam milta hai" % (loose[0], nm(loose[0])) if strong else
                              "Shayad ID %s (%s)? Naam thoda milta hai — dekh kar ID likhein" % (loose[0], nm(loose[0]))), strong
    return "", "", False


_s752_xray_items_before = xray_items


def xray_items(con):
    """S752: the S373 items, and on a parked picture the likely ID (in its box when it is a strong one)."""
    out = _s752_xray_items_before(con)
    try:
        rows = {"xf:" + r["src_id"]: r for r in _rows(con, "SELECT * FROM xray_filing WHERE state='check'")}
        cache = {}
        for i in out:
            if i.get("kind") != "xray_file":
                continue
            r = rows.get(i.get("key"))
            if not r:
                continue
            sug, words, prefill = _s752_suggest(con, r, cache)
            if sug:
                if prefill:
                    i["suggest"] = sug
                i["why"] = ((i.get("why") or "") + " · " if i.get("why") else "") + words
    except Exception:                                    # noqa: BLE001 -- a suggestion never breaks the page
        pass
    return out
