# gmail-automation — Gmail/Drive Automation + Renewals Suite

**v2.2.1 · OPERATIONAL · owner: drmanojkragarwal@gmail.com**

Personal-account automation: credit-card statement capture, inbox janitor
(5 rules + sweeps), Payment Register, complete renewals reminder system
(26 dated entries + 6 yearly series), and a PC-side Tally extraction pipeline
launched from the Clinic Hub dashboard.

## Start here
**`DOSSIER.md` — the sole reference document.** Architecture, canonical IDs,
schedules, configuration map, renewals register, runbook, troubleshooting,
security, open items, recovery, version history. It supersedes KB_MASTER.md
and every interim note.

`docs/EOS_24Jul2026_FINAL_handoff.md` is the session-level handoff used to
cold-start an AI-assisted working session.

## Layout
```
gmail-automation/
├── DOSSIER.md          # sole reference document — read this first
├── README.md           # this file
├── CHANGELOG.md        # version history
├── gas/
│   ├── cc-statement-saver/
│   │   └── save_cc_statements.gs              # GAS project 1 (deployed, daily 06-07)
│   └── inbox-janitor/
│       ├── inbox_janitor_v2.2_FINAL.gs        # GAS project 2 (deployed, daily 07-08)
│       └── pending/
│           └── 03_pending_patch_friendly_narrations.gs   # NOT deployed - gated on accountant
├── scripts/                    # ==> mirrors D:\Scripts on the clinic PC
│   ├── process_statements.py   # statement decrypt + transaction extraction
│   └── statements_app.py       # Flask runner, 127.0.0.1:5059
├── clinic-hub/                 # ==> hub folder on the clinic PC
│   ├── clinic_hub.html         # local dashboard (cards + status dots)
│   ├── open_clinic_hub.bat     # launcher, starts each service
│   └── GMB_Review_Assist_DrManojAgarwal.html
└── docs/
    └── EOS_24Jul2026_FINAL_handoff.md
```

## Deployment model
The repo is **canonical for all code**. Google Apps Script projects are deployed
by full-file paste from `gas/…`; PC files are copied to their live locations:

| Repo file | Live location |
|---|---|
| `gas/cc-statement-saver/save_cc_statements.gs` | GAS project "CC Statement Saver" |
| `gas/inbox-janitor/inbox_janitor_v2.2_FINAL.gs` | GAS project "Inbox Janitor" |
| `scripts/process_statements.py` | `D:\Scripts\process_statements.py` |
| `scripts/statements_app.py` | `D:\Scripts\statements_app.py` |
| `clinic-hub/clinic_hub.html`, `open_clinic_hub.bat` | clinic PC hub folder |

Sheet, Drive and Calendar state lives in Google — IDs are listed in DOSSIER §4.

## ⚠️ Security
`CARD_PASSWORDS` in `scripts/process_statements.py` must stay **empty in the
repo**. Live values exist only in the `D:\Scripts` copy. Check the diff before
every commit.
