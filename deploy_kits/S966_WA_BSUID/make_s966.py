#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s966.py -- kit S966_WA_BSUID (the parent, S531, 27-Nov-2026).

MyOperator's mail of 26-Nov-2026 20:30 IST ("WhatsApp webhook users: 5 days left to update"): from 1-Dec-2026 a WhatsApp
event may carry Meta's Business-Scoped User ID (BSUID, 'IN.' + 128 characters, up to 131) in customer_identifier instead of
the patient's mobile, and a meta_bsuid field beside it. Four live files read that field as a mobile and turn it into digits;
the Call Consoles' chat key (calls_console.py, cold review MUST) would cut a BSUID-keyed chat into a made-up number.

This script remakes the four TO files from the LIVE bytes, by exact anchored replacements (each anchor must occur exactly
the stated number of times, or nothing is written) -- five files:
    python3 make_s966.py <wa_receiver.py> <wa_alert.py> <portal_inbox.py> <records.py> <calls_console.py> <out_dir>
The rule, the same in all four: a value is a mobile only when it has no letter (every number seen so far); a value with a
letter is the BSUID -- never turned into digits, never sent to, never dialled. When no value in a push is a BSUID, every file
behaves byte-for-byte as before (the walk proves it on the FROM vs TO).
"""
import hashlib
import os
import sys

HELPERS = '''

# S966 (27-Nov-2026, MyOperator's mail of 26-Nov 20:30 IST): Meta's Business-Scoped User ID (BSUID). From 1-Dec a WhatsApp
# event may carry it in customer_identifier instead of the mobile ('IN.' + 128 characters, up to 131), with a meta_bsuid
# field beside it. A value is a mobile only when it has no letter -- every number seen so far; a value with a letter is the
# BSUID and is never turned into digits. With no BSUID in a push, everything below behaves exactly as before.
def s966_is_bsuid(v):
    """True for Meta's BSUID: 6-200 characters, no space, at least one letter A-Z. A mobile never has a letter."""
    if isinstance(v, (dict, list, tuple)):
        return False
    s = str(v if v is not None else "").strip()
    return 6 <= len(s) <= 200 and not any(ch.isspace() for ch in s) and any("a" <= ch.lower() <= "z" for ch in s)


def s966_find_bsuid(d, depth=0):
    """The first meta_bsuid value anywhere in the push (6 levels deep at most), or ''. Never raises."""
    try:
        if depth > 6:
            return ""
        if isinstance(d, dict):
            v = d.get("meta_bsuid")
            if s966_is_bsuid(v):
                return str(v).strip()
            for x in d.values():
                r = s966_find_bsuid(x, depth + 1)
                if r:
                    return r
        elif isinstance(d, list):
            for x in d[:50]:
                r = s966_find_bsuid(x, depth + 1)
                if r:
                    return r
    except Exception:                                                   # noqa: BLE001
        pass
    return ""


def s966_pick(d, dig, paths):
    """(the mobile, the BSUID). The first value found, in the paths' order, is exactly what dig(d, *paths) gave before. When
    it is a BSUID there is NO mobile in this push (MyOperator: the BSUID comes instead of the mobile) -- no later path is
    trusted for one; the BSUID is that value. Otherwise the BSUID is any meta_bsuid in the push."""
    for p in paths:
        v = dig(d, p)
        if v in (None, "", [], {}):
            continue
        if s966_is_bsuid(v):
            return "", str(v).strip()
        return v, s966_find_bsuid(d)
    return "", s966_find_bsuid(d)
