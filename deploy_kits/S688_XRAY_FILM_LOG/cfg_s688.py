"""cfg_s688.py -- kit S688_XRAY_FILM_LOG, the data step (idempotent).
    python3 -B cfg_s688.py <finance.db> <finance dir> [--record <file>]
                                                       makes the xf_* tables (xray_film.ensure, from <finance dir>: the seed of
                                                       the studies' film sizes and the one supplier row come with them) and puts
                                                       the new lines on Shavez's and Reception's SAVED panels, switched on, if
                                                       they have one; and takes the RETIRED weekly line reception.week_film_stock
                                                       off every saved panel (its lines and its 'removed' list); --record writes
                                                       exactly what it did (JSON {"added": {person: [ids]}, "retired": {person:
                                                       [[part, index, line]]}}), rewritten after each commit
    python3 -B cfg_s688.py --undo <finance.db> <file>  a red install: takes off exactly the lines the record says were added, and
                                                       puts each retired line back exactly where it was
    python3 -B cfg_s688.py --lines                     prints the lines as JSON (the walk compares them with aaj_seed.py's)
WHY THE TABLES HERE TOO: the four Aaj duties read the xf_* tables; until they exist each line is UNREAD (F-1024: a list with
an unread line says it is not whole). xray_film.py makes them on its first request; this step makes them at install, with
the same CREATE ... IF NOT EXISTS, so every list is whole from the first minute. Additive only.
WHY THE PANELS: aaj_kaam._merge adds a seed line the owner has never seen to a SAVED panel switched OFF (marked new). The owner's
word (31-Oct-2026) is that these lines go ON, so where a saved panel for 'shavez' or 'reception' exists in aaj_cfg each
missing line is appended, switched on -- what his own tap on the panel would store. Nothing else is touched:
  * no aaj_cfg table, or no row for that person -> nothing to do (the seed's lines are on by themselves);
  * a line already on the panel, or in its 'removed' list (he took it off) -> left as it is: his word stands;
  * a damaged row -> left alone (aaj_kaam keeps that list off until the owner's next save repairs it).
THE RETIRED LINE (the owner, 20:20 IST 31-Oct-2026: "the machine shows the films loaded"): the weekly tick 'X-ray film ka stock
giniye' leaves the seed and the duties file in this kit; a saved panel still naming it would read it as a line with no duty
(UNREAD), so it is taken off every saved panel here too. Its duty_tick history rows are never touched.
edited_at moves to now, so a panel left open on another screen is told 'stale' and reloads. Prints one line: what it did."""
import datetime as dt
import json
import os
import sqlite3
import sys

RETIRED = "reception.week_film_stock"
LINES = {
    "shavez": [
        {"id": "shavez.xray_film_count", "hi": "X-ray film ginti: reception nahi hai to aap likhiye", "when": "day", "on": True,
         "en": "Stand-in: the morning film count, when reception has not saved it by 11:00."},
        {"id": "shavez.xray_film_order_8x10", "hi": "8×10 film mangwaiye — 1 box", "when": "comeup", "on": True,
         "en": "The 8×10 films left last under 10 days and no spare box: order one box. The page it opens says if a bill is still to be scanned."},
        {"id": "shavez.xray_film_order_11x14", "hi": "11×14 film mangwaiye — 1 box", "when": "comeup", "on": True,
         "en": "The 11×14 films left last under 10 days and no spare box: order one box. The page it opens says if a bill is still to be scanned."},
    ],
    "reception": [
        {"id": "reception.xray_film_count", "hi": "X-ray film: machine mein kitni film bachi hain, likhiye (dono size)", "when": "first", "on": True,
         "en": "Each morning: the films left on the Fuji machine's screen for 8×10 and 11×14, one Save."},
    ],
}


def tables(db, fin):
    import importlib.util                                              # noqa: PLC0415 -- the PLACED module's own schema, by its path
    spec = importlib.util.spec_from_file_location("xray_film_s688_cfg", os.path.join(os.path.abspath(fin), "xray_film.py"))
    xray_film = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(xray_film)
    con = sqlite3.connect(db, timeout=60)
    try:
        before = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        xray_film.ensure(con)
        after = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        seeded = con.execute("SELECT COUNT(*) FROM xf_study").fetchone()[0] if "xf_study" not in before else None
    finally:
        con.close()
    made = sorted(after - before)
    return "tables: %d made (%s)%s" % (len(made), ", ".join(made) or "all there already",
                                       ("; %d studies seeded" % seeded) if seeded is not None else "")


def panel_one(con, person):
    r = con.execute("SELECT doc, edited_at FROM aaj_cfg WHERE person=?", (person,)).fetchone()
    if r is None:
        return 0, "no saved panel for %s" % person, []
    try:
        doc = json.loads(r[0])
        if not isinstance(doc, dict) or not isinstance(doc.get("lines", []), list):
            raise ValueError("not a document")
    except (TypeError, ValueError):
        return 0, "%s's saved panel is damaged -- left alone" % person, []
    ids = {str(x.get("id")) for part in ("lines", "removed") for x in (doc.get(part) or []) if isinstance(x, dict)}
    add = [dict(x) for x in LINES[person] if x["id"] not in ids]
    if not add:
        return 0, "%s: the lines are already there (or taken off by the owner)" % person, []
    doc.setdefault("lines", []).extend(add)
    cur = con.execute("UPDATE aaj_cfg SET doc=?, edited_at=? WHERE person=? AND doc=?",
                      (json.dumps(doc, ensure_ascii=False), dt.datetime.now().isoformat(), person, r[0]))
    con.commit()
    if cur.rowcount != 1:
        return 0, "%s's saved panel changed while this ran -- not written (run the installer again)" % person, []
    return len(add), "%s: %d line(s) appended, switched on" % (person, len(add)), [x["id"] for x in add]


