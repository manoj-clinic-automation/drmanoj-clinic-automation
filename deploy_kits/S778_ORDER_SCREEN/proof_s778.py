#!/usr/bin/env python3
"""proof_s778.py FILES_DIR SHARED_DIR FINANCE_DIR DB_COPY LABEL -- kit S778_ORDER_SCREEN on a COPY of finance.db (it writes to the copy only;
no Web Push is sent: ORDER_PUSH_NONE). The red box as the staff would see it now, then every door pressed once on today's real lines:
'Ab nahi milta' -> the doctor's line -> Stop it everywhere (held from the plan, off every card) -> Undo (the rule as it was); 'Dobara order
karo' -> the dealer's card -> 'Order ho gaya' -> out of the box; the wrong-dealer move when a card has one. Prints medicine and dealer
names and counts only. Last line: 'PROOF S778 <LABEL>: ... GREEN' (or RED)."""
import os
import shutil
import sqlite3
import sys
import tempfile
import types

FILES, SHARED, FIN, DB, LABEL = sys.argv[1:6]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]
os.environ["ORDER_PUSH_NONE"] = "1"
os.environ.setdefault("SPINE_DB", os.path.join(tempfile.gettempdir(), "s778_no_spine.db"))   # the proof never opens the live spine
RUN = tempfile.mkdtemp(prefix="p778_")
for f in ("porders_s454.py", "order_s778.py"):
    shutil.copyfile(os.path.join(FILES, f), os.path.join(RUN, f))
sys.path[:0] = [RUN, FIN, SHARED]
from flask import Flask  # noqa: E402

ROLE = {"kind": "sender"}
con = sqlite3.connect(DB, timeout=30)
con.row_factory = sqlite3.Row
po = types.ModuleType("porders")
po.S441 = None
po._auth = lambda: (dict(user=("manoj" if ROLE["kind"] == "owner" else "shavez"), login=("manoj" if ROLE["kind"] == "owner" else "shavez")), con, ROLE["kind"], None)
sys.modules["porders"] = po
import order_rules  # noqa: E402
order_rules.RULES_JSON = os.path.join(RUN, "order_rules.json")          # never the live lists (nothing here writes them; belt and braces)
import porders_s454 as PS  # noqa: E402
import order_s778 as S  # noqa: E402
import order_sheet as OS  # noqa: E402
app = Flask(__name__)
PS.init(app)
cl = app.test_client()


def post(u, b):
    r = cl.post("/finance/porders/api/s778/" + u, json=b)
    return r.status_code, (r.get_json(silent=True) or {})


def box():
    with app.test_request_context():
        return S.red_lines(con, False)


def on_cards(item):
    return [e["vendor"] for e in OS.entries(con) for l in e["lines"] if l["item"] == item]


res, words = {}, []
r = cl.get("/finance/porders/s454/order")
res["page"] = r.status_code
ls = box()
off = [c for c in ls if not c.get("on_card")]
print("red box now: %d line(s) (%d more on today's cards)" % (len(off), len(ls) - len(off)))
for c in ls:
    print("  %2d din %-5s %-26s %-26s %s%s" % (c["age"], c["kind"], c["item"][:26], c["vendor"][:26], ("on card " + S.short(c["on_card"])) if c.get("on_card") else "",
                                              (" · wrong dealer: %s brings it" % c["wrong"]["other"]) if c.get("wrong") else ""))
