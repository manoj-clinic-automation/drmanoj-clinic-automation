# PORTAL WHATSAPP + SURGICAL CASE PACK — SUBSYSTEM DOSSIER v1 (S172)

**Dr. Manoj Agarwal Clinic · Bareilly · Tier 1 · sole reference for the in-portal Case Pack, the shared WhatsApp sender, and the follow-up batch sender. Built Session 172. Read on demand when any of these three touch a task.**

> All three ship as **routes inside the existing clinic portal** (`clinic-portal.service`, port 8099, `/root/portal/portal.py`) — no new service, no subdomain, no web-server config. UI is served from disk and editable in place (D312). Live-file md5s are Register-pinned (F-31 keeps DATA out of docs).

---

## 0 · One-screen map

| Piece | Live file | md5 (S172) | Kind |
|---|---|---|---|
| Portal (routes + tiles + guards) | `/root/portal/portal.py` | `2cc42372867bad90a9cec455f81bcd10` | code (committable) |
| Case Pack logic | `/root/portal/casepack_portal.py` | `341404d7e6d054b4c49fae09d59ea13b` | code |
| WhatsApp sender (canonical) | `/root/portal/portal_wa.py` | `34994b235c95a7c611996738ab14bdd1` | code |
| Follow-up batch | `/root/portal/portal_followups.py` | `98547bc41869360bf224b190fc27cc5d` | code |
| Case Pack page (dark) | `/root/wa/casepack/casepack_page.html` | `161d3e89da6c4ed90581bf9db1818b40` | UI (disk-served) |
| WA widget | `/root/wa/wa_portal/wa_widget.js` | `36cb7aa3a52826a5827a5b6739e2b80a` | UI |
| WA page | `/root/wa/wa_portal/wa_page.html` | `0f5ae827519dd842b341d32762a61a24` | UI |
| Follow-up page | `/root/wa/wa_portal/followups_page.html` | `9c22db64f70b431e7aea620390d0b895` | UI |

**Install chain this session:** portal `d74aa3f9` (console v3 FINAL, S171) → `931adf6e` (casepack) → `faf13f7c` (WhatsApp sender) → `2cc42372` (follow-up batch + A.1 date-pickers). VPS backups: `portal.py.bak-S172`, `.bak-S172wa`, `.bak-S172fu`.

**PHI stores (gitignored — F-31/F-49, MANDATORY before any commit):**
- `/root/wa/casepack/` — `case_ledger.csv` + `case_archive/` (bundles + consents). 12 PC cases migrated in.
- `/root/wa/wa_portal/wa_portal_sends.csv` — every send logged (sole writer = `portal_wa`).
- `/root/wa/followups/` — the daily push target for `Staff_Action_Today_*.xlsx`.

