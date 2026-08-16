# FROZEN DOSSIER — Callback Tracker (Apps Script project) (v1, S147)

**Dr. Manoj Agarwal Clinic · Bareilly · Tier 2 core + Tier 1 app · built from the LIVE Apps Script export (`Clinic_Callback_Tracker.json`, project digest `e4fd4512522c2e2723cb50690b92c5e8`), verified file-by-file against `drmanoj-clinic-automation/dashboard/`.**

> Source-of-truth note (D160): the **live Apps Script project is canonical**, the repo is its mirror. This dossier documents the live export. **Only the system-of-record *core* is frozen; the console / dashboard / reporting layers stay active Tier 1** (they demonstrably still evolve — CallConsole v1.7, Health v2.3, Dashboard v18.28f). Freeze scope is proposed here and flagged for owner confirmation (§6).

---

## 1. What it is / does

The **Callback Tracker** is the Apps Script project bound to the *Clinic Callback Tracker* Google Sheet. It is **Product A — the system of record**: it pulls call records from MyOperator, computes the net "needs a callback now" list, writes it to the Sheet without wiping staff notes, and serves an always-live web dashboard. Layered on top (same project) are the doctor's outcome-review console, the call console (dialer), a daily monitor + summary emails, and health/diagnostics self-checks.

## 2. Where it lives

- **Apps Script project** bound to the Sheet **`1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0`** ("Clinic Callback Tracker"). Timezone Asia/Kolkata; MyOperator token in Script Property `MYOP_TOKEN` (no secrets in code).
- **Web app:** one URL served from this project (WebApp.gs) — the live callback dashboard.
- **Repo mirror:** `dashboard/` in `drmanoj-clinic-automation`.

**The 14 files (live md5 · role · repo sync):**

| File | Live md5 | Lines | Role | Repo sync |
|---|---|---|---|---|
| `WebApp.gs` | `5173c3c7…` | 1647 | **core** · the live "needs a callback now" web dashboard (one URL, patient-CSV + WhatsApp context). **D34-frozen.** | exact |
| `Config.gs` | `6107ca1a…` | 82 | **core** · all tunables; token from Script Properties; Sheet id from a property | exact |
| `MyOperator.gs` | `b31f47a7…` | 177 | **core** · Search-Logs API client, paginated; `probeApi()` | exact |
| `Netting.gs` | `70398568…` | 185 | **core** · turns raw call records into the net-missed callback list (accurate **status** signal, supersedes the old duration<30s proxy) | exact |
| `Sheets.gs` | `afc047ba…` | 132 | **core** · all Sheet I/O; the intraday digest **UPSERTs** the callback tab so it never wipes staff notes | exact |
| `Main.gs` | `1a85166c…` | 107 | **core** · entry points + triggers (`runIntradayDigest`/`runSummaryEmail`/`runMorningReport`; `removeTriggers` scoped to its own three — D206) | **⚠ DRIFT — repo behind (pre-D206); push live→repo** |
| `appsscript.json` | `7ad6f2fe…` | 18 | **core** · project manifest (Asia/Kolkata, Stackdriver) | whitespace-only |
| `Monitor.gs` | `9cc38ccb…` | 325 | *active* · Daily_Monitor tab + summary emails (own view over raw records) | exact |
| `Health.gs` | `83ebfc51…` | 428 | *active* · daily heartbeat health report (v2.3; S128 +§4b S136) | exact |
| `Diagnostics.gs` | `40d3f019…` | 153 | *active* · self-checks (S53); follow-up stale-list guard | exact |
| `OutcomeLog.gs` | `07d05cf2…` | 554 | *active* · doctor's outcome-review console, server layer (v2.0; from S25) | whitespace-only |
| `CallConsole.gs` | `afca092c…` | 1224 | *active* · Call Console server data layer (v1.7, S140 — K-2 + Block-C merge) | whitespace-only |
| `Dashboard.html` | `d528e666…` | 3170 | *active* · the dashboard/console UI (current live = repo `Dashboard.html`; v18.28f) | exact |
| `CallField.gs` (`CallFeed`) | `333e5507…` | 106 | *bridge* · one name-free `Call_Feed` for the Follow-Up Tracker (outgoing reconciliation + incoming) | exact |

