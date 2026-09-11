# HANDOFF RUNBOOK — v170 — at the S239 close, 11-Sep-2026

**Supersedes v169 (S238 close).**

## 0 · WHAT HAPPENED

One day, one compaction, eight kits in the repository; every VPS change installed by the owner from one
line and read back GREEN. **Docterz exports are now picked up by themselves** on the tracker PC (task
DocterzPickup, D455), with `/run` kept as the fallback. **The stale call list he reported was made current
at 09:10 IST**, then both call-list pickers were fixed to choose the latest day by name (D456, F-421).
The clinical data report was **measured, not built** — his order. **Staff app phase 1** for Shavez,
Shivani, Alisha and Darpan (D457). **The August Money page** rebuilt from his reading of the print, and
part-time staff pay no leave charge (D458, D459). **August is NOT locked:** his sequence runs first (D460).
**F-242, the login loop that cost Amir a day, is closed** with AF-12 (D461). The Sanjeevni restart was
planned; items 1–3 are approved **for the next chat** (D462). **Nine findings, F-420 … F-428, four the
assistant's; F-419, F-242, AF-12 closed. Eight decisions, D455 … D462.**

## 1 · WHERE THINGS STAND

**Canon:** Archive **v1.86** · Register **v5.89** · Fault Register **v2.71** (F-0 … F-428) ·
**START_HERE_SESSION_240** · `S239_BUILD_BRIEF` · `CANONICAL_MANIFEST.md` · `MD5SUMS_ALL.txt`.
Next free **D463 · F-429**.

**Live pins (read back):** `/root/portal/portal.py` `ed558b36…` · `/root/portal/tile_grants.json` v10
`812cbbc6…` · `/root/staff_register/salary_policy.py` v1.16 `c7577174…` · `staff_register.py` v0.18
`b9a72d1a…` (unchanged) · `/root/staff_ledger.py` v3.7 `49b13f42…` (unchanged). **Not read:**
`/root/wa/push_followups_vps.py` after the sed patch — first thing at S240.
**Tracker PC:** `docterz_pickup.py` `d117786f…` · `revenue.py` `5d8f2a71…` · `push_followups_today.py`
`74122185…`.

## 2 · WHAT TO START ON

**`START_HERE_SESSION_240`** — §2a where the August lock is (ask which step; never lock for him) · §2b
Amir's exports (none since 06-Sep at 09:50 IST) · §2c read the VPS picker hash · §2d the pickup's
heartbeat · **then §3: Sanjeevni items 1–3** (missed-export check on Amir's punch days · spine cadence ·
Rung 1 backfill through the `marg-push` door, clubbed).

## 3 · THE TRAPS THIS SESSION EARNED

- **"Latest" is the business date a file is about, never when it was written (F-421).**
- **Overlapping exports need a key and a winner in code (F-420).**
- **Keep rows by what they are, not by where the table seems to end (F-422).**
- **Zero rows from a non-empty file is a failure, never a refresh (F-425).**
- **Render a permission preview from the file it installs; read the login list off the box (F-426, F-427).**
- **"Ready" names the next human step (F-428).** He corrected "August is ready to lock" twice.
- **A fix on one of two doors is not a fix** — F-242 closed only when login, home, case pack and
  WhatsApp were changed together.
- The device shell still mounts nothing; stage → container → commit → md5 worked every time.

## 4 · THE BOUNDARY

**Changed this session:** the portal sign-in (all staff), four staff home screens (tiles), the August
Money page, the tracker PC (pickup task, three files), the VPS call-list picker. **Not changed:** the
staff ledger, the reconciler, the Docterz reader on the VPS, manojz, the medical PC. Marg is never
written to. **His PC tidy** is a script he runs (`D:\dr-manoj-git\TIDY_TO_DELETE_S239.bat`): Recycle Bin
only, proven-safe folders only, log first.

*HANDOFF_RUNBOOK v170 · S239 close · 11-Sep-2026.*
