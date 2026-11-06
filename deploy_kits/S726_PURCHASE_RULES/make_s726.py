#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_s726.py -- S726_PURCHASE_RULES (Sanjeevni session 393, 06-Nov-2026; D839, D840, F-1140 - F-1143).

Builds the three changed files from the live bytes by anchored edits: every anchor must stand EXACTLY ONCE and every FROM pin must be
exact, else REFUSED and nothing is written.

    python3 -B make_s726.py <dir holding the FROM files> <out dir>

The dir must hold all three: scan_register.py, purchase_app.py, porders.py (/root/finance).
"""
import hashlib
import os
import sys

FROM = {
    "scan_register.py": "904f07b1c7c6ce2291632586b7ddf279",   # /root/finance (S454 part 2)
    "purchase_app.py": "2e1e9023d7cd2887fefee3aa80276a93",    # /root/finance (the newest bundle)
    "porders.py": "8326dfc53a668689e7098bfdcb7ddfc0",         # /root/finance (S441 / S454 / S662)
}

# ---------------------------------------------------------------------------------------------------------------- scan_register.py
E_SR = [
# 1 -- the header: the total and the auto-link as S726 reads them
('''#    total     -- within Rs 1 is equal; up to purchase.total_noise_rs (10) agrees, with the difference shown; more differs. A paper
#                 amount reception typed stands in for the scan's reading.
''',
'''#    total     -- within Rs 1 is equal, and a non-zero rupee is SHOWN ("Paper Rs 7,979 · Rs 1 rounding -- supplier's figure paid"); more
#                 differs (S726, F-1140: for a COUNTED month the Rs 1-10 noise band no longer passes a total -- every such rupee is corrected
#                 in Marg by Amir; a parked or hidden month keeps purchase.total_noise_rs, so September raises nothing new -- band_p()).
#                 A paper amount reception typed stands in for the scan's reading.
''', 1),
('''#  The auto-link: a scan whose supplier agrees and whose amount is within Rs 1 of EXACTLY ONE unscanned bill of that supplier (dated from
#  porders.scan_from, within 60 days of the scan, not refused for it) is paired with no card (audit auto_link).
''',
'''#  The auto-link: a scan whose supplier agrees and whose amount is within Rs 1 of EXACTLY ONE unscanned bill of that supplier (dated from
#  porders.scan_from, within 60 days of the scan, not refused for it) is paired with no card (audit auto_link) -- S726 (F-1141, D839) only
#  when ALSO: the paper's date (no date read: the scan day) is in the bill's calendar month; NO other bill of that supplier (scanned or
#  not, any state) within the 60 days carries an amount within Rs 1; and neither the read bill number nor the read date differs.
#  Otherwise the pair is reception's one-tap "is this the same bill?" (purchase_app's _why: the bill becomes the scan's likely bill).
#  S726 also adds two states of a paired bill, neither settled: Second look (F-1142: an answer -- a paper amount typed -- contradicts
#  what the scan itself read by more than Rs 1; You & Shavez) and Paired, nothing read (F-1143: the scan read neither a total nor a
#  bill number; reception rescans). In a parked month both are shown with whose line "Nobody (<month> is parked)": nobody is asked.
#  The owner's step view (D840) is check_body(), served at /finance/purchase/page/check.
''', 1),
# 2 -- the states
('''STATES = ("verified", "has_scan", "amount_differs", "no_scan", "double", "accepted")
STATE_EN = {"verified": "Verified", "has_scan": "Has its scan", "amount_differs": "Amount differs", "no_scan": "No scan",
            "double": "Entered twice in Marg", "accepted": "Accepted without paper"}
''',
'''STATES = ("verified", "has_scan", "amount_differs", "no_scan", "double", "accepted", "second_look", "unread_pair")    # S726 adds the last two
STATE_EN = {"verified": "Verified", "has_scan": "Has its scan", "amount_differs": "Amount differs", "no_scan": "No scan",
            "double": "Entered twice in Marg", "accepted": "Accepted without paper", "second_look": "Second look",
            "unread_pair": "Paired, nothing read"}
KIT_S726 = "S726_PURCHASE_RULES"
''', 1),
# 3 -- rs2: the paise shown when there are any (the new notes only)
('''def _date(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None
''',
'''def rs2(p):
    """S726: like rs(), with the paise shown when there are any ('₹4,762.50')."""
    if p is None:
        return "—"
    p = int(p)
    a = abs(p)
    v = rs(a - a % 100) + ((".%02d" % (a % 100)) if a % 100 else "")
    return ("−" + v) if p < 0 else v


def _date(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None
''', 1),
# 4 -- the band of a bill's month: Rs 1 for a counted month, the noise setting for a parked one
('''        self.noise = noise_p(con)
''',
'''        self.noise = noise_p(con)
        v726 = setting(con, "purchase.register_from", "2026-10-01")          # S726: the first counted month (as month_class reads it)
        self.first = v726[:7] if re.match(r"^\\d{4}-\\d\\d", v726) else "2026-10"
''', 1),
('''    tc, diff = total(tp, b["amount_p"], cx.noise)
''',
'''    tc, diff = total(tp, b["amount_p"], band_p(cx, b))              # S726 (F-1140): Rs 1 in a counted month
''', 1),
('''def verified(a):
''',
'''def band_p(cx, b):
    """S726 (F-1140): the total's band for this bill -- Rs 1 when its month is counted (every rupee beyond is corrected in Marg); a parked or
    hidden month (September) keeps purchase.total_noise_rs, as it was cleared."""
    ym = str(b.get("month") or str(b.get("bill_date") or "")[:7])
    return 100 if (not ym or ym >= getattr(cx, "first", "2026-10")) else cx.noise


def verified(a):
''', 1),
# 4c -- the S726 number test: Marg's number and the scan's reading written two ways
('''def date_md(scan_date, marg_date):
''',
'''def billno_compat(scan_no, marg_no):
    """S726: the scan's reading against Marg's number for the S726 tests only (billno() itself is unchanged; other code reads it) ->
    'agree' | 'close' | 'differ' | 'not_read'. All the digits of each, letters and separators dropped, leading zeros stripped:
    'agree' when equal, or when the shorter (4 digits or more) ends the longer (Marg truncates: 90058 <- RT-490058, 1692 <- A011692), or
    when the digit runs, each without its zeros, join to the same (YS0706202627 <- YS/0706/2026-27, the year kept here);
    'close' when the shorter (3 digits or more) and the same-length end of the longer differ in exactly ONE digit (an OCR misread:
    11086 <- A011986, 77627 <- GPPL/24-77527); else 'differ'. A licence-shaped reading is 'differ', as in billno()."""
    st = str(scan_no or "")
    if not re.search(r"\\d", st):
        return "not_read"
    if billno(scan_no, marg_no) == "agree":
        return "agree"                                             # never stricter than billno() (1692 <- 1692/26-27)
    if LICENCE_RE.search(st):
        return "differ"
    sd = re.sub(r"\\D", "", st).lstrip("0")
    md = re.sub(r"\\D", "", str(marg_no or "")).lstrip("0")
    if not sd or not md:
        return "differ"
    sr = "".join(x.lstrip("0") for x in re.findall(r"\\d+", st))
    mr = "".join(x.lstrip("0") for x in re.findall(r"\\d+", str(marg_no or "")))
    if sd == md or (sr and sr == mr) or sr == md or sd == mr:
        return "agree"
    short, long_ = sorted((sd, md), key=len)
    if len(short) >= 4 and long_.endswith(short):
        return "agree"
    if len(short) >= 3 and sum(1 for x, y in zip(short, long_[-len(short):]) if x != y) == 1:
        return "close"
    return "differ"


def date_md(scan_date, marg_date):
''', 1),
# 5 -- the two new states of a paired bill
('''def sarvam_flags(cx, s, b):
''',
'''def s726_state(cx, s, a, present=True):
    """S726: a paired bill's state -- pair_state(a), unless the scan read neither a total nor a bill number (unread_pair, F-1143) or an
    answer (a paper amount typed) contradicts what the scan itself read by more than Rs 1 (second_look, F-1142). `present`: the scan's
    own row was read (a scan missing from the asset app's list is never judged unread)."""
    st = pair_state(a)
    if not present:
        return st
    raw = s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount"))
    read_total = raw not in (None, 0)
    if not read_total and a["billno"] == "not_read":
        return "unread_pair"
    sid = int(s["id"]) if s.get("id") is not None else None
    if sid is not None and sid in cx.paper and read_total and abs(int(cx.paper[sid]) - int(raw)) > 100:
        return "second_look"
    return st


def sarvam_flags(cx, s, b):
''', 1),
# 6 -- the auto-link and its S726 conditions
('''def autolink_choice(cx, s, bills, taken, scan_from, refused=()):
    """The one unscanned bill this scan pairs with by itself, or None: its supplier agrees, its amount is within Rs 1 of EXACTLY ONE
    unscanned bill of that supplier dated from scan_from and within HINT_DAYS of the scan (paper date or scan day), not refused for it."""
    sp = scan_amount(cx, s)
    if sp is None or int(sp) == 0:
        return None
    sid = int(s["id"])
''',
'''def scan_month(s, bill_month=None):
    """S726: the month a scan belongs to -- the asset app's bill_month, else its paper date (when within 120 days of its scan day: a
    misread year is not a month), else its scan day (IST). '' when nothing is known."""
    bm = str(bill_month or s.get("bill_month") or "")
    if re.match(r"^\\d{4}-\\d\\d$", bm):
        return bm
    day = _date(_scan_day(s))
    pd = _date(s.get("bill_date"))
    if pd and (day is None or abs((pd - day).days) <= 120):
        return pd.isoformat()[:7]
    return day.isoformat()[:7] if day else ""


def autolink_ok(cx, s, b, bills, undo=False, before=None):
    """S726 (F-1141, D839): may this amount-only pair stand by itself? -> (True, '') or (False, the reason in plain English).
    The paper's date (no date read: the scan day) is in the bill's calendar month; no OTHER bill of that supplier (scanned or not, any
    state) within HINT_DAYS of the scan carries an amount within Rs 1 of the scan's; the read bill number and the read date do not differ.
    The number: 'differ' (billno_compat) always contradicts; 'close' (one digit off) does not take an existing link apart (undo=True) but
    is not enough for a NEW pair (reception is asked). before (the undo only): only bills dated on or before it count as 'another bill'."""
    a = agree(cx, s, b)
    bcmp = billno_compat(s.get("bill_no"), b["bill_no"])
    if bcmp == "differ" or (bcmp == "close" and not undo):      # S726: Marg's number written another way is not a contradiction
        return False, "the scan's bill number reads %s%s" % (str(s.get("bill_no") or "").strip()[:30] or "otherwise",
                                                             " (one digit off: a question, not a pair by itself)" if bcmp == "close" else "")
    if a["date"] == "differ":
        return False, "the scan's date reads %s" % (ddmon(s.get("bill_date")) or "otherwise")
    bd = _date(b.get("bill_date"))
    if a["date"] != "agree":
        day = _date(_scan_day(s))
        if bd is None or day is None or (day.year, day.month) != (bd.year, bd.month):
            return False, "no date read and it was scanned in another month (%s)" % (ddmon(day.isoformat()) if day else "unknown")
    sp = scan_amount(cx, s)
    if sp is None or int(sp) == 0:
        return False, "no amount read"
    sid = int(s["id"])
    days = [d for d in (_date(s.get("bill_date")), _date(str(s.get("created_at") or "")[:10])) if d]
    pa = _pa()
    bk = pa.supplier_key(b["supplier"])
    for x in bills:
        if x["id"] == b["id"] or abs(int(sp) - int(x["amount_p"] or 0)) > 100:
            continue
        xd = _date(x.get("bill_date"))
        if not xd or not days or min(abs((d - xd).days) for d in days) > HINT_DAYS:
            continue
        if before is not None and xd > before:
            continue                                               # the undo: a newer same-amount bill never takes a correct pair apart
        if pa.supplier_key(x["supplier"]) != bk and supplier(cx, s.get("vendor"), x["supplier"], cx.chosen.get(sid)) != "agree":
            continue
        return False, "another bill of this supplier carries this amount (%s of %s)" % (x["bill_no"], ddmon(x.get("bill_date")))
    return True, ""


def autolink_choice(cx, s, bills, taken, scan_from, refused=()):
    """The one unscanned bill this scan pairs with by itself, or None (S726: autolink_pick's first part -- the S726 conditions applied)."""
    return autolink_pick(cx, s, bills, taken, scan_from, refused)[0]


def autolink_pick(cx, s, bills, taken, scan_from, refused=()):
    """(bill, None, '') -- the one unscanned bill this scan pairs with by itself: its supplier agrees, its amount is within Rs 1 of EXACTLY
    ONE unscanned bill of that supplier dated from scan_from and within HINT_DAYS of the scan (paper date or scan day), not refused for it,
    AND autolink_ok (S726). (None, candidate, why) when S726 refuses that one candidate -- it becomes reception's question. (None, None, '')."""
    sp = scan_amount(cx, s)
    if sp is None or int(sp) == 0:
        return None, None, ""
    sid = int(s["id"])
''', 1),
('''        if supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(sid)) != "agree":
            continue
        out.append(b)
    return out[0] if len(out) == 1 else None
