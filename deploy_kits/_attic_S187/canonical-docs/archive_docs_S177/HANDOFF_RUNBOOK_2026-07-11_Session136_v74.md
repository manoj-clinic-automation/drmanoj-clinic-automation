# HANDOFF RUNBOOK — 11 Jul 2026 · Session 136 close · v74

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Companion set at this close (md5 of the artefacts, not from memory):**
KB **v1.62** `26fae0f8fc0659a90f051e0dbae0a4cd` · Audit **v1.7** `90539cb107ecb53adfe518a7eb00f8d8` ·
Umbrella **v1.48** `7fa7ae2251996bdc4c5f38ac1606903b` · Console Spec **v2.1** `3b29097c02eaa5397281ab5ec37dc8fc` ·
API Quick-Ref, Diagnostics Spec v2.1, Maintenance SOP v1.1, Frontend Doc v2 (S134) — **unchanged this session**
(Frontend Doc is now STALE in its read-path section; v3 scheduled, see §2).

---

## §0 — WHAT HAPPENED (Session 136, one evening, THREE deploys, all live-verified)

**§0.1 The builds.** All three on the ONE existing deployment (New version each time; URL unchanged).

1. **Deploy 1 — Block C** (`Dashboard.html` v18.24 · `Callconsole.gs` v1.4 · `Health.gs` v2.3):
   ONE CLOCK — the server's IST date (`cc_todayIST_`) rides in every refresh; `fuDayKey()` prefers it; the
   page computes no dates; the last UTC line retired (**F-13, F-5 closed**).
   ONE TRIP — `getDashboardBundle(key,{force,olDay})` replaces ~9 calls/min/device, behind a **45 s per-ROLE
   CacheService entry** (staff cache ≠ doctor cache; `force` bypasses **and refills**, so a post-save refresh
   is what every device sees next; non-today outcome review never cached; cache failure degrades to a plain
   build). `getCallDurationFast` reads the **last 200 rows** of `Call_Durations` only. Hidden tabs stop
   polling; instant catch-up on return. `QC_BUNDLE_BUILDS` counts builds/day → `Health.gs` §4b prints
   **QUOTA HEADROOM** in the 08:00 mail (**F-6, F-12, audit §4-Q3 closed**). Old per-function endpoints kept
   answering deliberately — stale open pages survive a deploy. **D211 minted.**
2. **Deploy 2 — F-36 + WA call line** (`Dashboard.html` v18.25):
   **F-36 raised AND closed same evening.** The doctor's ESCALATION card was a **seventh** phone-keyed
   surface F-34 never counted (ID/last-visit baked at save time or filled from the phone-keyed
   `cc_patientMap_`). Live case: Raj Rani's card showed **7362 · 30-May** (= Ekta). Cure = the S135
   name-aware `fuLookup` pattern client-side; shared-no-match shows **ID ⚠ verify** (D208). Live-verified:
   card now **7361 · 04-Jul**. Deliberately untouched (recorded in Audit §7): the card's *diagnosis* and the
   history/log chips that display a *saved* clinicId.
   **WA tiles** now show today's outgoing call — who called · when · duration / not connected · 🎧 recording —
   built from the bundle's `allCalls` (phone10 from the call-id prefix; zero extra reads). Today-only by
   design (**D212**); per-call history = Block D. **Verification parked** — no WA-tile call occurred
   post-deploy; the first natural one verifies it.
3. **Deploy 3 — F-4 + Block E + D183** (`Callconsole.gs` v1.5 · manifest · **Probe.gs DELETED**):
   **F-4 closed** (dead `logOutcome` ledger removed). **Block E closed** (`documents` scope dropped —
   F-15/F-7). **D183 built + ARMED**: `sweepUnloggedCalls` mails the doctor at ~21:30 every call today, both
   directions, with no outcome row today; read-only mirror; shared family mobiles unnamed (D208); trigger
   owner-installed once (D206). Manual run live-verified: **~34 numbers**, dominated by **incoming connected**
   calls — the measured Block D gap, now visible nightly.

**§0.2 Verification state.** Post-deploy export **`Clinic_Callback_Tracker__7_.json`** byte-verified in
session: **all 13 files match delivered work; Probe absent; manifest scope-clean.** New rule recorded
(KB §S136.4): editor exports strip the file's final newline → **expected hashes are export-form**
(`rstrip('\n')` before md5). Proven on OutcomeLog's apparent "drift" at session start (byte-identical to the
S135 GitHub copy except one trailing newline).

**§0.3 Corrections owned this session.**
- CALLHOOK: the assistant read two clean status checks as "Step 3 appears done" — **withdrawn**: "accepted
  today" was 108 in both checks, so **zero calls flowed in the window; the clean reading was vacuous.**
  Step 3 (Lokesh updates the panel) remains unconfirmed; Step 4 stays locked (D173). Decisive test: a status
  check during weekday traffic.
- Two build-script failures (a cutter stopped by a `}` inside a docstring example; a stray placeholder line)
  were caught by the anchor/content guards **before any file was written**. Delivered files clean.

