# S204_C1 — capture the live VPS bytes into the repo

**D350 §4. Built offline at S204. Nothing live is changed by this kit.**

## The finding it answers

At the S204 open all 67 rows of `live_pins_S203close.txt` were checked against all 1,952
files in the repo, by hash. **61 are recoverable. Four exist in one place only:**

| live file | nearest copy in the repo |
|---|---|
| `/root/finance/finance_app.py` | `deploy_kits/S202_B2C/finance_app.py`, 26-Aug 01:36 — before the S203 gate fix |
| `/root/finance/finance_ui/finance_entry.html` | `finance/finance_ui/finance_entry.html`, 15-Aug |
| `/root/deploy/email_agent.py` | `deploy_kits/S195_EMAIL/email_agent.py`, 21-Aug |
| `/root/wa/recordings-archive/make_force_keys.py` | none, ever |

`verify_live_pins.py` is GREEN on all four — correctly, because they match the record.
**The record is a hash, not the bytes.** A pin proves identity; it cannot restore a file.

## What it does

For every VPS row in the pin list: hashes the live file, compares it with the pin, and

- **MATCH** → eligible for capture
- **DRIFT** → reported loudly and **never captured** (capturing an unrecorded file would put
  bytes nobody has ruled on into a public repo, and would hide the drift by making it look
  ordinary)
- **MISSING** → reported

Before copying anything it applies the **F-185 publish gate** — the same three patterns
`tools/phi_scan.py` uses. A file with a hit is held back unless it carries an ALLOWLIST entry
**with a stated reason**. Counts are printed; **values never are**.

Then it copies the eligible files under flattened names, writes `SUMS.md5` and `MANIFEST.md`,
**re-hashes everything it wrote**, and refuses to say GREEN unless every byte matches.

It writes only inside its destination folder. It never touches a live file, never commits and
never pushes.

## Run it (VPS)

```
cd /root/deploy/repo && git pull --ff-only
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S204_C1/capture_live_to_repo.py
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S204_C1/capture_live_to_repo.py --write
```

The first run is a **dry run** — it prints exactly what it would do and writes nothing.

## Red-proof (done offline before delivery, F-195's lesson)

Projection written first, then measured. Against a five-row fixture — one clean file, one
drifted, one missing, one carrying a mobile-shaped number, one clean HTML:

- projected 5 VPS rows / 2 eligible / 1 drift / 1 missing / 1 gated → **all five landed**
- with faults present: **exit 1**; clean set: **exit 0** and `md5sum -c` exit 0
- **every check was seen RED before it was trusted GREEN.**

## What it deliberately does not do

Commit, push, or decide anything about repository visibility. **F-185 is the owner's ruling.**
The captured files sit in the repo clone on the VPS; they reach GitHub only when the repo is
committed and pushed.
