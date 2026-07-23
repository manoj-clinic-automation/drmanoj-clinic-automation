# gmail-automation — Gmail/Drive Automation + Renewals Suite (v2.2, OPERATIONAL)

Personal-account automation: CC statement capture, inbox janitor (5 rules + sweeps),
Payment Register, complete renewals reminder system (26 dated + 6 annual series),
PC-side Tally extraction.

**Start here: `KB_MASTER.md`** (11-section canonical reference — architecture, IDs,
runbook, open items). `docs/EOS_23Jul2026_session3_handoff.md` is the session-level
handoff for AI-assisted continuation.

## Layout
```
gmail-automation/
├── KB_MASTER.md                  # canonical KB (11-section standard)
├── README.md                     # this file
├── CHANGELOG.md                  # suite changelog
├── gas/
│   ├── cc-statement-saver/save_cc_statements.gs      # GAS project 1 (deployed)
│   └── inbox-janitor/
│       ├── inbox_janitor_v2.2_FINAL.gs               # GAS project 2 (deployed, full file)
│       └── pending/03_pending_patch_friendly_narrations.gs  # NOT pasted; gated on Hemant
├── pc-scripts/process_statements.py                  # D:\Scripts copy (passwords stripped locally only)
└── docs/EOS_23Jul2026_session3_handoff.md            # cold-start session handoff
```

## Update workflow (GitHub Desktop)
1. Copy this `gmail-automation/` folder into the repo root of `drmanoj-clinic-automation`.
2. GitHub Desktop → review changes → commit: `gmail-automation suite v2.2 operational`.
3. Any future GAS edit: paste new full file over the repo copy, bump CHANGELOG, commit.
   GAS project is deployed by full-paste from the repo copy — repo is canonical.

⚠️ Never commit `CARD_PASSWORDS` values in process_statements.py — local PC copy only.
