"""cfg_s687.py -- kit S687_DARPAN_MONTH_JOBS, the data step (idempotent).
    python3 -B cfg_s687.py <finance.db> <finance dir>   makes the mj_* tables (month_jobs.ensure, from <finance dir>) and puts
                                                       Darpan's four new lines on his SAVED panel, switched on, if he has one
    python3 -B cfg_s687.py --lines                     prints the four lines as JSON (the walk compares them with aaj_seed.py's)
WHY THE TABLES HERE TOO: the four Aaj lines read the mj_* tables; until they exist each line is UNREAD (F-1024: a list with
an unread line says it is not whole). month_jobs.py makes them on its first request; this step makes them at install, with
the same CREATE ... IF NOT EXISTS, so Darpan's list is whole from the first minute. Additive only.
WHY THE PANEL: aaj_kaam._merge adds a seed line the owner has never seen to a SAVED panel switched OFF (marked new). The owner's
word (31-Oct-2026) is that these jobs go ON Darpan's list, so where a saved panel for 'darpan' exists in aaj_cfg each missing
line is appended, switched on -- what his own tap on the panel would store. Nothing else is touched:
  * no aaj_cfg table, or no row for 'darpan' -> nothing to do (the seed's lines are on by themselves);
  * a line already on his panel, or in its 'removed' list (he took it off) -> left as it is: his word stands;
  * a damaged row -> left alone (aaj_kaam keeps that list off until the owner's next save repairs it).
edited_at moves to now, so a panel left open on another screen is told 'stale' and reloads. Prints one line: what it did."""
import datetime as dt
import json
import os
import sqlite3
import sys

LINES = [
    {"id": "darpan.home_meds", "hi": "Home medicines — ginti", "when": "month", "on": True,
     "en": "From the last 7 days of the month: what is left at home of each medicine on your list; the page works out what to order."},
    {"id": "darpan.vehicle_check", "hi": "Gaadi ki jaanch — kaagaz, stepney, jack aur paana", "when": "month", "on": True,
     "en": "Month end: each vehicle's papers, and the stepney and jack on Wagon R and Vento -- Hai / Nahi."},
    {"id": "darpan.expiry_clear", "hi": "Expiry ki safai", "when": "month", "on": True,
     "en": "Month end: each expired line of Sanjeevni's newest expiry list -- returned to the supplier, destroyed, or not found."},
    {"id": "darpan.paper_renewal", "hi": "Kaagaz ki yaad", "when": "comeup", "on": True,
     "en": "A vehicle paper inside its reminder time (pollution 7 days, insurance 1 month, RC 45 days) until you enter the new date."},
]


def tables(db, fin):
    import importlib.util                                              # noqa: PLC0415 -- the PLACED module's own schema, by its path
    spec = importlib.util.spec_from_file_location("month_jobs_s687_cfg", os.path.join(os.path.abspath(fin), "month_jobs.py"))
    month_jobs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(month_jobs)
    con = sqlite3.connect(db, timeout=60)
    try:
        before = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        month_jobs.ensure(con)
        after = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    finally:
        con.close()
    made = sorted(after - before)
    return "tables: %d made (%s)" % (len(made), ", ".join(made) or "all there already")


def panel(db):
    con = sqlite3.connect(db, timeout=60)
    try:
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='aaj_cfg'").fetchone() is None:
            return "panel: no saved panels (aaj_cfg not there) -- the seed's lines show switched on; 0 changed"
        r = con.execute("SELECT doc, edited_at FROM aaj_cfg WHERE person='darpan'").fetchone()
        if r is None:
            return "panel: no saved panel for darpan -- the seed's lines show switched on by themselves; 0 changed"
        try:
            doc = json.loads(r[0])
            if not isinstance(doc, dict) or not isinstance(doc.get("lines", []), list):
                raise ValueError("not a document")
        except (TypeError, ValueError):
            return "panel: darpan's saved panel is damaged -- left alone; 0 changed"
        ids = {str(x.get("id")) for part in ("lines", "removed") for x in (doc.get(part) or []) if isinstance(x, dict)}
        add = [dict(x) for x in LINES if x["id"] not in ids]
        if not add:
            return "panel: the four lines are already on darpan's saved panel (or taken off by the owner) -- left as they are; 0 changed"
        doc.setdefault("lines", []).extend(add)
        cur = con.execute("UPDATE aaj_cfg SET doc=?, edited_at=? WHERE person='darpan' AND doc=?",
                          (json.dumps(doc, ensure_ascii=False), dt.datetime.now().isoformat(), r[0]))
        con.commit()
        if cur.rowcount != 1:
            return "panel: darpan's saved panel changed while this ran -- not written; 0 changed (run the installer again)"
        return "panel: %d line(s) appended to darpan's saved panel, switched on; %d changed" % (len(add), len(add))
    finally:
        con.close()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--lines"]:
        print(json.dumps(LINES, ensure_ascii=False))
    elif len(sys.argv) == 3:
        print("data step: %s · %s" % (tables(sys.argv[1], sys.argv[2]), panel(sys.argv[1])))
    else:
        raise SystemExit(__doc__)
