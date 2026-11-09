# S758_AUDIT_RUN11 — the 09-Nov weekly audit's asks

**The owner, 09-Nov-2026 07:48 IST:** *"Proceed with this work"* — on the audit's four asks (run 11, slice 1).

| ask | what was found | what changes |
|---|---|---|
| **AF-37** — the S672 deduction at ingest fails silently | `finance_ingest.py`'s savepoint swallowed any failure (`except: pass`) | a failure opens a **HIGH exception on that day** — *"do not approve this day until this clears"* — where the approver and the console look, plus a journal line; the next good ingest of the day resolves it |
| **AF-38** — "Gmail DKIM-blocks the estate's mails" | **not alerts**: the two 550 5.7.30 refusals (07/08-Nov) were copies of **spam contact-form messages** (the clinic's own copy of each still arrived). The nightly 00:07 bounce is **acme.sh failing to renew the public website's certificate every night since 01/02-Nov** (the check file answers 404) — the certificate served now ends **08-Dec-2026** | the installer LOOKS which folder the website really serves the check file from (a temporary file, removed), and only then sets acme.sh's webroot to it, renews, and reads back the certificate the site SERVES (> 60 days); else nothing changes. The acme.sh cron line now writes to a log instead of mailing a dead address |
| **ask 3** — the auditor's eyes | the bundle (10.6 MB) and db copy (11.3 MB) are past the auditor's 10 MB channel | two small owner-owned slots beside them (created on Drive from the owner's account, 09-Nov): `code_nightly.MD5SUMS` (the bundle's own manifest) and `finance_summary.json` (counts and day totals, read-only, no patient name / ID / phone / free text — 37 KB on the 09-Nov copy) |
| **AF-36** — the health mail's "last 24h" shows July | the watchman writes `[YYYY-MM-DD HH:MM:SS]`; the reader took `s[:19]`, found no time, and showed every line "to be safe" | the bracketed time is read; a line with no time is counted, not shown |
| **AF-39** — stale DECLARED-PENDING pin rows | a close step | in `close_build.py` on manojz (not this kit) |

**Proof:** the walk 16/16 on a copy of the 09-Nov database (made-up bills on 2030-03-01 — the forced failure opens the exception, a good ingest resolves it, a second failure re-opens the same row; the summary carries no name or bill number; the slots filled and read back; a missing slot is a warning; July's line gone, the recent one kept); the control on the live files red at check 1.

**The cold review (S413) — no break found; built:** the web server is restarted only after a renewal that succeeded and only if the site
still shows the old certificate, then the site is checked to answer; an unreadable served certificate changes nothing; every name on
the certificate (www too) must serve the check file; a failed renewal puts acme.sh's setting back and restarts nothing; an unreadable
crontab is never rewritten; *--undo* reverses part 1 and the one cron line only (the certificate setting stays — putting the broken
one back would only break the next renewal); the probe file is removed even on Ctrl-C. **Named to the Sanjeevni chat:** when
day_resync's 30-minute re-try does deduct a day, it should call `finance_ingest._s758_noncash_mark(con, unit, day, None)` so the new
exception closes then too (day_resync.py is theirs).

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s758kit && cp -rp /root/deploy/repo/deploy_kits/S758_AUDIT_RUN11 /tmp/s758kit && bash /tmp/s758kit/install_S758_AUDIT_RUN11.sh
```
Undo: `bash /tmp/s758kit/install_S758_AUDIT_RUN11.sh --undo`
