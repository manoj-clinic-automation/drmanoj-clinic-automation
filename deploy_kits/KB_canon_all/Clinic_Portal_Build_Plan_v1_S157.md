# CLINIC PORTAL BUILD PLAN — Doctor + Manager (v1 · S157)

**Owner:** Dr. Manoj Agarwal · Bareilly · **With:** Claude (Clinic Automation) · **07 Aug 2026**
**Status:** PLAN ONLY — no code. Companion to `Clinic_Portal_SSO_Architecture_v1.md` (the login
mechanism) and `Clinic_Estate_Master_Inventory_v1.md` v1.7 (what exists). This doc decides **what goes
on each portal** and **which local + GAS apps live there**.

---

## 1. What "the portal" is (and the one constraint that shapes everything)

Two role-scoped launcher pages, each a single sign-on into the apps its tiles open:
- **Doctor portal** — your remote-first control centre (phone or PC), plus a bridge to the PC tools.
- **Manager portal** — a small web-only page: the three things the manager runs.

**The constraint that decides the local-apps question:** the portal is served from the VPS and is
reachable from anywhere; the **local PC apps run on `localhost:5000–5059`**, which only resolves *on the
clinic PC itself*. A `localhost` tile therefore **works when the portal is opened on the clinic PC and is
dead on your phone** — and that's fine, because those apps hold patient data and are *deliberately*
never exposed to the internet. So local apps join the portal as a **"Clinic PC only" group** that
live-detects whether it's reachable, rather than being pushed onto the remote surface.

---

## 2. DOCTOR PORTAL — tile roster

Grouped so the phone view (top three groups) stays clean and the PC-only group appears only at the clinic.

### Group A — Web apps (SSO, work everywhere)
| Tile | Opens | Auth |
|---|---|---|
| **Attendance** | `attendance.dr-manoj.in` | SSO cookie |
| **Salary & Ledger** | `attendance.dr-manoj.in/ledger` (checker role → full, incl. `/salary`) | SSO cookie → ledger `checker` |
| **Asset Register** | `assets.dr-manoj.in` (owner role) | SSO cookie → asset `owner` |
| **WhatsApp Approvals** | `followup.dr-manoj.in/wa-approve` | SSO cookie *(tile shown but noted "blocked until Lokesh clears the vendor authorizer")* |

