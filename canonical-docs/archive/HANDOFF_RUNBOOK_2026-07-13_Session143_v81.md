# HANDOFF RUNBOOK — 13 Jul 2026 · Session 143 · v81 (FULL EOS)

**Files changed this session (all gated md5→COMPILE-OK→selftest on the VPS interpreter):**
`verdict_review.py` **v3-S143** (`280eb2cef9295d89f30c7b84d4c94adb`, 1,837 lines, 144/144) ·
`call_verdict.py` **v2.1 + F-40 comment fix** (`539ea68fb4ce99f0029fdbb53bbf8ebe`, 42/42, logic
byte-identical) · `daily_digest.py` **v1.3-S143** (`63a558d2a73dc5ec22ea8bb772869353`, 74/74) ·
NEW `make_force_keys.py` **v1.1** (one-off, read-only, `9b44831a0a2a2003fac5c4901f7da35c`, 11/11) ·
NEW `force_keys.txt` (41 keys, proven by `grep -cv '^#'` = 41) · crontab **+1** (`0 21 * * *`
verdict_review redraw → `verdict_review_cron.log`). New canonical docs: KB **v1.69** · Umbrella **v1.55**
· this runbook · START_HERE_SESSION_144. No incident file (no live-system fault occurred; F-42 escalation
is data, not a new fault).

---

## §0 — WHAT HAPPENED (Session 143, Mon afternoon 13 Jul)

**§0.1 🟢 BUILD 1 COMPLETE END-TO-END, same afternoon.** `verdict_review.py` v3 (D240): a forced-card band
above every section — any supplied Join Key draws a FULL answer card (MATCH included, cap-exempt by
construction), answered keys collapse to ✓ lines and are never re-asked, missing keys are named never
dropped, and counts/match-rate stay placement-independent. Proof chain entirely on live data: dry-run
without keys (0+2 band, 390 cells), dry-run with the 41 keys (**413 cells = 370+43, predicted before the
run**, dedupe deltas reconciled per section), real redraw, then the harvest round-trip. Spot-checks got
their landing cell AND their one decider: verdict_review picks, marks (★), and writes the `Today's
spot-checks` summary row; `daily_digest.py` v1.3's own picker was **deleted** and it reads that row — its
live dry-run showed the email and the tab naming the same pair. A 21:00 daily redraw cron now precedes the
21:30 digest by design (and a redraw must NEVER run during an active sitting — the harvest-to-delete window
would eat a mid-typing answer).

**§0.2 🟢 THE GROUND-TRUTH LEDGER IS ALIVE.** The owner refereed 18/41 within the hour the band went live.
Verified from a fresh export (not the run log): `Doctor_Verdicts` = 18 rows, 18 unique keys, all stamped
v3; the upsert proved itself **idempotent** (`0 new, 0 updated, 18 unchanged` on the second pass — the
property F-39 demands of every writer). **First calibration numbers ever: 16/18 = 89% raw doctor↔AI
agreement**, and on all 5 staff-vs-AI disagreement cards the doctor sided WITH the AI — the judge's
mismatch findings are signal. Both differs are benign classes (the dikha_chuke↔close_followup soft pair;
AI erring toward more action). D191 gate: **18/100**.

**§0.3 The unpadded-hour trap struck a THIRD file — and the dry-run gate caught it.** `make_force_keys.py`
v1.0 resolved 21/41; every miss had an hour before 10. `Call_Verdicts` stores `9:06`, Excel dressed the
referee workbook as `09:06`, text-prefix matching failed on every single-digit hour. v1.1 compares
minutes-since-midnight; 41/41. Minted as **D240(g): clinic times are compared numerically, never as
text** — this class has now cost three files in two days (digest sort, this matcher, and it masked inside
the S142 grep too).

**§0.4 F-40 CLOSED — and the record corrected.** Four `F-21` mislabels in `call_verdict.py` (not the
recorded three): header L7 + L709/L1034/L1083, all now F-39. Plus the honest v3 banner. Every version
string in the verdict layer now tells the truth.