''',
'''        if supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(sid)) != "agree":
            continue
        out.append(b)
    if len(out) != 1:
        return None, None, ""
    ok, why = autolink_ok(cx, s, out[0], bills)
    return (out[0], None, "") if ok else (None, out[0], why)
''', 1),
# 7 -- the register: the two new states
('''            st = pair_state(a)
''',
'''            st = s726_state(cx, s, a, l["scan"] in scans)           # S726: second look (F-1142) / paired, nothing read (F-1143)
''', 1),
# 7a -- the parked bills an S726 undo freed ask nobody
('''def month_class(con, ym):
''',
'''def s726_quiet_bills(con):
    """S726: the bills of a month not counted (September) whose AUTO link S726 undid and that have no scan now -> {bill id}. Nobody is
    asked about them: September is parked and was cleared by the owner (the undo only freed a counted month's paper)."""
    try:
        ids = {int(r[0]) for r in con.execute("SELECT DISTINCT ref FROM purchase_audit WHERE action='auto_link_undone'") if str(r[0] or "").isdigit()}
        if not ids:
            return set()
        linked = {int(r[0]) for r in con.execute("SELECT bill_id FROM purchase_scan_link")}
        out = set()
        for bid in ids - linked:
            r = con.execute("SELECT month, bill_date FROM purchase_bill WHERE id=?", (bid,)).fetchone()
            ym = (r[0] or str(r[1] or "")[:7]) if r else ""
            if r and re.match(r"^\\d{4}-\\d\\d$", ym) and month_class(con, ym) != "counted":
                out.add(bid)
        return out
    except sqlite3.Error:
        return set()


