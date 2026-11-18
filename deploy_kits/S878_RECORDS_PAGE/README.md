# S878_RECORDS_PAGE — his per-patient record page (F-1466) · the parent · S484 · 18-Nov-2026

**What it does.** `https://followup.dr-manoj.in/finance/records/p/<id>` rebuilt on the one reader (`patient_events.events`), to his mock-up v6 of today:

- banner: name · ID · the **full mobile** (from the Call Console mirror; last-4 as before when the mirror has none) · **Diagnosis** (latest standardised diagnosis from `dx_visit`, the earlier ones under it) · next follow-up advised · first seen · visit days · the counts;
- the money a quiet **`₹ ···`** chip, folded — a click opens the heads (consultations paid/free/concession, X-rays, procedures, pharmacy net of returns, bill discounts) and a months table;
- every day a **folded card** whose line says what happened (Consulted · X-ray · Bought medicines …) and its total; inside: the consultation (fee / free / concession), the **Docterz line** folded with the analytical use on its face (diagnosis · prescribed n, bought n here ✓ · follow-up advised → came / did not come) and the clinical lines (prescribed, dosage, advice, tests, procedures) inside; the pharmacy bills as **the Hub's table** (item · qty · pack · rate · line ₹ · batch · exp), returns in red; films and reports **open in place** with an *Open in a new tab* link;
- **Expand all · Collapse all · ↑ Top**; no dialog (F-1464); English only; the add-paper and hospital-event forms kept;
- the old page stays in the file as `_patient_html_s834` (the fallback if the reader is absent).

**Files.** `finance/records.py` 29114ddd → 274460dc (`_patient_html` renamed `_patient_html_s834`; the S878 page appended) · `finance/patient_events.py` 4ad64172 → 5c77bf96 (Sanjeevni's reader, PLANNED line D646: a `dx` event per visit with a diagnosis, ORDER 0.5, nothing else).

**Proof.** `walk_s878.py` 28/28 on a made-up root (made-up finance db, a made-up Call Console mirror via `NID_CONSOLE_DB`, a made-up clinical data report); the live files as the control: 6/28. `synth_s876.py` (S876's proof of the Hub's record panel) 39 ok, 0 failed on the new files. `walk_s834.py` (Check karein's due rule, in records.py) 34 green. `shape_s878.py`: 60 real IDs on a copy of the live database — every page 200, max 62 ms, every one with the diagnosis and the Docterz line. Rehearsed on a made-up /root: DRY · forced red at [4/5] restores both files · real · already-installed · `--undo`.

**Install (the VPS, one line):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s878kit && cp -rp /root/deploy/repo/deploy_kits/S878_RECORDS_PAGE /tmp/s878kit && bash /tmp/s878kit/install_S878_RECORDS_PAGE.sh
```
`DRY=1` before `bash` proves without placing. Undo: `bash /tmp/s878kit/install_S878_RECORDS_PAGE.sh --undo`.

**Not in this kit.** No data changes; no other route of records.py touched; the Hub's panel (S876) reads the same reader and now also carries the `dx` line.
