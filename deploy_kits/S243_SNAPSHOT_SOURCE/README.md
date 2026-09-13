# S243_SNAPSHOT_SOURCE — the computed feed stops overwriting Marg's closing stock

**stock_app.py** `0b965da40816079a60c49a20946832b3` → `aa6d9cd9afbe5c7a2e44315678f58de3` · one new table `stock_expected` · no other file, no URL change.

## The defect (found at S243 by code reading — confirmed in the walk, not described)

`POST /finance/stock/api/snapshot` (stock_app.py L945) is one door used by two senders:

| sender | `source` it sends | `as_on` it sends |
|---|---|---|
| `push_snapshot.py` L287 | `push_snapshot` | Marg's closing-stock export date |
| `push_expected.py` L1277–1280 | `push_expected base=<dd-mm-yyyy> pur_to=<dd-mm-yyyy\|none>` | the **last sale date** (L951–952) |

Both upserted `stock_snapshot`, primary key `(as_on, item)` (stock_schema.sql L82–91), with no source in the key (L968–974). `reconcile()` (L799–828) reads `stock_snapshot` by `(as_on, item)` at L818 without looking at `source`. So when both landed for one day the later push silently became "Marg's figure" — for the count page (`_newest_snapshot` L832), for `reconcile()` (a difference could close because OUR arithmetic agreed with the count), and for every pad reader keyed on the count's `as_on`. And because the computed feed's `as_on` is the last sale date, it was usually the NEWEST day in `stock_snapshot` — the count page's item universe. `stock_feed` (append-only, `_feed_kind` L446) already told the two apart; S228's provenance line and S240's gate R3 both had to work around this.

## The fix (the smallest safe shape)

1. **`stock_expected`** — a new table, same columns as `stock_snapshot`, created idempotently from inside stock_app (`EXPECTED_SCHEMA`, `_expected_ensure`) and by `stock_expected_schema.sql`.
2. **`/api/snapshot` routes by sender** using the same rule stock_feed has used since S221 (`_feed_kind`): `expected` → `stock_expected`; `marg` and any unrecognised sender → `stock_snapshot`, exactly as before. **`stock_feed` still receives every push, unchanged.** `stock_rate` is written by both, unchanged.
3. **`reconcile()` is not run for the computed feed** (returns `reconciled=0`). The function itself is untouched. A difference closes only when MARG's export agrees with the count.
4. The reply keeps `ok / as_on / items / reconciled / revalued` (both push scripts read `items` and `reconciled`) and adds `stored_in`.

Every reader of the computed figure goes through `stock_feed`, not `stock_snapshot` — checked line by line (EVIDENCE_S243.txt §2). Nothing needs pointing at `stock_expected`.

## Install (three lines, the third only after reading the dry run)

```
bash /root/deploy/repo/deploy_kits/S243_SNAPSHOT_SOURCE/install_S243_SNAPSHOT_SOURCE.sh
```

The installer: refuses unless live `stock_app.py` is `0b965da4…` · walks on the box (base = the live file) · applies the table (idempotent) · `.new` → md5 → `.bak_S243_0b965da4` → `mv` · `py_compile` + `import stock_app` from `/root/finance` · restarts `clinic-finance.service` only if both pass · polls `http://127.0.0.1:8106/finance/healthz` up to 20 s · **auto-rollback** (old file back + restart) on any failure after the copy · prints the migration **dry run** · prints predicted and actual md5.

**Migration — separate, explicit, NOT run by the installer.** It moves the computed rows already in `stock_snapshot` to `stock_expected` and puts Marg's own figure back where `stock_feed` still has it. Backs the db up first to `finance.db.bak_S243_SNAPSHOT_<stamp>`. Rows it KEEPS (a computed-only day a count was measured against) are named for the owner's decision.

```
/usr/bin/python3 /root/deploy/repo/deploy_kits/S243_SNAPSHOT_SOURCE/migrate_stock_expected_s243.py --db /root/finance/finance.db --dry-run
```
```
/usr/bin/python3 /root/deploy/repo/deploy_kits/S243_SNAPSHOT_SOURCE/migrate_stock_expected_s243.py --db /root/finance/finance.db --apply
```

**Rollback (code):**
```
\cp -f /root/finance/stock_app.py.bak_S243_0b965da4 /root/finance/stock_app.py && systemctl restart clinic-finance.service
```
`stock_expected` may stay: the old code never reads it. **Rollback (data, only if `--apply` was run):** copy `finance.db.bak_S243_SNAPSHOT_<stamp>` back over `finance.db` with the service stopped.

## What changes on the screens

- The count page counts against **Marg's newest export** — no longer against the computed feed's newer day. Gate R3 ("no Marg STOCK CLOSING for this day") stops firing for that reason.
- `/page/now`, `/page/drift`, the readiness header and the three-way block: **same figures** (they read `stock_feed`) — proven by JSON diff before/after in the walk.
- The S228 provenance line reads "Marg's own closing-stock export" for every day from now on.

## Files

`KIT_ID.txt` · `README.md` · `SUMS.md5` (every file but itself and EVIDENCE) · `EVIDENCE_S243.txt` · `patch_stock_snapshot_source_s243.py` (base → patched, four `count(old)==1` anchors) · `stock_app.py` · `stock_expected_schema.sql` · `migrate_stock_expected_s243.py` · `walk_snapshot_source_s243.py` · `install_S243_SNAPSHOT_SOURCE.sh`.

The walk needs the sibling kits `S240_STOCK_GATE_R2` (base), `S208_STOCK_LEDGER` (stock_schema.sql), `S224_MARG_PURCHASES`, `S204_VPS_LIVE` — all in the deploy clone — or `--base` / `--schema-dir`.
