# Follow-Up Voice Bot — Pipeline Architecture & Costing Plan
**Dr. Manoj Agarwal Clinic, Bareilly · v1.1 · 30 June 2026**
**Owner:** Dr. Manoj Agarwal · **Engineer:** Claude (per session)
**Status:** PLAN ONLY — no code written yet. Decisions in §5 are now LOCKED.
Build proceeds stage by stage, only on explicit "go".

> **Changes from v1.0 (this version):**
> - §5 decisions all resolved (see the locked table).
> - **Inbound calls now processed IN PARALLEL** with outbound — same plumbing,
>   forks only at analysis. Inbound = the bot's *listening* half + the KB.
> - **90-day purge of raw transcripts is now an automated, audited job** (spec in §2a).
> - **Sarvam Samvaad confirmed as the bot** (Option A), Option B kept as fallback only.

---

## 0. Two headline findings (unchanged — they set the budget)

1. **No 5 TB storage problem.** Only *connected* calls have audio (~25–40/day,
   ~1 min each, ~0.5 MB/min) → **~5–15 GB over 10 months**, not 5 TB (~300× off).
   Existing Workspace (Business Standard = 2 TB pooled) holds it many times over.
   Recordings also persist on MyOperator indefinitely; Drive = working copy + backup.

2. **Transcription is near-free.** Sarvam STT = **₹30/hour** (diarization +
   Hinglish included). All 10 months ≈ ₹4,500–9,000; a mining sample ≈ ₹250–500,
   inside the ₹1,000 free credit.

**The cheap parts are storage + transcription. The real cost is the bot (Stage 6).**

---

## 1. The shape — ONE pipeline, forking at analysis

```
 MyOperator cloud (recordings; ~24h signed links; infinite retention)
        │  Stage 1: pull → archive  (BOTH directions)
        ▼
 Google Drive: raw .mp3 archive (PHI, restricted)  +  manifest.csv (direction-tagged)
        │  Stage 2: segregate & sample  (tag inbound vs outbound; keep both)
        ▼
 Transcription queue  (direction-tagged; both lanes)
        │  Stage 3: Sarvam STT (Hindi/Hinglish, diarized, timestamped)
        ▼
 Raw transcripts (PHI)  ── Doctor+Shavez only ── AUTO-PURGE @ 90 days (§2a)
        │  Stage 4: DE-IDENTIFY → then analyse
        ▼
        ├── OUTBOUND lane → how staff talk → the bot's SCRIPT (speaking half)
        └── INBOUND  lane → why patients call → INTENT TAXONOMY / KB (listening half)
                                   │
                                   └── KB feeds back into the bot's comprehension
        │  Stage 5: structured bot spec (script + tree + templates)
        ▼
 Doctor review gate → Stage 6: Sarvam Samvaad bot (calls, talks, captures outcome)
```

**Why inbound runs in parallel (the v1.1 decision).** The two corpora teach the
bot different halves of the same conversation:
- **Outbound** (receptionist → patient) teaches the bot **to talk** — openings,
  framing, how the best agents phrase the nudge.
