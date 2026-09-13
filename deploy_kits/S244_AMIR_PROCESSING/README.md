# S244_AMIR_PROCESSING — processing → processing done → what is still to be made

Built 13-Sep-2026 (S244) to the owner's ruling of the same morning:

> change the report acceptance flow — system shd tell amir — processing — processing done — then
> any report still to generate, meanwhile he shd be able to start whatever next tasks he has in
> his 7 steps flow, while the report is being processed

## Why

On 13-Sep Amir exported the same two reports three times. The screen told him *"aaj ki nahi
aayi"* while his file was still crossing from the medical PC to the server — so he exported it
again, and again. One message was being used for two different situations: **a file still in
transit** and **a file that was never made**. They are not the same thing and must not read
the same.

## What changes — one file, `/root/finance/amir_day.py`, replaced whole

| where | what |
|---|---|
| **step 4, while a file is on its way** | **"Report ban rahi hai…"** — *server file le raha hai, lagbhag N minute aur; aapko kuch nahi karna hai.* The screen re-checks itself every 20 s. It does **not** say *aaj ki nahi aayi* and does **not** ask for another export. |
| **step 4, once the wait is over** | **"Jaanch poori ho gayi ✓"** — then the pair: each report green with period, rows and time, or red **"Dobara banaiye: \<the report, by name\>"**, with the Excel warning and the two dates he has to type. |
| **he is not held up** | While anything is in transit, *"where did I leave off"* skips step 4, and step 4 itself carries **"Aage ka kaam shuru kijiye"** straight to step 5. The step-4 chip in the 1→7 banner turns **amber**, and steps 5 and 6 carry one amber line — *Report abhi ban rahi hai* / *Ek report dobara banani hai* — with a link back. It never blocks. |
| **the clock** | Starts when **he** says the export was taken (the step-3 tick), never when the page is opened. **"Dobara banai — phir se dekhiye"** rewrites that tick, so a fresh export gets a fresh window instead of inheriting the old one. Window: `EXPORT_GRACE_MIN`, **6 minutes**, env `AMIR_EXPORT_GRACE_MIN`. |
| **a wrong file that DID arrive** | Reported **at once**, not waited on: a file stamped *after* his tick with the wrong period is his own fresh attempt, so *"tareekh galat hai — 1 tareekh se aaj tak chahiye"* appears immediately. A *stale* wrong file (yesterday's, older than his tick) does not mask the fresh one still in transit. This is exactly the 13-Sep failure, walked both ways. |
| **step 3, before he goes to Marg** | The two dates printed large: `FROM 01-09-2026` · `TO 13-09-2026 (aaj)`, and *"TO ki tareekh aaj ki honi chahiye — kal ki nahi"*. The same block is repeated with the *dobara banaiye* ask. |
| **`/finance/amir/api/healthz`** | `kit: S244_AMIR_PROCESSING` |

## What deliberately does **not** change

- **The gate.** `GATE_STEPS = (2, 4, 5, 6)`. A day still does not close until both reports are
  verified. Processing is a message, never a pass.
- **He never certifies a report.** There is still no way for Amir to tick step 4. Neither button
  on that screen claims anything: *dobara banai* only restarts the clock, *aage ka kaam* only
  moves him on. `done[4]` is still the server reading `purchase_export`, and nothing else.
- **The owner's page stays English** — *"still arriving"* while in transit, *"not verified"* once
  it is genuinely late.
- No schema change, no new table, no new route, no cron, no service file, no second file.
  `finance_app.py` is untouched — `amir_day` has been mounted there since S241.

## Proof

`EVIDENCE_S244.txt`, verbatim: a **62-check live-shape walk** — a real Flask app, a real sqlite
database with the real column shapes of `purchase_export` / `purchase_bill` / `amir_step` /
`mi_file`, driven over WSGI the way his phone drives it. **62 ok, 0 failed.** It covers: nothing
exported yet · the transit window · one report in, one still coming · both in · the window
running out · *dobara banai* restarting the clock · the fresh wrong-period file · the stale
wrong-period file · the close still refused and **writing nothing** · the English on the owner's
page · a `<script>` supplier still escaped · **no ten-digit phone-shaped number on any screen
walked** (F-185) · the role refusal · idempotent schema (F-303) · a missing `purchase_export`
table not crashing the page.

And the **negative control**: the same walk run against the live S243 file, which fails at check
A2. A walk that passes on the unchanged file proves nothing (S208).

## Install — ONE line on the VPS, after the owner's publish

```
bash /root/deploy/repo/deploy_kits/S244_AMIR_PROCESSING/install_S244_AMIR_PROCESSING.sh
```

Refuses unless `/root/finance/amir_day.py` is **exactly** `bf7d9826119edab48652fd959e1e8da5`
(the S243_AMIR_VISIT pin, confirmed live at the 13-Sep install). Gates in order: `SUMS.md5` +
`KIT_ID` → the live pin → the patcher's selftest **on the live bytes** → the kit's own 62-check
walk **on the box** → `amir_day.py.bak_S244_bf7d9826` → place → `py_compile` → import smoke under
the unit's own environment (blueprint and all four routes must still be registered, `GATE_STEPS`
unmoved) → `systemctl restart clinic-finance` → healthz 200 within 20 s. Any red after placing:
the file is restored and the service restarted. Re-run → `ALREADY INSTALLED`.

**Predicted to-pin:** `amir_day.py` → `aad400fa9c4b7804229c9f175c86533b`.

Rollback by hand:

```
\cp -f /root/finance/amir_day.py.bak_S244_bf7d9826 /root/finance/amir_day.py && systemctl restart clinic-finance
```

## To tune the window later, without a kit

```
systemctl set-environment AMIR_EXPORT_GRACE_MIN=8 && systemctl restart clinic-finance
```

(Or the unit's `Environment=` line. 6 minutes is the built-in default: Marg writes, MargPull
picks up, the one door takes it in — about five minutes end to end on a normal day.)
