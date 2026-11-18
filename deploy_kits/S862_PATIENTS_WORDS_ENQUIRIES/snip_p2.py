# -*- coding: utf-8 -*-
# Snippets for patients_part2.py (S862). Read by make_s862.py.
DOC_OLD = '''It also puts its own lines at the head of each month's reading-and-suggestions (fixed rules, as Part 1's).
'''
DOC_NEW = '''  became   -- S862 (S480, 18-Nov-2026): enquiry callers who became patients. A caller of the month = a number that rang in
              (incoming, answered or not) while it was not yet a patient's: in no clinic ID of a patient seen before, and not
              yet at a first visit. He "became a patient" when a NEW patient's first visit (Part 1's rule) under that number
              came within BECAME_DAYS (60) days of his first call of the month. Beside it: of the month's new patients, how many
              rang the clinic in the 60 days up to their first visit (only where the call record covers those 60 days). A
              number shared by a family counts for whichever patient it carries; a call from another number is not seen.
  google   -- S862: also patients_google_mail.json beside this file when present -- the months the server read from Google's
              own monthly mail (S863's reader); a month's counts from the mail win, Google's year-on-year stays from the
              session file; an unreadable mail file is ignored.
It also puts its own lines at the head of each month's reading-and-suggestions (fixed rules, as Part 1's).
'''

CONST_OLD = '''CALLED_BEFORE, CALLED_AFTER = 3, 30
'''
CONST_NEW = '''CALLED_BEFORE, CALLED_AFTER = 3, 30
BECAME_DAYS = 60              # S862: an enquiry caller "became a patient" when his first visit came within 60 days
'''

GOOGLE_OLD = '''    return dict(ok=True, rows=rows, top_terms=G.get("top_terms", ""), closed_days=G.get("closed_days", ""),
                last=(rows[-1]["ym"] if rows else None))
'''
GOOGLE_NEW = '''    return dict(ok=True, rows=rows, top_terms=G.get("top_terms", ""), closed_days=G.get("closed_days", ""),
                last=(rows[-1]["ym"] if rows else None),
                read_by=("server" if merged else ""), mail_day=(str(GM.get("mail_day") or "") if merged else ""))   # S862
'''

GHEAD_OLD = '''def google_block(reading, hist):
    G = _json(GOOGLE)
    rows = []
'''
GHEAD_NEW = '''FIG_MAIL = ("searches", "views", "calls", "directions", "chats", "website", "interactions")


def google_mail():
    """S862: the months the server read from Google's own monthly mail (S863's reader writes patients_google_mail.json:
    {"months": {ym: {searches, views, calls, directions, chats, website, interactions}}, "mail_day": "YYYY-MM-DD", ...}).
    Missing or unreadable = {} (the page stands on patients_google.json alone, as before)."""
    try:
        g = _json(GOOGLE_MAIL)
        return g if isinstance(g, dict) and isinstance(g.get("months"), dict) else {}
    except Exception:                                                  # noqa: BLE001
        return {}


MERGED = {"n": 0}


def merge_months(base, mail):
    """A month's counts from the mail win; Google's year-on-year (read from the Performance page) stays from the session file."""
    out = {k: dict(v) for k, v in base.items() if isinstance(v, dict)}
    for ym, g in mail.items():
        if not (isinstance(g, dict) and re.fullmatch(r"\\d{4}-\\d\\d", str(ym))):
            continue
        figs = {}
        for k in FIG_MAIL:
            v = g.get(k)
            if isinstance(v, float) and v.is_integer():
                v = int(v)                                             # second look 6: a whole number written as 12.0
            if isinstance(v, int) and not isinstance(v, bool) and v >= 0:
                figs[k] = v
        if len(figs) == len(FIG_MAIL):
            out[ym] = dict(out.get(ym) or {}, **figs)
            out[ym].setdefault("yoy", {})
            MERGED["n"] += 1
    return out


def google_block(reading, hist):
    try:
        G = _json(GOOGLE)
        G = G if isinstance(G, dict) else {}
    except Exception:                                                  # noqa: BLE001 -- second look 4: the mail alone can stand
        G = {}
    GM = google_mail()                                                 # S862: the months S863's reader took from the mail
    MERGED["n"] = 0
    G = dict(G, months=merge_months(G.get("months") or {}, GM.get("months") or {}))
    merged = MERGED["n"]
    rows = []
'''

GCONST_OLD = '''GOOGLE = os.environ.get("PATIENTS_GOOGLE", os.path.join(FIN, "patients_google.json"))
'''
GCONST_NEW = '''GOOGLE = os.environ.get("PATIENTS_GOOGLE", os.path.join(FIN, "patients_google.json"))
GOOGLE_MAIL = os.environ.get("PATIENTS_GOOGLE_MAIL", os.path.join(FIN, "patients_google_mail.json"))   # S862 / S863
'''