def month_class(con, ym):
''', 1),
('''    t = today()
    rows, seen_double = [], set()
''',
'''    t = today()
    quiet726 = s726_quiet_bills(con) if cls != "counted" else set()
    rows, seen_double = [], set()
''', 1),
('''                row.update(state="no_scan", note=" ".join(bits), whose=whose, missing=bool(m))
''',
'''                row.update(state="no_scan", note=" ".join(bits), whose=whose, missing=bool(m))
                if b["id"] in quiet726:                            # S726: its amount-only pair was undone to free a counted paper
                    row.update(note="Its amount-only pair with a later month's paper was undone (S726).",
                               whose="Nobody (%s is parked)" % MONTHS[int(month[5:7]) - 1])
''', 1),
# 7b -- a parked month's new states ask nobody
('''            row["note"], row["whose"] = _note(cx, st, a, b, s, l)
''',
'''            row["note"], row["whose"] = _note(cx, st, a, b, s, l)
            if cls != "counted" and st in ("second_look", "unread_pair"):        # S726: a parked month raises nothing to a person
                row["whose"] = "Nobody (%s is parked)" % MONTHS[int(month[5:7]) - 1]
''', 1),
# 8 -- the notes
('''    bits = []
    how = l.get("grade") or ""
    if st == "amount_differs":
''',
'''    bits = []
    how = l.get("grade") or ""
    if st == "unread_pair":                                    # S726 (F-1143): nothing read is never settled
        return ("%s; the scan read neither a total nor a bill number, so nothing on it confirms this bill. Rescan the paper."
                % ("Paired by reception" if how == "CONFIRMED" else "Paired"), "Reception: rescan")
    if st == "second_look":                                    # S726 (F-1142): the answer and the scan disagree
        raw = s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount"))
        return ("The amount given for the paper is %s; the scan itself reads %s; Marg %s. The two readings of one paper disagree by more "
                "than ₹1 — a second look." % (rs2(a["scan_p"]), rs2(raw), rs2(b["amount_p"])), "You & Shavez")
    if st == "amount_differs":
''', 1),
('''    if a["total"] == "noise":
        bits.append("Paper %s, %s rounding." % (rs(a["scan_p"]), rs(abs(a["diff"]))))
''',
'''    if a["total"] in ("equal", "noise") and a.get("diff"):     # S726 (F-1140): a rounding rupee is shown, never silent
        bits.append("Paper %s · %s rounding — supplier's figure paid." % (rs2(a["scan_p"]), rs2(abs(a["diff"]))))
''', 1),
('''    elif how == "AUTO":
        lead = "Paired by itself: the only unscanned bill of this supplier with this amount"
''',
'''    elif how == "AUTO":
        lead = "Paired by itself: the only unscanned bill of this supplier with this amount"
    elif "S726" in (l.get("rule") or ""):
        lead = "Paired on bill number and date"
