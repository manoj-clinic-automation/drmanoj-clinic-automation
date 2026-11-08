#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s755.py -- S755_SUMMARY_REMINDERS: the anchored changes and the appended sections of four live files (this project's only).
    python3 -B make_s755.py <finance dir> <out dir> [<dir holding the sec_*755.txt files>]
Each FROM file must carry its pinned md5 (the live bytes of 08-Nov 18:58 IST: the 08-Nov bundle + kits S749, S750, S753); every anchor must
stand EXACTLY the number of times named; the TO md5s are printed."""
import hashlib
import os
import sys

FROM = {"finance/scan_register.py": "0f7ba5fdae40a6c7c35bfb070c4fbc02",     # S753's TO (live 08-Nov 18:58 IST)
        "finance/purchase_app.py": "52d9e10c5b4b5b5142d7600f0b698dac",      # S753's TO
        "finance/porders_s454.py": "a8fca8efcb93256bbf8e579c72ce84e1",      # S750's TO
        "finance/owner_notice.py": "7adbfc2442d1f8158a110ee44dcdcbc4"}      # S722's TO (the 08-Nov bundle)
APPEND = {"finance/scan_register.py": "sec_sr755.txt", "finance/owner_notice.py": "sec_on755.txt"}

SR_EDITS = [
    # F-1188: the hub's and the console's 'paper matches' count the accepted and confirmed bills, as row 1's heading does
    ('''    n = dict(match=c.get("verified", 0) + c.get("has_scan", 0), accepted=c.get("accepted", 0), confirmed=c.get("confirmed", 0),''',
     '''    n = dict(match=c.get("verified", 0) + c.get("has_scan", 0) + c.get("accepted", 0) + c.get("confirmed", 0),   # S755 (F-1188): as row 1's heading
             accepted=c.get("accepted", 0), confirmed=c.get("confirmed", 0),''', 1),
    # row 1's body counts as its heading does
    ('''    l1 = ['<div class="mut">Nothing to do here. The %d bill%s that match are on <a href="%s/page/scans?month=%s">the full list</a>.%s</div>'
          % (n_match, "" if n_match == 1 else "s", esc(prefix), esc(month),
             (" %d accepted without paper." % c.get("accepted", 0)) if c.get("accepted") else "")]''',
     '''    n_head = n_match + c.get("accepted", 0) + c.get("confirmed", 0)                           # S755: the body counts as the heading does
    l1 = ['<div class="mut">Nothing to do here. The %d bill%s that match are on <a href="%s/page/scans?month=%s">the full list</a>%s.</div>'
          % (n_head, "" if n_head == 1 else "s", esc(prefix), esc(month),
             (" (%d matched to the rupee%s%s)" % (n_match, (", %d accepted without paper" % c.get("accepted", 0)) if c.get("accepted") else "",
                                                 (", %d confirmed by you" % c.get("confirmed", 0)) if c.get("confirmed") else ""))
             if (c.get("accepted") or c.get("confirmed")) else "")]''', 1),
    # row 8: ' -- ' read as ' · '
    ('''The lock and the NEFT read this page and Marg\\'s reports -- nothing else.''',
     '''The lock and the NEFT read this page and Marg\\'s reports · nothing else.''', 1),
    # row 7: the awaited line -- the ask is automatic now
    ('''        else:
            who = "Reception, or you."
            acts.append(_s749_btn("Ask reception to scan it", dict(u=u, b=dict(body, decision="scan")), "s736b s749y"))
        acts.append(_s749_btn("%s gives no summary" % d["name"].title(), dict(u=u, b=dict(body, decision="none"))))''',
     '''        else:                                             # S755: on reception's list by itself since the month ended; the owner and Shavez told each morning
            who = "On reception's list by itself since the month ended · you and Shavez are told each morning until it comes."
        acts.append(_s749_btn("%s gives no summary" % d["name"].title(), dict(u=u, b=dict(body, decision="none"))))''', 1),
    ('''                who = "%s<br>Asked the dealer %s -- waiting." % (why, esc(ddmon(str(a.get("at") or "")[:10])))''',
     '''                who = "%s<br>Asked the dealer %s · waiting." % (why, esc(ddmon(str(a.get("at") or "")[:10])))''', 1),
    ('''            who = "%s<br><b>Nothing for you here</b> -- it clears through rows 2 and 6." % why''',
     '''            who = "%s<br><b>Nothing for you here</b> · it clears through rows 2 and 6." % why''', 1),
    ('''                who += " <b>That carry is stale</b> -- Marg now carries the bill; nothing is carried; undo it."''',
     '''                who += " <b>That carry is stale</b> · Marg now carries the bill; nothing is carried; undo it."''', 1),
    ('''        who = "Nobody yet -- reception scans the dealer's summary when it comes, early next month."''',
     '''        who = "Nobody yet · reception scans the dealer's summary when it comes, early next month."''', 1),
    # row 7's footer and row 8's note: ' -- ' read as ' · '
    ("""Every dealer\\'s running ledger -- bills with their items, returns, summaries, payments, the balance,""",
     """Every dealer\\'s running ledger · bills with their items, returns, summaries, payments, the balance,""", 1),
    ("""re-export after the last correction is in -- that export is the proof the corrections went in.""",
     """re-export after the last correction is in · that export is the proof the corrections went in.""", 1),
    # the possessive
    ('''        acts.append(_s749_btn("Not %s's summary" % d["name"].title(), dict(u=prefix + "/api/s750/dealer_of", b=dict(scan=sid, dealer=""))))''',
     '''        acts.append(_s749_btn("Not %s summary" % _s755_poss(d["name"].title()), dict(u=prefix + "/api/s750/dealer_of", b=dict(scan=sid, dealer=""))))''', 1),
    ('''        h += '<div class="mut" style="margin:-2px 0 6px"><a href="%s/page/ledger/%s">%s\\'s ledger</a></div>' % (esc(prefix), esc(_s750_q(d["key"])), esc(d["name"].title()))''',
     '''        h += '<div class="mut" style="margin:-2px 0 6px"><a href="%s/page/ledger/%s">%s ledger</a></div>' % (esc(prefix), esc(_s750_q(d["key"])), esc(_s755_poss(d["name"].title())))''', 1),
    # row 7's help sentence, in plain English
    ('''A difference rows 2 or 6 already carry holds nothing new. A dealer who gives no summary is marked once and not waited for.</div>\'''',
     '''A difference that row 2 (Amir\\'s corrections) or row 6 (returns) already explains needs nothing from you. A dealer who gives no summary is marked once and not waited for. '
           'Once the month has ended, every awaited summary is on reception\\'s list by itself, and you and Shavez are told each morning until all are in.</div>\'''', 1),
]

