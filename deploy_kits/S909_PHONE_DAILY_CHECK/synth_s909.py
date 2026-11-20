# synth_s909.py -- S909 on a COPY of the finance database with the code laid out beside it. Made-up numbers only (built at run time).
#   python3 synth_s909.py --code <dir with phone_check.py, supplier_msg.py, porders_s454.py, owner_notice.py ...> --finance <copy of finance.db>
import argparse, datetime as dt, importlib, json, os, random, re, sqlite3, sys, tempfile

ap = argparse.ArgumentParser(); ap.add_argument("--code", required=True); ap.add_argument("--finance", required=True); a = ap.parse_args()
W = tempfile.mkdtemp(prefix="s909synth_")
RAW = os.path.join(W, "wa_logs"); os.makedirs(RAW)
INBOX = os.path.join(W, "inbox.db")
STUB = os.path.join(W, "doctor.json")
os.environ.update(PHONE_CHECK_RAW_DIR=RAW, PHONE_CHECK_INBOX_DB=INBOX, PHONE_CHECK_DOCTOR_STUB=STUB, PHONE_CHECK_LOCK=os.path.join(W, "lk"),
                  FINANCE_OFF_DIR=os.path.join(W, "_off"), PHONE_CHECK_DB=a.finance)
_here = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _here]      # F-1441: never import the kit's own copy
sys.path.insert(0, a.code); sys.path.insert(1, os.path.join(a.code, "spine"))
R = []


def check(n, c, why=""):
    R.append((n, bool(c))); print(("ok   " if c else "RED  ") + n + ("" if c else "  " + str(why)[:220]))


def made_up_mobile():
    return str(random.choice("6789")) + "".join(str(random.randint(0, 9)) for _ in range(9))


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
today = dt.datetime.now(IST).date()
at = lambda h, m=0: dt.datetime(today.year, today.month, today.day, h, m, tzinfo=IST)
con = sqlite3.connect(a.finance); con.row_factory = sqlite3.Row
c_in = sqlite3.connect(INBOX); c_in.execute("CREATE TABLE msgs(rid INTEGER PRIMARY KEY, mid TEXT, phone TEXT, dir TEXT, ts TEXT, body TEXT)"); c_in.commit(); c_in.close()

try:
    PC = importlib.import_module("phone_check"); SM = importlib.import_module("supplier_msg")
except Exception as e:
    print("import failed: %s: %s" % (e.__class__.__name__, e)); print("synth_s909: 0 ok, 1 red"); sys.exit(1)


def arrive(code, where="raw"):
    if where == "raw":
        with open(os.path.join(RAW, "%s.jsonl" % today.isoformat()), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"body": {"payload": {"data": {"context": {"body": PC.body_for(code)}}}}}) + "\n")
    else:
        c = sqlite3.connect(INBOX); c.execute("INSERT INTO msgs(mid,phone,dir,ts,body) VALUES ('m','x','in','t',?)", (PC.body_for(code),)); c.commit(); c.close()


def back(run_id, minutes):
    """Age the running try by `minutes` (its row and its message's queued time)."""
    t = PC.iso(PC.now_local() - dt.timedelta(minutes=minutes))
    con.execute("UPDATE phone_check_try SET queued_at=? WHERE run_id=? AND attempt=(SELECT MAX(attempt) FROM phone_check_try WHERE run_id=?)", (t, run_id, run_id))
    con.commit()


def tries(run_id):
    return con.execute("SELECT attempt, code, msg_id, step, found_in FROM phone_check_try WHERE run_id=? ORDER BY attempt", (run_id,)).fetchall()


def run_row(run_id):
    return con.execute("SELECT result, step, text, doctor FROM phone_check_run WHERE id=?", (run_id,)).fetchone()


