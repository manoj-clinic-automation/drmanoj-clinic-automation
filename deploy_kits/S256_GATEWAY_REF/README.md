# S256_GATEWAY_REF

**What:** two full-file replacements in `/root/finance` so the Razorpay reference Docterz already
sends is **kept** instead of thrown away.

| file | from | to |
|---|---|---|
| `/root/finance/docterz_day.py` | `e939235e…` | `75f89072…` |
| `/root/finance/docterz_ingest.py` | `80bf760d…` | `3809f046…` |

## Why

Docterz writes the gateway reference into the **Mode** cell of the Day Revenue sheet:

```
Online Payment pay_TVSzKeESCXc04L
```

`docterz_day.py` has always detected that, **stripped it**, and mentioned it only in a variance
note. So the single fact that tells a portal payment apart from counter UPI arrived every day and
was deleted every day.

**The premise was proven before a line was written** — the lesson of S255, where a kit was built on
an unverified sentence and rolled back within the hour. Two independent sources, one payment:

- the Docterz *payment completed* email (29-Aug-2026): **Payment ID `pay_TVSzKeESCXc04L`**
- the 29-Aug Day Revenue sheet on Drive: Bindu M., ID 7961 — consultation ₹600 **and** procedure
  ₹800, both with Mode `Online Payment pay_TVSzKeESCXc04L`

Same id, character for character.

## What changes

- `docterz_day.py` — each line gains `gateway_ref`, captured from the raw Mode cell. The mode is
  still normalised exactly as before.
- `docterz_ingest.py` — `clinic_day_line` gains `gateway_ref TEXT NOT NULL DEFAULT ''`, an
  idempotent `ALTER` migrates the existing database on first write, and the insert carries it.

**Nothing else moves.** Not a bucket, not a tender, not a total, not a screen. The selftest asserts
this on the rebuilt 29-Aug day: ₹1,200 consultations, ₹800 procedures, ₹1,400 online under the
plain name "Online Payment", ₹1,100 cash — all identical to before.

## What it makes possible (not in this kit)

A payment is portal because it **carries a Razorpay id**, not because someone typed "Wallet". Once
a few days of references have accumulated, the reconciler can be changed to read `gateway_ref` —
this time on evidence. That is the correct order, and the reverse of what D507 originally proposed:
**the record first, the reconciler second.**

## Install (one line, on the VPS)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S256_GATEWAY_REF/install_S256_GATEWAY_REF.sh
```

Refuses unless both live md5s match the from-pins; backs both up; `py_compile`; an in-memory smoke
that stores one reference and one blank; restarts `clinic-finance`; restores both byte-identically
on any failure. A second run prints `ALREADY INSTALLED`.

## Rollback (one line)

```
\cp -p /root/finance/docterz_day.py.bak_S256_e939235e /root/finance/docterz_day.py && \cp -p /root/finance/docterz_ingest.py.bak_S256_80bf760d /root/finance/docterz_ingest.py && systemctl restart clinic-finance
```

The column stays behind after a rollback; it is harmless — the old code simply never fills it.

## Proof
`selftest_gateway_s256.py` — **19 checks, all pass** offline on a rebuilt 29-Aug sheet, including
the old-database migration and a re-run leaving no duplicate. Installer mock-tested four ways
(clean, rerun, wrong base refused, forced failure → both files restored). See `EVIDENCE_S256.txt`.
