# HANDOFF RUNBOOK — 12 Jul 2026 · Session 138 close · v76

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**
**Companion set at this close (md5 of the artefacts, not from memory — table in START_HERE_SESSION_139):**
KB **v1.64** · Umbrella **v1.50** · Console Spec **v2.2** · API Quick-Ref Card (S137) ·
`WABA_Approved_Templates_v1_S137.md` · Audit **v1.7** · Diagnostics **v2.1** · Maintenance SOP **v1.1** ·
Frontend Doc **v2 (stale read-path, v3 pending)** — the last five unchanged this session.
**Live VPS files this session:** `call_hook_capture.py` **v3.0.1** (827 lines, md5
`b64aee2b7b0bcc986a72e5e4f176a86c`) · NEW `backfill_call_durations.py` (131 lines, md5
`974ae54952dbc235e5cc6af107e83eeb`).

---

## §0 — WHAT HAPPENED (Session 138, 11 Jul evening → 12 Jul morning, FULL EOS — VPS code changed)

**§0.1 Phase 0/0b clean.** All 7 canonical docs md5-exact; all 14 export-`__7_` files match export-form
hashes, `Probe` absent. Phase 1 could not run at open (12-Jul mails had not arrived; session opened 11-Jul
evening). Session opened with a live read of the full tracker workbook: 3 missed-call callbacks DUE + 62
follow-up items pending (65 total) — the owner's first ask, answered before the build.

**§0.2 Backlog A1 EXECUTED — F-19's scope change against D80 is done.** The two session-start design
decisions were put to the owner and minted:
- **D217** — incoming rows keyed **`IN-<session_id>`** (webhook `payload.id`; same in `call.end` and
  `call.summary`, so the pair collapses to one row; `IN-` cannot collide with phone-timestamp OBD refs;
  no session id → raw-logged and skipped, never guessed).
- **D218** — new final column **`phone10`**: caller's last-10 number, **incoming rows only**; OBD blank
  (their ref already embeds it). Identity resolves at VIEWING time against `Patient_Master` — a caller who
  becomes a patient later links retroactively; no caller NAME is ever written.

**§0.3 The build, and the one live lesson.** v3.0 changed exactly three things (incoming accepted; phone10;
header self-heal) — gate/rotation/reject/OBD untouched; selftest 42→**57**. **First restart (23:34 IST
11-Jul) failed: `Range (Call_Durations!N1) exceeds grid limits ... max columns: 13`.** The tab was CREATED
exactly 13 columns wide; offline selftests cannot see grid geometry. Side effect: ~9 h of every sheet write
(incoming AND OBD) deferring while the service showed green — the raw `.jsonl` held everything, as designed.
**v3.0.1** adds a guarded `ws.add_cols(1)` before the header write. Restart 08:25 IST 12-Jul: `grid widened
to 14 columns` → `header self-heal: added 'phone10' at column N` → `connected ... 205 rows known`.

**§0.4 Backfill — 219 rows, then verified from the artefact.** New `backfill_call_durations.py`: reads every
raw log, uses the receiver's own imported `extract_record` (no copied logic), `call.summary` beats
`call.end`, **insert-only + idempotent**, hard-aborts if the `phone10` header is absent, `--dry-run` first.
Result: 9 files / 874 lines / 0 unparsable / 424 extractable → **inserted 219** (216 incoming since 03-Jul +
3 OBD strays). Independent read of the live tab: **424 data rows (205+219 exact); 216 `IN-` rows all
`category=incoming`, phone10 exactly 10 digits on all; 208 OBD rows phone10 blank on all; zero duplicate
keys; 138/216 incoming carry `recording_filename`** (bridged only — missed calls have none). Newest incoming
row's phone10 ends `…2497` — the top pending callback of 11-Jul. **§K Phase K-2 is UNBLOCKED.**

**§0.5 Findings raised, not fixed (D180).** **F-37** — the VPS health mail's "ACTIONS TAKEN BY WATCHMAN
(last 24h)" showed 04-Jul entries on the 12-Jul mail (window filter or label wrong; cosmetic). **F-38** —
liveness ≠ write-success: nothing surveils the receiver's write path (its own "deferred" log lines, or a
`Call_Durations` freshness probe, are candidate checks). Both wait for the Diagnostics Spec's next opening.

