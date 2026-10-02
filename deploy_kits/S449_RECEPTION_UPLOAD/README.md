# S449_RECEPTION_UPLOAD — the reception PC reports straight to the server (session 290, 02-Oct-2026, D659)

**The owner, 02-Oct-2026:** "One is direct upload from the reception PC to server."

Until this kit, the reception PC's heartbeat and the two Docterz reports reached the server only through Google Drive
for desktop on that PC — and on 01-Oct that Drive stopped starting and nothing said so. This is the second road.

## What it places on the server
| file | what |
|---|---|
| `/root/finance/reception_door.py` (NEW) | `POST /finance/api/reception/heartbeat` and `POST /finance/api/reception/report`; every request signed (Ed25519) by a key made on the reception PC; a report is taken through `docterz_pickup.take()` (S443), the Drive pickup's own door, so two roads count a report once; one row for `/finance/health` |
| `/root/finance/reception_keys.txt` (NEW) | the reception PC's **public** key — the only key material on the server or in this kit |
| `/root/finance/finance_app.py` (four anchored edits, `ac24fc5e…` → `022a9b0e…`) | the two paths in `PUBLIC_PATHS` (the door authenticates itself, like the phone doors of S290 and S407) · the guarded mount · the health row "Reception PC" · the mounts row counts 26 |

It writes `/root/finance/reception_heartbeat.json` (counts and dates only — the agent's own rule) and, for a report,
the same `docterz_export` rows and `/root/finance/docterz_exports/` files the Drive pickup writes. No new table, no
setting, no cron, nothing sent anywhere.

## The reception PC's side
`reception/reception_agent.py` is agent **S449.1** — the file the PC runs (it went in through the agent's own update
path, a signed Drive job). It is here because the walk drives it against the door, and so the box holds the exact
client it was proven with. The living reinstall kit for that PC is `deploy_kits/S448_RECEPTION_AGENT/`.

## Rules the door enforces
- no key file → 503, nothing taken (fail closed) · unsigned, wrong key, changed body, or a signature made for the other
  path → 401 · more than 15 minutes from the server's clock → 401 `CLOCK`
- a file that is not one of the two Docterz reports **by its content** → 400, nothing kept
- the same bytes again → `ALREADY` · a newer export with fewer rows → quarantined, never replaces (S443's rule)
- the health row measures age on the server's clock from arrival: in the clinic day (10:00–20:00, Sunday closed)
  amber after 15 minutes, red after 45; outside it, a note. Settings, all optional: `reception.clinic_hour_from`,
  `reception.clinic_hour_to`, `reception.stale_warn_min`, `reception.stale_bad_min`.

## Install — one line, the owner's
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S449_RECEPTION_UPLOAD/install_S449_RECEPTION_UPLOAD.sh
```
Gates → pins → the walk on scratch copies (the real app over a copy of `finance.db`; the agent's own code over real
HTTP; the box as it is as the negative control) → backup → place → restart → the door's own refusal read back → it then
waits up to six minutes for the reception PC's next heartbeat and prints it. Anything red after placing restores every
file. `DRY=1` in front of `bash` runs the gates and the walk and places nothing.

## After a Windows reinstall of the reception PC
The PC makes a new upload key. Its public key appears in its heartbeat (`direct_upload.public_key`); it replaces the
line in `/root/finance/reception_keys.txt` by a small kit. Nothing secret moves.
