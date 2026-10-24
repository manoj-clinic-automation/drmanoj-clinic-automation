#!/usr/bin/python3
"""make_s641.py -- kit S641_DAY_CHECK_TILES: counted edits on the REAL bytes (F-472) of
    /root/finance/day_check.py 332bc8d4 (S640, live), /root/finance/clinic_money.py 7152cd3a, /root/finance/aaj_seed.py ab6e4b14
    (S640, live), /root/finance/owner_console.py 32780bcb (S636, live), /root/portal/portal.py d6202952.
python make_s641.py <dir holding the five files> <out_dir>. Every anchor must occur exactly once or nothing is written."""
import hashlib, os, sys

FROM = {"day_check.py": "332bc8d42d51cc3b829de29e71b510ef", "clinic_money.py": "7152cd3a7d3dcae6da2a9aee893064e7",
        "aaj_seed.py": "ab6e4b14f83e665400efe91e2f3050e1", "owner_console.py": "32780bcbf4c2a0877df819519cb1334a",
        "portal.py": "d6202952f80fdb8c831463be884ead36"}

CM = [
 # 1 -- the counter-vs-Docterz total is no longer a flag to explain in words: the day check names it, patient by patient
 ('''        if abs(diff1) < SMALL_P:
            notes.append(text + " Under ₹100 — noted, not flagged.")
        else:
            flag("total:%d" % diff1, "total_diff", diff1, text)
''', '''        if abs(diff1) < SMALL_P:
            notes.append(text + " Under ₹100 — noted, not flagged.")
        elif _s641_day_check():                         # S641 (the owner, 24-Oct): the day check names it, patient by patient
            res["handed_p"] = diff1
            notes.append("The counter sheet has ₹%s %s than Docterz — explained patient by patient on the day check: "
                         "/finance/clinic/check/%s" % (_r(abs(diff1)), more, d))
        else:
            flag("total:%d" % diff1, "total_diff", diff1, text)
'''),
 # 2 -- no more "almost certainly <patient>'s" guesses for bank money rung as cash (the day check names the right patient)
 ('''                whose = next((c for c in doc["cash_entries"] if c["amount_p"] == b["amount_p"]), None)
                expl("rung_as_cash", b["amount_p"], "The ₹%s at %s in the bank is almost certainly %s's ₹%s — paid by UPI, "
                     "written down as cash. No money is missing; the drawer will be short by the same."
                     % (_r(b["amount_p"]), b.get("txn_time") or "—", (whose or {}).get("patient") or "a cash entry", _r(b["amount_p"])))
''', '''                if not _s641_day_check():                    # S641: the day check names the patient; no guess here
                    whose = next((c for c in doc["cash_entries"] if c["amount_p"] == b["amount_p"]), None)
                    expl("rung_as_cash", b["amount_p"], "The ₹%s at %s in the bank is almost certainly %s's ₹%s — paid by UPI, "
                         "written down as cash. No money is missing; the drawer will be short by the same."
                         % (_r(b["amount_p"]), b.get("txn_time") or "—", (whose or {}).get("patient") or "a cash entry", _r(b["amount_p"])))
'''),
 # 3 -- the verdict never says "agree" while the totals differ
 ('''    dayword = dt.date.fromisoformat(d).strftime("%A %d-%b")
    if not flags:
        res["verdict"] = "nothing_to_do"
''', '''    dayword = dt.date.fromisoformat(d).strftime("%A %d-%b")
    if not flags and res.get("handed_p"):                # S641: only the counter-vs-Docterz difference, and the day check has it
        res["verdict"] = "day_check"
        res["lines"] = ["%s: the counter sheet has ₹%s %s than Docterz — see the day check, patient by patient. Nothing else to do here."
                        % (dayword, _r(abs(res["handed_p"])), "more" if res["handed_p"] > 0 else "less")]
    elif not flags:
        res["verdict"] = "nothing_to_do"
'''),
 # 3b -- with other flags too, the line says where the counter-vs-Docterz difference went
 ("""            res["lines"] = ["%s: %d thing%s need%s a person. Everything else matches or is explained." % (dayword, n, "s" if n > 1 else "", "" if n > 1 else "s")]
    return res
""", """            res["lines"] = ["%s: %d thing%s need%s a person. Everything else matches or is explained." % (dayword, n, "s" if n > 1 else "", "" if n > 1 else "s")]
    if res.get("handed_p") and res["verdict"] == "flags":           # S641
        res["lines"][0] += " The counter sheet's ₹%s difference with Docterz is on the day check, patient by patient." % _r(abs(res["handed_p"]))
    return res
"""),
 # 4 -- the bank part, as Morning match shows it, for the day check page; and the switch that hands the total over
 ('''# ---------------------------------------------------------------- flags that persist
def sync_flags(con, d, m):''', '''def _s641_day_check():
    """S641: True when day_check.py is beside this file (it then names the counter-vs-Docterz difference itself)."""
    try:
        import day_check                         # noqa: F401,PLC0415
        return True
    except Exception:                            # noqa: BLE001
        return False


BANK_CODES = ("not_in_bank", "bank_extra", "mpr_missing", "mpr_rejected", "sms_diff", "pos_diff")


def bank_part(con, d, u=None):
    """S641 (the owner, 24-Oct: "all can see the bank arrival part as it was existing"): Morning match's bank words for one
    day, for the day check page -- the bank line, the money still on its way, and the bank's flags. Pure read."""
    m = match_day(con, d)
    if not m.get("p1"):
        return None
    waiting = [n for n in m["notes"] if "not in the bank yet" in n]
    if m["bank_known"] and not m.get("expected_bank_p") and not m["bank_p"]:
        line = "No online payments this day."
    elif m["bank_known"]:
        oo = m["p4"]["ours_only"]
        line = "Bank: ₹%s received of ₹%s online%s." % (_r(m["bank_p"]), _r(m.get("expected_bank_p")),
                                                        ("; ₹%s still on its way (%d payment%s)" % (_r(sum(o["amount_p"] for o in oo)), len(oo),
                                                                                                   "s" if len(oo) != 1 else "")) if oo else "")
        line += _sms_after_mpr(con, d, u or {})
    elif m.get("standin") and m["standin"].get("source") == "sms":
        line = "Bank SMS %s: ₹%s credited — the bank's MPR mail has not come yet; this figure stands until it does." % (
            m["standin"].get("sms_at") or "", _r(m["standin"]["amount_p"]))
    elif m.get("standin"):
        line = "Bank: %s. POS total ₹%s stands in for the bank's statement; Docterz expects ₹%s online." % (
            m["standin"]["label"], _r(m["standin"]["amount_p"]), _r(m.get("expected_bank_p")))
    else:
        _sp = _sms_early_p(con, d)
        line = (("Bank SMS this morning: ₹%s credited to the clinic account — the early figure; the bank file (MPR) has not "
                 "arrived yet, so the match waits for it." % _r(_sp)) if _sp is not None else
                "Bank: the file for this day has not arrived yet (%s)." % m["bank_state"].replace("_", " "))
    flags = [f for f in m["flags"] if f["code"] in BANK_CODES]
    return dict(line=line, waiting=waiting, flags=flags)


# ---------------------------------------------------------------- flags that persist
def sync_flags(con, d, m):'''),
]

