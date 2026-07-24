# Asset Register

Equipment, contracts, renewals and staff documents for Dr Manoj Agarwal Clinic, NK Pathology and personal assets.

**Live:** https://assets.dr-manoj.in · **Version:** v1.1.0 · **Stack:** Flask + SQLite, single file, server-rendered.

| Document | Purpose |
|---|---|
| `DOSSIER.md` | What this system is, how it works, why it was built this way — read first |
| `DEPLOY.md` | Deployment and update runbook, restore procedure, troubleshooting |
| `CHANGELOG.md` | Version history |
| `app.py` | The entire application |
| `smoke_test.py` | 41 checks across 9 steps — run before every deploy |

**Deploy rule:** full-file replacement of `app.py` only. Never overwrite `assets.db` or `uploads/`.

**Quick local run:** `python3 app.py` → http://127.0.0.1:8030 (creates a fresh database beside the file).