def phone_takes(msg_id, report=None):
    con.execute("UPDATE supplier_msg SET handed_at=? WHERE id=?", (PC.iso(PC.now_local()), msg_id))
    if report == "sent":
        con.execute("UPDATE supplier_msg SET status='sent', sent_at=?, sent_by='reception-phone' WHERE id=?", (PC.iso(PC.now_local()), msg_id))
    elif report == "failed":
        con.execute("UPDATE supplier_msg SET status='failed', attempts=attempts+1 WHERE id=?", (msg_id,))
    con.commit()


def notices(run_id):
    try:
        return con.execute("SELECT key, title, body FROM owner_notice WHERE key LIKE ?", ("phonecheck:%d:%%" % run_id,)).fetchall()
    except sqlite3.Error:
        return []


def finish(run_id):
    con.execute("UPDATE phone_check_run SET result=COALESCE(result,'pass'), decided_at=COALESCE(decided_at,?) WHERE id=?", (PC.iso(PC.now_local()), run_id)); con.commit()


NUM = made_up_mobile()
D10 = re.compile(r"\d{10}")

# T1 no number: nothing starts; the Needs-you asks for it once; the card says none saved
con.execute("DELETE FROM setting WHERE key LIKE 'phone_check.%'"); con.commit()
r = PC.tick(con, at(10, 5))
check("T1 no number: the 10:05 tick starts nothing", r.get("ok") and not con.execute("SELECT COUNT(*) FROM phone_check_run").fetchone()[0], r)
ny = PC.needs_you_lines(con)
check("T1 ...one Needs-you line asks for the number (card link)", len(ny) == 1 and ny[0]["cls"] == "warn" and ny[0]["href"].endswith("#s454phone"), ny)
check("T1 ...and it is among supplier_msg's Needs-you lines", any("daily check" in x["text"] for x in SM.needs_you_lines(con)))

# T2 save: refused junk, the number masked to its last four, never in a page in full
ok1, m1 = PC.save_to(con, "synth", "12ab")
ok2, m2 = PC.save_to(con, "synth", "+91 " + NUM)
check("T2 junk refused, a mobile saved masked", (not ok1) and ok2 and m2.endswith(NUM[-4:]) and NUM not in m2, (m1, m2))
card = PC.card_block(con)
check("T2 card: no 10-digit run, the last four shown", not D10.search(re.sub(r"<[^>]+>", " ", card)) and NUM[-4:] in card)
check("T2 card: no confirm()/alert()", "confirm(" not in card and "alert(" not in card)

# T3 the schedule: before 10:00 nothing; 10:05 one run, one 'check' message on the road; again at 10:10 no second run
PC.tick(con, at(9, 55))
n0 = con.execute("SELECT COUNT(*) FROM phone_check_run").fetchone()[0]
PC.tick(con, at(10, 5))
rid = con.execute("SELECT id FROM phone_check_run WHERE manual=0 AND day=?", (today.isoformat(),)).fetchone()
check("T3 nothing before 10:00; started at 10:05", n0 == 0 and rid is not None, n0)
rid = rid[0] if rid else 0
tr = tries(rid)
m = con.execute("SELECT kind, month, status, to_number, body FROM supplier_msg WHERE id=?", (tr[0][2],)).fetchone() if tr else None
check("T3 ...one message of kind 'check', queued, to the saved number, carrying its code", m and m[0] == "check" and m[2] == "queued" and m[3] == "91" + NUM and tr[0][1] in m[4], m and tuple(m)[:3])
PC.tick(con, at(10, 10))
check("T3 ...no second run the same day", con.execute("SELECT COUNT(*) FROM phone_check_run WHERE day=?", (today.isoformat(),)).fetchone()[0] == 1)

# T4 a pass: the code in the receiver's file -> passed, quiet (no notice, no Needs-you line)
phone_takes(tr[0][2], "sent"); arrive(tr[0][1], "raw")
PC.tick(con, at(10, 12))
rr = run_row(rid)
check("T4 arrived in the receiver's file: passed", rr and rr[0] == "pass", rr)
check("T4 ...quiet: no notice, no Needs-you line", not notices(rid) and not PC.needs_you_lines(con))


