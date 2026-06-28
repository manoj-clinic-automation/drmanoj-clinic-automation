# clinic-attendance

Self-hosted biometric attendance for **Dr. Manoj Agarwal Clinic, Bareilly**.
Captures Secureye terminal punches to the clinic's own VPS, computes per-person
shift-aware attendance, shows a mobile dashboard, sends daily emails, and
self-checks with a watchdog. **ONtime-cloud-free** as of 28 Jun 2026.

> ⚠️ **Private repo. No secrets, no staff financial data.** Real passwords live
> only on the VPS in `att_config.py`; salary `.xlsx` and `staff_master.csv`
> (it contains base salaries) stay in Drive/local only. See `.gitignore`.

## Components

| File | Role |
|---|---|
| `attlistener_v2.py` | **STANDALONE capture + local ack.** Receives Secureye JSON punches, replies `response_code: OK` / `ERROR_NO_CMD` itself (no upstream), writes de-duplicated `punches.csv`. systemd `attlistener`. **Critical path.** |
| `att_doctor.py` | Watchdog + safe repair. `--check` (default), `--fix`, `--cron` (email only on attention-needed). |
| `att_core.py` | Attendance engine — per-person, Sunday-aware late/early logic. |
| `att_dashboard.py` | Flask web view on port 8042 (day view + responsive month register). |
| `att_mailer.py` | Morning (11:30) + evening (21:00) summary emails via cron. |
| `att_config.py` | The only settings file. **Template here** — fill real values on the VPS only. |
| `build_staff_master.py` | Rebuilds `staff_master.csv` from the salary workbook's Staff Master sheet. |
| `*.service` | systemd unit files. |

`staff_master.csv` and `punches.csv` are **not** in the repo (data, not code).

## How the device is acked (standalone)

The Secureye S-B251CB marks a record delivered purely from one HTTP **response
header**; the body is always empty:

| Device sends | Listener replies |
|---|---|
| a real punch (`request_code: realtime_glog`, body has `user_id`+`io_time`) | `200` + header `response_code: OK` |
| heartbeat / poll (`request_code: receive_cmd`) | `200` + header `response_code: ERROR_NO_CMD` |

No call is made to any external server. De-dup key is `(user_id, datetime)` — the
same key the engine uses on read — so a device re-send can never duplicate a row.

## Deploy (VPS, AlmaLinux 9)

```bash
scp att_*.py *.service build_staff_master.py root@<vps>:/root/
nano /root/att_config.py            # password, Gmail app password, recipients
firewall-cmd --add-port=8041/tcp --permanent
firewall-cmd --add-port=8042/tcp --permanent
firewall-cmd --reload
systemctl enable --now attlistener
systemctl enable --now attendance-dashboard
crontab -e
# 30 11 * * * cd /root && /usr/bin/python3 /root/att_mailer.py morning >> /root/att_mailer.log 2>&1
# 0  21 * * * cd /root && /usr/bin/python3 /root/att_mailer.py evening >> /root/att_mailer.log 2>&1
# 0  14 * * * cd /root && /usr/bin/python3 /root/att_doctor.py --cron  >> /root/att_doctor.log 2>&1
```

Dashboard: `http://<vps>:8042` (basic auth from `att_config.py`).
Health check anytime: `python3 /root/att_doctor.py` (add `--fix` to repair).

## First push (GitHub Desktop)

1. Put the sanitized files in a folder named `clinic-attendance` (the
   `attendance_system/` contents, plus this `README.md` and `.gitignore`).
2. Confirm `punches.csv`, `staff_master.csv`, `*.xlsx`, `*.log`, `*.bak` are **absent**.
3. GitHub Desktop → File → Add local repository → choose the folder → Create repository.
4. Commit (message e.g. "Standalone listener + doctor, 28 Jun 2026") → Publish repository (Private).
