#!/usr/bin/env python3
"""build_patch.py -- produces staff_ledger.py v3.7-S238-CLOSE-GUARD from the live
pin v3.6-S225-LOANS-D374 (md5 802577112e6db82bcf763d142efcd00c). Every edit is an
anchored, exactly-once replacement; a missing or doubled anchor aborts the build."""
import hashlib, sys

SRC, DST = sys.argv[1], sys.argv[2]
PIN = "802577112e6db82bcf763d142efcd00c"
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != PIN:
    sys.exit("source is not the pinned v3.6 rev 3")
s = raw.decode("utf-8")

def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)

# ---- 0. version + the file's own history (F-404: the log stopped at v3.0) ----
rep('APP_VERSION = "3.6-S225-LOANS-D374"', 'APP_VERSION = "3.7-S238-CLOSE-GUARD"', "version")
rep('''Environment (all optional):''', '''v3.1 .. v3.6 (S157-S225): D331 ceiling + signed application · SL2-SL7 (quota lane,
  capacity rule, schedules, DEFER, perks) · D374 approve-first · S225 loans view.
  (Recorded here at S238 -- the log had stopped at v3.0 while the code ran v3.6, F-404.)
v3.7 (S238, D447 -- the owner, 10-Sep-2026: "the close should be after the calendar
  month is over and only when I manually do it"):
  + THE CLOSE IS THE OWNER'S, AND ONLY AFTER THE MONTH HAS ENDED. The Salary page
    offers the close only from the 1st of the following month; the route and the CLI
    refuse an earlier one. Nothing on the box has ever closed a month by itself, and
    nothing does now.
  + NO SILENT PENDING. The close refuses while a row that belongs to the month is
    still PENDING (August's Rs 20,000 was pending at its close and collected
    nothing) -- unless the checker ticks "close anyway", which names them.
  + THE CLOSE SAYS WHAT IT DID NOT COLLECT (F-396): held by capacity, waiting behind
    the loan, a schedule left behind, rows left pending -- by name, on the page and
    in close_report_<month>.txt.
  + DUPLICATE WARNING AT ENTRY (F-400): same person, category, date and amount as a
    live row is refused with a one-click "save it anyway" for a genuine second entry.
  + A SPECIAL ADVANCE NEEDS A NARRATION (the one row that most needs a reason).

Environment (all optional):''', "doclog")

