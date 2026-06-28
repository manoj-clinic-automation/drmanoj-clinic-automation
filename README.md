# drmanoj-clinic-automation

Clinic-automation system for Dr. Manoj Agarwal (Advanced Orthopaedic Surgery Centre, Bareilly).
Unifies MyOperator IVR + WhatsApp Business API + a Google Apps Script dashboard +
a Hostinger VPS (Flask relays) + Google Sheets (data spine) into one operations hub.

> **Canonical reference:** `docs/Clinic_Master_KB_SystemsRegister_v1.2.md` (the Master KB / Systems Register).
> Where any other note disagrees with it, the Master KB wins.

## Architecture in one line
Modules talk through DATA (the Google Sheet), never to each other. One universal join key
(Clinic ID + last-10 mobile). One writer per Sheet tab. Every module degrades to a fallback,
never a crash. The EMR (Docterz) is closed — CSV export only, no API, no webhooks.

## Folder map
| Folder | What it holds |
|---|---|
| `dashboard/` | Apps Script web-app project — `WebApp.gs` (cockpit, build v17.1 + `lookupPatient360`), `Dashboard.html`, `MyOperator.gs` (call-logs client), `Config.gs` (CFG + FIELD_MAP). All four files belong to ONE Apps Script project. |
| `wa-receiver/` | Inbound WhatsApp receiver (port 8095) + VPS core utility scripts + requirements. |
| `wa-send/` | Outbound WhatsApp send relay (port 8096). |
| `wa-call/` | OBD click-to-call relay (port 8097) + tests. |
| `obd/` | OBD click-to-call working recipe + helpers. |
| `notifier/` | WhatsApp → ntfy name-only alert service. |
| `converter/` | Docterz CSV → MyOperator campaign CSV converter. |
| `followups-ingest/` | Daily staff-PC ingest (Staff_Action_Today.xlsx → Followups tabs). |
| `token-rotation/` | WhatsApp token rotation plan + helper (HIGH-risk, planned). |
| `api/` | MyOperator API reference docs + Postman collection. |
| `revenue-reconciliation/` | Revenue reconciler SPEC (D11). Source samples are PHI — not in repo. |
| `docs/` | Living docs (Master KB v1.2, Umbrella v1.2), runbook v12, carryover, staff/clinic manuals, project context. |

## Security
- **No secrets in this repo.** Tokens live only in VPS `/root/wa/.env` (chmod 600),
  Apps Script Script Properties, and Apple Notes. Docs carry masked hints only.
- **No PHI in this repo.** Patient rows, revenue source files, and the service-account
  JSON are git-ignored and never committed.

## Three MyOperator systems (never mix)
- **A — Call/Logs + Recordings:** `developers.myoperator.co`, token as a body parameter.
- **B — WhatsApp send:** `publicapi.myoperator.co`, `Authorization: Bearer` (capital B) + `X-MYOP-COMPANY-ID`.
- **C — Inbound webhooks:** MyOperator POSTs to the receiver with a `?key=` gate.
- **OBD — click-to-call:** `obd-api.myoperator.co`, `x-api-key` header + secret in body.
