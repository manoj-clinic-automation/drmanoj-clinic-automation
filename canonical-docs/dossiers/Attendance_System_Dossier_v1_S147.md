# FROZEN DOSSIER — Biometric Attendance System (v1, S147)

**Dr. Manoj Agarwal Clinic · Bareilly · Tier 2 (frozen, D247) · built from live GitHub source `drmanoj-clinic-automation/attendance/` + `sops/SOP_Biometric_Attendance.md`.**

> Canonical as-built reference for the frozen Attendance product. Not read in the session loop; hash-verified only. Changing the system requires an explicit owner waiver (D34 discipline) + version bump. Operational fix-it guide (separate): `SOP_Biometric_Attendance.md` (Tier 1).

---

## 1. What it is / does

Self-hosted **biometric staff attendance**. Staff punch in/out on a Secureye device at the clinic; each punch goes to a listener on the clinic's own VPS, which records it; an engine computes per-person shift-aware attendance; a mobile dashboard shows it, daily emails summarise it, and a watchdog self-checks it. **Cloud-free (no ONtime) since 28 Jun 2026.** It runs **independently of the patient-facing systems** — a fault here does not affect calls or follow-ups.

## 2. Where it lives

- **GitHub (code):** `attendance/` in `drmanoj-clinic-automation`. Folder digest md5 `dc12f4a0f9cb921b4cf2ce7c579aae16`.

  | File | md5 | Role |
  |---|---|---|
  | `attlistener_v2.py` | `94fc58ca…` | standalone capture + local ack (**critical path**) |
  | `att_core.py` | `08a815ea…` | attendance engine (per-person, Sunday-aware) |
  | `att_dashboard.py` | `225d6d9d…` | Flask web view, port 8042 |
  | `att_mailer.py` | `7d87910d…` | morning + evening summary emails |
  | `att_doctor.py` | `048257ee…` | watchdog + safe repair |
  | `build_staff_master.py` | `d7e0110c…` | rebuilds `staff_master.csv` from salary workbook |
  | `att_config.example.py` | `a919712e…` | settings **template** (real values VPS-only) |
  | `attlistener.service` | `28390740…` | systemd unit — listener |
  | `attendance-dashboard.service` | `7b3a0cf4…` | systemd unit — dashboard |
  | `README.md` | `64360a2c…` | component/deploy reference |

- **VPS (live):** `/root/att_*.py`, `/root/*.service`, `/root/build_staff_master.py`; the only settings file `/root/att_config.py` (**secrets — VPS only, never in repo**).
- **Data (NOT in repo — data, not code):** `punches.csv`, `staff_master.csv` (**contains base salaries**), salary `.xlsx` — Drive/local only.
- **URLs:** primary `https://attendance.dr-manoj.in` (D224); fallback `http://93.127.195.49:8042/`.
- **Ports:** 8041 (listener), 8042 (dashboard). **Services:** `attlistener`, `attendance-dashboard`.
- **Cron:** `att_mailer.py morning` 11:30 · `att_mailer.py evening` 21:00 · `att_doctor.py --cron` 14:00.

## 3. How it works

- **Capture (`attlistener_v2.py`).** Receives Secureye JSON punches and **acks purely via one HTTP response header** — `response_code: OK` for a real punch (`realtime_glog`, body has `user_id`+`io_time`), `ERROR_NO_CMD` for a heartbeat (`receive_cmd`); the body is always empty. No call to any external server. De-dup key `(user_id, datetime)` — the **same key the engine reads on** — so a device re-send cannot duplicate a row. Writes `punches.csv`.
- **Engine (`att_core.py`).** Per-person, Sunday-aware late/early logic over the punches.
- **Dashboard (`att_dashboard.py`).** Flask on :8042 — day view + responsive month register, basic auth from `att_config.py`.
- **Mailer (`att_mailer.py`).** Morning (11:30) and evening (21:00) summary emails via cron.
- **Watchdog (`att_doctor.py`).** `--check` (default), `--fix` (safe repair), `--cron` (emails only when attention is needed). A separate watchman (S61) also monitors both services and auto-restarts.
- **Device.** Secureye S-B251CB marks a record delivered from the response header alone; when offline it **buffers punches locally and syncs on reconnect** — so a gap can fill itself in.

## 4. Decisions & findings that shaped it

- Went **live S59**; watchman added **S61**.
- **28 Jun 2026** — cutover to cloud-free (standalone listener + doctor; ONtime cloud dropped).
- **D224** — canonical address is `https://attendance.dr-manoj.in`.
- **F-31 (closed)** — `.gitignore` cannot untrack what git already tracks; `att_config.py` untracked and `att_config.example.py` added so real secrets never ship.
- **S139** — portal https hotfix (attendance reachable over https via the portal).

## 5. Known quirks / limits (read before ever reopening)

- The Secureye **acks via header only, empty body** — do not "fix" this by adding a response body.
- An **offline gap is not necessarily lost data** — buffered punches sync on reconnect.
- `staff_master.csv` **contains base salaries** — never commit it; Drive/local only.
- The **de-dup key `(user_id, datetime)` is shared** by listener and engine — change it on one side and you risk duplicate rows.
- Manual fallback: staff record on **paper**, reconcile once the listener is back.

## 6. Freeze note

**Frozen as of S147 / D247.** Artefact = the `attendance/` folder (digest `dc12f4a0f9cb921b4cf2ce7c579aae16`) + live VPS deployment. Not read or edited in the session loop; hash-verified only. Any change requires an **explicit owner waiver + version bump + a note**. The patient-facing systems are unaffected by this freeze. Operational guide: `SOP_Biometric_Attendance.md` (Tier 1).

---

**END — Attendance System Dossier v1 (S147).**
