# REPORT S561_PRINT_FRESH — 15-Oct-2026 (installed 15:10 IST)

**For the owner**
- A phone can no longer reopen an old copy of either order paper. Every tap on *Order sheet print karo* / *Print the order sheet*, or on
  *Marg ka order (PDF)*, now opens a new address, so the phone has to fetch the paper fresh from the server.
- The file names now carry the export's time, for example `order_sheet_15-10_1412_151030.pdf` and `marg_order_15-10_1412.pdf`. The order
  sheet's name also carries the time it was printed. So two papers no longer share one name all day.
- Every page of the order sheet now says at the bottom when it was printed, for example *"chhapa: 15-10-2026 15:10  ·  Sanjeevni"*, as
  Marg's own PDF already does.
- Nothing else changed: the same buttons, the same words and the same sheet (the pages and the rows on each page are the same as before).
  Tested on a copy first, installed, and checked on the server: working.

---

## For the chat

### Live files, FROM → TO, read back on the box (15:10:40 IST, `date` on the box)
| file | FROM | TO (read back) |
|---|---|---|
| `/root/finance/porders_s454.py` | `72e7fd563dadf2ae657fadef66e4e72e` | `1c3d3927163e08114e3e26c5f06052a4` |
| `/root/finance/order_sheet_pdf.py` | `d0735df84f17a67474bc0cecd58e5c6c` | `b0cc86945d560e8cce842b799913e021` |
| `/root/finance/marg_order_pdf.py` (read only) | `c9cd44a55d4cb39247d3c2e8e2602f1d` | unchanged |
| `/root/finance/order_sheet.py` (read only) | `247eeb48db8cc007faedfe14f3676893` | unchanged |

All four FROM pins matched the brief before anything was touched.

### What was built (kit `deploy_kits/S561_PRINT_FRESH/`)
- **porders_s454.py** (4 counted edits):
  - The two buttons (were lines 606–607) now carry `href="/finance/porders/s454/sheet.pdf?s=<stamp>&amp;t=<YYYYMMDDHHMMSS>"` (the same for
    `marg.pdf`) and `data-fresh="1"`, keep `target="_blank"`, and are followed once by the brief's click script (`FRESH_JS`, byte for byte).
  - `<stamp>` is `OS.newest_sheet(con)["stamp"]` when it matches `_stamp_text`'s regex (`STAMP_RE`), else `''`.
  - `r_sheet_pdf` / `r_marg_pdf` take `n = OS.now()` once, call `order_sheet_pdf.build(con, now=n)`, name the file through `_pdf_name`,
    send `_pdf_headers` (no-store, max-age=0 / no-cache / 0), and record `file=` in both audit rows.
  - Both routes ignore `s` and `t`.
- **order_sheet_pdf.py** (4 counted edits):
  - `PRINTED = "chhapa: %s  ·  Sanjeevni"`.
  - `build(con, lay=None, now=None)`.
  - One `p.text(LM, <last FOOT2 baseline> − 3.6 mm, …, 8)` per page, regular font. `_foot_h`, `_measure`, `rows_per_page` and
    `marg_order_pdf`'s imports are untouched.
- **Other links to the two routes** (§2.1): `grep -rnI` of the live `/root/finance` and `/root/portal` (`*.py *.html *.js *.json`, excluding
  `.bak`) found none outside porders_s454.py 606–607 (the route lines and the header comment only). Nothing else was changed.