'''

NO_NUMBER = ('S966_NO_NUMBER = ("This patient wrote on WhatsApp with a username, so there is no mobile number to reply to or '
             'call from here. Reply from MyOperator\'s own WhatsApp page.")\n')

PHONE_PATHS = ('("customer_identifier", "payload.customer_identifier",\n'
               '                    "data.customer_identifier", "customer_number", "payload.customer_number",\n'
               '                    "payload.data.context.from", "contact.wa_id")')


def rep(src, old, new, n=1, what=""):
    k = src.count(old)
    if k != n:
        raise SystemExit("REFUSED: anchor %r found %d times, expected %d" % (what or old[:60], k, n))
    return src.replace(old, new)


def receiver(s):
    s = rep(s, '\n\ndef to_ist_iso(ts):\n    """Make an unambiguous IST timestamp',
            HELPERS + '\n\ndef to_ist_iso(ts):\n    """Make an unambiguous IST timestamp', what="receiver helpers")
    s = rep(s, '    phone     = dig(payload, "customer_identifier", "payload.customer_identifier",\n'
               '                    "data.customer_identifier", "customer_number", "payload.customer_number",\n'
               '                    "payload.data.context.from", "contact.wa_id")\n',
            '    phone, bsuid = s966_pick(payload, dig, ' + PHONE_PATHS + ')   # S966: never a number made from the BSUID\n',
            what="receiver phone")
    s = rep(s, '        "phone":           "".join(ch for ch in str(phone) if ch.isdigit()),\n',
            '        "phone":           "".join(ch for ch in str(phone) if ch.isdigit()),\n'
            '        "bsuid":           str(bsuid or ""),            # S966: written only where the tab has a "bsuid" column\n',
            what="receiver fields")
    return s


def alert(s):
    s = rep(s, '\n\ndef _now():\n', HELPERS + '\n\ndef _now():\n', what="alert helpers")
    s = rep(s, '    phone = dig(payload, "customer_identifier", "payload.customer_identifier", "data.customer_identifier", "customer_number",\n'
               '                "payload.customer_number", "payload.data.context.from", "contact.wa_id")\n',
            '    phone, bsuid = s966_pick(payload, dig, ("customer_identifier", "payload.customer_identifier", "data.customer_identifier",\n'
            '                                            "customer_number", "payload.customer_number", "payload.data.context.from",\n'
            '                                            "contact.wa_id"))   # S966\n',
            what="alert phone")
    s = rep(s, '    return alert("".join(ch for ch in str(phone) if ch.isdigit()), str(message or ""), str(msg_id or ""))\n',
            '    num = "".join(ch for ch in str(phone) if ch.isdigit())\n'
            '    text = str(message or "")\n'
            '    if not num and bsuid:                                           # S966: a WhatsApp username, no mobile in the push\n'
            '        text = "(WhatsApp ID - no mobile number)\\n" + text\n'
            '    return alert(num, text, str(msg_id or ""))\n',
            what="alert return")
    return s


def inbox(s):
    s = rep(s, '\n\ndef to_ist_iso(ts):\n    """The receiver\'s own to_ist_iso()',
            HELPERS + '\n\n' + NO_NUMBER + '\n\ndef s966_key(c, phone, bsuid, ts=""):\n'
            '    """S966: the chat key. A push with a mobile AND a BSUID: the pair is remembered, and a chat kept so far under that\n'
            '    BSUID moves to the mobile. A push with the BSUID alone: the mobile it was last seen with, else the BSUID itself.\n'
            '    Inside the caller\'s transaction, in its own savepoint; never raises (a failure keeps the mobile, else the BSUID)."""\n'
            '    bs = str(bsuid or "").strip()\n'
            '    if not bs or not s966_is_bsuid(bs):\n'
            '        return phone\n'
            '    try:\n'
            '        c.execute("SAVEPOINT s966")\n'
            '        try:\n'
            '            if phone:\n'
            '                r = c.execute("SELECT phone FROM s966_bsuid WHERE bsuid=?", (bs,)).fetchone()\n'
            '                if not r or r[0] != phone:\n'
            '                    c.execute("INSERT OR REPLACE INTO s966_bsuid(bsuid, phone, ts) VALUES(?,?,?)", (bs, phone, str(ts or "")))\n'
            '                if c.execute("SELECT 1 FROM msgs WHERE phone=? LIMIT 1", (bs,)).fetchone():\n'
            '                    c.execute("UPDATE msgs SET phone=? WHERE phone=?", (phone, bs))\n'
            '                    c.execute("UPDATE retry_q SET phone=? WHERE phone=?", (phone, bs))\n'
            '                    rd = c.execute("SELECT ts FROM reads WHERE phone=?", (bs,)).fetchone()\n'
            '                    if rd:\n'
            '                        old = c.execute("SELECT ts FROM reads WHERE phone=?", (phone,)).fetchone()\n'
            '                        if not old or str(rd[0] or "") > str(old[0] or ""):\n'
            '                            c.execute("INSERT OR REPLACE INTO reads(phone, ts) VALUES(?,?)", (phone, rd[0]))\n'
            '                        c.execute("DELETE FROM reads WHERE phone=?", (bs,))\n'
            '                key = phone\n'
            '            else:\n'
            '                r = c.execute("SELECT phone FROM s966_bsuid WHERE bsuid=?", (bs,)).fetchone()\n'
            '                key = r[0] if r and r[0] else bs\n'
            '            c.execute("RELEASE SAVEPOINT s966")\n'
            '            return key\n'
            '        except Exception:                                               # noqa: BLE001\n'
            '            c.execute("ROLLBACK TO SAVEPOINT s966")\n'
            '            c.execute("RELEASE SAVEPOINT s966")\n'
            '    except Exception:                                                   # noqa: BLE001\n'
            '        pass\n'
            '    return phone or bs\n'
            '\n\ndef to_ist_iso(ts):\n    """The receiver\'s own to_ist_iso()', what="inbox helpers")
    # the chat key, the patient-list key, abroad, the full number, the masked tail
    s = rep(s, '    a key passed back by the page comes out unchanged."""\n    d = re.sub(r"\\D", "", str(s or ""))\n',
            '    a key passed back by the page comes out unchanged.\n'
            '    S966: Meta\'s BSUID (a value with a letter) is its own key, unchanged -- never cut into digits."""\n'
            '    if s966_is_bsuid(s):\n'
            '        return str(s).strip()\n'
            '    d = re.sub(r"\\D", "", str(s or ""))\n', what="inbox last10")
    s = rep(s, '    """The old rule (the last 10 digits): kept for the patient list, whose numbers are Indian."""\n',
            '    """The old rule (the last 10 digits): kept for the patient list, whose numbers are Indian."""\n'
            '    if s966_is_bsuid(s):                                                # S966: a BSUID is no patient number\n'
            '        return ""\n', what="inbox ten")
    s = rep(s, '    """True for a chat key longer than 10 digits: a number from another country."""\n',
            '    """True for a chat key longer than 10 digits: a number from another country."""\n'
            '    if s966_is_bsuid(key):                                              # S966: a BSUID is no number at all\n'
            '        return False\n', what="inbox abroad")
    s = rep(s, '    """Country code + number, digits only (the send log\'s customer_number column)."""\n',
            '    """Country code + number, digits only (the send log\'s customer_number column)."""\n'
            '    if s966_is_bsuid(key):                                              # S966\n'
            '        return ""\n', what="inbox full_number")
    s = rep(s, '            return int(c.execute("SELECT COUNT(DISTINCT phone) FROM msgs WHERE length(phone) > 10").fetchone()[0])\n',
            '            return int(c.execute("SELECT COUNT(DISTINCT phone) FROM msgs WHERE length(phone) > 10 "\n'
            '                                 "AND phone NOT GLOB \'*[A-Za-z]*\'").fetchone()[0])     # S966: a BSUID chat is not abroad\n',
            what="inbox abroad_count")
    s = rep(s, 'def tail4(s):\n    return "',
            'def tail4(s):\n    if s966_is_bsuid(s):                                                # S966\n'
            '        return "WA-ID"\n    return "', what="inbox tail4")
    # the push reader
    s = rep(s, '    g = lambda *p, **k: dig(payload, *p, **k)                           # noqa: E731\n    return {\n',
            '    g = lambda *p, **k: dig(payload, *p, **k)                           # noqa: E731\n'
            '    ph, bs = s966_pick(payload, dig, ("customer_identifier", "payload.customer_identifier", "data.customer_identifier",\n'
            '                                      "customer_number", "payload.customer_number", "payload.data.context.from",\n'
            '                                      "contact.wa_id"))                 # S966\n'
            '    return {\n', what="inbox read_push g")
    s = rep(s, '        "phone": g("customer_identifier", "payload.customer_identifier", "data.customer_identifier", "customer_number",\n'
               '                   "payload.customer_number", "payload.data.context.from", "contact.wa_id"),\n',
            '        "phone": ph,\n        "bsuid": bs,\n', what="inbox read_push phone")
    # the store: the remembered pairs
    s = rep(s, "        next_at TEXT NOT NULL, tries INTEGER NOT NULL DEFAULT 1, state TEXT NOT NULL DEFAULT 'waiting', last_err TEXT);\n"
               '    """)\n',
            "        next_at TEXT NOT NULL, tries INTEGER NOT NULL DEFAULT 1, state TEXT NOT NULL DEFAULT 'waiting', last_err TEXT);\n"
            '    CREATE TABLE IF NOT EXISTS s966_bsuid(bsuid TEXT PRIMARY KEY, phone TEXT NOT NULL, ts TEXT);\n'
            '    """)\n', what="inbox db")
    s = rep(s, '    ts = to_ist_iso(p["ts"]) or iso(now_ist())\n    if is_inbound_message(p["event"], p["direction"], mtype, p["body"]):\n',
            '    ts = to_ist_iso(p["ts"]) or iso(now_ist())\n'
            '    phone = s966_key(c, phone, p.get("bsuid"), ts)                      # S966\n'
            '    if is_inbound_message(p["event"], p["direction"], mtype, p["body"]):\n', what="inbox ingest_line")
    # the sender and the routes: never a send or a call to a BSUID
    s = rep(s, '    answered -- status, body, headers (x-amzn-requestid is the id their tech team asks for), time taken."""\n'
               '    cc, nat = split_cc(phone)',
            '    answered -- status, body, headers (x-amzn-requestid is the id their tech team asks for), time taken."""\n'
            '    if s966_is_bsuid(phone):                                            # S966: never a number made from a BSUID\n'
            '        return False, "", S966_NO_NUMBER\n'
            '    cc, nat = split_cc(phone)', what="inbox myop_send")
    s = rep(s, '        if not ph:\n            return fail("no number for this chat")\n',
            '        if not ph:\n            return fail("no number for this chat")\n'
            '        if s966_is_bsuid(ph):                                           # S966\n'
            '            return fail(S966_NO_NUMBER)\n', n=3, what="inbox route guards")
    s = rep(s, '    ph = last10(phone)\n    text = (text or "").strip()[:4000]\n    user = (user or "").strip()\n'
               '    if not ph:\n        return _s959(False, "No number for this chat.", 400)\n',
            '    ph = last10(phone)\n    text = (text or "").strip()[:4000]\n    user = (user or "").strip()\n'
            '    if not ph:\n        return _s959(False, "No number for this chat.", 400)\n'
            '    if s966_is_bsuid(ph):                                               # S966\n'
            '        return _s959(False, S966_NO_NUMBER, 409)\n', what="inbox staff text")
    s = rep(s, '    ph = last10(phone)\n    user = (user or "").strip()\n'
               '    if not ph:\n        return _s959(False, "No number for this chat.", 400)\n',
            '    ph = last10(phone)\n    user = (user or "").strip()\n'
            '    if not ph:\n        return _s959(False, "No number for this chat.", 400)\n'
            '    if s966_is_bsuid(ph):                                               # S966\n'
            '        return _s959(False, S966_NO_NUMBER, 409)\n', what="inbox staff template")
    s = rep(s, "(len(qd) >= 3 and (qd in ph or qd == cid))",
            "(len(qd) >= 3 and ((qd in ph and not s966_is_bsuid(ph)) or qd == cid))", what="inbox search")
    # the page: a BSUID chat reads 'WhatsApp ID (no number)', no MyOperator number link, 'WA' in the circle
    s = rep(s, 'function myopUrl(p){var d=',
            'function isWid(p){return /[A-Za-z]/.test(String(p==null?"":p));}\nfunction myopUrl(p){if(isWid(p))return "";var d=',
            what="inbox js myopUrl")
    s = rep(s, 'function fmtNum(p){p=String(p==null?"":p);',
            'function fmtNum(p){p=String(p==null?"":p);if(isWid(p))return "WhatsApp ID (no number)";', what="inbox js fmtNum")
    s = rep(s, 'function initials(n,p){if(!n)return p.slice(-2);',
            'function initials(n,p){if(!n)return isWid(p)?"WA":p.slice(-2);', what="inbox js initials")
    return s


def records(s):
    s = rep(s, '\n\ndef _fp_of(phone):\n',
            '\n\ndef _s966_phone(b):\n'
            '    """S966: the sender\'s mobile as _dig() found it before. When the first value found is Meta\'s BSUID (a value with\n'
            '    a letter) the push has no mobile: \'\' -- a BSUID is never fingerprinted as a number."""\n'
            '    for p in ("customer_identifier", "payload.customer_identifier", "data.customer_identifier",\n'
            '              "customer_number", "payload.customer_number", "payload.data.context.from"):\n'
            '        v = _dig(b, p)\n'
            '        if v in (None, ""):\n'
            '            continue\n'
            '        s = str(v).strip()\n'
            '        if not isinstance(v, (dict, list)) and 6 <= len(s) <= 200 and not any(ch.isspace() for ch in s) \\\n'
            '                and any("a" <= ch.lower() <= "z" for ch in s):\n'
            '            return ""                                          # the BSUID came instead of the mobile\n'
            '        return v\n'
            '    return ""\n'
            '\n\ndef _fp_of(phone):\n', what="records helper")
    s = rep(s, '            phone = _dig(b, "customer_identifier", "payload.customer_identifier", "data.customer_identifier",\n'
               '                         "customer_number", "payload.customer_number", "payload.data.context.from") or ""\n',
            '            phone = _s966_phone(b)                                     # S966: never a BSUID as a number\n',
            what="records phone")
    return s


def console(s):
    s = rep(s, '    """S871: the WhatsApp chat key as the inbox keeps it -- an Indian number\'s 10 digits, a number abroad whole."""\n',
            '    """S871: the WhatsApp chat key as the inbox keeps it -- an Indian number\'s 10 digits, a number abroad whole.\n'
            '    S966: Meta\'s BSUID (a value with a letter) is no number at all -> \'\' (never listed, never dialled)."""\n'
            '    if any("a" <= ch.lower() <= "z" for ch in str(s or "")):\n'
            '        return ""\n', what="console _s871_key")
    s = rep(s, '    row (10 digits), one call per number per minute. Returns (ok, message, http status). Nothing logged."""\n',
            '    row (10 digits), one call per number per minute. Returns (ok, message, http status). Nothing logged."""\n'
            '    if any("a" <= ch.lower() <= "z" for ch in str(phone10 or "")):     # S966: never digits cut from a BSUID\n'
            '        return False, "This patient wrote on WhatsApp with a username - there is no mobile number to call.", 400\n',
            what="console ivr_call")
    return s


def main(a):
    if len(a) != 6:
        raise SystemExit(__doc__)
    rx, al, ib, rc, cc, out = a
    os.makedirs(out, exist_ok=True)
    jobs = (("wa_receiver.py", rx, receiver), ("wa_alert.py", al, alert), ("portal_inbox.py", ib, inbox),
            ("records.py", rc, records), ("calls_console.py", cc, console))
    made = []
    for name, src, fn in jobs:
        with open(src, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
        made.append((name, fn(text)))
    for name, text in made:                                             # nothing is written unless all four remade
        p = os.path.join(out, name)
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        print("%s  %s" % (hashlib.md5(text.encode("utf-8")).hexdigest(), name))


if __name__ == "__main__":
    main(sys.argv[1:])
