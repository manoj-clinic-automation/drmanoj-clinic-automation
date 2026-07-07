# Clinic_Master_KB_SystemsRegister — v1.41 DELTA (Session 94)

**Base:** v1.38 consolidated + v1.39 delta (S75) + v1.40 delta (S93). This delta folds in
Session 94 — a **live-systems incident-and-repair session on Track 2** (call-webhook 403
outage fixed; doctor-console `isGenericAgent_` bug fixed). **KB still WINS on any conflict.**

---

## §94 — Track 2: call-webhook outage + doctor-console fix (LIVE CODE CHANGED)

Session 94 was **not** a planned build session. It opened on a manual follow-up push and
turned into two live-fault repairs, then a project examination and a six-item forward agenda.

### §94.1 Incident 1 — call-webhook 403 outage (FIXED, verified end-to-end)

**Symptom:** staff dashboard follow-up tiles stuck on "⌛ Checking the call… the outcome
unlocks once it connects" even after a genuine >15-second connected call. The outcome
dropdown never unlocked. Started ~Jul 6, all tiles at once. WhatsApp feed unaffected.

**Diagnosis chain (all read-only until the fix):**
1. `call-hook.service` (:8098) was **up and healthy** — ruled out dead service.
2. Raw-log folder `/root/wa/call-hook/call_hook_logs` had **no `2026-07-07.jsonl`** — no
   call webhook had been received all day; last body landed Jul 6 ~13:41.
3. MyOperator panel → Webhooks v2: the **Call** webhook showed **status Failed**; the
   WhatsApp webhook showed **Active** (hence WhatsApp still worked).
4. Panel Failure Logs: **every** Call Ended / Call Summary delivery returned **HTTP 403**,
   consistently, on both Jul 6 and Jul 7.
5. A local `curl` to the receiver with the correct key **also returned 403** — proving the
   rejection was the receiver's own secret-gate, not an OLS/IP/WAF block.

**Root cause:** the VPS `.env` had **two secrets mashed onto one physical line** — a lost
newline had merged `CALLHOOK_SECRET` with a trailing `FU_UPLOAD_SECRET=…` fragment, so the
receiver read `CALLHOOK_SECRET` as a long run-on string that could never match the panel's
key → every incoming call webhook 403'd → nothing written to `Call_Durations` → the duration
gate could never unlock. (A **second, clean** `FU_UPLOAD_SECRET` on the next line was the one
actually in force — last-definition-wins — so the follow-up upload catcher kept working,
which is why only calls broke.)

**Fix (owner ran, one step at a time):**
- Timestamped backup of `.env` first.
- `sed -i '17s|.*|CALLHOOK_SECRET=<new clean key>|'` — rewrote **only** line 17 to a fresh
  **plain-alphanumeric** call key (Option B, chosen to remove the `@` special-char that
  complicates URL transport). The run-on `FU_UPLOAD_SECRET=…` junk on line 17 was thereby
  deleted; the real `FU_UPLOAD_SECRET` on line 18 was untouched.
- `systemctl restart call-hook.service` → verified `active`, `secret gate: ON`, `connected
  to 'Call_Durations' — 98 rows known`.
- MyOperator panel → Webhooks v2 → **Call** webhook → Edit → updated `?key=` to the new
  clean key; Call Ended + Call Summary still ticked; Authentication None; Save.

**Verified end-to-end:** Shavez placed a real follow-up call; the tile's "Checking…"
resolved; the outcome unlocked and saved. Outage closed.

**New fault code:** `CALLHOOK_SECRET_MISMATCH_403` — **ASSISTED**. Detection idea (not yet
built): if the panel's Call webhook shows Failed OR no `YYYY-MM-DD.jsonl` raw-log file has
appeared by mid-morning on a clinic day, alert. Procedure = compare `grep CALLHOOK_SECRET
/root/wa/.env` against the panel URL's `?key=`; re-sync + restart if they differ.

### §94.2 Incident 2 — doctor console "Could not load: isGenericAgent_ is not defined" (FIXED)

**Symptom:** the doctor dashboard's **Outcome Review → Today** view showed "Could not load:
isGenericAgent_ is not defined" and a count of 0. **Yesterday** view worked (13 outcomes
listed). So saved outcomes were fine; only the Today *display* was broken.

**Diagnosis (static scan of the live Apps Script JSON export, all 14 files):**
- `OutcomeLog.gs` line ~333 calls `isGenericAgent_(by)` — a helper **defined nowhere** in
  the project. When the Today build loop reaches it, JS throws → the whole Today view dies.
- The scan flagged 5 "called-but-undefined" names; 4 (`escPick_`, `fmtLV_`, `fmtWhen_`,
  `sbPick_`) are false positives — defined as `var x = function`. **Only `isGenericAgent_`
  is genuinely undefined.** It is the sole such fault in the project.
- Today vs Yesterday difference: line 333 only bites when a live matched call with an agent
  name is present, which the Today enrichment path produces and the archive-based Yesterday
  path does not — explaining why only Today failed.

**Fix (D143):** added the one missing helper to `OutcomeLog.gs`, placed among the small
helpers after `OL_col_`. It answers the question the call site needs — *is this "Handled By"
value a generic placeholder (staff / doctor / unknown / agent / system / blank) rather than
a real name?* — so line 333 can borrow the real caller's name from the call log when the
outcome was filed under a generic label.

```
function isGenericAgent_(name) {
  var n = String(name || '').trim().toLowerCase();
  if (!n) return true;
  return (n === 'staff' || n === 'doctor' || n === 'unknown' || n === 'agent' || n === 'system');
}
```

