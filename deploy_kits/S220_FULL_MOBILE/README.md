# S220_FULL_MOBILE — "phone full 10 for me and Darpan" (owner's ruling, 02-Sep 23:05)

The S180-era rule — `last4()` is *"the ONLY form of a phone number that leaves this module … never written to a
CSV, a database or a log"* — was reversed for the counter by **D356** (S211: the full mobile on Darpan's
worksheet, F-86 reversed), and `patient_ref` has carried `mobile` since S218. The one place it still bit: a bill
the ingest **parks for review** kept only the last four, so nobody at the counter could ring the patient.

**Three anchored patches, one chain:** `marg_report.py` writes a `mobile` column into the lines CSV (ten digits
or nothing; `phone_last4` untouched; its own selftest now says so — 40/40) → the ingest's adapter already stores
the whole CSV row as the parked bill's `raw_text`, so the number arrives with **no ingest change** →
`darpan_app.py` carries it → `darpan_card.html` shows it, falling back to `…last4` for exports that predate the
ruling. Proven: selftest 6/6 on a copy of the live db (a post-ruling parked bill shows the full number; a
pre-ruling one shows blank → last four); marg_report's own selftest 40/40 on the patched bytes. Three pins predicted.

**Today's seven** were parked before this change and hold only their last four. They pick up the full number
the moment 02-Sep is exported again (a second export of a day auto-applies and supersedes the first) — one
Marg export of 02-Sep tomorrow morning does it.

| file | what |
|---|---|
| `patch_marg_report_mobile_s220.py` | marg_report.py — 4 anchors (column, writer, docstring, selftest) |
| `patch_darpan_mobile_s220.py` | darpan_app.py — 1 anchor |
| `patch_card_mobile_s220.py` | darpan_card.html — 1 anchor |
| `selftest_full_mobile_s220.py` | 6 checks |
