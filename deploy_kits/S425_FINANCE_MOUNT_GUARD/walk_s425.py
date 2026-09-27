#!/usr/bin/env python3
"""walk_s425.py -- the walk for kit S425_FINANCE_MOUNT_GUARD. No network, no database, no Flask needed.
usage: walk_s425.py <original finance_app.py (FROM bytes)> <patched finance_app.py>
Proves: (1) the patch changes nothing but the eleven wraps, the list and the health row (un-wrapping the patched
file gives back the original byte for byte); (2) eleven try blocks at module level, each holding exactly its old
section's code; (3) with every part loading, _MOUNT_FAILED stays empty and the row is green 'all 25 parts loaded';
(4) with one part broken (an import error) and one broken in its init (a runtime error) the rest still mount, both
are recorded, and the row turns red naming both; (5) a guarded later module missing from sys.modules also turns it
red. Prints WALK OK n/n."""
import ast
import re
import sys
import types

ORIG, NEW = sys.argv[1], sys.argv[2]
o = open(ORIG, encoding="utf-8").read()
s = open(NEW, encoding="utf-8").read()
N = [0, 0]


def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1
        print("  ok  %s" % name)
    else:
        print("  RED %s %s" % (name, extra))


FIRST = "# --- S208_STOCK_LEDGER begin"
LAST_END = "# --- S241_AMIR_DAY end ---"
B2 = "    # ---- B2: THE NEVER-FIRED WITNESS"

print("[1] the patch changes nothing else")
lines = s.split("\n")
back, k = [], 0
skip_row = False
while k < len(lines):
    l = lines[k]
    if l.startswith("# S425: every mount below records") or l == "_MOUNT_FAILED = []":
        k += 1
        if l == "_MOUNT_FAILED = []" and k < len(lines) and lines[k] == "":
            k += 1
        continue
    if l.startswith("    # ---- S425: PARTS OF THE FINANCE APP"):
        skip_row = True
    if skip_row:
        if l.startswith(B2):
            skip_row = False
            back.append(l)
        k += 1
        continue
    if l.startswith("try:") and "S425" in l:
        k += 1
        continue
    if l.startswith("except Exception as _ex_m:"):
        k += 3           # the except line, the record, the print
        continue
    back.append(l)
    k += 1
unwrapped = "\n".join(back)
# inside the region the wrapped code lines carry four extra spaces; comments and blanks do not
i, j = unwrapped.index(FIRST), unwrapped.index(LAST_END)
oi, oj = o.index(FIRST), o.index(LAST_END)
orig_reg = o[oi:oj].split("\n")
new_reg = unwrapped[i:j].split("\n")
ok_lines = len(orig_reg) == len(new_reg)
if ok_lines:
    for a, b in zip(orig_reg, new_reg):
        code = a.strip() and not a.lstrip().startswith("#")
        if (code and b != "    " + a) or (not code and b != a):
            ok_lines = False
            print("      differs:", repr(a[:60]), "|", repr(b[:60]))
            break
check("inside the region every code line is the original line indented by four, every comment untouched", ok_lines,
      "%d vs %d lines" % (len(orig_reg), len(new_reg)))
check("outside the region the file is the original byte for byte",
      unwrapped[:i] == o[:oi] and unwrapped[j:] == o[oj:])

print("[2] the shape")
tree = ast.parse(s)
tries = [n for n in tree.body if isinstance(n, ast.Try)
         and any(isinstance(h.type, ast.Name) and h.type.id == "Exception" and h.name == "_ex_m" for h in n.handlers)]
check("eleven module-level try blocks, one per old section", len(tries) == 11, str(len(tries)))
mods = []
for t in tries:
    mods += [a.name for st in t.body if isinstance(st, ast.Import) for a in st.names]
check("the twelve old modules, each imported inside a guard, in the original order",
      mods == ["stock_app", "darpan_app", "staff_pages", "joiner_app", "returns_desk", "finance_clinic_day",
               "clinic_register", "purchase_app", "bank_mpr_status", "clinic_day_pdf", "marg_door", "amir_day"], str(mods))
top_imports = [a.name for n in tree.body if isinstance(n, ast.Import) for a in n.names]
check("none of them is still imported bare at module level",
      not set(top_imports) & set(mods), str(set(top_imports) & set(mods)))
check("the health row is inside _health_state, once, before the B2 marker",
      s.count('"mounts", "Parts of the finance app that did not load"') == 3
      and s.index("S425: PARTS OF THE FINANCE APP") < s.index(B2)
      and s.rfind("def _health_state", 0, s.index("S425: PARTS OF THE FINANCE APP")) != -1)
