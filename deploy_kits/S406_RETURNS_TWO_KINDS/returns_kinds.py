#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""returns_kinds.py -- S406 (26-Sep-2026, D622). The Returns section of the owner's approvals page read TWO ways:
COUNTER returns (cash back over the counter) and the owner's own NON-CASH returns (goods back against a home /
procedure bill, no cash). A read layer over finance_returns_audit (the S212/S213 engine) and darpan_app's cn-detail:
it changes no money figure, no day figure, no cash or Marg reconciliation. It owns ONE table (cn_kind) and three settings.

  kind      counter | noncash. noncash when the credit note's own text names a home / procedure bill (the word lists
            noncash.home_words / noncash.proc_words, read the way day_resync and sale_check read them, from the review
            queue's kept JSON and the two identity tables -- S399's method), or the S357 cash adjustment names the
            credit note, or the patient's own bill in the window is a home / procedure bill (day_noncash_bill) or a
            ruled one (cash_bill_ruling). Stored once per credit note in cn_kind; recomputed on read while the month
            is open; the owner's flip (source 'owner', by, when) is kept.
  status    ONE word per line: ok · never bought · over-refund · discounted · unchecked · large · your OK · rejected.
            The brief named five; 'discounted' (the refund was SHORT, not over -- a different fact) and 'unchecked'
            (the audit could not run: no patient, identity needed / disputed, no lines) are the two the data forced.
  noise     a DISCOUNTED RETURN / REFUNDED MORE THAN PAID whose difference is below returns.noise_p (default Rs 20)
            or below returns.noise_pct (default 2 %) of the return reads ok -- rounding is not a finding.
  needs OK  amount >= returns.big_p (default Rs 1,000) or NEVER BOUGHT or RETURNED MORE THAN SOLD -- COUNTER returns
            only (the owner's own non-cash returns are his), from returns.act_from (S219, the past is accepted),
            undecided. cn-approve (darpan_app) is untouched: an approved item stays approved.
  the %     counter returns of the month / (the month's sale - home - procedure bills), the figures sanjeevni_cash's
            month_rows already gives the Month table.
"""
import datetime as dt
import json
import re

DDL = ("CREATE TABLE IF NOT EXISTS cn_kind ("
       " unit TEXT NOT NULL, bill_no TEXT NOT NULL,"
       " kind TEXT NOT NULL CHECK (kind IN ('counter','noncash')),"
       " why TEXT, source TEXT NOT NULL DEFAULT 'auto', decided_at TEXT NOT NULL, by TEXT,"
       " PRIMARY KEY (unit, bill_no))")
HOME_DEFAULT = "HOME MEDI"
PROC_DEFAULT = "PROSIJ,PROSEJ,PROCIJ,PROCED,PROSED,PRUSIJ"
SETTINGS = {
    "returns.noise_p": ("2000", "S406 D622 -- paise below which a refund difference is rounding, not a finding"),
    "returns.noise_pct": ("2", "S406 D622 -- per cent of the return below which a refund difference is rounding"),
    "returns.big_p": ("100000", "S406 D622 -- paise from which a counter return needs the owner's OK"),
}
CANT = ("not examinable", "identity needed", "identity disputed", "no patient attributed")
REAL = ("NEVER BOUGHT", "RETURNED MORE THAN SOLD")
_SOLD_RE = re.compile(r"sold for (\d+) paise on \S+, refunded (\d+)")


def _now():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def ensure(con):
    con.execute(DDL)


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone() is not None


def _setting(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r else default) or default
    except Exception:                                    # noqa: BLE001
        return default


def _int(con, key, default):
    try:
        return int(str(_setting(con, key, str(default))).strip())
    except (TypeError, ValueError):
        return default


def _float(con, key, default):
    try:
        return float(str(_setting(con, key, str(default))).strip())
    except (TypeError, ValueError):
        return default


def settings(con):
    return dict(noise_p=_int(con, "returns.noise_p", 2000), noise_pct=_float(con, "returns.noise_pct", 2.0),
                big_p=_int(con, "returns.big_p", 100000), act_from=(_setting(con, "returns.act_from", "") or "2026-09-02"),
                window_days=_int(con, "returns.window_days", 30))


def words(con):
    home = [w.strip().upper() for w in _setting(con, "noncash.home_words", HOME_DEFAULT).split(",") if w.strip()]
    proc = [w.strip().upper() for w in _setting(con, "noncash.proc_words", PROC_DEFAULT).split(",") if w.strip()]
    return home, proc


def head_for(text, home, proc):
    t = " ".join(str(text or "").upper().split())
    if any(w in t for w in home):
        return "home"
    if any(w in t for w in proc):
        return "procedure"
    return None


# ---------------------------------------------------------------- the credit note's own text (S399's method)
def cn_text(con, unit, date, bill):
    """The credit note's customer text where the ingest kept it: the review queue's raw JSON (by bill number), then
    identity_resolution / identity_dispute (bill_name). '' when nowhere."""
    b = str(bill or "").strip().upper()
    out = []
    if b and _has(con, "sale_item_review"):
        for raw, guess in con.execute("SELECT r.raw_text, r.guess_name FROM sale_item_review r JOIN day_entry e ON e.id=r.day_entry_id "
                                      "WHERE e.unit=? AND e.business_date=?", (unit, date)):
            try:
                j = json.loads(raw or "{}")
            except ValueError:
                j = {}
            if str(j.get("bill_no") or "").strip().upper() == b:
                out.extend([guess or "", j.get("patient_name") or "", j.get("description") or ""])
    for tbl in ("identity_resolution", "identity_dispute"):
        if b and _has(con, tbl):
            for (nm,) in con.execute("SELECT bill_name FROM %s WHERE unit=? AND UPPER(bill_no)=?" % tbl, (unit, b)):
                out.append(nm or "")
    return " | ".join(x for x in out if x)


def _patient_id(con, unit, bill):
    r = con.execute("SELECT s.patient_ref_id FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
                    "WHERE e.unit=? AND UPPER(s.source_ref)=? AND s.service LIKE '%!_return' ESCAPE '!' LIMIT 1", (unit, bill)).fetchone()
    return r[0] if r else None


def _stub(con, pid):
    try:
        from finance_returns_audit import _stub_identity          # noqa: PLC0415
        return bool(_stub_identity(con, pid))
    except Exception:                                            # noqa: BLE001
        return False


def classify(con, unit, date, bill):
    """(kind, why) from the data alone."""
    home, proc = words(con)
    b = str(bill or "").strip().upper()
    h = head_for(cn_text(con, unit, date, b), home, proc)
    if h:
        return "noncash", "the credit note's own text names a %s-medicine bill" % h
    if _has(con, "cash_adjustment") and b:
        for (reason,) in con.execute("SELECT reason FROM cash_adjustment WHERE UPPER(reason) LIKE ?", ("%" + b + "%",)):
            if head_for(reason, home, proc):
                return "noncash", "the cash adjustment that names it: %s" % str(reason or "")[:60]
    pid = _patient_id(con, unit, b)
    if pid and not _stub(con, pid):
        try:
            since = (dt.date.fromisoformat(str(date)[:10]) - dt.timedelta(days=settings(con)["window_days"])).isoformat()
        except ValueError:
            since = str(date)[:10]
        for (ref,) in con.execute("SELECT s.source_ref FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
                                  "WHERE e.unit=? AND s.patient_ref_id=? AND s.service NOT LIKE '%!_return' ESCAPE '!' "
                                  "AND e.business_date BETWEEN ? AND ?", (unit, pid, since, str(date)[:10])):
            ref = str(ref or "").strip()
            if not ref:
                continue
            r = con.execute("SELECT head FROM day_noncash_bill WHERE unit=? AND bill_no=?", (unit, ref)).fetchone()
            if r:
                return "noncash", "the patient's bill %s is a %s bill" % (ref, str(r[0] or "").replace("_", " "))
            if _has(con, "cash_bill_ruling") and con.execute("SELECT 1 FROM cash_bill_ruling WHERE unit=? AND bill_no=?", (unit, ref)).fetchone():
                return "noncash", "the patient's bill %s was paid elsewhere (ruling)" % ref
    return "counter", "cash back over the counter (no home / procedure sign)"


def month_open(con, unit, month):
    if month >= dt.date.today().isoformat()[:7]:
        return True
    return con.execute("SELECT 1 FROM day_entry WHERE unit=? AND substr(business_date,1,7)=? AND status IN ('submitted','draft') LIMIT 1",
                       (unit, month)).fetchone() is not None


def kind_of(con, unit, date, bill, recompute):
    """The stored kind (the owner's word always; the auto word when the month is closed), else classified and stored."""
    ensure(con)
    b = str(bill or "").strip().upper()
    r = con.execute("SELECT kind, why, source, by, decided_at FROM cn_kind WHERE unit=? AND bill_no=?", (unit, b)).fetchone()
    if r and (r[2] == "owner" or not recompute):
        return dict(kind=r[0], why=r[1], source=r[2], by=r[3], at=r[4])
    kind, why = classify(con, unit, date, b)
    if not r or r[0] != kind or r[1] != why:
        con.execute("INSERT INTO cn_kind (unit, bill_no, kind, why, source, decided_at, by) VALUES (?,?,?,?,'auto',?,NULL) "
                    "ON CONFLICT(unit, bill_no) DO UPDATE SET kind=excluded.kind, why=excluded.why, source='auto', "
                    "decided_at=excluded.decided_at, by=NULL", (unit, b, kind, why, _now()))
        con.commit()
    return dict(kind=kind, why=why, source="auto", by=None, at=_now())


def flip(con, unit, bill, kind, who):
    """The owner's one tap. Kept over every recompute."""
    if kind not in ("counter", "noncash"):
        raise ValueError("kind is counter or noncash")
    ensure(con)
    b = str(bill or "").strip().upper()
    con.execute("INSERT INTO cn_kind (unit, bill_no, kind, why, source, decided_at, by) VALUES (?,?,?,?,'owner',?,?) "
                "ON CONFLICT(unit, bill_no) DO UPDATE SET kind=excluded.kind, why=excluded.why, source='owner', "
                "decided_at=excluded.decided_at, by=excluded.by", (unit, b, kind, "the owner's word", _now(), who))
    con.commit()
    return dict(bill=b, kind=kind, source="owner", by=who)


# ---------------------------------------------------------------- the lines
def _diff_p(n):
    """The money difference behind a DISCOUNTED RETURN (gross - net) or a REFUNDED MORE THAN PAID (the per-pack excess
    the audit names on its lines); None for every other verdict."""
    v = n.get("verdict")
    if v == "DISCOUNTED RETURN":
        return int(n.get("refund_shortfall_p") or 0)
    if v == "REFUNDED MORE THAN PAID":
        d = 0
        for ln in (n.get("audit_lines") or n.get("lines") or []):
            if ln.get("verdict") == "REFUNDED MORE THAN PAID":
                m = _SOLD_RE.search(ln.get("detail") or "")
                if m:
                    d += max(0, int(m.group(2)) - int(m.group(1)))
        return d
    return None


def enrich(con, unit, month, notes, with_prev=True):
    """Adds to every cn-detail note: kind, kind_why, kind_source, kind_by, status, diff_p, noise, needs_ok, pending_ok,
    patient_text. Returns the section's summary."""
    ensure(con)
    st = settings(con)
    recompute = month_open(con, unit, month)
    counter, noncash = dict(n=0, p=0), dict(n=0, p=0)
    pending, pending_p = 0, 0
    for n in notes:
        k = kind_of(con, unit, n["date"], n["bill"], recompute)
        n["kind"], n["kind_why"], n["kind_source"], n["kind_by"] = k["kind"], k["why"], k["source"], k["by"]
        d = _diff_p(n)
        n["diff_p"] = d
        amt = int(n.get("amount_p") or 0)
        noise = (d is not None) and (d < st["noise_p"] or (amt and d < st["noise_pct"] / 100.0 * amt))
        n["noise"] = bool(noise)
        hist = bool(n.get("historical")) or str(n["date"]) < st["act_from"]
        big = amt >= st["big_p"]
        needs = (not hist) and k["kind"] == "counter" and (big or n.get("verdict") in REAL)
        appr = n.get("approval") or {}
        status = appr.get("status") if isinstance(appr, dict) else None
        pend = needs and (not status or status == "pending")
        n["needs_ok"], n["pending_ok"] = bool(needs), bool(pend)
        v = n.get("verdict")
        if pend:
            word = "your OK"
        elif status == "approved":
            word = "ok"
        elif status == "rejected":
            word = "rejected"
        elif v == "NEVER BOUGHT":
            word = "never bought"
        elif v in ("REFUNDED MORE THAN PAID", "RETURNED MORE THAN SOLD") and not noise:
            word = "over-refund"
        elif v == "DISCOUNTED RETURN" and not noise:
            word = "discounted"
        elif v in CANT:
            word = "unchecked"
        elif big:
            word = "large"
        else:
            word = "ok"
        n["status"] = word
        n["patient_text"] = ""
        if not n.get("name"):
            t = cn_text(con, unit, n["date"], n["bill"])
            n["patient_text"] = t.split(" | ")[0][:60] if t else ""
        tgt = noncash if k["kind"] == "noncash" else counter
        tgt["n"] += 1
        tgt["p"] += amt
        if pend:
            pending += 1
            pending_p += amt
    cs = counter_sales_p(con, unit, month)
    counter["sales_p"] = cs
    counter["pct"] = round(100.0 * counter["p"] / cs, 1) if cs else None
    out = dict(counter=counter, noncash=noncash, pending_ok=pending, pending_ok_p=pending_p, month_open=recompute,
               settings=dict(noise_p=st["noise_p"], noise_pct=st["noise_pct"], big_p=st["big_p"]))
    if with_prev:
        prev = prev_month(month)
        try:
            out["prev"] = dict(ym=prev, **month_fields(con, unit, prev))
        except Exception:                                # noqa: BLE001
            out["prev"] = dict(ym=prev)
    return out


def prev_month(month):
    try:
        y, m = int(month[:4]), int(month[5:7])
        return "%04d-%02d" % ((y - 1, 12) if m == 1 else (y, m - 1))
    except (TypeError, ValueError):
        return None


def counter_sales_p(con, unit, month):
    """The month's sale less the home / procedure bills -- sanjeevni_cash's own month row. None when it cannot answer."""
    try:
        import sanjeevni_cash as sc                      # noqa: PLC0415
        for m in sc.month_rows(con, unit):
            if m["ym"] == month:
                return int(m["sale_p"]) - int(m["home_p"]) - int(m["proc_p"])
    except Exception:                                    # noqa: BLE001
        return None
    return None


def month_notes(con, unit, month):
    """The month's returns as cn-detail sees them (the same day discovery, the same engine), reduced to what enrich needs."""
    from finance_returns_audit import returns_for_day    # noqa: PLC0415
    lo, hi = month + "-01", month + "-31"
    act_from = settings(con)["act_from"]
    days = [r[0] for r in con.execute(
        "SELECT DISTINCT business_date FROM sale_line_item WHERE unit=? AND is_return=1 AND business_date BETWEEN ? AND ? "
        "UNION SELECT DISTINCT e.business_date FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id "
        "WHERE e.unit=? AND s.service LIKE '%!_return' ESCAPE '!' AND e.business_date BETWEEN ? AND ? ORDER BY 1 DESC",
        (unit, lo, hi, unit, lo, hi))]
    notes = []
    for d in days:
        rows, _s = returns_for_day(con, d, unit)
        for r in rows:
            appr = con.execute("SELECT status, decided_by, decided_at, note FROM darpan_return_approval WHERE unit=? AND cn_bill=?",
                               (unit, r["bill"])).fetchone()
            notes.append(dict(date=d, bill=r["bill"], amount_p=r["amount_p"], verdict=r["verdict"],
                              refund_shortfall_p=r["refund_shortfall_p"], audit_lines=r["lines"], name=r["name"],
                              historical=(d < act_from),
                              approval=(dict(zip(("status", "decided_by", "decided_at", "note"), tuple(appr))) if appr else None)))
    return notes


def pending_count(con, unit, month):
    """(n, paise) of the month's counter returns that wait for the owner's OK -- the Needs-you line."""
    s = enrich(con, unit, month, month_notes(con, unit, month), with_prev=False)
    return s["pending_ok"], s["pending_ok_p"]


def month_fields(con, unit, month):
    """counter_returns_n / _p / _pct for the Month table."""
    s = enrich(con, unit, month, month_notes(con, unit, month), with_prev=False)
    return dict(counter_returns_n=s["counter"]["n"], counter_returns_p=s["counter"]["p"], counter_returns_pct=s["counter"]["pct"],
                counter_sales_p=s["counter"]["sales_p"], noncash_returns_n=s["noncash"]["n"], noncash_returns_p=s["noncash"]["p"])
