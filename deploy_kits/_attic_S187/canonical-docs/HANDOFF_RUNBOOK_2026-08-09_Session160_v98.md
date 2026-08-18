# HANDOFF RUNBOOK — 2026-08-09 · Session 160 · v98 (Tier 0)

**Dr. Manoj Agarwal Clinic · Bareilly.** Supersedes v97. §0 = what just happened · §1 = mental models · §2 = the live backlog.

---

## §0 — WHAT HAPPENED THIS SESSION (S160)

Phase 0 verified all 24 canonical rows by md5 — **zero mismatches**. A mixed session: closed portal work, then a long, productive design run that turned "fine-tune the salary ledger" into a specced subsystem. **Two design decisions minted (D270, D271); one live file shipped; a critical July-salary evaluation drove the design.**

- **Portal (live):** `portal.py` **`679a0087…` → `81c2baef638f0d2d59d438c6370522cb`** (650→717 lines, `/root/portal/`, `clinic-portal` :8099). Two changes: **3 doctor-only personal health link-tiles** (RxGuard `rx.` · GutLog `health.` · FitLog `fit.dr-manoj.in`, own logins kept) and a **sectioned mobile layout** (Clinic / Money & Accounts / Clinic PC tools / Personal / Health / Coming soon; empty sections auto-hide per role; phone 2-col; role/PC filter moved server-side to `_visible_sections`). Backups on VPS. Repo commit owed → `launcher/portal.py`.
- **F-63 incident (caught + fixed live):** an interim build shipped a `pc`-NameError (route referenced a `pc` local that existed only as a render kwarg) → 500 for logged-in users while the logged-out curl 302 passed. Rolled back one line, refixed to `81c2baef`. New delivery gate: a **Flask test-client hit on the actual route** for any live Flask change.
- **D270 — Surgical Case Pack → VPS (off-Drive):** code audit proved it's a **local PHI store** (case_archive bundles/consents + ledger, off-Drive by design; reads the tracker's Drive-synced patient CSVs) — the twin of Vitals, not the "Website/SEO" tile a doc labelled (**F-62**). Owner chose VPS **off-Drive** (VPS-disk archive + PC-push patient input → F-56 stays parked, no service-account key). Sarvam is API-based, so VPS-disk still delivers doc-search. Reverses D262 / re-amends D137. Wave: **Case Pack → Vitals (D34 waiver) → CC→Tally** (owner reclassified CC→Tally as a **full** VPS move — output is an accountant CSV/Excel, no desktop-Tally import). **Build parked behind a phase-3 strategy hard-bake.**
- **D271 — Staff Daily Register subsystem** (design v1.0, sign-off pending): a maker-checker daily-capture page feeding the salary engine so month-end is confirmation not entry. Roles: maker = Alisha + Shivani[inactive], checker = Shavez, override = Manoj + Bhawna. Three stores, one writer each (Daily Register SQLite / Yearly Balances / Staff Ledger). Full locked policy in the dossier + Register §S160. Dossier `Staff_Daily_Register_Dossier_v1_0.md` (`84fe26dd…`) = **Tier-1 DRAFT**.
- **July salary critique:** 8 structural flaws found (punch-out equity, OT sanity ceiling, off-day denominator, EARLY_BIG brief-presence, two-nets, preview-vs-FINAL, habitual, incentive reach) → triaged into the D271 design.
- **WABA state corrected:** record said "blocked pending Lokesh" (D120); owner says **not blocked — operationalise**. Verification-first, reworded in §2. Not a finding.
- **Parked (owner):** SSO passthrough for the 3 health apps; F-56 key rotation (do not raise until asked).

**Decisions D270–D271 · Findings F-62–F-63 minted. Next free: D272 · F-64 · Session 161.**

---

## §1 — MENTAL MODELS (carry these)

