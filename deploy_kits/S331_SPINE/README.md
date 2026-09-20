# S331_SPINE — the spine, rungs 1–3 (Sanjeevni · S272 · 20-Sep-2026)

**Project: Sanjeevni — Pharmacy & Marg.** Plan: `S272_SPINE_ARCHITECTURE.md` (working papers S272 and the project).
Owner's word, 20-Sep: *"build the three steps … and in all cases the 6 September stock check every aspect should be
left untouched until it is completed."*

**One line on the VPS, after the publish:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S331_SPINE/install_S331_SPINE.sh
```

## What it is

One new folder, `/root/finance/spine/`, and nothing else:

| file | rung | what |
|---|---|---|
| `marg_read.py` | 1 | the certified readers — one per Marg report the spine uses (salt list, category list, item master, whole-stores closing, purchase bill-wise, purchase supplier/item- and bill/item-wise, sale bill-wise DETAIL). Every row classified positively; every report checked by its own witness; the sale reader never reads the patient columns |
| `spine_evidence.py` | 1 | the evidence store: one PHI-free JSON reading per export in the Drive archive, read through the collector's own read-only `DriveSource`; the raw file is fetched to a private temp folder and deleted. Readings in `MargArchive/_SPINE_SEED/` (the April–Aug back-fill, made on manojz with the same reader) are copied in |
| `spine_build.py` | 2 | `spine.db` built **from empty** from the readings and `spine_rules.json`, the gate run against it, and only a passing build renamed over the old one. A failing build is kept as `spine.db.failed`; the last good spine stays |
| `spine_rules.json` | 2 | every hand-declared fact with its source: the opening (Marg's 31-Mar closing), the 34 dated reconciliation entries (S270 reference §6), the aliases the S229 spine and S270 learned, the 31-Mar total exception |
| `spine_read.py` | 3 | the one read door (`Spine().stock / sales / fact / bills / purchases / status`). **Nothing reads it yet** — rung 4 will |
| `spine_compare.py` | 3 | the witness: where today's tables differ from the spine, per lane, read-only, into `spine_compare_latest.txt` |
| `selftest_spine.py` | — | 39 checks; every reader and the gate are **made to fail on purpose** (F-536's rule) |

## What it touches, and what it does not

- **Touches:** the new folder; **two lines in root's crontab** tagged `# S331_SPINE` (every 10 min 08–23: evidence then
  build; 23:55: compare). *Declared for the parent's next open, as §3 of the Sanjeevni start prompt requires.*
- **Does not touch:** any existing file; any table of `finance.db` — it is opened **read-only**, for one `COUNT(*)` of
  `stock_count_item` (gate check: 373 = the 06-Sep count is untouched); the collector; the archive; the shadow; the
  old `marg_spine.py`; any screen. The switches honoured: `/root/finance/_off/ALL_OFF` and `/root/finance/spine/OFF`.
- **Backups:** the spine is rebuilt from the archive, so what must be backed up is the archive (already mirrored) —
  `spine.db` is not added to the state backup by this kit (named to the parent).

## The gate (reference §8, as run offline on the 19-Sep database and the whole archive, 20-Sep 02:38 IST)

14/14 blocking checks green: every export passes its own witness or a sourced exception · every purchase line ties to
exactly one bill-wise bill (supplier + number + date; a number two suppliers share on one day is settled by its lines'
money) · the 5 purchase returns carried as RETURN (F-527) · 3,915 sale bills, no repeat, the 72 missing bills present ·
**stock = Marg on every item at the latest checkable closing (17-Sep)** — 144 earlier item-day differences all closed by
a later closing (Marg keyed the entry after the export) · the 06-Sep count 373/373 · no salt is the shop's name ·
every sale and purchase name reaches an item Marg holds. Non-blocking notes carried: 1 purchase bill whose lines do
not re-add (LKD 67025: Marg's own bill-wise figure, 1,862 vs 1,822.91 net), the 10 Marg-side sale bills (fault 12),
43 items whose live median-price "MRP" differs from Marg's MRP.

## The opening (the one question §6 of the plan raised)

The owner's 20-Sep re-export of the 31-Mar closing (md5 cc608ca2) is **row-for-row identical** to the 27-Aug export
except Marg's advertising footer. So the 40-unit gap is Marg's own printed total, not a reading error; the lines are
taken and the printed total carried as a sourced exception in `spine_rules.json`.

## Rehearsed (fake root, the real archive mirror and the real 19-Sep database)

install green (157 readings, gate 14/14, compare, 2 cron lines) · re-run = ALREADY INSTALLED · `--restore` · seed
missing → REFUSED at 6/8, nothing scheduled · gate failing (no bill-wise purchases) → REFUSED at 7/8, no spine, nothing
scheduled. `SUMS.md5` verifies inside the folder. `NO_PHONE_NUMBERS.py` clean.

## Numbering note (for the close)

Claimed as S324 at 02:36 (the board's nextFree), withdrawn three minutes later: the published repository already held
S324–S330 (the parent's 19-Sep kits, no board claim). Renumbered S331 before any file was copied into `deploy_kits\`.
