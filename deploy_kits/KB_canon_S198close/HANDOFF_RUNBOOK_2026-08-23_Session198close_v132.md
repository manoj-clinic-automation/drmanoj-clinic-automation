# HANDOFF RUNBOOK — v132 (Session 198 · the eight-kit build day · 23 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 198 — FULL build EOS)

**The owner's eight-job "club everything, automate, run independently" day.** Club 0 (the owner/Darpan money batch) was owner-moved to the end and stayed in the copy-block; Club C (WABA works · call-pop · free-text blog replies) was surveyed into the backlog. Everything else shipped.

1. **Club A — EIGHT kits installed GREEN, pins recorded as they moved (F-97):** `S198_P1` home revamp (dark theme; the health HERO + per-tile chips off the existing `tile-summary` fetch; Staff group; toTop; gate 127/127 — the v2 install's probe rolled back healthy bytes, **F-170**, fixed in v3) · `S198_H1` health checks become DOORS to their exact fix points (smoke 674) · `S198_P2` Forms & Downloads (`/portal/forms`) · `S198_P3` the Renewals tile · `S198_P4` the portal is a **PWA** (no service worker — ATT2) · `S198_P5` the duplicate Payment-Register tile removed (Janitor opens the same Sheet) · `S198_H2` the owner's live-eyes fixes (**F-171** worst-first claimed-never-sorted · **F-172** Sunday-blind push age · the renewals door; smoke 680) · `S198_G1` the gist tile filled from `console.db` (funnel / staff-AI / leads; selftest 27). **Final pins: `portal.py ab019dda3ac68e566de017c5ae536a6b` · `finance_app.py 2c99b2c6c719091deada5603fc295c90` · `portal_gist.py ef3ad196a00c2df44a7770553237a0e6`.**
2. **Club B — the purchase/NEFT layer, offline, in `D:\dr-manoj-git\NEFT_Vendor_Master\` (OUTSIDE the git tree — vendor bank data, D320/F-31):** `NEFT_Vendor_Master_v1.xlsx` (22 FY-verified vendors · dated account changes · UNVERIFIED flags for pre-April-2026 vendors unseen this FY) · `Neft_Guard.gs` in GAS "UPI Reconciliation" (daily 07:00, emails only on problems; **D325 held — the person signs and sends, the system never touches the bank**) · `make_recon.py` (fortnight-split prefill of Amir's vendor reconciliation; **July proof: 20/21 exact vs the executed NEFT, KEDAR ₹310 a genuine discrepancy**, AGARWAL SURGICALS ₹3,556 never-NEFT-paid surfaced) · `make_billcheck.py` (the staff bill-check workbook, vendor-grouped expandable rows, Correct/Wrong dropdowns, per-vendor progress; corrections harvested to `corrections_log.csv`) · the RUN/LOG bats + `RECON_SETUP.md` + PROOF workbooks. **F-173 OPEN:** the April-2025 advice file's account column is shifted against its names — the owner checks that month's bank statement.
3. **D335 MINTED AND SIGNED — the Purchase Portal** (`S198_Purchase_Portal_Design_CONTRACT.md`, v8 final; *the 14-state workflow table IS the spec*; stages PP0–PP4; Phase-2 two-witness item layer; both trial gates fail-safe; **no audit trail reaches the accountant or the bank**). **Build = the S199 flagship.**
4. **Close mechanics:** Archive → v1.45 (§S198 pure append, 834,626 prefix bytes proven identical) · Fault Register → v2.35 (F-170…F-173; reverse-proven onto `bb33585e…`) · Register → v5.43 (reverse-proven onto `2d7ca7be…`) · manifest rebuilt · `live_pins.txt` regenerated from v5.43 (A8) · the Notion session page (A9) · session docs filed to `deploy_kits/KB_canon_S198close/filed/` (F-107) · cold kit NOT due (1 of 3–5 since S197).

---

## §1 — MENTAL MODELS (added this session)

- **A probe's expected code is measured on the box or it is printed, never judged (F-170).** The S196 installer *printed* the HTTP code; S198_P1 v2 turned the same probe into a gate with an assumed pass set — and rolled back a healthy install, because the box 301s plain HTTP for good and bad bytes alike. Serves-proof belongs where it is real: import the installed module and render through `test_client`. Probes inform; gates measure.
- **The owner's eyes are a test tier (F-171 · F-172).** Two faults live since S195 — a docstring's sort that never existed, an alarm that could not read a calendar — passed every harness and fell in one live look. Budget the owner's first look as part of every UX kit's verification, and fold what he finds into the smoke the same day (674 → 680 did exactly that).
- **A false alarm is worse than no alarm (F-172, the F-121 family).** "Something is wrong" on a healthy Monday teaches the exact person the page exists for to ignore red. Age alarms count expected-activity days, never calendar days.
- **Model-generated base64 is not a file-transfer method — proven twice, loudly.** Both re-emissions of xlsx bytes corrupted (BadZipFile). The standing method is the Drive **text route + per-file total verification** (it preserves exact account digits and leading zeros; 18/18 totals matched building B1).
- **A currency-gate RED on a re-run can be the gate WORKING** — the H2 re-run refused a duplicate install of already-current bytes. Verify from the box before treating a RED as an incident.
- **Prefill from the source, verify by the person (Club B's shape, now D335's shape).** The machine assembles (recon prefill, bill-check rows, the bank letter); the human checks and signs. Every correction is logged and becomes data. That division is what the Purchase Portal industrialises.

---

## §2 — THE LIVE BACKLOG

**⭐0 — owner actions (the copy-block in the S198 close chat):**
- **Token rotation** — `FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN` (cron token also in GAS "UPI Reconciliation"). Exposed in chat 21-Aug. **Still the highest-severity open item.**
- **The first item-wise Marg purchase export from 01-08-2026** (owner-committed; the D335 prerequisite; expected to file under `_UNKNOWN` in MargArchive — the Club-3 router sample, NOT a fault).
- Darpan's Club 0 **before the August close**: signed-application scan → approve SPECIAL `0cc0b26b38c5` → the 17-Aug ₹20,000 → Staff Ledger → drawer ≈ ₹175,201; the ₹20,003 surplus entry.
- 18-Aug 8 bills ₹4,577 attribution · the correction-checklist days · July salary sheet · staff-phone **PWA installs** (now live, `S198_P4`) · verify `ToMedical` lands on the medical PC (closes **F-168**) · upload the printable forms to the Forms tile · `pip install openpyxl xlrd` on manojz · paste `Neft_Guard.gs` + enable Drive API + run `ng_setup()` · **F-173**: check the April-2025 bank statement against the vendor master · triage the Auditor's Monday report (~07:05).

**⭐1 — S199 FLAGSHIP: the Purchase Portal build (D335, PP0 → PP4).** The signed contract is the spec; nothing in it is re-litigated at build time. Add the item-wise-export router signature (Club 3) from the owner's 01-08 sample first.

**⭐2 — August month-end** — first full run on SL5–SL7 + F6 + present-request + D331/D332 + the new health doors. Watch, don't assume.

**⭐3 — carried builder backlog:** Club C — C1 WABA pending-works survey/re-enable (sender DRYRUN since F-82) · C2 call-pop (tick `call.initiated`/`answered` in MyOperator Webhooks v2; capture bodies first) · C3 free-text WABA content replies (blogs at drmanojagarwal.com in process) · B2 accountant email pack for Hemant/Shyam (awaiting owner: pack-only vs per-statement drip; the Tally "MARG FILE EXPORT" spec) · Club 4 (Amir/accountant answers) · expense-scan viewer · entry-page disabled-File explanation · vehicle module (#11) · local-PC migration roadmap (#12) · casepack saved-cases survey (#13) · refresh the repo mirrors of the live `finance/`/`portal/` trees (S180/S182-stale).

---

## §3 — INSTALL DISCIPLINE (updated this session)

The standing chain holds: hash-verified base bytes (recover live bytes by hash from kit tarballs — the repo trees are stale) · offline pre-flight (`py_compile` · `pyflakes` · `check_late_locals` · `check_row_keys`) · the seeded-store differential before any finance kit · currency gates on every live file a kit touches · `bash -n` every installer · the projection written before measuring · the publish destination read from `PUBLISH_ALL.bat`'s `REPO_DIR` (F-160) · **NEW: installer probes print, never judge (F-170) — serves-proof via importlib + `test_client` on the app's own render path** · every hash in a delivery note transcribed from `md5sum` output, never typed (F-141 — enforced again this session, caught pre-seal).

---

## §4 — THE EOS AUTOMATION BOUNDARY (held)

The assistant executed the build end-to-end (kits, gates, projections) and the full close (Archive/Register/Fault bumps with mechanical proofs, manifest, A8 pin list, A9 Notion, F-107 filing). **Owner residual: one `PUBLISH_ALL.bat` double-click, then on the box `git pull` and copy `live_pins_S198close.txt` → `/root/deploy/live_pins.txt`, then run `verify_live_pins.py` — expect GREEN, `source: VERIFIED`** (the three moved pins are in the new list; the old list would show RED drift 3 on files the box has right — that RED would be the stale-list condition F-134/A8 exists to prevent, not a fault).

---

*HANDOFF_RUNBOOK v132 · Session 198 close · supersedes v131. If §0, §2 or this end-marker is absent, this file is truncated and must not be used as canonical.*
