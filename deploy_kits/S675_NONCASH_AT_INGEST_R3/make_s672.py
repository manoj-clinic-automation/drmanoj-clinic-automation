"""make_s672.py -- kit S672_NONCASH_AT_INGEST (Sanjeevni session S361, 28-Oct-2026). F-1037.
The owner, 08:53 IST 28-Oct: procedure bill A004474 (27-Oct, Rs 98, "PROSIJER <patient>") was not counted by the system.
Cause: the home / procedure deduction (day_noncash_bill) was made ONLY by day_resync pass 2, every 30 minutes, and ONLY on an
unapproved day. The 27-Oct export landed ~08:31 IST, after the 08:30 run; the day was approved before 09:00; the job never
touches an approved day, so the bill was never deducted (expected cash read Rs 98 high).
The fix: the deduction is made INSIDE the sale ingest, in the same transaction, the moment a pharmacy day's bills land.
  /root/finance/day_resync.py      c62e98b9 -> TO  noncash_day(..., commit=True, via=None); NEW at_ingest(con, unit, business_date):
        an unapproved medical day since 2026-09-01, the Sanjeevni switch not OFF -> noncash_day(apply=True, commit=False). Never commits.
  /root/finance/finance_ingest.py  d7b07fb6 -> TO  ONE counted edit at the end of ingest_day: day_resync.at_ingest under a SAVEPOINT,
        fail-soft (any error is rolled back to the savepoint and the ingest goes on exactly as before).
Usage: python make_s672.py <live root, e.g. /root> <out dir>"""
import hashlib, os, sys

FROM = {"finance/day_resync.py": "c62e98b971fab7c6802b74b9029c291e",
        "finance/finance_ingest.py": "d7b07fb6514da7129b969b878ce5fbbd"}
src, out = sys.argv[1], sys.argv[2]
T = {}
for r, h in FROM.items():
    b = open(os.path.join(src, r), "rb").read()
    assert hashlib.md5(b).hexdigest() == h, "the live %s is not %s" % (r, h[:8])
    T[r] = b.decode("utf-8")


def rep(r, old, new):
    assert T[r].count(old) == 1, "%s: anchor not found exactly once: %s" % (r, old[:80])
    T[r] = T[r].replace(old, new, 1)


D = "finance/day_resync.py"
rep(D, '''Marg's latest bills and the bank, and carries its home / procedure medicine bills and their credit notes.
''', '''Marg's latest bills and the bank, and carries its home / procedure medicine bills and their credit notes.

S672 (F-1037, the owner 28-Oct-2026: "one procedure bill ... was not mentioned by the system" -- A004474 of 27-Oct, Rs 98)
    Pass 2 runs every 30 minutes and only on an unapproved day. The 27-Oct export landed at 08:31, after the 08:30 run; the
    day was approved before 09:00, so the bill was never deducted. at_ingest() now makes the same rows INSIDE the sale ingest
    (finance_ingest.ingest_day), in the ingest's own transaction, so a day can no longer be seen -- or approved -- before
    its home / procedure bills are deducted. Pass 2 stays as the safety net (it finds them PRESENT).
''')
rep(D, '''def noncash_day(con, e, home_w, proc_w, apply):''',
       '''def noncash_day(con, e, home_w, proc_w, apply, commit=True, via=None):''')
rep(D, '''"from Marg's customer text (%s), %s" % (where, KIT), WHO, now,''',
       '''"from Marg's customer text (%s), %s" % (where, via or KIT), WHO, now,''')
rep(D, '''                                      kit=KIT)), WHO, now))
    con.commit()
    return "ADDED", line''', '''                                      kit=via or KIT)), WHO, now))
    if commit:
        con.commit()
    return "ADDED", line''')
rep(D, '''def main(argv=None):''', '''KIT_INGEST = "S672 at ingest"
INGEST_SINCE = "2026-09-01"


def at_ingest(con, unit, business_date):
    """S672 (F-1037): called by finance_ingest.ingest_day once a day's bills are written, inside its transaction.
    For an UNAPPROVED pharmacy day (submitted / draft) since INGEST_SINCE, and only while the Sanjeevni switch is not OFF:
    pass 2's own rows (noncash_day), at once. NEVER commits -- the caller's commit (or rollback) carries them.
    Returns pass 2's verdict, or None when nothing was looked at."""
    if unit != UNIT or switched_off() or str(business_date or "") < INGEST_SINCE:
        return None
    rf = con.row_factory
    con.row_factory = sqlite3.Row
    try:
        if not (_has(con, "day_noncash_bill") and _has(con, "day_entry")):
            return None
        e = con.execute("SELECT id, business_date, status FROM day_entry WHERE unit=? AND business_date=?",
                        (UNIT, business_date)).fetchone()
        if e is None or e["status"] not in ("submitted", "draft"):
            return None
        home_w = words(con, "noncash.home_words", HOME_DEFAULT)
        proc_w = words(con, "noncash.proc_words", PROC_DEFAULT)
        v, _line = noncash_day(con, e, home_w, proc_w, apply=True, commit=False, via=KIT_INGEST)
        return v
    finally:
        con.row_factory = rf


def main(argv=None):''')

I = "finance/finance_ingest.py"
rep(I, '''    reconcile_day_attribution(con, unit, business_date, now)
    if commit:
        con.commit()
''', '''    reconcile_day_attribution(con, unit, business_date, now)
    # S672 (F-1037): a pharmacy day's home / procedure medicine bills are deducted HERE, in this transaction, not
    # half an hour later by day_resync -- an approval in between left A004474 (27-Oct) undeducted for good.
    # Fail-soft: anything wrong is rolled back to the savepoint and the ingest stands exactly as before.
    try:
        con.execute("SAVEPOINT s672_noncash")
        try:
            import day_resync as _dr672                                   # noqa: PLC0415
            _dr672.at_ingest(con, unit, business_date)
            con.execute("RELEASE SAVEPOINT s672_noncash")
        except Exception:                                                 # noqa: BLE001
            con.execute("ROLLBACK TO SAVEPOINT s672_noncash")
            con.execute("RELEASE SAVEPOINT s672_noncash")
    except Exception:                                                     # noqa: BLE001
        pass
    if commit:
        con.commit()
''')

for r, t in T.items():
    p = os.path.join(out, r)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "wb").write(t.encode("utf-8"))
    print("%s %s -> %s" % (r, FROM[r][:8], hashlib.md5(t.encode("utf-8")).hexdigest()))
