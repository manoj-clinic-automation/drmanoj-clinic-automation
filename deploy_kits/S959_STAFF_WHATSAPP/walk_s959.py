#!/usr/bin/env python3
"""walk_s959.py -- S959_STAFF_WHATSAPP: the walk of the WhatsApp tab's reply on the staff Call Console, on S948's MADE-UP
console.db + inbox.db (every number 500000xxxx; 'today' 24-Nov 11:30), the inbox's times in the store's own +05:30 form,
a STUBBED sender (nothing is sent; no key is real) and every store, log and mail in a temp folder.

  python walk_s959.py walk <code dir>            every check; exit 0 only when all pass (walk_s948.py sits beside this file)
  python walk_s959.py prefix <FROM> <TO>         portal_inbox.py: the TO is the FROM's bytes + one block with no route
  python walk_s959.py page <FROM dump> <TO dump> the owner's page (walk_s948.py dump): equal but for the one Accept line
"""
import datetime as _dt
import json
import os
import sqlite3
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FAILS = []
N = [0]
CC_OLD = "b.textContent=(ans==='accept'?'Accepted — off the count':'It stands ✓'); b.classList.add('done');"
CC_NEW = ("b.textContent=(ans==='accept'?(b.textContent.indexOf('verdict')>=0?'Accepted — the verdict was wrong':"
          "'Accepted — off the count'):'It stands ✓'); b.classList.add('done');")


def ok(cond, what):
    N[0] += 1
    print(("  PASS  " if cond else "  FAIL  ") + what)
    if not cond:
        FAILS.append(what)


def finish():
    print("%d checks, %d failed" % (N[0], len(FAILS)))
    print("ALL PASS" if not FAILS else "SOME FAILED")
    sys.exit(0 if not FAILS else 1)


def J(resp):
    try:
        j = resp.get_json()
    except Exception:
        j = None
    return j if isinstance(j, dict) else {"ok": None, "status": resp.status_code}