''', 1),
# 9 -- the register page: the two new states' colour and place
('''#s454reg .st.no_scan{color:#8c1d18}
''',
'''#s454reg .st.no_scan{color:#8c1d18}
#s454reg .st.second_look,#s454reg .st.unread_pair{color:#8c1d18}
''', 1),
('''    order = {"no_scan": 0, "amount_differs": 1, "double": 2, "has_scan": 3, "accepted": 4, "verified": 5}
''',
'''    order = {"no_scan": 0, "unread_pair": 0, "amount_differs": 1, "second_look": 1, "double": 2, "has_scan": 3, "accepted": 4, "verified": 5}
''', 1),
# 10 -- the owner's step view (D840)
('''def accept_nopaper(con, who, bill_id, accept):
''',
'''# ------------------------------------------------------------------ S726 (D840): the owner's step view -- read only, English, phone-first
CHECK_CSS = """
#s726chk{max-width:560px;margin:0 auto;font-size:17px;line-height:1.35;overflow-wrap:anywhere;word-break:break-word}
#s726chk h1{font-size:21px;margin:4px 0 10px}
#s726chk .strip{border-radius:10px;padding:10px 12px;font-weight:700;margin:0 0 10px}
#s726chk .strip.hold{background:#fff4e0;border:1px solid #e0b060;color:#7a4a00}
#s726chk .strip.clear{background:#e8f4ea;border:1px solid #8cc39a;color:#1f4d25}
#s726chk details{border-top:1px solid #e6e2dc}
#s726chk details.last{border-bottom:1px solid #e6e2dc}
#s726chk summary{display:flex;justify-content:space-between;align-items:center;gap:10px;min-height:48px;cursor:pointer;list-style:none}
#s726chk summary::-webkit-details-marker{display:none}
#s726chk summary .l{min-width:0}
#s726chk summary .n{font-weight:800;white-space:nowrap}
#s726chk .grey summary{color:#9a958e}
#s726chk ul{margin:0 0 10px 18px;padding:0;font-size:15px}
#s726chk li{margin:4px 0}
#s726chk .mut{color:#666;font-size:14px}
#s726chk .msel{margin:12px 0}
#s726chk select{min-height:40px;font-size:16px;max-width:100%}
"""


def check_month(con, months):
    """(month, its register or None): the oldest counted month (2026-10 on) not fully settled; else the newest counted month."""
    v = setting(con, "purchase.register_from", "2026-10-01")
    first = max(v[:7] if re.match(r"^\\d{4}-\\d\\d", v) else "2026-10", "2026-10")
    counted = sorted(m for m in months if re.match(r"^\\d{4}-\\d\\d$", m) and m >= first and month_class(con, m) == "counted")
    for m in counted:
        r = register(con, m)
        if r["settled"] < r["total"] or r["open_scans"]:
            return m, r
    if counted:
        return counted[-1], None
    return (months[0] if months else today().strftime("%Y-%m")), None


def _ck_line(x, tail):
    return "%s %s%s" % (esc(x["supplier"]), esc(x["bill_no"]), tail)


def check_rows(r, cx):
    """The seven rows of the step view as [(label, count text, [list lines as HTML], grey)] -- read only; the register's own states."""
    month_ids = {x["id"] for x in r["rows"]}
    rows = [x for x in r["rows"] if not str(x.get("whose") or "").startswith("Nobody (")]     # a parked month's new states ask nobody
    paired = [x for x in r["rows"] if x.get("scan") is not None]
    unpaired = [x for x in r["rows"] if x.get("scan") is None and x["state"] != "double"]
    l1 = [_ck_line(x, " · %s · %s" % (esc(rs(x["amount_p"])), esc(STATE_EN[x["state"]].lower()))) for x in unpaired]
    rec = []
    for x in rows:
        if x["state"] == "no_scan" and not x.get("missing"):
            rec.append(_ck_line(x, " · %s · %s" % (esc(rs(x["amount_p"])), "a question" if x.get("whose") == "Reception: a question" else "to scan")))
        elif x["state"] == "unread_pair":
            rec.append(_ck_line(x, " · scan %s · paired, nothing read: rescan" % esc(x["stamp"])))
    hinted = {sid for sid, bid in cx.likely.items() if bid in month_ids}
    for s in r["scans"]:
        if s["state"] in ("probably", "vendor", "to_name", "unread") and not (s["state"] == "probably" and s["id"] in hinted):
            rec.append("Scan %s · %s" % (esc(s["stamp"]), esc(SCAN_EN[s["state"]])))
    amir = []
    for x in rows:
        if x["state"] == "amount_differs":
            ag = x.get("agree") or {}
            d = ag.get("diff") or 0
            amir.append(_ck_line(x, " %s%s" % (esc(rs2(abs(d))), ' <span class="mut">· the %s reads %s · %s</span>'
                                               % ("paper" if ag.get("paper") else "scan", "more" if d > 0 else "less", esc(x.get("whose") or "")))))
        elif x["state"] == "double":
            amir.append(_ck_line(x, ' <span class="mut">· entered twice in Marg</span>'))
    rnd = []
    for x in rows:
        a = x.get("agree") or {}
        if x["state"] in ("verified", "has_scan") and a.get("diff") and abs(int(a["diff"])) <= 100:
            rnd.append(_ck_line(x, " · paper %s · %s" % (esc(rs2(a.get("scan_p"))), esc(rs2(abs(int(a["diff"])))))))
    you = []
    for x in rows:
        if x["state"] == "second_look":
            you.append(_ck_line(x, ' · second look <span class="mut">· %s</span>' % esc(x.get("note") or "")))
        elif x["state"] == "no_scan" and x.get("missing"):
            you.append(_ck_line(x, " · %s · paper not found" % esc(rs(x["amount_p"]))))
    return [("Scans paired", "%d / %d" % (len(paired), r["total"]), l1 or ["Every bill has its scan."], False),
            ("With reception", str(len(rec)), rec, False),
            ("Differences → Amir", str(len(amir)), amir, False),
            ("Rounding (supplier's figure paid)", str(len(rnd)), rnd, False),
            ("You & Shavez", str(len(you)), you, False),
            ("Supplier summaries", "later", ["Comes after rows 1–5."], True),
            ("Lock & NEFT", "after 1–6", ["Opens when rows 1–6 are clear."], True)]