DC = [
 # 1 -- the bank part under the cards, for everyone who opens the day
 ('''    for en, hi in chk.get("notes", []):
        out.append("<p class='mut'>%s</p>" % _esc(en if english else hi))''', '''    out.append(_bank_html(con, d, u, english))           # S641: the bank part, as Morning match shows it
    for en, hi in chk.get("notes", []):
        out.append("<p class='mut'>%s</p>" % _esc(en if english else hi))'''),
 ('''def _btn(d, key, act, label, cls="", extra=""):''', '''def _bank_html(con, d, u, english):
    """S641: Morning match's bank words for the day (clinic_money.bank_part), the same for staff and the owner. Its flags are
    answered where they always were -- on Morning match."""
    try:
        import clinic_money                              # noqa: PLC0415
        b = clinic_money.bank_part(con, d, u)
    except Exception:                                    # noqa: BLE001
        return ""
    if not b:
        return ""
    out = ["<h3 class='grp'>%s</h3><p>%s</p>" % ("Bank" if english else "Bank", _esc(b["line"]))]
    for f in b["flags"]:
        out.append("<div class='cline'><span class='ct'>%s</span><span class='cb'><a class='tb x' href='/finance/clinic/match/%s'>%s</a></span></div>"
                   % (_esc(f["text"]), d, "Answer on Morning match" if english else "Morning match par jawab"))
    if b["waiting"]:
        out.append("<details><summary class='mut'>%s (%d)</summary><ul>%s</ul><p class='mut'>%s</p></details>" % (
            "Waiting for the bank" if english else "Bank ka intezaar", len(b["waiting"]),
            "".join("<li class='mut'>%s</li>" % _esc(n) for n in b["waiting"]),
            "Money still on its way is not a flag; it becomes one only if it has not arrived after two banking days."))
    return "".join(out)


def _btn(d, key, act, label, cls="", extra=""):'''),
 # 2 -- the tile's door: the owner lands on the oldest day of the week that still has lines
 ('''    s = staff_lines(con, u)
    d = s["days"][-1] if s["days"] else (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return redirect("/finance/clinic/check/%s#check" % d, code=302)''', '''    s = staff_lines(con, u)
    days = s["days"]
    if not days and english:                             # S641: his tile -- every kind of line, the last STAFF_DAYS days
        for i in range(1, STAFF_DAYS + 1):
            dd = (dt.date.today() - dt.timedelta(days=i)).isoformat()
            ck = check_day(con, dd)
            if ck.get("state") == "checked" and ck["cards"]:
                days.append(dd)
    d = days[-1] if days else (dt.date.today() - dt.timedelta(days=1)).isoformat()
    return redirect("/finance/clinic/check/%s#check" % d, code=302)'''),
]

