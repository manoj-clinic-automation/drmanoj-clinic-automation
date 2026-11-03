#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s702.py -- kit S702_OWNER_REPORT_NOTICES (03-Nov-2026, Sanjeevni session 380).

    python3 -B make_s702.py <root> <kitdir> <outdir>   reads <root>/finance/{reports_tile,reports_watch,porders_s454}.py and
                                                       <kitdir>/owner_notice.py; writes all four under <outdir>/finance/

WHY.  The owner, 03-Nov 09:43-10:10 IST: he is to be told when Shavez's morning reports, Amir's exports and Darpan's order sheet are DONE,
and about his own three lists -- every day, Sundays too ("Saturday work is exported on Sunday, and Amir also works on Sunday ... Don't
make them silent on Sundays"); the plan he approved said a Monday that does not ask for Sunday's own sale report is fixed too.

WHAT.  One new file (owner_notice.py, copied whole) and three files with anchored edits (each anchor exactly once, else REFUSED).
  reports_tile.py (03902a5d):
    1. the docstring's date rule: yesterday, every day.
    2. _due_day: yesterday, every day -- the counter sold on 20-Sep, 18-Oct and 25-Oct (sale_bill), and an empty Sunday's sale report
       is VERIFIED by the door and passes the spine's reader (04-Oct: 0 bills, ok) -- so a Monday asks for Sunday's pair.
    3. _month_rows: Stock Expiry out (F-1090, D822; nothing reads it since S642); the valuation stays.
    4-5. its selftest: a Monday's due day is Sunday; the 3rd's monthly row is the valuation alone.
  reports_watch.py (428c389c):
    1. the docstring: every day, Sundays too.
    2-3. decide() and tick(): the two Sunday-quiet returns go.
    4. its selftest: a Sunday is told.
  porders_s454.py (438714b8):
    1. _s702_waoff: the disabled WhatsApp button's line says WHY (F-1089) -- the reception phone silent since <dd-mm hh:mm>, or refused,
       or (no key) the old words.
    2. the order page uses it.
    3. the WhatsApp confirm screen uses it too (it said "not set up" when the phone was only silent -- the cold review).
"""
import hashlib
import os
import sys

FROM = {"finance/reports_tile.py": "03902a5d1e2be049d51bcfe38306b431",
        "finance/reports_watch.py": "428c389c0cbac3eab881fa99d4659b06",
        "finance/porders_s454.py": "438714b8d5c094a9ee7cdc71731b44e0"}

EDITS_RT = [
    ("    the settings, and the DATE it is for: yesterday, or the last day the counter sold (the counter is\n"
     "    closed on Sundays -- measured, no Sunday sale day since July -- so on a Monday the date is Saturday);\n",
     "    the settings, and the DATE it is for: yesterday, every day of the week (S702, 03-Nov-2026: the counter\n"
     "    sells on some Sundays -- 20-Sep, 18-Oct, 25-Oct -- so on a Monday the date is Sunday);\n"),
    ('def _due_day(today):\n'
     '    """The day the morning pair is for: yesterday, or the last day the counter sold.  The counter is\n'
     '    closed on Sundays (measured Jul-Sep 2026: no Sunday sale day), so a Monday\'s pair is Saturday\'s."""\n'
     '    d = today - timedelta(days=1)\n'
     '    while d.weekday() == 6:\n'
     '        d -= timedelta(days=1)\n'
     '    return d\n',
     'def _due_day(today):\n'
     '    """The day the morning pair is for: yesterday, every day of the week.  S702 (03-Nov-2026, the owner: Saturday\'s reports are\n'
     '    exported on Sunday; Sundays are not silent): the counter sold on 20-Sep, 18-Oct and 25-Oct (sale_bill), and an empty Sunday\'s\n'
     '    sale report is VERIFIED and passes the spine\'s reader (04-Oct, 0 bills) -- so a Monday\'s pair is Sunday\'s.  Until S702 a Monday\n'
     '    skipped back to Saturday (measured Jul-Sep: no Sunday sale day)."""\n'
     '    return today - timedelta(days=1)\n'),
    ('    for typ, label, hint in (("STOCK_VALUATION", "Stock valuation", "Stock Valuation, %s tak ka" % _ddmm(last)),\n'
     '                             ("STOCK_EXPIRY", "Stock expiry", "Stock Expiry, %s tak ka" % _ddmm(last))):\n',
     '    for typ, label, hint in (("STOCK_VALUATION", "Stock valuation", "Stock Valuation, %s tak ka" % _ddmm(last)),):\n'
     '        # S702 (F-1090, D822): the monthly Stock Expiry is retired -- nothing reads it since S642; the Batch Stock is the expiry input\n'),
    ('    ck("a Monday\'s due day is Saturday (the counter is closed on Sundays)", _due_day(date(2026, 9, 14)) == date(2026, 9, 12))\n',
     '    ck("a Monday\'s due day is Sunday (S702: the counter sells on some Sundays)", _due_day(date(2026, 9, 14)) == date(2026, 9, 13)\n'
     '       and _due_day(date(2026, 9, 13)) == date(2026, 9, 12))\n'),
    ('       [r["key"] for r in s36["rows"][2:4]] == ["STOCK_VALUATION", "STOCK_EXPIRY"] and s36["rows"][2]["state"] == "due"\n',
     '       [r["key"] for r in s36["rows"] if r.get("monthly")] == ["STOCK_VALUATION"] and s36["rows"][2]["state"] == "due"   # S702: no expiry\n'),
]

