#!/root/wa/venv/bin/python3
# =============================================================================
#  walk_s319.py  ·  S319_WITNESS_INFO  ·  v1
#
#  Runs THE REAL EXPRESSION, not a copy of it. The witness's one list
#  comprehension is lifted out of the file BY TEXT -- from the unpatched file and
#  from the patched one -- and executed against a scratch sqlite table shaped
#  like the live health_check_seen. That is the only honest way to test a change
#  inside a 686 KB module without importing the whole app: no reimplementation
#  can drift from what the file says if the file's own line is what runs.
#
#  Read-only against everything live: the scratch database is created in /tmp and
#  the live finance.db is never opened.
#
#  NEGATIVE CONTROLS: the same patched expression run with HEALTH_INFO_ONLY empty
#  must name the two rows again (so the exclusion, not the fixture, is what
#  removes them); and the unpatched expression must name them, or the fixture
#  proves nothing.
# =============================================================================
import datetime as dt
import os
import re
import sqlite3
import sys
import tempfile

OK, BAD = [], []
START = '        _never = [r["key"] for r in con.execute('
END = '.days >= 14]'


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


def lift(path):
    """The witness's own list comprehension, as text, out of the file."""
    text = open(path, "r", encoding="utf-8").read()
    i = text.find(START)
    if i < 0:
        return None
    j = text.find(END, i)
    if j < 0:
        return None
    block = text[i:j + len(END)]
    # dedent the 8 leading spaces so it can be exec'd at module level
    return "\n".join(l[8:] if l.startswith("        ") else l for l in block.split("\n"))


def run(expr, con, keys, now_iso, info_only):
    env = {"con": con, "_keys": keys, "_nowi": now_iso, "dt": dt,
           "HEALTH_INFO_ONLY": info_only}
    exec(compile(expr, "<witness>", "exec"), env)
    return sorted(env["_never"])


def fixture(path):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE health_check_seen (key TEXT PRIMARY KEY, first_seen TEXT,"
                " nonok_count INTEGER NOT NULL DEFAULT 0, last_nonok TEXT)")
    now = dt.datetime.now()

    def add(key, days, nonok):
        con.execute("INSERT INTO health_check_seen (key, first_seen, nonok_count) VALUES (?,?,?)",
                    (key, (now - dt.timedelta(days=days)).isoformat(timespec="seconds"), nonok))
    add("flags", 40, 0)          # informational by design
    add("margqueue", 40, 0)      # informational by design
    add("backup", 40, 0)         # a real guard, quiet
    add("outbox", 40, 0)         # a real guard, quiet
    add("drawer", 5, 0)          # too young to count yet
    add("renewals", 40, 3)       # has fired
    add("gone", 40, 0)           # no longer a check on the page
    con.commit()
    return con, now.isoformat(timespec="seconds")


def main(argv):
    plain = patched = None
    for a in argv[1:]:
        if a.startswith("--plain="):
            plain = a.split("=", 1)[1]
        elif a.startswith("--patched="):
            patched = a.split("=", 1)[1]
    if not plain or not patched:
        print("usage: walk_s319.py --plain=OLD.py --patched=NEW.py")
        return 2
    e_old, e_new = lift(plain), lift(patched)
    check("the witness's expression was found in the unpatched file", e_old is not None)
    check("and in the patched file", e_new is not None)
    if not (e_old and e_new):
        return 1
    check("the patched expression carries the exclusion", "HEALTH_INFO_ONLY" in e_new)
    check("and the unpatched one does not", "HEALTH_INFO_ONLY" not in e_old)

    tmp = tempfile.mkdtemp(prefix="s319_")
    db = os.path.join(tmp, "scratch.db")
    con, now = fixture(db)
    keys = {"flags", "margqueue", "backup", "outbox", "drawer", "renewals"}
    info = ("flags", "margqueue")

    before = run(e_old, con, keys, now, info)
    check("BEFORE: the witness names four, flags and margqueue among them",
          before == ["backup", "flags", "margqueue", "outbox"])
    after = run(e_new, con, keys, now, info)
    check("AFTER: it names only the two real guards", after == ["backup", "outbox"])
    check("the two informational rows are gone from the list",
          "flags" not in after and "margqueue" not in after)
    check("a check too young to count is still not named (drawer, 5 days)",
          "drawer" not in before and "drawer" not in after)
    check("a check that HAS fired is still not named (renewals)",
          "renewals" not in before and "renewals" not in after)
    check("a stored key that is no longer a card is still not named (gone)",
          "gone" not in before and "gone" not in after)

    neg = run(e_new, con, keys, now, ())
    check("NEGATIVE CONTROL -- with HEALTH_INFO_ONLY empty the two come back, so the"
          " exclusion is what removes them, not the fixture", neg == before)

    # the tracking above the filter must be untouched: both files must still
    # count non-ok for EVERY key, including the excluded two.
    t_old = open(plain, encoding="utf-8").read()
    t_new = open(patched, encoding="utf-8").read()
    ins = ('con.execute("INSERT OR IGNORE INTO health_check_seen (key, first_seen) "')
    upd = ('con.execute("UPDATE health_check_seen SET nonok_count=nonok_count+1,"')
    check("the excluded rows are STILL TRACKED -- the insert is untouched",
          t_old.count(ins) == 1 and t_new.count(ins) == 1)
    check("and their non-ok counter is untouched",
          t_old.count(upd) == 1 and t_new.count(upd) == 1)
    check("the card says in its own words why five and not seven",
          "informational by design" in t_new and "informational by design" not in t_old)
    check("HEALTH_INFO_ONLY is declared exactly once, and only those two keys",
          t_new.count('HEALTH_INFO_ONLY = ("flags", "margqueue")') == 1)
    check("nothing else in the file selects on nonok_count=0",
          t_new.count("nonok_count=0") == 1)

    con.close()
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("WALK OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
