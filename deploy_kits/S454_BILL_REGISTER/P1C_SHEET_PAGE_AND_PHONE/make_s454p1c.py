#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p1c.py -- kit S454_BILL_REGISTER, part 1C (S454 17): the printed order sheet carries the whole open order and nothing prints over
another column; the owner's "Reception phone" card and its test message; the phone-setup page's steps as the macro was built; the reception
phone counted alive for 720 minutes; "1 medicine". CLAUDE.md rule 2: built from the live bytes (every anchor exactly once, FROM -> TO pinned),
order_sheet_pdf.py replaced whole by the kit's v1.1 (a module of this kit's own part 1; its FROM pin checked first).

    make_s454p1c.py --finance /root/finance --kit DIR --out DIR
"""
import argparse
import hashlib
import os

FROM = {"supplier_msg.py": "fc6c1724d6da4e1d04897b60d61c13b8", "porders_s454.py": "05716f3c040478d09fd2016561c7c99c",
        "order_sheet.py": "93f55d87730e749d78ea5561de38266f", "order_sheet_pdf.py": "9c28df38435a25d7e1d65c34b8d43ec9"}
REPLACE = {"order_sheet_pdf.py": "order_sheet_pdf.py"}          # whole file from the kit folder

# ------------------------------------------------------------------------------------------------ supplier_msg.py
SM_NEXT_OLD = ('''                    "(status='queued' OR (status='failed' AND kind<>'order' AND (last_try_at IS NULL OR last_try_at<=?))) ORDER BY queued_at, id LIMIT 1",''')
SM_NEXT_NEW = ('''                    "(status='queued' OR (status='failed' AND kind NOT IN ('order','test') AND (last_try_at IS NULL OR last_try_at<=?))) "
                    "ORDER BY (kind='test') DESC, queued_at, id LIMIT 1",          # S454 P1C: the owner's test first; a failed test is never retried''')

SM_SETUP_OLD = ('''<div class="card"><h2>Yeh kya hai</h2><p>Doctor sahab jab NEFT "done" karte hain, server har supplier ke liye ek WhatsApp message tayyar rakhta hai
(poora account number aur IFSC ke saath). Reception ka phone har 5 minute mein server se poochta hai "koi message hai?", milta hai to
WhatsApp mein khol kar bhej deta hai, aur server ko bata deta hai "ho gaya". Aapko kuch type nahi karna.</p>
<p>S454: supplier ko <b>medicine ka order</b> bhi isi raste se jaata hai (Purchase orders par "Sab ko WhatsApp bhejo"). Har message ke baad phone <b>turant dobara poochhe</b>, jab tak jawab khaali (<code>{}</code>) na aaye — tabhi das message ek-do minute mein chale jaate hain.</p>
<div class="warn">Yeh ek personal WhatsApp ko automation se chalata hai. WhatsApp ki screen badle to macro mein chhota sa sudhaar lag sakta hai.
Neeche wala <b>Bhejo</b> button (Vendor payments page par, 30 minute baad) hamesha kaam karta hai.</div></div>
<div class="card"><h2>Ek baar ka kaam — MacroDroid mein macro banaiye</h2>
<p><b>Trigger:</b> <i>Regular Interval</i> · har <b>5 minute</b> · sirf jab phone unlocked ho (Constraint: <i>Device Unlocked</i>; aur <i>WiFi/Data connected</i>).</p>
<p><b>Actions, isi kram mein:</b></p>
<ol>
<li><b>HTTP Request</b> · GET · URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/next</code> · Header: naam <code>X-Phone-Token</code>, value = neeche wala token (long-press, copy, paste) · Response ko variable <code>resp</code> mein save karein.</li>
<li><b>If</b> <code>resp</code> contains <code>"id"</code> (yaani message hai):</li>
<li>&nbsp;&nbsp;<b>JSON Parse</b> (ya <i>Text Manipulation</i>): <code>resp</code> se <code>id</code>, <code>to</code>, <code>text</code> nikaalein.</li>
<li>&nbsp;&nbsp;<b>Open Website / Launch URL</b>: <code>https://wa.me/{to}?text={text}</code> (text ko URL-encode karein — MacroDroid ka <i>Encode URL</i> option).</li>
<li>&nbsp;&nbsp;<b>Wait</b> 6 second.</li>
<li>&nbsp;&nbsp;<b>UI Interaction</b> → <i>Click</i> → text <code>Send</code> (WhatsApp ka Send button; Accessibility permission chahiye).</li>
<li>&nbsp;&nbsp;<b>Wait</b> 3 second.</li>
<li>&nbsp;&nbsp;<b>HTTP Request</b> · POST · URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/done</code> · wahi header · Body (JSON): <code>{"id": {id}, "ok": true}</code>.</li>
<li><b>End If</b>.</li>
<li><b>S454:</b> agar message mila tha (<code>resp</code> mein <code>"id"</code> tha) to <b>turant step 1 se phir chalaiye</b> (MacroDroid: <i>Repeat Actions</i> / <i>While</i> loop), jab tak jawab khaali na ho. Ek message server do baar nahi deta: diya hua message 10 minute tak dobara nahi milta.</li>
</ol>
<p class="mut">Agar Send nahi dab paaya: POST body <code>{"id": {id}, "ok": false, "error": "send not clicked"}</code> bhejein — server 30 minute baad phir se dega, aur 30 minute baad Vendor payments page par <b>Bhejo</b> button dikhne lagega.</p>''')
SM_SETUP_NEW = ('''<div class="card"><h2>Yeh kya hai</h2><p>Doctor sahab jab NEFT "done" karte hain, server har supplier ke liye ek WhatsApp message tayyar rakhta hai
(poora account number aur IFSC ke saath). Reception ka phone har minute server se poochta hai "koi message hai?", milta hai to
WhatsApp mein khol kar bhej deta hai, aur server ko bata deta hai "ho gaya". Aapko kuch type nahi karna.</p>
<p>S454: supplier ko <b>medicine ka order</b> bhi isi raste se jaata hai (Purchase orders par "Sab ko WhatsApp bhejo"). Phone ek minute mein ek message bhejta hai.</p>
<div class="warn">Yeh ek WhatsApp ko automation se chalata hai. WhatsApp ki screen badle to macro mein chhota sa sudhaar lag sakta hai.
Neeche wala <b>Bhejo</b> button (Vendor payments page par, 30 minute baad) hamesha kaam karta hai.</div></div>
<div class="card"><h2>Ek baar ka kaam — MacroDroid mein macro banaiye (03-Oct ko jaisa bana)</h2>
<p><b>Phone par sirf ek WhatsApp:</b> <b>WhatsApp Business</b>. Uske saath doosra (bina register kiya) WhatsApp Messenger pada ho to link ek box par ruk jaata hai aur kuch nahi jaata — use hata dijiye.</p>
<p><b>Trigger:</b> <i>Regular Interval</i> · har <b>1 minute</b>. Koi loop nahi.</p>
<p><b>Constraints (dono zaroori):</b> <i>Device Unlocked</i> aur <i>Screen On</i>. Kyon: macro "sent" bata deta hai chahe screen par kuch bhi hua ho — screen band ho to woh bina bheje "sent" likh dega. Isliye phone sirf jaga aur unlocked ho tabhi poochta hai; phone andhera ho to na poochna theek hai.</p>
<p><b>Actions, isi kram mein:</b></p>
<ol>
<li><b>HTTP Request</b> · GET · URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/next</code> · Header ka naam bilkul <code>X-Phone-Token</code> — beech mein ya aakhir mein koi space nahi (keyboard khud ek space jod deta hai, tab request phone se nikalti hi nahi) · value = neeche wala token · Response ko variable <code>resp</code> mein save karein.</li>
<li><b>If</b> <code>resp</code> contains <code>text</code>:</li>
<li>&nbsp;&nbsp;<b>JSON Parse</b>: <code>resp</code> ko dictionary <code>msg</code> mein.</li>
<li>&nbsp;&nbsp;<b>Open Website</b>: address haath se type kijiye, chat se kabhi paste nahi: <code>https://wa.me/{lv=msg[to]}?text={lv=msg[text]}</code> (<code>lv</code> mein chhota <b>L</b> hai, ank 1 nahi) · <i>URL encode parameters</i> par tick.</li>
<li>&nbsp;&nbsp;<b>Wait</b> 6 second.</li>
<li>&nbsp;&nbsp;<b>UI Interaction</b> → <i>Click</i> → text <code>Send</code>.</li>
<li>&nbsp;&nbsp;<b>Wait</b> 3 second.</li>
<li>&nbsp;&nbsp;<b>HTTP Request</b> · POST · URL <code>https://followup.dr-manoj.in/finance/api/supplier-msg/done</code> · content type <code>application/json</code> · Body: <code>{"id": {lv=msg[id]}, "ok": true}</code>. Yeh request <b>pehli request ko copy karke</b> banaiye — tab key uske saath aa jaati hai.</li>
<li><b>End If</b>.</li>
</ol>
<p><b>Pehli baar:</b> macro ko ek baar <i>Test actions</i> se chalaiye aur phone ki screen dekhte rahiye. Bina dekhe dobara mat chalaiye.</p>
<p class="mut">Ek message server do baar nahi deta: diya hua message 10 minute tak dobara nahi milta. Agar Send nahi dab paaya: POST body <code>{"id": {lv=msg[id]}, "ok": false, "error": "send not clicked"}</code> bhejein — server 30 minute baad phir se dega, aur 30 minute baad Vendor payments page par <b>Bhejo</b> button dikhne lagega.</p>''')

SM_APPEND = '''

# ==========================================================================================================================================
# S454_BILL_REGISTER part 1C (03-Oct-2026, S454 17.7-17.10): THE OWNER'S "RECEPTION PHONE" CARD AND ITS TEST MESSAGE.
#   * kind 'test' (month 'test', vendor 'Test message'): one message the owner queues to his own saved number (setting supplier_msg.test_to,
#     shown masked to its last four, never written to a log, an audit detail or a page in full). Two lines, to prove the line break and the
#     encoding. It is handed out FIRST (the owner is testing now), once per gap (F-702), and a failed test is never retried. It is counted
#     nowhere else: every payment reader reads kinds neft/cheque, every order reader kind 'order'.
#   * s454_card_facts(con): when the phone last asked, the order and payment messages waiting, the masked number, the last test's times.
#     The key is never in it.
# ==========================================================================================================================================
S454_TEST_KEY = "supplier_msg.test_to"


def s454_test_to(con):
    return re.sub(r"\\D", "", str(_setting(con, S454_TEST_KEY, "") or ""))


def s454_mask(d):
    d = re.sub(r"\\D", "", str(d or ""))
    return ("•" * max(0, len(d) - 4) + d[-4:]) if d else ""


def s454_save_test_to(con, who, raw):
    """(ok, message): the owner's own number for test messages; the number never reaches the audit."""
    d = _pa()._wa_digits(raw)
    if not d:
        return False, "Not a phone number (10 digits, or with 91 in front)."
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (S454_TEST_KEY, d, "S454 17.7 -- the owner's own number for the reception phone's test message (never printed in full)"))
    try:
        _pa()._audit(con, who, "s454_test_number_saved", "reception-phone", dict(kit="S454 P1C", digits=len(d)))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return True, "Saved: %s" % s454_mask(d)