SEED = [
 ('''            {'id': 'rec.match',
             'hi': 'Morning match: kal ka hisaab milaiye, har flag ki wajah likhiye',
             'en': 'Morning match for yesterday, with a reason on each flag.',
             'when': 'day',
             'on': True,''', '''            {'id': 'rec.match',
             'hi': 'Morning match: kal ka hisaab milaiye, har flag ki wajah likhiye',
             'en': 'Morning match for yesterday, with a reason on each flag.',
             'when': 'day',
             'on': False,                                # S641 (the owner, 24-Oct): Din ki galtiyan does this job now; the page stays''')]

OC = [
 ('''        word, dot = {"nothing_to_do": ("matched", "g"), "flags":''', '''        word, dot = {"nothing_to_do": ("matched", "g"), "day_check": ("see the day check", "w"), "flags":''')]

PO = [
 ('''    {"icon": "\\u2705", "name": "Morning match",''', '''    {"icon": "\\U0001F50E", "name": "Day check",
     # S641 NEW (owner, 24-Oct-2026, D776). The day's corrections -- parchi x Docterz x register x bank, patient by
     # patient, with the bank part -- opening the oldest day of the week that still has lines. Every button is his too.
     "desc": "The day's corrections \\u00b7 bank",
     "live": True,
     "url": "/finance/clinic/check/mine",
     "roles": ["doctor"]},
    {"icon": "\\U0001F4CB", "name": "Parchi desk",
     # S641 NEW (owner, 24-Oct-2026, D775). OPD, X-ray/Proc and Blood test on one page -- for his chamber when staff are away.
     "desc": "OPD \\u00b7 X-ray/Proc \\u00b7 Blood \\u2014 one page",
     "live": True,
     "url": "/finance/slips/desk",
     "roles": ["doctor"]},
    {"icon": "\\u2705", "name": "Morning match",'''),
 ('''    "Morning match": "Docterz & clinic day", "Physiotherapy": "Docterz & clinic day",''',
  '''    "Morning match": "Docterz & clinic day", "Physiotherapy": "Docterz & clinic day",
    "Day check": "Docterz & clinic day", "Parchi desk": "Patients",                     # S641'''),
]

PLAN = (("clinic_money.py", CM), ("day_check.py", DC), ("aaj_seed.py", SEED), ("owner_console.py", OC), ("portal.py", PO))


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    built = {}
    for name, edits in PLAN:
        p = os.path.join(src, name)
        h = hashlib.md5(open(p, "rb").read()).hexdigest()
        if h != FROM[name]:
            sys.exit("STOP: %s is %s, not %s" % (p, h[:8], FROM[name][:8]))
        s = open(p, encoding="utf-8", newline="").read()
        for i, (a, b) in enumerate(edits, 1):
            n = s.count(a)
            if n != 1:
                sys.exit("STOP: %s edit %d anchor found %d times" % (name, i, n))
            s = s.replace(a, b)
        built[name] = s
    for name, s in built.items():
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as fh:
            fh.write(s)
        print("%s: %d counted edit(s) -> %s" % (name, len(dict(PLAN)[name]), hashlib.md5(s.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    main()
