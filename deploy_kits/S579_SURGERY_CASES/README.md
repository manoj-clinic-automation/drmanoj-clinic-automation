# S579_SURGERY_CASES — one record per surgery (kit S579, session S325, 18-Oct-2026, D735)

**Why.** The owner, 18-Oct-2026 10:51–11:39 IST: the surgical case work on the server — papers scanned or uploaded for every surgery
(Ayushman / cashless pre-approval, file cover, billing page, implant page, discharge summary, X-rays and scans, medicolegal papers,
police memo), a ledger of implants vendor-wise and patient-wise, and the hospital's payments reconciled against each patient; cash and
credit (cashless, Ayushman, Deendayal) sorted apart; started from the Case Pack or directly; new surgeries from now.

## What he sees
- Tile **Surgery cases** (Clinic section) → `https://followup.dr-manoj.in/finance/surgery`
  - tabs All · Cash · Credit — all · Cashless · Ayushman · Deendayal; search; open / closed;
  - each case: details and stage (Planned → Pre-approval applied → Pre-approved → Admitted → Operated → Discharged → Bill / claim sent
    → Closed), ten kinds of paper with **Scan / upload** each (the shared scanner: camera, photos, or a PDF), what is still missing,
    the implants, and (his alone) the money from the hospital;
  - **Implant vendors** (his alone): one ledger per vendor, printable to share — cash cases owed to the vendor, his cash payments,
    the cheques the vendor received for credit patients (assigned to patients by him, since cheques often carry no names) and what
    is actually due to the vendor for each, so the gap is in his favour;
  - **Hospital payments** (his alone): one payment per monthly statement — scan the statement, write the amount paid against each
    patient, optionally tie it to the bank credit of the same amount.
- In the Case Pack, after choosing a patient: **→ Continue to surgery case**, which opens a new case prefilled (name, clinic ID,
  payer from the estimate, the Case Pack number).
- Shavez: the tile, the cases, the papers and the implant lines (vendor, item, vendor's bill) — no money pages, no money columns.
  Dr Bhawna: the tile is masked (the owner: private to me).

## Rules kept
- Its own unit `surgery` (shavez maker, manoj checker); its own `surg_*` tables in finance.db; patient_ref and the three bank-statement
  tables read only. Money rows are never edited — a void with its reason, then a new row. Every write is audited.
- Papers live in `/root/wa/casepack/surgery_papers/<year>/<case>/` — inside the Case Pack tree the nightly encrypted backup already
  carries whole (S424). Only a PDF or a photo is filed; the same file twice is filed once; a file is served only from that folder.
- The switch `surgery_cases.on` (on by default) closes the pages for Shavez; the owner always sees them.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s579kit && cp -rp /root/deploy/repo/deploy_kits/S579_SURGERY_CASES /tmp/s579kit && bash /tmp/s579kit/install_S579_SURGERY_CASES.sh
```
Gates → pins (finance_app 87cc4266, portal f8b059f6, Case Pack page 08807cdf) → compile on both pythons → rebuild by counted edits →
the walk on a made-up database and on a copy of the live one (53 of 53 each) → the real finance app on copies, as manoj and shavez
(10 of 10; the old files 1 of 10) → backups → place → the grants merged → the data step → both services restarted → health → the
same look on the placed files. A second run says ALREADY INSTALLED. `DRY=1` before `bash` writes nothing.

## Proof
- `walk_s579.py`: 53 checks — the gate (incl. the doctor's very first visit), numbering under a race, the Case Pack prefill, papers
  (PDF, photo, refusals, duplicates), implants (Shavez cannot write money), the vendor ledger's arithmetic, cheque and receipt
  assignment limits, the bank tie, what Shavez may not do, voids with reasons, the switch, the tabs, the audit, a path outside
  the folder. Nine broken versions each turn checks red; a missing module is red.
- `probe_s579.py`: the real finance app with the edited files, on copies.

## Undo
```
cp -p /root/finance/finance_app.py.bak_S579_87cc4266 /root/finance/finance_app.py && cp -p /root/portal/portal.py.bak_S579_f8b059f6 /root/portal/portal.py && cp -p /root/wa/casepack/casepack_page.html.bak_S579_08807cdf /root/wa/casepack/casepack_page.html && rm -f /root/finance/surgery_cases.py && systemctl restart clinic-finance clinic-portal
```
The grants file's copy is `/root/portal/tile_grants.json.bak_S579_<time>`; the surg_* tables and the 'surgery' rows are additive and
unused once the module is out.
