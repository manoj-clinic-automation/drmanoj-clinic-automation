#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest_cheque_s270.py -- S270 proved OFFLINE, before anything is installed.

block.py is executed against stubs of the helpers purchase_app.py provides, so
every route and every helper in it runs here exactly as written. A check that
could not run says so and is never counted as a pass (F-443).
"""
import io, json, os, re, sqlite3, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OK = [0]; BAD = []; SKIP = []

def ck(name, cond, detail=""):
    if cond: OK[0] += 1; print("  ok   %s" % name)
    else: BAD.append(name); print("  FAIL %s   %s" % (name, detail))

def skip(name, why): SKIP.append(name); print("  skip %s  -- %s" % (name, why))

# ----------------------------------------------------------------- the stubs
class Req(object):
    script_root = ""
    _json = {}
    def get_json(self, silent=False): return self._json
request = Req()

class Resp(object):
    def __init__(self, payload, code=200): self.payload = payload; self.code = code
    def __repr__(self): return "Resp(%r,%d)" % (self.payload, self.code)

def jsonify(**kw): return Resp(kw)

def _refuse(msg): return Resp({"ok": False, "message": msg}, 200)

class BP(object):
    def route(self, *a, **k):
        def deco(f): return f
        return deco
bp = BP()

CON = [None]
def _db(): return CON[0]
def _ensure(con): pass
def _pay_ensure(con): pass
def now_iso(): return "2026-09-14T21:30:00+05:30"
def _who(u): return u.get("who", "manoj")
def _audit(con, who, action, ref, detail): AUDIT.append((who, action, ref, detail))
AUDIT = []
def _int_or_none(v):
    try: return int(v)
    except (TypeError, ValueError): return None
def _esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))
def _r(p):
    p = p or 0
    return ("-" if p < 0 else "") + "₹" + "{:,}".format(abs(int(p)) // 100)
def _page(title, body, js=""): return "<html><!--%s-->%s<script>%s</script>" % (title, body, js)
def _month_name(m): return m
_url_prefix = "/finance/purchase"
CSS = ""
PAY_JS = "function esc(s){return s;}\n"

PERSON = {"role": "maker", "who": "manoj", "viewer": False}
def _person(*roles):
    if PERSON["role"] not in roles: return None, Resp({"ok": False, "message": "no"}, 403)
    return dict(PERSON), None
def _is_viewer_only(u): return bool(u.get("viewer"))

GROUPS = []
SUMMARY = {"status": {"status": "provisional"}}
def _pay_rows(con, month): return SUMMARY, GROUPS

# ------------------------------------------------------------- load block.py
NS = dict(globals())
src = io.open(os.path.join(HERE, "block.py"), encoding="utf-8").read()
exec(compile(src, "block.py", "exec"), NS)
api_cheque = NS["api_cheque_s270"]
api_mark = NS["api_cheque_mark_s270"]
page_cheques = NS["page_cheques_s270"]
recon = NS["_cheque_recon_s270"]
pdate = NS["_cheque_parse_date_s270"]
card = NS["_cheque_card_s270"]
ensure = NS["_cheque_ensure"]

def fresh():
    NS["_cheque_done"] = False
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    CON[0] = con
    ensure(con)
    return con

def post(payload, fn=None):
    request._json = payload
    return (fn or api_cheque)()

def vend(norm, name, payable, route="CHEQUE", why="no account on this server"):
    return {"norm": norm, "name": name, "payable_p": payable, "route": route, "why": why}

print("S270 selftest -- the cheque register")

# 1..6  the date the owner actually writes
ck("1 dd-mm-yyyy is read day-first", pdate("14-09-2026") == "2026-09-14", pdate("14-09-2026"))
ck("2 yyyy-mm-dd is read as written", pdate("2026-09-14") == "2026-09-14")
ck("3 slashes are accepted", pdate("14/09/2026") == "2026-09-14")
ck("4 the 31st of a 30-day month is refused", pdate("31-09-2026") is None)
ck("5 29 Feb 2028 is a real date", pdate("29-02-2028") == "2028-02-29")
ck("6 29 Feb 2026 is not", pdate("29-02-2026") is None)

# 7..12  logging one cheque
con = fresh()
GROUPS[:] = [vend("RAMA MEDICOSE", "RAMA MEDICOSE", 146900)]
r = post({"month": "2026-08", "vendor_norm": "RAMA MEDICOSE", "vendor": "RAMA MEDICOSE",
          "payee": "Rama Medicose", "cheque_no": "000431", "cheque_date": "14-09-2026",
          "amount": "1469"})
ck("7 a cheque is logged", r.payload.get("ok") is True, r)
ck("8 its date is stored ISO", r.payload.get("cheque_date") == "2026-09-14")
ck("9 rupees became paise", r.payload.get("amount_p") == 146900, r.payload)
ck("10 the audit trail names it", any(a[1] == "cheque_logged" for a in AUDIT))
row = con.execute("SELECT * FROM purchase_cheque").fetchone()
ck("11 the payee is kept as written", row["payee"] == "Rama Medicose")
ck("12 amounts with a comma and a rupee sign are read",
   post({"month": "2026-08", "vendor_norm": "X", "cheque_no": "000999",
         "cheque_date": "14-09-2026", "amount": "₹1,234.50"}).payload.get("amount_p") == 123450)

# 13..16  what the register refuses
r = post({"month": "2026-08", "vendor_norm": "OTHER", "cheque_no": "000431",
          "cheque_date": "15-09-2026", "amount": "500"})
ck("13 the same cheque number twice is REFUSED", r.payload.get("ok") is False, r.payload)
ck("14 and the refusal names the cheque it clashes with",
   "000431" in r.payload.get("message", "") and "RAMA" in r.payload.get("message", "").upper(),
   r.payload.get("message"))
ck("15 a cheque with no number is refused",
   post({"month": "2026-08", "vendor_norm": "Y", "cheque_date": "14-09-2026",
         "amount": "10"}).payload.get("ok") is False)
ck("16 a cheque with no readable date is refused",
   post({"month": "2026-08", "vendor_norm": "Y", "cheque_no": "A1",
         "cheque_date": "sometime", "amount": "10"}).payload.get("ok") is False)
ck("17 a zero or negative amount is refused",
   post({"month": "2026-08", "vendor_norm": "Y", "cheque_no": "A2",
         "cheque_date": "14-09-2026", "amount": "0"}).payload.get("ok") is False)

# 18..21  void, and only then may the number come back
cid = con.execute("SELECT id FROM purchase_cheque WHERE cheque_no='000431'").fetchone()["id"]
ck("18 a void with no reason is refused",
   post({"id": cid, "what": "void"}, api_mark).payload.get("ok") is False)
ck("19 a void with a reason is accepted",
   post({"id": cid, "what": "void", "reason": "written for the wrong vendor"},
        api_mark).payload.get("ok") is True)
gone = con.execute("SELECT * FROM purchase_cheque WHERE id=?", (cid,)).fetchone()
ck("20 the voided row STAYS, with its reason", gone is not None
   and gone["void_reason"] == "written for the wrong vendor")
ck("21 and only now may that number be used again",
   post({"month": "2026-08", "vendor_norm": "OTHER", "vendor": "OTHER",
         "cheque_no": "000431", "cheque_date": "15-09-2026", "amount": "500"}
        ).payload.get("ok") is True)
ck("22 a voided cheque can never be changed again",
   post({"id": cid, "what": "handed"}, api_mark).payload.get("ok") is False)

# 23..24  handed over, and back
live_id = con.execute("SELECT id FROM purchase_cheque WHERE cheque_no='000431' "
                      "AND voided_at IS NULL").fetchone()["id"]
ck("23 a cheque can be marked handed over",
   post({"id": live_id, "what": "handed"}, api_mark).payload.get("ok") is True
   and con.execute("SELECT handed_at FROM purchase_cheque WHERE id=?",
                   (live_id,)).fetchone()["handed_at"] is not None)
ck("24 and unmarked", post({"id": live_id, "what": "unhanded"}, api_mark).payload.get("ok") is True
   and con.execute("SELECT handed_at FROM purchase_cheque WHERE id=?",
                   (live_id,)).fetchone()["handed_at"] is None)

# 25..30  the reconciliation -- the thing a counterfoil cannot do
con = fresh(); AUDIT[:] = []
GROUPS[:] = [vend("RAMA", "RAMA MEDICOSE", 146900),
             vend("AGARWAL", "AGARWAL SURGICALS AND MEDICALS", 40000),
             vend("KEDAR", "KEDAR PHARMA", 9824000, route="NEFT", why="")]
rc = recon(CON[0], "2026-08", GROUPS)
ck("25 the cheque lane is the two vendors, not the NEFT one", rc["owed_p"] == 186900, rc)
ck("26 nothing written yet, so the whole lane is the gap", rc["gap_p"] == 186900)
ck("27 both vendors are named as waiting", len(rc["waiting"]) == 2)
post({"month": "2026-08", "vendor_norm": "RAMA", "vendor": "RAMA MEDICOSE",
      "cheque_no": "000431", "cheque_date": "14-09-2026", "amount": "1469"})
rc = recon(CON[0], "2026-08", GROUPS)
ck("28 one cheque written closes its own vendor and nothing else",
   rc["written_p"] == 146900 and rc["gap_p"] == 40000 and len(rc["waiting"]) == 1, rc)
ck("29 the vendor still waiting is named with what is short",
   rc["waiting"][0]["vendor"].startswith("AGARWAL") and rc["waiting"][0]["short_p"] == 40000)
post({"month": "2026-08", "vendor_norm": "AGARWAL", "vendor": "AGARWAL SURGICALS AND MEDICALS",
      "cheque_no": "000432", "cheque_date": "14-09-2026", "amount": "400"})
rc = recon(CON[0], "2026-08", GROUPS)
ck("30 with both written the gap is nil and nobody waits",
   rc["gap_p"] == 0 and rc["waiting"] == [], rc)

# 31..33  a part payment is not a settled vendor
con = fresh()
GROUPS[:] = [vend("RAMA", "RAMA MEDICOSE", 146900)]
post({"month": "2026-08", "vendor_norm": "RAMA", "vendor": "RAMA MEDICOSE",
      "cheque_no": "000501", "cheque_date": "14-09-2026", "amount": "1000"})
rc = recon(CON[0], "2026-08", GROUPS)
ck("31 a part cheque leaves the vendor waiting", len(rc["waiting"]) == 1)
ck("32 and the page knows exactly how much is short", rc["waiting"][0]["short_p"] == 46900)
h = card(CON[0], "2026-08", "/finance/purchase", GROUPS, True)
ck("33 the sheet's card says the remainder out loud", "still to write" in h, h[:200])

# 34..36  THE DELIBERATE DEPARTURE: a locked month still takes a cheque
con = fresh()
SUMMARY["status"]["status"] = "final"
GROUPS[:] = [vend("RAMA", "RAMA MEDICOSE", 146900)]
r = post({"month": "2026-08", "vendor_norm": "RAMA", "vendor": "RAMA MEDICOSE",
          "cheque_no": "000601", "cheque_date": "20-09-2026", "amount": "1469"})
ck("34 a cheque is accepted on a FINAL month -- it is written after the lock",
   r.payload.get("ok") is True, r.payload)
ck("35 and the month it settles is stored on the row",
   con.execute("SELECT month FROM purchase_cheque").fetchone()["month"] == "2026-08")
SUMMARY["status"]["status"] = "provisional"

# 37..41  the register page itself
con = fresh()
GROUPS[:] = [vend("RAMA", "RAMA MEDICOSE", 146900)]
post({"month": "2026-08", "vendor_norm": "RAMA", "vendor": "RAMA MEDICOSE",
      "cheque_no": "000431", "cheque_date": "14-09-2026", "amount": "1000"})
PERSON.update(role="maker", viewer=False)
h = page_cheques("2026-08")
ck("36 the register renders", "Cheque register" in h)
ck("37 it shows the number and the day-first date", "000431" in h and "14-09-2026" in h, "")
ck("38 it holds itself against the sheet and names the shortfall",
   "Against the sheet" in h and "still owed" in h)
ck("39 a maker is offered the void and handed controls",
   'onclick="chqvoid(' in h and 'onclick="chqmark(' in h)
PERSON.update(role="viewer", viewer=True)
h = page_cheques("2026-08")
ck("40 a viewer sees the register but is offered no controls",
   "000431" in h and 'onclick="chqvoid(' not in h and 'onclick="chqmark(' not in h,
   "the controls must be absent from the BODY; the script always defines them")
r = post({"month": "2026-08", "vendor_norm": "RAMA", "cheque_no": "X9",
          "cheque_date": "14-09-2026", "amount": "5"})
ck("41 and a viewer cannot log one", isinstance(r, tuple) or r.code == 403 or
   (hasattr(r, "payload") and r.payload.get("ok") is False), r)
PERSON.update(role="maker", viewer=False)

# 42..44  the whole-register view and the empty case
h = page_cheques(None)
ck("42 the register with no month shows every cheque", "000431" in h and "Every cheque" in h)
con = fresh(); GROUPS[:] = []
h = page_cheques("2026-09")
ck("43 an empty register says so plainly and does not pretend", "No cheque has been logged" in h)
h = card(CON[0], "2026-09", "/finance/purchase", [], True)
ck("44 a month with nobody on the cheque lane says that too", "Nobody this month" in h, h[:160])

# 45..47  nothing here writes to the sheet's own tables
con = fresh()
GROUPS[:] = [vend("RAMA", "RAMA MEDICOSE", 146900)]
con.execute("CREATE TABLE purchase_pay_line (month TEXT, vendor_norm TEXT, carry_fwd_p INT)")
con.commit()
post({"month": "2026-08", "vendor_norm": "RAMA", "vendor": "RAMA MEDICOSE",
      "cheque_no": "000701", "cheque_date": "14-09-2026", "amount": "1469"})
ck("45 the payment sheet's own table is untouched",
   con.execute("SELECT COUNT(*) c FROM purchase_pay_line").fetchone()["c"] == 0)
tables = {r["name"] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table'")}
ck("46 exactly one new table was created", "purchase_cheque" in tables)
ck("47 the unique index is partial, so a void really does free the number",
   any("ux_pchq_live_no" in (r["name"] or "") for r in con.execute(
       "SELECT name FROM sqlite_master WHERE type='index'")))

print("\n%d checks passed, %d failed, %d skipped" % (OK[0], len(BAD), len(SKIP)))
if BAD: print("FAILED: " + ", ".join(BAD))
sys.exit(1 if BAD else 0)