**§0.4 Also this session:** F-3 **classified** (KB §S136.5 — column-disjoint-by-layout contract written);
watch item logged (one 55 s cold `getDashboardBundle` build at 21:09 — single data point, not a finding;
tomorrow's QUOTA HEADROOM line is the real picture); D183's first digest doubles as a live measurement of
the incoming-outcome gap.

---

## §1 — MENTAL MODELS (what Session 137 must hold in its head)

1. **The dashboard reads through ONE pipe now (D211).** Any new per-cycle data belongs INSIDE
   `getDashboardBundle`, never as a new `google.script.run` polling call. Post-write refreshes call
   `poll(true)` — force refills the shared cache for every device.
2. **Export-form hashing.** Every expected hash for an editor export is computed on `rstrip('\n')` content.
   START_HERE_137's table is already export-form; do not "correct" a one-newline difference into a drift.
3. **The identity rule is now uniform on staff/doctor tiles (D208):** name-aware maps win; shared-no-match
   shows *verify*, never a relative. Two surfaces knowingly remain phone-keyed or saved-value:
   incoming-call tiles (S135 decision) and history/log chips (a log shows what was logged).
4. **The sweep is a mirror, not a mechanism.** D183 mails the gap; it must never grow write behaviour.
   The cure for its dominant line (incoming connected, unlogged) is Block D: F-19 on the VPS + §K one-tap UI.
5. **WebApp.gs stays frozen (D34).** Tonight's entire server surface went into Callconsole.gs and Health.gs.
6. **One deploy = New version on the EXISTING deployment.** Three times tonight; URL never moved.

---

## §2 — OPEN BACKLOG (ordered; owner questions first because they unblock the most)

**Q — THREE OWNER ANSWERS PENDING (asked in-session, re-ask at S137 start if unanswered):**
1. **D205 template choice** — which WABA message do seen-today patients get (thank-you / care-instructions /
   review-request / combination)? Then: session-START design, half-session, VPS `wa_approve` scope.
2. **§K button wording** — approve/edit the five one-tap choices (proposed: मरीज़ आ रहे हैं · नहीं आएँगे ·
   बात हुई — फिर call करना · बात नहीं हो पाई · डॉक्टर को दिखाना है).
3. **Third-attempt rule** — D78 (auto-drop + WABA + snooze) vs D195 (send to doctor). One must win before §K builds.

**A — Block D remainder (recommended next build, in this order):**
- **A1. VPS receiver stops discarding incoming (F-19)** — `call_hook_capture.py`, its OWN careful pass
  (build offline → py_compile → selftest → WinSCP+md5 → restart → status). Design constraint: the tab is
  PHI-clean (no phone number today) and incoming calls have no `client_ref_id` — the row key and the join
  need a session-start decision. Enables incoming verdicts + duration data.
- **A2. §K one-tap staff UI** — after Q2+Q3; run ALONGSIDE the old flow; completion-rate is the deciding
  metric (spec §K.4). Includes the F-34-family residue if owner wants it: escalation-card diagnosis +
  incoming tiles name-aware.
- **A3. F-10 markup cure** — **own commit** per the audit; ~24 fragile sites → row-ID + page-level map.

**B — Standing / carried:**
- **CALLHOOK Steps 3–4** — one message to Lokesh ("update the call-webhook secret in the panel to the new
  value"); then ONE weekday-traffic status check; then Step 4. Not blocking anything.
- **Service-account key rotation** — overdue, highest-standing security risk (needs Lokesh coordination).
- **AKEY_14 rotation** (guessable).
- **Docterz clinical-data-report migration** — owner decision open (strict superset confirmed S135; the
  follow-up column question open).
- **Frontend Dashboard Documentation v3** — v2 (S134) is stale in its read-path section after D211; write at
  the next Apps Script documentation pass.
- **Hindi spelling corrections** — `vitals_page.html` LIB strings (Track 1).
- **Notion orphaned pages** — deferred cleanup.
- **Watch item:** dashboard cold-build latency (one 55 s observation); read tomorrow's QUOTA HEADROOM line
  before treating it as real.

**C — Explicitly parked:** AI review layer (A-00…Block A″, two-phase gate, workbook with owner) ·
ClickUp (D17) · Maintenance & SOP project (created only after Diagnostics.gs has ≥1 real clinic day —
Diagnostics.gs is live; the owner may green-light the project any session).

---

## §3 — STATE SNAPSHOT (delta from v73 only; v73 remains true otherwise)

- Apps Script: **Dashboard v18.25 · Callconsole v1.5 · Health v2.3 · Probe.gs deleted · manifest minus
  `documents`** · deployment URL unchanged · **new trigger:** `sweepUnloggedCalls` daily 21:00–22:00 slot.
- New Script Property in use: `QC_BUNDLE_BUILDS` (self-rolling daily counter; Health reads it).
- Live editor == delivered work, byte-verified (`__7_` export). GitHub push pending this close (see commit).
- CALLHOOK: dual-key, healthy, 108/0 accepted/refused today; Steps 3–4 open (Lokesh).
- Everything else exactly as Runbook v73 §3 recorded it.

**END OF RUNBOOK v74. §3 is the last section. If absent, this file is truncated — do not use as canonical.**