def s454_test_body(at=None):
    at = at or _now()
    return "Sanjeevni test · %s\\nYeh sirf jaanch hai — ₹ 1,234.50" % at.strftime("%d-%m %H:%M")


def s454_queue_test(con, who):
    """(ok, message_id or the reason) -- one message of kind 'test' to the saved number."""
    ensure(con)
    to = s454_test_to(con)
    if not to:
        return False, "No test number saved."
    ref = int(con.execute("SELECT COALESCE(MAX(ref), 0) + 1 FROM supplier_msg WHERE kind='test'").fetchone()[0])
    cur = con.execute("INSERT INTO supplier_msg (month, vendor_norm, vendor, kind, ref, to_number, body, status, queued_at) VALUES (?,?,?,?,?,?,?,?,?)",
                      ("test", "TEST", "Test message", "test", ref, to, s454_test_body(), "queued", _iso()))
    try:
        _pa()._audit(con, who, "s454_test_queued", "reception-phone", dict(kit="S454 P1C", message=cur.lastrowid))
    except Exception:                                          # noqa: BLE001
        pass
    con.commit()
    return True, cur.lastrowid


def s454_card_facts(con):
    """The "Reception phone" card's facts (never the key, never a full number)."""
    ensure(con)
    at, _sp, code = str(_setting(con, S452_PHONE_KEY, "")).partition(" ")
    if not at:
        at, code = _s452_phone_from_log()

    def n(sql):
        try:
            return int(con.execute(sql).fetchone()[0])
        except Exception:                                      # noqa: BLE001
            return 0
    t = con.execute("SELECT id, status, queued_at, handed_at, sent_at, last_try_at, last_error FROM supplier_msg WHERE kind='test' ORDER BY id DESC LIMIT 1").fetchone()
    return dict(last_ask=at or "", code=code or "",
                orders_wait=n("SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND status IN ('queued','failed') AND to_number IS NOT NULL"),
                pay_wait=n("SELECT COUNT(*) FROM supplier_msg WHERE kind IN ('neft','cheque') AND status IN ('queued','failed') AND to_number IS NOT NULL"),
                test_to=s454_mask(s454_test_to(con)),
                last_test=(dict(id=t[0], status=t[1], queued_at=t[2], handed_at=t[3], sent_at=t[4], tried_at=t[5], error=t[6]) if t else None))
