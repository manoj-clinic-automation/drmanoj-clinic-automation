> ## ⚠ SUPERSEDED — DO NOT ACT ON THIS DOCUMENT
> **Superseded on 26-Aug-2026 by the `KB_Register` live-file table** —
> `KB_Register_v5_54_S202.md` (md5 `8fede84d7126e13fca17418e449f9d0a`), which is the owner of
> every VPS and manojz pin (and the source `gen_live_pins.py` generates from).
> The pin this record fixes has moved repeatedly since S201; `S203_MARG_RETIREMENT_LIST.md` §1 row 5
> counts four moves. **Where the Register and the box disagree, the box wins (D321(d), F-169).**
> The one durable item here — the offline-harness recovery recipe — is intact below and is cited by
> `S201_PARKED_BACKLOG.md` §B (md5 `3083d35fb29b5565d2bebb4b6aeb2b26`), which is KEEP.
> Label added at S203, 26-Aug-2026. **Retained, not deleted (F-23).**

# S201_A1FIX — live pin record (recorded AS IT MOVED, F-97)

**25-Aug-2026 17:03 IST · kit `S201_A1FIX` INSTALLED GREEN, first pass.**

| file | was | now |
|---|---|---|
| `/root/finance/finance_app.py` | `2c99b2c6c719091deada5603fc295c90` (S198_H2, smoke 680) | **`d930b6b5bca59e7f52ce46f6b88332fd`** (smoke **683**) |

Backup: `/root/deploy/_backup_S201_A1FIX_20260825_170311`.
`/finance/healthz` → HTTP 200 after restart.

## What the kit is

**Auditor finding AF-2, closed.** The A1 save-time *"does your total match Marg?"* warning — and its
**high-severity `TOTAL_VS_MARG` data_flag** — had **never fired once since S195**.

`_marg_total_for_date()` (line 3843) reads a staged push looking for days keyed `business_date` /
`net_p`. `api_marg_push`'s `days_payload` (line ~2870) wrote `date` / `expect` / `lines_csv` /
`items_csv`. The reader could never match a real staged push.

**Confirmed from the live bytes, not from the database.** The S198_H2 kit in the repo hashes to the
live pin exactly, so both functions were read directly — no `SELECT COUNT(*)` needed. The auditor's
predicted `0` was right by construction.

**The fix:** carry the two keys through. Both values were already in `d` — the loop reads
`d["business_date"]` on its first line and `d["net_p"]` two lines later for the survey. **Purely
additive:** the apply path reads only `date` / `expect` / `lines_csv` / `items_csv` and ignores every
other key, so replay behaviour is byte-unchanged.

**The vacuous test replaced.** The push-path stub fabricated the **reader's** key shape, so the suite
stayed green while the feature was dead — the S195 "never assert against an invented fixture" lesson
recurring inside the machinery built to encode it. The three new checks go through the **real
writer** and then call the **real reader**:

- `AF-2: the staged payload carries business_date`
- `AF-2: the staged payload carries net_p`
- `AF-2: _marg_total_for_date FINDS a real staged push`

## Proof chain

**Offline differential** on the seeded live-shape store (S193_F6 `seed_live_shape.py` + the four
additive migrations S182_clinic / S182_c2 / S183_marg_map / S186_reserve_yesbank), every imported
module hash-recovered to its live pin — `finance_ingest 6cb83302` · `marg_report 6411a57d` ·
`staff_ledger acd7b538` · `finance_yesbank 5dcbdd3a`:

**570/679 → 573/682, +3 exactly, fail set byte-identical (109 rows).**

**On the box:** 680/680 → **683/683, +3 exactly** — the projection held to the check.

## A capability unlocked, worth recording

The offline smoke harness was rebuilt from the repo alone. **The live VPS bytes are recoverable**:
`deploy_kits/S198_H2/finance_app.py` hashes to the live pin exactly (D188 — recover by hash, never by
filename). Recipe:

```
finance_app.py      deploy_kits/S198_H2/finance_app.py               2c99b2c6
finance_ingest.py   deploy_kits/S194_TRIPLE/finance_ingest_S194.py   6cb83302
marg_report.py      deploy_kits/S193_DISC/marg_report_S193.py        6411a57d
staff_ledger.py     deploy_kits/S193_F6/staff_ledger_S193.py         acd7b538
finance_yesbank.py  deploy_kits/S186_R1a/finance_yesbank.py          5dcbdd3a
finance_upi / finance_returns / finance_identity   from finance/
schema              deploy_kits/S193_DISC/finance_schema_S193.sql -> finance_schema.sql
seeder              deploy_kits/S193_F6/dev/seed_live_shape.py
then apply the four additive migrations listed above
```

This is what lets a kit's `+N exactly` projection be **measured** rather than guessed, before
anything touches the money system.

## A fault I reported that was NOT real — retracted, and why

During this kit I reported that **`vps_deploy.sh` could not find any installer written since
S196_HLT3**: its last line globs `bash install_*.sh` (lowercase) while kit installers have been
`INSTALL_*.sh` (uppercase) since S196_HLT3, and Linux globs are case-sensitive.

**That was wrong, and it was tested and disproven the same hour.** Run live:

```
bash /root/deploy/vps_deploy.sh S201_A1FIX
  -- kit found and internally consistent:  S201_A1FIX d602ea6e…
  -- handing off to the kit's own gated installer...
  [2/7] currency gate
        finance_app : d930b6b5bca59e7f52ce46f6b88332fd
  *** RED: expected 2c99b2c6… STOP
```

The wrapper pulled, verified `SUMS.md5`, read `KIT_ID.txt`, **found and ran the uppercase
installer**, and stopped at the currency gate because the fix was already installed — a clean no-op
proof of the whole path.

**Where the mistake came from:** I read `deploy_kits/S182_C1a/deploy/vps_deploy.sh` — the stale
*shipped copy* in the repo — and assumed the live `/root/deploy/vps_deploy.sh` matched it. The live
copy already carries the case-insensitive glob. **This is exactly D188 — a file's location is not
its provenance — committed while quoting D188 in the same document.** Verify the live artefact, not
a copy that shares its name.

**The residual, minor and real:** the repo's shipped copy of `vps_deploy.sh` is stale relative to the
live one. Worth syncing so a rebuild from the repo does not reintroduce the old glob.

## Owed at the next fold

- KB Register live-file table: `/root/finance/finance_app.py` → `d930b6b5…`, smoke 683.
- Mint an F-number for AF-2 (born-dead check + a fixture that mirrored the reader).
- Sync the repo's `vps_deploy.sh` to the live one.
- `live_pins.txt` regeneration.

---
*S201_A1FIX · installed by the owner from Termius · no patient identifiers reproduced; no tokens read
or printed.*
