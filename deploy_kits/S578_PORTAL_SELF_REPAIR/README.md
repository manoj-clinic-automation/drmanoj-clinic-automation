# S578_PORTAL_SELF_REPAIR — the portal-down flow made automatic (kit S578, session S325, 18-Oct-2026, D734)

**Why.** The owner, 18-Oct-2026 07:43 IST: *"automate the steps as much as possible, so that when I need to run it, it detects
the message and the flow starts automatically till as much as it can go. And prompt me accurately for each step."*
His two decisions, 18-Oct ~09:55 IST: **yes**, the server may restart its own stuck parts by itself (at most once an hour each);
**yes**, the watcher may start or restart the whole server through Hostinger (at most once an hour).

## What changes

**On the server (this kit's one install line):**
- `/root/deploy/clinic_doctor.py` af696c77 → 2.0. It gains `clinic-doctor --auto`:
  - the same repair as the manual run, but **at most one restart per part per hour**;
  - a part switched off on purpose (stopped **and** disabled) is left alone; a part still starting up is left alone;
  - nothing at all while an install holds the build lock, in the first 5 minutes after boot, or while
    `/root/deploy/_off/DOCTOR_AUTO_OFF` exists;
  - the web server is restarted only when a **clinic** address fails, never for the website alone, and never while a part
    behind it is still down (that last rule also applies to the manual run: a web-server restart cannot cure a stopped app);
  - **a line to his phone only** when it fixed something, could not fix something (then once an hour while it lasts),
    or things came back after a failure — through the watchman's own alert address, never printed;
  - its log line only when something was not right; its status in `/root/deploy/clinic_doctor_status.json` every run.
  The manual `clinic-doctor` and `clinic-doctor --check` work as before.
- `/etc/systemd/system/clinic-watchdog.service.d/s578-doctor-first.conf` (new): **the repair runs first on the watchman's own
  5-minute timer**, then the watchman reports what is still down. So a part the repair fixes never reaches his phone as
  "DOWN". The watchman's own files are not edited.
- `/root/deploy/_off/` (new, empty): `touch /root/deploy/_off/DOCTOR_AUTO_OFF` stops the automatic repair; removing the file
  starts it again. The manual command is never stopped by it.

**In his Apps Script project *Clinic Portal Watcher* (edited in the editor; `Clinic_Portal_Watcher.gs` is the copy):**
- portal down, website up (server on): it waits 15 minutes for the server's own repair, then one alert — step 3 of the guide.
- portal and website down (whole server off or stuck), with `HOSTINGER_KEY` in its Script Properties:
  - Hostinger busy (the server locked, or a Hostinger action still open — the nearest the API has to a maintenance notice)
    → nothing pressed; one plain line; an alert only if still so after an hour;
  - **stopped → start** after 10 minutes down; **running but not answering → restart** after 15 minutes; at most one press an
    hour; 15 minutes' grace after a press; then one plain line "started / restarted it automatically" and, when it is back,
    "back — the watcher started it at …";
  - suspended, error or anything else → nothing pressed; one alert naming the state (step 4);
  - the key refused or Hostinger unreachable → one alert, step 4, saying why.
  - An alert (high) only when the automatic steps did not work, opening the guide at the step (`#s3`, `#s4`).
- Without `HOSTINGER_KEY` it behaves as S573 did.
- Every attempt goes to the Script Property `log` (the newest 30 lines, IST). `testHostinger()` reads Hostinger once and
  presses nothing.
- Hostinger's API (from Hostinger's own published spec, `github.com/hostinger/api`): `GET /api/vps/v1/virtual-machines`,
  `GET …/{id}` (`state`, `actions_lock`), `GET …/{id}/actions`, `POST …/{id}/start`, `POST …/{id}/restart`, Bearer token from
  hPanel → Profile → API. A token has the owner's full rights (no VPS-only scope), so it lives only in Script Properties.

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s578kit && cp -rp /root/deploy/repo/deploy_kits/S578_PORTAL_SELF_REPAIR /tmp/s578kit && bash /tmp/s578kit/install_S578_PORTAL_SELF_REPAIR.sh
```
- `DRY=1` before `bash` runs every gate, the walk and the control, and writes nothing.
- Gates: SUMS → build lock → compile → the walk on the server (55 of 55) → pins (the live file af696c77, the wrapper e22da9c9,
  the watchman's unit b3021bd1) → the control (the same walk on the live file must go red) → backup → place → read-back →
  daemon-reload → systemd shows the hook → housekeeping (`/tmp/s573kit`, `/tmp/s576kit`) → one read-only check → one
  watchman round. No service is restarted by the installer. A second run says ALREADY INSTALLED.

## The walks
- `walk_s578.py` — 55 checks: S573's 22 (the manual run unchanged) plus D2 and 32 for `--auto` (the hour rule, the switch,
  the build lock, boot, disabled parts, starting parts, the website-only rule, the phone lines and their once-an-hour rule,
  secrets never printed or logged). The live S573 file scores 30 of 55; seven broken versions each turn checks red.
  S573's own walk still scores 22 of 22 on the new file.
- `walk_watcher_s578.js` — 27 checks, the real watcher script in Node against a made-up Google and Hostinger with a moving
  clock. The live S573 watcher scores 8 of 27; six broken versions each turn checks red.

## Undo
```
rm -f /etc/systemd/system/clinic-watchdog.service.d/s578-doctor-first.conf && systemctl daemon-reload && \cp -p /root/deploy/clinic_doctor.py.bak_S578_af696c77 /root/deploy/clinic_doctor.py
```
The watcher: paste the S573 copy (`deploy_kits/S573_PORTAL_DOWN_FLOW/Clinic_Portal_Watcher.gs`) back into the editor, or
simply delete `HOSTINGER_KEY` from its Script Properties (it then behaves as S573).
