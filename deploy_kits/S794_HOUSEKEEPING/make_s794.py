#!/usr/bin/python3
# make_s794.py -- kit S794_HOUSEKEEPING part (a) (S431, 11-Nov-2026, the parent; Runbook §2A item 7, D899: "why S723's
# pc_kits_current.py still lets the PC set-up kits go stale"). Usage: make_s794.py <pc_kits_current.py 6c5887c5> <out dir>.
# WHY (read at S431): pin_map() skipped every pin row whose note held the word "superseded" anywhere -- the medical PC's
# newest marg_watch.py row (S763) names a backup file "...marg_watch_S722.py.superseded kept beside", so it was skipped, the
# older row was taken as the newest pin, the PC's own copy "is not its newest pin" -> left as packed, and the report still
# said CURRENT. Two exact changes: (1) only the WORD superseded marks a row, not a file name ending in .superseded;
# (2) a member left as packed makes the kit BEHIND -- NOT REPACKED in the report, never CURRENT.
import hashlib, os, sys
src, out = sys.argv[1], sys.argv[2]
b = open(src, "rb").read()
assert hashlib.md5(b).hexdigest().startswith("6c5887c5"), "not the live pc_kits_current.py (6c5887c5)"
C = b.decode("utf-8")
def rp(t, a, b):
    assert t.count(a) == 1, "anchor not once: " + a[:80]
    return t.replace(a, b)
C = rp(C, 'KIT = "S723"', 'KIT = "S723+S794"')
C = rp(C, "def pin_map(pins_path):",
       "_SUP = re.compile(r\"(?<![.\\w])superseded\\b\", re.I)   # S794: the word, not a file name such as x.py.superseded\n\n\n"
       "def pin_map(pins_path):")
C = rp(C, '            if "superseded" in f[2].lower() or (len(f) > 3 and "superseded" in f[3].lower()):',
          '            if _SUP.search(f[2]) or (len(f) > 3 and _SUP.search(f[3])):')
C = rp(C, '''    if not changes:
        return say("medical", "CURRENT", "every payload file equals the PC's own copy" + ("; " + "; ".join(notes) if notes else ""))''',
          '''    if not changes:
        held = [x for x in notes if "left as packed" in x]             # S794: a member behind and not repacked is never CURRENT
        if held:
            return say("medical", "BEHIND -- NOT REPACKED", "; ".join(notes))
        return say("medical", "CURRENT", "every payload file equals the PC's own copy" + ("; " + "; ".join(notes) if notes else ""))''')
os.makedirs(out, exist_ok=True)
open(os.path.join(out, "pc_kits_current.py"), "wb").write(C.encode("utf-8"))
print("written pc_kits_current.py", hashlib.md5(C.encode("utf-8")).hexdigest()[:8])
