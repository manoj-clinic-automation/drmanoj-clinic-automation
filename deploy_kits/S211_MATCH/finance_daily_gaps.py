#!/usr/bin/env python3
"""
finance_daily_gaps.py  --  S211 / H2: yesterday's gaps, for both screens.

The owner's scope ruling governs every line of this file:

    "Make this gap visible to him and to me on a daily basis so that it can be
     conveyed to the person the very next day he makes the sales, and given
     opportunity to match the patient if possible... only feedback and
     information should be sufficient."

So: **no enforcement, no blocking, no approval queue, no escalation.** This
module only ever READS. It computes what to show and returns it. Nothing here
writes to any table.

IT REPORTS ONE DAY, NEVER A BACKLOG. A cumulative total can never reach zero,
and a number that can never reach zero is a number everyone stops reading -- the
same trap already recorded for the UPI mismatch shout.

Two kinds of gap, per the owner:
  * IDENTITY   -- bills that resolve to nobody, or to several
  * PAYMENT    -- the day's declared modes against what the bank actually settled

Plus WHO WAS AT THE COUNTER, by his rule: Darpan's punch means Darpan, no punch
means Vinay, and his own selector overrides both.
"""
import collections
import csv
import os

try:
    from finance_patient_match import match_bill, read_bill_identity_json
except ImportError:                                           # pragma: no cover
    from .finance_patient_match import (match_bill,           # noqa: TID252
                                        read_bill_identity_json)

PUNCH_CSV = os.environ.get("SR_PUNCH_CSV", "/root/punches.csv")
STAFF_CSV = os.environ.get("SR_STAFF_CSV", "/root/staff_master.csv")
DEFAULT_SELLER = "darpan"
FALLBACK_SELLER = "vinay"

# The backfill boundary: before the three-identifier discipline began, an
# unmatched bill says nothing about the counter, so it is NOT a gap (D355 s3).
IDENTITY_ERA_START = os.environ.get("IDENTITY_ERA_START", "2026-06-18")


# ----------------------------------------------------------- who was there

def _staff_ids(staff_csv, name):
    ids = set()
    try:
        with open(staff_csv, encoding="utf-8-sig", errors="replace") as f:
            for r in csv.DictReader(f):
                if name.lower() in (r.get("name") or "").strip().lower():
                    try:
                        ids.add(int(r["user_id"]))
                    except (KeyError, TypeError, ValueError):
                        continue
    except OSError:
        return None                                  # cannot read -> unknown
    return ids


def counter_for_date(business_date, punch_csv=None, staff_csv=None,
                     override=None):
    """Who was at the sale counter on this date.

    The owner's rule, and it is a RULE rather than a measurement of who typed
    the bill -- so the answer always carries HOW it was decided, and his own
    selector always wins.
    """
    if override:
        return dict(seller=override, decided_by="owner", darpan_punched=None,
                    note="set by the owner")
    ids = _staff_ids(staff_csv or STAFF_CSV, DEFAULT_SELLER)
    if ids is None:
        return dict(seller=None, decided_by="unknown", darpan_punched=None,
                    note="staff master not readable - attribution pending")
    if not ids:
        return dict(seller=None, decided_by="unknown", darpan_punched=None,
                    note="no staff row matches '%s' - attribution pending"
                         % DEFAULT_SELLER)
    punched = None
    try:
        with open(punch_csv or PUNCH_CSV, encoding="utf-8-sig", errors="replace") as f:
            punched = False
            for r in csv.DictReader(f):
                try:
                    uid = int(r["user_id"])
                except (KeyError, TypeError, ValueError):
                    continue
                if uid in ids and (r.get("datetime") or "").startswith(business_date):
                    punched = True
                    break
    except OSError:
        return dict(seller=None, decided_by="unknown", darpan_punched=None,
                    note="punches not readable - attribution pending")
    return dict(seller=DEFAULT_SELLER if punched else FALLBACK_SELLER,
                decided_by="rule", darpan_punched=punched,
                note="Darpan punched" if punched
                     else "no punch for Darpan, so the counter is Vinay")


# ----------------------------------------------------------- the two gaps

