# S426_VITALS_ARCHIVE_IN — session 284 (parent), 27-Sep-2026

**Why.** Vitals & Plan moved to the server at S423 with its two ledgers, but the sheets already printed in July (22 PDFs in `D:\clinic_writer\plan_archive` on the clinic PC) had no road to the server that keeps patient data off Drive and out of the repository.

**What.** `/root/portal/vitals_portal.py` b234627a (S423) → `db170077dce3cd82b8c1f859b76763db` (full file). Adds `archive_put()` and ONE route, `/portal/vitals/archive` (the Case Pack's own doctor gate): GET a small page, POST PDFs with a folder. Folder must be `<year>/<UID>` or `pending/NA_NA`; name must be `YYYY-MM-DD_P-YYYY-<n>_(patient|physio).pdf`; bytes must start `%PDF-` (≤5 MB); an existing file is never overwritten (same bytes → "same", different → "kept (differs)"). Files 0600, folders 0700, md5 returned per file. Nothing else changes; portal.py untouched. Restarts clinic-portal.

**Carrying.** The assistant uploads from the owner's signed-in browser, folder by folder, and checks every returned md5 against the PC's file.

**Proof.** `walk_s426.py`, 18 checks, no network (gate, placing, 0600/0700, never overwrites, seven refusals, no temp left, health count).