EDITS_RW = [
    ("     Never on a Sunday (the counter is closed).  A row not yet sent is withdrawn when the report turns\n",
     "     Every day, Sundays too (S702, the owner 03-Nov: Saturday's reports are exported on Sunday).  A row not yet sent is withdrawn when the report turns\n"),
    ("    out = []\n"
     "    if now.weekday() == 6:\n"
     "        return out\n"
     "    mins = now.hour * 60 + now.minute\n",
     "    out = []                                                     # S702: Sundays are not silent\n"
     "    mins = now.hour * 60 + now.minute\n"),
    ("        if now.weekday() == 6:\n"
     "            return {\"ok\": True, \"quiet\": \"sunday\"}\n",
     ""),
    ('    ck("a Sunday is quiet", decide(s, 2, 600, at(11, 0, d=11)) == [])\n',
     '    ck("a Sunday is told too (S702)", len(decide(s, 2, 600, at(11, 0, d=11))) == 1)\n'),
]

WAOFF = '''
def _s702_waoff(con, en, why):
    """S702 (F-1089): the disabled WhatsApp button says WHY -- since when the reception phone has been silent (or refused); with no key,
    the old words.  The phone's last ask is supplier_msg.phone_last ('<when> <code>'), written by the queue door."""
    if why != "silent":
        return L(en, "wa_off")
    raw = str(OS.setting(con, "supplier_msg.phone_last", "") or "")
    at, _sp, code = raw.partition(" ")
    d = OS._dtm(at)
    if d is None:
        return L(en, "wa_off")
    when = d.strftime("%d-%m %H:%M")
    if code and code != "200":
        return ("The reception phone asked at %s and was refused (%s) \\u2014 tell the doctor; order by call meanwhile" % (when, code) if en else
                "Reception phone ne %s par poocha par mana ho gaya (%s) \\u2014 Doctor sahab ko bataiye; tab tak call se order kijiye" % (when, code))
    return ("The reception phone has been silent since %s \\u2014 unlock it, keep the screen on and mobile data on; order by call meanwhile" % when
            if en else
            "Reception phone %s se chup hai \\u2014 phone unlock kijiye, screen on aur mobile data on rakhiye; tab tak call se order kijiye" % when)

'''

EDITS_PO = [
    ("\ndef _s605_waiting(con):\n", WAOFF + "\ndef _s605_waiting(con):\n"),
    ("            h.append('<div class=\"mut\" id=\"waoff\">%s</div>' % L(en, \"wa_off\"))\n",
     "            h.append('<div class=\"mut\" id=\"waoff\">%s</div>' % esc(_s702_waoff(con, en, _why)))   # S702 (F-1089): why, in words\n"),
    ("'<div class=\"mut\" id=\"waoff\">%s</div><a class=\"more\" id=\"waback\" href=\"%s\">%s</a>' % (L(en, \"wa_off\"), back, L(en, \"wa_back\"))",
     "'<div class=\"mut\" id=\"waoff\">%s</div><a class=\"more\" id=\"waback\" href=\"%s\">%s</a>' % (esc(_s702_waoff(con, en, _why)), back, L(en, \"wa_back\"))"),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build_one(rel, src_bytes, edits):
    if md5(src_bytes) != FROM[rel]:
        raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (rel, md5(src_bytes)[:8], FROM[rel][:8]))
    s = src_bytes.decode("utf-8")
    for i, (old, new) in enumerate(edits, 1):
        n = s.count(old)
        if n != 1:
            raise SystemExit("REFUSED: %s anchor %d occurs %d times (must be exactly once)" % (rel, i, n))
        s = s.replace(old, new, 1)
    return s.encode("utf-8")


def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    root, kitdir, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    for rel, edits in (("finance/reports_tile.py", EDITS_RT), ("finance/reports_watch.py", EDITS_RW), ("finance/porders_s454.py", EDITS_PO)):
        with open(os.path.join(root, rel), "rb") as fh:
            out = build_one(rel, fh.read(), edits)
        dst = os.path.join(outdir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s %s -> %s (%d edits)" % (rel, FROM[rel][:8], md5(out)[:8], len(edits)))
    with open(os.path.join(kitdir, "owner_notice.py"), "rb") as fh:
        b = fh.read()
    dst = os.path.join(outdir, "finance/owner_notice.py")
    with open(dst, "wb") as fh:
        fh.write(b)
    print("built finance/owner_notice.py (new) -> %s" % md5(b)[:8])


if __name__ == "__main__":
    main()