def manual():
    ok, v = PC.start_run(con, manual=True, who="synth")
    if not ok:
        raise RuntimeError(v)
    return v


def phone_asked(minutes_ago):
    con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('supplier_msg.phone_last', ?, 'synth')",
                ("%s 200" % PC.iso(PC.now_local() - dt.timedelta(minutes=minutes_ago)),)); con.commit()


# T5 a phone that has not asked at all is waited for (2 h), then FAILED naming MacroDroid; the message withdrawn; notice + red line
phone_asked(300)
r5 = manual(); t5 = tries(r5)
back(r5, 21); w5 = PC.step(con)
check("T5 not asked since the message was queued: still waiting at 21 min", w5.startswith("waiting for the phone") and run_row(r5)[0] is None, w5)
back(r5, 125); PC.step(con)
rr = run_row(r5); st = con.execute("SELECT status FROM supplier_msg WHERE id=?", (t5[0][2],)).fetchone()[0]
check("T5 ...after 2 h: FAILED, step named, MacroDroid named", rr[0] == "fail" and rr[1] == "not_collected" and "MacroDroid" in rr[2], rr)
check("T5 ...the message withdrawn (skipped), never handed later", st == "skipped", st)
nt = notices(r5); ny = PC.needs_you_lines(con)
check("T5 ...one notice and one red Needs-you line", len(nt) == 1 and nt[0][1] == "Phone check FAILED" and len(ny) == 1 and ny[0]["cls"] == "bad", (nt, ny))
check("T5 ...no 10-digit run in the notice or the line", not D10.search(nt[0][2] + ny[0]["text"]) if nt and ny else False)

# T5b the phone asks but does not collect: FAILED at 20 min (no 2-h wait)
r5b = manual(); back(r5b, 21); phone_asked(1); PC.step(con)
rr = run_row(r5b)
check("T5b the phone asked but did not collect: FAILED at 20 min", rr[0] == "fail" and rr[1] == "not_collected" and "asked the server" in rr[2], rr)

# T6 taken, no report -> a second message once; it arrives -> fixed itself (notice + info line)
r6 = manual(); t6 = tries(r6)
phone_takes(t6[0][2]); back(r6, 21); PC.step(con)
t6b = tries(r6)
check("T6 taken, no report: a second message queued, the first withdrawn", len(t6b) == 2 and t6b[0][3] == "no_report"
      and con.execute("SELECT status FROM supplier_msg WHERE id=?", (t6b[0][2],)).fetchone()[0] == "skipped", t6b)
arrive(t6b[1][1], "inbox"); PC.step(con)
rr = run_row(r6); nt = notices(r6); ny = PC.needs_you_lines(con)
check("T6 ...the second arrives (inbox store): fixed itself", rr[0] == "fixed" and "queued it once more" in rr[2], rr)
check("T6 ...a 'fixed itself' notice and an info line", len(nt) == 1 and nt[0][1] == "Phone check: fixed itself" and ny and ny[0]["cls"] == "info", (nt, ny))

# T7 reported sent, not in the inbox -> the doctor runs, a fresh message; it never arrives -> FAILED naming MyOperator
json.dump({"verdict": "FIXED", "words": "it restarted WhatsApp messages coming in"}, open(STUB, "w"))
r7 = manual(); t7 = tries(r7)
phone_takes(t7[0][2], "sent"); back(r7, 21); PC.step(con)
rr = run_row(r7); t7b = tries(r7)
check("T7 sent, not in the inbox: the doctor ran, a second message queued", rr[3] and rr[3].startswith("FIXED") and len(t7b) == 2 and t7b[0][3] == "not_in_inbox", (rr, t7b))
phone_takes(t7b[1][2], "sent"); back(r7, 21); PC.step(con)
rr = run_row(r7)
check("T7 ...the second also missing: FAILED, MyOperator named, the doctor's verdict in the words", rr[0] == "fail" and "MyOperator" in rr[2] and "FIXED" in rr[2], rr)
check("T7 ...the doctor ran once only", len(tries(r7)) == 2)

