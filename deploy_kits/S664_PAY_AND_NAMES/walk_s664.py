"""walk_s664.py -- kit S664_PAY_AND_NAMES (Sanjeevni session S359, 26-Oct-2026). Writes nothing outside --scratch.
Loads supplier_msg, bank_sms and purchase_app from the root under test and runs them on a COPY of finance.db (rows of its own where a
fix is about a case, F-998).
  python walk_s664.py --new <root holding finance/ as built> --db <a COPY of finance.db> --scratch <dir> [--lib <root of unchanged modules>]
  --old <live root>: the control -- every S664 check red, every older check green."""
import argparse, os, re, shutil, sqlite3, sys, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--old"); ap.add_argument("--db"); ap.add_argument("--scratch"); ap.add_argument("--lib")
a = ap.parse_args()
ROOT = os.path.abspath(a.old or a.new)
LIB = os.path.abspath(a.lib or a.old or a.new)
a.scratch = os.path.abspath(a.scratch); os.makedirs(a.scratch, exist_ok=True)
DB = os.path.join(a.scratch, "walk.db")
shutil.copyfile(a.db, DB)
FIN = os.path.join(ROOT, "finance")
if LIB != ROOT:                                                    # the files under test beside every unchanged sibling (symlinks; nothing copied)
    FIN = os.path.join(a.scratch, "overlay", "finance"); os.makedirs(FIN)
    for e in os.listdir(os.path.join(LIB, "finance")):
        if not os.path.exists(os.path.join(ROOT, "finance", e)):
            os.symlink(os.path.join(LIB, "finance", e), os.path.join(FIN, e))
    for e in os.listdir(os.path.join(ROOT, "finance")):
        if e.endswith(".py"):
            shutil.copyfile(os.path.join(ROOT, "finance", e), os.path.join(FIN, e))
sys.path[:0] = [FIN]
os.chdir(a.scratch)
res = []


def check(name, ok, s664=True, note=""):
    res.append((name, bool(ok), s664, str(note)[:300]))


def con_():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


import flask                                                       # noqa: E402
import purchase_app, supplier_msg, bank_sms                        # noqa: E402
for m in (purchase_app, supplier_msg, bank_sms):
    assert os.path.dirname(os.path.abspath(m.__file__)) == FIN, "%s not loaded from the root under test" % m.__name__
DOC = {"user": "manoj", "roles": ["checker"], "role": "checker"}
STAFF = {"user": "shavez", "roles": ["viewer"], "role": "viewer"}
app = flask.Flask("walk_s664")
purchase_app.init(app, con_, lambda *r, **k: (dict(DOC), None))
cl = app.test_client()

# ---- A: the backup Bhejo asks first when the message was handed to the phone ---------------------------------------------------------
c = con_()
supplier_msg.ensure(c)
MONTH = "2099-02"
cols = [r[1] for r in c.execute("PRAGMA table_info(supplier_msg)")]
base = dict(month=MONTH, vendor_norm="WALK S664 A", vendor="WALK S664 A", kind="neft", ref="w", channel="whatsapp", to_number="", body="walk",
            status="queued", queued_at="2099-02-01T09:00:00", attempts=0)
def own(vendor, handed):
    d = dict(base, vendor_norm=vendor, vendor=vendor, handed_at=handed)
    d = {k: v for k, v in d.items() if k in cols}
    cur = c.execute("INSERT INTO supplier_msg (%s) VALUES (%s)" % (",".join(d), ",".join("?" * len(d))), list(d.values()))
    return cur.lastrowid
h_id = own("WALK S664 HANDED", "2099-02-01T09:05:00")
n_id = own("WALK S664 NOT HANDED", None)
c.commit()
supplier_msg._now = lambda: __import__("datetime").datetime(2099, 2, 1, 12, 0, 0)       # three hours after the queue: both rows pending


def card(u):
    with app.test_request_context("/finance/purchase/page/pay?month=" + MONTH):
        return supplier_msg.pay_card(con_(), dict(u), MONTH, "/finance/purchase", True, [])


def button(html, mid):
    m = re.search(r'<button class="sm" onclick="msgSend407\(%d[^"]*"[^>]*>Bhejo</button>' % mid, html)
    return m.group(0) if m else ""


ho, hs = card(DOC), card(STAFF)
bh, bn = button(ho, h_id), button(ho, n_id)
check("A1 the owner's Bhejo on a message handed to the phone asks first, in English (when it was handed, it may still go)",
      'data-handed="This message was handed to the reception phone on 01-Feb-2099 09:05' in bh, note=bh)
