# -*- coding: utf-8 -*-
"""S260 live-shape walk -- proves the machine.conf reader on real copies, offline.

The point of every check is the same: WITH NO CONFIG FILE NOTHING CHANGES, and
with one, one line moves the whole machine.
"""
import importlib, io, os, shutil, sys, tempfile

KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manojz")
if not os.path.isdir(KIT):
    KIT = os.path.dirname(os.path.abspath(__file__))
OK = BAD = 0


def ck(name, cond, detail=""):
    global OK, BAD
    if cond:
        OK += 1
        print("  ok    %s" % name)
    else:
        BAD += 1
        print("  FAIL  %s   %s" % (name, str(detail)[:200]))


def load(mod_name, conf_text=None):
    """A fresh copy of the module in its own tree, with or without a conf file."""
    root = tempfile.mkdtemp()
    mp = os.path.join(root, "MargPull")
    os.makedirs(mp)
    shutil.copy(os.path.join(KIT, mod_name + ".py"), mp)
    if conf_text is not None:
        os.makedirs(os.path.join(root, "_config"))
        io.open(os.path.join(root, "_config", "machine.conf"), "w",
                encoding="utf-8").write(conf_text)
    sys.path.insert(0, mp)
    for k in list(sys.modules):
        if k == mod_name:
            del sys.modules[k]
    try:
        return importlib.import_module(mod_name)
    finally:
        sys.path.remove(mp)


OLD = {
    "marg_gate": {
        "DEF_TOKEN_UNC": r"\\100.119.151.40\DDrive\SendToClinic\token.txt",
        "DEF_TOKEN": r"D:\Downloads\margsync\SendToClinic\token.txt",
        "DEF_URL": "https://followup.dr-manoj.in/finance/api/marg-push",
    },
    "pipeline_status": {
        "DEF_URL": "https://followup.dr-manoj.in/finance/api/pipeline-status",
        "DEF_TOKEN": r"D:\Downloads\margsync\SendToClinic\token.txt",
        "DEF_TOKEN_UNC": r"\\100.119.151.40\DDrive\SendToClinic\token.txt",
        "DEF_MEDICAL_HOST": "100.119.151.40",
        "DEF_SHARE_PROBE": r"\\100.119.151.40\DDrive\MARGERP\users",
    },
}

# ---------------------------------------------------------- 1 · no config file
for mod, want in OLD.items():
    m = load(mod, None)
    for k, v in want.items():
        ck("%s: with NO config file, %s is exactly what it always was" % (mod, k),
           getattr(m, k) == v, "%r != %r" % (getattr(m, k), v))

# ------------------------------------------- 2 · an empty / commented config
EMPTY = "# nothing but comments\n\n   \nMEDICAL_HOST=\n"
for mod, want in OLD.items():
    m = load(mod, EMPTY)
    for k, v in want.items():
        ck("%s: comments and a blank value change nothing (%s)" % (mod, k),
           getattr(m, k) == v, "%r != %r" % (getattr(m, k), v))

# ------------------------------------------------------- 3 · a real config
CONF = ("# the machine\n"
        "MEDICAL_HOST = 100.64.9.9\n"
        "MEDICAL_SHARE=DShare\n"
        "SERVER_BASE=https://example.test/\n"
        "TOKEN_LOCAL=E:\\keys\\token.txt\n"
        "STOCK_BASELINE=01-10-2026\n")

m = load("marg_gate", CONF)
ck("marg_gate: the URL follows SERVER_BASE, trailing slash trimmed",
   m.DEF_URL == "https://example.test/finance/api/marg-push", m.DEF_URL)
ck("marg_gate: the key path follows TOKEN_LOCAL",
   m.DEF_TOKEN == r"E:\keys\token.txt", m.DEF_TOKEN)
ck("marg_gate: ONE line moved the medical PC -- the share path followed it",
   m.DEF_TOKEN_UNC == r"\\100.64.9.9\DShare\SendToClinic\token.txt", m.DEF_TOKEN_UNC)

m = load("pipeline_status", CONF)
ck("pipeline_status: the URL follows SERVER_BASE",
   m.DEF_URL == "https://example.test/finance/api/pipeline-status", m.DEF_URL)
ck("pipeline_status: the key path follows TOKEN_LOCAL",
   m.DEF_TOKEN == r"E:\keys\token.txt", m.DEF_TOKEN)
