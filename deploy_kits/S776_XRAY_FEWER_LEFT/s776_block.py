

# ---------------------------------------------------------------- S776: fewer pictures left for a person
# S776_XRAY_FEWER_LEFT (the parent, S422, 10-Nov-2026). The owner, 13:01 IST: "I do not want to leave any work for staff in Check
# karein as much as possible." S774 (read-only, on the live database after S772) found 41 of 70 still parked. S776 adds, for a
# picture nothing else placed (the film read; never a child's picture; names compared by WHOLE words, never by first letters):
#   R1 the ID printed on the film, on its X-ray day by the film's date, when the picture's name is that patient's strictly, OR
#      close (the same first word, or two words shared -- a surname alone never) and no patient of that day, X-rayed or only
#      seen, has an ID one keystroke off; a picture with no name is never placed on a read ID alone;
#   R2 the film's date within a day; the file has no ID (or one a keystroke off) and the film prints none (or his): the name
#      close to ONE X-ray patient of that day -- nobody else X-rayed that day close -- whose X-ray of that day has no photo;
#   R3 the ID printed on the film is a patient who CAME that day (a slip or a Docterz line) with no X-ray billed -- name as R1 --
#      or, with no ID on the film, the name is word for word ONE such patient: the picture is filed on him and appears on the
#      owner's "X-ray taken, no X-ray slip" list (S757), where it goes to Shavez to bill.


def _s776_words(a, b):
    return any(x == y for x in a for y in b)


def _s776_close(toks, names):
    """The picture's name and one of the patient's: the same FIRST word, or two whole words shared (a surname alone never)."""
    for n in names:
        t = _s752_tokens(n)
        if toks and t and (toks[0] == t[0] or len(set(toks) & set(t)) >= 2):
            return True
    return False


def _s776_neighbour(con, x, day, cache):
    """Another patient of that day -- X-rayed or only seen -- whose ID is one keystroke off x (an OCR misread could be him)."""
    others = set(_s752_day(con, day, cache)[0]) | _s776_visitors(con, day)
    return any(_s752_one_off(x, o) for o in others if o != x)


def _s776_ok(con, x, orig, day, cache):
    """The ID x may take this picture: its patient's name is the picture's strictly, or close (the same first word, or two words)
    while no patient of that day has an ID one keystroke off x. A picture with no name is never placed on a read ID alone."""
    st = xray_stem(orig)
    if _s752_child(st):
        return False
    if _s772_strict(con, x, orig):
        return True
    toks = _s752_tokens(st)
    return bool(toks) and _s776_close(toks, _s772_names(con, x)) and not _s776_neighbour(con, x, day, cache)


def _s776_day_only(con, cid, film, first, cache):
    """A picture whose own ID is not confirmed: its film's ONE date as the day -- only when its own ID is not an X-ray patient of
    that day (the S776 name and film-ID rules then decide, never the file's ID)."""
    if len(film) == 1 and film[0] != first and cid not in _s752_day(con, film[0], cache)[0]:
        return film[0], S772_MARK + "the date printed on the film, %s (the file's ID %s is not that day's)" % (_dmy(film[0]), cid)
    return "", ""


def _s776_visitors(con, day):
    s = {r["c"] for r in _rows(con, "SELECT DISTINCT clinic_id c FROM slip WHERE day=? AND state='ok' AND clinic_id<>''", (day,))}
    s |= {r["c"] for r in _rows(con, "SELECT DISTINCT clinic_id c FROM clinic_day_line WHERE business_date=? AND clinic_id<>''", (day,))}
    return s


def _s776_more(con, sid, orig, day, cache):
    """(clinic ID, why) for a parked picture nothing else placed -- R2 then R3 (see the head of this section) -- or ('', '')."""
    st = xray_stem(orig)
    if _s752_child(st):
        return "", ""
    fr = _s772_film(con, sid)
    if fr is None:
        return "", ""                                    # the film not read yet
    toks = _s752_tokens(st)
    pats, filed = _s752_day(con, day, cache)
    fid_ok = [x for x in fr[1] if re.fullmatch(r"\d{4,6}", x)]
    fcid, fhow = xray_id(orig)
    if toks and fr[0] and _s772_near(day, fr[0], 1) and not [x for x in fid_ok if x in pats]:   # R2
        hits = [c for c, names in pats.items() if _s776_close(toks, list(names) + _s772_names(con, c))]
        if len(hits) == 1 and not filed.get(hits[0]) \
                and (fhow == "none" or (fhow == "one" and _s752_one_off(fcid, hits[0]))) \
                and (not fid_ok or fid_ok == [hits[0]]):
            return hits[0], "S776 \u00b7 its name is close to %s's one matching X-ray patient %s, whose photo was missing" % (_dmy(day), hits[0])
        if hits:
            return "", ""                                # several, his photo there, or the file / film names another: a person decides
    if not fr[0] or not _s772_near(day, fr[0], 1):
        return "", ""
    vis = _s776_visitors(con, day) - set(pats)
    ids = sorted({x for x in fid_ok if x in vis and _s776_ok(con, x, orig, day, cache)})
    if len(ids) == 1:                                    # R3
        return ids[0], "S776 · the ID printed on the film, %s, came on %s with no X-ray billed" % (ids[0], _dmy(day))
    if not fid_ok and toks:                              # R3, no ID on the film: the name word for word
        vm = [c for c in vis if _s772_strict(con, c, orig)]
        if len(vm) == 1:
            return vm[0], "S776 · its name is, word for word, that of %s who came on %s with no X-ray billed" % (vm[0], _dmy(day))
    return "", ""
