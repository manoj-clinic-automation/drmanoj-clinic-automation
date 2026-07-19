# SYSTEM → DOCUMENTATION COVERAGE MAP (S147)

**Dr. Manoj Agarwal Clinic · Bareilly · companion to `CANONICAL_MANIFEST.md`. Answers: "when tool X needs attention, what is its wholesome reference?"**

**Legend:** ✅ wholesome single reference · 🟢 well-covered by a living spec · 🟡 operational-only (SOP/README) · ⚠ **scattered — consolidation candidate**.

## Frozen products (Tier 2 — dossier is the wholesome reference)

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| Attendance | `attendance/` | `Attendance_System_Dossier_v1_S147` + `SOP_Biometric_Attendance` | ✅ |
| Nutrition/Diet write-path | `clinic_writer/` | `Nutrition_Diet_clinic_writer_Dossier_v1_S147` | ✅ |
| Callback Tracker (core) | `dashboard/` | `Callback_Tracker_Core_Dossier_v1_S147` | ✅ |
| WABA templates | MyOperator panel | `WABA_Approved_Templates_v1_S137` | ✅ |

## Active systems (Tier 1 — spec/SOP + code is the reference)

| System | Repo | Authoritative doc | Status |
|---|---|---|---|
| Call Intelligence / verdict pipeline | `recordings-archive/` | `AI_Verdict_Layer_Master_v1_S145` + `README_call_verdict` | 🟢 comprehensive |
| Call Console / dialer + Dashboard | `dashboard/` (CallConsole, Dashboard.html) | `Call_Console_Evolution_Spec_v2_4` + `Frontend_Dashboard_Documentation_v4` + `SOP_Dashboard_AppScript` | 🟢 |
| Diagnostics / surveillance | `diagnostics-vps/`, `dashboard/Diagnostics.gs`,`Health.gs` | `Diagnostics_Surveillance_System_Spec_v2_3` | 🟢 |
| MyOperator IVR / call API | panel, `api/` | `SOP_MyOperator_IVR` + `API_QUICK_REFERENCE_CARD` + `api/` refs | 🟢 |
| OBD click-to-call | `obd/` | `OBD_ClickToCall_WORKING_Recipe` + API ref | 🟢 |
| Revenue reconciliation | `revenue-reconciliation/` | `SOP_Revenue_Reconciler` + `README` | 🟡 |
| Docterz→MyOperator converter | `converter/` | `CONVERTER_README` | 🟡 (small) |
| VPS services (general) | `followup-vps/`, `diagnostics-vps/` | `SOP_VPS_Services` + `Maintenance_SOP_System_Spec` | 🟡 |
| Portal / launcher | `portal/`, `launcher/` | `PORTAL_S139_PATCH_NOTE` + `README` | 🟡 thin |

## ⚠ Consolidation candidates (active, but docs are scattered)

| System | Repo | What exists today | Why it's a gap |
|---|---|---|---|
| **Follow-up Tracker** (clinic-PC app; the *source of follow-up intent*, D246) | `followup-tracker/` | `SOP_FollowUp_Tracker` + `FollowupTracker_WABA_Context` + assorted READMEs/guides | Major product, no single wholesome reference — knowledge is spread across a SOP, a context doc, and several READMEs |
| **Call-hook capture family** (VPS webhook capture) | `call-hook/` | `INCIDENT_…CALLHOOK_403` + API refs | Incident-prone; documented by incidents, not a standing reference |
| **WhatsApp API family** (send/receive/call/approve/receiver/notifier) | `wa-send/` `wa-receiver/` `wa-call/` `wa-approve/` `wa-diagnostics/` `notifier/` | scattered per-folder READMEs + `api/` refs + WABA context | Six small services, no one map of the family |
| Follow-up VPS ingest/receiver | `followup-vps/`, `followups-ingest/` | KB/Runbook + `INCIDENT_2026-07-01` | Thin |

## Forward (not yet a system)

- **Surgical Estimate tool (+ Consent HTML)** — in development, not in GitHub. Dossier + freeze when it ships.

---

**Recommendation.** Don't eagerly dossier active systems — you'd be documenting churn. Consolidate a scattered system into one reference **only when it next needs sustained attention, or when it stabilises toward frozen.** Priority order if/when you do: (1) Follow-up Tracker, (2) Call-hook family, (3) WhatsApp API family.

**END — Coverage Map S147.**