## 3. How it works

- **Ingest → net → write.** `MyOperator.gs` fetches call records for a window (paginated); `Netting.gs` reduces them to the net-missed callback list using MyOperator's **status** field (not talk duration); `Sheets.gs` **UPSERTs** the callback tab so staff notes are never overwritten.
- **Serve.** `WebApp.gs` serves one always-live web dashboard (the "needs a callback now" view with patient-CSV + WhatsApp context) — **D34-frozen**.
- **Schedule.** `Main.gs` installs/owns three time triggers (`runIntradayDigest`, `runSummaryEmail`, `runMorningReport`) and, per **D206**, `removeTriggers()` deletes only those three — never other files' triggers.
- **Report / watch.** `Monitor.gs` writes the Daily_Monitor tab + summary emails; `Health.gs` sends the daily heartbeat; `Diagnostics.gs` runs self-checks incl. the follow-up stale-list guard.
- **Doctor + staff surfaces.** `OutcomeLog.gs` (doctor outcome review) and `CallConsole.gs` + `Dashboard.html` (the call console / dialer) sit on top. `CallField/CallFeed.gs` exposes the name-free `Call_Feed` the Follow-Up Tracker reads.

## 4. Decisions & findings that shaped it

- **D34** — `WebApp.gs` is frozen; never edited without an explicit waiver.
- **D206** — trigger ownership: each file removes only its own triggers (the live `Main.gs` fix; the repo copy predates it).
- **Status-signal rule (19-Jun-2026)** — `Netting.gs` keys off MyOperator's status field, superseding the old "duration < 30s" proxy (same principle later hardened as D244 / F-44).
- **UPSERT rule** — `Sheets.gs` never wipes staff notes on the callback tab.
- Layer lineage: OutcomeLog from S25 (v2.0); Health v2.3 (S128/S136); CallConsole v1.7 (S140).

## 5. Known quirks / limits (read before ever reopening)

- **`WebApp.gs` is D34-frozen** — no edits without a waiver, full stop.
- **`Main.gs` drift:** the repo's copy is the pre-D206 version that deletes *all* triggers — do not deploy the repo copy over live; push live→repo instead.
- The netting result depends on the **status** field, not talk duration — don't "fix" it back to a duration threshold.
- The callback-tab write is an **UPSERT** — a naïve full-rewrite would wipe staff notes.
- Secrets live only in **Script Properties** (`MYOP_TOKEN`) — never in code.
- The frozen core and the active layers **share one Apps Script project** — editing an active layer must not touch the core files.

## 6. Freeze note — PROPOSED (confirm scope)

**Proposed frozen core (S147 / D247):** `WebApp.gs` (D34), `Config.gs`, `MyOperator.gs`, `Netting.gs`, `Sheets.gs`, `Main.gs`, `appsscript.json` — the system-of-record write path — **plus the Sheet** `1USj…klo0`. Waiver required to change (D34 discipline) + version bump.

**Active Tier 1 (NOT frozen):** `Monitor.gs`, `Health.gs`, `Diagnostics.gs`, `OutcomeLog.gs`, `CallConsole.gs`, `Dashboard.html`, `CallField/CallFeed.gs` — covered by `Call_Console_Evolution_Spec` + `Frontend_Dashboard_Documentation`.

**⚠ Two things for the owner:**
1. **Confirm the core/active split above** — I've kept the freeze conservative (only the write-path), because several other files still evolve. Move any file across the line if you disagree.
2. **Repo hygiene:** push the live `Main.gs` (D206) over the stale repo copy so GitHub matches live.

Frozen-artefact reference = the live project digest `e4fd4512522c2e2723cb50690b92c5e8`; the per-core-file md5s are in §2.

---

**END — Callback Tracker (Apps Script project) Dossier v1 (S147).**
