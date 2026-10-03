#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walks_old_s454p3b.py -- kit S454_BILL_REGISTER P3B: the earlier walks that touch what S454 changes, re-run on P3B's patched files
(a copy of part 3's: the box carries parts 1, 1B, 1C, 1D, 2 and 3 now, so their adjustments apply to BOTH runs; "part 3" below = P3B's run).

  S403 (the orthotic order screen), S407 (the NEFT messages and the phone's queue), S410 (the ordering day), S414 (the rules page), S417 (the
  stock beside an order), S428 (the stock watch), S439 (the matcher), S440 (Scan ka kaam), S441 (the scan checks), S444 (the staff-eye walk),
  S446 (Amir's stages) and S452 (Amir's panel).

Each walk is COPIED to scratch (the kit folders are never edited) and run twice: on the box as it is (the baseline -- it carries S454 part 1,
1B, 1C, 1D and 2, so their adjustments apply to BOTH runs) and on the box + part 3 (patched). Every adjustment is an anchored replacement on the copy (anchor exactly once, else STOP), or a data step on that run's own scratch
copy, named below with its reason. The gate: on the patched files a walk is green, or every one of its reds is in its ACCEPT list AND red in the
baseline too (a fact of today's data, or a control that no longer exists -- never something S454 moved).

    walks_old_s454p3b.py --plan PLAN.json
"""
import json
import os
import re
import sqlite3
import subprocess
import sys

R = "S454-ADJUSTED"
# P0 (every walk, the patched run): "?old=1 and porders.simple=0 serve today's page, and S440's and S410's walks pass on it" (the brief, 4.9).
# The earlier walks read the old Purchase-orders page and its API; on their own scratch copy the setting reads 0. The new screen is S454's own walk's.
PRE_SQL = ("INSERT INTO setting (key, value, note) VALUES ('porders.simple', '0', 'S454 walk: the earlier walks read the old page') "
           "ON CONFLICT(key) DO UPDATE SET value='0'")
# P2 (every walk, the patched run): the S454 tables exist on the scratch copy, as the install's first load leaves them on the box (the duty
# map's v4 queries read them).
P2_PY = ("import sys, sqlite3; sys.path.insert(0, sys.argv[1]); import order_sheet; c = sqlite3.connect(sys.argv[2]); order_sheet.ensure(c); c.close(); "
         "print('S454 tables made')")
PRE = {}  # name -> [(code, why, sql)] -- more data on the patched run's own scratch copy
NO_P0 = ("walk_s444.py",)      # its staff-eye walk reads the duty map v4, whose doors are the new screen's: the new screen it must see
BOTH = {  # file -> [(code, why, old, new)] -- on BOTH runs: the box moved on since that kit (never something S454 changes)
    "seed_s403.py": [("B1", "S441 (01-Oct) put the shared reception login on the porders unit: the seed's own list of roles carries it, on both runs",
                      'ROLES = [("darpan", "maker"), ("shavez", "maker"), ("shivani", "maker"), ("alisha", "maker"), ("manoj", "checker")]',
                      'ROLES = [("darpan", "maker"), ("shavez", "maker"), ("shivani", "maker"), ("alisha", "maker"), ("manoj", "checker"), ("reception", "maker")]   # S454-ADJUSTED B1')],
    "walk_s403.py": [("B2", "S441 (01-Oct): the asset app now names who scanned (g.user['username']); the walk's stand-in reception user carries a username, "
                            "on both runs",
                      'ar.g.user = {"display_name": "walk-reception", "role": "reception"}',
                      'ar.g.user = {"display_name": "walk-reception", "role": "reception", "username": "walk-reception"}   # S454-ADJUSTED B2')],
}
P1ADJ = {                      # part 1's adjustments (the box carries part 1 now): on BOTH runs
    "walk_s410.py": [("P3", "order.source = system on its scratch copy, after the walk clears the order.* settings: S410's ordering day (its 09:00 notice, its "
                            "proposals, 'Order not sent', Darpan's count line) is what S454 keeps for the system's own list; Darpan's sheet (the default) is "
                            "S454's own walk's",
                      'db.execute("DELETE FROM setting WHERE key LIKE \'order.%\' OR key=\'porders.rules_approved\'")\n',
                      'db.execute("DELETE FROM setting WHERE key LIKE \'order.%\' OR key=\'porders.rules_approved\'")\n'
                      'db.execute("INSERT INTO setting (key, value, note) VALUES (\'order.source\', \'system\', \'S454-ADJUSTED P3\')")   # S454-ADJUSTED P3\n'),
                     ("P4", "S454 (D666): the 12:00 reminder goes -- the forced 12:00 tick says nothing",
                      r'''check("12:00 before any send: 'Aaj N order: 0 bheja, N baaki — …' naming W410 Weekly;''',
                      r'''check("S454-ADJUSTED P4: 12:00 says nothing (S454: the 12:00 reminder goes);'''),
                     ("P4", "(the same)",
                      r'''re.match(r"^Aaj (\d+) order: 0 bheja, \1 baaki — ", N["remind12"] or "") and "W410 Weekly" in N["remind12"] and ''',
                      r'''N["remind12"] is None and '''),
                     ("P5", "S454 (D666): the 15:00 reminder goes -- the forced 15:00 tick says nothing; Darpan's count line is checked as it was",
                      r'''check("15:00 reads 'Aaj N order: 1 bheja, N-1 baaki — …' without W410 Weekly;''',
                      r'''check("S454-ADJUSTED P5: 15:00 says nothing (S454: the 15:00 reminder goes);'''),
                     ("P5", "(the same)",
                      r'''re.match(r"^Aaj (\d+) order: 1 bheja, \d+ baaki — ", N["remind15"] or "") and "W410 Weekly" not in N["remind15"]''',
                      r'''N["remind15"] is None'''),
                     ("P6", "S454 (D666): ONE reminder at 17:00, 'Order baaki: <the suppliers still to be ordered>' (notice slot R1700); the pushes are "
                            "09:00's and 17:00's, four senders each (8, not 16)",
                      r'''check("17:00 with Fort Co still unsent speaks ('3 bheja', W410 Fort named, W410 Weekly not): '%s'; the notice log holds 0900/1200/1500/1700 once each;''',
                      r'''check("S454-ADJUSTED P6: 17:00 with Fort Co still unsent speaks ('Order baaki: ...', W410 Fort named, W410 Weekly not): '%s'; the notice log holds 0900 and S454's one reminder R1700;'''),
                     ("P6", "(the same)",
                      r'''"3 bheja" in (N["remind17"][0] or "") and "W410 Fort" in N["remind17"][0] and "W410 Weekly" not in N["remind17"][0] and [x["slot"] for x in N["notices"]] == ["0900", "1200", "1500", "1700"] and N["pushes"][0] == 16''',
                      r'''(N["remind17"][0] or "").startswith("Order baaki: ") and "W410 FORT" in N["remind17"][0].upper() and "W410 WEEKLY" not in N["remind17"][0].upper() and [x["slot"] for x in N["notices"]] == ["0900", "R1700"] and N["pushes"][0] == 8'''),
                     ("P7", "S454 (D666): the repeat is of the 17:00 slot (the only one left), its row is R1700; once every proposal is sent the reminder "
                            "names none of them -- silent, or only S403's orthotic card (S454 names that card on both settings: four more pushes)",
                      r'''os.environ["ORDER_TICK"] = "remind12"; out["already12"]''',
                      r'''os.environ["ORDER_TICK"] = "remind17"; out["already12"]'''),
                     ("P7", "(the same)",
                      r'''db.execute("DELETE FROM order_notice WHERE day=? AND slot='1700'", (T.isoformat(),))''',
                      r'''db.execute("DELETE FROM order_notice WHERE day=? AND slot='R1700'", (T.isoformat(),))'''),
                     ("P7", "(the same)",
                      r'''out["silent17"] = [s17.get("silent"), len(q("SELECT id FROM order_notice WHERE day=? AND slot='1700'", T.isoformat())), len([1 for x in open(os.environ["ORDER_PUSH_STUB"], encoding="utf-8") if x.strip()])]''',
                      r'''out["silent17"] = [bool(s17.get("silent")) or not [v for v in (s17.get("text") or "")[len("Order baaki: "):].split(", ") if v in {r["vendor"] for r in q("SELECT vendor FROM order_proposal WHERE day=?", T.isoformat())}], len(q("SELECT id FROM order_notice WHERE day=? AND slot='R1700' AND text LIKE '%W410%'", T.isoformat())), len([1 for x in open(os.environ["ORDER_PUSH_STUB"], encoding="utf-8") if x.strip()]), bool(s17.get("silent")), s17.get("text")]   # S454-ADJUSTED P7'''),
                     ("P7", "(the same)",
                      r'''check("once every proposal of the day is sent the reminder is SILENT (no notice row, no push); a repeat of a slot already sent answers already", N["silent17"] == [True, 0, 16] and N["already12"] is True''',
                      r'''check("S454-ADJUSTED P7: once every proposal of the day is sent the 17:00 reminder names none of them -- silent, or only S403's orthotic card (S454 names it on both settings); a repeat of the 17:00 slot answers already", N["silent17"][:2] == [True, 0] and N["silent17"][2] == (8 if N["silent17"][3] else 12) and N["already12"] is True''')],
    "walk_s444.py": [("P8", "S444's bar check reads the old page's s440bar; with S454 /finance/porders is the one-task screen -- the old page stays at ?old=1 "
                            "and is checked there, word for word; the new screen is checked beside it: 'Signed in: alisha' on its home, '← BACK' once",
                      '''    s, hp, _l = FG("alisha", "/finance/porders")\n''',
                      '''    s, hp, _l = FG("alisha", "/finance/porders?old=1")   # S454-ADJUSTED P8\n'''
                      '''    _sn, _hn, _ln = FG("alisha", "/finance/porders")\n'''
                      '''    out["porders_new"] = dict(status=_sn, signed="Signed in: alisha" in _hn, backs=_hn.count("← BACK"))\n'''),
                     ("P8", "(the same)",
                      '''    check("Purchase orders: 'Signed in: alisha' inside the BACK bar; the bar once, '← BACK' once", P["status"] == 200 and P["signed_in_bar"] and P["bars"] == 1 and P["backs"] == 1, P)\n''',
                      '''    check("Purchase orders: 'Signed in: alisha' inside the BACK bar; the bar once, '← BACK' once", P["status"] == 200 and P["signed_in_bar"] and P["bars"] == 1 and P["backs"] == 1, P)\n'''
                      '''    check("S454-ADJUSTED P8: the new Purchase-orders screen (S454): 'Signed in: alisha' on its home, '← BACK' once", '''
                      '''N["porders_new"]["status"] == 200 and N["porders_new"]["signed"] and N["porders_new"]["backs"] == 1, N["porders_new"])\n''')],
}
for _k, _v in P1ADJ.items():                                   # part 1's ADJ on both runs now
    BOTH.setdefault(_k, []).extend(_v)
LEG = "S454 part 2 (7.1): /finance/purchase/page/scans is the month's register; the old tables -- every line this walk reads there -- stay at ?legacy=1"
P2ADJ = {                       # name -> [(code, why, old, new)] -- part 2's own (on the box now: BOTH runs)
    "walk_s403.py": [("Q1", LEG, '''out["scans_red"] = "Unscanned 3 days after arrival" in G("manoj", "/finance/purchase/page/scans")[1]''',
                      '''out["scans_red"] = "Unscanned 3 days after arrival" in G("manoj", "/finance/purchase/page/scans?legacy=1")[1]   # S454-ADJUSTED Q1''')],
    "walk_s439.py": [("Q2", LEG + " (the pass still runs at the page's opening)", '''pg = G("manoj", "/finance/purchase/page/scans")               # the owner opens''',
                      '''pg = G("manoj", "/finance/purchase/page/scans?legacy=1")      # S454-ADJUSTED Q2 -- the owner opens''')],
    "walk_s440.py": [("Q3", LEG, '''pg = FG("manoj", "/finance/purchase/page/scans")\nm = re.search(r"what the staff see''',
                      '''pg = FG("manoj", "/finance/purchase/page/scans?legacy=1")   # S454-ADJUSTED Q3\nm = re.search(r"what the staff see'''),
                     ("Q3", "(the same)", '''pg = FG("manoj", "/finance/purchase/page/scans")\nout["scans_page"]''',
                      '''pg = FG("manoj", "/finance/purchase/page/scans?legacy=1")   # S454-ADJUSTED Q3\nout["scans_page"]'''),
                     ("Q3", "(the same)", '''pf = FG("manoj", "/finance/purchase/page/scans?from=/finance/approvals"); pe = FG("manoj", "/finance/purchase/page/scans?from=//evil.example/x")''',
                      '''pf = FG("manoj", "/finance/purchase/page/scans?legacy=1&from=/finance/approvals"); pe = FG("manoj", "/finance/purchase/page/scans?legacy=1&from=//evil.example/x")   # S454-ADJUSTED Q3'''),
                     ("Q3", "(the same)", '''int((re.search(r"\\((\\d+) to act on\\)", FG("manoj", "/finance/purchase/page/scans")[1]) or [0, -1])[1])]''',
                      '''int((re.search(r"\\((\\d+) to act on\\)", FG("manoj", "/finance/purchase/page/scans?legacy=1")[1]) or [0, -1])[1])]   # S454-ADJUSTED Q3''')],
    "walk_s446.py": [("Q4", LEG + " (S446's Sarvam card is there; the register's own foot carries the counter by the rules)",
                      '''out["s_scans_page"] = "id=\\"s446sarvam\\"" in FG("manoj", "/finance/purchase/page/scans")[1]''',
                      '''out["s_scans_page"] = "id=\\"s446sarvam\\"" in FG("manoj", "/finance/purchase/page/scans?legacy=1")[1]   # S454-ADJUSTED Q4''')],
    "walk_s452.py": [("Q5", LEG + " (Amir's list line: N to enter, M held)", '''    hs = FG("manoj", "/finance/purchase/page/scans")[1]''',
                      '''    hs = FG("manoj", "/finance/purchase/page/scans?legacy=1")[1]   # S454-ADJUSTED Q5''')],
}
for _k, _v in P2ADJ.items():                                   # part 2's ADJ on both runs now
    BOTH.setdefault(_k, []).extend(_v)
ADJ = {}                        # name -> [(code, why, old, new)] -- P3B's own, the patched run only (none: part 3 had none either)
PRE["walk_s452.py"] = [("Q6", "S454 part 2 (6): on purchase.entry_mode = paper Amir's step 2 reads 'Scan ho chuke bill (N)'; the brief: 'On both: S452's walk "
                              "passes' -- the patched run's copy reads both",
                        "INSERT INTO setting (key, value, note) VALUES ('purchase.entry_mode', 'both', 'S454 walk: S452 on both') ON CONFLICT(key) DO UPDATE SET value='both'")]
AUTO = ("S454 part 2 (5, the auto-link): a scan whose supplier agrees and whose amount is within Rs 1 of the ONLY unscanned bill of that supplier is "
        "paired with no card -- this walk's crafted near-match is paired by itself, so the question and the answers about it no longer arise")
RULE = ("S454 part 2 (5): the same scan and bill pair, now made by the rule 'verified (S454 5)' (number + total + supplier or date) -- its grade / rule "
        "words changed, never the pair")
AMT = ("S454 part 2 (5): a scan whose total differs from Marg's is no longer paired by the matcher (S439's vendor + bill-tail rule did): it is asked "
       "'is this the bill?' and becomes 'Amount differs' only after reception's Haan; the amount question asks beyond Rs 10 (purchase.total_noise_rs), not 2%")
P2_INTENDED = {                 # part 2's intended reds -- on the box now: red on BOTH runs, accepted as such (ACCEPT_WHY)
    "walk_s439.py": [("I1", "'A0439166'", r"verified \(S454 5\)", RULE), ("I1", "'GPPL-26-43964906'", r"verified \(S454 5\)", RULE),
                     ("I1", "'NOT043915521'", r"verified \(S454 5\)", RULE), ("I1", "'SF 004393051'", r"verified \(S454 5\)", RULE),
                     ("I1", "'A04397234'", r"verified \(S454 5\)", RULE), ("I1", "'G-4394430'", r"verified \(S454 5\)", RULE),
                     ("I1", "'T004395620' under a letterhead", r"verified \(S454 5\)", RULE), ("I1", "'A000439601' with the BUYER", r"verified \(S454 5\)", RULE),
                     ("I1", "'43918112 (NOT04315878)' links by its LAST digit run", r"verified \(S454 5\)", RULE),
                     ("I1", "the first, exact scan of bill 439175", r"verified \(S454 5\)", RULE),
                     ("I1", "every one of the 13 links written is audited", r"verified \(S454 5\)", RULE),
                     ("I1", "the scan made before Marg had its bill waits", r"verified \(S454 5\)", RULE),
                     ("I1", "the misspelt vendor linked (bills 439166 and 439182)", r"S439 learned from scan", RULE + " (the spelling is still learned once)"),
                     ("I2", "the licence number read as the bill number", r"auto_link \(S454 5\)", "S454 part 2 (5): a licence-shaped reading is never the bill "
                                                                                                   "number; the pair is made by the auto-link, not S439's date rule"),
                     ("I2", "a fifth, beside the brief's four: bill number differs", None, AUTO),
                     ("I2", "the page (200) carries the two new columns and the reason of each of the six open W439 scans",
                      r"^(?!.*'s12').*\[\(\[True, True\], \{'s13b': True, 's15': True, 'w_nobill': True, 'w_vendor': True, 'w_amount': True, 'w_digits': True",
                      AUTO + " (its scan s12 is paired with bill 439634, so it is no longer open and its reason is not on the page; the five other reasons are)"),
                     ("I2", "the 'Marg bills with no scan' list names the open scan beside bill 439189 and bill 439634", r"\[\[True, False\]\]",
                      AUTO + " (bill 439634 has its scan s12 now, so it is not on the list; bill 439189's hint is)"),
                     ("I3", "vendor misspelt AND the amount misread", r"\[\[None, None, None\]\]", AMT)],
    "walk_s440.py": [("I4", "a login of the unit that is not a sender may READ", r"auto_link \(S454 5\)", AUTO),
                     ("I4", "Haan, yahi hai: linked, grade CONFIRMED", r"auto_link \(S454 5\)", AUTO),
                     ("I4", "Nahi: not linked; the refusal is kept", r"auto_link \(S454 5\)", AUTO),
                     ("I4", "Haan on the scan whose bill already has a scan", r"verified \(S454 5\)", RULE),
                     ("I4", "'Yeh supplier hai' on the unreadable", r"auto_link \(S454 5\)", AUTO),
                     ("I4", "the OTHER scan with the same misspelling links too", r"auto_link \(S454 5\)", AUTO),
                     ("I4", "the scan that read the BUYER's own name as the vendor", r"auto_link \(S454 5\)", AUTO),
                     ("I4", "after two more passes", r"auto_link \(S454 5\)", AUTO),
                     ("I4", "'the line already gone'", r"verified \(S454 5\)", RULE),
                     ("I4", "2 Yahi bill hai?: the three scans", None, AUTO + " (and the amount-off pairs of group 4 are asked here now)"),
                     ("I4", "the line shows the scan's reading and Marg's bill side by side", None, AUTO),
                     ("I4", "after the three answers", None, AUTO),
                     ("I4", "reception's state (200) carries 'kaam'", None, AUTO + "; the groups' counts follow"),
                     ("I4", "the count on the section is groups 1-4", None, AUTO + "; the groups' counts follow"),
                     ("I4", "the five groups are the same after those passes", None, AUTO + "; the groups' counts follow"),
                     ("I4", "the read door (/finance/porders/api/scan-status", None, AUTO + "; a paired scan reads 'linked'"),
                     ("I4", "the status column's four words", None, AUTO + "; a paired scan reads 'Marg se mil gaya'"),
                     ("I4", "the count agrees everywhere", None, AUTO + "; the groups' counts follow"),
                     ("I4", "at the end the three counts still agree", None, AUTO + "; the groups' counts follow"),
                     ("I4", "the owner's Scan links page shows the five groups ONCE", r"\[\[1, False\]\]",
                      AUTO + "; and " + AMT[len("S454 part 2 (5): "):] + " -- the groups are shown once, as before; the walk's three crafted scans are no longer in them"),
                     ("I5", "4 Amount milao: the three linked scans", None, AMT),
                     ("I5", "paper = Marg -> Scan galat padha", None, AMT),
                     ("I5", "paper = the scan -> Marg galat", None, AMT),
                     ("I5", "paper = neither -> Dr sahab ko dikhao", None, AMT)],
    "walk_s452.py": [("I6", "a near-match scan (W452-01) is held back", r"Yeh bill Marg mein aa chuka hai", AUTO),
                     ("I6", "reception answers 'Nahi' (Yahi bill hai?)", r"\[\[409, False\]\]", AUTO)],
}
INTENDED = {}                   # name -> [(code, label prefix, regex or None, why)] -- P3B's own
ACCEPT_WHY = {                 # a patched red is accepted only when it is red, word for word, on the box as it is too -- and its walk is named here
    "walk_s403.py": "the walk's own control (the box before S403) is gone: --old is the box as it is, so its NEGATIVE checks are red on both runs; the "
                    "rest are today's data and the kits since (S410's ordering day, S440's scan flow, S441's reception login)",
    "walk_s407.py": "S452 (F-687) moved the setup page to the owner and a checker and renewed the key; the 18 live August NEFT messages queued since 26-Sep "
                    "answer the queue door first; the control (the box before S407) is gone",
    "walk_s410.py": "today's data (the Sarvam trial's owner line; September's real first-ever items carry no manufacturer in the item master); the "
                    "control (the box before S410) is gone",
    "walk_s414.py": "the control (the box before S414) is gone",
    "walk_s417.py": "the control (the box before S417) is gone; the card statements are read and placed on the live shelf since 26-Sep",
    "walk_s428.py": "today's data (the S427 ground moved with the first count's vouchers, a real arrival in the roster's window, October's leakage); the "
                    "control (the box before S428) is gone",
    "walk_s439.py": "the kits since S439 (S440's approve(), the matcher's own S440 decisions); the control (the box before S439) is gone",
    "walk_s440.py": "today's data (the real scans of 02/03-Oct in the groups; the intake's month line); the control (the box before S440) is gone",
    "walk_s441.py": "today's data (the real scans since 01-Oct in the S440 groups); the control (the box before S441) is gone",
    "walk_s444.py": "the kits since S444 (S446's stages, S452's Roman Hindi and 12 vouchers a visit, the claim settled by S444's own rule); the control "
                    "(the box before S444) is gone",
    "walk_s446.py": "S452's rulings (12 vouchers a visit, held scans, Amir's NEFT) and today's real scans; the control (the box before S446) is gone",
    "walk_s452.py": "today's real scans (B-0103..B-0113 of 03-Oct) on the list; the control (the box before S452) is gone",
}


def _lab(x):
    """A red's words with today's figures blanked: the label before its '   [' value, digits as '#'."""
    return re.sub(r"\d+", "#", x.split("   [")[0]).strip()


def adjust(name, src, patched):
    for code, _why, old, new in BOTH.get(name, []):
        n = src.count(old)
        if n != 1:
            raise SystemExit("STOP: %s -- adjustment %s anchor occurs %d times" % (name, code, n))
        src = src.replace(old, new, 1)
    if patched:
        for code, _why, old, new in ADJ.get(name, []):
            n = src.count(old)
            if n != 1:
                raise SystemExit("STOP: %s -- adjustment %s anchor occurs %d times" % (name, code, n))
            src = src.replace(old, new, 1)
    return src


def fails(out):
    return [l.strip()[5:].strip() for l in out.splitlines() if re.match(r"^\s*FAIL\s", l)]


def main():
    plan = json.load(open(sys.argv[sys.argv.index("--plan") + 1], encoding="utf-8"))
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    red = []
    print("-- the adjustments (each made on a scratch COPY or on that run's own scratch database; the kit folders are never edited):")
    print("   P0   every walk but S444  porders.simple = 0 on the patched run's scratch copy: the earlier walks read the old page (the brief, 4.9); S444's "
          "staff-eye walk reads the duty map v4, whose doors are the new screen's")
    print("   P2   every walk     the S454 tables made on the patched run's scratch copy, as the install's first load leaves them (the duty map v4 reads them)")
    for name, items in PRE.items():
        for code, why, _sql in items:
            print("   %-4s %-14s %s" % (code, name, why))
    for name, items in list(BOTH.items()) + list(ADJ.items()):
        for code, why, _o, _n in items:
            print("   %-4s %-14s %s" % (code, name, why))
    for w in plan:
        if only and w["name"] not in only:
            continue
        name = os.path.basename(w["src"])
        src = open(w["src"], encoding="utf-8").read()
        res = {}
        for side in ("baseline", "patched"):
            d = os.path.join(w["work"], side)
            os.makedirs(d, exist_ok=True)
            for extra in w.get("beside") or []:
                bs = open(extra, encoding="utf-8").read()
                with open(os.path.join(d, os.path.basename(extra)), "w", encoding="utf-8") as gh:
                    gh.write(adjust(os.path.basename(extra), bs, False))
            if True:                                         # S454 part 3: the box carries parts 1 and 2 -- P0 / P2 / PRE on both runs
                c = sqlite3.connect(w["db"][side])
                c.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
                if name not in NO_P0:
                    c.execute(PRE_SQL)
                for _code, _why, sql in PRE.get(name, []):
                    c.execute(sql)
                c.commit()
                c.close()
                q2 = subprocess.run([w.get("py") or sys.executable, "-B", "-c", P2_PY, w["fin"][side], w["db"][side]], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, timeout=300)
                if "S454 tables made" not in q2.stdout:
                    raise SystemExit("STOP: P2 failed on %s: %s" % (name, q2.stdout[-300:]))
            f = os.path.join(d, name)
            open(f, "w", encoding="utf-8").write(adjust(name, src, side == "patched"))
            env = dict(os.environ, **w["env"][side])
            for k in ("ORDER_TICK", "ORDER_TODAY", "SARVAM_API_KEY"):
                env.pop(k, None)
            p = subprocess.run([w.get("py") or sys.executable, "-B", f] + w["args"][side], cwd=d, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, timeout=3600)
            tally = [l for l in p.stdout.splitlines() if re.match(r"^WALK(_\w+)? (GREEN|RED|OK)", l)]
            res[side] = dict(fails=fails(p.stdout), tally=(tally[-1] if tally else "NO TALLY (exit %s)" % p.returncode), tail=p.stdout.splitlines()[-15:])
            print("   %-9s %-15s %s" % (side, name, res[side]["tally"][:200]))
            for x in res[side]["fails"]:
                print("               red: %s" % re.sub(r"\d{10,}", "##########", x)[:700])
        why = ACCEPT_WHY.get(name)
        bad, intended = [], []
        base_labels = {_lab(b) for b in res["baseline"]["fails"]}
        for x in res["patched"]["fails"]:
            if why and _lab(x) in base_labels:                # red on the box as it is too, word for word (today's figures blanked)
                continue
            hit = next((c for c in INTENDED.get(name, []) if x.startswith(c[1]) and (c[2] is None or re.search(c[2], x))), None)
            if hit:
                intended.append((hit[0], x, hit[3]))
                continue
            bad.append(x)
        for code, x, w_ in intended:
            print("   %-4s %s: intended -- %s -- %s" % (code, name, re.sub(r"\d{10,}", "##########", x.split("   [")[0])[:150], w_))
        if "NO TALLY" in res["patched"]["tally"]:
            bad.append(res["patched"]["tally"])
            print("\n".join("      " + re.sub(r"\d{10,}", "##########", l) for l in res["patched"]["tail"]))
        if bad:
            red.append(name)
            print("   !! %s: red on the patched files beyond the accepted and the intended:" % name)
            for b in bad:
                print("      !! %s" % re.sub(r"\d{10,}", "##########", b)[:600])
        elif res["patched"]["fails"]:
            print("   %s: %d red(s): %d red word for word on the box as it is too (%s); %d intended (named above)"
                  % (name, len(res["patched"]["fails"]), len(res["patched"]["fails"]) - len(intended), why, len(intended)))
    if red:
        print("WALKS_OLD_S454P3B RED -- %s" % ", ".join(red))
        return 1
    print("WALKS_OLD_S454P3B GREEN -- S403's, S407's, S410's, S414's, S417's, S428's, S439's, S440's, S441's, S444's, S446's and S452's walks: green on the "
          "patched files but for the named reds: each red on the box as it is too, or one the brief's part 3 rules make (named)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
