# HANDOFF RUNBOOK — v152 · Session 220 close · 02 September 2026 IST (evening)

**Tier 0.** §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline ·
§4 the boundary. **§2 is the close-time snapshot; `OWNER_TODO_LIVE.md` is the always-current truth.**

---

## §0 — WHAT HAPPENED AT S220

**The intent session. NINE INSTALLS ON THE LIVE BOX in four hours, twenty pins predicted offline and
read back identical, one read back as declared — and the first live day through all of it reconciled
to the rupee by 22:48.** It opened on F-277 (the ingest name-check, the owner's queue-head) and was
reframed by him within the first hour: *"rethink … the most mature way … catch any intent issues from
past data and constant monitoring, because this is a sum which anyone can exploit."* The whole
returns system was measured on the live db copy before anything was designed
(`S220_RETURNS_INTENT_DESIGN`, the brief with his eleven rulings folded in §8).

| kit | what went live | pin after |
|---|---|---|
| `S220_F277_NAMECHECK` | attach by ID only; a disagreeing name RECORDED (`identity_dispute`); verdict "identity disputed" — amber, a question | finance_ingest **d5ff50ad** · audit **d693c0b4** |
| `S220_REJOIN_RETURNS` | 17 split returns since 18-Jun re-keyed to their CNs; audit 46 → 29 rows on those days; money untouched | data (backup beside the db) |
| `S220_LARGE_RETURN_GATE` | `returns.large_p` enforced — the owner's OK regardless of verdict; `stock_spot_check`, the deterrent | escalate **c4864500** |
| `S220_RETURNS_METRICS` | the gist line: rate vs last month · examinable % · flagged % · to look at | — |
| `S220_OWNER_ENGLISH` | the coverage table and the correction instruction in English | — |
| `S220_INTENT_SCORER` | **`finance_intent.py` NEW** — seven signals vs own baselines, nightly 01:30; first run 21 signals, 5 to look at | finance_intent **6f11548a** |
| `S220_DAY_TOTAL_TRUTH` | **found by the owner**: the Marg total ADDED the return (F-281); parked bills in neither total (F-282); truth 17,644 = declared | finance_app **f7dd9e57** (read back) |
| `S220_CARD_PARKED_BILLS` | *bina pehchaan ke bill (N)* expands — bill · naam · ID · phone · ₹ | — |
| `S220_FULL_MOBILE` | *"phone full 10 for me and Darpan"* — the lines CSV carries the mobile (D363) | marg_report **f9370dde** · darpan_app **43abdd58** · darpan_card **aeb4fd7d** · hub **e1652297** |

### The numbers that shaped the design

191 returns / ₹65,360 against ₹30.9 L sales (Apr–Aug) · the monthly rate **1.4 → 2.9 %** — **not more
returns (43 · 31 · 39 · 43) but bigger ones**: average ₹232 → ₹433, ₹1,000+ returns **0 → 6 in
August, 45 % of the month** · 55 % of return ₹ on WALK-IN historically, **0 % in September** ·
**July 71 % examinable / 50 % flagged; August 75 % / 29 %** — the two lines now on the card ·
**no user and no time on any Marg export** — the exploitable seam · 3 single bills vanished in
five months; 66 "gaps" were two missing May export days.

### The first live day

Exported 21:44 on the medical PC → captured in seconds → pulled 21:50 → ACCEPTED → applied itself
when the owner filed the day at 22:26 (M1). 27 bills, 20 accepted, **7 parked** (a name, no clinic
ID, confidence 0.5), one CN. The portal read 17,674 and Darpan's card 15,614 against a declared
17,644; the owner said *"glitch"*, the code was read first, the db confirmed both faults to the rupee,
and both screens read 17,644 within the hour. The seven parked bills now show on his card with the
identity owed; they gain their full mobiles the moment 02-Sep is exported again.

**Decisions (his words):** D362 cash-only refunds · D363 the full mobile on the counter's screens ·
D364 the past is scored, never worked · D365 the ₹1,000 gate and the spot count · D366 the owner's
console is English. **Findings:** F-277 CLOSED; F-280 … F-285 minted (the stale repo copy · the
sign-blind total · the vanished parked money · the confidence gate vs D355 · a false Phase-0
claim about the manifest, the assistant's own, caught at the close · the compile residue on the owner's disk).

---

## §1 — MENTAL MODELS EARNED HERE

1. **The owner reframes; the assistant measures before it designs.** A three-option ruling on one
   verdict was the wrong size of question. The right first move was to measure the whole system on
   the live data and bring goals with numbers.
2. **Predict the pin offline; read it back from the box.** Reproduce the live bytes by applying the
   previous kits' patchers to the previous pins (S218 bases + S219 M7 patchers → the S219 pins,
   md5-proven), anchor on those, predict the result. Twenty for twenty. When the bytes are not held
   offline (finance_app), say "declared pending" and read back — never guess a pin.
