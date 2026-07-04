# SOP — VPS Services & Timer Jobs
## Advanced Orthopaedic Surgery Centre, Bareilly
**Drafted: Session 63 · 04 Jul 2026 · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Source of truth: Master KB v1.30 · Runbook Session 62 (v42). KB wins on any conflict.**

> **What this SOP is.** The operational guide for everything running on the clinic VPS —
> the nine always-on services and the four scheduled timer jobs. Use it when something on
> the server seems down, stale, or misbehaving. It tells you what each piece does, how to
> confirm it is healthy, what breaks it, and how to bring it back — without needing to
> remember the architecture.

---

## 1. The machine (one place, all constants)

| Item | Value |
|---|---|
| Hostname / IP | `followup.dr-manoj.in` / `93.127.195.49` |
| Host | Hostinger VPS (CyberPanel / OpenLiteSpeed / gunicorn) |
| Work directory | `/root/wa` |
| Python (ALWAYS use this) | `/root/wa/venv/bin/python3` — system `python3` lacks `gspread` |
| Secrets | `/root/wa/.env` (chmod 600) — never printed, never in Git |
| Service account | `patient-mirror@sincere-octane-500413-v8.iam.gserviceaccount.com` |
| Private alert channel | ntfy topic `drmka-yfv80gjcixa643` + Gmail (watchman path) |

**Golden rule:** every function on this box gets its own walled-off port + systemd service
+ OpenLiteSpeed proxy. They never share. If one dies, the others keep running.

---

## 2. The nine always-on services

These are meant to be running **all the time**. "Healthy" = `active (running)`.

| Service | Port | What it does |
|---|---|---|
| `wa-receiver.service` | 8095 | Receives WhatsApp **inbound** pushes from MyOperator, de-dupes, writes each to the **WA_Inbox** sheet tab. |
| `wa-send-api` (send relay) | 8096 | Sends WhatsApp messages out (templates + 24h-session free-text). |
| `call-api` (call relay) | 8097 | Places outbound OBD (click-to-call) calls. |
| `call-hook.service` | 8098 | Receives MyOperator **call-ended / call-summary** webhooks; writes PHI-clean duration rows to **Call_Durations**. Route `/mo-callhook`. |
| `clinic-portal.service` | 8099 | The staff launcher portal at `https://followup.dr-manoj.in/portal`. |
| `clinic-followup-receiver` | 8100 | Catcher that receives the follow-up workbook from the clinic PC and refreshes `Followups_Today`. |
| `wa-notifier` | — | Polls WA_Inbox ~every 30s, pushes name-only alerts to ntfy. **NOT** the same as `wa-receiver`. |
| `attendance-dashboard` | 8042 | Serves the biometric attendance dashboard (`https://attendance.dr-manoj.in`). |
| `attlistener` | — | Listens for punches from the Secureye biometric device. |

### Quick health check — are they all up?
```
systemctl is-active wa-receiver wa-send-api call-api call-hook clinic-portal \
  clinic-followup-receiver wa-notifier attendance-dashboard attlistener
```
Every line should say `active`. Anything else = that service is down → §5.

### The watchman does this automatically (S61)
`clinic-watchdog.timer` runs every **5 minutes**, checks all nine, and if any is down it
sends **ntfy + Gmail**, attempts an automatic restart, and alerts once per outage
(anti-spam). So in normal operation you learn about a dead service from your phone before
staff notice. Read-only, fail-loud, will not spam.

---

## 3. The four timer jobs (scheduled — meant to sleep)

These are **supposed** to be `inactive (dead)` between runs. That is normal — do NOT
"fix" a sleeping timer job.

| Timer | Schedule (IST) | What it does |
|---|---|---|
| `clinic-followup-push` | 22:00 / 07:00 / 11:00 | Builds & pushes the day's follow-up list into `Followups_Today`. **Replace-only / harmless to re-run.** |
| `call-recording-archive` | 02:00 | Archives yesterday's call recordings. Overnight — do NOT hand-trigger. |
| `call-transcription` | 03:00 | Transcribes archived recordings (Sarvam). Overnight — do NOT hand-trigger. |
| `clinic-watchdog` | every 5 min | The service watchman (§2). |

### Are the timers armed?
```
systemctl list-timers | grep -E 'followup-push|recording-archive|transcription|watchdog'
```
Each should show `active (waiting)` with a `NEXT` time. (Note: the `LAST` column is blank
on this box — that is a known quirk, not a fault. See §4.)

### Timer-freshness surveillance (S62 — heartbeats LIVE, checker being armed)
Because a sleeping timer can silently **fail to wake**, each of the three real timer jobs
now leaves a **heartbeat file** when it finishes:

