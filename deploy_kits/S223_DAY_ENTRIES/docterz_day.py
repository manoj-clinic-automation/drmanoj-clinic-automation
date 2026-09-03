# -*- coding: utf-8 -*-
"""
docterz_day.py -- read one `Day Revenue` sheet and return the day, computed FROM THE ROWS.

D367, the owner's ruling at the S223 open:
    "if totalling error is on docterz, sort it out, from individual entries, its their
     reporting method which is fixed, we can fix our side only"

So every figure this module returns is derived from the itemised lines. The sheet's own SUMMARY,
Cash and Online/UPI lines are read too, but ONLY so a disagreement can be logged where the owner
will never have to look at it. They are never shown and never win.

Traps this file exists to handle, every one measured on real exports, not assumed:
  * Row numbers are NOT stable. Blocks move with the length of the list above them, and the
    PROCEDURES block is absent entirely on a day with no procedures. Blocks are found by their
    banner text in column A.
  * Column meaning CHANGES per block. Mode is column F in PAID CONSULTATIONS, column E in X-RAY,
    and column E in PROCEDURES under a header that says "Note".
  * F-93: the FREE / CONCESSION list ends with three phantom rows that continue the S.N sequence
    ('nan', 'Cash', and the day's cash total as a STRING). Column C is None on all three and on
    no real line, so that is the discriminator.
  * The `vs 600` cells hold the literal text '= 600', which Excel stores as a FORMULA, so
    data_only=True returns None for them. Nothing here reads that column.
  * Clinic ID is a string. It is never coerced and never stored by this module at all.
  * The Mode vocabulary is open (Cash, Online Payment, Debit Card, Split Payment so far). An
    unknown mode is carried through under its own name rather than being folded into "online".

IDENTITY, and what changed at S223. This module originally discarded the patient name and clinic
ID entirely. The owner then asked for the per-patient table -- "with amt name and clinic id" -- and
that is his own recorded ruling for this screen: **clinic ID + NAME on the view, no mobile**
(DOCTERZ_REVENUE_PHASE1_WORKING_PAPER, owner rulings, #2). So `lines` now carries name and clinic
ID, and NOTHING ELSE about the person.

There is no mobile number anywhere in the Day Revenue sheet to carry, and none is derived. F-185
governs the REPOSITORY: no identity of any kind may appear in a kit file, a test fixture, or an
evidence file. It lives in finance.db on the box, behind the same SSO gate as every other screen
that already shows a patient by name.
"""
import re

# A payment-gateway reference is sometimes appended to the mode, e.g.
# "Online Payment pay_XXXXXXXX". It is the SAME tender; the reference is a receipt id.
# This is not cosmetic: the one row seen carrying it (29-Aug-2026, Rs 1,400) is exactly the
# row Docterz's OWN footer drops, which is why D367 rules the lines the truth and the footer
# a cross-check. The reference is stripped for the bucket and recorded in the note.
_GATEWAY = re.compile(r"\s+(?:pay|order|txn|ref)[_-][A-Za-z0-9]{6,}\s*$", re.I)

BANNERS = {
    "consult": "PAID CONSULTATIONS",
    "xray": "X-RAY",
    "proc": "PROCEDURES",
    "revisit": "FREE REVISITS",
    "concession": "FREE / CONCESSION",
}
# amount column, mode column (1-based), per block
SHAPE = {
    "consult": (4, 6),
    "xray": (4, 5),
    "proc": (4, 5),
}
SHEET_NAME = "Day Revenue"


class DayRevenueError(Exception):
    pass


def _s(v):
    return "" if v is None else str(v).strip()


