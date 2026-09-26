#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s414.py -- kit S414_RULES_PAGE_UX (F-635). THE REAL finance_app.py (a copy of /root/finance carrying the kit's two files) over a
SCRATCH COPY of finance.db: the rules state API unchanged (same keys and counts as the box as it is); the new items API (filters on every
typed word, caps at 20, owner-only); a tick posts the item rule and the answer carries the counts and the row; the owner's page carries the
new block with NO prompt( / confirm( in it, its markers, balanced braces (a string-aware count -- no browser or node on the box), and
everything S410's walk reads. Own rows by key (W414 …), never by count; the spine's order_rules.json restored byte for byte. Negative
control: the box as it is (S410's page and API).

  --app NEW --old OLD --db PATH
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import subprocess
import sys

ap = argparse.ArgumentParser()
for k in ("--app", "--old", "--db"):
    ap.add_argument(k, required=True)
a = ap.parse_args()
assert "walk" in a.db or "scratch" in a.db or a.db.startswith("/tmp"), "refusing a non-scratch database"
n, fails = 0, []
W = os.path.dirname(os.path.abspath(a.db))


def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:600] + "]") if got is not None else ""))
    if not cond:
        fails.append(label)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


# ---------------------------------------------------------------- the fixture: three snapshot items of our own (by key), nothing else
db = sqlite3.connect(a.db)
db.row_factory = sqlite3.Row
NOW = dt.datetime.now().replace(microsecond=0).isoformat()
db.execute("DELETE FROM stock_snapshot WHERE item LIKE 'W414%'")
if db.execute("SELECT 1 FROM sqlite_master WHERE name='order_item_rule'").fetchone():
    db.execute("DELETE FROM order_item_rule WHERE item LIKE 'W414%'")
AS_ON = max({r[0] for r in db.execute("SELECT DISTINCT as_on FROM stock_snapshot")}, key=lambda s: (s[6:], s[3:5], s[:2]))
for item, qty in (("W414 TEST ALPHA 10MG", 5), ("W414 TEST BETA", 3), ("W414 ALPHA BETA GAMMA", 7)):
    db.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,?)", (AS_ON, item, qty, "1*10", 10, NOW, "walk"))
db.commit()
db.close()
copydb(a.db, a.db + ".old")
print("-- scratch copy made (.old = the box as it is); 3 snapshot items of our own (W414 …) on as_on %s" % AS_ON)

