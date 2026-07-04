# Dr. Manoj Clinic — Umbrella Architecture · v1.22 Delta

**Session 60 · 04 Jul 2026.** Carries forward v1.21 (attendance session) unchanged; adds the Gap A follow-up-push migration. **KB v1.28 wins on any conflict.**

> Numbering: attendance HTTPS/cookie work = Session 59 (D99–D100, Umbrella v1.21). This follow-up-push migration = **Session 60** (D101–D105, Umbrella v1.22).

---

## What changed strategically this session

**A new architectural boundary is now enforced and proven: "PC computes, VPS delivers."**

Before this session the follow-up list's delivery depended on a Windows Task Scheduler watcher on the always-on clinic PC — an inherently fragile point that silently failed on "At log on." This session that dependency was removed by drawing a clean line:

- **The clinic PC remains the brain.** It holds all PHI, runs the interactive 2,137-line tracker back-office (Docterz/Marg/Labmate ingest, diagnosis refresh, lab/pharmacy revenue sorting with a manual-unclassified pile, vacation, lookups, Call_Feed pull), and reconciles patients — none of which can or should go headless.
- **The VPS becomes the delivery layer.** It receives only the *derived output* (the daily workbook) and pushes it to the Google Sheet on its own clock. No PHI store expands; the VPS gets the same names/mobiles/diagnoses that already flow to the sheet for the call list.

This mirrors the one-way patient-mirror pattern and the one-writer-per-table invariant: the PC is the single writer of the workbook; the VPS is the single writer of the sheet's follow-up tabs.

## The delivery layer (new)

```
PC tracker (app.py /run)
   │  run_daily() writes Staff_Action_Today_*.xlsx
   │  + NEW: push_to_vps.upload_workbook(staff_path)   [non-fatal]
   ▼
HTTPS POST /fu-upload  (X-FU-Secret)
   ▼
VPS catcher  followup_receiver.py  (:8100, systemd)
   │  atomic write → /root/wa/followup-inbox/
   ▼
VPS pusher  push_followups_vps.py  (--push)
   │  fired by clinic-followup-push.timer (22:00/07:00/11:00 IST)
   │  replace-only → Followups_Today + Followups_Settled
   ▼
Google Sheet  →  Dashboard
```

Old path (`\Follow-up Auto-Push Watcher` on the PC) **disabled**. Manual `--push` (PC + VPS) remains the fallback on both ends.

## Decisions this session
- **D101** VPS catcher live (:8100). **D102** VPS pusher live (223+153 proven). **D103** push timer armed (22:00/07:00/11:00). **D104** PC auto-upload hook live. **D105** old watcher retired.

## Forward strategy (sequenced)
1. **Goal 2 — diagnostics/surveillance across all projects** (next). Now that delivery is VPS-native, one surveillance layer should watch every service + timer + token (attendance :8042, follow-up :8100, WA, call-hook, transcription, portal) and alert. The natural next architectural layer above "PC computes, VPS delivers."
2. **WABA trigger ("Gap C")** — the VPS is confirmed the **single WABA sender** (token lives there; the PC can't sensibly send). The PC tags who-gets-what (`message_category_for()` already stamps categories per row); the VPS reads the tags from the uploaded output and sends. Deferred until after diagnostics.
3. **Workflow redesign (morning-generate)** — shift generation to the morning using *yesterday's complete* consultation report as the anchor, calling patients the afternoon before. Fixes the two-CSV anchor friction (the reason the afternoon-shift stalled) and likely lifts return rates for travel-dependent patients. Touches `processor.py` day-math → its own tested session. Nothing installed this session blocks it.

## Guardrails reaffirmed
- Interactive apps stay on the PC; only unattended delivery moves to the VPS.
- Every VPS function = its own walled-off port + service + proxy (catcher is :8100, its own unit; new contexts above the catch-all).
- Secrets only in `.env`/gitignored files, masked in chat; restart the consuming service after any secret change and verify.
- Vhost edits: back up + rollback-in-hand + verify existing routes after reload.
