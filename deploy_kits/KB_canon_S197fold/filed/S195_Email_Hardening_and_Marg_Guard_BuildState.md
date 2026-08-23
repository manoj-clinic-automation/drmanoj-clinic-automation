# S195 build state — email-agent hardening (⭐5) + Marg guard-and-send (Quick-Win)

**Session 195 · 21 Aug 2026.** Two kits built offline, tested, and delivered into
the repo working copy (`D:\dr-manoj-git\...\deploy_kits\`). Neither is applied on
the box yet — owner installs. Nothing live was rebuilt without OK; maker/checker
(D325) intact; `token.txt` never read/printed.

## ⭐5 email-agent hardening — kit `deploy_kits/S195_EMAIL/`
Addresses S195 backlog #4 (owner asked S194). `email_agent.py` new md5
**`2c191082c27cb9a4acc52bb0e068aa2b`** (was `96cd7b75…`).
- (a) "Answered" now tracked by a **Gmail label** `clinic-agent-done`, not the
  read/unread flag. Poll uses Gmail raw search `subject:Q: -label:clinic-agent-done`
  (server-side narrow, no full-inbox fetch), with a per-message label re-check and
  a SUBJECT fallback if X-GM-RAW is unavailable. Label applied only AFTER a reply
  is sent → a `Q:` opened before the poll is no longer skipped (the 18:27 miss),
  and nothing is answered twice.
- (b) **Always reply, even on error** — query exceptions are caught and an error
  reply still goes out; a message is marked done only when a reply truly left (a
  send failure is retried next poll).
- Config gains `done_label` (defaults automatically — existing `email_agent.json`
  works unchanged) and `max_per_poll` (25). systemd units unchanged. Installer
  `install_s195_email.sh` backs up the old agent as `email_agent.py.bak_s195`.
- Offline-verified: compile clean; router refuses `sql UPDATE`, `rm -rf /`, any
  non-allowlisted verb; label parser correct. Live IMAP/SMTP + label round-trip
  run on the box (`--selftest`, `--once`). **→ this hardened build became live pin
  `e535c4f8…` after the folded-subject fix later in S195.**
- **Install:** `cd deploy_kits/S195_EMAIL && bash install_s195_email.sh`. If the
  S194 3-min timer is already enabled, the next poll runs the hardened agent.

## Marg Quick-Win (Method B) guard — kit `deploy_kits/S195_MARG/`
The "fail visibly, never a silent partial" gate in front of the existing sender.
- `guard_and_send.py` (md5 `6c248d5712731256c576722ad85f3ef1`) reuses
  **`marg_report.py`** (bundled, exact copy of the live `finance/marg_report.py`
  md5 `28b47d447cfd966411742055717a5c56`) so its judgment == the server's. Exit 0
  only when the file is single-day Detail, ends with `GRAND TOTAL :` (not
  truncated), arithmetic balances, and the business date is sane.
- Date rules via `--expect any|today|yesterday|YYYY-MM-DD`; `any` (default) allows
  a single-day file up to `--max-age-days 3` old, still blocking truncated /
  Summary-1 / range / stale files.
- On GREEN it also copies to `Sent\` **named by business date/period**
  (`REPORT_2026-08-19.XLS`, or `REPORT_<from>_to_<to>.XLS`) per owner request
  21 Aug; incomplete/refused files never archived. `SEND_TO_CLINIC.bat` untouched.
- `GUARD_AND_SEND.bat` wraps the loop over `D:\MARGERP\users\*\report\REPORT_1.XLS`
  → guard → only if GREEN call `SEND_TO_CLINIC.bat <file>`. `AUTO` 2nd arg
  suppresses pauses for Task Scheduler.
- **Validated against REAL exports** (staged from `D:\Downloads\MARG REPORTS CLAUDE`
  + `D:\Downloads\margsync`): 17/18/19-Aug SENT files and users 50018/61376 pass
  with correct date/bills/net/cash (confirmed 61376 = UPI-reclassified: 19-Aug
  ₹44,120 day, cash 18,790 / non-cash 25,330 vs 50018 all-cash); 1–15 & 14–15 Aug
  ranges refused; synthetic truncated / arithmetic-mismatch / Summary-1 / stale
  all refused (8/8 suite + real-file checks GREEN).
- **Setup on medical (SETUP_S195_MARG.md):** install Python + `pip install xlrd==1.2.0`;
  copy `guard_and_send.py`, `marg_report.py`, `GUARD_AND_SEND.bat` into
  `D:\SendToClinic`; reception double-clicks `GUARD_AND_SEND.bat` instead of the
  raw sender. Usable TODAY with the existing manual export. *(Superseded by the
  medical-PC leg's portable-Python packaging — see the Macro/Guard Runbook.)*

## Still pending (Marg)
1. **AutoHotkey generation macro** — blocked on ONE screen recording of a real
   Marg export on medical. *(Done in the medical-PC leg — macro calibrated.)*
2. **Task Scheduler** unattended run (`GUARD_AND_SEND.bat any AUTO`) — test once by
   hand on medical, then set the schedule time (TBD).
3. **Method A (Daily Sale v2 from `D:\MARGERP\Data` `.dbf`)** — needs the sales
   header/detail/payment `.dbf` tables on LOCAL disk. *(Retired — encryption
   negative, `S195_Marg_decrypt_partial_key.md`.)*
4. Then replicate for Lab PC / Labmate.

## Access facts confirmed S195
- Connected: `D:\dr-manoj-git` (RW, mounts in device_bash at ~/mnt/dr-manoj-git),
  `Z:\MARGERP` (list-only — full metadata now, but **contents unreadable**),
  and (granted mid-session) `D:\Downloads\MARG REPORTS CLAUDE` + `D:\Downloads\margsync`.
- Delivery mechanism works: kit tar → SendUserFile → device_commit_files to
  deploy_kits → device_bash extract + md5 verify → owner PUBLISH_ALL.bat → box.
