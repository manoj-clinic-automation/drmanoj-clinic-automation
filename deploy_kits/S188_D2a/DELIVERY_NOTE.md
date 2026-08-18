# S188_D2a — Daily Flow v2 · stage D2: Darpan's mirror (D326) + F-127

**Session 188 · 18 Aug 2026 · built on live bytes, rehearsed offline, not yet installed.**

Two files, **one install**. They must move together: the entry page's fetch of the
unit-position endpoint is removed in the same breath as that endpoint gains its
checker gate. Either half alone leaves the page broken or the data open.

---

## What it does

**1. Darpan now Saves, sees the check, then Files.**
A new maker-scoped endpoint `GET /finance/api/day/<date>/mirror` answers his own day and
nothing else: his declared figures, the bank's settled UPI with a match-or-gap verdict, the
Marg verdict, which scans are attached, his opening carry, and the days he still owes.

**Save-then-see is enforced on the server, not in the browser.** An unsaved day returns
`409 not_saved`. The sequencing is what keeps his declaration and the Marg export two
independent records; a promise the page makes to itself is not a property of the system.

**The Marg card has three states, not two,** because "no comparison" has two different causes
that need two different people to act:

| state | what he reads |
|---|---|
| `applied` | the comparison — Marg total, bill count, variance chip |
| `staged_not_applied` | *"it has arrived from the counter — the doctor has not applied it yet"* |
| `absent` | *"no report has been sent. Ask the counter to run SEND TO CLINIC."* |

Since he files the previous day after 10am, ICICI (pushed 09:30 daily since S179) fires every
morning; Marg fires as soon as the doctor's **Apply** is done.

**2. `edited_after_reveal` — the stamp, not the lock (D326).**
The reveal is recorded with a *fingerprint of the money he was shown*. A later save that
**moves the money** writes a `data_flag` and warns him it will be visible. A save that changes
**nothing** — which is exactly what tapping **Scan** does on the way to the scanner — is not an
edit, and is not stamped. Nothing is ever blocked: a lock forces a round trip for an honest
typo (F-105).

**The badge reaches the doctor with no checker-side code change at all**, because
`/finance/api/day/<date>/full` already renders `data_flag` rows. Proven in the suite.

**3. F-127 — the maker's page stops receiving the unit position.**
`/finance/api/tile` was ungated at the route level. `_gate` requires *a* medical role, so it was
never open to the world — but it did not distinguish maker from checker, and Darpan's page
fetched it on **every load** to render one deposit banner. What his browser actually received:
`cash_in_hand`, `cash_with` (the custodian's name), `month_to_date`, `last_revenue`,
`deposit_threshold`, `deposit_excess`, `last_bank_deposit`, `days_since_bank_deposit`,
`noncash_month_to_date`, `awaiting_approval`, `last_month_close`, and every shout count.

> **F-127: a role gate on the surface is not a role gate on the data.** `_gate` protects the
> **unit** boundary; nothing protected the **role** boundary inside a unit, so a route that needed
> `checker` and forgot to say so silently accepted the maker. The F-84 family, one layer in.

Fixed here:

| route | before | after |
|---|---|---|
| `/finance/api/tile` | no role check | `require("checker")` — payload otherwise untouched |
| `/finance/api/exceptions` | no role check, every open exception | maker+checker; a **maker receives only `missing_day`**, which is all his page ever used |
| `/finance/api/day/<date>` | no role check | maker+checker; **payload unchanged** — it was already correctly scoped |

Its docstring claimed it "feeds the portal tile". **It has not since S187** — the portal reads
`my-day-summary` and `tile-summary`. Checked against the live `portal.py`, not believed.
A stale claim about another component nearly argued this gate out of existence.

**4. The page is rebuilt under Clinic Design Language v1** — the doc names "Darpan's D2 mirror"
as *born in v1*. Warm surfaces, sticky branded header with your Canva logo (the same bytes as
the Hub), in-page tabs, tabular right-aligned numerals, `<details class="help">` folded help
(**which is where D6's contextual instructions will land, with no further page surgery**),
empty `.hindi` companion slots awaiting the label sign-off, 46px back-to-top.

**5. The File button is gated** on the three scans being attached **or** a stated reason.
Today `scanReason` is free text and enforces nothing. Blank is UNKNOWN, never zero.

---

## Evidence

**F-87 differential — `F87_DIFFERENTIAL.txt`, verdict CLEAN.** A page-only rebuild:

- element ids the script addresses: **23 of 24 kept**
- API paths called: **6 of 7 kept**
- querySelector targets **8/8** · scanner doc types **4/4** · repeater field classes **15/15**
- keys in the POSTed day payload: **11 of 11 kept**

The only two removals are the two declared in the contract: `depositMsg` and `/tile`.

**Smoke, offline, on a store seeded to the live schema:**

| | total | passed | failures |
|---|---|---|---|
| live bytes (`db4373a5…`) | 400 | 398 | 2 (seeded data, not code) |
| this kit | **453** | **451** | the same 2 |

**+53 checks, zero new failures.** The two are seeded-data artefacts — legacy carry-forward
breaks and a parked month the seed does not build. The real box was **400/400** at the S187
close, so the live projection is **453/453**.

**The rehearsal harness was itself wrong, and fixing it mattered.** `dev_seed_smoke_db.py`
seeded a `unit_role(medical, selftest, checker)` row. The live box has no such row, so eight
"a maker cannot X" assertions were passing **by accident** — the F-106 trap living inside the
harness. Corrected in `dev/`, and the baseline moved 375 → 398 the moment it was. The three new
role-refusal tests deliberately run as `smoke_no_seat`, with no checker rights riding along.

**Installer rehearsed against a throwaway target, all three paths:**

1. **Pre-existing red** → refused, nothing swapped.
2. **Green** → currency gate PASS · 398/400 → 451/453 · backup · swap · md5 verify · restart ·
   healthz · live re-smoke · GREEN.
3. **Red at the health check** → **restored byte-perfect** (`db4373a5…` / `8ec6ad49…`, identical
   to before the run).

`bash -n` on the **whole** installer (F-126). It also caught a real trap `bash -n` cannot see:
`$KIT_$STAMP` parses as a variable named `KIT_`, and under `set -u` would have killed the
install at the backup step. Fixed to `${KIT}_${STAMP}`.

---

## Install

```
cd /root/deploy/repo/deploy_kits/S188_D2a && bash install_d2a.sh
```

It refuses unless the box carries **exactly** `finance_app.py db4373a5…` and
`finance_entry.html 8ec6ad49…`. Publish with `PUBLISH_ALL.bat` (D328).

**After it goes green:** pin both md5s into the KB Register **from the box** (D321(d)) —

- `finance_app.py` → `5a7fea4fe50f67a687bf27eeec97f411`
- `finance_ui/finance_entry.html` → `a114ebc48565491cd2d145ed767bb923`

---

## The one human cost

**This changes Darpan's habit.** Save → the check → File, where there were two independent
buttons. Walk him through it **once**, in the morning before 10am, on the day it lands.

## Owed after this kit

- **F-127** to the Fault Register (next free was F-127; **F-128** is the stale-seed finding above
  if you want it recorded separately — I think it should be).
- Hindi labels still gate his wording; English until the sign-off.
- D3 remains blocked by the §4a ₹70,000 Staff Ledger check (D326(c)).