def _verdict_from_link(con, row):
    """The verdict for a bill whose patient was already resolved at INGEST.

    S211, corrected after measuring the live box: `sale_item.description` is
    EMPTY on every real pharmacy row, and `patient_ref_id` is set on every one.
    The Marg parser already extracts the clinic id and the name, and
    finance_ingest.resolve_patient already links the bill to a patient_ref row.
    Re-parsing the bill text here was solving a problem that had been solved
    upstream years ago -- the S103-121 lesson: read the live code before
    assuming a feature is missing.

    So the question is not "who is this bill for", it is "is the patient it was
    linked to a REAL one from the master, or a stub the bill itself created".

      * no link at all               -> unmatched, the counter gap
      * linked to a MASTER patient   -> matched (patient_uid arrives only from
                                        the clinic PC's patient master)
      * linked to a stub with no uid -> the bill named somebody who is not in
                                        the master. Still the counter gap, and
                                        the more interesting shape of it.
      * the clinic id collides       -> ambiguous, never a clean match
    """
    pid = row["patient_ref_id"]
    if not pid:
        return _end("unmatched", [], [dict(step="link at ingest",
                       detail="this bill was never linked to a patient")])
    p = con.execute("SELECT clinic_id, name, patient_uid FROM patient_ref "
                    "WHERE id=?", (pid,)).fetchone()
    if p is None:
        return _end("unmatched", [], [dict(step="link at ingest",
                       detail="linked to a patient row that no longer exists")])
    steps = [dict(step="link at ingest",
                  detail="clinic ID %s" % (p["clinic_id"] or "(blank)"))]
    if _has_table(con, "patient_id_collision") and con.execute(
            "SELECT 1 FROM patient_id_collision WHERE clinic_id=?",
            (p["clinic_id"],)).fetchone():
        steps.append(dict(step="collision check",
                          detail="this clinic ID names more than one patient"))
        return _end("ambiguous", [dict(clinic_id=p["clinic_id"], name=p["name"])], steps)
    if p["patient_uid"]:
        steps.append(dict(step="patient master", detail="found - a real clinic patient"))
        return _end("matched_clinic_id", [], steps)
    steps.append(dict(step="patient master",
                      detail="NOT found - the bill named somebody the master "
                             "does not have"))
    return _end("unmatched", [], steps)


def _has_table(con, name):
    return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                            "AND name=?", (name,)).fetchone())


def _end(verdict, cands, steps):
    """Every chain ends by naming its verdict, whichever path produced it. The
    two paths disagreeing on their own shape is how a row ends up displayed
    with half its working missing."""
    steps.append(dict(step="verdict", detail=verdict))
    return verdict, cands, steps


def identity_gaps(con, business_date, unit="medical", env=None,
                  exclude_returns=False):
    """Every bill of the day, with its verdict and its working. Read-only.

    A SALES RETURN IS NOT A SALE. Counting the two together made the S211 tally
    report more matches than there were sales, which is the sort of small lie
    that makes a whole screen untrustworthy. Callers that are counting the
    counter's work pass exclude_returns=True; the returns get their own
    treatment in H3, tagged to the sale they reverse.
    """
    rows = con.execute(
        "SELECT s.id, s.source_ref AS bill_no, s.description, s.amount_p, s.mode, "
        "       s.disc_p, s.patient_ref_id, s.service "
        "FROM sale_item s JOIN day_entry d ON d.id = s.day_entry_id "
        "WHERE d.unit = ? AND d.business_date = ? "
        "ORDER BY s.source_ref, s.id", (unit, business_date)).fetchall()
    if exclude_returns:
        rows = [r for r in rows if not (r["service"] or "").endswith("_return")]
    out = []
    tally = dict(bills=0, matched=0, ambiguous=0, unmatched=0)
    for r in rows:
        tally["bills"] += 1
        if (r["description"] or "").strip():
            # some paths DO carry the typed text; use it when it is there
            res = match_bill(con, r["description"], business_date, env)
            v, cands, steps = res["verdict"], res["candidates"], res["steps"]
        else:
            v, cands, steps = _verdict_from_link(con, r)
            res = dict(steps=steps, candidates=cands)
        if v.startswith("matched"):
            tally["matched"] += 1
        elif v == "ambiguous":
            tally["ambiguous"] += 1
        else:
            tally["unmatched"] += 1
        if v.startswith("matched"):
            continue                                  # only gaps are listed
        # THE ROW LABEL. `source_ref` is not always the bill number -- on some
        # rows it carries an ingest reference like S186-F104-394, which is what
        # the owner saw on his card. The structured record holds the real
        # `bill_no`, so prefer it and fall back only when there is none.
        ident = read_bill_identity_json(r["description"]) or {}
        bill = (ident.get("bill_no") or "").strip() or r["bill_no"]
        # name and number, so a row can be READ and the patient CALLED without
        # opening anything. The number comes from the patient where one was
        # resolved; otherwise the bill's own last four, shown as such.
        nm = (ident.get("name") or "").strip()
        mob = ""
        pid = r["patient_ref_id"]
        if pid:
            pr = con.execute("SELECT name, mobile, phone_last4 FROM patient_ref "
                             "WHERE id=?", (pid,)).fetchone()
            if pr is not None:
                nm = nm or (pr["name"] or "")
                mob = (pr["mobile"] or "")
                if not mob and (pr["phone_last4"] or ""):
                    mob = "xxxxxx" + pr["phone_last4"]
        if not mob and ident.get("last4"):
            mob = "xxxxxx" + ident["last4"]
        out.append(dict(bill_no=bill, name=nm, mobile=mob,
                        amount_p=r["amount_p"],
                        mode=r["mode"], verdict=v,
                        entered=steps[0]["detail"] if steps else "",
                        candidates=cands, steps=steps,
                        sale_item_id=r["id"]))
    return out, tally


