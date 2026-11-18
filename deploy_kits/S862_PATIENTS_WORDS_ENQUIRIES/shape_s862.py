#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""shape_s862.py -- kit S862 (S480, 18-Nov-2026): the LIVE SHAPE on COPIES of the live stores (the box makes the copies).
    python3 shape_s862.py <new_code_dir> <old_code_dir> <finance.db copy> <console.db copy or -> <calls_console.py>
Counts only; prints no word, name, number or ID. 1) the new reading's Part 1 equals the old one's in every block but the
words; 2) the words rows cover every unrecognised visit once; 3) the became block reads (when a call record is given) and its
lists hold clinic IDs only; 4) a Place of the largest row on a SECOND copy moves exactly its visits and changes no other table
(then Undo puts every visit back). Last line "SHAPE OK ..." or "SHAPE FAIL ..."."""
import datetime as dt
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

NEW, OLD, FDB, CDB, CC = sys.argv[1:6]
try:
    _ME = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _ME = None
WORK = tempfile.mkdtemp(prefix="shape862_")
F = []


def chk(name, cond, extra=""):
    print("  %s %s%s" % ("ok " if cond else "BAD", name, (" -- " + str(extra)[:200]) if extra else ""))
    if not cond:
        F.append(name)


def run_read(code, tag):
    """read() in a child python on the given code (so old and new never share a module)."""
    out = os.path.join(WORK, tag + ".json")
    prog = ("import sys,json,sqlite3,datetime as dt;sys.path[:0]=[%r];import patients_page as pp;"
            "c=sqlite3.connect('file:%%s?mode=ro'%%%r,uri=True);r,l=pp.read(c,today=dt.date.today());"
            "json.dump(dict(r=r,lk=sorted(l),bec=[x for k,v in l.items() if k.startswith(('bec:','rf:')) for x in v]),open(%r,'w'))") % (code, FDB, out)
    env = dict(os.environ, PATIENTS_READING=os.path.join(WORK, tag + ".dat"), PATIENTS_CONSOLE_DB=(CDB if CDB != "-" else "/nonexistent/c.db"),
               PATIENTS_CALLS_CONSOLE=CC)
    p = subprocess.run([sys.executable, "-B", "-c", prog], cwd=WORK, env=env, capture_output=True, text=True, timeout=600)
    if p.returncode:
        return None, p.stderr[-300:]
    return json.load(open(out)), ""


new, e1 = run_read(NEW, "new")
old, e2 = run_read(OLD, "old")
chk("both readings build", new is not None and old is not None, e1 or e2)
if new and old:
    rn, ro = new["r"], old["r"]
    skip = {"words", "built", "took", "version", "p2", "readings", "glance"}
    same = [k for k in ro if k not in skip and json.dumps(ro.get(k), sort_keys=True) == json.dumps(rn.get(k), sort_keys=True)]
    diff = [k for k in ro if k not in skip and k not in same]
    chk("Part 1 identical in every block but the words (%d blocks)" % len(same), not diff, diff)
    chk("the readings-and-suggestions lines identical", json.dumps(ro.get("readings"), sort_keys=True) ==
        json.dumps(rn.get("readings"), sort_keys=True) or CDB != "-", "")
    W = rn.get("words") or {}
    rows = W.get("rows") or []
    chk("words rows cover every unrecognised word once (%d words in %d rows)" % (W.get("n", 0), len(rows)),
        sum(len(r["words"]) for r in rows) == W.get("n") and sum(r["n"] for r in rows) == W.get("visits"))
    chk("every row's suggestion is one of the choices (or none)", all(r["sug"] in {c["std"] for c in W.get("choices") or []} | {""} for r in rows))
    print("  -- %d words, %d visits, %d rows, %d with a suggestion, %d placed" % (W.get("n", 0), W.get("visits", 0), len(rows),
          sum(1 for r in rows if r["sug"]), len(W.get("placed") or [])))
    if CDB != "-":
        B = (rn.get("p2") or {}).get("became") or {}
        chk("became block reads", B.get("ok") is True, B.get("why"))
        chk("became lists hold clinic IDs and days only", all(len(x) == 3 and str(x[0]).isdigit() and len(str(x[1])) == 10 for x in new["bec"]))
        for ym, b in sorted((B.get("months") or {}).items()):
            print("  -- %s callers %s, became %s, new %s, rang first %s of %s%s" % (ym, b["callers"], b["became"], b["newp"], b["rang"], b["rang_base"],
                  "" if b["complete"] else " (so far)"))
    # a Place and its Undo on a second copy
    if rows:
        cp = os.path.join(WORK, "second.db")
        s = sqlite3.connect("file:%s?mode=ro" % FDB, uri=True)
        d = sqlite3.connect(cp)
        s.backup(d)
        s.close()
        d.close()

        def tables(path):
            c = sqlite3.connect(path)
            out = {}
            for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
                h = hashlib.md5()
                for r in c.execute('SELECT * FROM "%s" ORDER BY 1' % t.replace('"', '""')):
                    h.update(repr(r).encode())
                out[t] = h.hexdigest()
            c.close()
            return out
        t0 = tables(cp)
        sys.path[:0] = [NEW]
        os.environ["PATIENTS_READING"] = os.path.join(WORK, "second.dat")
        os.environ["PATIENTS_CONSOLE_DB"] = CDB if CDB != "-" else "/nonexistent/c.db"   # review 6: the copy, never the live file
        os.environ["PATIENTS_CALLS_CONSOLE"] = CC
        import patients_page as pp                                      # noqa: E402
        con = sqlite3.connect(cp)
        top = max(rows, key=lambda r: r["n"])
        std = top["sug"] or (W.get("choices") or [{}])[0].get("std")
        res = pp.place_words(con, [w["word"] for w in top["words"]], std, "shape862")
        chk("Place of the largest row moves exactly its visits (%d)" % top["n"], res["moved"] == top["n"] and res["placed"] == len(top["words"]), res)
        t1 = tables(cp)
        chk("only dx_visit and dx_term_map changed", sorted(k for k in t0 if t0[k] != t1.get(k)) == ["dx_term_map", "dx_visit"] or
            sorted(k for k in t0 if t0[k] != t1.get(k)) == ["dx_visit"], sorted(k for k in t0 if t0[k] != t1.get(k)))
        moved = 0
        for (k,) in con.execute("SELECT term FROM dx_term_map WHERE set_by='shape862'").fetchall():
            moved += pp.unplace_word(con, k)["moved"]
        con.close()
        t2 = tables(cp)
        chk("Undo puts every visit back (dx_visit as before but its 'updated_at')", moved == top["n"], moved)
        c2 = sqlite3.connect(cp)
        c0 = sqlite3.connect("file:%s?mode=ro" % FDB, uri=True)
        q = "SELECT patient_uid, visit_date, std_dx, category FROM dx_visit ORDER BY 1, 2"
        chk("dx_visit's diagnoses as on the live copy after the Undo", c2.execute(q).fetchall() == c0.execute(q).fetchall())
        chk("every other table untouched", {k: v for k, v in t2.items() if k not in ("dx_visit", "dx_term_map")} ==
            {k: v for k, v in t0.items() if k not in ("dx_visit", "dx_term_map")})
shutil.rmtree(WORK, ignore_errors=True)
print("SHAPE OK" if not F else "SHAPE FAIL: %s" % "; ".join(F))
sys.exit(0 if not F else 1)