def check_body(con, month, prefix, months, r=None):
    """S726 (D840): the owner's step view of one month -- a header, the NEFT strip, seven one-line rows (each opens its list), a month
    select. Reads only: register() and the scan state the last pass left."""
    r = r if r is not None else register(con, month)
    cx = Ctx(con)
    total_p = sum(int(x["amount_p"] or 0) for x in r["rows"])
    open_n = (r["total"] - r["settled"]) + r["open_scans"]
    try:
        mname = MONTHS[int(month[5:7]) - 1]
    except (ValueError, IndexError):
        mname = month
    h = ['<div id="s726chk"><style>%s</style>' % CHECK_CSS]
    h.append('<h1 id="s726head">%s · %d bill%s · %s</h1>' % (esc(mname), r["total"], "" if r["total"] == 1 else "s", esc(rs(total_p))))
    if r["cls"] != "counted":
        quiet = [x for x in r["rows"] if str(x.get("whose") or "").startswith("Nobody (")]
        h.append('<div class="mut" id="s726parked" style="margin:-6px 0 8px">%s is parked: shown for reading only; nobody is asked.%s</div>'
                 % (esc(month_name(month)), (" %d bill%s under the new rules (%s) wait with nobody." % (len(quiet), "" if len(quiet) == 1 else "s",
                    esc(", ".join("%s %s · %s" % (x["supplier"], x["bill_no"], STATE_EN[x["state"]]) for x in quiet[:6])))) if quiet else ""))
    if open_n:
        h.append('<div class="strip hold" id="s726strip">NEFT on hold · %d open</div>' % open_n)
    else:
        h.append('<div class="strip clear" id="s726strip">All clear ✓</div>')
    rows = check_rows(r, cx)
    for i, (lab, n, lines, grey) in enumerate(rows, 1):
        h.append('<details class="%s%s" data-row="%d"><summary><span class="l"><b>%d</b> %s</span><span class="n">%s</span></summary>'
                 '<ul>%s</ul></details>' % ("grey" if grey else "row", " last" if i == len(rows) else "", i, i, esc(lab), esc(n),
                                           "".join("<li>%s</li>" % x for x in lines) or "<li>Nothing here.</li>"))
    opts = "".join('<option value="%s"%s>%s</option>' % (esc(m), " selected" if m == month else "", esc(month_name(m))) for m in months)
    h.append('<div class="msel">Month <select id="s726month" onchange="location.href=\\'%s/page/check?month=\\'+this.value">%s</select></div>'
             % (esc(prefix), opts))
    h.append('<div class="mut">Read only. The full list is on <a href="%s/page/scans?month=%s">the month\\'s register</a>.</div></div>'
             % (esc(prefix), esc(month)))
    return "".join(h)


def accept_nopaper(con, who, bill_id, accept):
''', 1),
]

# ---------------------------------------------------------------------------------------------------------------- purchase_app.py
E_PA = [
('''# ---- S454 part 5 end -------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
''',
'''# ---- S454 part 5 end -------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S726_PURCHASE_RULES (06-Nov-2026, Sanjeevni session 393; D839, D840, F-1140 - F-1143) -- the rules still live in scan_register.py.
#   * _rematch: before the pass, every AUTO link that fails the S726 auto-link rule (scan_register.autolink_ok) is undone -- the link row
#     deleted, purchase_bill.scan_bill_id cleared, audit 'auto_link_undone' kit S726 -- ONLY when the bill's month or the scan's month is a
#     counted month (scan_register.month_class; October 2026 on). A link whose two months are both parked or hidden (September) is never
#     touched. The pass then pairs the scans again under the rules.
#   * _match_s439: after the verified pair, a scan pairs with a Marg bill on its bill number AND its full date (within S439_DATE_DAYS, the
#     year included) AND its supplier, that number being the only one of the supplier's bills in the window (grade PROBABLE, rule "number +
#     date + supplier (S726 1)"), whatever the totals -- the total then gives the state (Amount differs -> reception's amount question ->
#     Amir). Only for a bill or scan of a counted month. A finalised month's AUTO link is never undone.
#   * If the S726 context cannot be set up, the pass runs exactly as before S726 (nothing new refused, asked or paired).
#   * _s454_autolink: scan_register.autolink_pick -- a candidate S726 refuses is kept on the scan (_s726_cand) and _why_s439 makes it the
#     scan's likely bill ("number_differs"), which is the existing one-tap "Yahi bill hai?" of porders.scan_work. No new reception screen.
#     A pair whose bill and scan are both of a parked month (September) keeps the old auto-link: nothing is raised for it. A paper dated
#     after Marg's last bill is not asked about (its own bill is probably not entered yet): it waits for Marg's entry, as before. A paper of
#     a counted month is never asked against a bill of a month not counted: it waits for its own bill ("no_bill_yet"). A likely bill
#     whose number agrees is worded as an amount question ("amount_differs").
#   * GET /page/check?month=YYYY-MM -- the owner's step view (scan_register.check_body), the checker only; it writes nothing.
# ==========================================================================================================================================
_S726_PASS = None                                                 # set only while a pass runs: the months the S726 rules may act on


def _s726_bill_months():
    """{scan id: bill_month} from the asset app (READ ONLY); {} when the column or the database is not there."""
    acon = _assets_con()
    if acon is None:
        return {}
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        if "bill_month" not in cols:
            return {}
        return {int(r[0]): str(r[1] or "") for r in acon.execute("SELECT id, bill_month FROM bills WHERE kind='Pharmacy'")}
    except sqlite3.Error:
        return {}
    finally:
        acon.close()


def _s726_counted(con, ym):
    return bool(re.match(r"^\\d{4}-\\d\\d$", str(ym or ""))) and _s454_sr().month_class(con, ym) == "counted"