# ---- S454 part 1C end -------------------------------------------------------------------------------------------------------------------
'''

# ------------------------------------------------------------------------------------------------ porders_s454.py
PS_L_OLD = ('''def L(en, k, *a):
    s = T[k][1 if en else 0]
    return (s % a) if a else s
''')
PS_L_NEW = ('''def L(en, k, *a):
    s = T[k][1 if en else 0]
    s = (s % a) if a else s
    if en:                                                    # S454 P1C (17.5): "1 medicine", "1 supplier", "1 bill" -- never "1 medicines"
        s = re.sub(r"(?<![\\d,])1 (medicine|supplier|bill)s\\b", r"1 \\1", s)
    return s
''')
PS_VALID_OLD = '''"order.phone_alive_min": (5, 600),'''
PS_VALID_NEW = '''"order.phone_alive_min": (5, 1440),'''
PS_CARD_OLD = '''    h.append('<details %s id="s454settings"><summary><b>Settings (S454)</b></summary><table style="width:100%%;font-size:14px">%s</table></details>' % (st, "".join(rows)))'''
PS_CARD_NEW = '''    h.append(phone_card(con, st))                              # S454 P1C (17.7): the reception phone's state and a test message
    h.append('<details %s id="s454settings"><summary><b>Settings (S454)</b></summary><table style="width:100%%;font-size:14px">%s</table></details>' % (st, "".join(rows)))'''
PS_APPEND = '''

