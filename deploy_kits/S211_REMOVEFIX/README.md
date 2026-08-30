# S211_REMOVEFIX — Remove could never have worked

## The fault, measured

`S210_MARGTIDY` shipped `POST /finance/api/marg-push/dismiss`, and it does:

    UPDATE marg_push_staging SET status='dismissed' ...

The table forbids that value. From `_marg_staging()`, the authoritative DDL:

    status TEXT NOT NULL DEFAULT 'pending'
      CHECK (status IN ('pending','applied','rejected','superseded'))

So every Remove raised `sqlite3.IntegrityError` and Flask answered a 500 HTML
page. **The button was broken from the hour it was written.** The owner pressed
it four times over two days.

Two things hid it:

1. the page turned every 500 into the word **"network"** — fixed by
   `S211_HONESTERRORS`, and the honest popup is what exposed this;
2. `MARGTIDY`'s selftest checked the **patch** — that it applied, compiled, was
   idempotent, and left its filter present — and **never called the route
   against a database**. Five green checks over a route that could not run.
   This is the S208 lesson again: a gate that measures the wrong thing.

Note also that `_marg_staging` is `CREATE TABLE IF NOT EXISTS`. The live table
carries the constraint it was born with, so editing the DDL would have changed
nothing whatsoever.

## The fix — no migration of a live money database

`rejected` is already this schema's word for a push ruled out, and
`_marg_push_reject()` already uses it for exactly that meaning. A removed report
becomes `rejected`: the row is kept, the audit entry is kept, the replay payload
is still cleared, and the page renders a red badge with **no Apply button**, so
it can never be loaded into the books.

**It stays visible rather than vanishing, and that is deliberate.** MARGTIDY's
hide-filter tested for `'dismissed'` — a value the schema forbids — so it never
hid anything; the list has always shown every row. This patch makes that honest
rather than quietly changing what the owner sees. **Hiding removed reports is a
separate decision and is left to him.**

## Proof — 14/14, and the first check reproduces the owner's own failure

    python3 -B patch_finance_app_removefix.py --selftest <a post-MARGTIDY finance_app.py>

- the real DDL is built in memory, a pending row inserted, and the OLD
  `status='dismissed'` UPDATE **refused by the table** — `CHECK constraint
  failed` — with the row left untouched, exactly as the owner found it;
- the NEW `status='rejected'` UPDATE accepted, payload cleared, row kept;
- the patch applied to a real post-MARGTIDY `finance_app.py`, compiled,
  idempotent, no `dismissed` value surviving anywhere.

The post-MARGTIDY target was built by applying MARGTIDY's own patch to the
captured live copy `deploy_kits/S204_VPS_LIVE/root__finance__finance_app.py`.

## Install — after the publish, ONE line on the VPS

    cd /root/deploy/repo && git pull && /root/wa/venv/bin/python3 -c "import sqlite3;print(sqlite3.connect('/root/finance/finance.db').execute(\"SELECT sql FROM sqlite_master WHERE name='marg_push_staging'\").fetchone()[0])" && /root/wa/venv/bin/python3 deploy_kits/S211_REMOVEFIX/patch_finance_app_removefix.py /root/finance/finance_app.py && systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service

The first thing it prints is the LIVE table's own constraint, so the diagnosis
above is confirmed on the box and not merely inferred from a capture.

## Rollback

    \cp /root/finance/finance_app.py.bak_S211_removefix_* /root/finance/finance_app.py && systemctl restart clinic-finance.service
