# Call Console Evolution Spec — v1.4 (delta)
**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document.** Carries forward everything in v1.3 unchanged and records Session 54: the **duration gate AS BUILT** (v18.16, D82) — which supersedes the §E *design* in v1.3 — plus the real-body corrections (D81) and the new `call-hook` receiver (D80). Where this delta describes shipped behaviour it is authoritative.

---

## §G — The DURATION GATE, AS BUILT (v18.16; D82; supersedes the §E design in v1.3)

**Shipped end-to-end in three phases. Outcome availability is now driven by the call's MEASURED result, never a self-declaration.**

### G.1 The pipe (D80)
- New walled-off VPS service **`call-hook.service`** — gunicorn `-w 1` on `127.0.0.1:8098`, public route **`/mo-callhook`** (secret-gated with `?key=`, OLS-proxied via a `context /mo-callhook` block; path chosen to share no prefix with `/call`).
- MyOperator **Webhooks v2 → Add New Webhook → Call Ended (`call.end`) + Call Summary (`call.summary`)** point at it. Additive, separate from the WABA token — no vendor escalation, no token rotation.
- The service raw-logs every body (owner-only `.jsonl`), then **upserts one row** into the one-writer **`Call_Durations`** tab, keyed on **`client_ref_id`** (so call.end + call.summary collapse to one row). **No phone number is written.** Auto-creates the tab, auto-discovers the `patient-mirror` service-account key, connects at startup, and is degrade-safe (raw-log + 200 even if Sheets is down; never retry-storms). **Skips incoming / non-OBD calls.**
- Helper `peek_callhook.py` prints a captured body with the patient number auto-masked.

### G.2 The corrected field mechanics (D81 — from real captured bodies)
- **Join key = `payload.client_ref_id`** — the value our dialer stamps (`make_reference_id` in `call_api.py`) echoes back here. The webhook's **`ref_id` is MyOperator's OWN UUID** — not ours. `session_id` is a backup.
- **Gate signal = the CUSTOMER leg** (`legs[]` where `type == "customer"`): its **`talk_duration`** and **`result`**. Top-level `duration` includes agent pickup + ring time, so it is *not* the signal. The gate requires **`result == "answered"`** — a real call showed `result:"connected"` with `answered_at:null` at 11 talk-seconds (reached, not answered).
- `Call_Durations` columns: `client_ref_id, ref_id, session_id, category, status, total_duration, customer_result, customer_talk_duration, customer_ring_duration, recording_filename, ended_at_ist, captured_at_ist, source_event`.

### G.3 The gate decision (server, one const)
`CallConsole.gs::getCallDuration(key, clientRefId)` (read-only; **WebApp.gs untouched**, D34) returns:
```
allowOutcome = (status == "bridged") AND (customer_result == "answered") AND (customer_talk_duration >= CC_GATE_MIN_TALK)
```
`CC_GATE_MIN_TALK = 15` (seconds). The 15s doubles as the opening-line **script-adherence** check. Any ambiguity or missing field → `allowOutcome:false` (fail-safe).

### G.4 The tile flow (Dashboard.html v18.16)
1. Staff taps **Call** → `fuDoCall` places the OBD call and **captures that call's `reference_id`** (stored per tile, persisted per-day).
2. Tile shows **⏳ "Checking the call… the outcome unlocks once it connects"** and **polls `getCallDuration` every 6s** (fail-safe timeout 3 min).
3. When the `Call_Durations` row appears:
   - **bridged + answered + talk ≥ 15s** → the **outcome dropdown** unfolds (unchanged outcome UI).
   - **missed / not-answered / talk < 15s** → **📵 "Call didn't connect — patient talked Xs (need 15s)"** — no outcome.
   - **no row after 3 min** (webhook hiccup, rare) → **⏳ "Couldn't confirm — Call again"** — no outcome.
4. **Manual fallbacks preserved throughout:** **↻ Call again** and **📵 No answer** stay available in every not-yet-connected state. The self-declared **✅ Talked tap is removed.**
5. **Reload-safe:** a call still awaiting its result resumes polling after any full render (`fuResumePolls`).

### G.5 Scope boundary
- The gate catches **no-call / ring-only / too-short / not-answered** outcomes at the source (Layer 1, prevention).
- **Determined dead-air lies** (line held open, no real conversation) are out of scope for the gate → caught post-hoc by the **AI-verdict layer (D62)**, and flagged nearer-term by the **missed-call fabrication sentinel** over the Call-Logs register (Layer 2, detection).

### G.6 Deferred
- **PHI base swap:** `client_ref_id` currently embeds the patient mobile (the dialer's `reference_id` base = the number). Deferred (the operational sheet already holds mobiles); when done, the gate still matches on the full returned reference_id regardless of base.

## CHANGELOG
| v1.4 | 03 Jul 2026 (Session 54) | Duration gate AS BUILT (v18.16, D82) — supersedes the §E design; real-body corrections (D81, join key = `client_ref_id`, signal = customer-leg talk/`answered`); new `call-hook` receiver + `Call_Durations` (D80). |
| v1.3 | 03 Jul 2026 (Session 53) | D66 vanish-on-file as built (v18.15); duration-gate design (D77); sticky-on-staff (D78). |
| v1.2 | 03 Jul 2026 (Session 51) | Missed-call binding (D68) + Escalations-card overhaul (D69). |
| v1.1 | (Session 25) | As previously recorded. |