**Delivered as a full-file replacement** (per protocol), built from the live JSON export
(21,076 → 21,690 chars; only the one function + comment added). Verified: `node --check`
PASS; exactly one definition, one call site. Owner deployed via **edit existing deployment →
New version** (URL stable). Owner confirmed: Today view loads, "all good now."

### §94.3 Project examination (no code beyond the two fixes)

Full static analysis of the live project was run from the Apps Script JSON export. Findings:
- The dashboard **does not de-duplicate** the follow-up worklist — it reads `Followups_Today`
  exactly as the PC push writes it. So **duplicate patient rows originate PC-side** (the
  tracker's list generation), not in the dashboard.
- Today's real worklist was **238 rows** (20 Due Today, 34 Grace, 52 Actionable Missed,
  **124 Probable Dropout**, plus small buckets) — confirming the ">200, not humanly callable"
  problem is dominated by the Probable-Dropout bucket.
- `Call_Feed` remains the known-unreliable feed (D55); archive is authoritative.

### §94.4 Six-item forward agenda (owner-set; DESIGN captured, not built)

Logged for sequencing. My recommended order and current standing:

1. **Duplicate patient entries in a day** — real; fix is **PC-side** (de-dupe before/inside
   `push_followups_today.py`, or in the tracker's list builder). SAFE, ready to build once
   we see why a patient doubles (same section twice vs two sections). *Next execution item.*
2. **Reconcile "didn't pick up but visited"** — auto-settle a follow-up when the patient
   actually visits (proof = new Docterz visit). HIGH VALUE. Overlaps **Track-1 Step 7**
   (new-patient reconciliation) — same match machinery (Clinic ID + mobile). Needs a design
   step (which visits qualify, what outcome to write, where it runs).
3. **Trim the staff calling list (>200)** — needs an OWNER POLICY decision (what caps the
   daily list, where the 124 dropouts go — separate low-priority queue / weekly batch).
   Partly pre-designed as **D66 "Living Staff List"** (snooze, 3-tries-escalate,
   outcome-vanishes) — designed, not fully built.
4. **Live staff-activity summary on the doctor dashboard** — today live + yesterday
   cross-verified/audited against archive + transcripts. Buildable; the "audited" half
   depends on item 5.
5. **Migrate to AI audit layer** — this is **Stage 3 (D62)**: overnight Haiku-tier batch,
   ~₹200–350/month, transcript-vs-claimed-outcome, doctor-only flags. Designed, not built.
   Doctor-only "Call Audit" sheet already exists.
6. **Historical follow-up insights across taxonomy** — analysis only, no code. **Blocked on
   a de-identified data export** (patient data is deliberately not in this project). Claude
   can deliver the analysis plan now; real numbers need the export.

**Owner stance at close:** open to doing more together when it fits limited time; delegated
sequencing to Claude ("your call"). Claude's call: do the safe/ready items (Item 0 done +
Item 1 next), design-sheet the rest — do NOT bundle policy/AI-cost decisions into a rushed
build.

### §94.5 Decisions
- **D143** — `isGenericAgent_` helper added to `OutcomeLog.gs`: generic = staff / doctor /
  unknown / agent / system / blank. Purpose: let the Today outcome view borrow the real
  caller name from the matched call when the outcome was filed under a generic label.
  Full-file replacement; node-check verified; deployed as New version (URL stable).
- **D144** — Call-hook secret standard: the `?key=` gate for `/mo-callhook` (and by
  extension similar self-chosen VPS webhook gates) shall be **plain alphanumeric, no special
  characters** (no `@ # / ? & =`), because special characters corrupt under URL transport and
  caused the S94 403 outage. Applies to future key rotations of these gates.
- **D145** (hygiene note, not yet acted) — during S94 the plain-text values of
  `CALLHOOK_SECRET` (new), `FU_UPLOAD_SECRET` (line 18), and the old junk fragment were
  visible in terminal paste. These are self-chosen VPS gate keys (NOT WABA/MyOperator
  tokens), so exposure is low-risk, but a courtesy rotation of `CALLHOOK_SECRET` +
  `FU_UPLOAD_SECRET` is advisable at a convenient time (no Lokesh coordination needed).

### §94.6 State changes to §12
- **Duration gate is LIVE and healthy again.** `call-hook.service` (:8098) up; `Call_Durations`
  filling; outcome unlock working. The S94 403 outage is CLOSED.
- **Dashboard Apps Script:** `OutcomeLog.gs` updated (D143), redeployed as a New version of
  the existing deployment; dashboard URL unchanged.
- Everything else in §12 (KB v1.40) stands verbatim: WABA sends still BLOCKED vendor-side
  (D120); `wa_approve` still nohup (not systemd); key rotations still overdue; watchman /
  health report / attendance / follow-up push all live; Track 1 Step 5 COMPLETE, Step 7 not
  started.

---

**Decisions index now runs to D145. Next free: D146.** D83–D92 still reserved (P1–P10).
**Canonical after S94:** KB v1.38 base + v1.39 + v1.40 + **v1.41** delta · Umbrella v1.28 +
v1.29 + **v1.30** delta (Umbrella UNCHANGED this session) · **Runbook v52**.

## Changelog
- **v1.41 — 07 Jul 2026 (Session 94):** Added §94. Two live fixes: call-webhook 403 outage
  (`.env` run-on-line corruption → clean key rotation + panel re-sync, D144) and doctor
  console `isGenericAgent_` undefined-function bug (D143). New fault code
  `CALLHOOK_SECRET_MISMATCH_403`. Six-item forward agenda captured (design only). Hygiene
  note D145. Decisions index → D145.