3. **The first live day is the walk nobody can script.** Two screens finally reading the same day
   disagreed and exposed a sign error and a blind spot that had been live since S180. A system that
   surfaces its own defects on day one is working.
4. **Two errors that cancel are two errors.** "Variance 30 ✓" was 17,674 (return added) against
   17,644 (the truth) — the tolerance hid it. Read the view that already knows the answer (D349).
5. **A "past" flag is not a mute.** The scorer's first LOOKs are inherited from August because
   their windows end today. Say so. The number that matters is a week from now.
6. **The gate that refuses is doing its job.** The F-185 gate refused twice tonight (a test string;
   test literals) and the publish gate once (a `__pycache__`) — each refusal was correct and each
   fix was one line. Never widen a gate to make it quiet.
7. **Writes on the owner's disk leave residue the shell cannot remove.** Compile, test and hash in
   the workspace; `git --no-optional-locks`; move the result once (F-233, F-285).

---

## §2 — THE LIVE BACKLOG (close-time snapshot)

**⭐0 — the owner:** the close publish (below) · one word on the whole-history re-join (*"history
too"* = 94 more pairs Apr–Jun) · export 02-Sep once more tomorrow so the seven parked bills gain
their full mobiles · give Darpan his sheet · tap OK on any ₹1,000+ return the card shows · the
rulings still owed (S214/S215/S216 candidate sets, F-244).

**⭐1 — the build order (Layer C and the seam):**
1. **Darpan's Hindi list on the Vaapsi Desk** — identity disputes, identity needed, spot counts:
   one question per row, three buttons (यह सही है · बिल ढूँढो · पता नहीं); unanswered 2 days →
   escalates.
2. **The D355 ladder at ingest** (F-283) — name + mobile lookup against the master BEFORE parking;
   park only what the ladder cannot resolve. 7 of 27 bills were parked on 02-Sep.
3. **Marg's user-wise register on the router** (the owner: it exists; every user entry-only) — WHO
   keyed each bill; the per-person dimension the scorer is waiting for.
4. The intent scorer's second week: the first measurement that means anything; then the
   owner-absent-day signal once attendance reaches `day_entry`.
5. Then, as before: M3 purchase tables (build yes, feed no) · M4 Phase B · M5 · M6 · the F-269 route
   patch · Docterz feed Phase 1 · the August staff close · the scanner A5 vertical resize.

**Standing holds:** AUGUST PURCHASE IS PROVISIONAL · NEFT portal WAITS · the hub's shape is not
reopened (extending the returns card's drill-down is allowed — owner, 02-Sep).

---

## §3 — INSTALL DISCIPLINE (as S219, extended)

- Anchored patchers, verbatim anchors, refuse-unless-exactly-once, `.bak` beside the file, compile
  check, "already patched" on re-run. One paste per kit, every current pin guarded by `test`.
- **Reproduce the live bytes offline before anchoring** (previous bases + previous patchers → the
  current pins, md5-proven). Predict every pin. A pin not held offline is declared pending, never
  predicted.
- Selftest on a COPY of the live db (`/tmp`), then a LIVE-SHAPE walk through the real entry point.
  A browser render in real Chromium for any page change (the S209 lesson: intact is not valid).
- Test numbers are assembled at runtime (`"98765" + "43210"`), never literal — the F-185 gate is
  right to refuse them.
- No compile, no `git status`, nothing that writes, inside a kit folder on the owner's disk.

---

## §4 — THE BOUNDARY

Built and live: everything in §0. Designed, measured, and deliberately not built tonight: the
D355 ladder at ingest (F-283), Darpan's Hindi list, the user-wise register, return-then-resale
(no discriminating power — 171 of 204 lines resell within 30 days), owner-absent-day concentration
(no attendance on `day_entry`). The whole-history re-join runs on one word. The scorer is
owner-only until it has proven itself.
