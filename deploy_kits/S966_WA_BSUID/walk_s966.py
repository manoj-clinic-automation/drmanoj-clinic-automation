#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s966.py -- the walk of kit S966_WA_BSUID (the parent, S531, 27-Nov-2026).

Made-up numbers only (built at run time, none written here), made-up BSUIDs, temp stores; never the network, never a live file.
    python3 walk_s966.py walk <dir>                 the checks on the four files in <dir>; last line ALL PASS, exit 0.
                                                    On the FROM files the S966 checks go red -- the control.
    python3 walk_s966.py same <from_dir> <to_dir>   every push WITHOUT a BSUID gives the same result on both sides:
                                                    the receiver's row, the alert, the inbox's read + its store, records' sender.
    python3 walk_s966.py replay <from_dir> <to_dir> <raw_log_dir> [days]
                                                    the REAL raw pushes of the last [days] (30) read through both sides:
                                                    every push without a BSUID must give the same result; COUNTS ONLY are
                                                    printed (no number, no text); a phone value with letters that is not
                                                    Meta's 'XX.' shape stops it (an unknown shape).
    python3 walk_s966.py count <inbox.db>           how many chats are keyed on a BSUID (read only; for --undo's warning)
    python3 walk_s966.py dump|rdump ...             (one side per process, used by 'same' and 'replay')
<dir> holds wa_receiver.py, wa_alert.py, portal_inbox.py, records.py, calls_console.py.
"""
import ast
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import types

PASS, FAIL = [], []
PHONE_PATHS = ("customer_identifier", "payload.customer_identifier", "data.customer_identifier", "customer_number",
               "payload.customer_number", "payload.data.context.from", "contact.wa_id")


def ok(cond, name):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name)


def num(i):
    """A made-up Indian mobile with its 91 (12 digits), built here so no number is written in this file."""
    return "91" + "9" + str(10 ** 8 + i)


def bsuid(i):
    return "IN." + ("A%dbC" % (i % 10)) * 32                           # 'IN.' + 128 characters


def _stub_missing():
    """Stand-ins for flask / gspread / google auth where this Python has none (the build machine). The box has them all."""
    try:
        import flask  # noqa: F401
    except Exception:                                                   # noqa: BLE001
        f = types.ModuleType("flask")

        class _App(object):
            def __init__(self, *a, **k):
                pass

            def route(self, *a, **k):
                return lambda fn: fn
        f.Flask = _App
        f.Blueprint = _App
        f.request = types.SimpleNamespace(args={}, headers={}, method="GET")
        for n in ("jsonify", "Response", "redirect", "abort", "send_file", "make_response"):
            setattr(f, n, lambda *a, **k: (a, k))
        sys.modules["flask"] = f
    try:
        import gspread  # noqa: F401
    except Exception:                                                   # noqa: BLE001
        sys.modules["gspread"] = types.ModuleType("gspread")
    try:
        from google.oauth2.service_account import Credentials  # noqa: F401
    except Exception:                                                   # noqa: BLE001
        g = types.ModuleType("google")
        o = types.ModuleType("google.oauth2")
        s = types.ModuleType("google.oauth2.service_account")
        s.Credentials = object
        g.oauth2 = o
        o.service_account = s
        sys.modules.update({"google": g, "google.oauth2": o, "google.oauth2.service_account": s})


def load(d, tmp):
    """The four modules from <d>, the inbox on a temp store, nothing that can reach the network."""
    os.environ.update({"INBOX_STORE": os.path.join(tmp, "store"), "INBOX_RAW_DIR": os.path.join(tmp, "raw"),
                       "INBOX_WA_ENV": os.path.join(tmp, "none.env"), "INBOX_PORTAL_LOG": os.path.join(tmp, "none.csv"),
                       "INBOX_API_URL": "http://127.0.0.1:9/never", "INBOX_CALL_URL": "http://127.0.0.1:9/never",
                       "WA_RAW_LOG_DIR": os.path.join(tmp, "rxlog"), "WA_ALERT_STATE": os.path.join(tmp, "al.json"),
                       "NTFY_TOPIC": "", "WA_SA_KEY": ""})
    os.makedirs(os.path.join(tmp, "raw"), exist_ok=True)
    sys.path.insert(0, d)
    _stub_missing()
    import wa_alert, wa_receiver, portal_inbox, records                 # noqa: E401
    for m in (wa_alert, wa_receiver, portal_inbox, records):
        if os.path.dirname(os.path.abspath(m.__file__)) != os.path.abspath(d):
            raise SystemExit("REFUSED: %s did not load from %s" % (m.__name__, d))
    import http.client

    def _never(*a, **k):
        raise AssertionError("the walk tried the network")
    http.client.HTTPSConnection = _never
    http.client.HTTPConnection = _never
    wa_receiver._state["header"] = ["timestamp", "phone", "direction", "type", "message", "message id",
                                    "conversation id", "status"]
    wa_receiver._state["ws"] = object()
    return wa_receiver, wa_alert, portal_inbox, records


def console_funcs(d):
    """_s871_key and ivr_call from <d>/calls_console.py, by themselves (the module needs the box's ring_* files)."""
    tree = ast.parse(open(os.path.join(d, "calls_console.py"), encoding="utf-8").read())
    keep = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("_s871_key", "ivr_call")]
    ns = {"re": re, "_LAST_CALL": {}, "os": os, "json": json}
    exec(compile(ast.Module(body=keep, type_ignores=[]), "calls_console_part", "exec"), ns)
    return ns["_s871_key"], ns["ivr_call"]


def plain_pushes():
    """Pushes WITHOUT a BSUID, in the shapes the receiver has met: the number at each of its paths, an int, a '+',
    a status ping, an outbound echo, a photo with no text, nothing at all."""
    P = []
    P.append({"event_type": "message.received", "customer_identifier": num(1), "timestamp": "1764200000",
              "payload": {"id": "m1", "data": {"type": "text", "context": {"body": "pain in knee"}}}})
    P.append({"event_type": "message.received", "payload": {"customer_identifier": num(2), "id": "m2", "timestamp": 1764200100000,
              "data": {"type": "text", "context": {"body": "appointment?"}}}})
    P.append({"event": "message.received", "data": {"customer_identifier": "+" + num(3), "id": "m3", "body": "hello"}})
    P.append({"event_type": "message.received", "customer_number": int(num(4)), "id": "m4", "message": "x-ray report"})
    P.append({"event_type": "message.received", "payload": {"customer_number": num(5)[2:], "id": "m5",
              "data": {"type": "image", "context": {"link": "https://myop-chat-prod.s3.amazonaws.com/media/a.jpg"}}}})
    P.append({"event_type": "message.received", "payload": {"id": "m6", "data": {"type": "text",
              "context": {"from": num(6), "body": "from context"}}}})
    P.append({"event_type": "message.received", "contact": {"wa_id": num(7)}, "id": "m7", "text": "wa_id only"})
    P.append({"event_type": "message.delivered", "customer_identifier": num(1), "payload": {"id": "o1", "status": "delivered"}})
    P.append({"event_type": "message.sent", "direction": "outgoing", "customer_identifier": num(8),
              "payload": {"id": "o2", "data": {"type": "text", "context": {"body": "reply from clinic"}}}})
    P.append({"event_type": "message.received", "payload": {"id": "m9", "data": {"type": "text", "context": {"body": "no number"}}}})
    P.append({"event_type": "message.received", "customer_identifier": "", "customer_number": num(10), "id": "m10", "message": "empty first"})
    P.append({"event_type": "message.received", "customer_identifier": " " + num(11) + " ", "id": "m11", "message": "spaced"})
    for i, p in enumerate(P):                                           # every push timed, so 'now' never enters a result
        if "timestamp" not in p and "timestamp" not in (p.get("payload") or {}):
            p["timestamp"] = str(1764200000 + 60 * i)
    return P


def bsuid_pushes():
    return [
        {"event_type": "message.received", "customer_identifier": bsuid(1), "timestamp": "1764201000",
         "payload": {"id": "b1", "data": {"type": "text", "context": {"body": "username only"}}}},
        {"event_type": "message.received", "customer_identifier": num(21), "meta_bsuid": bsuid(1), "timestamp": "1764201100",
         "payload": {"id": "b2", "data": {"type": "text", "context": {"body": "now with number"}}}},
        {"event_type": "message.received", "customer_identifier": bsuid(1), "timestamp": "1764201200",
         "payload": {"id": "b3", "data": {"type": "text", "context": {"body": "username again"}}}},
        {"event_type": "message.received", "customer_identifier": bsuid(2), "timestamp": "1764201300",
         "payload": {"id": "b4", "data": {"type": "text", "context": {"body": "never a number"}}}},
    ]


def run_store(pi, pushes):
    c = pi.db()
    c.execute("BEGIN IMMEDIATE")
    res = [pi.ingest_line(c, p) for p in pushes]
    c.execute("COMMIT")
    rows = [list(r) for r in c.execute("SELECT mid, phone, dir, mtype, body, media_url, status FROM msgs ORDER BY rid")]
    c.close()
    return res, rows


def do_dump(d, out):
    tmp = tempfile.mkdtemp(prefix="s966_")
    try:
        rx, al, pi, rc = load(d, tmp)
        got = {"rx": [], "al": [], "pi": [], "rc": []}
        cap = []
        al.alert = lambda phone, text, msg_id="": cap.append([phone, text, msg_id]) or True
        for p in plain_pushes():
            b = rx.build_row(p)
            got["rx"].append(list(b) if b else None)
            del cap[:]
            al.from_payload(p, rx.dig, rx.is_inbound_message)
            got["al"].append(list(cap))
            rp = pi.read_push(p)
            rp.pop("bsuid", None)
            got["pi"].append({k: str(v) for k, v in sorted(rp.items())})
            if hasattr(rc, "_s966_phone"):
                got["rc"].append(str(rc._s966_phone(p)))
            else:
                got["rc"].append(str(rc._dig(p, "customer_identifier", "payload.customer_identifier", "data.customer_identifier",
                                             "customer_number", "payload.customer_number", "payload.data.context.from") or ""))
        got["store"] = run_store(pi, plain_pushes())
        got["keys"] = [pi.last10(x) for x in (num(1), num(5)[2:], "+" + num(3), "1" + num(9)[2:], "", "12345")]
        k871, _ivr = console_funcs(d)
        got["cc"] = [k871(x) for x in (num(1), num(5)[2:], "+" + num(3), "1" + num(9)[2:], "", "12345", "00" + num(4))]
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(got, fh, sort_keys=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def do_same(dfrom, dto):
    tmp = tempfile.mkdtemp(prefix="s966same_")
    try:
        outs = []
        for i, d in enumerate((dfrom, dto)):
            o = os.path.join(tmp, "%d.json" % i)
            r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "dump", d, o],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            if r.returncode != 0:
                print(r.stdout[-1500:])
                ok(False, "dump ran on %s" % ("FROM" if i == 0 else "TO"))
                return
            outs.append(json.load(open(o, encoding="utf-8")))
        a, b = outs
        for k, name in (("rx", "the receiver's sheet row"), ("al", "the phone alert"), ("pi", "the inbox's read of each push"),
                        ("rc", "records' sender number"), ("store", "the inbox store after the pushes"),
                        ("keys", "the inbox chat key of plain numbers"), ("cc", "the Call Consoles' chat key of plain numbers")):
            ok(a[k] == b[k], "no BSUID: %s is the same before and after (%d pushes)" % (name, len(plain_pushes())))
            if a[k] != b[k]:
                print("     FROM %s\n     TO   %s" % (json.dumps(a[k])[:600], json.dumps(b[k])[:600]))
        ok(any(r for r in a["rx"]) and any(x for x in a["al"]) and a["store"][1], "the pushes were read at all (rows, alerts, store)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def do_walk(d):
    tmp = tempfile.mkdtemp(prefix="s966w_")
    try:
        rx, al, pi, rc = load(d, tmp)
        marked = all(hasattr(m, "s966_is_bsuid") for m in (rx, al, pi)) and hasattr(rc, "_s966_phone")
        ok(marked, "kit S966 marked in all four files")
        B1, B2 = bsuid(1), bsuid(2)
        isb = getattr(pi, "s966_is_bsuid", lambda v: False)
        ok(isb(B1) and len(B1) == 131, "a BSUID ('IN.' + 128) is known as one")
        ok(not any(isb(v) for v in (num(1), "+" + num(1), num(1)[2:], int(num(1)), "", None, {"a": 1}, " " + num(1) + " ")),
           "a mobile in any shape seen so far is never taken for a BSUID")
        # the receiver
        r1 = rx.build_row(bsuid_pushes()[0])
        ok(bool(r1) and r1[0][1] == "", "receiver: a BSUID-only push writes the row with NO number (never digits cut from the ID)")
        r2 = rx.build_row(bsuid_pushes()[1])
        ok(bool(r2) and r2[0][1] == num(21), "receiver: a push with a mobile and a meta_bsuid keeps the mobile")
        # the alert
        cap = []
        al.alert = lambda phone, text, msg_id="": cap.append([phone, text, msg_id]) or True
        al.from_payload(bsuid_pushes()[0], rx.dig, rx.is_inbound_message)
        ok(len(cap) == 1 and cap[0][0] == "" and "no mobile number" in cap[0][1] and cap[0][1].endswith("username only"),
           "alert: a BSUID-only push alerts with no number and says so, the message kept")
        del cap[:]
        al.from_payload(bsuid_pushes()[1], rx.dig, rx.is_inbound_message)
        ok(len(cap) == 1 and cap[0][0] == num(21) and cap[0][1] == "now with number", "alert: a mobile beside a meta_bsuid alerts as before")
        # records
        ok(str(getattr(rc, "_s966_phone", lambda b: "x")(bsuid_pushes()[0])) == "", "records: a BSUID is never fingerprinted as a number")
        # the inbox: keys, the store, the pairs
        ok(pi.last10(B1) == B1 and pi.last10(pi.last10(B1)) == B1, "inbox: a BSUID is its own chat key, unchanged both ways")
        ok(pi.ten(B1) == "" and not pi.abroad(B1) and pi.full_number(B1) == "" and pi.tail4(B1) == "WA-ID",
           "inbox: a BSUID is no patient number, not 'abroad', no full number, masked as WA-ID")
        rp = pi.read_push(bsuid_pushes()[0])
        ok(rp.get("phone") == "" and rp.get("bsuid") == B1, "inbox: the push reader gives no mobile and the BSUID")
        res, rows = run_store(pi, bsuid_pushes()[:1])
        ok(res == ["in"] and rows and rows[0][1] == B1, "inbox: a BSUID-only message is stored under the BSUID (not lost, not 'unread')")
        c = pi.db()
        c.execute("INSERT OR REPLACE INTO reads(phone, ts) VALUES(?,?)", (B1, "2026-12-01T10:00:00+05:30"))
        c.commit()
        c.close()
        res, rows = run_store(pi, bsuid_pushes()[1:4])
        keys = {r[0]: r[1] for r in rows}
        ok(keys.get("b1") == num(21)[2:] and keys.get("b2") == num(21)[2:], "inbox: when the mobile arrives with the BSUID, the earlier chat moves to the mobile")
        ok(keys.get("b3") == num(21)[2:], "inbox: a later BSUID-only message joins the mobile's chat")
        ok(keys.get("b4") == B2, "inbox: a BSUID never seen with a mobile stays its own chat")
        c = pi.db()
        rd = dict((r[0], r[1]) for r in c.execute("SELECT phone, ts FROM reads"))
        pair = c.execute("SELECT phone FROM s966_bsuid WHERE bsuid=?", (B1,)).fetchone() if marked else None
        c.close()
        ok(rd.get(num(21)[2:]) == "2026-12-01T10:00:00+05:30" and B1 not in rd, "inbox: the 'read' mark moves with the chat")
        ok(bool(pair) and pair[0] == num(21)[2:], "inbox: the pair BSUID -> mobile is remembered")
        ok(pi.abroad_count() == 0, "inbox: a BSUID chat is not counted as a number abroad")
        # never a send, a template or a call to a BSUID
        r = pi.myop_send("t", B2, {"type": "text", "context": {"body": "x"}})
        ok(r[0] is False and "username" in str(r[2]), "inbox: the sender refuses a BSUID before any network")
        s1 = pi.staff_send_text(B2, "hello", "shivani", lambda k, d="": d)
        s2 = pi.staff_send_template(B2, "x", {}, "shivani", lambda k, d="": d)
        ok(s1.get("ok") is False and s1.get("code") == 409 and "username" in s1.get("msg", ""), "staff: a text reply to a BSUID chat is refused in words")
        ok(s2.get("ok") is False and s2.get("code") == 409 and "username" in s2.get("msg", ""), "staff: a template to a BSUID chat is refused in words")
        # the BSUID came INSTEAD of the mobile: no later field is trusted for one (cold review SHOULD 2)
        B3 = bsuid(3)
        px = {"event_type": "message.received", "customer_identifier": B3, "customer_number": num(30), "timestamp": "1764202000",
              "payload": {"id": "b9", "data": {"type": "text", "context": {"body": "id first", "from": num(31)}}}}
        r9 = rx.build_row(px)
        del cap[:]
        al.from_payload(px, rx.dig, rx.is_inbound_message)
        rp9 = pi.read_push(px)
        ok(bool(r9) and r9[0][1] == "" and cap and cap[0][0] == "" and rp9.get("phone") == "" and rp9.get("bsuid") == B3
           and str(getattr(rc, "_s966_phone", lambda b: "x")(px)) == "",
           "a BSUID in customer_identifier: no other field is taken for the mobile (receiver, alert, inbox, records)")
        res9, rows9 = run_store(pi, [px])
        c = pi.db()
        pair9 = c.execute("SELECT COUNT(*) FROM s966_bsuid WHERE bsuid=?", (B3,)).fetchone()[0] if marked else -1
        c.close()
        ok(dict((r[0], r[1]) for r in rows9).get("b9") == B3 and pair9 == 0, "inbox: such a push is its own chat and pairs with nothing")
        # reading the same pushes again changes nothing
        before = run_store(pi, [])[1]
        again = run_store(pi, bsuid_pushes() + [px])[1]
        ok(before == again and len(again) == 5, "inbox: the same pushes read again change nothing (5 messages, same keys)")
        # the same BSUID later with another mobile: the pair moves on, messages already filed stay where they are
        run_store(pi, [{"event_type": "message.received", "customer_identifier": num(22), "meta_bsuid": B1, "timestamp": "1764203000",
                        "payload": {"id": "b10", "data": {"type": "text", "context": {"body": "new phone"}}}}])
        c = pi.db()
        pair = c.execute("SELECT phone FROM s966_bsuid WHERE bsuid=?", (B1,)).fetchone() if marked else None
        k1 = c.execute("SELECT phone FROM msgs WHERE mid='b1'").fetchone()
        c.close()
        ok(bool(pair) and pair[0] == num(22)[2:] and k1 and k1[0] == num(21)[2:], "inbox: the same BSUID with a new mobile re-pairs; filed messages stay")
        # the Call Consoles (cold review MUST): a BSUID-keyed chat is never cut into a made-up number, never dialled
        k871, ivr = console_funcs(d)
        ok(k871(B1) == "" and k871(B2) == "" and k871("IN.13491208655302741918") == "", "Call Consoles: a BSUID chat key gives no number (so it is never listed)")
        try:
            iv = ivr(B1, "manoj")
        except Exception as e:                                              # noqa: BLE001
            iv = (None, type(e).__name__, 0)
        ok(iv[0] is False and "username" in str(iv[1]), "Call Consoles: a call to a BSUID is refused before anything is dialled")
        src = open(os.path.join(d, "portal_inbox.py"), encoding="utf-8").read()
        ok(src.count("        if s966_is_bsuid(ph):                                           # S966\n            return fail(S966_NO_NUMBER)\n") == 3,
           "inbox page: the send, template and call routes each refuse a BSUID")
        ok("function isWid(p)" in src and 'if(isWid(p))return "WhatsApp ID (no number)";' in src and 'if(isWid(p))return "";var d=' in src,
           "inbox page: a BSUID chat shows 'WhatsApp ID (no number)' and no MyOperator number link")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _letter_kind(p, dig):
    """'' | 'id' (a value of Meta's 'XX.' shape in a phone path) | 'other' (letters in a phone path, not that shape)."""
    for path in PHONE_PATHS:
        v = dig(p, path)
        if v in (None, "", [], {}) or isinstance(v, (dict, list)):
            continue
        sv = str(v).strip()
        if any("a" <= ch.lower() <= "z" for ch in sv):
            return "id" if re.match(r"^[A-Za-z]{2}\.\S{8,}$", sv) else "other"
    return ""


def do_rdump(d, raw, days, out):
    tmp = tempfile.mkdtemp(prefix="s966r_")
    try:
        rx, al, pi, rc = load(d, tmp)
        cap = []
        al.alert = lambda phone, text, msg_id="": cap.append([phone, text, msg_id]) or True
        names = sorted(n for n in os.listdir(raw) if re.match(r"^\d{4}-\d{2}-\d{2}\.jsonl$", n))[-int(days):]
        hs, plain, n_id, n_other, n_lines = [], [], 0, 0, 0
        for n in names:
            with open(os.path.join(raw, n), "rb") as fh:
                for line in fh.read().split(b"\n"):
                    if not line.strip():
                        continue
                    try:
                        rec = json.loads(line.decode("utf-8", "replace"))
                    except ValueError:
                        continue
                    b = rec.get("body") if isinstance(rec, dict) else None
                    if not isinstance(b, dict):
                        continue
                    n_lines += 1
                    if not any(rx.dig(b, t) not in (None, "", [], {}) for t in
                               ("timestamp", "payload.timestamp", "data.timestamp", "payload.data.timestamp")):
                        b = dict(b, timestamp=str(rec.get("at") or "2026-01-01T00:00:00+05:30"))   # never 'now' (second look)
                    k = _letter_kind(b, rx.dig)
                    if k:
                        n_id += (k == "id")
                        n_other += (k == "other")
                        continue
                    plain.append(b)
                    del cap[:]
                    br = rx.build_row(b)
                    al.from_payload(b, rx.dig, rx.is_inbound_message)
                    rp = pi.read_push(b)
                    rp.pop("bsuid", None)
                    if hasattr(rc, "_s966_phone"):
                        rcp = rc._s966_phone(b)
                    else:
                        rcp = rc._dig(b, "customer_identifier", "payload.customer_identifier", "data.customer_identifier",
                                      "customer_number", "payload.customer_number", "payload.data.context.from") or ""
                    one = json.dumps([list(br) if br else None, cap, {k2: str(v) for k2, v in sorted(rp.items())}, str(rcp)],
                                     sort_keys=True, default=str)
                    hs.append(hashlib.md5(one.encode("utf-8")).hexdigest())
        res, rows = run_store(pi, plain)
        st = hashlib.md5(json.dumps([res, rows], default=str).encode("utf-8")).hexdigest()
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"h": hs, "store": st, "files": len(names), "lines": n_lines, "id": n_id, "other": n_other,
                       "stored": len(rows)}, fh)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def do_replay(dfrom, dto, raw, days):
    tmp = tempfile.mkdtemp(prefix="s966rep_")
    try:
        snap = os.path.join(tmp, "snap")                                # ONE copy of the live, growing logs: both sides read it
        os.makedirs(snap)
        os.chmod(tmp, 0o700)
        names = sorted(n for n in os.listdir(raw) if re.match(r"^\d{4}-\d{2}-\d{2}\.jsonl$", n))[-int(days):]
        for n in names:
            shutil.copyfile(os.path.join(raw, n), os.path.join(snap, n))
        raw = snap
        outs = []
        for i, d in enumerate((dfrom, dto)):
            o = os.path.join(tmp, "%d.json" % i)
            r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "rdump", d, raw, str(days), o],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            if r.returncode != 0:
                print("     " + " ".join(sorted(set(re.findall(r"\b[A-Z][A-Za-z]*(?:Error|Exception)\b", r.stdout))))[:200])
                ok(False, "the real pushes were read on the %s side" % ("FROM" if i == 0 else "TO"))
                return
            outs.append(json.load(open(o, encoding="utf-8")))
        a, b = outs
        print("     real pushes: %d files, %d pushes, %d with Meta's ID, %d with another lettered value, %d messages stored"
              % (a["files"], a["lines"], a["id"], a["other"], a["stored"]))
        ok(a["lines"] > 0, "real pushes were found to replay")
        ok(a["other"] == 0, "no phone field holds an unknown lettered value (only Meta's 'XX.' shape is read as an ID)")
        diff = sum(1 for x, y in zip(a["h"], b["h"]) if x != y) + abs(len(a["h"]) - len(b["h"]))
        ok(diff == 0, "every real push without a BSUID: the same row, alert, inbox read and records sender (%d pushes, %d differ)"
           % (len(a["h"]), diff))
        ok(a["store"] == b["store"], "the real pushes give the same inbox store before and after")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def do_count(path):
    try:
        c = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=5)
        try:
            n = c.execute("SELECT COUNT(DISTINCT phone) FROM msgs WHERE phone GLOB '*[A-Za-z]*'").fetchone()[0]
        finally:
            c.close()
        print("BSUID chats: %d" % n)
    except Exception as e:                                              # noqa: BLE001
        print("BSUID chats: unknown (%s)" % type(e).__name__)
    return 0


def main(a):
    if len(a) >= 2 and a[0] == "walk":
        do_walk(a[1])
    elif len(a) >= 3 and a[0] == "same":
        do_same(a[1], a[2])
    elif len(a) >= 3 and a[0] == "dump":
        do_dump(a[1], a[2])
        return 0
    elif len(a) >= 5 and a[0] == "rdump":
        do_rdump(a[1], a[2], a[3], a[4])
        return 0
    elif len(a) >= 4 and a[0] == "replay":
        do_replay(a[1], a[2], a[3], int(a[4]) if len(a) > 4 else 30)
    elif len(a) >= 2 and a[0] == "count":
        return do_count(a[1])
    else:
        print(__doc__)
        return 2
    print("%d checks, %d failed" % (len(PASS) + len(FAIL), len(FAIL)))
    print("ALL PASS" if not FAIL else "NOT ALL PASS")
    return 0 if not FAIL else 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as e:                                              # noqa: BLE001 -- a crash is a red, said in one line
        import traceback
        traceback.print_exc()
        print("  FAIL  the walk crashed: %s" % type(e).__name__)
        print("NOT ALL PASS")
        sys.exit(1)