### Group B — Call cockpit (link-based, doctor-only)
| Tile | Opens | Auth |
|---|---|---|
| **Call Console / Dashboard** | Apps Script `/exec?k=DASH_KEY` | key baked into the tile (Google-hosted — can't take our cookie) |

### Group C — Report views (optional, doctor-only) — open the Google Sheet a background job writes
| Tile | Opens | Why |
|---|---|---|
| **Daily Clinic Reports** | the DailyClinicReports output Sheet | see attendance/vehicle/ICICI digest at a glance |
| **Accounting** | the Clinic Accounting Reports Sheet | daily/monthly accounting + open issues |
| **UPI Reconciliation** | the UPI-recon Sheet | logged-vs-settled mismatches |

*(These open in your Google session — they are views of outputs, not the scripts. Include only the ones
you actually check; skip the rest.)*

### Group D — Clinic PC tools (shown only when the portal is opened on the clinic PC)
This group **absorbs the Clinic Hub** — same tiles, live "reachable?" dots, but now inside the portal.
| Tile | Opens | Note |
|---|---|---|
| **Follow-up Tracker** ("the brain") | `localhost:5000` | Docterz → call list; the source of follow-up intent |
| **Vitals & Plan** | `localhost:5057` | clinic_writer v28 |
| **Surgical Case Pack** | `localhost:5058` | pre-surgical paperwork |
| **CC Statements → Tally** | `localhost:5059` | statement conversion |
| **GMB Review Assist** | local HTML | patient-review composer |

---

## 3. MANAGER PORTAL — tile roster

Web-only, works on the manager's phone. **No cockpit, no reports, no local tools, no salary figures.**

| Tile | Opens | Auth / role |
|---|---|---|
| **Attendance** | `attendance.dr-manoj.in` | SSO cookie |
| **Asset Register** | `assets.dr-manoj.in` | SSO cookie → asset `manager` (its limited view) |
| **Staff Ledger — Entry** | `attendance.dr-manoj.in/ledger` | SSO cookie → ledger `maker` (enter events only) |

**F-31 guard (already in code):** `/salary` is checker-only, so the manager cannot open salary figures
or APPROVE even by typing the URL. The manager tile set simply never shows a salary tile.

---

## 4. Per-app SELECTION — the full decision table

Every app in the estate, and where it lives. This is the "select which local + GAS apps should live
there" answer.

### VPS web apps
| App | Doctor | Manager | Verdict / reason |
|---|---|---|---|
| Attendance (8042) | ✅ | ✅ | shared |
| Staff Ledger + `/salary` (8043) | ✅ full | ✅ entry-only | role-differentiated (F-31) |
| Asset Register (8030) | ✅ owner | ✅ manager | role-differentiated |
| WABA Approve (8101) | ✅ | ❌ | doctor decision; blocked vendor-side for now |
| attlistener, wa-receiver/send, call-api, call-hook, fu-receiver, wa-notifier | ❌ | ❌ | back-end services, **no screen** — never portal tiles |

### Google Apps Script
| App | Doctor | Manager | Verdict / reason |
|---|---|---|---|
| **Call Console / Dashboard** (cockpit) | ✅ (link) | ❌ | the only user-facing GAS; doctor cockpit |
| DailyClinicReports · Accounting · UPI-recon | ⭕ optional (Sheet view) | ❌ | background jobs — link the *output Sheet* if useful, not the script |
| Personal: Inbox Janitor · CC_saver | ❌ | ❌ | personal account, different trust class |

### Local PC apps (localhost — "Clinic PC only" group)
| App | Doctor (PC-only) | Manager | Verdict / reason |
|---|---|---|---|
| Follow-up Tracker (5000) | ✅ PC-only | ❌ | localhost + PHI; works only at the PC |
| Vitals & Plan (5057) | ✅ PC-only | ❌ | localhost + PHI |
| Surgical Case Pack (5058) | ✅ PC-only | ❌ | localhost + PHI |
| CC Statements → Tally (5059) | ✅ PC-only | ❌ | localhost; owner-only finance |
| GMB Review Assist | ✅ PC-only | ❌ | local HTML |
| Clinic Hub | — | — | **retired/absorbed** into Doctor Group D |

### Personal cluster (VPS)
| App | Doctor | Manager | Verdict |
|---|---|---|---|
| RxGuard · GutLog · FitLog | ⭕ optional single "Personal" link-out | ❌ | different trust class; keep on their own switcher — at most one link-out tile |

Legend: ✅ include · ❌ exclude · ⭕ optional (owner's call).

---

## 5. What actually gets BUILT (named pieces — for the build session)

1. **The SSO broker** — the portal grows a clinic user+role store (roles `doctor`, `manager`) and issues
   the `.dr-manoj.in` SSO cookie (per the architecture doc).
2. **Two portal pages** — one tile-config for `doctor`, one for `manager`; the same page renders the
   right group set by role. Group D live-detects `localhost` reachability (shown only on the clinic PC).
3. **Per-app SSO shim** — the ~15-line "accept the SSO cookie" addition to attendance, ledger, asset
   (each keeps its own login as fallback).
4. **Cockpit + report tiles** — link tiles carrying the `?k=` key (cockpit) / Sheet URLs (reports).
   No change to the cockpit itself.

Nothing new is built for the local apps — they're linked as-is (localhost tiles).

---

## 6. Build sequence (when we start, next session)

1. Broker (user+role store + SSO cookie + "sign out everywhere").
2. Doctor portal Group A + B (web SSO tiles + cockpit) — the highest-value remote surface first.
3. Attendance shim → Asset shim → Ledger shim (verify manager can't reach `/salary`).
4. Manager portal (three tiles) + onboard the manager login.
5. Doctor portal Group C (report views) + Group D (local tools, absorbing the Hub).

Each step independently testable; every app keeps its own login as fallback; nothing left unreachable.

---

## 7. Decisions still needed from you

1. **Manager login** — one shared "manager" login, or named per person (Shavez / Alisha)? *(sets the
   ledger maker mapping too.)*
2. **Report-view tiles (Group C)** — include all three Sheets, some, or none?
3. **Local tools** — absorb the Clinic Hub into the Doctor portal's PC-only group (recommended), or keep
   the Hub separate and just link to it?
4. **Personal link-out** — one "Personal" tile on the Doctor portal, or keep Rx/GutLog/FitLog fully
   separate (recommended)?

*Answer these and the build session opens straight into step 1 (the broker).*

---

*End — Portal Build Plan v1 (S157). Plan only. Pairs with the SSO Architecture doc; both feed the
next-session build.*