# ---- 1. the guard functions, right after close_month() ----------------------
rep('''# --------------------------------------------------------------- migration ---
def migrate_loan(''', '''# =============================================================================
#  S238 (D447): THE CLOSE IS THE OWNER'S, AND ONLY AFTER THE MONTH HAS ENDED.
#  close_month() itself -- the engine -- is unchanged: the guard lives in front of
#  it (the route and the CLI), so every earlier proof of the engine still stands.
# =============================================================================
CLOCK_OVERRIDE = None          # selftest only: 'YYYY-MM-DD'

def _today():
    if CLOCK_OVERRIDE:
        return datetime.date.fromisoformat(CLOCK_OVERRIDE)
    return datetime.date.today()          # the server runs on IST

def month_ended(month):
    """True only once the calendar month is over (from the 1st of the next)."""
    return month < _today().strftime("%Y-%m")

def close_opens_on(month):
    y, m = int(month[:4]), int(month[5:7])
    d = datetime.date(y + m // 12, m % 12 + 1, 1)
    return d.strftime("%d-%b-%Y")

def _row_month(r):
    if r["category"] == "ADVANCE_ISSUE":
        return advance_against_month(r)
    return (r.get("date_from") or "")[:7]

def pending_for_month(month, rows=None):
    """PENDING rows that belong to `month` or earlier -- the close would leave
    them out of this month without a word."""
    return [r for r in (rows or load_ledger())
            if r["status"] == "PENDING" and _row_month(r) and _row_month(r) <= month]

def close_blockers(month, rows=None, allow_pending=False):
    rows = rows or load_ledger()
    out = []
    if any(r.get("closed_month") == month for r in rows):
        out.append(f"{month} is already closed")
    if not month_ended(month):
        out.append(f"{month} has not ended — the close opens on {close_opens_on(month)}, "
                   f"and it runs only when you press it")
    pend = pending_for_month(month, rows)
    if pend and not allow_pending:
        out.append(f"{len(pend)} entr{'y is' if len(pend) == 1 else 'ies are'} still PENDING for "
                   f"{month} — approve or reject first, or tick 'close anyway'")
    return out

def close_report(month, rows=None, write=True):
    """F-396: what the close did NOT collect, by name. Read after the close."""
    import re as _re
    rows = rows or load_ledger()
    lines = []
    for r in rows:
        if r["category"] == "CAPACITY_HOLD" and r.get("closed_month") == month:
            m = _re.search(r"Rs (\\d+)", r.get("narration", ""))
            lines.append((r["staff"], f"Rs {m.group(1) if m else '?'} HELD — the salary could not bear it; it stays owed"))
    for a in open_advances():
        iss = a["issue"]
        if advance_against_month(iss) > month or a["balance"] <= 0:
            continue
        got = sum(-x["amount"] for x in rows if x.get("contra_of") == iss["id"]
                  and x["category"] == "ADVANCE_INSTALMENT" and x.get("closed_month") == month)
        lane = advance_lane(a)
        what = f"advance of Rs {iss['amount']} dated {iss['date_from']}"
        if lane == "schedule":
            due = schedule_due_cum(iss, month, rows) or 0
            short = due - advance_recovered(iss["id"], rows)
            if short > 0:
                lines.append((iss["staff"], f"{what}: its schedule is Rs {short} BEHIND after this close"))
        elif lane == "waterfall" and got == 0:
            lines.append((iss["staff"], f"{what}: nothing collected — it waits in line behind "
                          f"the interest loan (Rs {a['balance']} outstanding)"))
        elif lane == "quota" and got == 0:
            lines.append((iss["staff"], f"{what}: nothing collected (Rs {a['balance']} outstanding)"))
    for r in pending_for_month(month, rows):
        lines.append((r["staff"], f"{CATEGORIES[r['category']][0]} of Rs {abs(r['amount'])} dated "
                      f"{r['date_from']} was still PENDING — it is NOT in {month}"))
    lines.sort()
    if write:
        p = _p(f"close_report_{month}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"CLOSE REPORT {month} — written {now()}\\n")
            f.write("what this close did NOT collect:\\n" if lines else "everything due was collected.\\n")
            for st, t in lines:
                f.write(f"  {st}: {t}\\n")
        os.chmod(p, 0o600)
    return lines

def load_close_report(month):
    try:
        with open(_p(f"close_report_{month}.txt"), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None


# --------------------------------------------------------------- migration ---
def migrate_loan(''', "guards")

# ---- 2. make_entry: duplicate check + narration on SPECIAL -------------------
rep('''def make_entry(users, maker, staff, cat, date_from, date_to, days, manual_amount,
               narration, instalment=None, contra_of=None, interest=False,
               against_month=None, special=False, schedule=None):
    u = users[maker]''', '''class DuplicateEntry(ValueError):
    """F-400: same person, category, date and amount as a live row."""
    def __init__(self, match):
        self.match = match
        super().__init__(
            f"this looks like a DUPLICATE — {match['staff']} already has "
            f"{CATEGORIES[match['category']][0]} Rs {abs(match['amount'])} dated "
            f"{match['date_from']} (entered {match['ts_entry']} by {match['maker']}, "
            f"{match['status']})")

def find_duplicate(staff, cat, date_from, amount, rows=None):
    rows = rows or load_ledger()
    for r in rows:
        if (r["staff"] == staff and r["category"] == cat and r["date_from"] == date_from
                and abs(r["amount"]) == abs(int(amount)) and r["amount"] != 0
                and r["status"] in ("PENDING", "APPROVED") and not r.get("contra_of")
                and not any(x.get("contra_of") == r["id"] and x["category"] == r["category"]
                            and x["amount"] == -r["amount"] and x["status"] == "APPROVED"
                            for x in rows)):
            return r
    return None

def make_entry(users, maker, staff, cat, date_from, date_to, days, manual_amount,
               narration, instalment=None, contra_of=None, interest=False,
               against_month=None, special=False, schedule=None, dup_check=False):
    u = users[maker]''', "make_entry_sig")

