# Call Console Evolution Spec — v1.3 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward everything in v1.2 unchanged and records Session 53: the D66 vanish-on-file as built (v18.15), the **duration gate** that replaces the self-declared Talked gate (D77), and the **sticky-on-staff** 3-strike model (D78). Where this delta describes shipped behaviour it is authoritative.

---

## §D — Vanish-on-file, AS BUILT (v18.15; D66)

- **On Save of a completing/escalating outcome:** the tile is **removed immediately**; the write is **held 10 seconds**; a bottom **UNDO** toast counts down.
- **UNDO within 10s:** tile returns exactly as it was, counter reverts, **nothing is written**. If the page closes / signal drops in the window, the write never fires and the patient **re-surfaces on the next poll** — the safe failure (never a fake "done").
- **Section-wise progress header** at the top of the follow-up card: `Today's follow-up calls — total N / (N−x) done`, a line per band (Due Today, Grace Period, …), and a timestamp. Driven by server `counts` (open + settled) plus a new **additive** `sectionDone` per-band count in `getFollowups`. Sent-back band counts in the overall total but has no breakdown line.
- **Retry outcome exception:** only **"Connected but couldn't communicate"** stays on the list (mirrors `WebApp.gs` `FU_SETTLING` + `FU_ESCALATING`); every other outcome vanishes.
- Surface: `Dashboard.html` only + the additive `getFollowups` field. No new writer.

## §E — The DURATION GATE, DESIGN (D77; supersedes the v18.14 self-declared Talked gate; build next)

**Problem:** the v18.14 gate revealed the outcome dropdown after a self-declared **✅ Talked** tap, with **no check the call connected** — so a ring-only call could reach an outcome.

**Fix:** outcome availability is driven by the call's **real duration**, read from the MyOperator **`call.end` webhook** (real-time; the KB's documented alternative to the 30-min-lag poll). No Talked/Missed buttons.

**Tile flow:**
1. Staff taps **Call** (OBD; agent leg first, then patient). The dashboard already receives the call's unique **`reference_id`**.
2. Call ends → the `call.end` webhook (received on the VPS) reports that call's **`duration`** (int seconds), **`status`** (`bridged`/`missed`), and **`ref_id`** (= our `reference_id`).
3. Tile shows **"checking call…"** briefly, then resolves by duration:
   - **< threshold (~10–15s)** → **📵 Missed call · time/date** + **↻ Call again**; **no outcome field.** Counts toward the strike tally.
   - **≥ threshold** → the outcome dropdown appears.
- **Threshold** is a config knob and doubles as a **script-adherence** check (the mandated opening line takes ~10–15s to deliver).
- **Exact-call binding** via `reference_id` — never fuzzy number+time matching.
- **Determined dead-air lies** (line held open with no real conversation) are out of scope for the gate — caught post-hoc by the **AI-verdict layer (D62)**.

**Build shape:** VPS **call-receiver** (same pattern as `wa_receiver.py`) storing `{reference_id → duration, status}` from `call.end`; a new server fn in **`CallConsole.gs`** (per D34) the tile polls after a call; `Dashboard.html` tile logic. Step 1 is **passive capture** of one real `call.end` body to confirm per-account field names (vendor examples are from a sample company) — **no test calls needed.**

## §F — STICKY-ON-STAFF 3-strike, DESIGN (D78; supersedes the v18.4 doctor-only exit; build after the gate)

- A patient at 3 misses **does not leave** the staff worklist — it drops to a distinct **bottom band** ("📵 Sampark nahi ho raha — tried N×"), out of the active-call flow but never hidden.
- **Next day and after:** the patient **reappears in that band with cross-day context** — total tries, last attempt times, WhatsApp-sent date. The **miss count accumulates across days** (no daily reset).
- **3rd strike:** fires the **WABA template** to the patient + **snoozes X days** (pre-decided). Active re-calling wakes on a patient reply, X days elapsing, or a staff "Try again now."
- One-tap staff options, nothing auto-vanishes: **Try again now · Reached another way (settles) · Send to doctor (escalates with context).**
- **Build need:** a **cross-day miss counter** in the worklist assembly (today it's per-day only).

## CHANGELOG
| v1.3 | 03 Jul 2026 (Session 53) | D66 vanish-on-file as built (v18.15); duration-gate design (D77) replacing the self-declared Talked gate; sticky-on-staff 3-strike (D78). |
| v1.2 | 03 Jul 2026 (Session 51) | Missed-call binding (D68) + Escalations-card overhaul (D69). |
| v1.1 | (Session 25) | As previously recorded. |
