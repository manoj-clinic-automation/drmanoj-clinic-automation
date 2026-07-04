# SOP — Biometric Attendance
## Advanced Orthopaedic Surgery Centre, Bareilly
**Drafted: Session 63 · 04 Jul 2026 · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Source of truth: Master KB v1.30 · Runbook Session 62 (v42). KB wins on any conflict.**

> **What this SOP is.** The operational guide for the staff biometric attendance system —
> the Secureye device, the listener that receives punches, and the dashboard that displays
> them. Use it when punches stop recording or the attendance dashboard is down.

---

## 1. What the attendance system does

Staff punch in/out on a Secureye biometric device. Each punch is sent to a listener on the
VPS, which records it; a dashboard displays attendance. It runs independently of the
patient-facing systems — a fault here does not affect calls or follow-ups.

| Item | Value |
|---|---|
| Dashboard (primary) | `https://attendance.dr-manoj.in` |
| Dashboard (fallback) | `http://93.127.195.49:8042/` |
| Dashboard service | `attendance-dashboard` (VPS :8042) |
| Punch listener | `attlistener` (VPS) |
| Device | Secureye biometric unit at the clinic |
| Went live | Session 59 |

---

## 2. What "healthy" looks like

- The dashboard loads at `https://attendance.dr-manoj.in` and shows recent punches.
- Both services are up: `systemctl is-active attendance-dashboard attlistener` → both `active`.
- A test punch on the device appears on the dashboard within a short delay.
- The watchman (S61) is not alerting on either service.

---

## 3. Known failure modes & fix paths

### Punches not appearing on the dashboard
1. Is the listener up? `systemctl is-active attlistener`. If not: `systemctl restart attlistener`.
2. Is the device online / networked? A Secureye that lost network buffers punches locally and
   syncs when it reconnects — so a gap can fill in once connectivity returns.
3. Check the listener log: `journalctl -u attlistener -n 50 --no-pager`.

### Dashboard won't load
1. Try the fallback URL `http://93.127.195.49:8042/` — if that works, the domain/proxy is the
   issue, not the app.
2. Is the service up? `systemctl is-active attendance-dashboard` → restart if needed.
3. The watchman monitors both services and will alert + attempt restart automatically.

### Device not reading fingerprints
- Hardware/enrolment issue at the clinic — clean the sensor, re-enrol the staff member if
  needed. This is device-side, not server-side.

---

## 4. Manual fallback (system down)

- Staff record in/out **on paper** for the day; reconcile once the listener is back.
- Buffered punches on the Secureye device will sync automatically when it reconnects, so
  short outages often need no manual entry at all.

---

## 5. Emergency contacts

| For | Who |
|---|---|
| VPS listener / dashboard services | Owner (with Claude) — `SOP_VPS_Services.md` |
| Secureye device (hardware) | Device vendor / clinic IT |

---

*Keep one copy in Notion "Clinic HQ" and one in the handoff kit. Update in the same session
the attendance architecture changes (KB discipline).*
