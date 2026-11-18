#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s878.py -- kit S878_RECORDS_PAGE (the parent, S484, 18-Nov-2026). F-1466, his 'good to build now' 16:46 on mock-up v6
(https://claude.ai/artifact/HpTDoxnksccZGA4Ldypddq).

/root/finance/records.py (29114ddd): the patient page _patient_html rebuilt on patient_events.events() -- the one reader
  (S876) -- as the mock-up: a folded page; the banner with the full mobile (the Call Console's mirror, as the Hub), the
  diagnosis (dx_visit, the clinical data report) and a quiet money chip; one folded line per day; the Docterz clinical line
  folded under the day (diagnosis, prescribed vs bought here, the follow-up advised and whether he came; the drugs, advice,
  tests from the kept clinical exports); the Hub's bill-line table folded under each bill; X-rays and reports opening in
  place with 'Open in a new tab'; Expand all / Collapse all / Top. The old page stays as _patient_html_s834, served when
  patient_events cannot be imported. English; no dialog (F-1464).
/root/finance/patient_events.py (4ad64172, the SANJEEVNI chat's; PLANNED line on the board): ONE added event kind 'dx' per
  visit day from dx_visit -- the diagnosis and the follow-up advised -- so the Hub's inline record shows it too (its ask of
  16:12). Nothing else of theirs touched.
Usage: python make_s878.py SRC_DIR OUT_DIR    (SRC_DIR holds records.py and patient_events.py at their FROM pins)
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"records.py": "29114ddd", "patient_events.py": "4ad64172"}

DX_BLOCK = '''    # ---- S878 (the parent): the diagnosis of each visit day and the follow-up advised (dx_feed's dx_visit, from the
    # Docterz clinical data report) -- one line, so the Hub's inline record shows it too (his word 16:12, 18-Nov)
    if _has(con, "dx_visit"):
        for r in _rows(con, "SELECT visit_date d, diagnosis_raw, std_dx, category, follow_up_date FROM dx_visit "
                            "WHERE clinic_id=? ORDER BY visit_date DESC", (cid,)):
            dx = (r["std_dx"] or "").strip()
            raw = (r["diagnosis_raw"] or "").strip()
            if dx.lower().startswith("other") and raw:
                dx = raw
            dx = dx or raw
            fu = str(r["follow_up_date"] or "")[:10]
            if not dx and not fu:
                continue
            add(r["d"], "dx", "📋", dx or "Diagnosis not written",
                (" (" + raw + ")") if raw and dx and raw.lower() != dx.lower() else "",
                sub=" · ".join(x for x in ((r["category"] or ""), ("follow-up advised " + dmy(fu)) if fu else "") if x))
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    sd, od = sys.argv[1:3]
    os.makedirs(od, exist_ok=True)
    # ---- patient_events.py: ORDER + the dx block before the slips
    with open(os.path.join(sd, "patient_events.py"), "rb") as fh:
        pe = fh.read()
    if md5(pe)[:8] != FROM["patient_events.py"]:
        print("!! patient_events.py is %s, not %s -- read the real file first (F-472)" % (md5(pe)[:8], FROM["patient_events.py"]))
        sys.exit(2)
    t = pe.decode("utf-8")
    a1 = 'ORDER = {"consult": 0, "visit": 0, "xray": 1, "proc": 2, "blood": 3, "paper": 4, "hospital": 5,'
    a2 = "    # ---- the slips: their items go under the day's line (X-ray / procedure names; the OPD slip one tap under)\n"
    for a in (a1, a2):
        if t.count(a) != 1:
            print("!! patient_events.py anchor not found once: %r" % a[:60])
            sys.exit(2)
    t = t.replace(a1, 'ORDER = {"consult": 0, "visit": 0, "dx": 0.5, "xray": 1, "proc": 2, "blood": 3, "paper": 4, "hospital": 5,   # S878: dx')
    t = t.replace(a2, DX_BLOCK + a2)
    out = t.encode("utf-8")
    with open(os.path.join(od, "patient_events.py"), "wb") as fh:
        fh.write(out)
    print("patient_events.py %s -> %s (%d -> %d bytes)" % (FROM["patient_events.py"], md5(out)[:8], len(pe), len(out)))
    # ---- records.py: the old page renamed, the new page appended
    with open(os.path.join(sd, "records.py"), "rb") as fh:
        rc = fh.read()
    if md5(rc)[:8] != FROM["records.py"]:
        print("!! records.py is %s, not %s -- read the real file first (F-472)" % (md5(rc)[:8], FROM["records.py"]))
        sys.exit(2)
    t = rc.decode("utf-8")
    a3 = "def _patient_html(con, cid):\n    p = person(con, cid)\n"
    if t.count(a3) != 1:
        print("!! records.py anchor not found once")
        sys.exit(2)
    t = t.replace(a3, "def _patient_html_s834(con, cid):                          # S878: the page before, kept as the fallback\n    p = person(con, cid)\n")
    with open(os.path.join(HERE, "s878_page.py"), "r", encoding="utf-8") as fh:
        page = fh.read()
    if not t.endswith("\n"):
        t += "\n"
    t += "\n\n" + page
    out = t.encode("utf-8")
    with open(os.path.join(od, "records.py"), "wb") as fh:
        fh.write(out)
    print("records.py %s -> %s (%d -> %d bytes)" % (FROM["records.py"], md5(out)[:8], len(rc), len(out)))


if __name__ == "__main__":
    main()