BECAME_ANCHOR = '''# =================================================================================================== the "Called" columns
'''
BECAME = '''# =================================================================================================== S862: callers who became patients
def became_block(reading, lists, today, calls, cid_ph, calls_from):
    """Enquiry callers who became patients, month by month (see the head of this file). Adds lists bec:<ym> and rf:<ym>
    (clinic IDs only, with the first-visit day)."""
    newday, orig, seen_max = {}, {}, 0
    for mo in reading["months"]:
        for row in lists.get("m:%s:new" % mo["ym"], []):
            c = cid_key(row[0])
            d = str(row[1] or "")[:10]
            if c and re.fullmatch(r"\\d{4}-\\d\\d-\\d\\d", d) and (c not in newday or d < newday[c]):
                newday[c] = d
                orig[c] = str(row[0]).strip()                   # review 3: the clinic ID as Part 1 wrote it (lists, links)
        for row in lists.get("m:%s:patients" % mo["ym"], []) + lists.get("m:%s:new" % mo["ym"], []):
            c = cid_key(row[0])
            if c.isdigit():
                seen_max = max(seen_max, int(c))
    ph_cids = defaultdict(set)
    for c, phs in cid_ph.items():
        for p in phs:
            ph_cids[p].add(c)
    known = set(KNOWN_CACHE.get("ph") or ()) | set(ph_cids)
    ph_first, old = {}, set()
    for p in known:
        cs = ph_cids.get(p) or set()
        cs = {c for c in cs if not (c.isdigit() and seen_max and int(c) > seen_max)}   # review 4: an ID the visit record
        if not cs and ph_cids.get(p):                                                      # has not reached yet -- not old
            continue
        if not cs or any(c not in newday for c in cs):
            old.add(p)                    # a patient seen before the new ones of these months, or a number with no clinic ID
        else:
            ph_first[p] = min(newday[c] for c in cs)
    inc = defaultdict(list)
    for c in calls:
        if c["direction"] == "In":
            inc[c["phone"]].append(c["day"])
    for p in inc:
        inc[p].sort()
    loaded = (D(reading["months"][0]["ym"] + "-01") - dt.timedelta(days=8)).isoformat()
    cover = max(str(calls_from or "9999-12-31"), loaded)
    months = {}
    for mo in reading["months"]:
        ym = mo["ym"]
        a, b = mspan(ym, today)
        lo, hi = a.isoformat(), b.isoformat()
        mend = (a.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)
        callers = {}
        for p, days in inc.items():
            if p in old:
                continue
            d1 = next((d for d in days if lo <= d <= hi), None)
            if d1 is None:
                continue
            f = ph_first.get(p)
            if f is not None and f < d1:
                continue                  # already a patient on that day
            callers[p] = d1
        bec = []
        for p, d1 in sorted(callers.items()):
            f = ph_first.get(p)
            if f is not None and (D(f) - D(d1)).days <= BECAME_DAYS:
                cid = orig.get(sorted(c for c in ph_cids[p] if newday.get(c) == f)[0], "")
                gap = (D(f) - D(d1)).days
                bec.append([cid, f, ("rang %s and came the same day" % _dmy(d1)) if gap == 0 else
                            ("rang %s, first visit %d day%s later" % (_dmy(d1), gap, "" if gap == 1 else "s"))])
        lists["bec:%s" % ym] = sorted(bec, key=lambda x: x[1], reverse=True)
        newp = [(cid_key(r[0]), str(r[1] or "")[:10], str(r[0]).strip()) for r in lists.get("m:%s:new" % ym, [])]
        base, rang, rf = 0, 0, []
        for c, f, raw in newp:
            phs = cid_ph.get(c) or set()
            if not phs or not f or (D(f) - dt.timedelta(days=BECAME_DAYS)).isoformat() < cover:
                continue
            base += 1
            lo2 = (D(f) - dt.timedelta(days=BECAME_DAYS)).isoformat()
            hit = sorted(d for p in phs for d in inc.get(p, ()) if lo2 <= d <= f)
            if hit:
                rang += 1
                rf.append([raw, f, "rang first on %s" % _dmy(hit[0])])
        lists["rf:%s" % ym] = sorted(rf, key=lambda x: x[1], reverse=True)
        months[ym] = dict(callers=len(callers), became=len(bec), became_p=pct(len(bec), len(callers)),
                          complete=(mend + dt.timedelta(days=BECAME_DAYS)) <= today, newp=len(newp),
                          rang=(rang if base else None), rang_base=base, rang_p=pct(rang, base))
    return dict(ok=True, months=months, window=BECAME_DAYS, calls_from=calls_from,
                note=("A caller here is a number that rang in while it was not yet a patient's; he became a patient when a new "
                      "patient's first visit under that number came within %d days of his first call of the month. A month is "
                      "\\u201cso far\\u201d until %d days after its end. The right-hand count needs the call record to cover the %d days "
                      "before the first visit (it begins on %s). A call from another number, or a number shared by a family, "
                      "is not told apart. A caller who rang in two months before he came counts in both.") % (BECAME_DAYS, BECAME_DAYS, BECAME_DAYS, _dmy(calls_from) if calls_from else "–"))


'''

READ2_OLD = '''        p2["called"] = _safe(called_block, reading, lists, today, calls, cid_ph, desk.get("calls_from"))
'''
READ2_NEW = '''        p2["called"] = _safe(called_block, reading, lists, today, calls, cid_ph, desk.get("calls_from"))
        p2["became"] = _safe(became_block, reading, lists, today, calls, cid_ph, desk.get("calls_from"))   # S862
'''
READ2B_OLD = '''        p2["desk"] = dict(ok=False, why=why)
        p2["called"] = dict(ok=False, why=why)
'''
READ2B_NEW = '''        p2["desk"] = dict(ok=False, why=why)
        p2["called"] = dict(ok=False, why=why)
        p2["became"] = dict(ok=False, why=why)
'''