def _s726_undo_plan(con, cx=None, scans=None, bills=None, bm=None):
    """READ ONLY: the AUTO links the S726 rule undoes -> [dict(bill, scan, why, bill_month, scan_month, supplier, bill_no, amount_p, final)];
    None when the asset app's database is not reachable. A link whose bill month and scan month are both not counted is never listed.
    A finalised bill month (purchase_month.status = 'final'): final_undo=True only when that bill month is NOT counted and the SCAN's month
    is counted -- the owner, 06-Nov 17:20 ("yes"): such a link is undone, it frees a counted paper; every other finalised-month link has
    final=True -- KEPT, listed only so the proof flags it."""
    SR = _s454_sr()
    if scans is None:
        acon = _assets_con()
        if acon is None:
            return None
        try:
            scans = _scans(acon)
        finally:
            acon.close()
    if bills is None:
        bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()]
    cx = cx if cx is not None else SR.Ctx(con)
    bm = _s726_bill_months() if bm is None else bm
    final = _s683_final_months(con)
    sby = {s["id"]: s for s in scans}
    bby = {b["id"]: b for b in bills}
    out = []
    try:
        auto = con.execute("SELECT bill_id, asset_bill_id, linked_at FROM purchase_scan_link WHERE grade='AUTO' ORDER BY bill_id").fetchall()
    except sqlite3.Error:
        auto = []
    for r in auto:
        b, s = bby.get(r[0]), sby.get(r[1])
        if b is None or s is None:
            continue                                               # the S439 pass itself drops a link whose bill or scan is gone
        bmon = str(b.get("month") or str(b.get("bill_date") or "")[:7])
        smon = SR.scan_month(s, bm.get(int(s["id"])))
        if not (_s726_counted(con, bmon) or _s726_counted(con, smon)):
            continue                                               # September-only (parked, cleared by the owner): never changed
        before = SR._date(s.get("bill_date")) or SR._date(str(r[2] or "")[:10])
        ok, why = SR.autolink_ok(cx, s, b, bills, undo=True, before=before)
        if not ok:
            out.append(dict(bill=int(r[0]), scan=int(r[1]), why=why, bill_month=bmon, scan_month=smon, supplier=supplier_key(b["supplier"]),
                            bill_no=b["bill_no"], amount_p=b["amount_p"],
                            final=(bmon in final and not (not _s726_counted(con, bmon) and _s726_counted(con, smon))),
                            final_undo=(bmon in final and not _s726_counted(con, bmon) and _s726_counted(con, smon))))
    return out


def _s726_setup(con):
    """The pass's S726 context: the first counted month, the asset app's bill months, the bills by supplier and by id."""
    v = _s454_sr().setting(con, "purchase.register_from", "2026-10-01")
    bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF_BILL).fetchall()]
    by_sup = {}
    for b in bills:
        by_sup.setdefault(supplier_key(b["supplier"]), []).append(b)
    return dict(first=(v[:7] if re.match(r"^\\d{4}-\\d\\d", v) else "2026-10"), bm=_s726_bill_months(), by_sup=by_sup,
                byid={b["id"]: b for b in bills})


_rematch_before_s726 = _rematch


def _rematch(con, who="system"):                                  # noqa: F811
    """S726: the wrong amount-only links of a counted month undone first (never in a finalised month), then the S454 / S439 pass with the
    S726 rules. If the S726 context cannot be set up, the pass runs exactly as before S726 (no undo, no new refusal, question or pair)."""
    global _S726_PASS
    undone = []
    try:
        _S726_PASS = _s726_setup(con)
    except Exception as _e_set:                                # noqa: BLE001 -- fail toward the old behaviour entirely
        _S726_PASS = None
        try:
            _audit(con, who, "s726_setup_error", "", dict(error=str(_e_set)[:200], kit="S726"))
        except Exception:                                      # noqa: BLE001
            pass
    if _S726_PASS is not None:
        try:
            plan = _s726_undo_plan(con)
            for x in plan or []:
                if x.get("final"):
                    continue                                       # a finalised month is never changed -- unless it holds a counted paper
                cur = con.execute("DELETE FROM purchase_scan_link WHERE bill_id=? AND asset_bill_id=? AND grade='AUTO'", (x["bill"], x["scan"]))
                if not cur.rowcount:
                    continue
                con.execute("UPDATE purchase_bill SET scan_bill_id=NULL WHERE id=? AND scan_bill_id=?", (x["bill"], x["scan"]))
                _audit(con, who, "auto_link_undone", x["bill"], dict(scan=x["scan"], why=x["why"], supplier=x["supplier"], bill_no=x["bill_no"],
                                                                      amount_p=x["amount_p"], bill_month=x["bill_month"], scan_month=x["scan_month"],
                                                                      kit="S726", **({"note": "owner 06-Nov 17:20: frees a counted paper from a "
                                                                                      "finalised month"} if x.get("final_undo") else {})))
                undone.append(x)
            if undone:
                con.commit()
        except Exception as _e_s726:                           # noqa: BLE001 -- the pass never fails for it
            try:
                _audit(con, who, "auto_link_undo_error", "", dict(error=str(_e_s726)[:200], kit="S726"))
            except Exception:                                  # noqa: BLE001
                pass
    try:
        out = _rematch_before_s726(con, who)
    finally:
        _S726_PASS = None
    if isinstance(out, dict):
        out["undone"] = len(undone)
    return out


def _s726_pass_counted(ym):
    p = _S726_PASS
    return bool(p) and bool(re.match(r"^\\d{4}-\\d\\d$", str(ym or ""))) and ym >= p["first"]


def _s726_bill_ym(b):
    return str(b.get("month") or str(b.get("bill_date") or "")[:7])


_match_before_s726 = _match_s439


def _match_s439(s, b):                                            # noqa: F811
    """S726 (1): the verified pair first (S454); then the bill number, the FULL date (within S439_DATE_DAYS, the year included) and the
    supplier agree, and that number is the only one of this supplier's bills in that window -> rank 2, PROBABLE, whatever the totals (the
    total gives the state). Only inside a pass, for a bill or a scan of a counted month."""
    m = _match_before_s726(s, b)
    if m or _S726_PASS is None or b["id"] in s.get("_no", ()):
        return m
    SR = _s454_sr()
    if SR.billno_compat(s.get("bill_no"), b["bill_no"]) != "agree":
        return None
    sd, bd = SR._date(s.get("bill_date")), SR._date(b.get("bill_date"))
    if sd is None or bd is None or abs((sd - bd).days) > S439_DATE_DAYS:
        return None                                                # the day and month alone are not the date (Oct-2025 is not Oct-2026)
    if not (_s726_pass_counted(_s726_bill_ym(b)) or _s726_pass_counted(SR.scan_month(s, _S726_PASS["bm"].get(int(s["id"]))))):
        return None
    same = [x for x in _S726_PASS["by_sup"].get(supplier_key(b["supplier"]), []) if SR.billno_compat(s.get("bill_no"), x["bill_no"]) == "agree"
            and SR._date(x.get("bill_date")) is not None and abs((SR._date(x.get("bill_date")) - sd).days) <= S439_DATE_DAYS]
    if len(same) != 1:
        return None                                                # two series of one supplier carry this number: a question, not a pair
    cx = _s454_cx()
    if SR.supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(s["id"])) != "agree":
        return None                                                # a number and a day alone, with no supplier, stay a question
    return 2, "PROBABLE", "number + date + supplier (S726 1)"


