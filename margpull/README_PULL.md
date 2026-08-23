# Auto-pull Marg reports from the medical PC to manojz  (S195)

## Why
On 21-08-2026 a report sat unsent on the medical PC and could not be seen or
diagnosed from anywhere else. With this running, **every Marg export exists on
manojz within minutes** — a second copy, on a machine that can actually be
inspected — and any report whose send FAILED is surfaced automatically.

## What it does
`PULL_FROM_MEDICAL.bat` (runs on **manojz**) reads three folders on the medical PC:
- `\\100.119.151.40\DDrive\MARGERP\users\*\report\` — every export Marg writes
- `...\SendToClinic\Sent\` — the sender's own archive
- `...\SendToClinic\NEEDS_UPLOAD\` — reports whose send to the clinic failed

and for each file: captures it (content-hashed, so nothing is ever copied twice),
identifies it **by content**, renames it by the business date inside it, and files
it under `D:\MargArchive\<TYPE>\<YYYY-MM>\`, appending to `index.csv`.

It is **read-only** on the medical PC and uses **UNC paths**, so it does not depend
on the `Z:` mapping (which exists only inside the interactive login session).

## Install (manojz)
1. Put this folder somewhere permanent, e.g. `D:\MargPull`.
2. Needs Python 3 (`xlrd` is vendored here — no pip).
3. Run `PULL_FROM_MEDICAL.bat` once by hand and confirm files appear in
   `D:\MargArchive`.
4. Task Scheduler → new task, every **10 minutes**, action:
   `D:\MargPull\PULL_FROM_MEDICAL.bat AUTO`
   "Run whether user is logged on or not" is fine (UNC needs no mapped drive),
   provided that account can reach the medical share.

## The failed-send path
If `GUARD_AND_SEND.bat` on the medical PC cannot get a report to the clinic server,
it parks a copy in `D:\SendToClinic\NEEDS_UPLOAD\` and appends the reason (and the
server's reply) to `NEEDS_UPLOAD.txt`. This puller then copies those onto manojz and
prints a loud ATTENTION block. From there, upload the report through the **Hub in
your browser** — that route needs no token and is unaffected by whatever broke the
sender.

## Files
`PULL_FROM_MEDICAL.bat` · `marg_watch.py` (capture) · `marg_router.py` (identify,
verify, rename, archive) · `signatures.json` (report registry — add new report types
here, no code change) · `marg_report.py` (the server's own parser) · `xlrd/`