PROBE = r'''
import json, os, sys, sqlite3, re
APP = os.environ["APPDIR"]; sys.path.insert(0, APP); os.chdir(APP)
os.environ["FINANCE_ALLOW_HEADER_AUTH"] = "1"
NEW = os.environ["MODE"] == "new"
import finance_app as fa
c = fa.app.test_client()
H = lambda u: {"X-Clinic-User": u, "X-Clinic-Role": ""}
def G(u, p):
    r = c.get(p, headers=H(u)); j = r.get_json(silent=True)
    return [r.status_code, j if j is not None else r.get_data(as_text=True)]
def P(u, p, b=None):
    r = c.post(p, json=(b or {}), headers=H(u)); return [r.status_code, r.get_json(silent=True)]
db = sqlite3.connect(os.environ["FINANCE_DB"], timeout=30); db.row_factory = sqlite3.Row
q = lambda s, *a: [dict(r) for r in db.execute(s, a).fetchall()]
out = {"mounted": "order_rules" in fa.app.blueprints}
st = G("manoj", "/finance/porders/api/rules/state")
S = st[1] if isinstance(st[1], dict) else {}
out["state"] = [st[0], sorted(S.keys()), len(S.get("rules") or []), len((S.get("candidates") or {}).get("never") or []), len((S.get("candidates") or {}).get("on_demand") or []), len(S.get("item_rules") or []),
                sorted((S.get("rules") or [{}])[0].keys()), G("darpan", "/finance/porders/api/rules/state")[0]]
out["x_in_never"] = any(x["item"] == "W414 ITEM X" for x in (S.get("candidates") or {}).get("never") or [])
out["alpha_in_never"] = any(x["item"] == "W414 TEST ALPHA 10MG" for x in (S.get("candidates") or {}).get("never") or [])
# the items API
def items(u, qs):
    r = G(u, "/finance/porders/api/rules/items?q=" + qs); j = r[1] if isinstance(r[1], dict) else {}
    return [r[0], [x["item"] for x in (j.get("items") or [])], sorted((j.get("items") or [{}])[0].keys()) if j.get("items") else None]
out["items_alpha"] = items("manoj", "w414%20alpha")
out["items_gb"] = items("manoj", "gamma%20beta")
out["items_all"] = items("manoj", "")
out["items_none"] = items("manoj", "w414%20zzzqqq")
out["items_gate"] = G("darpan", "/finance/porders/api/rules/items?q=w414")[0]
# the tick: the answer carries counts + the row; the state then shows the rule and drops the candidate; untick; keep with a value
RJ = os.path.join(APP, "spine", "order_rules.json"); rj0 = open(RJ, "rb").read()
before = {r["rule"]: r["n"] for r in q("SELECT rule, COUNT(*) AS n FROM order_item_rule GROUP BY rule")} if NEW or True else {}
t = P("manoj", "/finance/porders/api/rules/item", {"item": "W414 TEST ALPHA 10MG", "rule": "never", "on": True})
tb = t[1] or {}
out["tick"] = [t[0], tb.get("counts"), tb.get("row"), sorted(tb.keys())]
S2 = G("manoj", "/finance/porders/api/rules/state")[1] or {}
out["after_tick"] = [any(x["item"] == "W414 TEST ALPHA 10MG" and x["rule"] == "never" for x in S2.get("item_rules") or []), any(x["item"] == "W414 TEST ALPHA 10MG" for x in (S2.get("candidates") or {}).get("never") or []),
                     "W414 TEST ALPHA 10MG" in ((S2.get("lists") or {}).get("never_reorder") or [])]
u = P("manoj", "/finance/porders/api/rules/item", {"item": "W414 TEST ALPHA 10MG", "rule": "never", "on": False})
out["untick"] = [u[0], (u[1] or {}).get("counts"), (u[1] or {}).get("row"), "W414 TEST ALPHA 10MG" in ((json.load(open(RJ)).get("never_reorder")) or [])]
kp = P("manoj", "/finance/porders/api/rules/item", {"item": "W414 TEST BETA", "rule": "keep", "on": True, "value": 50})
out["keep"] = [kp[0], ((kp[1] or {}).get("row") or {}).get("value"), ((kp[1] or {}).get("counts") or {}).get("by_rule", {}).get("keep")]
P("manoj", "/finance/porders/api/rules/item", {"item": "W414 TEST BETA", "rule": "keep", "on": False})
out["bad_rule"] = P("manoj", "/finance/porders/api/rules/item", {"item": "W414 TEST BETA", "rule": "nonsense", "on": True})[0]
out["tick_gate"] = P("darpan", "/finance/porders/api/rules/item", {"item": "W414 TEST BETA", "rule": "never", "on": True})[0]
out["before"] = before
out["after"] = {r["rule"]: r["n"] for r in q("SELECT rule, COUNT(*) AS n FROM order_item_rule GROUP BY rule")}
open(RJ, "wb").write(rj0)
db.execute("DELETE FROM order_item_rule WHERE item LIKE 'W414%'"); db.commit()
# the page
page = G("manoj", "/finance/approvals")[1]
i, j = page.find("/* ---- S410 (D626)"), page.find("function loadPOOos(){")
blk = page[i:j] if (i >= 0 and j > i) else ""
def balanced(s):
    """a string-aware count of {} () [] outside quotes and comments (the block carries no regex literal); (ok, detail)"""
    depth = {"{": 0, "(": 0, "[": 0}; close = {"}": "{", ")": "(", "]": "["}
    k, L, mode = 0, len(s), None
    while k < L:
        ch = s[k]
        if mode in ("'", '"'):
            if ch == "\\": k += 2; continue
            if ch == mode: mode = None
        elif mode == "//":
            if ch == "\n": mode = None
        elif mode == "/*":
            if s.startswith("*/", k): mode = None; k += 2; continue
        else:
            if ch in ("'", '"'): mode = ch
            elif s.startswith("//", k): mode = "//"
            elif s.startswith("/*", k): mode = "/*"
            elif ch in depth: depth[ch] += 1
            elif ch in close:
                depth[close[ch]] -= 1
                if depth[close[ch]] < 0: return False, "negative at %d" % k
        k += 1
    return all(v == 0 for v in depth.values()) and mode is None, (depth, mode)
out["block"] = dict(chars=len(blk), prompt=blk.count("prompt("), confirm=blk.count("confirm("), balanced=balanced(blk),
                    markers={m: (m in blk) for m in ("poKeepOpen(", "poTick(", "poTickAll(", "poApply(", "poEditOpen(", "poEditSave(", "poPauseAsk(", "poFreezeAsk(", "poApproveAsk(", "poApproveHTML(", "rules/items?q=", "poItemSuggest(", "poItemOff(", "poItemRowSet(", "Tick all shown", "show ticked only", "Yes, approve", "Yes, freeze", "poD_never", "poD_od", "poD_items", "poD_sup", "poD_audit", "Approve rules")},
                    old_markers={m: (m in blk) for m in ("poEdit(sn)", "Which setting for")}, approve_places=blk.count('poApproveHTML("Top")') + blk.count('poApproveHTML("Bottom")'))
out["page"] = dict(oosBar="oosBar" in page, loadPOOos="loadPOOos" in page, new_items="New items this month" in page, approve="Approve rules" in page, css="#poRules tr.ticked td" in page,
                   summary="edit in place" in page, one_block=page.count("function loadPORules(")==1, leak=bool(re.search(r"\b[6-9]\d{9}\b", page)))
print("JSON:" + json.dumps(out, default=str))
'''


