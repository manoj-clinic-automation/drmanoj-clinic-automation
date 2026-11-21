"""synth_s914.py -- the walk for kit S914_PHONE_SETUP_PAGE (Sanjeevni session 497, 21-Nov-2026).

  python synth_s914.py --code <folder holding supplier_msg.py and porders_s454.py> [--macro <folder holding macros.template.mdr + KIT_INFO.txt>]

Renders the reception phone's set-up page through Flask's own test client on a MADE-UP database (a made-up key built at run
time; nothing real is read), and reads the two other places the phone's wording lives. The control (the live files) must go
red on T2-T8, T11 and, with --macro on the 04-Oct template, T12-T14 (T15/T16 hold on both: the kit stays whole).
The last line is 'synth_s914: N ok, M red'.
"""
import argparse
import hashlib
import json
import os
import re
import secrets
import sqlite3
import sys
import tempfile
import types

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]       # F-1441: never import the kit's own copy by accident

ap = argparse.ArgumentParser()
ap.add_argument("--code", required=True)
ap.add_argument("--macro", default="")
A = ap.parse_args()

OK, RED = [], []


def t(name, cond, why=""):
    (OK if cond else RED).append(name)
    print(("ok   " if cond else "RED  ") + name + ("" if cond else ("  -- " + why if why else "")))


tmp = tempfile.mkdtemp(prefix="s914_")
db = os.path.join(tmp, "f.db")
log = os.path.join(tmp, "access.log")
open(log, "w").close()
os.environ["FINANCE_ACCESS_LOG"] = log
KEY = secrets.token_hex(24)                                   # made up here, never a real key
con = sqlite3.connect(db)
con.execute("CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
con.execute("INSERT INTO setting VALUES ('supplier_msg.phone_token', ?, 'made-up')", (KEY,))
con.commit()
con.close()

stub = types.ModuleType("purchase_app")
stub._audit = lambda *a, **k: None
sys.modules["purchase_app"] = stub
sys.path.insert(0, os.path.abspath(A.code))
import flask                                                  # noqa: E402
import supplier_msg as sm                                     # noqa: E402

app = flask.Flask("s914")


def _getdb():
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    return c


sm.init(app, _getdb, lambda *roles: ({"user": "made-up-checker"}, None))
r = app.test_client().get("/finance/purchase/page/phone-setup")
html = r.get_data(as_text=True)
t("T1 the page answers 200", r.status_code == 200, str(r.status_code))
t("T2 screen lock None is a step", "Screen lock: None" in html)
t("T3 the macro carries no constraint", "Constraints: koi nahi" in html)
i_json, i_scr, i_wait2, i_open = (html.find("JSON Parse"), html.find("<b>Screen On</b>"),
                                  html.find("<b>Wait</b> 2 second"), html.find("<b>Open Website</b>"))
t("T4 Screen On, then Wait 2 s, between JSON Parse and Open Website", -1 not in (i_json, i_scr, i_wait2, i_open) and i_json < i_scr < i_wait2 < i_open,
  "positions %s" % [i_json, i_scr, i_wait2, i_open])
t("T5 the old constraints are no longer asked for", "dono zaroori" not in html and "aur <i>Screen On</i>" not in html)
t("T6 the 10:00 daily check named as the proof", "10:00 baje" in html)
i_post = html.find("supplier-msg/done")
t("T7 the POST has no constraint", i_post > 0 and html.find("Is action par koi constraint nahi", i_post) > i_post)
t("T8 the old 'no file given' line is gone; the Clinic PCs file named",
  "file yahan nahi di gayi" not in html and "Clinic PCs" in html)
t("T9 the key shows once, in its box, and nowhere else", html.count(KEY) == 1 and ('<p class="key">%s</p>' % KEY) in html)
t("T10 the phone's state line and the page's Hindi frame", 'id="s452phone"' in html and 'lang="hi"' in html)
t("T10b no unformatted %s or %% left", "%s" not in html and "%%" not in html)

po = open(os.path.join(A.code, "porders_s454.py"), encoding="utf-8").read()
t("T11 the order pages no longer say 'keep the phone unlocked' / 'a dark phone does not ask'",
  "Reception phone unlocked rakhiye" not in po and "Keep the reception phone unlocked" not in po
  and "unlock it, keep the screen on" not in po and "phone unlock kijiye" not in po
  and "a dark phone does not ask" not in po and "with its screen dark too" in po)
t("T11b the wa_unlock line still takes its one number", re.search(r'"wa_unlock": \("[^"]*%d[^"]*",[ \t]*(#[^\n]*)?\s*"[^"]*%d[^"]*"\)', po) is not None)

if A.macro:
    tp = os.path.join(A.macro, "macros.template.mdr")
    raw = open(tp, "rb").read()
    d = json.loads(raw.decode("utf-8"))
    m = d["macroList"][0]
    kinds = [a.get("m_classType") for a in m["m_actionList"]]
    t("T12 the macro has no constraint", m.get("m_constraintList") == [], str(len(m.get("m_constraintList") or [])))
    t("T13 Screen On + Wait 2 s after JSON Parse",
      kinds[:6] == ["HttpRequestAction", "IfConditionAction", "JsonParseAction", "ScreenOnAction", "PauseAction", "OpenWebPageAction"]
      and m["m_actionList"][4].get("m_delayInSeconds") == 2 and m["m_actionList"][3].get("m_screenOff") is False, str(kinds))
    posts = [a for a in m["m_actionList"] if a.get("m_classType") == "HttpRequestAction"]
    t("T14 no action carries a constraint but the If's own condition",
      all(not a.get("m_constraintList") for a in m["m_actionList"] if a.get("m_classType") != "IfConditionAction") and len(posts) == 2)
    info = {}
    for ln in open(os.path.join(A.macro, "KIT_INFO.txt"), encoding="utf-8"):
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.strip().split("=", 1)
            info[k] = v
    t("T15 KIT_INFO's template_md5 is the template's (the Clinic PCs page serves it only then)",
      info.get("template_md5") == hashlib.md5(raw).hexdigest())
    t("T16 the key stays a placeholder", raw.count(b"{{PHONE_TOKEN}}") >= 1 and len(set(re.findall(rb"\{\{[A-Z_]+\}\}", raw))) == 1)

for f in os.listdir(tmp):
    os.remove(os.path.join(tmp, f))
os.rmdir(tmp)
print("synth_s914: %d ok, %d red" % (len(OK), len(RED)))