**§0.6 Live reads at close.** 12-Jul VPS health mail (08:00): **ALL GREEN** (9/9 services, 3/3 timers, disk
10 %). 11-Jul evening journal WARN lines prove MyOperator was still delivering on the PREVIOUS key —
CALLHOOK Step 3 (Lokesh, panel update) is genuinely still open; the Step-3 message went out only 11-Jul.

---

## §1 — MENTAL MODELS (what Session 139 must hold in its head)

1. **`Call_Durations` is now dual-population.** OBD rows keyed by our own `client_ref_id`; incoming rows
   keyed `IN-<session_id>` with phone10 filled. Anything that consumes the tab (verdict layer, K-2, D183
   analytics) must branch on the `IN-` prefix or the `category` column — never assume OBD-only again.
2. **`verdict_review.py` still excuses incoming calls (F-18).** With incoming data now flowing, the excuse
   is obsolete — incoming verdicts are the natural next consumer, but that is a design pass, not a patch.
3. **Grid geometry is invisible offline.** A Sheets tab created N columns wide rejects writes beyond column
   N with a 400. Any future header extension must widen the grid first (`add_cols`) — the v3.0.1 pattern.
4. **A green service can be failing its purpose (F-38).** `systemctl status` proves liveness, not
   write-success. Until Diagnostics covers it, a post-deploy check must include the journal's write lines,
   not just `active (running)`.
5. **Template sends are family-specific** (`drmanoj_*` numeric keys, all others named — S137) and
   **`MYOP_AUTH_TOKEN`** is the WABA Bearer's `.env` name. Unchanged, still load-bearing.
6. **Standing:** one deploy = New version on the EXISTING deployment · WebApp.gs frozen (D34) · per-cycle
   data rides inside `getDashboardBundle` (D211) · export-form hashing for editor exports · expected values
   come from the artefact (D172) · an audit finds, it does not fix (D180).

---

## §2 — OPEN BACKLOG (ordered)

**A — Ready builds (owner picks; one per session):**
- **A2. §K K-1 build** — one-tap staff UI per Console Spec v2.2 §K.6 (design complete, zero open inputs).
  Dashboard.html + Callconsole.gs; includes the F-34 residue; runs alongside the old flow; completion
  metric decides. **K-2 (incoming one-tap) is now unblocked** — plan K-1 with K-2 in sight. Natural moment
  for Frontend Doc v3.
- **A3. D205/D213 seen-today WABA** — session-start design per D205; half-session; VPS `wa_approve` scope;
  template `drmanoj_post_visit` locked.
- **A4. F-10 markup cure** — own commit per the audit (~24 fragile sites → row-ID + page-level map).
- **A5 (new, small). Incoming-verdict design pass** — `call_verdict.py` + `verdict_review.py` learn to
  consume `IN-` rows (also retires F-18's stale exemption). Design first; not urgent.

**B — Standing / carried:**
- **CALLHOOK Steps 3–4** — Step-3 message sent (S137); 11-Jul WARN lines prove the panel is still on the
  old key. **Monday:** ONE weekday-traffic `rotate_callhook.sh status` check → if clean AND calls flowed,
  Step 4. (Zero-traffic clean readings are vacuous — S136.)
- **Service-account key rotation** — overdue, highest-standing security risk (Lokesh coordination).
- **AKEY_14 rotation** (guessable).
- **Docterz clinical-data-report migration** — owner decision open (superset confirmed S135).
- **Frontend Dashboard Documentation v3** — write at the next Apps Script pass (A2 is the natural moment).
- **Hindi spelling corrections** — `vitals_page.html` LIB strings (Track 1).
- **Notion orphaned pages** — deferred cleanup.
- **Panel-tidy candidates (Lokesh/panel, no urgency):** stray `daily_account_summary`; which of
  `missedaftercall`/`eng_missedaftercall` fires.
- **F-37 / F-38** — health-mail watchman window; liveness≠write-success surveillance gap. For the next
  Diagnostics/maintenance pass.
- **Watch items (carried, time-gated):** QUOTA HEADROOM first read (Apps Script ~09:43 mail, 12-Jul or
  later) · D183 arrival count (~21:30 digest; exactly ONE = healthy, two = duplicate trigger) · first
  natural WA-tile call verifies D212 · dashboard cold-build latency (one 55 s observation, S136).

**C — Explicitly parked:** AI review layer (A-00…Block A″, two-phase gate, workbook with owner) ·
ClickUp (D17) · Maintenance & SOP project (Diagnostics.gs is live; owner may green-light any session).

---