def retire(con, rec):
    """Takes the retired line off every saved panel ('lines' and 'removed'); rec[person] = [[part, index, line], ...]."""
    n = 0
    for person, d in list(con.execute("SELECT person, doc FROM aaj_cfg ORDER BY person")):
        try:
            doc = json.loads(d)
        except (TypeError, ValueError):
            continue
        if not isinstance(doc, dict):
            continue
        took = []
        for part in ("lines", "removed"):
            lst = doc.get(part)
            if not isinstance(lst, list):
                continue
            for i, x in enumerate(lst):
                if isinstance(x, dict) and x.get("id") == RETIRED:
                    took.append([part, i, x])
            doc[part] = [x for x in lst if not (isinstance(x, dict) and x.get("id") == RETIRED)]
        if not took:
            continue
        cur = con.execute("UPDATE aaj_cfg SET doc=?, edited_at=? WHERE person=? AND doc=?",
                          (json.dumps(doc, ensure_ascii=False), dt.datetime.now().isoformat(), person, d))
        con.commit()
        if cur.rowcount == 1:
            rec[person] = took
            n += 1
    return n


def panel(db, record=None):
    con = sqlite3.connect(db, timeout=60)
    added, retired = {}, {}

    def keep():
        if record:
            with open(record, "w", encoding="utf-8") as fh:
                json.dump({"added": added, "retired": retired}, fh, ensure_ascii=False)
    try:
        keep()
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='aaj_cfg'").fetchone() is None:
            return "panel: no saved panels (aaj_cfg not there) -- the seed's lines show switched on; 0 changed"
        nr = retire(con, retired)
        keep()
        n, words = 0, ["the retired weekly film-stock line taken off %d saved panel(s)" % nr]
        for person in LINES:
            k, w, ids = panel_one(con, person)
            if ids:
                added[person] = ids
                keep()
            n += k
            words.append(w)
        return "panel: %s; %d changed" % ("; ".join(words), n)
    finally:
        con.close()


def undo(db, record):
    """Takes off each panel exactly the lines `record` says this step added; prints what it did. Idempotent."""
    try:
        rec = json.load(open(record, encoding="utf-8"))
        added, retired = rec.get("added") or {}, rec.get("retired") or {}
    except (OSError, ValueError, AttributeError):
        return "undo: no record of added lines -- nothing taken off"
    con = sqlite3.connect(db, timeout=60)
    try:
        n, words = 0, []
        for person, ids in sorted(added.items()):
            r = con.execute("SELECT doc FROM aaj_cfg WHERE person=?", (person,)).fetchone()
            if r is None:
                continue
            doc = json.loads(r[0])
            before = len(doc.get("lines") or [])
            doc["lines"] = [x for x in (doc.get("lines") or []) if not (isinstance(x, dict) and x.get("id") in ids)]
            k = before - len(doc["lines"])
            if k:
                con.execute("UPDATE aaj_cfg SET doc=?, edited_at=? WHERE person=?", (json.dumps(doc, ensure_ascii=False), dt.datetime.now().isoformat(), person))
                con.commit()
            n += k
            words.append("%s: %d line(s) taken off" % (person, k))
        back = 0
        for person, took in sorted(retired.items()):
            r = con.execute("SELECT doc FROM aaj_cfg WHERE person=?", (person,)).fetchone()
            if r is None:
                continue
            doc = json.loads(r[0])
            for part, i, x in sorted(took, key=lambda t: (t[0], t[1])):
                lst = doc.setdefault(part, [])
                if not any(isinstance(y, dict) and y.get("id") == RETIRED for y in lst):
                    lst.insert(min(i, len(lst)), x)
                    back += 1
            con.execute("UPDATE aaj_cfg SET doc=?, edited_at=? WHERE person=?", (json.dumps(doc, ensure_ascii=False), dt.datetime.now().isoformat(), person))
            con.commit()
        words.append("the retired line put back on %d panel(s)" % len(retired))
        return "undo: %s; %d taken off; %d put back" % ("; ".join(words), n, back)
    finally:
        con.close()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--lines"]:
        print(json.dumps(LINES, ensure_ascii=False))
    elif sys.argv[1:2] == ["--undo"] and len(sys.argv) == 4:
        print(undo(sys.argv[2], sys.argv[3]))
    elif len(sys.argv) == 3 or (len(sys.argv) == 5 and sys.argv[3] == "--record"):
        print("data step: %s · %s" % (tables(sys.argv[1], sys.argv[2]), panel(sys.argv[1], sys.argv[4] if len(sys.argv) == 5 else None)))
    else:
        raise SystemExit(__doc__)
