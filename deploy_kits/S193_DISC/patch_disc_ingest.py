#!/usr/bin/env python3
# =====================================================================
#  S193_DISC — in-place patch of /root/finance/finance_ingest.py
#
#  Two edits, both in the code path Marg pushes take:
#    A) adapter_csv row-builder: read the CSV's gross/disc columns
#       (magnitudes) into the line dict.  Missing columns -> None.
#    B) sale_item INSERT: persist gross_p / disc_p alongside amount_p.
#
#  The adapter_manual row-builder (which uses r.get(...)/confidence=1.0)
#  is deliberately NOT matched — only the csv adapter's block is.
#
#  FAIL-LOUD + IDEMPOTENT: each anchor must be present exactly once, or
#  (already patched) exactly once in its new form; otherwise nothing is
#  written and the script exits non-zero.
# =====================================================================
import sys

TARGET = "/root/finance/finance_ingest.py"

A_OLD = '''        out.append(dict(bill_no=(get("bill_no") or "").strip() or None,
                        bill_date=get("bill_date"),
                        clinic_id=cid, patient_name=name,
                        description=(get("description") or "").strip() or None,
                        amount_p=amount, kind=kind,
                        mode=(get("mode") or "").strip().lower() or None,
                        confidence=conf, raw=json.dumps(row, ensure_ascii=False)[:2000]))'''

A_NEW = '''        _grp = paise(row.get(norm.get("gross")) if norm.get("gross") else None)
        _dsp = paise(row.get(norm.get("disc")) if norm.get("disc") else None)
        out.append(dict(bill_no=(get("bill_no") or "").strip() or None,
                        bill_date=get("bill_date"),
                        clinic_id=cid, patient_name=name,
                        description=(get("description") or "").strip() or None,
                        amount_p=amount, kind=kind,
                        gross_p=(abs(_grp) if _grp is not None else None),
                        disc_p=(abs(_dsp) if _dsp is not None else None),
                        mode=(get("mode") or "").strip().lower() or None,
                        confidence=conf, raw=json.dumps(row, ensure_ascii=False)[:2000]))'''

B_OLD = '''            "INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, service, "
            "description, amount_p, mode, source, source_ref, confidence) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (eid, batch_id, unit, pid,
             service_for(unit, kind),
             ln.get("description"), ln["amount_p"], ln.get("mode"),'''

B_NEW = '''            "INSERT INTO sale_item (day_entry_id, ingest_batch_id, unit, patient_ref_id, service, "
            "description, amount_p, gross_p, disc_p, mode, source, source_ref, confidence) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (eid, batch_id, unit, pid,
             service_for(unit, kind),
             ln.get("description"), ln["amount_p"], ln.get("gross_p"), ln.get("disc_p"), ln.get("mode"),'''

PATCHES = [("adapter_csv row builder", A_OLD, A_NEW),
           ("sale_item INSERT", B_OLD, B_NEW)]


def main():
    with open(TARGET, "r", encoding="utf-8") as fh:
        src = fh.read()

    problems = []
    for label, old, new in PATCHES:
        if src.count(new) == 1 and src.count(old) == 0:
            problems.append("ALREADY PATCHED: %s" % label)
        elif src.count(old) != 1:
            problems.append("anchor '%s' found %d time(s), expected 1" % (label, src.count(old)))
    if problems:
        print("*** INGEST PATCH PREFLIGHT FAILED — nothing written:")
        for p in problems:
            print("      -", p)
        sys.exit(2)

    for label, old, new in PATCHES:
        src = src.replace(old, new, 1)

    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(src)
    print("      finance_ingest.py patched: gross_p/disc_p read + stored.")


if __name__ == "__main__":
    main()