**§0.5 🔴 F-42 ESCALATED by its own detector: SIX lost conversations on 13-Jul alone** — the two known
pairs plus 13:21 `…8333` (33 s) and 14:54 `1206138695` (19 s; non-standard number shape, note it). The
D239 threshold is 3/WEEK. Build 2 (Flag Investigator + F-42) is S144's first work; recon defined in §2B.

**§0.6 Also this session:** repo drift closed by hash (owner committed the S142 files; verified, then
immediately re-owed for S143's three) · D241 Insight Harvest Register minted (14 analyses; the five
gist-tile feeders named — Pass 6 now has data AND content plan) · Umbrella's END marker found stale since
v1.51, corrected · VPS venv Python 3.9 EOL noted as Tier-C housekeeping.

---

## §1 — MENTAL MODELS (deltas only; v80 §1 still holds)

- **A recurring defect earns a standing rule, not a third fix.** Unpadded hours have now bitten three
  files. D240(g) exists so the fourth file never gets written wrong.
- **One decider beats two agreeing deciders.** Two scripts computing "the same" seeded pick from pools read
  at different times WILL diverge silently. Delete the second picker; make everyone read the first's
  output.
- **Idempotence is provable for free.** Run the writer twice; the second run's `0 new, 0 updated, N
  unchanged` line is the proof. Cheap enough to demand of every writer from now on.
- **The referee's first sample validates the judge's disagreements, not its agreements.** 89% raw agreement
  is nice; the doctor siding with the AI on all five staff-disputes is the number that matters — it means
  the mismatch list is worth staff coaching time.
- **A detector's threshold can be overtaken same-day.** D239 said 3/week; the data said 6/day before the
  Investigator was even built. Build order was right: detector → threshold → investigator.

---

## §2 — OPEN BACKLOG (ordered)

**A. Observe tonight/tomorrow (no action) — FOUR proofs now:** 21:00 `verdict_review_cron.log` exists and
shows a clean redraw (first scheduled firing) · 21:30 digest arrives (first cron-fired; spam-check once;
spot-check section should carry the SAME pair as the tab; suggestion line should carry the six F-42 calls)
· 08:45 write-probe log exists (`/root/wa/call-hook/write_probe.log`, its first real scheduled PASS) ·
11:00 pulse fires by cron.

**B. Session 144 build (owner-approved order):**
1. **Flag Investigator (D239) + F-42 investigation** — one build. Recon first, from artefacts: (a) does
   `Call_Durations` carry the MyOperator session_id or is it derived from `client_ref_id`; (b) exact Call
   API search shape from `MyOperator_Call_API_Master_Reference_23_june_.md`; (c) the hook log's kick trail
   for the six 13-Jul events. Locked defaults: self-heal ON · every 30 min 09:00–20:00 · results file the
   digest READS · ≥3 provider-never-recorded/week → digest says raise with Lokesh. Note `1206138695`'s
   number shape while in there.
2. **GitHub commits owed:** verdict_review v3 · call_verdict (F-40 fix) · daily_digest v1.3 ·
   make_force_keys v1.1 + the S143 canonical docs (git kit zip in outputs has all of it staged).
3. Owner continues the referee sitting (23 cards remain; band shrinks; nothing re-asked). Watch 18/100 →
   the D191 Phase-2 gate.
4. Digest cosmetics still queued (judged rows show Duration "-").

**C. Standing:** CALLHOOK Steps 3–4 with Lokesh (Step 4 locked until Step 3) · service-account key rotation
(Tier A1, Lokesh) · AKEY_14 · Hindi spellings in vitals_page.html · F-37 health-mail window · repo naming
tidy · K toggle-removal watch · **Docterz export migration (owner decision pending — D241 #10 is the
standing argument to close it)** · **NEW: VPS venv Python 3.9 EOL upgrade (Tier C — schedule deliberately;
venv rebuild = every pipeline retested)** · then A8 / D223 gist tile (feeders named in D241; consumes the
Investigator's results file too).
**Watch:** ai-only bucket day-over-day (K-adoption) · F-42 pattern count once the Investigator runs ·
referee progress toward 100.

**Session counter: 143 CLOSED (full EOS). Next session: 144.**