PA_EDITS = [
    # F-1189: the months before the register began read 'settled outside the system' on every ledger -- paid = payable, balance 0; a typed Paid wins
    ('''        paid_p = typed_paid if typed_paid is not None else (payable if (neft and bank == "NEFT") else sum(c["amount_p"] for c in cheques if not c["voided"]))
        final = str((_month_status(con, m) or {}).get("status") or "") == "final"''',
     '''        paid_p = typed_paid if typed_paid is not None else (payable if (neft and bank == "NEFT") else sum(c["amount_p"] for c in cheques if not c["voided"]))
        settled = False                                       # S755 (F-1189): a month before the register began was settled outside the system
        if typed_paid is None and m < str(_s454_sr().setting(con, "purchase.register_from", "2026-10-01"))[:7]:
            paid_p, settled = payable, True
        final = str((_month_status(con, m) or {}).get("status") or "") == "final"''', 1),
    ('''                                  payable_p=payable, paid_p=paid_p, balance_p=payable - (paid_p or 0), cheques=cheques, neft=neft, typed_paid=typed_paid, final=final,''',
     '''                                  payable_p=payable, paid_p=paid_p, balance_p=payable - (paid_p or 0), cheques=cheques, neft=neft, typed_paid=typed_paid, final=final, settled=settled,''', 1),
    ('''        fy = out["fys"].setdefault(_s750_fy(m), dict(fy=_s750_fy(m), months=0, purchases_p=0, returns_p=0, paid_p=0, payable_p=0, items={}))
        fy["months"] += 1''',
     '''        fy = out["fys"].setdefault(_s750_fy(m), dict(fy=_s750_fy(m), months=0, purchases_p=0, returns_p=0, paid_p=0, payable_p=0, items={}, settled=0))
        fy["months"] += 1
        fy["settled"] += 1 if settled else 0                  # S755 (F-1189)''', 1),
    ('''    pay_h = '<div class="pay">Paid: %s</div>' % (" · ".join(pays) if pays else '<span class="mut">nothing recorded yet</span>')''',
     '''    if mo.get("settled"):                                   # S755 (F-1189)
        pays.append("settled outside the system (before the register began) · paid = payable")
    pay_h = '<div class="pay">Paid: %s</div>' % (" · ".join(pays) if pays else '<span class="mut">nothing recorded yet</span>')''', 1),
    ('''        h.append('<div class="fy"><div class="kv"><span><b>%s</b> · %d month%s</span><span>purchases <b>%s</b></span><span>returns <b>%s</b></span><span>payable <b>%s</b></span>'
                 '<span>paid <b>%s</b></span><span class="%s">balance <b>%s</b></span></div>'
                 '<details class="b"%s><summary><span>Items supplied in %s · %d</span><span class="n">%s units</span></summary>%s</details></div>'
                 % (_esc(fy["fy"]), fy["months"], "" if fy["months"] == 1 else "s", _r(fy["purchases_p"]), _r(fy["returns_p"]), _r(fy["payable_p"]), _r(fy["paid_p"]),''',
     '''        h.append('<div class="fy"><div class="kv"><span><b>%s</b> · %d month%s%s</span><span>purchases <b>%s</b></span><span>returns <b>%s</b></span><span>payable <b>%s</b></span>'
                 '<span>paid <b>%s</b></span><span class="%s">balance <b>%s</b></span></div>'
                 '<details class="b"%s><summary><span>Items supplied in %s · %d</span><span class="n">%s units</span></summary>%s</details></div>'
                 % (_esc(fy["fy"]), fy["months"], "" if fy["months"] == 1 else "s",
                    (" (%d settled outside the system, before the register began)" % fy["settled"]) if fy.get("settled") else "",   # S755 (F-1189)
                    _r(fy["purchases_p"]), _r(fy["returns_p"]), _r(fy["payable_p"]), _r(fy["paid_p"]),''', 1),
    # the sheet's note: ' -- ' read as ' · '
    ('''carried by you (row 7) -- not typed; it leaves with your Undo''', '''carried by you (row 7) · not typed; it leaves with your Undo''', 1),
]

