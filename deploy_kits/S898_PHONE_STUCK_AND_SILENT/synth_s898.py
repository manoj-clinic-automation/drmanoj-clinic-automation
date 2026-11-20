# synth_s898.py -- S898 on a COPY of the finance database with the code laid out beside it.
#   python3 synth_s898.py --code <dir with supplier_msg.py, porders_s454.py, finance_ui/> --finance <copy of finance.db>
import argparse, datetime as dt, importlib, json, os, re, sqlite3, sys
ap = argparse.ArgumentParser(); ap.add_argument("--code", required=True); ap.add_argument("--finance", required=True); a = ap.parse_args()
sys.path.insert(0, a.code); sys.path.insert(1, os.path.join(a.code, "spine"))
R = []
def check(n, c, why=""):
    R.append((n, bool(c))); print(("ok   " if c else "RED  ") + n + ("" if c else "  " + str(why)[:200]))
try:
    SM = importlib.import_module("supplier_msg")
except Exception as e:
    print("import supplier_msg failed:", e); SM = None
con = sqlite3.connect(a.finance); con.row_factory = sqlite3.Row
has = lambda f: SM is not None and hasattr(SM, f)
iso = lambda d: d.replace(microsecond=0).isoformat()
now = dt.datetime.now()

# T1 the stuck list: no order, no test, every row taken by the phone and not reported
try:
    st = SM.s898_stuck(con)
    kinds = {r["kind"] for r in st}
    check("T1 stuck list: rows, never an order or a test", len(st) >= 1 and not (kinds & {"order", "test"}), kinds)
    check("T1 ...and no number or message body in a row", all(set(r) == {"id", "kind", "what", "month", "vendor", "queued", "handed"} for r in st))
except Exception as e:
    check("T1 stuck list", False, e); st = []

# T2 the silent-phone line: appears, then goes when a report arrives
try:
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('supplier_msg.phone_done_last', ?)", (iso(now - dt.timedelta(days=3)),))
    con.execute("UPDATE supplier_msg SET sent_by='x-synth' WHERE sent_by='reception-phone'")
    mid = con.execute("INSERT INTO supplier_msg (month, vendor_norm, vendor, kind, ref, channel, to_number, body, status, queued_at, handed_at, attempts) "
                      "VALUES ('synth','SYNTH','SYNTH DEALER','order',1,'whatsapp',NULL,'b','queued',?,?,0)",
                      (iso(now - dt.timedelta(minutes=40)), iso(now - dt.timedelta(minutes=35)))).lastrowid
    con.commit()
    l1 = SM.s898_silent_line(con)
    check("T2 silent phone: one Needs-you line naming MacroDroid", bool(l1) and "MacroDroid" in l1["text"] and l1["cls"] == "bad", l1)
    ny = SM.needs_you_lines(con)
    check("T2 ...and it is among the supplier Needs-you lines", any("'sent' report" in x["text"] for x in ny))
    SM._s898_done_seen(con)
    check("T2 a report arriving clears the line", SM.s898_silent_line(con) is None)
except Exception as e:
    check("T2 silent line", False, e)

# T3 send again: a stuck message is handed out once more; anything else is refused
try:
    if st:
        sid = st[0]["id"]
        n = SM.s898_resend(con, "synth", [sid, mid, 999999, "x"])
        r = con.execute("SELECT handed_at, status FROM supplier_msg WHERE id=?", (sid,)).fetchone()
        r2 = con.execute("SELECT handed_at FROM supplier_msg WHERE id=?", (mid,)).fetchone()
        check("T3 send again: only the stuck one, handed mark cleared", n == 1 and r[0] is None and r[1] == "queued" and r2[0] is not None, (n, tuple(r)))
    else:
        check("T3 send again (no stuck rows in this copy)", True)
except Exception as e:
    check("T3 send again", False, e)

# T4 remove: skipped and kept, off the list
try:
    st2 = SM.s898_stuck(con)
    if st2:
        rid = st2[-1]["id"]
        n = SM.s898_remove(con, "synth", [rid])
        r = con.execute("SELECT status, last_error FROM supplier_msg WHERE id=?", (rid,)).fetchone()
        check("T4 remove: skipped, kept with who, off the list", n == 1 and r[0] == "skipped" and "removed by synth" in r[1]
              and rid not in {x["id"] for x in SM.s898_stuck(con)}, tuple(r))
    else:
        check("T4 remove (no stuck rows in this copy)", True)
except Exception as e:
    check("T4 remove", False, e)

# T5 the card: its new part, two-tap, no number, no dialog
try:
    PO = importlib.import_module("porders_s454")
    h = PO.phone_card(con, 'class="card"')
    check("T5 the card carries the new part once", h.count('id="s898"') == 1 and "Last \"sent\" report" in h, h[-300:])
    check("T5 two-tap, no confirm()/alert() in the new part", "Tap again to confirm" in h and "confirm(" not in h[h.index('id="s898"'):]
          and "alert(" not in h[h.index('id="s898"'):])
    body = re.sub(r"<[^>]+>", " ", h[h.index('id="s898"'):])
    check("T5 no 10-digit number in the card's new part", not re.search(r"\d{10}", body))
    from flask import Flask
    app = Flask("synth"); app.register_blueprint(PO.bp)
    rules = {r.rule for r in app.url_map.iter_rules()}
    check("T6 the two doors are mounted", {"/finance/porders/api/s898/resend", "/finance/porders/api/s898/remove"} <= rules)
except Exception as e:
    check("T5/T6 card and doors", False, "%s: %s" % (e.__class__.__name__, e))

# T7 the Hub's Go to carries the link once
try:
    html = open(os.path.join(a.code, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
    check("T7 the Hub's Go to: one link to the card", html.count('href="/finance/porders?old=1#s454phone"') == 1)
except Exception as e:
    check("T7 Go to", False, e)

con.close()
bad = [n for n, ok in R if not ok]
print("synth_s898: %d ok, %d red" % (len(R) - len(bad), len(bad)))
sys.exit(1 if bad else 0)
