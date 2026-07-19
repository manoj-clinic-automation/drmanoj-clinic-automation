# HANDOFF RUNBOOK — 12 Jul 2026 · Session 139 close · v77

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Companion set at this close (md5 table in START_HERE_SESSION_140):** KB **v1.65** · Umbrella **v1.51** ·
Console Spec **v2.3** · Audit **v1.8** · Frontend Doc **v3** · API Quick-Ref Card (S137) ·
`WABA_Approved_Templates_v1_S137.md` · Diagnostics **v2.1** · Maintenance SOP **v1.1** — last four unchanged.
**Live files this session:** `Dashboard.html` **v18.27** (2,988 lines, `4e73682242a34d167c86e8a72a941854`) ·
`Callconsole.gs` **v1.6** (1,128 lines, `eb91034961a20545b5316b144f86075a`) · `wa_send_api.py` **v3**
(`a3ed37080aaec940226c98bf0d2c7e04`) · `/root/portal/portal.py` (attendance→https; backup
`portal_BACKUP_S139_pre_https.py`).

---

## §0 — WHAT HAPPENED (Session 139, Sunday 12 Jul, FULL EOS — two Apps Script deploys, one VPS install, one portal hotfix)

**§0.1 Phase 0 clean** (9 docs + Frontend v2 md5-exact; export hashes hold). Owner's ask: all pending
tracker corrections, minimum steps → two-pass plan → owner directed both passes TODAY (Sunday: no traffic,
parallel-run fallback intact, one Monday verification morning).

**§0.2 F-10 CURED (v18.26, D219, Audit F-10 CLOSED).** ~24 audit sites + 8 incoming-form `slotId` sites →
opaque `dref()`/`dget()` refs; 34 guarded edits, zero escaper residue in handlers, hostile-value proof,
node-clean; deployed, stamp verified. Incoming-form live tap PARKED to first weekday incoming call.

**§0.3 K-1 BUILT AND LIVE (§K.7 of Console Spec v2.3).** Pre-build checklist from the artefacts forced
three spec corrections, minted as **D220** (counter home = Callconsole bundle `missTotals`; WebApp frozen),
**D221** (write mapping: buttons 1–3 k-codes + explicit settle; button 4 = `no_answer` source='K'; button 5
delegates to `saveFollowupOutcome('problem')`; ui=K rides `source` — no grid widening), **D222** (3rd-strike
fires ONLY on transition to exactly 3; existing relay + new allow-listed capped `POST /wa-send/template`;
fail-open toward the save). Relay v3: selftest 10/10, live `version:3`, endpoint proven to REFUSE without
the secret (behaviour-check, F-38 lesson). Dashboard v18.27 + Callconsole v1.6 deployed (one New version);
stamp + ⚡ toggle live-verified 09:36 IST. New tab `K_Strikes` (Callconsole sole writer).

**§0.4 CALL-LIFECYCLE AUDIT (owner-requested; D180 — found, not fixed).** Both directions traced. Register:
**G-1** answered incoming calls produce NO outcome anywhere (cure **K-2**, next build) · **G-2** cross-day
counter — **CLOSED this session** · **G-3** Stage-3 verdict has no nightly timer · **G-4** D158 join defect,
more exposed now `IN-` rows flow · **G-5** recording-loss window (Stage-1 nightly vs 24 h links; F-21/D200
never built) · **G-6** F-38 write-path surveillance. Closure order: **K-2 → A5 (G-3+G-4) → Pass 5 (G-5+G-6,
+F-37) → Pass 6 portal gist tile (D223)**.

**§0.5 Portal hotfix (D224).** Attendance → `https://attendance.dr-manoj.in`; live `/root/portal/portal.py`
edited (guarded sed, backup, py_compile, restart, owner verified padlock). **GitHub's portal copy is STALE
against live** (tile absent from repo) — D160 reproven; this kit carries the live file.

**§0.6 Live reads.** **QUOTA BASELINE (first Block-C read): 453 builds ≈ 4,983 sheet reads/day — comfortable.**
K-1 adds two small per-build outcome-tab reads (negligible @420 rows; merge-into-one logged as a Block-C
micro-optimisation). `Call_Durations` today=222 (219 backfill + 3 natural) — v3.0.1 ingesting. Carried to
tonight: **D183 digest EXACTLY ONCE**.

---

## §1 — MENTAL MODELS (what Session 140 must hold)

1. **D219 is now law in Dashboard.html:** any new handler that interpolates `esc()`/`jsq()` data into
   markup reintroduces the F-8/F-10 bug class. Pattern: `handler(dget('\''+dref(v)+'\''))`.
2. **Two outcome surfaces share one table.** K rows carry `source='K'`; button 4 is `no_answer` so ALL old
   machinery + verdict joins keep working; the settle column, not the code table, drives worklist state.
3. **The counter is bundle-side (D220).** Anything needing cross-day miss counts reads `missTotals`; the
   frozen WebApp per-day logic is display-only legacy for the old surface.
4. **The relay now sends templates** — allow-list of two, capped, `MYOP_AUTH_TOKEN`. A3's server half
   already exists (`drmanoj_post_visit` on the list).
5. **Monday morning is the verification morning:** K-1 first-call buttons · F-10 incoming tap · CALLHOOK
   weekday status (→ Step 4 if clean AND calls flowed) · first natural weekday `IN-` row · WA-tile D212.
6. **Standing:** one deploy = New version on the EXISTING deployment · WebApp.gs frozen (D34) · expected
   values from the artefact (D172) · live beats repo (D160) · an audit finds (D180) · grid geometry is
   invisible offline (S138).

---

## §2 — OPEN BACKLOG (ordered)

**A — Ready builds (owner picks; one per session):**
- **A6. K-2 — incoming one-tap (G-1, the biggest lifecycle hole).** Relay, counter, button machinery all
  exist; primarily a tile-source change (incoming tiles + `IN-` rows). Design half-session + build.
- **A3. D205/D213 seen-today WABA** — relay half LIVE (post_visit allow-listed); remaining = trigger source
  (Docterz seen-today feed) + send loop; VPS scope.
- **A5. Incoming-verdict pass** — `call_verdict.py`/`verdict_review.py` consume `IN-` rows (retire F-18) +
  **fix D158 join** + **arm the Stage-3 nightly timer** (G-3, G-4) in one session.
- **A7 (Pass 5). D200 per-call recording download + F-38 write-probe (+F-37)** — VPS maintenance session.
- **A8 (Pass 6). Portal gist tile (D223)** — after K-2/A5 create its data.

**B — Standing / carried:** CALLHOOK Steps 3–4 (**Monday check**) · service-account key rotation (highest-
standing risk; Lokesh) · AKEY_14 · Docterz clinical-report migration (owner decision) · Hindi spellings
(Track 1) · Notion orphans · panel-tidy (Lokesh) · Block-C read-merge micro-optimisation (new, S139) ·
K-1 retirement watch: completion >42 % × 5 clinic days retires the old dropdown.
**Watch items:** D183 count tonight (ONE) · K-1 first-call verification · F-10 incoming-tap verification ·
first weekday `IN-` row · dashboard cold-build latency (one 55 s observation, S136).

**C — Explicitly parked:** AI review layer (two-phase gate, workbook with owner) · ClickUp (D17) ·
Maintenance & SOP project (owner may green-light any session).