**Config (secrets — `/root/portal/portal_config.py`, VPS only, never in any doc):**
`MYOP_AUTH_TOKEN` (same value as the tracker's `WA_TOKEN`, sha8 `d47a090a`) · `PORTAL_WA_DRYRUN` (default `"1"` = SAFE/TEST; `"0"` = live) · `PORTAL_WA_USERS` (default `manoj`) · `PORTAL_CASEPACK_USERS` (default `manoj`) · `PORTAL_FOLLOWUP_DIR` (optional override; default `/root/wa/followups/`).

---

## 1 · Surgical Case Pack — in portal (D309)

**Why:** the Case Pack moved off the clinic PC into the portal so it is reachable on the Fold anywhere; the PC tool stays as an **emergency fallback**.

**Routes** (all doctor-gated by `casepack_required`): `/portal/casepack` (page) · `/portal/casepack/search` · `/portal/casepack/cases` · `/portal/casepack/case/<id>` · `/portal/casepack/save`.

**Auth:** `casepack_required` — SSO user must be in `PORTAL_CASEPACK_USERS` (default `manoj`); a legacy trusted device is also allowed. Bhawna's mask hides the tile.

**Data:** patient search reads `console.db` `patients` table **READ-ONLY** (`mode=ro`) — fields phone10 / name / age / gender / clinic_id / patient_uid. Case bundles, consents and the ledger WRITE to `/root/wa/casepack/` (portal is sole writer). The printable consent is kept white for printing; the rest of the page is the teal-dark theme (owner-chosen).

**Tiles:** "Surgical Case Pack" in the Clinic section (doctor-only) + "Case Pack · PC fallback" in Clinic-PC tools.

---

## 2 · Shared WhatsApp sender (D310) — the ONE sender

**System B MyOperator WABA.** Base `https://publicapi.myoperator.co` · `Authorization: Bearer <MYOP_AUTH_TOKEN>` (capital B) + `X-MYOP-COMPANY-ID: 68384350414b9847` · send `POST /chat/messages` · `phone_number_id 1090067637530949`.

**Template-family rule (critical):**
- `drmanoj_*` templates → **numeric** body keys `"1","2","3"`, language `en`.
- all others → **named** keys (`var_1`, `var_2` …) at the template's OWN language.

**10 manually-sendable approved templates** (4 panel-automation templates deliberately excluded):
numeric — `drmanoj_post_visit`[1=name] · `drmanoj_followup_tomorrow`[1,2=date] · `drmanoj_followup_due`[1,2] · `drmanoj_followup_missed`[1,2] · `drmanoj_followup_dropout`[1,2,3=days];
named — `appointment_confirmation_ortho`[var_1,var_2=datetime, en] · `appointment_reminder_1day_ortho`[var_1,var_2, en] · `reschedule_confirmation`[var_1,var_2, hi] · `welcome_template`[var_1, hi] · `decline_acknowledgement_manoj`[var_1, en].

**Routes:** `/portal/wa` (page) · `/portal/wa/widget.js` · `/portal/wa/templates` · `/portal/wa/search` · `/portal/wa/send`. Guard `wa_required` (`PORTAL_WA_USERS`, default `manoj`; trusted device allowed).

**Field types (A.1):** `date` → calendar picker → renders "DD Mon YYYY"; `datetime` → datetime-local → "DD Mon YYYY, h:mm AM/PM"; `number` with `auto_from` (days-overdue auto-computed from a date). **Date defaults to today, datetime to now** (still changeable) — the calendar picker is always present. A `wa.me` fallback link ("Send via your own WhatsApp →") is offered.

**Safety:** `PORTAL_WA_DRYRUN="1"` by default — nothing leaves; every attempt is written to `/root/wa/wa_portal/wa_portal_sends.csv` with mode `DRY`/`LIVE`, ok flag and error. **Go-live discipline:** flip to `"0"`, restart, self-send `drmanoj_post_visit` to the doctor's OWN number FIRST, confirm it lands, only then any patient.

**Phase B (deferred):** `/portal/wa/send` is shaped to also accept a shared-secret for server-to-server calls from GAS (agent free-text replies inside the 24h window). Not built yet.

---

## 3 · Follow-up batch (D311)

**Source-stable by design:** reads a FILE, not an API/sheet. Daily `Staff_Action_Today_YYYY-MM-DD.xlsx` (sheet "Call Sheet") is pushed from the clinic PC to `/root/wa/followups/` (override `PORTAL_FOLLOWUP_DIR`); the portal auto-picks the latest by mtime. When the tracker later moves to the VPS it writes the SAME path — the reader never changes and never writes (extends D235).

**Parser:** sections detected by regex ("1. FOLLOW-UP CALLS", "2. PROCEDURE CALL-BACKS"); data columns [S.N, PR, Patient, Mobile(10), Diagnosis, Date(DD-Mon), OD(int), Status, Response, Caller]. On the 2026-08-13 file: 120 follow-up rows all sendable; 4 procedure call-backs excluded (no OD, not on the ladder).

**OD → template ladder:** OD<0 `drmanoj_followup_tomorrow` · 0–3 `drmanoj_followup_due` · 4–10 `drmanoj_followup_missed` · >10 `drmanoj_followup_dropout` (var 3 = OD). Values auto-built per row (name → 1/var_1, formatted date → 2, OD → 3 for dropout).

**Page (tier-grouped):** the follow-up section is split into the source-sheet tiers — **Due today · Grace 1–3 · Actionable Missed 4–10 · Dropout 10+** — each a collapsible section with its own Select-all + per-row checkbox, OD badge, template-override dropdown and ✅/❌ result. Procedure call-backs shown greyed (non-sendable). Reuses `portal_wa.send` (same log, same DRY switch). Route `POST /portal/wa/followups/send` (up to 500 items); page `/portal/wa/followups`, data `/portal/wa/followups/data`.

---

## 4 · UI-served-from-disk + cache-bust (D312)

The four UI files above are served from disk — edit + drop, **no restart** for UI-only changes. The widget is loaded with a per-load cache-buster (`/portal/wa/widget.js?t=Date.now()` written by `wa_page.html`) so an edited widget is never served stale from the browser cache. (The S172 "date default not taking" symptom was purely browser caching — the file was correct; the cache-bust is the permanent cure.)

**Install pattern (standing):** kits ship files pre-named — `.new` = promote-in-place under an md5 guard with auto-rollback (`.bak-S172*`); real names = overwrite-in-place, no restart. Install = drag files in WinSCP + paste one gated SSH block. No renaming ever.

---

## 5 · Known state at S172 close

- **Everything above is LIVE and gated** (DRY mode ON = safe). Selftests + F-63 route gates passed; all routes 302 (auth redirect) incl. `/portal/wa/followups/data` (proves the real batch module, not the fallback stub).
- **Blocked on vendor (F-82):** WABA outbound is down account-side at MyOperator — `HTTP 500 {"message":null}` on ALL authenticated calls (reads + sends), identical from the portal and the tracker's own `wa_send.py`, same token. No-auth = 401 (API up; account not resolving). Inbound webhook healthy. **Go-live waits on Khushi/Lokesh** to restore the account; then flip `PORTAL_WA_DRYRUN→"0"` and self-test. No code change needed.
- **Repo commit owed:** gitignore `casepack/`, `wa_portal/`, `wa_portal_sends.csv`, `followups/` content (plus the pre-existing `console_reviews.db`, `rec_cache/`), THEN commit the 4 code files + 4 UI files.

---
*Portal WhatsApp + Case Pack Dossier v1 — S172. Supersedes nothing (new subsystem). Pin in CANONICAL_MANIFEST Tier-1.*