check("A2 ... and Shavez's asks in Roman Hindi", 'data-handed="Yeh message 01-Feb-2099 09:05 ko reception phone ko diya gaya tha' in button(hs, h_id), note=button(hs, h_id))
check("A3 a pending message never handed to the phone has its Bhejo exactly as before (no question)", bn and "data-handed" not in bn, s664=False, note=bn)
check("A4 the button's script asks (confirm) before it sends, and Cancel sends nothing", "if(t&&!confirm(t))return;fetch(P+'/api/supplier-msg/send'" in ho)
m = supplier_msg.messages(con_(), MONTH)
check("A5 the message list never carries the number or the text of the message (unchanged)", m and not any(("to_number" in x or "body" in x) for x in m), s664=False)
live = [x for x in supplier_msg.messages(con_(), "2026-09") if x["status"] in ("queued", "failed")]
check("A6 on the live rows: every September message still waiting carries when it was handed (%d)" % len(live),
      all("handed_at" in x for x in live), note=[(x["id"], x.get("handed_at")) for x in live])

# ---- B: the NEFT portion = the advice's lines -------------------------------------------------------------------------------------------
real = purchase_app._pay_rows
def fake(con, month):
    if month != MONTH:
        return real(con, month)
    return {}, [dict(route="NEFT", payable_p=500000, name="X", norm="X"), dict(route="NEFT", payable_p=-120000, name="Y", norm="Y"),
                dict(route="CHEQUE", payable_p=70000, name="Z", norm="Z"), dict(route="NEFT", payable_p=0, name="W", norm="W")]
purchase_app._pay_rows = fake
check("B1 a month with a negative NEFT line: the portion is the payable lines only (Rs 5,000, not Rs 3,800)", bank_sms.neft_portion_p(con_(), MONTH) == 500000,
      note=bank_sms.neft_portion_p(con_(), MONTH))
purchase_app._pay_rows = real
cc = con_()
fin = [r[0] for r in cc.execute("SELECT month FROM purchase_month WHERE status='final' ORDER BY month DESC LIMIT 3")]
same = []
for mo in fin:
    _s, g = real(cc, mo)
    same.append((mo, bank_sms.neft_portion_p(cc, mo), int(sum(x["payable_p"] for x in g if x["route"] == "NEFT" and x["payable_p"] > 0))))
check("B2 every recent finalised month: the portion equals its advice lines (%s)" % ", ".join(fin), same and all(p == q for _m, p, q in same), s664=False, note=same)

# ---- C: Scan reading, not Sarvam -------------------------------------------------------------------------------------------------------
r = cl.get("/finance/purchase/page/sarvam?month=2026-10")
html = r.get_data(as_text=True)
check("C1 the S446 page is titled Scan reading against Marg", r.status_code == 200 and "<h1>Scan reading against Marg" in html and "Sarvam against Marg" not in html,
      note=(r.status_code, re.findall(r"<h1>[^<]{0,60}", html)[:1]))
purchase_app.sarvam_compare = lambda con: None                        # the counter itself is the asset app's reading; here only the words are walked
purchase_app._s446_trial_months = lambda con: (["2099-03"], "2099-04-01")
purchase_app.sarvam_summary = lambda con, m: dict(n=3, agreed=2, supplier_wrong=0, billno_wrong=1, date_wrong=0, total_wrong=0, items_wrong=1, items_read=9, items_right=8)
lines = purchase_app.sarvam_lines(con_())
check("C2 the owner's Needs-you line says Scan reading trial (%d line(s))" % len(lines), lines and all(x["text"].startswith("Scan reading trial") for x in lines) and
      not any("Sarvam" in x["text"] for x in lines), note=[x["text"][:60] for x in lines])
check("C3 the page still counts the same bills (the counter is untouched)", r.status_code == 200 and "· read right in full" in html, s664=False)

for n, ok, s, note in res:
    print("%s  %s%s" % ("green" if ok else "RED  ", n, "" if ok else "   -- " + note))
g = sum(1 for _n, ok, _s, _x in res if ok)
if a.old:
    r6 = sum(1 for _n, ok, s, _x in res if s and not ok); ro = sum(1 for _n, ok, s, _x in res if not s and not ok)
    print("%d S664 check(s) red · %d older red · %d green" % (r6, ro, g))
else:
    print("%d of %d green" % (g, len(res)))
