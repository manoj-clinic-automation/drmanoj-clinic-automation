"""make_s508.py -- S508_EXPORTS_CONFIRMED. Builds aaj_kaam.py and aaj_kaam.html from the live bytes by exact, counted edits.
    python3 make_s508.py <live dir> <out dir>"""
import hashlib
import os
import sys

PINS = {"aaj_kaam.py": "e8517623d1b8946eb7b7779e83f817ad", "aaj_kaam.html": "d7c9c38bbf3f96beba9d6167b1bd466e"}


def rep(s, a, b, what):
    n = s.count(a)
    assert n == 1, "%s: anchor found %d times: %r" % (what, n, a[:70])
    return s.replace(a, b)


def build(live, out):
    got = {}
    for name, pin in PINS.items():
        b = open(os.path.join(live, name), "rb").read()
        assert hashlib.md5(b).hexdigest() == pin, "%s: FROM pin differs" % name
        got[name] = b.decode("utf-8")
    s = got["aaj_kaam.py"]
    s = rep(s, '''def person_list(rd, doc, view_as=False):''', '''# S508 (the owner, 10-Oct-2026: staff want a CONFIRMATION that both evening Docterz exports are done) -- a line whose work is
# done may say so, in green, instead of vanishing. One line has it today: reception's 'Jaane se pehle: dono report'.
def _exports_confirmed(rd):
    """After 19:00 on a working day, when today's consultation report AND a follow-up log that reaches the next call day are
    both on the server: the words reception reads, with the patients counted and the times. None otherwise (the job line,
    or nothing before 19:00)."""
    if rd.now.hour < 19 or rd.today.weekday() == 6:
        return None
    con = rd.raw or rd.con
    try:
        day = rd.today.isoformat()
        cols = {r[1] for r in con.execute("PRAGMA table_info(docterz_export)")}
        c = con.execute("SELECT rows, taken_at FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current' "
                        "ORDER BY id DESC LIMIT 1", (day,)).fetchone()
        f = con.execute("SELECT rows, taken_at%s FROM docterz_export WHERE kind='followup' AND business_date=? AND status='current' "
                        "ORDER BY id DESC LIMIT 1" % (", due_to" if "due_to" in cols else ""), (day,)).fetchone()
    except sqlite3.Error:
        return None
    if not c or not f:
        return None
    nxt = rd.today + dt.timedelta(days=1)
    if nxt.weekday() == 6:
        nxt += dt.timedelta(days=1)
    due_to = f[2] if len(f) > 2 else ""
    if due_to and due_to < nxt.isoformat():
        return None                                                   # a short log is not done (S507): the job line stays
    hm = lambda t: str(t or "")[11:16]                                 # noqa: E731
    return ("Aaj ki dono Docterz report server par aa gayi ✓ -- Consultation: %d patient (%s) · Follow-up log%s (%s)"
            % (int(c[0] or 0), hm(c[1]), (" %s tak" % dm(due_to)) if due_to else "", hm(f[1])))


CONFIRM = {"reception.night_exports": _exports_confirmed}


def person_list(rd, doc, view_as=False):''', "confirm function")
    s = rep(s, '''            if not st["due"]:
                continue                                               # nothing there -- or only work from before the floor (held)''',
            '''            if not st["due"]:
                ok = CONFIRM[ln["id"]](rd) if ln["id"] in CONFIRM else None   # S508: done, said in green
                if ok:
                    secs[when].append(dict(id=ln["id"], kind="done", text=ok, how="", door=None, tile=None, done=None))
                continue                                               # nothing there -- or only work from before the floor (held)''',
            "person_list")
    h = got["aaj_kaam.html"]
    h = rep(h, '''    else if(r.door)opener('');
    if(acts.childNodes.length)w.appendChild(acts);''', '''    else if(r.kind==='done'){ w.className='row done'; }        /* S508: the work is done, said in green -- nothing to press */
    else if(r.door)opener('');
    if(acts.childNodes.length)w.appendChild(acts);''', "html row")
    h = rep(h, '''.row.done .ok{flex-basis:100%;text-align:left}''', '''.row.done .ok{flex-basis:100%;text-align:left}
.row.done .tx:only-child{color:#2f6b45;font-weight:600}''', "html css")
    os.makedirs(out, exist_ok=True)
    for name, text in (("aaj_kaam.py", s), ("aaj_kaam.html", h)):
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(text.encode("utf-8"))
        print("built %s %s" % (name, hashlib.md5(text.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
