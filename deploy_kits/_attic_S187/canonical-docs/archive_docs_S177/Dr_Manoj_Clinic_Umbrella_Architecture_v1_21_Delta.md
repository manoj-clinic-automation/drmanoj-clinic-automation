# Dr Manoj Clinic — Umbrella Architecture — v1.21 (delta)

**Owner: Dr. Manoj Agarwal · Bareilly · Maintained with: Claude**

> **Delta document.** Carries forward v1.20 unchanged. Records **Session 59**: the **attendance subsystem** was brought under HTTPS on its own subdomain and its login rebuilt to a signed-cookie session. This is the first time the attendance service appears in the architecture record. No follow-up/callback boundaries changed; that dashboard stays v18.18.

---

## Session 59 delta — the attendance subsystem, formalised and hardened

### Context: a second, independent web surface
The clinic runs **two separate web surfaces** on the VPS:
1. The **follow-up/callback dashboard** (Apps Script + `CallConsole.gs`/`OutcomeLog.gs`/`WebApp.gs`; MyOperator; the whole D-series) — the main automation.
2. The **attendance web view** (`att_dashboard.py`, Flask, port 8042; reads biometric punches; `attlistener_v2.py` captures from the Secureye device) — small, read-only, previously undocumented.

They share the VPS but nothing else: different code, service, port, data. Session 59 touched **only the second**, and gave it its first formal record (KB §ATT).

### 1. HTTPS via subdomain + reverse proxy (D99)
Pattern reinforced: **an internal `http://IP:port` app that must open cleanly on a phone is fronted by a subdomain on the existing domain's SSL, via an OpenLiteSpeed reverse proxy — never by trying to certify a bare IP** (impossible; certs are issued to names). `attendance.dr-manoj.in` → CyberPanel Let's Encrypt → reverse proxy → `127.0.0.1:8042`. The ACME challenge context is preserved in the vhost so renewal is automatic. The internal service is unchanged and its raw IP URL remains as a bypass/fallback. This is the same "each function gets its own walled-off front door" discipline already used for the wa-services — now extended to attendance.

### 2. Cookie-session auth for standalone (Home-Screen) use (D100)
Architectural note on **client context**, not just server code: an iOS Home-Screen icon runs in **standalone mode** with its **own credential jar**, which does not replay HTTP Basic Auth. For any small internal page meant to live as a phone icon, the auth must be **cookie-session** (a signed cookie the standalone container keeps), not Basic Auth. Implemented with a signed 30-day cookie (`SECRET_KEY` in config, `hmac`), Basic Auth retained as a fallback for zero regression. No new service, port, or token; secret stays in `att_config.py` on the VPS (never in chat, never in GitHub).

### Boundaries unchanged
- Follow-up/callback dashboard untouched (still v18.18); WebApp.gs untouched (D34).
- One-writer-per-table intact; attendance remains **read-only** (no writes).
- No new VPS Python service (reused `attendance-dashboard`); the only new infra is one CyberPanel website + one reverse-proxy vhost.
- No PHI implications (attendance is staff punch data, not patient data).

### Single-point-of-failure flagged
The attendance code still exists **only on the VPS** (not in GitHub). Recorded as a next-session task: commit the non-secret attendance files, keep `att_config.py` gitignored.

### Open architectural item carried forward
- **Agent attribution on escalation tiles** ("shows as Staff") — unchanged from v1.20; still the top open follow-up-dashboard item; needs a read of the agent-field build before deciding display-layer vs capture-layer fix.

## Changelog
| v1.21 | 04 Jul 2026 (Session 59) | +Attendance subsystem formalised: HTTPS via subdomain + OpenLiteSpeed reverse proxy (D99); Basic Auth → signed-cookie session for iOS Home-Screen use (D100). Follow-up/callback dashboard untouched (v18.18). Attendance code flagged as VPS-only (GitHub commit pending). |
| v1.20 | 04 Jul 2026 (Session 57) | +WhatsApp tap-to-call (D97); +stale-list top-bar guard (D98). No boundary changes; WebApp.gs untouched. |
| v1.19 | (Session 56) | As previously recorded. |