def _money(v):
    """Whole rupees off the sheet -> paise. Refuses anything that is not a plain number."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(round(float(v) * 100))
    t = str(v).replace(",", "").replace("₹", "").strip()
    if not t:
        return None
    try:
        return int(round(float(t) * 100))
    except ValueError:
        return None


def _norm(s):
    return " ".join(_s(s).casefold().split())


def parse_day_revenue(ws):
    """ws: an openpyxl worksheet opened with data_only=True. Returns a dict."""
    rows = list(ws.iter_rows(min_row=1, max_col=8, values_only=True))
    if not rows:
        raise DayRevenueError("empty sheet")

    # -- the date, out of the A1 banner ------------------------------------------------
    a1 = _s(rows[0][0])
    if "·" not in a1:
        raise DayRevenueError("A1 is not the expected banner: %r" % a1[:60])
    date_txt = a1.rsplit("·", 1)[-1].strip()
    business_date = _to_iso(date_txt)
    if not business_date:
        raise DayRevenueError("could not read a date from %r" % date_txt)

    # -- locate every banner by text ---------------------------------------------------
    at = {}
    for i, r in enumerate(rows):
        a = _s(r[0])
        for key, text in BANNERS.items():
            if key not in at and a.startswith(text):
                at[key] = i
    ends = sorted(at.values()) + [len(rows)]

    def block_rows(key):
        """The itemised lines of one block: banner+2 up to a Subtotal, a blank, or the next banner."""
        if key not in at:
            return []
        start = at[key] + 2                      # banner, header, then lines
        stop = next(e for e in ends if e > at[key])
        out = []
        for r in rows[start:stop]:
            if not any(_s(c) for c in r):
                break
            if _norm(r[1]).startswith("subtotal"):
                break
            out.append(r)
        return out

    # -- the money blocks, computed from their own lines --------------------------------
    streams, tender, unknown_modes, gateway_refs = {}, {}, set(), set()
    lines = []
    for key in ("consult", "xray", "proc"):
        amt_col, mode_col = SHAPE[key]
        n = total = 0
        for r in block_rows(key):
            if _s(r[2]) == "":                   # F-93 discriminator: no clinic id, not a real line
                continue
            p = _money(r[amt_col - 1])
            if p is None:
                continue
            n += 1
            total += p
            lines.append({
                "section": key,
                "sn": int(r[0]) if isinstance(r[0], int) else n,
                "patient": _s(r[1]),
                "clinic_id": _s(r[2]),
                "amount_p": p,
                "mode": "",          # filled just below, once normalised
                "shift": _s(r[mode_col]) if mode_col < 8 else "",
            })
            raw_mode = _s(r[mode_col - 1]) or "(blank)"
            m = _GATEWAY.sub("", raw_mode).strip() or raw_mode
            if m != raw_mode:
                gateway_refs.add(m)
            tender[m] = tender.get(m, 0) + p
            lines[-1]["mode"] = m
            if _norm(m) not in ("cash", "online payment", "debit card", "credit card",
                                "net banking", "patient app", "wallet", "split payment",
                                "(blank)"):
                unknown_modes.add(m)
        streams[key] = {"count": n, "amount_p": total}

    # -- the free lists: counts only, phantoms dropped ----------------------------------
    for key in ("revisit", "concession"):
        n = 0
        for r in block_rows(key):
            if _s(r[2]) == "":
                continue             # F-93 phantom, or a line with no identity at all
            n += 1
            lines.append({"section": key, "sn": int(r[0]) if isinstance(r[0], int) else n,
                          "patient": _s(r[1]), "clinic_id": _s(r[2]), "amount_p": 0,
                          "mode": "", "shift": _s(r[3])})
        streams[key] = {"count": n, "amount_p": 0}
    phantoms = sum(1 for r in block_rows("concession") if _s(r[2]) == "")

    # -- the shift split, off its own line ----------------------------------------------
    morning = evening = None
    for r in rows[:14]:
        b = _s(r[1])
        if b.startswith("Shift split"):
            mm = re.search(r"Morning:\s*(\d+)", b)
            ee = re.search(r"Evening:\s*(\d+)", b)
            morning = int(mm.group(1)) if mm else None
            evening = int(ee.group(1)) if ee else None
            break

    # -- what the sheet SAYS, for the background check only -----------------------------
    said = {}
    for r in rows[:14]:
        b, c, d = _norm(r[1]), r[2], r[3]
        if b.startswith("grand total"):
            said["total_p"], said["count"] = _money(d), (int(c) if isinstance(c, int) else None)
        elif b == "cash":
            said["cash_p"] = _money(d)
        elif b.startswith("online"):
            said["online_p"] = _money(d)

    rows_total_p = sum(streams[k]["amount_p"] for k in ("consult", "xray", "proc"))
    rows_count = sum(streams[k]["count"] for k in ("consult", "xray", "proc"))

    def _r(p_):
        return "Rs %s" % (p_ // 100) if p_ is not None else "?"

    notes = []
    if said.get("total_p") is not None and said["total_p"] != rows_total_p:
        notes.append("sheet total %s vs rows %s" % (_r(said["total_p"]), _r(rows_total_p)))
    declared = (said.get("cash_p") or 0) + (said.get("online_p") or 0)
    if said.get("total_p") is not None and declared != said["total_p"]:
        notes.append("the sheet's own cash+online %s does not equal its own total %s (difference %s)"
                     % (_r(declared), _r(said["total_p"]), _r(abs(declared - said["total_p"]))))
    if unknown_modes:
        notes.append("unrecognised payment mode(s): %s" % ", ".join(sorted(unknown_modes)))
    if gateway_refs:
        notes.append("a gateway reference was appended to the mode on this day (%s) -- counted "
                     "under the plain tender; this is the shape Docterz's own footer drops"
                     % ", ".join(sorted(gateway_refs)))
    if "proc" not in at and streams["proc"]["count"] == 0:
        pass                                     # a day with no procedures has no block. normal.

    return {
        "business_date": business_date,
        "cons_count": streams["consult"]["count"], "cons_amount_p": streams["consult"]["amount_p"],
        "xray_count": streams["xray"]["count"], "xray_amount_p": streams["xray"]["amount_p"],
        "proc_count": streams["proc"]["count"], "proc_amount_p": streams["proc"]["amount_p"],
        "total_count": rows_count, "total_amount_p": rows_total_p,
        "morning": morning, "evening": evening,
        "free_revisits": streams["revisit"]["count"],
        "free_concession": streams["concession"]["count"],
        "f93_phantom_rows": phantoms,
        "tender": tender,
        "sheet_total_p": said.get("total_p"), "sheet_cash_p": said.get("cash_p"),
        "sheet_online_p": said.get("online_p"),
        "variance_note": " | ".join(notes),
        "lines": lines,
    }


_MONTHS = {m: i + 1 for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def _to_iso(t):
    m = re.match(r"^(\d{1,2})-([A-Za-z]{3})-(\d{4})$", t.strip())
    if not m:
        return ""
    mon = _MONTHS.get(m.group(2).lower())
    return "%s-%02d-%02d" % (m.group(3), mon, int(m.group(1))) if mon else ""