# ==========================================================================================================================================
# S454 part 1C (17.7): THE OWNER'S "RECEPTION PHONE" CARD on the old page -- when the phone last asked, the messages waiting (orders,
# payments), the test number (masked), "Send a test message", the last test's state in IST. The key is never on it.
#    POST /finance/porders/api/s454/test_number {number}     the owner only; the number never reaches a log or the audit
#    POST /finance/porders/api/s454/test_send                the owner only; one message of kind 'test'
# ==========================================================================================================================================
def _when(iso):
    d = OS._dtm(iso)
    return d.strftime("%d-%m %H:%M") if d else ""


def phone_card(con, st):
    import supplier_msg as SM                                 # noqa: PLC0415
    f = SM.s454_card_facts(con)
    if f["last_ask"]:
        ask = "%s IST%s" % (_when(f["last_ask"]), "" if f["code"] == "200" else " — answered %s (wrong key)" % esc(f["code"]))
    else:
        ask = "never"
    lt = f["last_test"]
    if lt:
        steps = ["queued %s" % _when(lt["queued_at"])]
        if lt["handed_at"]:
            steps.append("handed to the phone %s" % _when(lt["handed_at"]))
        if lt["status"] == "sent":
            steps.append("sent %s" % _when(lt["sent_at"]))
        elif lt["status"] == "failed":
            steps.append("failed %s: %s" % (_when(lt["tried_at"]), lt["error"] or "the phone said no"))
        test_line = "Last test: " + " · ".join(steps)
    else:
        test_line = "No test sent yet."
    has = bool(f["test_to"])
    return ('<div %s id="s454phone"><b>Reception phone</b>'
            '<div>Last asked the server: <b>%s</b></div>'
            '<div>Waiting for the phone: <b>%d</b> order message%s · <b>%d</b> payment message%s</div>'
            '<div style="color:#666;font-size:13px">The phone sends only while it is awake and unlocked; a dark phone does not ask, and that is normal.</div>'
            '<div style="margin-top:6px">Test number: <b id="s454testto">%s</b> <input id="s454testnum" inputmode="tel" placeholder="your number" style="width:150px;min-height:36px"> '
            '<button style="min-height:36px" onclick="s454t(\\'test_number\\',{number:document.getElementById(\\'s454testnum\\').value})">Save</button></div>'
            '<div style="margin-top:6px"><button id="s454testsend" style="min-height:40px" %s onclick="s454t(\\'test_send\\',{})">Send a test message</button>%s</div>'
            '<div id="s454testlast" style="margin-top:4px">%s</div>'
            '<script>function s454t(a,b){fetch(\\'/finance/porders/api/s454/\\'+a,{method:\\'POST\\',headers:{\\'Content-Type\\':\\'application/json\\'},'
            'body:JSON.stringify(b)}).then(function(r){return r.json();}).then(function(j){if(!j.ok){alert(j.message||j.error);return;}location.reload();});}</script></div>'
            % (st, ask, f["orders_wait"], "" if f["orders_wait"] == 1 else "s", f["pay_wait"], "" if f["pay_wait"] == 1 else "s",
               esc(f["test_to"]) if has else "none saved", "" if has else "disabled",
               "" if has else ' <span style="color:#8c1d18">Save a test number first.</span>', esc(test_line)))