def _s454_autolink(con, who, scans, bills, taken, linked, dups):      # noqa: F811
    """S454 (5) as S726 (F-1141) rules it: a scan pairs by itself with the ONE unscanned bill of its supplier carrying its amount only
    when scan_register.autolink_ok agrees (grade AUTO, audit auto_link); a candidate it refuses is kept on the scan as _s726_cand for
    _why_s439 -- reception's "is this the same bill?" -- unless that bill is of a month not counted while the scan's is (it then waits for
    its own bill). A pair of a parked month only keeps the old rule; with no S726 context (a setup fault) every pair keeps the old rule."""
    SR = _s454_sr()
    cx = _s454_cx()
    scan_from = _scan_from_s409(con)
    dup_ok = set()
    try:
        dup_ok = {int(r[0]) for r in con.execute("SELECT asset_bill_id FROM purchase_scan_state WHERE dup_ok IS NOT NULL")}
    except sqlite3.Error:
        pass
    made = []
    for s in sorted(scans, key=lambda x: x["id"]):
        if s["id"] in linked or s["id"] in dups or s["id"] in dup_ok:
            continue
        b, cand, why = SR.autolink_pick(cx, s, bills, taken, scan_from, refused=s.get("_no", ()))
        rule = "auto_link (S726 1): the only bill of this supplier with this amount, in its month"
        if cand is not None:
            if _S726_PASS is None:
                b, cand = cand, None                               # no S726 context: the old rule, nothing new refused or asked
                rule = "auto_link (S454 5): the only unscanned bill of this supplier with this amount"
            else:
                bc = _s726_pass_counted(_s726_bill_ym(cand))
                sc = _s726_pass_counted(SR.scan_month(s, _S726_PASS["bm"].get(int(s["id"]))))
                if not (bc or sc):
                    b, cand = cand, None                           # a parked month only (September): the old rule stands, nothing is asked
                    rule = "auto_link (S454 5, a parked month): the only unscanned bill of this supplier with this amount"
                elif sc and not bc:
                    cand = None                                    # a counted paper against a parked bill: no question; it waits for its own bill
        if cand is not None:
            s["_s726_cand"], s["_s726_why"] = cand["id"], why
        if not b:
            continue
        cur = con.execute("INSERT OR IGNORE INTO purchase_scan_link (bill_id,asset_bill_id,grade,matched_on,linked_at) VALUES (?,?,?,?,?)",
                          (b["id"], s["id"], "AUTO", rule, now_iso()))
        if not cur.rowcount:
            continue
        con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (s["id"], b["id"]))
        _audit(con, who, "auto_link", b["id"], dict(scan=s["id"], supplier=supplier_key(b["supplier"]), bill_no=b["bill_no"], amount_p=b["amount_p"],
                                                     scan_no=s.get("bill_no"), scan_date=s.get("bill_date"), kit="S726"))
        taken[b["id"]] = s["id"]
        linked.add(s["id"])
        made.append((s["id"], b["id"], "AUTO", "auto_link"))
    return made


_why_before_s726 = _why_s439
_S726_ASK = ("number_differs", "amount_differs", "no_digits")


def _why_s439(s, bills, taken, last_date):                        # noqa: F811
    """S726: (1) a scan whose amount-only pair S726 refused -- with no likely bill by the older rules -- names that bill as its likely bill
    ("number_differs"): reception's one-tap "Yahi bill hai?"; not when the paper is dated after Marg's last bill (it waits for Marg's
    entry). (2) A scan of a counted month is never asked against a bill of a month not counted (the BLOCKER of the review): it waits for
    its own bill ("no_bill_yet"). (3) A likely bill whose NUMBER agrees is worded as an amount question ("amount_differs").
    With no S726 context (outside a pass, or a setup fault) the older rules' answer stands as it is."""
    why, detail, hint = _why_before_s726(s, bills, taken, last_date)
    if _S726_PASS is None:
        return why, detail, hint
    SR = _s454_sr()
    cand = s.get("_s726_cand")
    if cand and not (why in _S726_ASK and s.get("_likely")):
        last = _date_or_none_s439(last_date)
        fresh = s.get("_date") is not None and last is not None and s["_date"] > last
        b = _S726_PASS["byid"].get(cand)
        if not fresh and b is not None and b["id"] not in s.get("_no", ()):
            s["_likely"] = b["id"]
            lab = "%s bill %s (%s, %s)" % (supplier_key(b["supplier"]), b["bill_no"], _human(b["bill_date"]), _r(b["amount_p"]))
            also = (" — that bill already has scan #%d" % taken[b["id"]]) if b["id"] in taken else ""
            why, detail, hint = ("number_differs", "is this the same bill? — the scan's amount %s is %s's, but %s (S726: not paired by itself)%s"
                                 % (_r(s.get("amount_p")) if s.get("amount_p") is not None else "—", lab, s.get("_s726_why") or "the rule refused it",
                                    also), None if b["id"] in taken else b["id"])
    lk = s.get("_likely")
    b = _S726_PASS["byid"].get(lk) if lk else None
    if b is None or why not in _S726_ASK:
        return why, detail, hint
    if _s726_pass_counted(SR.scan_month(s, _S726_PASS["bm"].get(int(s["id"])))) and not _s726_pass_counted(_s726_bill_ym(b)):
        s["_likely"] = None
        return ("no_bill_yet", "waits for its own bill in Marg — the bill it reads like (%s %s, %s) is of %s, a month not counted (S726)"
                % (supplier_key(b["supplier"]), b["bill_no"], _human(b["bill_date"]), _s726_bill_ym(b)), None)
    if why == "number_differs" and SR.billno_compat(s.get("bill_no"), b["bill_no"]) == "agree":
        also = (" — that bill already has scan #%d" % taken[b["id"]]) if b["id"] in taken else ""
        return ("amount_differs", "amount differs — the scan reads %s; %s bill %s (%s, %s) carries the same number%s (S726)"
                % (_r(s.get("amount_p")) if s.get("amount_p") is not None else "no amount", supplier_key(b["supplier"]), b["bill_no"],
                   _human(b["bill_date"]), _r(b["amount_p"]), also), hint)
    return why, detail, hint