# T8 doctor path that mends: the second arrives -> fixed, doctor named
r8 = manual(); t8 = tries(r8)
phone_takes(t8[0][2], "sent"); back(r8, 21); PC.step(con)
t8b = tries(r8); arrive(t8b[1][1]); PC.step(con)
rr = run_row(r8)
check("T8 the fresh message arrives after the doctor: fixed itself, doctor named", rr[0] == "fixed" and "clinic doctor ran" in rr[2], rr)

# T9 a late first message while the second waits -> fixed (late), the second withdrawn
r9 = manual(); t9 = tries(r9)
phone_takes(t9[0][2]); back(r9, 21); PC.step(con)
t9b = tries(r9); arrive(t9b[0][1]); PC.step(con)
rr = run_row(r9)
check("T9 the first arrives late: fixed (late), the second withdrawn", rr[0] == "fixed" and "late" in rr[2]
      and con.execute("SELECT status FROM supplier_msg WHERE id=?", (t9b[1][2],)).fetchone()[0] == "skipped", rr)

# T10 waiting is waiting; one run at a time; a check now refused while one runs
r10 = manual(); w = PC.step(con)
ok_b, why_b = PC.start_run(con, manual=True)
check("T10 inside 20 min: waiting; a second check refused while one runs", w.startswith("waiting") and not ok_b and "already" in why_b, (w, why_b))
finish(r10)

# T11 the road: a check message never on the stuck list, never in the silent-phone line, never retried when failed
r11 = manual(); t11 = tries(r11)
con.execute("UPDATE supplier_msg SET handed_at=?, status='failed', attempts=1, last_try_at=? WHERE id=?",
            (PC.iso(PC.now_local() - dt.timedelta(hours=2)), PC.iso(PC.now_local() - dt.timedelta(hours=2)), t11[0][2])); con.commit()
check("T11 never on the stuck list", t11[0][2] not in {x["id"] for x in SM.s898_stuck(con, 0)})
sil = SM.s898_silent_line(con)
finish(r11)
r11s = manual(); t11s = tries(r11s)
con.execute("UPDATE supplier_msg SET handed_at=?, status='queued' WHERE id=?", (PC.iso(PC.now_local() - dt.timedelta(hours=1)), t11s[0][2]))
con.execute("UPDATE supplier_msg SET status='skipped' WHERE kind<>'check' AND status IN ('queued','failed') AND handed_at IS NOT NULL")
con.execute("UPDATE supplier_msg SET sent_by='x-synth' WHERE sent_by='reception-phone'")
con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('supplier_msg.phone_done_last', ?, 'synth')", (PC.iso(PC.now_local() - dt.timedelta(days=3)),))
con.commit()
sil = SM.s898_silent_line(con)
check("T11 a check message taken an hour ago, never reported: not counted by the silent-phone line", sil is None, sil)
finish(r11s)
try:
    from flask import Flask
    app = Flask("s909synth"); SM.init(app, lambda: con, lambda *x, **k: None)
    tok = con.execute("SELECT value FROM setting WHERE key='supplier_msg.phone_token'").fetchone()
    cl = app.test_client(); handed = []
    for _ in range(40):
        j = cl.get("/finance/api/supplier-msg/next", headers={"X-Phone-Token": tok[0] if tok else ""}).get_json() or {}
        if not j.get("id"):
            break
        handed.append(j["id"]); cl.post("/finance/api/supplier-msg/done", json={"id": j["id"], "ok": True}, headers={"X-Phone-Token": tok[0] if tok else ""})
    check("T11 the phone's door never hands a failed check message again", tok is not None and t11[0][2] not in handed, (bool(tok), len(handed)))
except Exception as e:
    check("T11 the phone's door", False, "%s: %s" % (e.__class__.__name__, e))