def probe(appdir, mode, dbpath):
    env = dict(os.environ, APPDIR=appdir, MODE=mode, FINANCE_DB=dbpath, FINANCE_DIR=appdir, FINANCE_UI_DIR=os.path.join(appdir, "finance_ui"), FINANCE_ALLOW_HEADER_AUTH="1",
               PORDERS_SOURCE="tables", ORDER_TODAY="2026-09-28")
    p = subprocess.run([sys.executable, "-B", "-c", PROBE], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=appdir)
    O = next((json.loads(x[5:]) for x in p.stdout.splitlines() if x.startswith("JSON:")), None)
    if not O:
        sys.exit("!! the %s app did not answer: %s\n%s" % (mode, p.stderr[-3000:], p.stdout[-800:]))
    return O


O = probe(a.old, "old", a.db + ".old")
N = probe(a.app, "new", a.db)

print("-- 1  the state API is unchanged; the new items API")
check("the rules state answers the owner with the SAME keys, the same rule keys and the same counts as the box as it is (%d suppliers, %d never / %d on-demand candidates, %d item rules); darpan refused" % tuple(N["state"][2:6]),
      N["state"][0] == 200 and N["state"][1] == O["state"][1] and N["state"][2:6] == O["state"][2:6] and N["state"][6] == O["state"][6] and N["state"][7] in (302, 403), (N["state"][:2], O["state"][:2], N["state"][7]))
check("GET rules/items?q=: 'w414 alpha' -> exactly the two of our items carrying BOTH words (item, packing, qty); 'gamma beta' (any order) -> the one; an empty q -> capped at 20 names; a nonsense q -> none; darpan 403",
      N["items_alpha"][0] == 200 and sorted(N["items_alpha"][1]) == ["W414 ALPHA BETA GAMMA", "W414 TEST ALPHA 10MG"] and N["items_alpha"][2] == ["item", "packing", "qty"]
      and N["items_gb"][1] == ["W414 ALPHA BETA GAMMA"] and N["items_all"][0] == 200 and len(N["items_all"][1]) == 20 and N["items_none"] == [200, [], None] and N["items_gate"] == 403,
      (N["items_alpha"], N["items_gb"], len(N["items_all"][1]), N["items_none"], N["items_gate"]))

