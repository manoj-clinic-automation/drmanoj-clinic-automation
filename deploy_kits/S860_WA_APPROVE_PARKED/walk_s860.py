#!/usr/bin/env python3
"""walk_s860.py -- kit S860_WA_APPROVE_PARKED (session 478, the parent, 17-Nov-2026), F-1364 / D964.
   python walk_s860.py <live clinic_doctor.py> <kit clinic_doctor.py> <live swap_key_s701.py> <kit swap_key_s701.py>
Proves on the files only (nothing is imported, run or restarted -- both are read as source and parsed):
  1  clinic_doctor.py: the kit's SERVICES is the live list without the one "wa-approve" row, every other row identical and in
     order; nothing else in the file differs except that row and its two comment lines; it compiles;
  2  swap_key_s701.py: READERS' default is the live default without "wa-approve" (clinic-portal, wa-send-api, in order);
     nothing else differs except that line and one comment line; it compiles;
  3  "wa-approve" is named in neither kit file's code (comments only).
Exit 0 = WALK OK; 1 = RED. The control (the live files in the kit's place) must go RED."""
import ast
import sys

ld, kd, ls, ks = sys.argv[1:5]
oks, fails = [], []


def ck(name, cond):
    (oks if cond else fails).append(name)
    print(("  ok   " if cond else "  FAIL ") + name)


def src(p):
    return open(p, encoding="utf-8").read()


def assign(text, name):
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return node.value
    return None


def code_lines(text):
    return [l for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]


LD, KD, LS, KS = src(ld), src(kd), src(ls), src(ks)
try:
    compile(KD, kd, "exec"); compile(KS, ks, "exec"); comp = True
except SyntaxError:
    comp = False
ck("0 both kit files compile", comp)

# 1 clinic_doctor
lsv = ast.literal_eval(assign(LD, "SERVICES")) if assign(LD, "SERVICES") is not None else []
ksv = ast.literal_eval(assign(KD, "SERVICES")) if assign(KD, "SERVICES") is not None else []
ck("1a the live SERVICES has the wa-approve row (the file this kit was built on)", any(r[0] == "wa-approve" for r in lsv))
ck("1b the kit's SERVICES = the live list without wa-approve, every other row identical and in order",
   ksv == [r for r in lsv if r[0] != "wa-approve"] and len(ksv) == len(lsv) - 1)
la, ka = LD.splitlines(), KD.splitlines()
gone = [l for l in la if l not in ka]
new = [l for l in ka if l not in la]
ck("1c nothing else in clinic_doctor.py differs (one row out, two comment lines in)",
   len(gone) == 1 and "wa-approve" in gone[0] and len(new) == 2 and all(l.strip().startswith("#") for l in new))

# 2 swap_key
def readers_default(text):
    v = assign(text, "READERS")
    for n in ast.walk(v) if v is not None else []:
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and "," in n.value and n.value.strip(",") and "-" in n.value:
            return n.value.split(",")
    return None


lr, kr = readers_default(LS), readers_default(KS)
ck("2a the live READERS default holds wa-approve", lr is not None and "wa-approve" in lr)
ck("2b the kit's READERS default = clinic-portal, wa-send-api (the live list less wa-approve, in order)",
   kr == [u for u in (lr or []) if u != "wa-approve"] == ["clinic-portal", "wa-send-api"])
la, ka = LS.splitlines(), KS.splitlines()
gone = [l for l in la if l not in ka]
new = [l for l in ka if l not in la]
ck("2c nothing else in swap_key_s701.py differs (the READERS line + one comment line)",
   len(gone) == 1 and "READERS" in gone[0] and len(new) == 2 and sum(1 for l in new if l.strip().startswith("#")) == 1)

# 3 named nowhere in code
ck("3 wa-approve is named in neither kit file's code (comments only)",
   not any("wa-approve" in l for l in code_lines(KD)) and not any("wa-approve" in l for l in code_lines(KS)))

print("WALK OK %d/%d" % (len(oks), len(oks) + len(fails)) if not fails else "WALK RED %d of %d failed" % (len(fails), len(oks) + len(fails)))
sys.exit(1 if fails else 0)