# T12 switches: the off file stops the tick and the lines
os.makedirs(os.environ["FINANCE_OFF_DIR"], exist_ok=True)
r12 = manual(); t12 = tries(r12); n12 = len(notices(r12))
open(os.path.join(os.environ["FINANCE_OFF_DIR"], "PHONE_CHECK_OFF"), "w").close()
r = PC.tick(con, at(10, 5)); ny = PC.needs_you_lines(con)
rr = run_row(r12); st = con.execute("SELECT status FROM supplier_msg WHERE id=?", (t12[0][2],)).fetchone()[0]
check("T12 PHONE_CHECK_OFF: the running check closed quietly, its message withdrawn, no lines", r.get("off") == "PHONE_CHECK_OFF"
      and rr[0] == "stopped" and st == "skipped" and ny == [] and len(notices(r12)) == n12 == 0, (r, tuple(rr), st, ny))
r = PC.tick(con, at(10, 10))
check("T12 ...and the next tick while off does nothing (no 'did')", r.get("off") and not r.get("did"), r)
os.remove(os.path.join(os.environ["FINANCE_OFF_DIR"], "PHONE_CHECK_OFF"))

# T12b a run older than 4 h is closed quietly, never a stale verdict
r12b = manual()
con.execute("UPDATE phone_check_run SET started_at=? WHERE id=?", (PC.iso(PC.now_local() - dt.timedelta(hours=7)), r12b)); con.commit()
PC.step(con); rr = run_row(r12b)
check("T12b a run older than 6 h, its message never taken: stopped, no notice", rr[0] == "stopped" and not notices(r12b), tuple(rr))
r12d = manual(); t12d = tries(r12d); phone_takes(t12d[0][2])
con.execute("UPDATE phone_check_run SET started_at=? WHERE id=?", (PC.iso(PC.now_local() - dt.timedelta(hours=7)), r12d)); con.commit()
PC.step(con); rr = run_row(r12d)
check("T12d a run older than 6 h whose message the phone took: FAILED with a notice", rr[0] == "fail" and rr[1] == "too_old" and len(notices(r12d)) == 1, tuple(rr))

# T12c the doctor stands aside (its own switch, an install) -> said, and still only once
json.dump({"verdict": "SKIPPED", "words": "the clinic doctor stood aside"}, open(STUB, "w"))
r12c = manual(); t12c = tries(r12c); phone_takes(t12c[0][2], "sent"); back(r12c, 21); PC.step(con)
rr = run_row(r12c)
check("T12c doctor stood aside: said in the run, a second message queued", rr[3] and rr[3].startswith("SKIPPED") and len(tries(r12c)) == 2, tuple(rr))
finish(r12c)

# T13 the card and its doors
try:
    PO = importlib.import_module("porders_s454")
    h = PO.phone_card(con, 'class="card"')
    part = h[h.index('id="s909"'):] if 'id="s909"' in h else ""
    check("T13 the card carries the daily check once, inside the Reception phone card", h.count('id="s909"') == 1 and h.count('id="s898"') == 1 and h.rstrip().endswith("</div>"))
    check("T13 ...no dialog, no 10-digit run", part and "confirm(" not in part and "alert(" not in part and not D10.search(re.sub(r"<[^>]+>", " ", part)))
    from flask import Flask
    app2 = Flask("s909po"); app2.register_blueprint(PO.bp)
    rules = {x.rule for x in app2.url_map.iter_rules()}
    check("T13 the two doors are mounted", {"/finance/porders/api/s909/clinic_number", "/finance/porders/api/s909/check_now"} <= rules)
except Exception as e:
    check("T13 card and doors", False, "%s: %s" % (e.__class__.__name__, e))

# T14 nothing written to the inbox store; the status line masked
c = sqlite3.connect(INBOX); n_in = c.execute("SELECT COUNT(*) FROM msgs").fetchone()[0]; c.close()
check("T14 the inbox store: only the made-up arrival this walk put there", n_in == 1, n_in)
check("T14 the status line masked", not D10.search(PC.status_line(con)))

con.close()
bad = [n for n, ok in R if not ok]
print("synth_s909: %d ok, %d red" % (len(R) - len(bad), len(bad)))
sys.exit(1 if bad else 0)