def _owner_api():
    u, con, kind, err = _auth_api()
    if err:
        return None, None, err
    if kind != "owner":
        return None, None, (jsonify(ok=False, error="owner_only"), 403)
    return u, con, None


@bp.route(P + "/api/s454/test_number", methods=["POST"])
def api_test_number():
    u, con, err = _owner_api()
    if err:
        return err
    import supplier_msg as SM                                 # noqa: PLC0415
    ok, msg = SM.s454_save_test_to(con, who(u), str(_body().get("number") or "")[:30])
    return jsonify(ok=ok, message=msg), (200 if ok else 400)


@bp.route(P + "/api/s454/test_send", methods=["POST"])
def api_test_send():
    u, con, err = _owner_api()
    if err:
        return err
    import supplier_msg as SM                                 # noqa: PLC0415
    ok, v = SM.s454_queue_test(con, who(u))
    return (jsonify(ok=True, message_id=v), 200) if ok else (jsonify(ok=False, error="no_test_number", message=v), 409)
# ---- S454 part 1C end -------------------------------------------------------------------------------------------------------------------
'''

# ------------------------------------------------------------------------------------------------ order_sheet.py
OS_SET_OLD = '''    "order.phone_alive_min": ("30", "S454: the reception phone silent this long -- the WhatsApp button is disabled"),'''
OS_SET_NEW = ('''    "order.phone_alive_min": ("720", "S454: the reception phone silent this long -- the WhatsApp button is disabled (17.10: it asks only while "
                                      "awake and unlocked, so a dark phone is normal)"),''')
OS_LINE_OLD = ('''"The reception phone has not asked the server for %d minutes%s" % (
                                                                     int_setting(con, "order.phone_alive_min"),''')
OS_LINE_NEW = ('''"The reception phone has not asked the server for %s%s" % (
                                                                     _span(int_setting(con, "order.phone_alive_min")),''')
OS_APPEND = '''


def _span(minutes):
    """S454 P1C: 720 -> '12 hours', 90 -> '90 minutes' (the owner's line)."""
    m = int(minutes or 0)
    if m >= 120 and m % 60 == 0:
        return "%d hours" % (m // 60)
    return "%d minute%s" % (m, "" if m == 1 else "s")
'''

EDITS = {
    "supplier_msg.py": [(SM_NEXT_OLD, SM_NEXT_NEW), (SM_SETUP_OLD, SM_SETUP_NEW)],
    "porders_s454.py": [(PS_L_OLD, PS_L_NEW), (PS_VALID_OLD, PS_VALID_NEW), (PS_CARD_OLD, PS_CARD_NEW)],
    "order_sheet.py": [(OS_SET_OLD, OS_SET_NEW), (OS_LINE_OLD, OS_LINE_NEW)],
}
APPEND = {"supplier_msg.py": SM_APPEND, "porders_s454.py": PS_APPEND, "order_sheet.py": OS_APPEND}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(FROM):
        raw = open(os.path.join(a.finance, f), "rb").read()
        m = hashlib.md5(raw).hexdigest()
        if m != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing built" % (f, m, FROM[f]))
        if f in REPLACE:
            out = open(os.path.join(a.kit, REPLACE[f]), "rb").read()
            n = "whole file, v1.1"
        else:
            txt = raw.decode("utf-8")
            for old, new in EDITS.get(f, []):
                c = txt.count(old)
                if c != 1:
                    raise SystemExit("STOP: an anchor occurs %d times in %s -- nothing built: %r" % (c, f, old[:80]))
                txt = txt.replace(old, new, 1)
            if not txt.endswith("\n"):
                txt += "\n"
            txt += APPEND.get(f, "").lstrip("\n") if txt.endswith("\n\n") else APPEND.get(f, "")
            out = txt.encode("utf-8")
            n = "%d edits + 1 block" % len(EDITS.get(f, []))
        with open(os.path.join(a.out, f), "wb") as fh:
            fh.write(out)
        print("built %-20s %s -> %s  (%s)" % (f, m[:8], hashlib.md5(out).hexdigest(), n))


if __name__ == "__main__":
    main()
