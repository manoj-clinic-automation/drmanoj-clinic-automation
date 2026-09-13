# S257_PORTAL_EVIDENCE

**What:** the portal channel done on evidence. Two full-file replacements in `/root/finance`, then a
re-read of every Docterz export on Drive so past days get their Razorpay ids.

| file | from | to |
|---|---|---|
| `/root/finance/finance_clinic_day.py` | `b2b7ff7d…` | `15818d91…` |
| `/root/finance/clinic_money.py` | `d5c3a845…` | `14e96b76…` |

**Requires `S256_GATEWAY_REF` installed** — the installer checks `docterz_ingest.py`'s md5 and refuses otherwise.

## The rule (D510)

An online payment is **portal** because the line **carries a Razorpay id** (`gateway_ref`, kept
since S256) — never because Docterz's mode says "Wallet", "Patient APP" or "Net Banking". The two
cases that refuted S255 are the selftest's first two checks:

- Bindu, 29-Aug — mode `Online Payment`, id `pay_TVSz…` → **portal**
- Alka, 12-Sep — mode `Wallet`, no id → **ICICI** (and indeed her ₹600 was in the ICICI file)

No mode-label list exists in either file; the selftest asserts that too.

## What changes

- `_our_online_entries` (the one F-459 source) tags each entry `portal` or `icici` by its id.
- `our_icici_online_p` / `our_portal_p` come off that one list; `our_online_p` is unchanged (all online revenue).
- The day card's bank line and **the MPR page's pairing list** both use the ICICI-only entries —
  the S255 contradiction (F-468) cannot recur: one list, two readers. The MPR page says what it kept out.
- The reconciler subtracts portal from `expected_bank`, keeps it out of pairing, and explains each
  one: *"₹600 (Bindu · ID 7961) is a portal payment — Razorpay id …04L — settled to the Yes Bank
  account, so it is never in the ICICI file."*
- The month card gains **Portal (Razorpay → Yes Bank)** — only when a line with an id exists.
- A database never written since S256 (no column) reads as all-ICICI, exactly as today. No crash.

**Volume, by the owner's account: two or three a month.** The channel is built for that — a line
each when it happens, nothing when it doesn't.

## Install (one line, on the VPS)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S257_PORTAL_EVIDENCE/install_S257_PORTAL_EVIDENCE.sh
```

Refuses unless S256 is in and both live md5s match; backs up; `py_compile`; a smoke that asserts
Wallet-without-id → ICICI and Online-with-id → portal; restarts `clinic-finance`; restores both on any
failure. **Then the backfill**: `docterz_ingest.py --all` re-reads every export on Drive (a minute or
two) and prints how many lines now carry an id, by date. If the backfill fails, the code stays
installed and correct; the line to re-run is printed.

## Rollback (one line)

```
\cp -p /root/finance/finance_clinic_day.py.bak_S257_b2b7ff7d /root/finance/finance_clinic_day.py && \cp -p /root/finance/clinic_money.py.bak_S257_d5c3a845 /root/finance/clinic_money.py && systemctl restart clinic-finance
```

## Proof
`selftest_portal_s257.py` — 18 checks, all pass, on the two real cases plus an unmigrated database.
Installer mock-tested four ways (clean · rerun · S256 missing refused · forced failure restored).
See `EVIDENCE_S257.txt`.
