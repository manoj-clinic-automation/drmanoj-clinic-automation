"""cfg_s553.py -- kit S553_BHATI_SLIP_DUTY, the data step (idempotent).
    python3 -B cfg_s553.py <finance.db>          puts Bhati's new line on his SAVED panel, switched on, if he has one
    python3 -B cfg_s553.py --line                prints the line as JSON (the walk compares it with aaj_seed.py's)
WHY: aaj_kaam._merge adds a seed line the owner has never seen to a SAVED panel switched OFF (marked new). The owner's word
(14-Oct-2026 05:43 IST) is that Bhati's slip entry goes ON his list, so where a saved panel for 'bhati' exists in aaj_cfg the
line is appended to it, switched on -- exactly what his own tap on the panel would store. Nothing else is touched:
  * no aaj_cfg table, or no row for 'bhati' -> nothing to do (the seed's line is on by itself);
  * the line already on his panel, or in its 'removed' list (he took it off) -> nothing to do: his word stands;
  * a damaged row -> left alone (aaj_kaam keeps that person's list off until his next save repairs it).
The row's edited_at is moved to now, so a panel left open on another screen is told 'stale' and reloads instead of saving
over the line. Prints one line: what it did."""
import datetime as dt
import json
import sqlite3
import sys

LINE = {"id": "bhati.physio_register",
        "hi": "Physio slips register mein likhiye — reception ke hisaab se nahin mil rahi",
        "en": "Bhati: physiotherapy slips of a day not entered in his register, or not agreeing with reception. Opens that day.",
        "when": "day", "on": True}


def run(db):
    con = sqlite3.connect(db, timeout=60)
    try:
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='aaj_cfg'").fetchone() is None:
            return "data step: no saved panels (aaj_cfg not there) -- the seed's line shows switched on by itself; 0 changed"
        r = con.execute("SELECT doc, edited_at FROM aaj_cfg WHERE person='bhati'").fetchone()
        if r is None:
            return "data step: no saved panel for bhati -- the seed's line shows switched on by itself; 0 changed"
        try:
            doc = json.loads(r[0])
            if not isinstance(doc, dict) or not isinstance(doc.get("lines", []), list):
                raise ValueError("not a document")
        except (TypeError, ValueError):
            return "data step: bhati's saved panel is damaged -- left alone (his list stays off until the owner saves it); 0 changed"
        ids = {str(x.get("id")) for part in ("lines", "removed") for x in (doc.get(part) or []) if isinstance(x, dict)}
        if LINE["id"] in ids:
            return "data step: bhati.physio_register is already on bhati's saved panel (or taken off by the owner) -- left as it is; 0 changed"
        doc.setdefault("lines", []).append(dict(LINE))
        cur = con.execute("UPDATE aaj_cfg SET doc=?, edited_at=? WHERE person='bhati' AND doc=?",
                          (json.dumps(doc, ensure_ascii=False), dt.datetime.now().isoformat(), r[0]))
        con.commit()
        if cur.rowcount != 1:
            return "data step: bhati's saved panel changed while this ran -- not written; 0 changed (run the installer again)"
        return "data step: bhati.physio_register appended to bhati's saved panel, switched on; 1 changed"
    finally:
        con.close()


if __name__ == "__main__":
    if sys.argv[1:2] == ["--line"]:
        print(json.dumps(LINE, ensure_ascii=False))
    else:
        print(run(sys.argv[1]))