rep('''        else:
            special = False            # no base salary on file: gate disabled,
                                       # shown inline as unenforced — never silent
    else:''', '''        else:
            special = False            # no base salary on file: gate disabled,
                                       # shown inline as unenforced — never silent
        # S238: the one row that most needs a reason must ask for one.
        if special and not (narration or "").strip():
            raise ValueError("a SPECIAL advance needs a narration — why it was given, "
                             "and where the cash came from")
    else:''', "special_narr")

rep('''    # D331: a SPECIAL advance is never direct — even a checker's own entry
    # goes PENDING, so the application gate at decide() can never be bypassed.
    direct = (role == "checker") and not special''', '''    # S238 (F-400): a live row with the same person, category, date and amount.
    if dup_check and amount:
        d = find_duplicate(staff, cat, date_from, amount)
        if d:
            raise DuplicateEntry(d)
    # D331: a SPECIAL advance is never direct — even a checker's own entry
    # goes PENDING, so the application gate at decide() can never be bypassed.
    direct = (role == "checker") and not special''', "dup_call")

# ---- 3. the entry route: dup_check on, one-click "save anyway" ---------------
rep('''                                 special=bool(f.get("special")),
                                 schedule=f.get("schedule", ""))''', '''                                 special=bool(f.get("special")),
                                 schedule=f.get("schedule", ""),
                                 dup_check=not f.get("dup_ok"))''', "route_dup")
rep('''            except Exception as e:
                msg = f"<p style='color:red'>NOT saved: {e}</p>"
        opts_staff = "".join(f"<option>{s}</option>" for s in staff_names())''', '''            except DuplicateEntry as e:
                keep = "".join(f"<input type='hidden' name='{html_esc(k)}' value='{html_esc(v)}'>"
                               for k, v in request.form.items() if k != "dup_ok")
                msg = (f"<div class='card' style='border-color:#b45309'><p style='color:#b45309'>"
                       f"<b>NOT saved — {html_esc(str(e))}.</b></p>"
                       f"<p>If this really is a separate, second entry, save it once more:</p>"
                       f"<form method='post'>{keep}<input type='hidden' name='dup_ok' value='1'>"
                       f"<button class='no'>Yes — save it as a separate entry</button></form></div>")
            except Exception as e:
                msg = f"<p style='color:red'>NOT saved: {e}</p>"
        opts_staff = "".join(f"<option>{s}</option>" for s in staff_names())''', "route_dup_msg")

