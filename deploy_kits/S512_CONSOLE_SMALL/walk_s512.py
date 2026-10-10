"""walk_s512.py -- S512_CONSOLE_SMALL, session 304 (parent), 10-Oct-2026. The walk the installer runs BEFORE placing.

A scratch copy of /root/finance's programs (the kit's owner_console.py over them, unless --control) builds the owner's console
from a scratch copy of finance.db (the console's own build: it copies again and reads read-only). GREEN needs: the work section
follows his panel (a head line per person on the panel, switched-off lists said so, the tasks); the System line carries the
age of the freshness reading; the flag codes have words. Prints names of lists and counts only.
The SAME walk on the live programs (--control) must end RED.
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile

ap = argparse.ArgumentParser()
ap.add_argument("--kit", required=True)
ap.add_argument("--fin", default="/root/finance")
ap.add_argument("--db", default="/root/finance/finance.db")
ap.add_argument("--venv", default="")
ap.add_argument("--control", action="store_true")
a = ap.parse_args()
scr = tempfile.mkdtemp(prefix="s512_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".json", ".html")) and not n.startswith("."):
        shutil.copy2(p, os.path.join(fin, n))
if not a.control:
    shutil.copy(os.path.join(a.kit, "owner_console.py"), os.path.join(fin, "owner_console.py"))
db = os.path.join(scr, "fin.db")
src = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
dst = sqlite3.connect(db)
src.backup(dst)
dst.close()
src.close()
os.environ["FINANCE_DB"] = db
os.environ["AAJ_DUTIES_JSON"] = os.path.join(fin, "aaj_duties.json")
sys.path.insert(0, fin)
os.chdir(fin)
red = []
try:
    import owner_console as OC                                     # noqa: E402
    out = os.path.join(scr, "snap.json")
    snap = OC.build(db, out)
    secs = snap.get("sections") or []
    secs = secs if isinstance(secs, list) else list(secs.values())
    work = next((x for x in secs if x.get("name") == "Today's work"), None)
    system = next((x for x in secs if x.get("name") == "System"), None)
    heads = [l.get("b") for l in (work or {}).get("lines", []) if l.get("b") and not l.get("sub")]
    off = [l.get("text") for l in (work or {}).get("lines", []) if "the list is switched off" in str(l.get("text") or "")]
    print("  pass the console's version: %s" % snap.get("version"))
    print("  pass the work section, by his panel: %s%s" % (", ".join(heads) or "no list heads", (" · switched off: %d" % len(off)) if off else ""))
    if not str(snap.get("version") or "").startswith("S512") or not (heads or off):
        red.append("the work section does not follow the panel")
    fl = [l.get("text") for l in (system or {}).get("lines", []) if "fresh" in str(l.get("text") or "")]
    print("  pass the System line: %s" % (fl[0][:110] if fl else "no freshness line"))
    if not fl or not ("ago" in fl[0] or "too old" in fl[0]):
        red.append("the freshness line carries no age")
    w = OC.flag_word("pos_diff", 0)
    print("  pass a flag in words: pos_diff -> %s" % w)
    if w == "pos diff":
        red.append("the flag pos_diff has no words")
    if snap.get("panel_err"):
        red.append("the panel could not be read: %s" % snap.get("panel_err"))
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S512 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
