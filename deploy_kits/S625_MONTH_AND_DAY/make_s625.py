#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s625.py -- S625_MONTH_AND_DAY: rebuilds the two TO files from the pinned FROM bytes by exact, counted edits.

    python3 -B make_s625.py <FROM folder> <TO folder>

Each anchor must occur exactly ONCE in its FROM file; a FROM byte other than the pin stops it; nothing else is written.
"""
import hashlib
import os
import sys

FROM_PIN = {"clinic_papers.py": "6db07c12a8ba5ab0123db2a5bee0fa7b",
            "asset_register.py": "70e35b105477cc2de5ed90c28875a05a"}

OLD_MONTH_OF = '''MONTH_OF = ("COALESCE(NULLIF(b.bill_month,''), CASE WHEN b.bill_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' THEN substr(b.bill_date,1,7) END, "
            "substr(datetime(b.created_at,'+330 minutes'),1,7), substr(b.created_at,1,7))")'''
NEW_MONTH_OF = '''S625_KEY = "papers.month_from_bill_date"     # S625 (F-980): the switch -- the moment the rule began (bills.created_at's form); absent / 'off' = the old rule
# S625 (F-980, the owner's ruling 22-Oct-2026: "Bill's own month"): a paper scanned from the switch-on counts in its bill's own month
# when the bill is dated in an earlier month than its scan (not more than 12 months before it) and the month on it is the scan month
# -- the intake's default; a person's earlier month still wins; papers scanned before the switch-on keep the months they had.
MONTH_OF = ("COALESCE(CASE WHEN COALESCE(b.created_at,'') >= COALESCE((SELECT s625.value FROM settings s625 WHERE s625.key='" + S625_KEY + "' "
            "AND s625.value GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]*'),'9999') "
            "AND COALESCE(b.bill_month,'') IN ('', substr(datetime(b.created_at,'+330 minutes'),1,7)) "
            "AND b.bill_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' "
            "AND substr(b.bill_date,1,7) < substr(datetime(b.created_at,'+330 minutes'),1,7) "
            "AND b.bill_date >= date(b.created_at,'+330 minutes','start of month','-12 months') THEN substr(b.bill_date,1,7) END, "
            "NULLIF(b.bill_month,''), CASE WHEN b.bill_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' THEN substr(b.bill_date,1,7) END, "
            "substr(datetime(b.created_at,'+330 minutes'),1,7), substr(b.created_at,1,7))")'''

EDITS = {
    "clinic_papers.py": [(OLD_MONTH_OF, NEW_MONTH_OF),
        ("""A paper counts in the month set on its bill, else its bill date, else the month it was scanned.</p>""",
         """A paper counts in the month set on its bill, else its bill date, else the month it was scanned; from 22-Oct-2026 a bill dated in an earlier month than its scan counts in its own month.</p>"""),
        ("""A paper counts in the month set on its bill; if none was set, the month of its bill date; if no date was read, the month it was scanned.</p>""",
         """A paper counts in the month set on its bill; if none was set, the month of its bill date; if no date was read, the month it was scanned. From 22-Oct-2026 a bill dated in an earlier month than its scan counts in its own month (a person's earlier month still wins).</p>""")],
    "asset_register.py": [
        # ---------------------------------------------------------------- F-976: the same month and year keep the day the record had
        ('''def compose_ym(y, m):''',
         '''def _s625_keep_day(a, col, ym01):
    """S625 (F-976): the form's month / year dropdowns give YYYY-MM-01; an edit that keeps the same month and year keeps the day the
    record had (a purchase of 28-04-2026 stays 28-04, never 01-04). A new record, or a changed month, takes the dropdowns' value."""
    try:
        old = (a[col] or "") if a is not None else ""
    except (IndexError, KeyError):
        old = ""
    if ym01 and re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", old) and old[:7] == ym01[:7]:
        return old
    return ym01


def compose_ym(y, m):'''),
        ('''        purchase_date = compose_ym(f.get("purchase_year"), f.get("purchase_month")) \\
            or (f.get("purchase_date") or None)
        coverage_start = compose_ym(f.get("coverage_year"), f.get("coverage_month")) \\
            or purchase_date''',
         '''        purchase_date = _s625_keep_day(a, "purchase_date", compose_ym(f.get("purchase_year"), f.get("purchase_month"))) \\
            or (f.get("purchase_date") or None)                                              # S625 (F-976)
        coverage_start = _s625_keep_day(a, "coverage_start", compose_ym(f.get("coverage_year"), f.get("coverage_month"))) \\
            or purchase_date'''),
        ('''        emi_start = compose_ym(f.get("emi_year"), f.get("emi_month")) or (purchase_date if emi else None)''',
         '''        emi_start = _s625_keep_day(a, "emi_start", compose_ym(f.get("emi_year"), f.get("emi_month"))) or (purchase_date if emi else None)   # S625 (F-976)'''),
        # ---------------------------------------------------------------- F-980: the paper's page says the month it counts in
        ('''<b>Month:</b> {{month_label(b['bill_month']) if b['bill_month'] else ('from the bill date' if b['bill_date'] else 'not set')}}''',
         '''{% if s625_counts and b['bill_month'] and s625_counts != b['bill_month'] %}<b>Month:</b> {{month_label(s625_counts)}} <span class=muted id=s625month>(the bill's own date — scanned as {{month_label(b['bill_month'])}}; to count it elsewhere, choose an earlier month below or correct its date)</span>{% else %}<b>Month:</b> {{month_label(b['bill_month']) if b['bill_month'] else ('from the bill date' if b['bill_date'] else 'not set')}}{% endif %}'''),
        ('''        months=_bill_months_s551(b), month_label=_month_label,                            # S435; S551: + its own month and the 12 before''',
         '''        months=_bill_months_s551(b), month_label=_month_label,                            # S435; S551: + its own month and the 12 before
        s625_counts=_s625_counts(db, bid),                                                  # S625 (F-980): the month it counts in'''),
        ('''def _month_label(ym):''',
         '''def _s625_counts(db, bid):
    """S625 (F-980): the month the paper counts in -- clinic_papers.MONTH_OF, the one rule; '' when that part is not mounted."""
    try:
        cp = globals().get("_clinic_papers")
        if cp is None or not getattr(cp, "MONTH_OF", ""):
            return ""
        r = db.execute("SELECT " + cp.MONTH_OF + " FROM bills b WHERE b.id=?", (bid,)).fetchone()
        return (r[0] or "") if r else ""
    except Exception:                                                # noqa: BLE001
        return ""


def _month_label(ym):'''),
    ],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst, out=print):
    os.makedirs(dst, exist_ok=True)
    total = 0
    for f, edits in EDITS.items():
        raw = open(os.path.join(src, f), "rb").read()
        if md5(raw) != FROM_PIN[f]:
            raise SystemExit("REFUSED: %s is %s, not the pinned %s" % (f, md5(raw)[:8], FROM_PIN[f][:8]))
        s = raw.decode("utf-8")
        for k, (a, b) in enumerate(edits, 1):
            n = s.count(a)
            if n != 1:
                raise SystemExit("REFUSED: %s edit %d -- its anchor occurs %d times (want 1)" % (f, k, n))
            s = s.replace(a, b)
            total += 1
        data = s.encode("utf-8")
        open(os.path.join(dst, f), "wb").write(data)
        out("%s: %d counted edit(s), %s -> %s" % (f, len(edits), FROM_PIN[f][:8], md5(data)))
    out("make_s625: %d counted edits in all" % total)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(build(sys.argv[1], sys.argv[2]))
