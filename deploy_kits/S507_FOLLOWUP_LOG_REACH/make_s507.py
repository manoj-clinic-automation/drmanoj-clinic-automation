"""make_s507.py -- S507_FOLLOWUP_LOG_REACH. Builds the three files from the live bytes by exact, counted edits.
    python3 make_s507.py <live dir> <out dir>        (--pins prints the pins)"""
import hashlib
import os
import sys

PINS = {"docterz_pickup.py": "b2dc54758bc5", "aaj_duties.json": "7aa29bef179b", "aaj_seed.py": "e13d03d0"}


def rep(s, a, b, what):
    n = s.count(a)
    assert n == 1, "%s: anchor found %d times: %r" % (what, n, a[:70])
    return s.replace(a, b)


def build(live, out):
    got = {}
    for name, pin in PINS.items():
        b = open(os.path.join(live, name), "rb").read()
        assert hashlib.md5(b).hexdigest().startswith(pin), "%s: FROM pin differs" % name
        got[name] = b.decode("utf-8")

    # ---------------------------------------------------------------------------------- docterz_pickup.py
    s = got["docterz_pickup.py"]
    s = rep(s, '''THE ALARM: no consultation export for the last working day''', '''S507 (10-Oct-2026): on Saturday 10-Oct reception exported the follow-up log for ONE day -- Sunday 11-Oct -- so the next call
day (Monday 12-Oct) was not in it and Monday's call list would have been empty; the duty lines counted the file as 'there'.
Now each follow-up log records the due dates it covers (due_from / due_to, two columns added by ensure() on first use, filled in
for the logs already kept, by themselves) and a log that does not reach the next call day (the day after, Sunday skipped) is
NOT a done export: reception's evening and morning lines stay up, and the owner's page says so. A one-day export of the next
call day is enough (the tracker loads only that day); Docterz's default one-month export always is.
THE ALARM: no consultation export for the last working day''', "pickup docstring")
    s = rep(s, '''def ensure(con):
    con.executescript(DDL)
''', '''def ensure(con):
    con.executescript(DDL)
    _span_cols(con)


def _span_cols(con):
    """S507: the due dates a follow-up log covers -- two columns, added once (no COMMIT of anyone's transaction)."""
    try:
        have = {r[1] for r in con.execute("PRAGMA table_info(docterz_export)")}
        for c in ("due_from", "due_to"):
            if c not in have:
                con.execute("ALTER TABLE docterz_export ADD COLUMN %s TEXT NOT NULL DEFAULT ''" % c)
    except sqlite3.Error:                                    # a read-only connection: the columns come with the next pass
        pass


def next_call_day(day_iso):
    """S507: the day after `day_iso`, Sunday skipped (the clinic is closed on Sunday)."""
    d = dt.date.fromisoformat(day_iso) + dt.timedelta(days=1)
    return (d + dt.timedelta(days=1) if d.weekday() == 6 else d).isoformat()


def followup_span(raw):
    """S507: (earliest, latest) due date of a follow-up log, iso; ('', '') when it is not one or carries no date."""
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = raw.decode("cp1252")
        except UnicodeDecodeError:
            return "", ""
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return "", ""
    if not rows:
        return "", ""
    head = [h.strip() for h in rows[0]]
    idx = {h: i for i, h in enumerate(head)}
    dkey = next((h for h in head if h.lower().replace("_", " ") in ("due date", "follow up date", "followup date", "follow-up date")), None)
    if not dkey or "Appointment ID" not in idx:
        return "", ""
    dates = [parse_date(r[idx[dkey]]) for r in rows[1:] if len(r) > idx[dkey]]
    dates = [d for d in dates if d]
    return (min(dates).isoformat(), max(dates).isoformat()) if dates else ("", "")


def backfill_spans(con):
    """S507: the follow-up logs kept before the two columns existed get their due dates from their own stored bytes (once)."""
    n = 0
    for rid, stored in con.execute("SELECT id, stored FROM docterz_export WHERE kind='followup' AND COALESCE(due_to,'')='' "
                                   "AND COALESCE(stored,'')<>''").fetchall():
        try:
            with open(stored, "rb") as fh:
                a, b = followup_span(fh.read())
        except OSError:
            continue
        if b:
            con.execute("UPDATE docterz_export SET due_from=?, due_to=? WHERE id=?", (a, b, rid))
            n += 1
    con.commit()
    return n
''', "ensure")
    s = rep(s, '''    if not dry:
        con.execute("INSERT OR IGNORE INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)", (f["id"], f.get("name") or "", f.get("modifiedTime") or "", md5, kind, day, nrows, stored, st, note,
                                                       now().isoformat(sep=" ")))
        con.commit()''', '''    if not dry:
        _span_cols(con)                                      # S507: the due dates covered, for a follow-up log
        dfrom, dto = followup_span(raw) if kind == "followup" else ("", "")
        if kind == "followup" and dto and day and st == "current" and dto < next_call_day(day):
            note = (note + "; " if note else "") + "covers only %s to %s -- the next call day %s is not in it" % (dfrom, dto, next_call_day(day))
        con.execute("INSERT OR IGNORE INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, status, note, taken_at, "
                    "due_from, due_to) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (f["id"], f.get("name") or "", f.get("modifiedTime") or "", md5, kind, day, nrows,
                                                                             stored, st, note, now().isoformat(sep=" "), dfrom, dto))
        con.commit()''', "take insert")
    s = rep(s, '''def run(con, dry=False):
    ensure(con)
''', '''def run(con, dry=False):
    ensure(con)
    if not dry:
        backfill_spans(con)                                  # S507
''', "run")
    s = rep(s, '''        since = (at.date() - dt.timedelta(days=3)).isoformat()
        for r in con.execute("SELECT kind, business_date, note FROM docterz_export WHERE status='quarantined' ''', '''        # S507: the last working day's follow-up log does not reach the next call day
        r = con.execute("SELECT due_from, due_to FROM docterz_export WHERE kind='followup' AND business_date=? AND status='current' "
                        "ORDER BY id DESC LIMIT 1", (day,)).fetchone()
        if r and r[1] and r[1] < next_call_day(day):
            out.append("The Docterz follow-up log of %s reaches only %s, so the next call day (%s) is not in it and that day's call list is "
                       "short. Export the follow-up log again with Docterz's usual one-month range (reception, or this PC); the tracker "
                       "re-runs the day within minutes." % (dt.date.fromisoformat(day).strftime("%a %d-%b"),
                                                            dt.date.fromisoformat(r[1]).strftime("%a %d-%b"),
                                                            dt.date.fromisoformat(next_call_day(day)).strftime("%a %d-%b")))
        since = (at.date() - dt.timedelta(days=3)).isoformat()
        for r in con.execute("SELECT kind, business_date, note FROM docterz_export WHERE status='quarantined' ''', "owner_lines")
    out_s = {"docterz_pickup.py": s}

    # ---------------------------------------------------------------------------------- aaj_duties.json (the two duties' SQL)
    j = got["aaj_duties.json"]
    j = rep(j, '''e.kind = 'followup' AND e.business_date = (SELECT day FROM d) AND e.status = 'current')''',
            '''e.kind = 'followup' AND e.business_date = (SELECT day FROM d) AND e.status = 'current' AND (COALESCE(e.due_to,'') = '' OR e.due_to >= (CASE strftime('%w', date((SELECT day FROM d),'+1 day')) WHEN '0' THEN date((SELECT day FROM d),'+2 day') ELSE date((SELECT day FROM d),'+1 day') END)))''',
            "duties: morning follow-up")
    j = rep(j, '''AND NOT EXISTS (SELECT 1 FROM docterz_export e WHERE e.kind = k.kind AND e.business_date = date('now','localtime') AND e.status = 'current')''',
            '''AND NOT EXISTS (SELECT 1 FROM docterz_export e WHERE e.kind = k.kind AND e.business_date = date('now','localtime') AND e.status = 'current' AND (e.kind <> 'followup' OR COALESCE(e.due_to,'') = '' OR e.due_to >= (CASE strftime('%w', date('now','localtime','+1 day')) WHEN '0' THEN date('now','localtime','+2 day') ELSE date('now','localtime','+1 day') END)))''',
            "duties: night exports")
    out_s["aaj_duties.json"] = j

    # ---------------------------------------------------------------------------------- aaj_seed.py (the hint staff read)
    t = got["aaj_seed.py"]
    hint = "Follow-up log mein agle kaam ke din (Sunday chhodkar) tak ki date honi chahiye -- Docterz ka default ek mahine wala export sabse sahi hai."
    t = rep(t, ''''rec.docterz_morning': {'how': 'Reception PC par Docterz se report nikaliye. Wo apne aap server par chali jaati hai.',''',
            ''''rec.docterz_morning': {'how': 'Reception PC par Docterz se report nikaliye. Wo apne aap server par chali jaati hai. %s',   # S507''' % hint,
            "seed: morning how")
    t = rep(t, ''''reception.night_exports': {'how': 'Raat ko rah jaaye to kal subah yahi pehla kaam hoga.'},''',
            ''''reception.night_exports': {'how': '%s Raat ko rah jaaye to kal subah yahi pehla kaam hoga.'},   # S507''' % hint,
            "seed: night how")
    out_s["aaj_seed.py"] = t

    os.makedirs(out, exist_ok=True)
    for name, text in out_s.items():
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(text.encode("utf-8"))
        print("built %s %s" % (name, hashlib.md5(text.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--pins"]:
        print(" ".join("%s:%s" % kv for kv in sorted(PINS.items())))
    else:
        build(sys.argv[1], sys.argv[2])