### The walk (`walk_s561.py`, on the box, scratch copies in /tmp, rows by key) — new files: **WALK OK S561, 26 checks green**
Install-day state, read before the walk: newest sheet id 5, stamp `20261015-141250` (the export's shape), `order.source marg_sheet`,
ordering not frozen, Marg's open order 44 lines / 14 suppliers, 14 suppliers still to order, so both buttons are shown.
1. The buttons for darpan, shavez, shivani, alisha, reception and manoj:
   - `s=20261015-141250&amp;t=…`, `data-fresh`, `target=_blank`.
   - Two fixed moments (14:31:07, 14:33:52) give two different `t`.
   - The click script appears once.
   - S543's link is re-checked as `href="/finance/porders/s454/marg.pdf?s=`.
   - The words on the buttons are unchanged, and the page is still no-store.
2. Routes, with the clock fixed:
   - The same bytes with no query, with `s/t`, with a wrong `s` and with a short `t` (8 reads each, shavez and manoj).
   - The file names are `order_sheet_15-10_1412_143107.pdf` and `marg_order_15-10_1412.pdf`, built from the stamp read from the database.
   - The three no-cache headers are sent.
   - Both audit rows carry `file`.
3. Fallbacks:
   - No `order_sheet` rows gives `order_sheet_15-10_1431_143107.pdf` / `marg_order_15-10_1431.pdf`, even with `ORDER_TODAY=2031-03-05` set
     (one clock).
   - Every stamp `''` gives the same names, and the buttons carry `s=&amp;t=`.
4. The printed sheet:
   - `chhapa: 15-10-2026 14:31  ·  Sanjeevni` appears exactly once on each of 2 pages.
   - The heading line is byte for byte the old file's (same text, place and size).
   - Pages and rows per page are the same as the old file's: install day [22, 22]; a made-up sheet of 120 W561 lines, 6 pages
     [27, 27, 27, 9, 23, 7].
   - `_foot_h` (49.89 pt) and `rows_per_page` (33) are unchanged.
   - Every row's bottom is at or above the foot's top.
   - The printed time is above the bottom margin and under the last foot line.
   - No two text runs overlap.
5. Staff-eye (S444):
   - The *Purchase orders* tile is on the portal home of all five reception logins (real portal.py and grants file, walk-only secret).
   - The door `/finance/porders` shows *Bill scan karna hai* (due 3), *Photo dekh kar bataiye* (1), *Maal aaya?* (2) and
     *Order karna hai* (14) to each of them.
   - Every page is under 100 KB and under 2 s.
6. The walk's own output holds no run of 10 digits.

### The negative control (the same walk on the OLD files) — every one of the 13 `C:` checks RED
```
RED: both buttons carry s=<stamp>, &amp;t=, data-fresh            (old href had no query)
RED: two fixed moments give two different t                        (t None)
RED: the click script exactly once                                 (0)
RED: S543's link as marg.pdf?s=
RED: sheet.pdf names the file order_sheet_15-10_1412_143107.pdf    (old: order_sheet_2026-10-15.pdf)
RED: sheet.pdf no-store, max-age=0 / no-cache / 0                  (old: no-store, None, None)
RED: marg.pdf names the file marg_order_15-10_1412.pdf             (old: marg_order_20261015-141250.pdf)
RED: marg.pdf no-store, max-age=0 / no-cache / 0
RED: the audit rows record the file name
RED: no order_sheet rows -> fallback names, ORDER_TODAY ignored    (old: order_sheet_2031-03-05.pdf — followed ORDER_TODAY)
RED: every stamp '' -> fallback names
RED: chhapa once on every page of the install-day sheet            ([0, 0])
RED: chhapa once on every page of the made-up 120-line sheet       ([0, 0, 0, 0, 0, 0])
WALK OK negative control: every one of the 13 'C:' checks is red on the old files (13 of 26 checks red)
```

### S543's walk, read-only, on the new files beside the live ones (§3.6)
- **New files:** 63 green, 7 red. **Live (old) files beside them:** the very same 7 red. The installer requires the two sets to be identical
  (plus the 353 check only).
- The 7 reds: `C: 9 heal` (as REPORT_S556 says), `C: 6 the brief's words …` and `C: … and on the printed sheet`, `C: section '5' ran to its end`,
  the two partial-line checks (RECEIVE 4:0 / PENDING 6:0), and "the three lines the newer export drops are on today's M: COCYP and Ked…".
- The brief expected only `C: 9 heal` and the 353 check. The other five are red on the live files too. They are bound to the 12-10 export's
  named lines (COCYP, UPRISE, Kedar, the brief's 26 words), and today's newest export is the 15-10 14:12 one, so this kit did not cause them.
- The 353 check stayed **green** on the new files: its condition is `cnt["order"] > 0 or (…)`, and 14 suppliers are still to order. It is
  re-checked by walk_s561 as `href="/finance/porders/s454/marg.pdf?s=` (green new, red old).

### Install (installer run from `/tmp/s561kit`, a byte copy of the kit; lock held throughout)
- `[1/10]` gates. `[2/10]` pins exact.
- `[3/10]` compiles on `/usr/bin/python3` and `/root/wa/venv/bin/python3`.
- `[4/10]` rebuilt from the live bytes at the TO pins.
- `[5/10]` walk, control and S543's walk as above.
- `[6/10]` backups: `finance.db.bak_S561_20261015_150926` (sqlite backup API, 600), `porders_s454.py.bak_S561_72e7fd56`,
  `order_sheet_pdf.py.bak_S561_d0735df8`.
- `[7/10]` placed; md5 read back = the kit's.
- `[8/10]` **clinic-finance restarted once at 15:10:26** (nothing else) and active. healthz 200. `/s454/order`, `sheet.pdf` and `marg.pdf`
  answer 302 without a login (the login gate, expected). Journal clean.
- `[9/10]` the placed files (copied) on a backup-API copy of the live database, as the walk's own header session (shavez) with the real
  clock, read at 15:10:30:
  - `sheet.pdf` 200, `order_sheet_15-10_1412_151030.pdf`, *chhapa* on 2 of 2 pages;
  - `marg.pdf` 200, `marg_order_15-10_1412.pdf`;
  - `/s454/order` 200, buttons carry `?s=…&t=…` and `data-fresh`.
  - PAGE OK.
- After the install, read independently: healthz 200 locally and on `https://followup.dr-manoj.in/finance/healthz`, and clinic-finance active.

**Rehearsed before the real run** on a made-up root under /tmp, with stub systemctl/journalctl:
- a forced red after placing put both files back byte-identically (72e7fd56 / d0735df8) and exited 1;
- the green run placed both files and gave PAGE OK;
- a second run said ALREADY INSTALLED.

The live files were untouched by the rehearsal. A `DRY=1` run on the real box was green before the install.

**Published** with PUBLISH_ALL (commit `33256ec`; the same publish also carried the other chat's pending brief
`S562_BANK_SMS_STANDS_IN.md`, which is expected). Then `/root/deploy/repo` was pulled `--ff-only`. The kit in the clone passes
`md5sum -c SUMS.md5`, and so does the `/tmp/s561kit` copy that ran: byte-identical. The clone is clean. After the pull, the live md5s were
still 1c3d3927 / b0cc8694 and healthz 200. The build lock (`/root/deploy/.claude_code_build.lock`, owner S561_PRINT_FRESH, taken 15:05:53)
was held from the rehearsal to this report and then removed.

### Decisions made (no question was put to the owner)
- **§4 "on the live box, read-only: sheet.pdf with a session of the walk's own".** I did not fetch from the live service. That would need a
  real login (a live secret), and the route writes an audit row, which is not read-only. Instead:
  - the live service was probed for healthz 200 and 302 on the three routes;
  - the placed files, copied, were served on a backup-API copy of the live database with the walk's own header session (`[9/10]` above).
- **The S543 walk gate** is "the same reds on new as on live, plus only the 353 check", not "exactly two reds". Today's export makes five
  more of S543's state-bound checks red on the live files as well. Gating on exactly two would have blocked a correct kit for a reason
  that has nothing to do with it.
- The kit ships `rehearse_s561.sh` (the made-up-root rehearsal) beside the brief's files.

### Charter
- **Retired:**
  - the one-name-a-day file name (`order_sheet_<yyyy-mm-dd>.pdf` from `OS.today()`, which followed `ORDER_TODAY`);
  - the cleaned-stamp name `marg_order_<yyyymmdd-hhmmss>.pdf`;
  - the fixed, query-less button addresses.
- **Left for later:**
  - The words `chhapa: %s  ·  Sanjeevni` now appear three times: twice inline in `marg_order_pdf.py` (121, 129), plus
    `order_sheet_pdf.PRINTED`. `marg_order_pdf` could read `SP.PRINTED`, but that file was read-only in this brief.
  - The stamp-shape regex is in two places: `order_sheet._stamp_text` (read-only here) and `porders_s454.STAMP_RE`. order_sheet could
    export one helper.
- **Left out:** nothing.
- **Seen, not touched:** walk_s543.py is frozen and bound to the 12-10 export's named lines, so five of its checks are now red on the live
  files for state reasons. A later kit could have it read the install-day export, or retire those checks.
- **Dependency at install (rule 1b):** newest order sheet id 5, stamp 20261015-141250 (taken by marg_watch), source marg_sheet, not frozen.
  The kit adds no new dependency.
- **Duty map:** no duty added, moved or removed. `DUTY_MAP.json` / `.md` not edited (v14, `891defd8`).

### Not done, and why
- No data step (none in the brief). The database was backed up, never written.
- Files not named by the brief were not touched: `marg_order_pdf.py` and `order_sheet.py` were read only.

### Undo
```
\cp -p /root/finance/porders_s454.py.bak_S561_72e7fd56 /root/finance/porders_s454.py && \cp -p /root/finance/order_sheet_pdf.py.bak_S561_d0735df8 /root/finance/order_sheet_pdf.py && systemctl restart clinic-finance
```
Then check healthz 200 and read the md5s back (72e7fd56 / d0735df8).