def do_walk(code):
    import walk_s948 as W
    W.CODE = code
    root = tempfile.mkdtemp(prefix="s959w_")
    os.makedirs(os.path.join(root, "raw"))
    for k, v in (("INBOX_STORE", root), ("INBOX_RAW_DIR", os.path.join(root, "raw")), ("INBOX_WA_ENV", os.path.join(root, "no.env")),
                 ("INBOX_PORTAL_LOG", os.path.join(root, "no_portal_log.csv")), ("PORTAL_WA_DIR", os.path.join(root, "wa_portal")),
                 ("PORTAL_CONSOLE_DB", os.path.join(root, "no_console.db"))):
        os.environ[k] = v                                # before portal_inbox / portal_wa are imported: no real path is read
    con_p, inbox_p = W.make_fixture(root)
    i = sqlite3.connect(inbox_p)                     # the store's own time form (iso + 05:30), as the receiver writes it
    i.execute("UPDATE msgs SET ts = replace(ts, ' ', 'T') || '+05:30'")
    d2 = (W.NOW.date() - _dt.timedelta(days=2)).isoformat()
    i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
              ("m11a", W.ph(11), "in", d2 + "T10:00:00+05:30", "text", "Appointment chahiye", "", "", ""))
    for n in range(40):                              # a long chat: only the newest 30 come back
        i.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES (?,?,?,?,?,?,?,?,?)",
                  ("m10x%02d" % n, W.ph(10), "in", W.TODAY + "T08:%02d:00+05:30" % n, "image" if n == 39 else "text",
                   "old %02d" % n, "", "", ""))
    i.commit()
    i.close()
    sys.path.insert(0, code)
    import portal_inbox as PI
    import portal_wa as PW
    ok(PI.DB_PATH == inbox_p and PI.PORTAL_LOG.startswith(root) and PW.LOG.startswith(root),
       "the walk's inbox, portal log and template log are temp files")
    clock = {"t": W.NOW.replace(tzinfo=PI.IST)}
    PI.now_ist = lambda: clock["t"]
    PI.patients = lambda: {}
    noted = []
    PI._note_refused = lambda e: noted.append(e)
    PI.SMTP_CLASS = None
    sent = []
    mode = {"m": "ok"}

    during = []

    def fake_send(token, phone, data, timeout=30, trace=None):
        sent.append((token, phone, json.dumps(data)))
        cx = sqlite3.connect(inbox_p)
        during.append(cx.execute("SELECT COUNT(*), MAX(sent_by) FROM msgs WHERE phone=? AND status='sending'", (phone,)).fetchone())
        cx.close()
        if trace is not None:
            trace.update({"endpoint": "stub", "request_json": "", "status": 200, "raw": "", "headers": {}, "ms": 1})
        if mode["m"] == "gateway":
            trace.update({"status": 500, "headers": {"x-amzn-ErrorType": "AuthorizerConfigurationException"}})
            return False, "", "MyOperator refused (HTTP 500): authorizer"
        if mode["m"] == "refuse":
            trace.update({"status": 400})
            return False, "", "MyOperator refused (HTTP 400): bad"
        if mode["m"] == "timeout":
            trace.update({"status": 0, "raw": "no answer: TimeoutError"})
            return False, "", "could not reach MyOperator (TimeoutError)"
        if mode["m"] == "echo":                     # the receiver ingests MyOperator's own 'out' echo before the settle
            cx = sqlite3.connect(inbox_p)
            cx.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES ('wamid.ECHO',?,'out',?,'text',?,'sent',NULL,'log')",
                       (phone, clock["t"].strftime("%Y-%m-%dT%H:%M:%S+05:30"), json.loads(data[0] if isinstance(data, tuple) else json.dumps(data))["context"]["body"]))
            cx.commit()
            cx.close()
            return True, "wamid.ECHO", ""
        return True, "wamid.T%d" % len(sent), ""
    PI.myop_send = fake_send
    tok = {"t": "TESTKEY-not-real"}
    PI._token = lambda cfg_get: tok["t"]
    tsent = []
    real_tsend = PW.send

    def fake_tsend(phone, name, values, by, token, dry_run=True, timeout=20):
        if dry_run:
            return real_tsend(phone, name, values, by, token, dry_run=True)
        tsent.append((phone, name, json.dumps(values), by))
        return {"ok": True, "message_id": "wamid.TPL%d" % len(tsent), "mode": "LIVE", "error": ""}
    PW.send = fake_tsend
    PW.normalize_phone = lambda raw: "".join(ch for ch in str(raw) if ch.isdigit())[-10:]   # the walk's 500000xxxx numbers pass

    app, cc, pm, _ = W.build_app(root, con_p, inbox_p, W.NOW)
    import calls_staff as CS
    base = cc._CFG
    over = {}
    cc._CFG = lambda k, d="": over[k] if k in over else base(k, d)
    CS._CFG = cc._CFG                                # the sender reads the same settings (the live portal hands both the one cfg_get)
    cl = app.test_client()
    H = W.H

    def page(u, role="staff", q=""):
        r = cl.get("/portal/console/staff" + q, headers=H(u, role))
        return r.status_code, r.get_data(as_text=True)

    def lists(u):
        return J(cl.get("/portal/console/staff/api/lists", headers=H(u))).get("tabs", {"wa": []})

    def chat(u, ph, role="staff", hdr=True):
        h = H(u, role)
        if hdr:
            h["X-Staff-Console"] = "1"
        r = cl.get("/portal/console/staff/api/wa/chat?phone=" + ph, headers=h)
        return r.status_code, J(r)

    def post(u, path, body, role="staff", hdr=True):
        r = cl.post("/portal/console/staff/api/wa/" + path, headers=H(u, role, post=hdr), data=json.dumps(body),
                    content_type="application/json")
        return r.status_code, J(r)

    def rows(ph):
        c = sqlite3.connect(inbox_p)
        c.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in c.execute("SELECT * FROM msgs WHERE phone=? AND dir='out' ORDER BY rid", (ph,))]
        finally:
            c.close()

    def slog():
        p = os.path.join(root, "send_log.jsonl")
        return [json.loads(x) for x in open(p, encoding="utf-8")] if os.path.exists(p) else []

    print("[1] the marks, the switch, the templates offered")
    ok(getattr(CS, "KIT_S959", "") == "S959_STAFF_WHATSAPP" and CS.VERSION == "S951 1.1", "kit S959 marked; VERSION stays 'S951 1.1'")
    ok(getattr(PI, "S959_KIT", "") == "S959_STAFF_WHATSAPP" and all(hasattr(PI, f) for f in ("staff_chat", "staff_send_text", "staff_send_template")),
       "portal_inbox carries the three callables")
    won = getattr(CS, "wa_send_on", lambda: None)
    ok(won() is True, "PORTAL_STAFF_WA_SEND unset -> on")
    for v in ("0", "off", "No", "false", 0, False):
        over["PORTAL_STAFF_WA_SEND"] = v
        ok(won() is False, "PORTAL_STAFF_WA_SEND=%r -> off" % (v,))
    over["PORTAL_STAFF_WA_SEND"] = ""
    ok(won() is True, "the switch empty -> the default (on)")
    over.pop("PORTAL_STAFF_WA_SEND")
    wt = getattr(CS, "wa_templates", lambda n="": [])
    t0 = wt("Ram")
    ok([x["key"] for x in t0] == ["welcome_template"] and t0[0]["title"] == "Enquiry acknowledgement" and t0[0]["name"] == "Ram"
       and "[name]" in t0[0]["preview"] and "{var_1}" not in t0[0]["preview"], "default: the Enquiry acknowledgement, the name prefilled")
    over["PORTAL_STAFF_WA_TEMPLATES"] = "drmanoj_followup_due, nosuch ,welcome_template,decline_acknowledgement_manoj,welcome_template"
    ok([x["key"] for x in wt()] == ["welcome_template", "decline_acknowledgement_manoj"],
       "the setting: a two-field template and an unknown name left out, no duplicate")
    over.pop("PORTAL_STAFF_WA_TEMPLATES")

    print("[2] the page -- Reply on the WhatsApp tab for the staff, the Inbox link kept for the Inbox logins")
    wa = lists("alisha")["wa"]
    wph = [r["phone"] for r in wa if r["phone"]]
    ok(W.ph(10) in wph and W.ph(11) in wph, "the WhatsApp tab lists the waiting chats (today's and the one past 24 h): %d" % len(wph))
    st, t = page("alisha")
    ok(st == 200 and t.count('onclick="waOpen(this)"') == len(wph) and t.count('class="wap"') == len(wph),
       "alisha (no Inbox login): one Reply and one chat box per WhatsApp row (%d)" % t.count('onclick="waOpen(this)"'))
    ok(all(('data-ph="%s" onclick="waOpen(this)"' % p) in t for p in wph) and "/portal/inbox?m=" not in t,
       "each Reply carries its own row's number; no Inbox link for her")
    ok("innerHTML" not in t and "function waDraw" in t and "createTextNode" in t, "the chat is drawn with textContent only (no innerHTML)")
    st, t = page("shivani")
    ok(st == 200 and "/portal/inbox?m=" in t and 'onclick="waOpen(this)"' not in t, "shivani (an Inbox login in the walk): the Inbox link, as before")
    st, t = page("manoj", "doctor", "?as=alisha")
    ok(st == 200 and 'onclick="waOpen(this)"' not in t and "/portal/inbox?m=" in t, "the doctor ?as=alisha: his Inbox link, no send box")
    st, t = page("reception")
    ok(st == 200 and 'onclick="waOpen(this)"' in t, "reception: may reply")
    over["PORTAL_STAFF_WA_SEND"] = "0"
    st, t = page("alisha")
    ok(st == 200 and 'onclick="waOpen(this)"' not in t and 'class="wap"' not in t, "switch 0: no Reply, no chat box")
    over.pop("PORTAL_STAFF_WA_SEND")

    print("[3] the chat route")
    lists("alisha")
    s, j = chat("alisha", W.ph(10), hdr=False)
    ok(s == 400, "no X-Staff-Console header -> 400")
    s, j = chat("bhawna", W.ph(10))
    ok(s == 403, "a login the page is not for -> 403")
    s, j = chat("alisha", W.ph(9))
    ok(s == 409 and "not on your WhatsApp list" in (j.get("msg") or ""), "a number the tab does not list -> 409")
    PI.ingest(force=True)
    c = sqlite3.connect(inbox_p)
    c.execute("INSERT INTO replies(title, body, sort) VALUES ('Timings', 'Clinic: 10 am to 2 pm, 5 to 8 pm', 1)")
    c.commit()
    c.close()
    s, j = chat("alisha", W.ph(10))
    m = j.get("msgs") or []
    ok(s == 200 and j.get("ok") and j.get("can_send") is True and j.get("me") == "alisha", "alisha's chat -> 200, she may send")
    ok(len(m) == 30 and m[-1]["text"].startswith("Kal aa sakte") and m[0]["text"] == "old 11", "the newest 30 messages, oldest first")
    ok(any(x["text"].startswith("Photo") for x in m), "a photo is named, not shown")
    ok((j.get("window") or {}).get("open") is True and j["window"].get("hours_left") == 23.5, "the window: open, 23.5 h left")
    ok([r["title"] for r in j.get("replies") or []] == ["Timings"], "his saved replies offered")
    s, j2 = chat("alisha", W.ph(11))
    ok(s == 200 and (j2.get("window") or {}).get("open") is False and [x["key"] for x in j2.get("templates") or []] == ["welcome_template"],
       "a chat past 24 h: the window closed, the approved message offered")
    s, j = chat("manoj", W.ph(10), "doctor")
    ok(s == 200 and j.get("can_send") is False and "WhatsApp Inbox" in (j.get("note") or "") and j.get("templates") == [],
       "the doctor (no ?as=) reads the chat; no send box, a note")

    print("[4] the text reply -- through portal_inbox's sender, signed with her login")
    n0 = len(sent)
    s, r = post("alisha", "send", {"phone10": W.ph(10), "text": "  Haan, kal 11 baje aa jaiye  "})
    o = rows(W.ph(10))
    ok(s == 200 and r.get("ok") and r.get("msg") == "Sent." and len(sent) == n0 + 1, "alisha replies -> Sent., the sender called once")
    ok(during and during[-1] == (1, "alisha"), "during the send a 'sending' row by her is already in the chat (what every other phone's guard sees)")
    ok(sent[-1][0] == "TESTKEY-not-real" and sent[-1][1] == W.ph(10) and json.loads(sent[-1][2]) == {"type": "text", "context": {"body": "Haan, kal 11 baje aa jaiye", "preview_url": False}},
       "the inbox's own key, number and text shape (trimmed)")
    ok(len(o) == 1 and o[0]["sent_by"] == "alisha" and o[0]["src"] == "staff-console" and o[0]["status"] == "sent" and o[0]["mid"] == "wamid.T%d" % len(sent),
       "the chat gains her reply: by alisha, src staff-console, sent, MyOperator's id")
    lg = slog()
    ok(lg and lg[-1]["route"] == "staff-console" and lg[-1]["by"] == "alisha" and lg[-1]["ok"] is True and "TESTKEY" not in json.dumps(lg[-1]),
       "the send log: route staff-console, by alisha, no key")
    cc._CARD_CACHE.clear()
    ok(W.ph(10) not in [x["phone"] for x in lists("alisha")["wa"]], "answered -> the chat leaves the WhatsApp tab by itself")
    _CS_WA = getattr(CS, "_WA_OFFERED", {})
    ok(W.ph(10) in _CS_WA, "the chat stays answerable for the hour")
    n1 = len(sent)
    s, r = post("alisha", "send", {"phone10": W.ph(10), "text": "Haan, kal 11 baje aa jaiye"})
    ok(s == 409 and "Already sent" in r.get("msg", "") and len(sent) == n1, "the same text again at once -> refused, nothing sent")
    s, r = post("shivani", "send", {"phone10": W.ph(10), "text": "Ji"})
    ok(s == 409 and "Alisha replied" in r.get("msg", "") and len(sent) == n1, "another person within 2 minutes, nothing new -> refused (read the chat)")
    s, r = post("alisha", "send", {"phone10": W.ph(10), "text": "Aur kuch?"})
    ok(s == 200 and len(sent) == n1 + 1, "she may send a second, different message")
    c = sqlite3.connect(inbox_p)
    c.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES ('m10z',?, 'in', ?, 'text', 'Theek hai', '', '', '')",
              (W.ph(10), W.TODAY + "T11:30:30+05:30"))
    c.commit()
    c.close()
    s, r = post("shivani", "send", {"phone10": W.ph(10), "text": "Dhanyavaad"})
    ok(s == 200 and len(sent) == n1 + 2 and rows(W.ph(10))[-1]["sent_by"] == "shivani", "the patient wrote again -> another person may answer")
    n2 = len(sent)
    for body, want, why in (({"phone10": W.ph(10), "text": "   "}, 400, "an empty message"),
                            ({"phone10": W.ph(11), "text": "Hello"}, 409, "a chat past 24 hours"),
                            ({"phone10": W.ph(9), "text": "Hello"}, 409, "a number the tab does not list"),
                            ({"phone10": "", "text": "Hello"}, 409, "no number")):
        s, r = post("alisha", "send", body)
        ok(s == want and r.get("ok") is False, "%s -> %d" % (why, want))
    s, r = post("alisha", "send", {"phone10": W.ph(11), "text": "Hello"})
    ok("approved message" in r.get("msg", ""), "past 24 hours: the message says only an approved message can go")
    s, r = post("manoj", "send", {"phone10": W.ph(10), "text": "Hi"}, "doctor")
    ok(s == 403, "the doctor -> 403 (his Inbox is his)")
    s, r = post("alisha", "send", {"phone10": W.ph(10), "text": "Hi"}, "doctor")
    ok(s == 403, "a doctor-role login under any name -> 403 (the doctor's check, not the name)")
    s, r = post("bhawna", "send", {"phone10": W.ph(10), "text": "Hi"})
    ok(s == 403, "a login the page is not for -> 403")
    s, r = post("alisha", "send", {"phone10": W.ph(10), "text": "Hi"}, hdr=False)
    ok(s == 400, "no X-Staff-Console header -> 400")
    over["PORTAL_STAFF_WA_SEND"] = "0"
    s, r = post("alisha", "send", {"phone10": W.ph(10), "text": "Hi"})
    ok(s == 403 and "switched off" in r.get("msg", ""), "switch 0 -> 403")
    over.pop("PORTAL_STAFF_WA_SEND")
    ok(len(sent) == n2, "none of those reached the sender")
    tok["t"] = ""
    s, r = post("alisha", "send", {"phone10": W.ph(10), "text": "Key test"})
    ok(s == 500 and "send key" in r.get("msg", "") and len(sent) == n2, "no key on the server -> said, nothing sent")
    tok["t"] = "TESTKEY-not-real"
    mode["m"] = "gateway"
    s, r = post("reception", "send", {"phone10": W.ph(10), "text": "Busy test"})
    c = sqlite3.connect(inbox_p)
    q = c.execute("SELECT by_user, state, text FROM retry_q WHERE phone=?", (W.ph(10),)).fetchall()
    c.close()
    ok(s == 200 and r.get("queued") is True and q == [("reception", "waiting", "Busy test")] and rows(W.ph(10))[-1]["status"] == "retrying",
       "a gateway refusal -> kept: the server's own retry queue, by reception, shown 'retrying'")
    mode["m"] = "refuse"
    k0, nn = len(rows(W.ph(10))), len(noted)
    s, r = post("reception", "send", {"phone10": W.ph(10), "text": "Refused test"})
    ok(s == 502 and r.get("ok") is False and r.get("msg", "").startswith("Not sent") and len(rows(W.ph(10))) == k0,
       "a plain refusal -> said; nothing added to the chat")
    ok(len(noted) == nn + 1 and slog()[-1]["ok"] is False, "the refusal is logged and noted as the Inbox's own are")
    mode["m"] = "ok"
    _CS_WA[W.ph(10)] = time.time() - 7200
    CS._REBUILT[0] = time.time()
    s, r = post("alisha", "send", {"phone10": W.ph(10), "text": "Late"})
    ok(s == 409, "listed more than an hour ago (and no re-read due) -> 409")

    print("[4b] a panel read before another person's answer; a store locked after the send")
    lists("alisha")
    p3 = next((x for x in wph if x not in (W.ph(10), W.ph(11))), "")
    s, js = chat("shivani", p3)
    ok(s == 200 and js.get("upto"), "shivani opens a third chat (its newest message's time comes with it)")
    s, r = post("alisha", "send", {"phone10": p3, "text": "Ji, bataiye"})
    ok(s == 200, "alisha answers it")
    clock["t"] = clock["t"] + _dt.timedelta(minutes=3)
    s, r = post("shivani", "send", {"phone10": p3, "text": "Namaste", "upto": js["upto"]})
    ok(s == 409 and "since you opened it" in r.get("msg", ""), "3 min later shivani sends from her old panel -> refused (alisha answered since)")
    s, js2 = chat("shivani", p3)
    s, r = post("shivani", "send", {"phone10": p3, "text": "Namaste", "upto": js2.get("upto")})
    ok(s == 200, "read again -> she may add her message")
    real_settle = PI._s959_settle
    PI._s959_settle = lambda *a, **k: False                         # the store stays locked after the send
    clock["t"] = clock["t"] + _dt.timedelta(minutes=5)
    s, r = post("alisha", "send", {"phone10": p3, "text": "Locked test"})
    ok(s == 200 and r.get("msg") == "Sent.", "the message went but the store stayed locked -> still 'Sent.' (never 'try again')")
    PI._s959_settle = real_settle
    nb = len(sent)
    s, r = post("shivani", "send", {"phone10": p3, "text": "Locked test"})
    ok(s == 409 and len(sent) == nb, "its 'sending' row still stops another phone's send")

    clock["t"] = clock["t"] + _dt.timedelta(minutes=11)
    mode["m"] = "timeout"
    s, r = post("alisha", "send", {"phone10": p3, "text": "Timeout test"})
    ok(s == 504 and "may have gone" in r.get("msg", "") and rows(p3)[-1]["status"] == "unsure" and rows(p3)[-1]["sent_by"] == "alisha",
       "no answer from MyOperator -> 'may have gone' (504); the row kept as unsure, by her")
    mode["m"] = "ok"
    nb = len(sent)
    s, r = post("alisha", "send", {"phone10": p3, "text": "Timeout test"})
    ok(s == 409 and "may have gone" in r.get("msg", "") and len(sent) == nb, "the same person's retry within 10 min -> refused (read the chat or call)")
    s, j3 = chat("alisha", p3)
    ok(j3.get("msgs") and j3["msgs"][-1]["st"] == "may have gone", "the chat shows that reply as 'may have gone'")
    clock["t"] = clock["t"] + _dt.timedelta(minutes=11)
    c = sqlite3.connect(inbox_p)
    c.execute("INSERT INTO msgs (mid,phone,dir,ts,mtype,body,status,sent_by,src) VALUES ('sending-stuck',?,'out',?,'text','Stuck','sending','shivani','staff-console')",
              (p3, (clock["t"] - _dt.timedelta(minutes=4)).strftime("%Y-%m-%dT%H:%M:%S+05:30")))
    c.commit()
    c.close()
    s, j3 = chat("alisha", p3)
    st_stuck = sqlite3.connect(inbox_p).execute("SELECT status FROM msgs WHERE mid='sending-stuck'").fetchone()[0]
    ok(st_stuck == "unsure", "a 'sending' row left 4 min (a worker killed mid-send) -> read as 'unsure'")
    clock["t"] = clock["t"] + _dt.timedelta(minutes=11)
    mode["m"] = "echo"
    s, r = post("alisha", "send", {"phone10": p3, "text": "Echo test"})
    er = [x for x in rows(p3) if x["mid"] == "wamid.ECHO"]
    ok(s == 200 and len(er) == 1 and er[0]["sent_by"] == "alisha" and not any(x["mid"].startswith("sending-") and x["body"] == "Echo test" for x in rows(p3)),
       "MyOperator's echo stored first -> one row, signed alisha (the placeholder gone)")
    mode["m"] = "ok"

    print("[5] the approved message after 24 hours")
    lists("alisha")
    s, r = post("alisha", "template", {"phone10": W.ph(11), "template": "welcome_template", "name": "  Both  Lambda "})
    o = rows(W.ph(11))
    ok(s == 200 and r.get("mode") == "DRY" and "Test mode" in r.get("msg", "") and o and o[-1]["body"].startswith("[TEST MODE")
       and o[-1]["sent_by"] == "alisha", "test mode (PORTAL_WA_DRYRUN unset): the template sender's DRY path, the chat says TEST MODE")
    pl = open(PW.LOG, encoding="utf-8").read() if os.path.exists(PW.LOG) else ""
    ok("welcome_template" in pl and "Both Lambda" in pl and pl.count("\n") == 2, "the template log (temp) holds the DRY row with the name")
    over["PORTAL_WA_DRYRUN"] = "0"
    s, r = post("alisha", "template", {"phone10": W.ph(11), "template": "welcome_template", "name": "Both Lambda"})
    o = rows(W.ph(11))
    ok(s == 200 and r.get("mode") == "LIVE" and tsent and tsent[-1] == (W.ph(11), "welcome_template", '{"var_1": "Both Lambda"}', "alisha"),
       "live: portal_wa.send with the name in var_1, signed alisha")
    ok(o[-1]["body"] == "Template: Enquiry acknowledgement" and o[-1]["status"] == "sent" and slog()[-1]["route"] == "staff-console-template",
       "the chat: 'Template: Enquiry acknowledgement', sent; the log's route staff-console-template")
    s, r = post("shivani", "template", {"phone10": W.ph(11), "template": "welcome_template", "name": "Both Lambda"})
    ok(s == 409 and "already went" in r.get("msg", "") and len(tsent) == 1, "a second approved message to the same chat -> refused, not sent")
    s, r = post("alisha", "template", {"phone10": p3, "template": "welcome_template", "name": "Wrote Kappa"})
    ok(s == 409 and "within 24 hours" in r.get("msg", "") and len(tsent) == 1, "the window open -> the server refuses the template too")
    over.pop("PORTAL_WA_DRYRUN")
    nt = len(tsent)
    for body, want, why in (({"phone10": W.ph(11), "template": "drmanoj_followup_due", "name": "X"}, 400, "a template not offered"),
                            ({"phone10": W.ph(11), "template": "welcome_template", "name": "  "}, 400, "no name"),
                            ({"phone10": W.ph(9), "template": "welcome_template", "name": "X"}, 409, "a number not listed")):
        s, r = post("alisha", "template", body)
        ok(s == want and r.get("ok") is False, "%s -> %d" % (why, want))
    s, r = post("manoj", "template", {"phone10": W.ph(11), "template": "welcome_template", "name": "X"}, "doctor")
    ok(s == 403 and len(tsent) == nt, "the doctor -> 403; none of those sent")
    finish()


