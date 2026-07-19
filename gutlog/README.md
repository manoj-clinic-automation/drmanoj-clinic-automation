# GutLog v3

A single-file Flask + SQLite personal health diary for **Dr. Manoj Agarwal**,
built to track IBS-mixed symptoms, meals (FODMAP + protein), as-needed
medicines, and clinic follow-up - as one timestamped, analytics-grade ledger.

Live at **https://health.dr-manoj.in** (private, password-gated).

```
gutlog/
|- app.py                     # the entire application (~1710 lines)
|- requirements.txt           # flask, gunicorn, werkzeug
|- README.md                  # you are here
|- CHANGELOG.md               # version history & decisions
|- docs/
|  |- DOSSIER.md              # <-- THE comprehensive reference (start here)
|  \- DEPLOYMENT.md           # step-by-step deploy/runbook
\- deploy/
   |- gutlog.service.example  # systemd unit
   |- backup_gutlog.sh        # daily backup script
   \- watchdog_entry.md       # how GutLog is wired into clinic-watchdog
```

## Quick start (local)
```bash
python3 -m venv venv && venv/bin/pip install -r requirements.txt
GUTLOG_INSECURE=1 venv/bin/python app.py     # http://127.0.0.1:8020
```
`GUTLOG_INSECURE=1` turns off the secure-cookie flag for plain-HTTP local use.
In production it runs under gunicorn behind HTTPS - see docs/DEPLOYMENT.md.

## The one document to keep
**docs/DOSSIER.md** is the sole reference for this tool: purpose, architecture,
every screen, the full data model, all 87 seeded foods and their FODMAP/status
flags, the complete API, the design system, deployment, the watchdog hook,
backup/recovery, security, and the decision log. If you read one file, read
that one.