ck("pipeline_status: the medical host follows the one line",
   m.DEF_MEDICAL_HOST == "100.64.9.9", m.DEF_MEDICAL_HOST)
ck("pipeline_status: the token share followed it too",
   m.DEF_TOKEN_UNC == r"\\100.64.9.9\DShare\SendToClinic\token.txt", m.DEF_TOKEN_UNC)
ck("pipeline_status: the probe the pull depends on followed it too",
   m.DEF_SHARE_PROBE == r"\\100.64.9.9\DShare\MARGERP\users", m.DEF_SHARE_PROBE)
ck("spaces around the = are ignored", m.DEF_MEDICAL_HOST == "100.64.9.9")

# ------------------------------------- 4 · an unreadable config is survivable
root = tempfile.mkdtemp()
mp = os.path.join(root, "MargPull"); os.makedirs(mp)
shutil.copy(os.path.join(KIT, "marg_gate.py"), mp)
os.makedirs(os.path.join(root, "_config", "machine.conf"))   # a DIRECTORY, not a file
sys.path.insert(0, mp)
sys.modules.pop("marg_gate", None)
try:
    m = importlib.import_module("marg_gate")
    ck("a config path that cannot be read falls back, it does not crash",
       m.DEF_URL == OLD["marg_gate"]["DEF_URL"], m.DEF_URL)
except Exception as e:                                        # noqa: BLE001
    ck("a config path that cannot be read falls back, it does not crash", False, e)
finally:
    sys.path.remove(mp)

# ------------------------------------------------------------ 5 · the two bats
# cmd.exe does not exist off Windows, so the parsing is proved here by reading
# and proved by RUNNING inside install_s260.py on manojz itself (F-443).
for f, key, var in (("PULL_FROM_MEDICAL.bat", "MEDICAL_HOST", "MEDHOST"),
                    ("PUSH_STOCK_DAILY.bat", "STOCK_BASELINE", "BASELINE")):
    t = io.open(os.path.join(KIT, f), encoding="utf-8").read().replace("\r\n", "\n")
    lines = t.split("\n")
    def first(pred):
        for i, l in enumerate(lines):
            if pred(l):
                return i
        return 10 ** 6
    i_def = first(lambda l: l.strip().lower().startswith("set ") and var.lower() in l.lower())
    i_read = first(lambda l: key in l and "%%~B" in l)
    i_use = first(lambda l: ("%" + var + "%") in l)
    name = f
    ck("%s: the old value is set BEFORE the config is read" % name,
       i_def < i_read < 10 ** 6, "def=%s read=%s" % (i_def, i_read))
    guard = 'if not "%%~B"=="" set "' + var + '=%%~B"'
    ck("%s: it only overwrites when the key is present and not blank" % name,
       guard in t, guard)
    ck("%s: comment lines in the config are skipped (eol=#)" % name, "eol=#" in t)
    ck("%s: the value is used after it is read" % name, i_use > i_read, "use=%s" % i_use)

# ------------------------------------- 6 · the format the installer must write
# cmd.exe splits on "=" and does NOT trim, so a conf line written as
# "KEY = value" would give batch the key "KEY " and the value " value".
# The file is therefore written strictly, and that strictness is checked here
# against the very generator the installer uses.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import install_s260 as _ins
    text = _ins.conf_text({"MEDICAL_HOST": "100.119.151.40", "MEDICAL_SHARE": "DDrive",
                           "SERVER_BASE": "https://followup.dr-manoj.in",
                           "TOKEN_LOCAL": r"D:\Downloads\margsync\SendToClinic\token.txt",
                           "STOCK_BASELINE": "03-09-2026"})
    bad = [l for l in text.splitlines()
           if l.strip() and not l.lstrip().startswith("#")
           and ("= " in l.split("=", 1)[0] + "=" or " =" in l.split("=", 1)[0] + "=")]
    ck("the config the installer writes has no space around the =", not bad, bad[:3])
    ck("every key batch reads is in the file the installer writes",
       all(k in text for k in ("MEDICAL_HOST=", "MEDICAL_SHARE=", "STOCK_BASELINE=")))
    ck("the file explains itself in the shop's own words",
       "KEY=VALUE" in text and "no spaces" in text.lower())
except Exception as e:                                        # noqa: BLE001
    ck("the installer's config generator could be read", False, e)

print("\n%d ok, %d failed" % (OK, BAD))
sys.exit(1 if BAD else 0)