print("-- 2  a tick: the item rule lands and the answer carries the counts and the row -- the page needs no re-fetch")
b, t = N["before"], N["tick"]
check("our in-stock never-sold item is a never-reorder candidate; the tick answers 200 with counts.by_rule.never = before + 1, counts.item_rules, counts.lists and the row (rule never, set_by manoj); the state then lists it under item rules, drops it from the candidates, the spine's list holds it",
      N["alpha_in_never"] is True and t[0] == 200 and isinstance(t[1], dict) and t[1]["by_rule"]["never"] == b.get("never", 0) + 1 and t[1]["item_rules"] == sum(b.values()) + 1 and set(t[1]["lists"]) == {"never_reorder", "on_demand", "internal_use"}
      and t[2] and t[2]["rule"] == "never" and t[2]["set_by"] == "manoj" and t[2]["item"] == "W414 TEST ALPHA 10MG" and N["after_tick"] == [True, False, True], (N["alpha_in_never"], t, N["after_tick"]))
check("untick: 200, counts.by_rule.never back to before, row null, gone from the spine's list; keep-in-stock 50: the row carries value 50 and counts.by_rule.keep counts it; a nonsense rule 400; darpan 403; our rows removed, the counts as before, order_rules.json restored",
      N["untick"][0] == 200 and N["untick"][1]["by_rule"]["never"] == b.get("never", 0) and N["untick"][2] is None and N["untick"][3] is False and N["keep"] == [200, 50, b.get("keep", 0) + 1]
      and N["bad_rule"] == 400 and N["tick_gate"] == 403 and N["after"] == b, (N["untick"], N["keep"], N["bad_rule"], N["tick_gate"], N["after"], b))

print("-- 3  the owner's page: the new block, no prompt() / confirm(), balanced, everything S410's walk reads still there")
B = N["block"]
check("the rules block is there (%d chars), carries NO prompt( and NO confirm(, its braces / parens / brackets balance (string-aware), the old prompt-driven editor is gone" % B["chars"],
      B["chars"] > 8000 and B["prompt"] == 0 and B["confirm"] == 0 and B["balanced"][0] is True and not any(B["old_markers"].values()), (B["prompt"], B["confirm"], B["balanced"], B["old_markers"]))
check("every piece is in the block: poKeepOpen (open <details> + scroll kept over a draw), the check-list ticks (poTick / poTickAll / poApply), the inline supplier editor (poEditOpen / poEditSave / poPauseAsk), the inline Freeze and Approve confirmations, the items autocomplete, the item-rule rows, Approve rules at the TOP and the BOTTOM",
      all(B["markers"].values()) and B["approve_places"] == 2, ({k: v for k, v in B["markers"].items() if not v}, B["approve_places"]))
check("the page still carries what S410's walk reads (oosBar, loadPOOos, New items this month, Approve rules), the S414 CSS, the new card words, ONE loadPORules, and no 10-digit number",
      N["page"]["oosBar"] and N["page"]["loadPOOos"] and N["page"]["new_items"] and N["page"]["approve"] and N["page"]["css"] and N["page"]["summary"] and N["page"]["one_block"] and N["page"]["leak"] is False, N["page"])

print("-- 4  NEGATIVE CONTROL on the box as it is (S410's page and API)")
OB = O["block"]
check("NEGATIVE: the S410 block asks with prompt( and confirm( (%d / %d), has no poKeepOpen and no check-list; the items API is 404; the tick answers without counts or row" % (OB["prompt"], OB["confirm"]),
      OB["prompt"] >= 3 and OB["confirm"] >= 2 and OB["markers"]["poKeepOpen("] is False and OB["markers"]["poTick("] is False and O["items_alpha"][0] == 404 and O["tick"][0] == 200 and O["tick"][1] is None and O["tick"][2] is None,
      (OB["prompt"], OB["confirm"], OB["markers"]["poKeepOpen("], O["items_alpha"][0], O["tick"][:3]))

print(("WALK_S414 GREEN -- %d/%d" % (n, n)) if not fails else ("WALK_S414 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
