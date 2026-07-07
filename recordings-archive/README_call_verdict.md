# call_verdict.py — Stage 3 of the Staff Call Audit project (the AI judge)

Session 122 · Decision D149 (parent D62) · md5 `bb17720d4857e3c040e8c89e7cc2e095`

Reads `Call_Transcripts` (Clinic Callback Tracker), sends each transcript — and ONLY the
transcript + direction + duration, never the staff claim or any patient/agent identifier
(the blind-judge rule) — to Claude Haiku, which classifies the call into the clinic's LIVE
dashboard outcome vocabulary and sets six safety flags (postop/complaint/urgent/surgery/
clinical/conduct). Python then fuzzy-matches the staff's claim from `Followup_Outcomes` and
computes Match/Mismatch/Partial/Unclear/No-claim. One row per call → a `Call_Verdicts` tab
in the DOCTOR-ONLY Call Audit sheet (this script is that tab's only writer).

v1 is classify-and-flag ONLY: no auto-accept, no downstream actions, no timer yet.

## Run
    /root/wa/venv/bin/python3 call_verdict.py --selftest                 # offline, no key/net
    /root/wa/venv/bin/python3 call_verdict.py --date 2026-07-06 --dry-run --limit 3
    /root/wa/venv/bin/python3 call_verdict.py --date 2026-07-06 --limit 15   # writes rows

## Env (in /root/wa/.env)
    ANTHROPIC_API_KEY   (required)  console.anthropic.com key
    GOOGLE_SA_KEY       (required)  service-account JSON (Sheets); falls back to WA_SA_KEY
    DRIVE_TOKEN_FILE    (required)  /root/wa/recordings-archive/drive_token.json (owner-OAuth)
    TRACKER_SHEET_ID    (optional)  defaults to the Clinic Callback Tracker
    AUDIT_SHEET_ID      (optional)  defaults to the doctor-only Call Audit sheet
    AI_JUDGE_MODEL      (optional)  default claude-haiku-4-5

## Known next task
The ±45-min claim-match window is too weak for real staff batch-filing (§122.4). Redesign the
join (mobile + Agent Ext + same-day) before trusting Match/Mismatch. The AI-verdict half is sound.

## OAuth token note
Stages 1/2/3 share `drive_token.json`. The OAuth app MUST stay in "In production" publishing
status — "Testing" status expires tokens after 7 days (root cause of the S122 incident).