ok = res["page"] == 200
# 1 · Ab nahi milta -> Stop it everywhere -> Undo
c1 = off[0] if off else None
if c1:
    k20 = order_rules._k20(c1["item"])
    rule0 = con.execute("SELECT rule, value FROM order_item_rule WHERE item_norm=?", (S.norm(c1["item"]),)).fetchone()
    rule0 = tuple(rule0) if rule0 else None
    code, j = post("na", dict(kind=c1["kind"], ref=c1["ref"]))
    ny = [l["text"] for l in order_rules.needs_you_lines(con) if l.get("href") == "/finance/porders/s454/abnahi" and c1["item"] in l.get("text", "")]
    nid = con.execute("SELECT id FROM order_s778_na WHERE item=? ORDER BY id DESC", (c1["item"],)).fetchone()[0]
    ROLE["kind"] = "owner"
    s1 = post("na_answer", dict(id=nid, answer="stop"))[0]
    held = k20 in order_rules.held_sets(con)
    gone = not on_cards(c1["item"]) and not any(x["item"] == c1["item"] for x in box())
    s2 = post("na_answer", dict(id=nid, answer="undo"))[0]
    rule1 = con.execute("SELECT rule, value FROM order_item_rule WHERE item_norm=?", (S.norm(c1["item"]),)).fetchone()
    rule1 = tuple(rule1) if rule1 else None
    ROLE["kind"] = "sender"
    good = code == 200 and len(ny) == 1 and s1 == 200 and held and gone and s2 == 200 and rule1 == rule0
    print("Ab nahi milta on %s: Needs-you %r · stopped: held %s, off every card and the box %s · undo: rule as before %s" % (c1["item"], ny[:1], held, gone, rule1 == rule0))
    words.append("Ab nahi milta %s %s" % (c1["item"], "ok" if good else "WRONG"))
    ok = ok and good
else:
    words.append("Ab nahi milta: no old line today")
# 2 · Dobara order karo -> the card -> Order ho gaya
c2 = next((c for c in box() if not c.get("on_card") and not c.get("marg_line") and not c.get("wrong") and (not c1 or c["item"] != c1["item"])), None)
if c2:
    code, j = post("again", dict(kind=c2["kind"], ref=c2["ref"]))
    on = S.short(c2["vendor"]) in [S.short(v) for v in on_cards(c2["item"])]
    left = not any(x["item"] == c2["item"] and not x.get("on_card") for x in box())
    b, oc = OS.order_supplier(con, "shavez", c2["sn"], "call")
    done = con.execute("SELECT done_order_id FROM order_s778_again WHERE item=? ORDER BY id DESC", (c2["item"],)).fetchone()[0]
    out = not any(x["item"] == c2["item"] for x in box())
    good = code == 200 and on and left and oc == 200 and done == b.get("order_id") and out
    print("Dobara on %s (%s): on its card %s · out of the box %s · ordered %s (order done %s) · gone after the order %s"
          % (c2["item"], S.short(c2["vendor"]), on, left, oc, done == b.get("order_id"), out))
    words.append("Dobara %s %s" % (c2["item"], "ok" if good else "WRONG"))
    ok = ok and good
else:
    words.append("Dobara: no line today")
# 3 · the wrong dealer, moved
mv = None
for e in OS.entries(con):
    if e.get("draft") or e.get("state") != "pending":
        continue
    for l in e["lines"]:
        w = S.wrong_dealer(con, e["sn"], l["item"], e["vendor"])
        if w:
            mv = (e, l, w)
            break
    if mv:
        break
if mv:
    e, l, w = mv
    code, j = post("move", dict(sn=e["sn"], src=l["src"], ref=str(l["ref"]), item=l["item"], to=w["other_sn"]))
    left = not any(x["item"] == l["item"] for x in (OS.entry_of(con, e["sn"]) or {}).get("lines", []))
    there = any(x["item"] == l["item"] for x in (OS.entry_of(con, w["other_sn"]) or {}).get("lines", []))
    good = code == 200 and left and there
    print("wrong dealer %s: %s -> %s · left %s · on %s's card %s" % (l["item"], S.short(e["vendor"]), w["other"], left, w["other"], there))
    words.append("moved %s %s" % (l["item"], "ok" if good else "WRONG"))
    ok = ok and good
else:
    words.append("no wrong dealer today")
r = cl.get("/finance/porders/s454/order")
ok = ok and r.status_code == 200
print("PROOF S778 %s: red box %d (+%d on cards) · %s · %s" % (LABEL, len(off), len(ls) - len(off), " · ".join(words), "GREEN" if ok else "RED"))
shutil.rmtree(RUN, ignore_errors=True)
