# S255_PORTAL_CHANNEL

**What:** full-file replacement of two files in `/root/finance` so that **portal money stops being
expected in the ICICI bank file**.

| file | from | to |
|---|---|---|
| `/root/finance/finance_clinic_day.py` | `b2b7ff7d…` | `992865c0…` |
| `/root/finance/clinic_money.py` | `d5c3a845…` | `97368596…` |

**Why (D510).** Docterz records four online modes. One of them — *Online Payment* — is the
counter's own ICICI UPI and does appear in the ICICI MPR. The other three — **Wallet, Patient APP,
Net Banking** — are Razorpay: the receipt goes to the owner's personal Gmail and the money settles
to the **Yes Bank** current account. All four were one bucket, so every portal rupee was expected in
the ICICI file, held for two banking days as "not in the bank yet", and then flagged to the owner as
*"never reached the ICICI account"*. The reconciler was right about the arithmetic and wrong about
the channel.

**What changes**

- `_our_online_entries` (the F-459 single source) tags every entry `icici` or `portal`.
- Two derived figures come off that one list: `our_icici_online_p` (what the MPR can show) and
  `our_portal_p`. `our_online_p` keeps its meaning — the day's whole online revenue.
- The MPR card compares the ICICI figure, not the total.
- The reconciler subtracts portal money from `expected_bank`, keeps portal entries out of the
  pairing, and gives each one an explained line: *"₹600 (B · ID C2, Wallet) is a portal payment —
  Razorpay settles it to the Yes Bank account, so it is never in the ICICI file. Awaiting the
  Razorpay record."*
- The month card gains a **Portal (Razorpay → Yes Bank)** row — and shows nothing when there is no
  portal money.

**What does NOT change:** the day's total, the counter-vs-Docterz comparison, every tender figure,
and the `never reached the ICICI account` flag for money that really is missing from ICICI.

## Install (one line, on the VPS)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S255_PORTAL_CHANNEL/install_S255_PORTAL_CHANNEL.sh
```

Refuses unless both live md5s equal the from-pins; backs both up; `py_compile`; an in-memory smoke
that asserts 500 / 600 / 1,100 split correctly; **restarts `clinic-finance`** (both files are
mounted into `finance_app`); restores both byte-identically on any failure. A second run prints
`ALREADY INSTALLED`. The watchdog has guarded `clinic-finance` since S243.

## Rollback (one line)

```
\cp -p /root/finance/finance_clinic_day.py.bak_S255_b2b7ff7d /root/finance/finance_clinic_day.py && \cp -p /root/finance/clinic_money.py.bak_S255_d5c3a845 /root/finance/clinic_money.py && systemctl restart clinic-finance
```

## Proof
`selftest_portal_s255.py` — 16 checks, all pass offline on a real sqlite day: the two channels add
back to the whole, revenue is untouched, portal entries leave the pairing exactly once, the month
row appears only when there is portal money. Installer mock-tested four ways (clean, rerun, wrong
base refused, forced failure → both files restored). See `EVIDENCE_S255.txt`.

## Where this sits
Step **1 of 3** in D507. Step 2 is the payment record itself — and the evidence for it arrived this
session: the receipt is a **Docterz** mail (`support@docterz.in`, subject *"… payment completed."*)
carrying Order Id, Payment ID (`pay_…`), amount and the patient's mobile, landing in the owner's
personal Gmail, where a relay of exactly this shape already runs (`S195_STMT/Bank_Statement_Relay.gs`).
Step 3 is Yes Bank settlement recognition.