P454_EDITS = [
    ('''          "bk_s750_since": ("Doctor sahab ne %s ko kaha", "Asked by the doctor %s")})''',
     '''          "bk_s750_since": ("Doctor sahab ne %s ko kaha", "Asked by the doctor %s"),
          "bk_s750_auto": ("%s khatam — dealer ka hisaab (summary) abhi tak nahi aaya", "%s has ended — the dealer's summary has not come yet")})   # S755''', 1),
    ('''                     % (esc(a["dealer"]), esc(a["month"]), esc(head), esc(L(en, "bk_s750_s")), esc(L(en, "bk_s750_since", OS.ddmm(str(a.get("at") or "")[:10]))),''',
     '''                     % (esc(a["dealer"]), esc(a["month"]), esc(head), esc(L(en, "bk_s750_s")),
                        esc(L(en, "bk_s750_auto", _s750_month_hi(a["month"], en)) if a.get("auto") else L(en, "bk_s750_since", OS.ddmm(str(a.get("at") or "")[:10]))),   # S755''', 1),
]

ON_EDITS = [
    ('''    ("owner_notice.medical_back_wait_min", "15", "S722 (F-1134): 'Medical PC back' waits until nothing is waiting on it, or this long after "
     "its first beat back"),
)''',
     '''    ("owner_notice.medical_back_wait_min", "15", "S722 (F-1134): 'Medical PC back' waits until nothing is waiting on it, or this long after "
     "its first beat back"),
    ("owner_notice.summaries_hhmm", "10:30", "S755 (D870): the awaited dealer summaries of an ended month are said once a day at this time"),
    ("owner_notice.summaries_to", "manoj,shavez", "S755 (D870): the logins whose clinic-app devices get the summaries line (the owner and Shavez)"),
)''', 1),
    ('''    for u in [x.strip().lower() for x in setting(con, "owner_notice.to").split(",") if x.strip()]:''',
     '''    to_key = "owner_notice.summaries_to" if str(key).startswith("summaries:") else "owner_notice.to"   # S755: the summaries line goes to the owner and Shavez
    for u in [x.strip().lower() for x in setting(con, to_key).split(",") if x.strip()]:''', 1),
]

EDITS = {"finance/scan_register.py": SR_EDITS, "finance/purchase_app.py": PA_EDITS, "finance/porders_s454.py": P454_EDITS, "finance/owner_notice.py": ON_EDITS}


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(text, edits, name):
    for old, new, n in edits:
        c = text.count(old)
        if c != n:
            sys.exit("!! %s: anchor stands %d time(s), expected %d:\n%s" % (name, c, n, old[:200]))
        text = text.replace(old, new)
    return text


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    fin, out = sys.argv[1], sys.argv[2]
    here = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    for rel, want in FROM.items():
        src = os.path.join(fin, os.path.basename(rel))
        b = open(src, "rb").read()
        if md5(b) != want:
            sys.exit("!! %s is %s, expected %s -- not the live bytes this kit was built on; STOP" % (src, md5(b)[:8], want[:8]))
        if b"\r\n" in b:
            sys.exit("!! %s carries CRLF; STOP" % src)
        t = b.decode("utf-8")
        if "KIT_S755" in t:
            sys.exit("!! %s already carries S755; STOP" % src)
        t = apply(t, EDITS[rel], rel)
        if rel in APPEND:
            sec = open(os.path.join(here, APPEND[rel]), "rb").read().decode("utf-8")
            t = t.rstrip("\n") + "\n" + sec
        nb = t.encode("utf-8")
        os.makedirs(os.path.join(out, os.path.dirname(rel)), exist_ok=True)
        open(os.path.join(out, rel), "wb").write(nb)
        print("%s  %s -> %s" % (rel, want[:8], md5(nb)))


if __name__ == "__main__":
    main()