compile(s, NEW, "exec")
check("compiles", True)

print("[3][4][5] the region and the row, executed against stand-ins")
region = s[s.index("# S425: every mount below records"):s.index(LAST_END)]
row_src = s[s.index("    # ---- S425: PARTS OF THE FINANCE APP"):s.index(B2)]


class Any:
    def __getattr__(self, n):
        return Any()

    def __call__(self, *a, **k):
        return Any()


OLD = ["stock_app", "darpan_app", "staff_pages", "joiner_app", "returns_desk", "finance_clinic_day",
       "clinic_register", "purchase_app", "bank_mpr_status", "clinic_day_pdf", "marg_door", "amir_day"]
LATER = ["darpan_kal", "reports_tile", "accountant_upi_cash", "clinic_money", "petty_book", "bank_sms",
         "owner_sheets", "slip_log", "records", "freshness_page", "sale_check", "stockmatch", "porders", "packs"]
INITS = []


def fake(name, init_raises=False):
    m = types.ModuleType(name)

    def init(*a, **k):
        if init_raises:
            raise RuntimeError("walk: %s init broke" % name)
        INITS.append(name)
    m.init = init
    m.joiner_require = lambda r: r
    return m


class Blocker:
    def __init__(self, names):
        self.names = set(names)

    def find_spec(self, name, path=None, target=None):
        if name in self.names:
            raise ImportError("walk: %s cannot be imported" % name)
        return None


def run(break_import=(), break_init=(), drop_later=()):
    for n in OLD + LATER:
        sys.modules.pop(n, None)
    for n in OLD:
        if n not in break_import:
            sys.modules[n] = fake(n, n in break_init)
    for n in LATER:
        if n not in drop_later:
            sys.modules[n] = fake(n)
    blk = Blocker(break_import)
    sys.meta_path.insert(0, blk)
    del INITS[:]
    import os as _os
    g = {"__name__": "walkfa", "sys": sys, "os": _os, "app": Any(), "db": Any(), "require": Any(), "audit": Any(),
         "UNIT": "medical", "CLINIC_UNIT": "clinic", "MARG_TOKEN": "", "UPI_DIR": "/nonexistent"}
    import io
    import contextlib
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            exec(compile(region, "region", "exec"), g)
    finally:
        sys.meta_path.remove(blk)
    rows = []
    g["add"] = lambda key, label, state, detail="", hint="": rows.append((key, state, detail))
    exec(compile("def _row():\n" + row_src, "row", "exec"), g)
    g["_row"]()
    return g["_MOUNT_FAILED"], rows, err.getvalue(), list(INITS)


mf, rows, err, inits = run()
check("all load: nothing recorded, every init ran", mf == [] and len(inits) == 12, str((mf, inits)))
check("all load: the row is ok 'all 25 parts loaded'", rows == [("mounts", "ok", "all 25 parts loaded")], str(rows))

mf, rows, err, inits = run(break_import=("returns_desk",), break_init=("purchase_app",))
names = [n for n, _w in mf]
check("one import broken + one init broken: both recorded, by name", names == ["returns_desk", "purchase_app"], str(mf))
check("... and the other nine still mounted, in order",
      inits == ["stock_app", "darpan_app", "joiner_app", "staff_pages", "finance_clinic_day", "clinic_register",
                "bank_mpr_status", "clinic_day_pdf", "marg_door", "amir_day"], str(inits))
check("... the journal line says '<part> NOT mounted' for each",
      "returns_desk NOT mounted" in err and "purchase_app NOT mounted" in err, err)
check("... the row is bad and names both",
      len(rows) == 1 and rows[0][1] == "bad" and "returns_desk" in rows[0][2] and "purchase_app" in rows[0][2]
      and rows[0][2].startswith("2 of 25"), str(rows))

mf, rows, err, inits = run(break_import=("staff_pages",))
check("staff_pages broken: the pair is one part, joiner_app's init not reached, recorded as staff_pages+joiner_app",
      [n for n, _w in mf] == ["staff_pages+joiner_app"] and "joiner_app" not in inits, str((mf, inits)))

mf, rows, err, inits = run(drop_later=("porders",))
check("a later guarded module absent from sys.modules turns the row red by name",
      mf == [] and rows and rows[0][1] == "bad" and "porders" in rows[0][2], str(rows))

print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
sys.exit(0 if N[0] == N[1] else 1)
