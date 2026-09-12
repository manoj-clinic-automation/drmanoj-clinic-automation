"""walk_patch_S241.py -- prove the mount patch on copies, never on the box."""
import io, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PATCH = os.path.join(HERE, "patch_finance_app_S241_amir.py")
PY = sys.executable

GOOD = '''import os
from flask import Flask
app = Flask(__name__)
UNIT = "medical"

def db():
    return None

def require(*roles, **kw):
    return {}, None

# --- S223_CLINIC_REGISTER begin -- x ---
import clinic_register
# --- S223_CLINIC_REGISTER end ---

# --- S240_MARG_DOOR begin -- y ---
import marg_door
# --- S240_MARG_DOOR end ---

if __name__ == "__main__":
    app.run()
'''

OK, BAD = [], []


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print(("   ok   " if cond else "   FAIL ") + name + (("  -- " + detail) if detail and not cond else ""))


def run(path):
    env = dict(os.environ, FA_PATH=path)
    p = subprocess.run([PY, PATCH], capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout + p.stderr)


def write(src, newline="\n"):
    d = tempfile.mkdtemp(prefix="fa_")
    p = os.path.join(d, "finance_app.py")
    io.open(p, "w", encoding="utf-8", newline=newline).write(src)
    return p


def main():
    print("-- happy path")
    p = write(GOOD)
    rc, out = run(p)
    src = io.open(p, encoding="utf-8").read()
    check("exit 0", rc == 0, out.strip())
    check("one block added", src.count("S241_AMIR_DAY begin") == 1)
    check("anchored after the LAST end marker",
          src.index("S241_AMIR_DAY begin") > src.index("S240_MARG_DOOR end"))
    check("it is before __main__", src.index("S241_AMIR_DAY end") < src.index('if __name__'))
    check("it still compiles", compile(src, p, "exec") or True)
    check("it names the anchor it used", "S240_MARG_DOOR end" in out)

    print("-- run it again")
    rc2, out2 = run(p)
    src2 = io.open(p, encoding="utf-8").read()
    check("exit 0 and says ALREADY MOUNTED", rc2 == 0 and "ALREADY MOUNTED" in out2)
    check("still exactly one block", src2.count("S241_AMIR_DAY begin") == 1)
    check("the file did not change", src2 == src)

    print("-- CRLF is refused")
    p = write(GOOD, newline="\r\n")
    before = io.open(p, "rb").read()
    rc, out = run(p)
    check("refused for CRLF", rc == 2 and "CRLF" in out)
    check("byte-identical after the refusal", io.open(p, "rb").read() == before)

    print("-- no anchor is refused")
    p = write(GOOD.replace("# --- S223_CLINIC_REGISTER end ---", "")
                  .replace("# --- S240_MARG_DOOR end ---", ""))
    before = io.open(p, "rb").read()
    rc, out = run(p)
    check("refused with no anchor", rc == 2 and "anchor" in out)
    check("byte-identical after the refusal", io.open(p, "rb").read() == before)

    print("-- a helper defined after the anchor is refused")
    late = GOOD.replace("def require(*roles, **kw):\n    return {}, None\n", "")
    late = late.replace("# --- S240_MARG_DOOR end ---",
                        "# --- S240_MARG_DOOR end ---\n\ndef require(*roles, **kw):\n    return {}, None\n")
    p = write(late)
    before = io.open(p, "rb").read()
    rc, out = run(p)
    check("refused because require comes later", rc == 2 and "NameError" in out)
    check("byte-identical after the refusal", io.open(p, "rb").read() == before)

    print("-- a missing UNIT is refused")
    p = write(GOOD.replace('UNIT = "medical"\n', ""))
    before = io.open(p, "rb").read()
    rc, out = run(p)
    check("refused for missing UNIT", rc == 2 and "UNIT" in out)
    check("byte-identical after the refusal", io.open(p, "rb").read() == before)

    print("-- a missing file is refused")
    rc, out = run(os.path.join(tempfile.mkdtemp(), "nope.py"))
    check("refused for a missing target", rc == 2 and "does not exist" in out)

    print("-- an indented end-marker is not mistaken for an anchor")
    p = write(GOOD.replace("# --- S240_MARG_DOOR end ---",
                           "if True:\n    pass\n    # --- S240_MARG_DOOR end ---"))
    rc, out = run(p)
    src = io.open(p, encoding="utf-8").read()
    check("it fell back to the previous real anchor",
          rc == 0 and "S223_CLINIC_REGISTER end" in out)
    check("and the result compiles", compile(src, p, "exec") or True)

    print("-- an edit that would not compile is rolled back")
    broken = GOOD.replace("# --- S240_MARG_DOOR end ---",
                          "_x = (\n# --- S240_MARG_DOOR end ---\n    1)")
    p = write(broken)
    before = io.open(p, "rb").read()
    rc, out = run(p)
    check("refused, and the file was put back",
          rc == 2 and "did not compile" in out and io.open(p, "rb").read() == before, out.strip())

    print("")
    print("%d ok, %d failed" % (len(OK), len(BAD)))
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