def do_prefix(f, t):
    a, b = open(f, "rb").read(), open(t, "rb").read()
    tail = b[len(a):].decode("utf-8", "replace")
    ok(b.startswith(a) and len(b) > len(a), "portal_inbox.py: the TO begins with the FROM's bytes, unchanged")
    ok("@app.route" not in tail and "register(" not in tail and "def staff_send_text" in tail, "the block appended holds no route and touches no register()")
    finish()


def do_page(f, t):
    a = [x for x in open(f, encoding="utf-8").read().split("\n") if not x.startswith("== ")]
    b = [x for x in open(t, encoding="utf-8").read().split("\n") if not x.startswith("== ")]
    na = sum(1 for x in a if CC_OLD in x)
    ok(na >= 1 and [x.replace(CC_OLD, CC_NEW) for x in a] == b, "the owner's page: equal but for the Accept line (%d place(s))" % na)
    ok(not any(CC_OLD in x for x in b), "the old Accept label is gone from his page")
    finish()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["walk"] and len(a) == 2:
        try:
            do_walk(a[1])
        except SystemExit:
            raise
        except Exception as e:                       # the control (the FROM code) must go red, never crash
            ok(False, "the walk could not go on: %s" % type(e).__name__)
            finish()
    elif a[:1] == ["prefix"] and len(a) == 3:
        do_prefix(a[1], a[2])
    elif a[:1] == ["page"] and len(a) == 3:
        do_page(a[1], a[2])
    else:
        print(__doc__)
        sys.exit(2)