- **Inbound** (patient → clinic) teaches the bot **to understand** — because that
  is where patients *lead* with their real words ("kitni door hai", "dusri jagah
  dikha chuka", "kitna kharcha", "bahar gaya hua hoon", "kaunsi dawai"). Those
  patient-side utterances ARE the branches the outbound bot must recognise.

Mining only outbound → a bot that speaks well but listens poorly. The cost of
adding inbound is ~nothing because it is the **same** archiver, transcription,
and de-id step; only the analysis splits in two. **Discipline:** inbound KB work
must NOT gate the outbound bot going live — insights flow in as they mature; ship
Phase 1 when its script is good enough.

---

## 2. Stage-by-stage

### Stage 1 — Raw recording archive (MyOperator → Drive), BOTH directions
**Job.** Pull recordings for a date range; store as an organised, de-duplicated
archive in a restricted Drive folder; write a direction-tagged manifest.

**How it works (proven recipe).**
- Read `Call_Feed`; keep `Status == connected` (missed = no audio). **Keep both
  `incoming` and `outgoing`** (v1.0 kept incoming only — now we keep both).
- `Call_Feed` lacks the MyOperator `filename`, so per candidate, re-query
  `POST /search` in a tight window around `Start_Unix`, match by phone10, accept
  only `status == 1`, recover `filename`.
- `GET /recordings/link?file=…` → download the `.mp3` immediately (link ~24h;
  recording itself persists).
- Save named by **last-4-masked phone + start_unix** (never full numbers).
- `manifest.csv`: masked phone, time, agent, duration, **direction**, local file.

**Needs.** `MYOP_TOKEN` (Calling/Logs `3f76…`, from `/root/wa/.env`); service-
account key with sheet read access; `gspread`, `requests`. Read-only; writes
nothing to the sheet; places no calls.

**Cadence.** One backfill (10 months), then a nightly sweep.

**Archive decision (LOCKED): KEEP the Drive archive** (restricted folder, 3-2-1
backed up). It is tiny and lets us re-run analysis without re-pulling.

**Status:** puller drafted + syntax-checked; needs the both-directions + Drive-
upload variant and the backfill run.

---

### Stage 2a — Automated 90-day purge of raw transcripts (LOCKED, audited)
**Job.** Enforce the retention rule automatically so PHI never lingers, while
the *useful* (de-identified) layer is kept forever.

**Two separate controls — do not confuse them:**
- **WHO can see raw transcripts** = permissions (one-time): restricted to
  Doctor + Shavez. Set once on the folder/path.
- **HOW LONG raw transcripts live** = retention (the automated part below).

**The purge job (three rails):**
1. **Quarantine, not instant delete.** Day 90 → raw transcript MOVES to
   `quarantine/` + a log line is written. Day ~97 → hard delete. The ~1-week gap
   lets a mistake be caught before it is irreversible.
2. **Touches ONLY raw identifiable transcripts.** De-identified transcripts and
   aggregate insights are NOT PHI → kept indefinitely → the purge never sees them.
   (This is what we actually learn from; we keep it.)
3. **Proves it ran.** Each run writes an audit line (count + date, **no PHI**)
   that the planned Supervisor (`doctor.py`) surfaces in the daily "all systems
   normal" ping — so a silently-stopped purge can't hide. **Log-only mode first**:
   it shows which files it *would* move before it is ever allowed to move/delete one.

**Where it lives (LOCKED): on the VPS** as a systemd timer (engine room), because
transcription output is files on the VPS. Same care class as other destructive
paths.

**Raw AUDIO retention (LOCKED): age out at 6 months** (longer than transcripts;
the originals still live on MyOperator). Same quarantine-then-delete pattern.

**Status:** new; spec locked here; build is a small VPS timer + script (later stage).

---

### Stage 2 — Segregation & sampling for transcription (BOTH lanes)
**Job.** Decide which calls to transcribe, per lane.

**Filters / buckets.**
- **By direction** — tag every call; route to the outbound lane or inbound lane
  (both are processed now; the tag drives the analysis split, not a drop).
- **By duration** — drop < ~10 s (no content).
- **By outcome** (outbound) — join `Followup_Outcomes` so each transcript carries
  its real result → learn which phrasing actually brought patients back.
- **By agent** (outbound) — sample across staff to learn the *best* patterns.
- **By condition** — sample across diagnosis groups (trauma vs chronic OA).
- **Inbound first-pass** — broad sample across times of day / callers to surface
  the full range of reasons people call.

**Sample size.** Outbound: ~300–800 calls. Inbound: ~300–800 calls. (Still tiny
in rupees.)
**Output.** `to_transcribe.csv` (direction-tagged) subset of the manifest.

**Status:** new (small) logic; not built.

---

### Stage 3 — Transcription (Sarvam STT), both lanes
**Job.** Sampled `.mp3`s → timestamped, speaker-separated text, direction-tagged.

**Why Sarvam.** Indian-language native, **Hinglish/code-mixing**, **diarization**
+ timestamps included, **₹30/hour**, **India-sovereign** (matters for PHI).
Model line: Saarika / Saaras.

**Output per call.** Speaker turns (Agent / Patient), timestamps, linked to the
manifest row (masked phone, direction, outcome, condition).

**Cost.** Both samples ≈ ₹400–800 total; everything ≈ ₹4,500–9,000 (see §4).

**Status:** Sarvam pipeline "PARTLY built"; wire to the queue + output format.

---

### Stage 4 — Safe analysis (DE-IDENTIFY FIRST, then fork)
**Job.** Find the patterns, never exposing identity in any aggregate/cloud surface.

**Fixed safety order:**
1. **Transcribe** (audio → Sarvam only). Raw transcript = PHI.
2. **De-identify** — strip names, numbers, addresses, Clinic IDs → role tags
   (`<PATIENT>`, `<AGENT>`, `<NUMBER>`). Keep conversation *structure*, lose identity.
3. **Only de-identified text** → clustering / NotebookLM / Claude. Outputs carry no PHI.
4. **Raw transcripts** → Doctor + Shavez only → **auto-purged at 90 days (§2a)**.

**Then the analysis forks into two lanes:**
- **OUTBOUND lane → the bot's SCRIPT (speaking half):** best openings; how staff
  handle "call later", "already went elsewhere", "coming tomorrow", "too far",
  "cost?", language switching; what *correlates with the patient returning*; the
  branch points the humans actually follow.
- **INBOUND lane → INTENT TAXONOMY / KB (listening half):** the real reasons
  people call (appointment, directions, report query, pain/emergency, cost/
  Ayushman, medicine doubt, …) in the patient's own words. **This KB feeds back
  into the outbound bot's comprehension** AND seeds IVR routing (D10 urgent path),
  WhatsApp auto-replies, and a future inbound bot. One corpus, many consumers.

**Where it runs.** De-identified text only — in this Claude project (no extra
spend); durable insights → Notion (Clinic HQ).

**Status:** de-id clustering "PARTLY built"; the de-identify step is the key new piece.

---

### Stage 5 — Structured bot spec (insight → design; a document, not a bot)
**Deliverables.**
- **Conversation flow** (decision tree): open → identify → purpose → handle the
  common branches → capture outcome → close. Branches drawn from BOTH lanes
  (outbound phrasing + inbound intents).
- **Response templates** per branch, in the clinic's real Hindi/Hinglish voice
  (lifted from the best agents — mined, not invented).
- **Guardrails:** no clinical advice, no triage; warm "the clinic caring", never
  call-centre; hand off to a human on anything unexpected; honour opt-out.
- **Outcome model:** the exact outcomes the bot writes back to `Followup_Outcomes`
  (reuse existing — returned / said-later / declined / no-answer / coming-on-date).

**Doctor review gate.** You approve the script + tree before a single live call.

**Status:** new; the bridge from data to product.

---

### Stage 6 — The voice bot: **Sarvam Samvaad (LOCKED, Option A)**
**Job.** Place outbound follow-up calls, speak the approved script, listen,
branch, record the outcome to the ledger.

**Decision (LOCKED).** Build on **Sarvam Samvaad** — managed voice agent
(telephony + STT + LLM + TTS + analytics), Hindi-native, sub-second latency,
same vendor as transcription, India-sovereign. **Option B (assemble it over
free MyOperator OBD) is kept ONLY as a fallback** if Samvaad pricing/availability
disappoints.

**Gate before committing:** confirm Samvaad self-serve availability + current
price (it was enterprise/waitlist, opening to self-serve now). One sign-up /
message to Sarvam.

**Phase 1 is narrow:** one well-defined list (recommended: grace-period
follow-ups), one approved script, capture outcome. Expand only on earned trust.

**Status:** vendor chosen; nothing built; availability gate pending.

---

## 3. What already exists vs what's new

| Stage | Already have | New work |
|---|---|---|
| 1 Archive | Proven API recipe; puller drafted; creds | Both-directions + Drive-upload variant; backfill |
| 2a Purge | D1 policy; planned `doctor.py` | VPS timer + audited purge (quarantine→delete); log-only first |
| 2 Segregate | `Call_Feed`, `Followup_Outcomes`, manifest | Small direction-tagged filter/sample script |
| 3 Transcribe | Sarvam pipeline "PARTLY built"; account | Wire to queue; output format |
| 4 Analyse | De-id clustering "PARTLY built"; Claude; Notion | De-identify step (key); two-lane clustering |
| 5 Bot spec | Outcome model; demographics lens; D1 | Flow + templates document |
| 6 Bot | MyOperator OBD proven & FREE; Sarvam vendor | Samvaad pilot; doctor-approved script |

---

## 4. Costs, by section (INR, current as of Jun 2026)

> Sources: Sarvam published API rates (sarvam.ai/api-pricing); Sarvam voice-agent
> ~₹1/min is a third-party developer figure (indicative — Samvaad self-serve
> pricing still firming as it opens); Google Workspace storage tiers
> (workspace.google.com/pricing). All exclude 18% GST.

### One-time / setup (mining phase)
| Item | Estimate | Notes |
|---|---|---|
| Drive storage, 10 months audio | **₹0** | ~5–15 GB; fits existing Workspace |
| Transcribe mining samples (both lanes, ~600–1,600 calls) | **₹400–800** | Covered by ₹1,000 free credit |
| Transcribe everything, 10 months (optional) | **₹4,500–9,000** | Only if you want the full corpus |
| Analysis / clustering | **₹0** | This Claude project, on de-id text |
| Build effort | **₹0 cash** | Claude sessions |

### Recurring (once the bot is live) — the real cost
| Item | Estimate / month | Notes |
|---|---|---|
| Samvaad conversation layer | **₹2,000–6,000** | ~40–80 calls/day × ~2 min × ~₹1/min indicative; firm up with Sarvam |
| Telephony (call leg) | **bundled via Samvaad, or ₹0 via MyOperator (fallback)** | MyOperator OBD free on SUV plan |
| Verification-loop transcription | **~₹100–500** | On-demand only (D1) |
| Storage | **₹0** | Within existing Workspace |

### Costs to keep on the radar
- **Samvaad onboarding/availability** — self-serve rolling out; may carry a
  minimum or need a sign-up call. Availability risk, not just price.
- **DPDP Act 2026** — patient audio leaving to Sarvam should sit under a clear
  data-processing understanding + the retention/purge rule (now automated, §2a).
  Note it in Clinic HQ.
- **Telephony minutes if ever off MyOperator** — keep the MyOperator-free lever.
- **Human review time** — the real bottleneck: Doctor/Shavez for the script gate
  and early-call spot-checks.
- **TTS / translation** — bundled or trivial (TTS ₹15–30/10K chars; translation
  ₹20/10K chars). Not worth tracking.

**Bottom line:** mining ≈ free; a live bot ≈ a few thousand rupees/month, bounded
by how many calls you let it make.

---

## 5. Decisions — LOCKED (30 Jun 2026)

| # | Decision | Locked outcome |
|---|---|---|
| 1 | Bulk mining = de-identified Insight use (D1)? | **YES** — Insight loop, de-identified/aggregate |
| 2 | Keep full Drive archive vs process-and-discard? | **KEEP** the archive (restricted, 3-2-1) |
| 3 | Outbound first vs parallel inbound? | **PARALLEL** — both lanes; fork only at analysis |
| 4 | Bot: Samvaad vs assemble? | **SAMVAAD (Option A)**; assemble = fallback only |
| 5 | First bot scope | **Grace-period follow-ups** — narrow, high-value, clear script |
| 6 | Raw-transcript retention | **Auto-purge @ 90 days**, quarantine→delete, audited, VPS timer |
| 7 | Raw-audio retention | **Auto-age @ 6 months**, same quarantine pattern |
| 8 | Hard line | Bot never advises/triages; cares, confirms, captures, hands off; **doctor approves script before any live call** |

---

## 6. Recommended sequence (build order, each on explicit "go")

1. Stage-1 archiver — both directions + Drive upload; backfill 10 months (one run).
2. Stage-2 sample (both lanes) → Stage-3 transcribe ~600–1,600 calls (~₹400–800, free credit).
3. Stage-4 de-identify → two-lane clustering → findings into Clinic HQ.
4. Stage-2a purge job — build in **log-only mode first**, confirm file selection, then arm.
5. Stage-5 draft bot script + decision tree (both lanes) → **doctor review gate**.
6. In parallel: confirm Samvaad self-serve availability + price.
7. Stage-6 pilot the bot on grace-period follow-ups. Measure. Expand only on trust.

*No code is written until you say go, stage by stage. Manual workflow stays as fallback throughout.*