# ---- 4. the Salary page, step 5 ------------------------------------------------
rep('''        # step 5 — ledger close
        if closed:
            steps.append(f"<div class='card'><b>5 · Ledger close</b> — {month} is closed "
                         f"(adjustments + loan instalments captured). ✔</div>")
        else:
            steps.append(f"""<div class="card"><b>5 · Ledger close</b> — NOT yet closed.
              The close computes loan instalments and stamps every approved adjustment
              into {month}. Run it once, after all of the month's entries are in.<br>
              <form method="post" action="{URL_PREFIX}/salary/close">
              <input type="hidden" name="m" value="{month}">
              <button class="no" onclick="return confirm('Close ledger month {month}? Loan instalments will be generated. A month closes only once.')">
              Run monthly close for {month}</button></form></div>""")''', '''        # step 5 — ledger close (S238/D447: only after the month, only by hand)
        if closed:
            _rep = load_close_report(month)
            steps.append(f"<div class='card'><b>5 · Ledger close</b> — {month} is closed "
                         f"(adjustments + loan instalments captured). ✔"
                         + (f"<pre style='white-space:pre-wrap;font-size:13px'>{html_esc(_rep)}</pre>"
                            if _rep else "") + "</div>")
        elif not month_ended(month):
            steps.append(f"<div class='card'><b>5 · Ledger close</b> — {month} is still running. "
                         f"The close opens on <b>{close_opens_on(month)}</b>, after the month has "
                         f"ended, and it never runs by itself: you press it, once, when attendance "
                         f"and every correction for {month} are done.</div>")
        else:
            _pend = pending_for_month(month, rows_l)
            _pl = "".join(f"<li>{html_esc(r['staff'])} · {CATEGORIES[r['category']][0]} · "
                          f"Rs {abs(r['amount'])} · {html_esc(r['date_from'])}</li>" for r in _pend)
            _pw = (f"<p style='color:#b45309'><b>{len(_pend)} entr{'y is' if len(_pend) == 1 else 'ies are'} "
                   f"still PENDING for {month}</b> — approve or reject them on "
                   f"<a href='{URL_PREFIX}/pending'>Pending</a> first. Closed now, they fall into "
                   f"the next month:</p><ul>{_pl}</ul><label style='font-weight:normal'>"
                   f"<input type='checkbox' name='allow_pending' value='1' style='width:auto'> "
                   f"close anyway — I know these are not in {month}</label><br>") if _pend else ""
            steps.append(f"""<div class="card"><b>5 · Ledger close</b> — NOT yet closed.
              The close computes loan instalments and stamps every approved adjustment
              into {month}. Run it once, after attendance and every correction are in.
              Afterwards it tells you, by name, anything it could not collect.<br>
              <form method="post" action="{URL_PREFIX}/salary/close">
              <input type="hidden" name="m" value="{month}">{_pw}
              <button class="no" onclick="return confirm('Close ledger month {month}? Loan instalments will be generated. A month closes only once.')">
              Run monthly close for {month}</button></form></div>""")''', "step5")

# ---- 5. the close route: blockers first, the report after ---------------------
rep('''        m = request.form["m"]
        try:
            out, n = close_month(users, u, m)
            msg = f"Closed {m}: {n} rows."
        except Exception as e:
            return page("Salary", f"<p style='color:red'>close failed: {html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/salary?m={m}'>back</a></p>", u)
        return redirect(URL_PREFIX + f"/salary?m={m}&msg={msg}")''', '''        m = request.form["m"]
        try:
            datetime.date.fromisoformat(m + "-01")
            stop = close_blockers(m, allow_pending=bool(request.form.get("allow_pending")))
            if stop:
                raise ValueError("; ".join(stop))
            out, n = close_month(users, u, m)
            close_report(m)
            msg = f"Closed {m}: {n} rows."
        except Exception as e:
            return page("Salary", f"<p style='color:red'>close NOT run: {html_esc(str(e))}</p>"
                        f"<p><a href='{URL_PREFIX}/salary?m={m}'>back</a></p>", u)
        return redirect(URL_PREFIX + f"/salary?m={m}&msg={msg}")''', "close_route")

# ---- 6. the CLI close ------------------------------------------------------------
rep('''        if not checkers: sys.exit("no checker user exists")
        out, n = close_month(users, checkers[0], args[1])
        print(f"Closed {args[1]}: {n} approved rows -> {out}")''', '''        if not checkers: sys.exit("no checker user exists")
        stop = close_blockers(args[1], allow_pending="--allow-pending" in args)
        if stop:
            sys.exit("close NOT run: " + "; ".join(stop))
        out, n = close_month(users, checkers[0], args[1])
        rep_ = close_report(args[1])
        print(f"Closed {args[1]}: {n} approved rows -> {out}")
        for st, t in rep_:
            print(f"  NOT collected — {st}: {t}")''', "cli_close")

