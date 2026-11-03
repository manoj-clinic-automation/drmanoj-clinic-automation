#!/usr/bin/env python3
"""render_s703.py -- kit S703_CALLS_PLAYER's check that runs ON THE BOX (no browser there). MADE-UP data only.
  python3 render_s703.py <old calls_console.py> <new calls_console.py> <portal_console.py> <walk_s698.py> <make_s703.py>
Renders the Call Console page through BOTH modules on S698's made-up console.db and proves: the new page carries the
player; take the four S703 pieces back out and the new page is the old page byte for byte (nothing else changed).
Prints 'RENDER OK' last, or 'RENDER RED: ...'."""
import importlib.util, os, sys, tempfile


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


OLDF, NEWF, PCF, W698, MK = [os.path.abspath(a) for a in sys.argv[1:6]]
sys.argv = [W698, tempfile.gettempdir()]
w = load("w698r", W698)
pc = load("pc703r", PCF)
mk = load("mk703r", MK)
td = tempfile.mkdtemp(prefix="s703render.")
dbp = os.path.join(td, "console.db")
_c, P = w.build_db(pc, dbp)
out = {}
for tag, f in (("old", OLDF), ("new", NEWF)):
    cc = load("cc703r_" + tag, f)
    app, _s = w.make_app(cc, dbp, spam={P["P8"]})
    r = app.test_client().get("/portal/console")
    out[tag] = (r.status_code, r.get_data(as_text=True))
os.remove(dbp)
os.rmdir(td)
bad = []
if out["old"][0] != 200 or out["new"][0] != 200:
    bad.append("status old %s new %s" % (out["old"][0], out["new"][0]))
new = out["new"][1]
for need in ('id="pl"', "function plSeek(", "function plToggle(", "function plClose(", "_fail(a)", "button.play" if False else "class=\"play\""):
    if need not in new:
        bad.append("the new page lacks %s" % need)
back = new
for old, nw, _n in mk.EDITS:
    if back.count(nw) != 1:
        bad.append("an S703 piece is not once in the rendered page")
    back = back.replace(nw, old)
if back != out["old"][1]:
    bad.append("with the S703 pieces taken out the new page is NOT the old page")
print("RENDER OK: the new page carries the player; without it the page is the old one byte for byte" if not bad else "RENDER RED: " + "; ".join(bad))
sys.exit(1 if bad else 0)