```
cat /root/wa/heartbeats/*.hb
```
- `followup-push.hb` — stamped after each 22:00 / 07:00 / 11:00 run
- `recording-archive.hb` — stamped after the 02:00 run
- `transcription.hb` — stamped after the 03:00 run

Each shows a recent UTC timestamp. A missing or old file = that job did not run.
The checker `clinic_timer_freshness.py` (hourly) reads these and alerts on a missed run.

> **STATUS AS OF SESSION 63:** heartbeats are live on all three jobs; the checker is built
> and tested but **not yet armed** (arming is a two-phase rollout — the overnight jobs must
> seed their first heartbeats before the checker goes live, else it false-alarms). Until
> armed, a missed overnight run would still show as a missing/old `.hb` if you check by hand.

---

## 4. What "healthy" looks like (normal indicators)

- All nine `systemctl is-active` lines say `active`.
- Timers show `active (waiting)` with future `NEXT` times.
- `cat /root/wa/heartbeats/*.hb` shows recent timestamps for each job that has run since install.
- No ntfy/Gmail alert on your phone in the last few hours.
- `Followups_Today` sheet has today's rows after the morning push.
- **The blank `LAST` column in `list-timers` is NORMAL here** — systemd's own last-run
  record is wiped by reboots/reloads on this box. That is exactly why heartbeats exist.
  Do not treat a blank `LAST` as a fault, and do not try to make the checker read it.

---

## 5. Known failure modes & fix paths

### A service is down (`active` shows `failed` or `inactive`)
1. See why: `systemctl status <service> --no-pager -l` and `journalctl -u <service> -n 50 --no-pager`.
2. Restart it: `systemctl restart <service>`.
3. Confirm: `systemctl is-active <service>` → `active`.
4. The watchman usually restarts it for you within 5 minutes — but confirm it actually recovered.

### A timer job missed its run (heartbeat missing or old)
- **followup-push** (safe to re-run): `systemctl start clinic-followup-push.service` → then
  `cat /root/wa/heartbeats/followup-push.hb` shows a fresh timestamp → confirm `Followups_Today` refreshed.
- **recording-archive / transcription** (overnight, do NOT casually re-run off-schedule):
  check `journalctl -u <service> -n 50` first to see why it didn't run. If it clearly failed
  and you need the data, then `systemctl start <service>` — but these were never confirmed
  harmless to run off-schedule, so read the log before acting.

### A gunicorn service won't start
- Almost always a code error or a missing env var. `journalctl -u <service> -n 80` shows the
  Python traceback. Fix the cause; do not just keep restarting.

### After editing any code file
- `py_compile` first: `/root/wa/venv/bin/python3 -m py_compile /root/wa/<file>.py`
- Only then `systemctl restart <service>`.
- Never paste large files into the terminal — upload by WinSCP + md5 verify.

### The whole box rebooted
- All nine services should auto-start (they're `enabled`). Confirm with the §2 health check.
- Timers resume automatically (`Persistent`), so a run missed during downtime catches up.
- Blank `LAST` columns after a reboot are expected — ignore.

---

## 6. Reverting a heartbeat edit (the S62 change)

Each of the three timer *service* units got one extra `ExecStartPost=` line. To revert any one:
```
cp /root/wa/heartbeats/<unit>.service.bak /etc/systemd/system/<unit>.service
systemctl daemon-reload
```
Backups live in `/root/wa/heartbeats/`. This does not touch any job's Python code (the code
was never edited).

---

## 7. Manual fallback (if the VPS is unreachable)

- **Follow-ups:** staff work from the last good `Followups_Today` list; the doctor can
  re-run the push once the box is back.
- **Calls:** staff dial through the MyOperator IVR panel directly (the dialer relay is a
  convenience layer, not the only path).
- **WhatsApp:** panel-native automations (`new_post_call_message`, `eng_missedaftercall`)
  keep firing independently of this box.
- **Attendance:** the Secureye device stores punches locally; they sync when `attlistener` returns.

---

## 8. Emergency contacts

| For | Who |
|---|---|
| VPS / hosting | Hostinger support |
| MyOperator (calls, WABA, webhooks) | Lokesh Kumar VB (vendor engineer) |
| WhatsApp token rotation | Lokesh — **coordinate BEFORE any rotation** (breaks live automations ~24h) |

---

*Keep one copy in Notion "Clinic HQ" and one in the handoff kit. Update in the same session
any VPS service or timer is added, moved, or removed (KB discipline).*
