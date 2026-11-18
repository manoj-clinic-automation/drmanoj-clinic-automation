#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s873.py -- kit S873 (the parent, S480, 18-Nov-2026). On a MADE-UP shelf (an empty sqlite built by packs.ensure; the
PDF reader stood in for -- no real file, no real number): a card statement with NO password in a card folder is read; a truly
locked one stays 'locked original'; neither is picked again; an undated one says so; the bank's locked copy with its
decrypted twin is unchanged; the month's card cell reads 'read'. Control: the live packs.py goes red.
    python3 walk_s873.py <dir holding packs.py> <scratch>          last line 'WALK n/m'"""
import os
import sqlite3
import sys

d, scr = sys.argv[1:3]
here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != here]          # F-1441: never the kit's own copy by accident
sys.path.insert(0, d)
os.makedirs(scr, exist_ok=True)
ok, n = 0, 0


def chk(name, cond, info=""):
    global ok, n
    n += 1
    ok += bool(cond)
    print(("ok   " if cond else "FAIL ") + name + (("  [" + str(info)[:150] + "]") if (info and not cond) else ""))


try:
    import packs as p
except Exception as e:                                   # noqa: BLE001
    print("FAIL import packs: %s" % e)
    print("WALK 0/9")
    sys.exit(1)

db = os.path.join(scr, "made_up_s873.db")
if os.path.exists(db):
    os.remove(db)
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
p.ensure(con)
sid = {r["key"]: r["id"] for r in con.execute("SELECT id, key FROM stmt_slot WHERE kind='card'")}

# the stand-in reader: a file's "text" is its made-up path's tag
TEXT = {"/made/up/web.pdf": ("WEB", False), "/made/up/locked.pdf": ("", True), "/made/up/nodate.pdf": ("NODATE", False),
        "/made/up/mail.pdf": ("", True), "/made/up/dec.pdf": ("DEC", False)}
CARD = {"WEB": dict(statement_date="2031-10-12", period_from="2031-09-13", period_to="2031-10-12", tails=["0000"]),
        "DEC": dict(statement_date="2031-11-12", period_from="2031-10-13", period_to="2031-11-12", tails=["0000"]),
        "NODATE": dict(statement_date=None, period_from=None, period_to=None, tails=[])}
p._file_text = lambda lp: TEXT.get(lp, ("", False))
p.card_read = lambda text: (dict(CARD[text]) if text in CARD else None)
p.place = lambda con_, ident: (None, "made-up: no words matched")


def add(name, folder, sub, rs, locked, lp, slot="card_icici_amazon", pt="2031-10-11", mt="2031-11-17T04:38:00"):
    cur = con.execute("INSERT INTO stmt_file (drive_id, name, mtime, size, folder, subfolder, slot_id, period_from, period_to, read_status, "
                "matched_status, locked, unlocked_path, local_path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                ("made-up-%s-%s" % (folder, name), name, mt, 1000, folder, sub, sid[slot] if slot else None, None, pt,
                 rs, "decrypted copy not yet made", locked, None, lp))
    return cur.lastrowid


f_web = add("CreditCardStatement.pdf", "cards", "ICICI Amazon Pay", "locked original", 0, "/made/up/web.pdf",
            mt="2031-11-18T04:38:00")                    # the newest card-folder file, newer than any decrypted copy
f_lock = add("2031-11-14_mail_locked.pdf", "cards", "ICICI Amazon Pay", "locked original", 0, "/made/up/locked.pdf")
f_nod = add("undated.pdf", "cards", "ICICI Amazon Pay", "locked original", 0, "/made/up/nodate.pdf")
f_gone = add("gone.pdf", "cards", "ICICI Amazon Pay", "locked original", 0, "/made/up/not-on-disk.pdf")
f_mail = add("2031-11-14_twin.pdf", "cards", "ICICI Amazon Pay", None, 0, "/made/up/mail.pdf")
f_dec = add("2031-11-14_twin.pdf", "decrypted", "ICICI Amazon Pay", "read", 0, "/made/up/dec.pdf", pt="2031-11-12",
            mt="2031-11-14T04:38:00")                    # November's, and OLDER than the downloaded one (review SHOULD 1)
con.commit()

r1 = p._process_once(con)
row = lambda i: dict(con.execute("SELECT * FROM stmt_file WHERE id=?", (i,)).fetchone())          # noqa: E731
w = row(f_web)
chk("W1 the statement downloaded from the bank (no password) is READ", w["read_status"] == "read", (w["read_status"], w["matched_status"]))
chk("W2 ... its words say so, and its dates are kept", "no password" in (w["matched_status"] or "") and w["period_from"] == "2031-09-13"
    and w["period_to"] == "2031-10-12", (w["matched_status"], w["period_from"], w["period_to"]))
lk = row(f_lock)
chk("W3 a truly locked mail copy stays 'locked original', now marked locked", lk["read_status"] == "locked original" and lk["locked"] == 1,
    (lk["read_status"], lk["locked"]))
nd = row(f_nod)
chk("W4 no password but no date: says so (never 'locked')", nd["read_status"] == "n/a" and "date could not be read" in (nd["matched_status"] or ""),
    (nd["read_status"], nd["matched_status"]))
ml = row(f_mail)
chk("W5 the bank's locked copy with its decrypted twin: a duplicate, as before", ml["read_status"] == p.DUP_OF_DECRYPTED, ml["read_status"])
gn = row(f_gone)
chk("W4b a file that cannot be opened at all: says so (never 'locked')", gn["read_status"] == "n/a" and "could not be opened" in (gn["matched_status"] or ""),
    (gn["read_status"], gn["matched_status"]))
r2 = p._process_once(con)
chk("W6 a second run picks none of them again", sum(r2.values()) == 0, r2)
try:
    cl = {c["slot"]: c for c in p.cells(con, "2031-10") if c["kind"] == "card"}
    c = cl.get("card_icici_amazon") or {}
    chk("W7 October's Amazon Pay cell is read -- from the downloaded statement", c.get("state") == "read"
        and ((c.get("file") or {}).get("id") == f_web), {k: c.get(k) for k in ("state", "note", "file")})
    chk("W7b ... and says nothing of a lock or a missing decrypted copy", "lock" not in str(c.get("note") or "").lower()
        and not c.get("twin_missing"), {k: c.get(k) for k in ("note", "twin_missing", "no_decrypted")})
except Exception as e:                                   # noqa: BLE001
    chk("W7 the month's cells could be made", False, "%s: %s" % (type(e).__name__, e))
dd = row(f_dec)
chk("W8 the decrypted copy untouched", dd["read_status"] == "read")
chk("W9 the first run read one, refused none", r1.get("read", 0) >= 1, r1)
con.close()
print("WALK %d/%d" % (ok, n))
sys.exit(0 if ok == n else 1)