def declared_vs_bank(con, business_date, unit="medical"):
    """Darpan's DECLARED day figure against what the bank settled.

    S211, corrected by the owner: he types the day's UPI total himself and the
    MPR is matched against THAT. It lives in `day_line` (service, mode, amount) --
    not in `sale_item.mode`, which comes from the Marg export and which nobody
    maintains. An earlier version of this module compared sale_item.mode to the
    bank, found 'zero digital' on days the bank settled five figures, and
    reported 133,514 rupees of disagreement. **That number was an artefact of
    reading a field nobody fills.** Comparing the declared figure is the check
    the system has actually run since S179.
    """
    d = con.execute(
        "SELECT COALESCE(SUM(l.amount_p),0) p, COUNT(*) n FROM day_line l "
        "JOIN day_entry e ON e.id=l.day_entry_id "
        "WHERE e.unit=? AND e.business_date=? AND l.mode IN ('upi','card')",
        (unit, business_date)).fetchone()
    cash = con.execute(
        "SELECT COALESCE(SUM(l.amount_p),0) p FROM day_line l "
        "JOIN day_entry e ON e.id=l.day_entry_id "
        "WHERE e.unit=? AND e.business_date=? AND l.mode='cash'",
        (unit, business_date)).fetchone()
    bank = con.execute(
        "SELECT parsed_total_p p, txn_count n FROM upi_statement "
        "WHERE unit=? AND statement_date=?", (unit, business_date)).fetchone()
    bank_p = (bank["p"] or 0) if bank else None
    return dict(declared_digital_p=d["p"], declared_lines=d["n"],
                declared_cash_p=cash["p"],
                bank_settled_p=bank_p,
                bank_txn_count=(bank["n"] if bank else None),
                difference_p=(None if bank_p is None else bank_p - d["p"]),
                note=("no bank statement for this day yet" if bank_p is None else
                      "the declared figure agrees with the bank"
                      if bank_p == d["p"] else
                      "the bank settled MORE than was declared"
                      if bank_p > d["p"] else
                      "MORE was declared than the bank settled"))


