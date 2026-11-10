"""S779 maker: python -B make_s779.py <live /root/finance/docterz_pickup.py (md5 f8cb978e, S507/S509)> <out file>
Five counted edits on the live bytes; each anchor must occur exactly once."""
import sys, hashlib
src, out = sys.argv[1], sys.argv[2]
b = open(src, encoding="utf-8").read()
assert hashlib.md5(b.encode("utf-8")).hexdigest() == "f8cb978e8d29a03d931b4e4a2d01ce6e", "not the live f8cb978e"
E = [
("THE ALARM: no consultation export",
 "S779 (S424, 10-Nov-2026, D884): Docterz's CLINICAL DATA REPORT carries the consultation columns too (Consultation Date, Mode Of\n"
 "Payment), so identify() took it for a consultation report -- a catch-up export of months would have replaced the day's real one.\n"
 "It is now a third kind, 'clinical' (it carries Diagnosis and Drugs Prescribed): kept by its bytes, never replacing or replaced\n"
 "by day (one export may span months), and read into the per-visit diagnosis table by dx_feed.py the moment it is taken.\n"
 "THE ALARM: no consultation export"),
('KINDS = {"consultation": "consultation report", "followup": "follow-up log"}',
 'KINDS = {"consultation": "consultation report", "followup": "follow-up log", "clinical": "clinical data report"}'),
('''    if "Consultation Date" in idx and "Mode Of Payment" in idx:
''',
'''    if "Consultation Date" in idx and "Diagnosis" in idx and "Drugs Prescribed" in idx:
        # S779: the clinical data report -- before the consultation test, whose two columns it also carries
        dates = [parse_date(r[idx["Consultation Date"]]) for r in body if len(r) > idx["Consultation Date"]]
        dates = [d for d in dates if d]
        return ("clinical", (max(dates).isoformat() if dates else ""), len(dates),
                ("covers %s to %s" % (min(dates).isoformat(), max(dates).isoformat())) if dates else "")
    if "Consultation Date" in idx and "Mode Of Payment" in idx:
'''),
('''            cur = con.execute("SELECT * FROM docterz_export WHERE kind=? AND business_date=? AND status='current'", (kind, day)).fetchone()
''',
'''            if kind == "clinical":                             # S779: by its bytes only -- one export may span months
                cur = con.execute("SELECT * FROM docterz_export WHERE kind=? AND md5=? AND status='current'", (kind, md5)).fetchone()
            else:
                cur = con.execute("SELECT * FROM docterz_export WHERE kind=? AND business_date=? AND status='current'", (kind, day)).fetchone()
'''),
('''        con.commit()
    return kind, day, nrows, st, note
''',
'''        con.commit()
        if kind == "clinical" and st == "current":           # S779: the diagnoses, at once (fail-soft: never refuses the export)
            try:
                if HERE not in sys.path:
                    sys.path.insert(0, HERE)
                import dx_feed                                # noqa: PLC0415
                dx_feed.run(con)
            except Exception as ex:                          # noqa: BLE001
                note = (note + "; " if note else "") + "diagnosis feed: %s" % str(ex)[:120]
    return kind, day, nrows, st, note
'''),
]
for a, c in E:
    assert b.count(a) == 1, "anchor not unique: " + a[:60]
    b = b.replace(a, c)
open(out, "w", encoding="utf-8", newline="").write(b)
print(hashlib.md5(open(out, "rb").read()).hexdigest())
