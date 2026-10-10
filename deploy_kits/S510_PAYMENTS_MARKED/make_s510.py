"""make_s510.py -- S510_PAYMENTS_MARKED. Builds packs.py and payments_register.py from the live bytes by exact edits.
    python3 make_s510.py <live dir> <out dir>"""
import hashlib
import os
import sys

PINS = {"packs.py": "2a7c2a63e734293751926fa0be49d421", "payments_register.py": "fa12a0a1911c401fd826ccc2342c34d5"}


def rep(s, a, b, what):
    n = s.count(a)
    assert n == 1, "%s: anchor found %d times: %r" % (what, n, a[:70])
    return s.replace(a, b)


def build(live, out):
    got = {}
    for name, pin in PINS.items():
        b = open(os.path.join(live, name), "rb").read()
        assert pin is None or hashlib.md5(b).hexdigest() == pin, "%s: FROM pin differs" % name
        got[name] = b.decode("utf-8")
    s = got["packs.py"]
    s = rep(s, '''        why = None
        if "APPOINTMENT" in up:''', '''        why = None
        if desc.startswith("[NOT A PAYMENT]"):                         # S510: the Janitor's own mark (v2.4, 10-Oct-2026)
            why = "marked not a payment in the sheet"
        elif desc.startswith("[DUPLICATE"):
            why = "the same mail twice (marked in the sheet)"
        elif "APPOINTMENT" in up:''', "digest marks")
    p = got["payments_register.py"]
    p = rep(p, '''                    drift.append((row_no, f, old[f], rec[f]))
                    con.execute(
                        "INSERT INTO payment_register_drift(at,row_no,field,"
                        "was,now) VALUES(?,?,?,?,?)",
                        (now, row_no, f,
                         None if old[f] is None else str(old[f]),
                         None if rec[f] is None else str(rec[f])))''', '''                    was = None if old[f] is None else str(old[f])
                    if f == "description" and str(rec[f] or "").startswith(PHI_GONE):
                        was = PHI_WAS                                  # S510: the patient's name is not kept as history
                    drift.append((row_no, f, was, rec[f]))
                    con.execute(
                        "INSERT INTO payment_register_drift(at,row_no,field,"
                        "was,now) VALUES(?,?,?,?,?)",
                        (now, row_no, f, was,
                         None if rec[f] is None else str(rec[f])))''', "drift")
    p = rep(p, '''CREATE TABLE IF NOT EXISTS payment_register_drift (''', '''CREATE TABLE IF NOT EXISTS payment_register_drift (''', "ddl check")
    p = rep(p, '''def open_db(path, readonly=False):''', '''# S510 (10-Oct-2026): the Inbox Janitor v2.4 replaced the description of every Docterz notification row (patient names) with
# words that name no one. The drift table would keep the old words as 'was' -- the patient's name, as history. It never does:
# such a change is recorded as PHI_WAS, and any older record of it is scrubbed on every run (the one-time correction is part of
# the design).
PHI_GONE = "[NOT A PAYMENT] Docterz notification"
PHI_WAS = "(a Docterz notification -- the patient's details were removed from the sheet)"


def scrub_phi(con):
    cur = con.execute("UPDATE payment_register_drift SET was=? WHERE field='description' AND now LIKE ? AND COALESCE(was,'')<>?",
                      (PHI_WAS, PHI_GONE + "%", PHI_WAS))
    return cur.rowcount or 0


def open_db(path, readonly=False):''', "phi helpers")
    p = rep(p, '''    gone = sorted(set(have) - {r for r, _ in rows})''', '''    scrub_phi(con)                                                    # S510
    gone = sorted(set(have) - {r for r, _ in rows})''', "scrub call")
    os.makedirs(out, exist_ok=True)
    for name, text in (("packs.py", s), ("payments_register.py", p)):
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(text.encode("utf-8"))
        print("built %s %s" % (name, hashlib.md5(text.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
