# S834_XRAY_DUE_RULE — X-ray photos count only once they are due (the parent, S462, 14-Nov-2026) — D979 item 1

**The rule (the plan `S450_XRAY_LAB_FILING_STUDY.md` §I point 1, the approved mock-up `https://claude.ai/artifact/W5TAwHRWP5zFBpN9HtqFhB`):**
a **morning** X-ray is due at **15:00 the same day**; an **evening** X-ray at **15:00 the next day** — the shift is Docterz's own
(`clinic_day_line.shift`, written by `docterz_day.py` from the X-ray block's own column; the X-ray line first, then any line of
that patient that day; when both shifts appear, evening). A slip with no Docterz line yet (Docterz's export comes in the evening)
goes by its own time: typed that day before 16:00 = morning, else evening. **Nothing is pending before it is due.** A photo
filed for the patient on the slip's day **or the two days after** counts. The 3 / 6 pm notice looks back **7 days**, not to 23-Sep.

**One rule, four places, byte-equal (the walk proves it):**
| where | file | before | now |
|---|---|---|---|
| the 3 / 6 pm phone notice | `/root/finance/xray_photo_nudge.py` `73d5a43f → 20823798` | every slip from 23-Sep through today, photo the same day | due only, 7 days back, photo within 2 days |
| Report baaki (`/finance/slips/pending?t=xray`) | `/root/finance/slip_log.py` `b47a5ded → 231aebde` | every slip; *der ho gayi* after next noon | due only; *photo baaki* once due, *der ho gayi* a day after |
| Check karein's "X-ray taken, no file" | `/root/finance/records.py` `b81e4e8f → 29114ddd` | up to yesterday, same day | due only, today included, within 2 days |
| reception's Aaj ka kaam (`alisha.xray_photo`) | `claude_code_briefs/DUTY_MAP.json` v24 → **v25** (+ `DUTY_MAP.md` row) | yesterday and older since 23-Sep; red from 1 day | due only, 7 days back; `allowed_days` 1 → 2, so red comes about a day after due, as Report baaki's *der ho gayi* |

Unchanged on purpose (as before S834): *X-ray not done* -- `records.py` reads its own answers (`record_check`), `slip_log.py` reads `pend_mark`, the
notice and the duty both; a picture already in the folder -- the notice skips `xray_filing` planned/done, Report baaki and Check karein
planned/check (Report baaki shows it as *file ho rahi hai*), the duty counts it until filed. A patient-day with several slips takes its
earliest due. A Docterz line with no slip: its X-ray shift, else any line's that day, else evening. No page's look changes. `alisha.xray_photo` has no
`aaj_seed.REWRITE` piece (F-1024: nothing to fit); DUTY_MAP is shared with the Sanjeevni chat — PLANNED line on `board/_numbers` (v1500).

**Live shape (the 14-Nov 03:15 database copy, counts only):** at 13-Nov 15:00 the notice said 3 today / 20 older → now 1 / 5; the duty
20 since 26-Sep → 6 since 09-Nov; Report baaki 23 → 21; Check karein 22 → 23 (today's due morning X-rays now in).

**Install (after the publish; one line on the server):**
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s834kit && cp -rp /root/deploy/repo/deploy_kits/S834_XRAY_DUE_RULE /tmp/s834kit && bash /tmp/s834kit/install_S834_XRAY_DUE_RULE.sh`
`DRY=1` before `bash`: every gate, the walk and the control; nothing live changes. Undo: `bash /tmp/s834kit/install_S834_XRAY_DUE_RULE.sh --undo`
(refuses if a later change is on any of the three files).

**Proof:** `walk_s834.py` on a copy of the live database with 14 made-up patients (ZZ9xxx, January 2027) at four clock times —
34 checks green on the new files; **the control (the live files and the v24 map) 34 red**; new files with the v24 map: the 6 duty checks red;
two mutations (Report baaki timed from the first slip; a Docterz-only blank shift sent to evening) go red. The installer runs the walk and
the control (the live files with the repository's v25 map: 5 green / 29 red) on the server before placing. A cold second reader: SAFE TO
INSTALL; its five points built in (a guarded undo; the duty's red timing; the Docterz-only fallback; the earliest-due slip; the walk's edges).
Note: the duty map goes live at the `git pull`, before the installer; if a gate stops it, the duty runs the new rule a while alone.