def payment_gaps(con, business_date, unit="medical"):
    """The day's declared modes against what the bank actually settled.

    The bank is the arbiter (owner's S208 ruling). This does not accuse a bill;
    it shows the difference and lists the cash-marked bills that could account
    for it -- it proposes, a person disposes.
    """
    modes = {}
    for r in con.execute(
            "SELECT COALESCE(s.mode,'(none)') m, SUM(s.amount_p) p, COUNT(*) n "
            "FROM sale_item s JOIN day_entry d ON d.id = s.day_entry_id "
            "WHERE d.unit=? AND d.business_date=? GROUP BY 1", (unit, business_date)):
        modes[r["m"]] = dict(paise=r["p"] or 0, bills=r["n"])
    bank = con.execute(
        "SELECT parsed_total_p p, txn_count n FROM upi_statement "
        "WHERE unit=? AND statement_date=?", (unit, business_date)).fetchone()
    bank_p = (bank["p"] or 0) if bank else None
    entered_digital = sum(v["paise"] for k, v in modes.items() if k in ("upi", "card"))
    diff = None if bank_p is None else bank_p - entered_digital

    candidates = []
    if diff and diff > 0:
        # money the bank settled that no bill claims as digital. Cash-marked
        # bills of exactly that size are the S184 suggestion -- shown, not applied.
        for r in con.execute(
                "SELECT s.source_ref bill_no, s.amount_p FROM sale_item s "
                "JOIN day_entry d ON d.id = s.day_entry_id "
                "WHERE d.unit=? AND d.business_date=? AND s.mode='cash' "
                "AND s.amount_p <= ? ORDER BY s.amount_p DESC LIMIT 25",
                (unit, business_date, diff)):
            candidates.append(dict(bill_no=r["bill_no"], amount_p=r["amount_p"]))
    # sale_item.mode is the MARG-side mode. It is kept here as a secondary
    # signal only -- it is NOT what the day is judged on (see declared_vs_bank).
    return dict(modes=modes, bank_settled_p=bank_p,
                bank_txn_count=(bank["n"] if bank else None),
                entered_digital_p=entered_digital, difference_p=diff,
                could_account_for_it=candidates,
                note=("no bank statement for this day yet" if bank_p is None else
                      "the day agrees with the bank" if diff == 0 else
                      "the bank settled more than the bills declare" if diff > 0 else
                      "the bills declare more digital than the bank settled"))


# ------------------------------------------------- the sanctioned discounts

PD_ROUND_TOLERANCE_P = int(os.environ.get("PD_ROUND_TOLERANCE_P", "500"))


def discount_rows(con, business_date, unit="medical"):
    """Every sale to a patient holding a sanctioned pharmacy discount.

    The owner's shape: sanctioned percent, amount given, did it match. Rounding
    is EXEMPTED but RECORDED -- a row within tolerance still shows what it was,
    it is simply not counted as a breach. The ones given MORE than sanctioned
    are their own bucket, because a cluster at one percentage means a different
    rule is being applied, and that is worth knowing.
    """
    rows = con.execute(
        "SELECT s.source_ref bill, s.gross_p, s.disc_p, s.amount_p, "
        "       p.admin_pd_pct pct, p.clinic_id, p.name "
        "FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
        "JOIN patient_ref p ON p.id=s.patient_ref_id "
        "WHERE e.unit=? AND e.business_date=? "
        "AND s.service NOT LIKE '%!_return' ESCAPE '!' "
        "AND p.admin_pd_pct IS NOT NULL AND p.admin_pd_pct > 0 "
        "ORDER BY s.source_ref", (unit, business_date)).fetchall()
    out = []
    tally = collections.Counter()
    for r in rows:
        g = r["gross_p"] or 0
        given = r["disc_p"] or 0
        want = int(round(g * r["pct"] / 100.0))
        diff = given - want
        if g == 0:
            v = "no gross amount"
        elif given == 0:
            v = "none given"
        elif abs(diff) <= PD_ROUND_TOLERANCE_P:
            v = "matches"
        elif diff < 0:
            v = "short"
        else:
            v = "over"
        tally[v] += 1
        out.append(dict(bill=r["bill"], clinic_id=r["clinic_id"],
                        sanctioned_pct=r["pct"], gross_p=g,
                        sanctioned_p=want, given_p=given, diff_p=diff,
                        given_pct=(round(100.0 * given / g, 1) if g else None),
                        verdict=v,
                        rounding_exempt=(v == "matches" and diff != 0)))
    return out, dict(tally)


# ----------------------------------------------------------- the day

def day_report(con, business_date, unit="medical", env=None,
               punch_csv=None, staff_csv=None, override_seller=None,
               exclude_returns=False):
    if business_date < IDENTITY_ERA_START:
        gaps, tally = [], dict(bills=0, matched=0, ambiguous=0, unmatched=0)
        era = ("before %s the three identifiers were not being captured, so an "
               "unmatched bill here says nothing about the counter"
               % IDENTITY_ERA_START)
    else:
        gaps, tally = identity_gaps(con, business_date, unit, env,
                                    exclude_returns)
        era = None
    return dict(date=business_date, unit=unit,
                counter=counter_for_date(business_date, punch_csv, staff_csv,
                                         override_seller),
                declared=declared_vs_bank(con, business_date, unit),
                totals=tally, identity_gaps=gaps,
                payment=payment_gaps(con, business_date, unit),
                discounts=discount_rows(con, business_date, unit),
                before_identity_era=era)