# ---- 7. selftest: the new behaviour, proven -------------------------------------
rep('''    print(f"SELFTEST PASSED — {ok[0]} maker-checker, rate-card, advance, loan, "
          f"skip, statement, salary, report, F-51 and D332/SL5+SL6+SL7 checks OK")''', '''    # ======== S238 (D447): the close guard, the report, duplicates, SPECIAL narration ====
    global CLOCK_OVERRIDE
    _n38 = ok[0]
    _app8 = create_app(); _app8.testing = True; _cl8 = _app8.test_client()
    _cl8.post(URL_PREFIX + "/login", data={"u": "doc", "p": "pw"})
    CLOCK_OVERRIDE = "2031-03-15"
    ck(not month_ended("2031-03") and month_ended("2031-02"), "S238: a month ends on the 1st of the next")
    ck(close_opens_on("2031-03") == "01-Apr-2031" and close_opens_on("2031-12") == "01-Jan-2032",
       "S238: the close opens on the 1st of the following month (year rolls)")
    _b8 = len(load_ledger())
    _r8 = _cl8.post(URL_PREFIX + "/salary/close", data={"m": "2031-03"}).data.decode()
    ck("close NOT run" in _r8 and "has not ended" in _r8 and len(load_ledger()) == _b8
       and not ledger_closed("2031-03"), "S238: the route refuses to close a running month, and writes nothing")
    _s8 = _cl8.get(URL_PREFIX + "/salary?m=2031-03").data.decode()
    ck("opens on <b>01-Apr-2031</b>" in _s8 and "Run monthly close for 2031-03" not in _s8,
       "S238: the Salary page offers no close button while the month runs")
    _p8 = make_entry(users, "mfull", "Alpha", "NIGHT_DUTY", "2031-02-10", "2031-02-10", 1, "0", "")
    ck(_p8["status"] == "PENDING", "S238: a maker's February entry is PENDING")
    ck(any("still PENDING" in x for x in close_blockers("2031-02")), "S238: a pending February row blocks the February close")
    _s8b = _cl8.get(URL_PREFIX + "/salary?m=2031-02").data.decode()
    ck("still PENDING for 2031-02" in _s8b and "close anyway" in _s8b and "Run monthly close for 2031-02" in _s8b,
       "S238: after the month ends the page names the pending row and offers 'close anyway'")
    _r8b = _cl8.post(URL_PREFIX + "/salary/close", data={"m": "2031-02"}).data.decode()
    ck("close NOT run" in _r8b and not ledger_closed("2031-02"), "S238: without 'close anyway' the pending row blocks the close")
    _big = make_entry(users, "doc", "Beta", "ADVANCE_ISSUE", "2031-02-05", "", 0, "3000", "feb advance",
                      instalment="1000")
    _r8c = _cl8.post(URL_PREFIX + "/salary/close", data={"m": "2031-02", "allow_pending": "1"})
    ck(_r8c.status_code == 302 and ledger_closed("2031-02"), "S238: 'close anyway' closes the finished month")
    _t8 = load_close_report("2031-02") or ""
    ck("still PENDING" in _t8 and "Alpha" in _t8, "S238: the close report names the row left pending")
    ck(_cl8.post(URL_PREFIX + "/salary/close", data={"m": "2031-02"}).data.decode().count("already closed") == 1,
       "S238: a second close is refused")
    _s8c = _cl8.get(URL_PREFIX + "/salary?m=2031-02").data.decode()
    ck("CLOSE REPORT 2031-02" in _s8c, "S238: the closed month shows its close report on the Salary page")
    # a schedule left behind is reported by name
    _sc = make_entry(users, "doc", "Gamma", "ADVANCE_ISSUE", "2031-03-02", "", 0, "6000", "sched",
                     schedule="2031-03:3000, 2031-04:3000")
    _lines = close_report("2031-03", write=False)
    ck(any(st == "Gamma" and "BEHIND" in t for st, t in _lines),
       "S238: an unclosed schedule step is reported as BEHIND, by name")
    # duplicates
    _d1 = make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2031-03-03", "", 0, "1100", "", dup_check=True)
    try:
        make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2031-03-03", "", 0, "1100", "", dup_check=True)
        ck(False, "S238: a duplicate must be refused")
    except DuplicateEntry as e:
        ck(e.match["id"] == _d1["id"], "S238: an identical second entry is refused as a DUPLICATE, naming the first")
    _d2 = make_entry(users, "doc", "Alpha", "ADVANCE_ISSUE", "2031-03-03", "", 0, "1100", "", dup_check=False)
    ck(_d2["id"] != _d1["id"], "S238: with the owner's say-so the second entry saves")
    ck(find_duplicate("Alpha", "ADVANCE_ISSUE", "2031-03-03", 1200) is None
       and find_duplicate("Alpha", "ADVANCE_ISSUE", "2031-03-04", 1100) is None,
       "S238: a different amount or date is not a duplicate")
    make_contra(users, "doc", _d2["id"], "test reversal")
    make_contra(users, "doc", _d1["id"], "test reversal")
    ck(find_duplicate("Alpha", "ADVANCE_ISSUE", "2031-03-03", 1100) is None,
       "S238: a reversed row is not a duplicate")
    _e1 = _cl8.post(URL_PREFIX + "/", data={"staff": "Alpha", "category": "ADVANCE_ISSUE",
                    "date_from": "2031-03-06", "amount": "900", "narration": "x"}).data.decode()
    _e2 = _cl8.post(URL_PREFIX + "/", data={"staff": "Alpha", "category": "ADVANCE_ISSUE",
                    "date_from": "2031-03-06", "amount": "900", "narration": "x"}).data.decode()
    ck("Saved" in _e1 and "DUPLICATE" in _e2 and "save it as a separate entry" in _e2
       and "name='dup_ok' value='1'" in _e2, "S238: the entry page refuses the duplicate and offers one-click save-anyway")
    _n0 = len(load_ledger())
    _e3 = _cl8.post(URL_PREFIX + "/", data={"staff": "Alpha", "category": "ADVANCE_ISSUE",
                    "date_from": "2031-03-06", "amount": "900", "narration": "x", "dup_ok": "1"}).data.decode()
    ck("Saved" in _e3 and len(load_ledger()) == _n0 + 1, "S238: save-anyway writes exactly one row")
    # SPECIAL needs a narration (ceiling gate on: give Alpha a base)
    with open(STAFF_CSV, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["user_id", "name", "active", "base_salary"])
        for i, n in enumerate(["Alpha", "Beta", "Gamma"]): w.writerow([i + 1, n, "Y", "10000"])
    try:
        make_entry(users, "doc", "Beta", "ADVANCE_ISSUE", "2031-05-01", "", 0, "9000", "   ", special=True)
        ck(False, "S238: a SPECIAL advance without a narration must be refused")
    except ValueError as e:
        ck("needs a narration" in str(e), "S238: a SPECIAL advance without a narration is refused")
    _sp = make_entry(users, "doc", "Beta", "ADVANCE_ISSUE", "2031-05-01", "", 0, "9000",
                     "cash from drawer, application to follow", special=True)
    ck(_sp["special"] and _sp["status"] == "PENDING", "S238: with a narration the SPECIAL advance saves PENDING")
    CLOCK_OVERRIDE = None
    ck(ok[0] - _n38 == 21, "S238: 21 new checks ran (counted, not projected)")

    print(f"SELFTEST PASSED — {ok[0]} maker-checker, rate-card, advance, loan, "
          f"skip, statement, salary, report, F-51, D332/SL5+SL6+SL7 and S238 checks OK")''', "selftest")

# ---- 8. two pre-S238 selftest calls made a SPECIAL advance with an EMPTY narration;
#         the new rule refuses that, so they now carry one (their subject is unchanged)
rep('''                     "2027-03-06", "2027-03-06", 0, "4000", "",
                     special=True)''', '''                     "2027-03-06", "2027-03-06", 0, "4000", "special test (S238: narration now required)",
                     special=True)''', "st_r32")
rep('''"2027-03-07", "2027-03-07", 0, "16000", "", special=True)''',
    '''"2027-03-07", "2027-03-07", 0, "16000", "special test (S238: narration now required)", special=True)''', "st_r33")

open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