def _s726_check_page(con, u):
    """S726 (D840): the owner's step view -- reads only (no pass on GET)."""
    SR = _s454_sr()
    prefix = request.script_root + _url_prefix
    months = SR.months_with_bills(con, 12)
    want = str(request.args.get("month") or "")
    if want and not re.match(r"^\\d{4}-\\d{2}$", want):
        return "bad month", 400
    if want:
        month, r = want, None
    else:
        month, r = SR.check_month(con, months)
    if month not in months:
        months = sorted(set(months + [month]), reverse=True)
    body = SR.check_body(con, month, prefix, months, r)
    return _page("Purchase check — %s" % SR.month_name(month), _s454_bar(month) + body)


@bp.route("/page/check")
def page_s726_check():
    """S726 (D840): the owner's step view of a month's purchase bills (English, phone-first). The checker only; it writes nothing."""
    u, err = _person("checker")
    if err:
        return err
    if not _is_doctor(u):
        return _refuse("This is for the doctor only.")
    return _s726_check_page(_db(), u)
# ---- S726 end -----------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
''', 1),
]

# ---------------------------------------------------------------------------------------------------------------- porders.py
E_PO = [
('''def _s440_differs(scan_p, marg_p):
    return bool(scan_p) and abs(int(scan_p) - int(marg_p)) > _s454_noise_p()   # S454 (5): beyond purchase.total_noise_rs (Rs 10), never 2%
''',
'''def _s440_differs(scan_p, marg_p, ym=None):
    """S726 (F-1140): beyond Rs 1 for a bill of a counted month; a parked month (September) keeps purchase.total_noise_rs -- no new
    question for it. ym: the bill's month (None: the old band)."""
    return bool(scan_p) and abs(int(scan_p) - int(marg_p)) > _s726_tol_p(ym)


_S726_SAID = []


def _s726_tol_p(ym):
    """Rs 1 for a bill of a counted month; the old noise band for a parked month, an unknown month (None) or any fault."""
    if ym is None:
        return _s454_noise_p()
    try:
        import scan_register                                   # noqa: PLC0415
        return S440_TOL_P if scan_register.month_class(_db(), str(ym or "")) == "counted" else _s454_noise_p()
    except Exception as e:                                    # noqa: BLE001 -- fail to the old band: nothing new is asked (S726 1)
        if not _S726_SAID:
            _S726_SAID.append(1)
            print("porders S726: the month of a bill could not be judged (%s) -- the old noise band is used" % str(e)[:160], file=sys.stderr)
        return _s454_noise_p()


def _s726_quiet(con):
    try:
        import scan_register                                   # noqa: PLC0415
        return scan_register.s726_quiet_bills(con)
    except Exception:                                         # noqa: BLE001
        return set()
''', 1),
('''            if b is not None and not row.get("amount_state") and _s440_differs(sp, b["amount_p"]):
''',
'''            if b is not None and not row.get("amount_state") and _s440_differs(sp, b["amount_p"], b.get("month") or str(b.get("bill_date") or "")[:7]):
''', 1),
('''    if row.get("amount_state") or not _s440_differs(scan_p, marg_p):
''',
'''    ym726 = (con.execute("SELECT COALESCE(month, substr(bill_date,1,7)) FROM purchase_bill WHERE id=?", (bill[0],)).fetchone() or [""])[0] or ""
    if row.get("amount_state") or not _s440_differs(scan_p, marg_p, ym726):
''', 1),
('''    extra, shown, scanned_twin = _s440_doubles(con, bills, links)
    for x in unscanned:                                           # 1 -- a Marg bill nobody has scanned
        bid = x["bill_id"]
        if bid in pending_bills or bid in extra or bid in scanned_twin:
''',
'''    extra, shown, scanned_twin = _s440_doubles(con, bills, links)
    quiet726 = _s726_quiet(con)                                   # S726: a parked bill an undo freed asks nobody
    for x in unscanned:                                           # 1 -- a Marg bill nobody has scanned
        bid = x["bill_id"]
        if bid in pending_bills or bid in extra or bid in scanned_twin or bid in quiet726:
''', 1),
('''                if b is not None and _s440_differs(sp, b["amount_p"]):
''',
'''                if b is not None and _s440_differs(sp, b["amount_p"], b.get("month") or str(b.get("bill_date") or "")[:7]):
''', 1),
]

EDITS = {"scan_register.py": E_SR, "purchase_app.py": E_PA, "porders.py": E_PO}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, raw):
    if md5(raw) != FROM[name]:
        raise SystemExit("make_s726: REFUSED -- %s is %s, not the FROM %s (nothing written)" % (name, md5(raw)[:8], FROM[name][:8]))
    s = raw.decode("utf-8")
    if "\r" in s:
        raise SystemExit("make_s726: REFUSED -- %s carries CR line endings (nothing written)" % name)
    for i, (old, new, want) in enumerate(EDITS[name], 1):
        n = s.count(old)
        if n != want:
            raise SystemExit("make_s726: REFUSED -- %s edit %d: the anchor stands %d time(s), not %d (nothing written)" % (name, i, n, want))
        s = s.replace(old, new)
    return s.encode("utf-8")


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    src, out = argv
    built = {}
    for name in FROM:
        p = os.path.join(src, name)
        if not os.path.isfile(p):
            raise SystemExit("make_s726: REFUSED -- %s is not in %s (nothing written)" % (name, src))
        with open(p, "rb") as fh:
            built[name] = build(name, fh.read())
    os.makedirs(out, exist_ok=True)
    for name, b in built.items():
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(b)
        print("make_s726: %s %s -> %s (%d edits)" % (name, FROM[name][:8], md5(b)[:8], len(EDITS[name])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
