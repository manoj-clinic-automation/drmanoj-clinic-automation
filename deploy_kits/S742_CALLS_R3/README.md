# S742_CALLS_R3 — the Call Console to mock-up R3 (Build A) · the parent · session 397 · 07-Nov-2026

**For the owner, in two lines.** The Call Console opens with every section folded and a coloured top line (rose = needs you, amber = to check, green = clear). WhatsApps now sit in each person's timeline beside the calls; the follow-up list is cleaned (one row per patient, today's included; it closes itself when the patient comes or staff file "not coming"); Call ke baad shows the week, booked → came / awaited / never came, per staff.

## Why
The owner's "build now" (06:36 IST 07-Nov) on mock-up R3 (https://claude.ai/artifact/AwBDzfttkYPygGVcrQbTfD, v19 — R2 merged into the one PC board). His asks of 06:00 IST: the icon key short; the staff sections folded with the summary on the top line and its colour saying "open me"; the page compact. Faults: F-1106 (the follow-up box listed only patients due BEFORE today), F-1107 (the old WhatsApp follow-ups tile read a list of 13-Aug).

## Files
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/calls_console.py` | e0f9312a (S703) | see `install_S742_CALLS_R3.sh` | the kit's copy, whole: WhatsApps in each timeline (D820's rule); the follow-up list cleaned; Call ke baad; the strip's two arrows (we called back / they rang again); the R3 look. Reads only. |
| `/root/wa/portal_console.py` | 3317394c | rebuilt by `make_s742.py` | + `build_fu_all()` and its call: table `fu_all`, the whole Followups_Today feed (today's rows included). `no_shows` and the old page untouched. The builder's own selftest stays green (54/54). |
| `/root/portal/portal.py` | 5cf80f82 | rebuilt by `make_s742.py` | the *Follow-up WhatsApps* tile opens `/portal/console#followups`; the batch page stays at `/portal/wa/followups`. |

The rules, as the page applies them:
- **A WhatsApp** is answered by a delivered (or read) reply, or by an answered call of 30 s or more within 2 clinic hours. A template or a failed reply never answers. A missed call is answered only by a connected call. Call counts count calls only.
- **A follow-up** keeps one open row per patient (by mobile; a row with no mobile by its name), at its latest due date; a due date after today is left out. It closes itself on a Docterz visit on or after the due date (finance.db `patient_visit`, by clinic ID or the clinic's own mobile fingerprint), or when staff FILE "not coming". The AI hearing "not coming" with nothing filed keeps the row open, amber. Sections: Today · Grace 1–3 · Overdue 4–14 · Lapsed 15+ · Came / closed (the last 7 days). Called-of counts calls.
- **Call ke baad**: `ring_outcome.list_data` (the list's own rule), the last 7 days.

## Proven (S397, cloud workspace, made-up data only — phones 9000000xxx, names "… Test")
- `walk_s742.py` **39 of 39** green; **control** on the live calls_console.py: 35 of 37 S742 checks red.
- `browser_s742.js` in Chromium at 1366, 1920 and 390 px: no sideways scroll, every section folded on opening, Follow-ups and Call ke baad on the first PC screen, expand all / fold all, the WhatsApp chip, no script error.
- the builder: `portal_console.py --selftest` 54/54 on the made file.
- `proof_s742.py` (runs on the box in the installer, read-only, counts only): the call figures through the live and the new page must be identical for today, yesterday and 7 days; each read under 20 s; the page renders.
- Rehearsed on a made-up server: DRY · install · ALREADY · a changed live file STOPS · a tampered kit STOPS · the lock held STOPS · red after placing puts all three files back byte-identically.

## Install (on the server, after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s742kit && cp -rp /root/deploy/repo/deploy_kits/S742_CALLS_R3 /tmp/s742kit && bash /tmp/s742kit/install_S742_CALLS_R3.sh
```
## Undo
```
for f in /root/portal/calls_console.py /root/portal/portal.py /root/wa/portal_console.py; do \cp -p $f.bak_S742 $f; done && systemctl restart clinic-portal
```
**Next:** the Staff performance section (kit B), then the Patients section of the command console (a mock-up first).
