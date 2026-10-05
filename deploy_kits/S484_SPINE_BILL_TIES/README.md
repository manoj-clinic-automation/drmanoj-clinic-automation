# S484_SPINE_BILL_TIES — the spine ties a shared bill number, orders same-second exports by what they are, and takes S483's two reader edits

Brief: `claude_code_briefs/S484_SPINE_BILL_TIES.md` (Sanjeevni chat, session 295, 05-Oct-2026). Faults **F-734, F-735** (S483's,
repaired here), **F-736** (repaired here), **F-737** (recorded and measured, NOT repaired). No D-number. Report:
`claude_code_briefs/REPORT_S484.md`. S483's kit folder stays as published; nothing of it is installed on its own.

## What, and why

`spine_build.py` refused every ten-minute build of 05-Oct from about 08:10. S483 mended the reader and its walk showed the gate
would still refuse, on five purchase lines. This kit carries the whole repair:

- **The reader (`marg_read.py`, S483's E.1 and E.2, the same bytes):** a date-only row is a DATE wherever its one cell sits; a
  list heading may carry one short code beside its name (`data["code"]`). Built by `make_s484_reader.py` — S483's
  `make_s483.py` under this kit's name, byte for byte; the file comes out `96f565a8`, as S483 built it.
- **The order of same-second exports (`spine_build.py`, §1.1 and §1.2, F-736).** The build sorted exports by stamp alone, so
  exports of one second fell into the store's file order — md5 order. Now: bill-wise exports by `(stamp, number of bills, md5)`;
  purchase-lines exports by `(stamp, grouping == SUPPLIER, number of lines, md5)` — at an equal second the sheet that names the
  supplier is the later, then the fuller print, then md5 so the order is total.
- **A bill number two suppliers share on one day, in a BILL-grouped sheet (§1.3, §1.4, F-736).** The sheet prints both bills'
  lines under the one number. Today's test stays first (all lines of the number sum to exactly one bill). When it settles on no
  single bill, `cut_shared_bill` cuts the number's lines, **in sheet order**, into as many runs as there are bills and looks for
  the cuttings whose money matches each bill within the gate's own tolerance (₹1 + 0.2 %). **Exactly one fit → each line ties to
  its run's bill. None, or more than one → every line stays tied to no bill**, and the gate line fails as before when the sheet is
  the authority. A group of more than 24 lines or more than 4 bills is not enumerated.
- **`BUILD_VERSION`** `S331.1` → `S484.1` (`sp_meta` records which rules made a spine).

## Pins — FROM → TO

| where | file | FROM | TO |
|---|---|---|---|
| server | `/root/finance/spine/spine_build.py` | `ce99bedf60194a84fe93455927a336e2` | `11f8acb05c46aeaa72e1771d5c89922c` |
| server | `/root/finance/spine/marg_read.py` | `099d621315f3bf9297a9b4626a5caee5` | `96f565a8d138d9ce75c0ed228b471495` |
| server | `spine/readings/de92f5d5185646d4de563e30d5464f6e.json` | `0af44311…` (0 of 208 lines dated) | removed (`.bak_S484_0af44311` beside it), written again by the mended reader |
| server | `spine/readings/f62cc9e3d93c692f1795229be9e7cfe1.json` | `b054e6c8…` (ok False) | removed (`.bak_S484_b054e6c8` beside it), written again |

Read only, md5 unchanged: `spine_evidence.py` `0fcf6c64`, `spine_read.py` `712a1e4e`, `selftest_spine.py` `fc63d2c6`,
`spine_rules.json`, `reports_tile.py`. `spine.db` is never written by this kit: the build swaps it in when its gate passes.
`finance.db` is read only to the build (it is backed up all the same — the rulebook's rule 6).

## The files here

| file | what it is |
|---|---|
| `make_s484.py` | the anchored patcher of `spine_build.py`: five sites, each anchor exactly once (`BUILD_VERSION`, the helper above `def build`, the two sort keys, the branch) |
| `make_s484_reader.py` | S483's `make_s483.py`, unchanged but for its name: builds `marg_read.py` |
| `walk_s484.py` | the walk, six sections, on scratch copies on the server: the reader · the order · the tie · the gate (four builds) · F-737 measured · the new spine against the last good one |
| `install_S484_SPINE_BILL_TIES.sh`, `PINS.sh` | gates → pins → both builds → compile on both pythons → walk on scratch copies → backups → place by rename → md5 read-back → the two readings removed → restart `clinic-finance` once → healthz → the spine's own job once, as the crontab spells it → the gate's line read back → restore on red |

## Run / undo

- `bash /root/deploy/repo/deploy_kits/S484_SPINE_BILL_TIES/install_S484_SPINE_BILL_TIES.sh` (holding the build lock; `DRY=1`
  places nothing).
- Undo: put back `spine_build.py.bak_S484_ce99bedf` and `marg_read.py.bak_S484_099d6213`, copy the two readings'
  `.bak_S484_<md5-8>` over them, restart `clinic-finance`, healthz 200, read the md5s back. The spine's gate then refuses again on
  the two lines of the morning of 05-Oct; the `spine.db` this kit's build swapped in stays until a later build passes.

## Calls made while building (each is in the report, with its reason)

1. **`itertools` is imported inside `cut_shared_bill`**, not at the top of the file — the brief allows five edit sites and
   "nothing else in the file".
2. **`tol` is passed as a function of the bill** (`lambda b: 100 + 0.002 * abs(b["amount_p"])`, the gate's own expression) — the
   tolerance depends on each bill's amount, so "the same expression, not a new constant" can only be handed over as one.
3. **An untied line of a shared number records how many bills carry that number** (the pre-filter count, as the brief asks) where
   the old code recorded how many survived the whole-sum test (0). Only the wording of the gate's detail changes.
4. **Section 3 also runs the tie end to end**, on a scratch store without the two SUPPLIER-grouped sheets — there `de92f5d5` is
   the authority of its period and the build itself must tie the five lines (in the true store the SUPPLIER sheet is the
   authority, so the tie is not what puts those lines into the spine).
5. **Section 6 is two comparisons, not one.** Sixteen readings arrived after the 08:00 build, not two, so "nothing else should
   move but what the two readings bring" cannot be read off one diff. 6a builds the 08:00 evidence again (212 readings) with the
   OLD and the NEW file: the same spine, row for row, in every table. 6b then explains every added and removed row of the true
   new spine by the readings that arrived since.
6. **Gate details are compared by verdict, not by wording, across builds:** two STOCK lines print a dictionary whose order changes
   from one run to the next, under the old file too.
7. **The installer runs the spine's job under `flock -n`, as the brief spells it, and tries again every 15 s** (up to 20 times)
   when the ten-minute job holds the lock — a busy lock writes nothing to `spine.log`, so a run is known by its lines.
8. **No staff-eye walk section and no duty-map change:** no page, tile, duty or door changes.

## Not in this kit

**F-737** — a filtered purchase-lines print cannot be told from a whole one by its own text; exported after the whole one it
becomes the period's authority (section 5 measures it: 208 lines → 5, gate still 13/13). The cutter's column rule for a one-token
line (F-734's root, the next medical-PC kit). Equal stamps from a one-second batch conversion (S480's converter).