- **Phase 0 first, every session** — hash-verify every manifest row before any work (D172/D188/D201). A filename/label is not provenance (F-62: audit the code, not the doc's category tag).
- **Build from the md5-verified live file**, full-file replacements only (D202), `py_compile` on the **VPS Python path** (F-53); for any **live Flask** change, a **test-client route hit** (200 + expected content) is now part of the gate (F-63). String replacement with count assertions, never sed.
- **One writer per table/store; append-only ledger; maker-checker for money** (D265). F-31: salary/finance data never in public repos or shared drives.
- **Off-Drive VPS-native is the phase-3 direction (D270):** local PHI apps migrate to VPS **disk** (not Drive), keeping the leaked service-account key (F-56) out of the loop. Sarvam is an API — it extracts from a file wherever it sits, so VPS-disk still delivers document search. D262 is reversed for Case Pack; Follow-up Tracker still stays local (D246).
- **Portal = SSO broker** (:8099); apps verify the `clinic_sso` cookie with their own login as fallback, inert if the secret is unreadable (D264). SSO proves WHO; each app's store decides WHAT (D265).
- **Hard-bake before code** on money/PHI subsystems: a signed dossier precedes the build (D271; owner: "coding only after hard baking it").
- **Secrets:** never displayed by a procedure (D176); a secrets file entering the transcript = rotate (S128). `portal_config.py` did this session → rotate `CLINIC_SSO_SECRET` when convenient.

---

## §2 — LIVE BACKLOG (the authoritative open list)

1. **Staff Daily Register — BUILD** *(gated on dossier sign-off; the session's main new work).* Page-first: (2) data model + maker/checker/override page behind portal SSO → (3) Yearly Balances store → (4) uniform/i-card issuance (seeded from Shavez's sheet) → (5) history-aware staff record (date-ranged shifts) → (6) engine reads the store (dress/i-card/leave/cover/outstation/encashment; incentive→pot; single net; header renames; Sunday toggle; lifecycle pro-rating; Shivani ₹200) → (7) **July + partial-August dry-run** before the first real APPROVE. Dossier `84fe26dd…` (Tier-1 DRAFT).
2. **Phase-3 local-apps strategy — hard-bake** *(gates item 3).* One doc: off-Drive VPS-native migration (Case Pack → Vitals[D34 waiver] → CC→Tally full-VPS); a **shared doc-ingestion + Sarvam** service; a **VPS patient index** (feeds Case Pack + a planned 360° patient lookup); Marg/Labmate revenue plumbing (wired-LAN PCs); **backup floor** = app-level nightly self-backup (recommend the paid daily platform backup once live PHI lands), off-Drive to keep F-56 parked.
3. **Case Pack → VPS (D270)** — build, after item 2 is signed off. Off-Drive; VPS-disk archive + PC-push patient CSVs; systemd + portal SSO (doctor-only); optional Sarvam extraction stored for search.
4. **GitHub commits + item-1 verify.** Commit `portal.py` `81c2baef…` → `launcher/portal.py`; the dossier → `canonical-docs/`; older owed (staff_ledger/watchdog mirror, canonical-docs mirror). External md5 re-check of the S158 six files still needs the **repo-owner path** (GitHub connector was OFF this chat). *(= "repo documents — organise".)*
5. **July salary reconciliation** — rupee-by-rupee vs actually-paid (owner carry).
6. **August salary run** (~Sep 01–09) — first real **APPROVE & LOCK**; ideally after the register build lands.
7. **WABA — operationalise** (NOT blocked; owner-corrected). Confirm the live send path fires, then migrate `wa_approve` nohup→systemd.
8. **Callback Tracker — remaining polish** (refs: Core Dossier + AppsScript Audit).
9. **Cold-kit collection — organise** (with Cowork).
10. **Parked / small:** SSO passthrough for the 3 health apps · **rotate `CLINIC_SSO_SECRET`** (transcript exposure this session) + re-run `portal_setup.py` · Notion catch-up (S151–S160) · verify `staff_master.sunday_group` populated (July showed no off-days) · tidy the stale `:8090` comment in `portal.py`.
11. 🔴 **PARKED by owner (do not raise until asked):** rotate the Google **service-account key** (F-56) + CALLHOOK Steps 3–4 (Lokesh).

*Backlog pointer for next session: this §2. Next free D272 · F-64 · Session 161.*
