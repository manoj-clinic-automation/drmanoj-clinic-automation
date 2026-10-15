# S561_PRINT_FRESH — the two order PDFs are fresh at every tap

Brief: `claude_code_briefs/S561_PRINT_FRESH.md` (v2, Sanjeevni session 316, 15-Oct-2026). No D or F number. Project: Sanjeevni.

## What and why
On 15-Oct at 14:24 a phone opened *Print the order sheet* and showed a copy from before S543, even though the server sent the right sheet
to every request. The phone reopened a copy it already had: the button opened the same address every time, and the file had the same name
all day (`order_sheet_2026-10-15.pdf`). After this kit:

- **Both buttons** (*Order sheet print karo* / *Print the order sheet*, and *Marg ka order (PDF)*) open
  `…/s454/sheet.pdf?s=<the export's stamp>&t=<the server's moment>` (and the same for `marg.pdf`). The links carry `data-fresh="1"`, and a
  small click script, once per page, sets `t` to the moment of the tap. So every tap opens a new address. `target="_blank"` stays, and the
  script never calls `preventDefault`.
- **The routes** ignore `s` and `t` and always print the newest sheet, as before. They read one clock, `order_sheet.now()`, once per
  request. The file names: `order_sheet_<dd-mm>_<HHMM>_<HHMMSS>.pdf` (the export's day and time, then the print's time) and
  `marg_order_<dd-mm>_<HHMM>.pdf` (the export's day and time). With no sheet, or a stamp of the wrong shape, the print's time is used.
  Headers: `Cache-Control: no-store, max-age=0`, `Pragma: no-cache`, `Expires: 0`. The audit rows also record the file name.
- **The order sheet's foot** says `chhapa: dd-mm-yyyy hh:mm  ·  Sanjeevni` on every page, as Marg's PDF already does. It is drawn inside
  the space the foot already keeps (3.6 mm under the last foot line), so the page count and the rows on each page do not change.

The words and buttons are unchanged, and so is the sheet itself.

## Pins (FROM → TO)
| file | FROM | TO |
|---|---|---|
| `/root/finance/porders_s454.py` | `72e7fd563dadf2ae657fadef66e4e72e` | `1c3d3927163e08114e3e26c5f06052a4` |
| `/root/finance/order_sheet_pdf.py` | `d0735df84f17a67474bc0cecd58e5c6c` | `b0cc86945d560e8cce842b799913e021` |

Read only (pinned by the installer): `marg_order_pdf.py` `c9cd44a5…`, `order_sheet.py` `247eeb48…`. `DUTY_MAP.json` / `.md` are not changed
(no duty is added, moved or removed).

## Files
- `make_s561.py`: the anchored patcher (4 + 4 counted edits, each anchor exactly once, FROM and TO pins checked).
- `walk_s561.py`: the test. It runs on scratch copies in `/tmp`, and has a negative control on the old files (`--expect-red`, all 13 `C:`
  checks red) and the after-placing look (`--page`).
- `install_S561_PRINT_FRESH.sh`: gates → pins → compile on both pythons → rebuild → walk + control + S543's walk (new beside old) →
  backups → place → md5 read-back → ONE restart of `clinic-finance` → healthz 200 and the pages 302 → journal → the look on a copy →
  restore on red.

Run: `rm -rf /tmp/s561kit && cp -rp <kit> /tmp/s561kit && bash /tmp/s561kit/install_S561_PRINT_FRESH.sh` (`DRY=1` = gates and walks only).

## Touches
`/root/finance/porders_s454.py` and `/root/finance/order_sheet_pdf.py`, plus their `.bak_S561_<from8>` copies. It also writes
`finance.db.bak_S561_<stamp>` (backup API), but the database itself is never written. Restarts `clinic-finance` only.

## Retired
- The one-name-a-day file name (`order_sheet_<yyyy-mm-dd>.pdf` from `OS.today()`, which follows `ORDER_TODAY`), and the cleaned-stamp
  name `marg_order_<yyyymmdd-hhmmss>.pdf`.
- The fixed button addresses `…/s454/sheet.pdf` and `…/s454/marg.pdf` with no query.

## Left for later
- The words `chhapa: %s  ·  Sanjeevni` now appear three times: twice inline in `marg_order_pdf.py` (121, 129) and once as
  `order_sheet_pdf.PRINTED`. `marg_order_pdf` could read `SP.PRINTED`, but this brief left that file untouched.
- The stamp's shape regex appears in two places: `order_sheet._stamp_text` (read-only here) and `porders_s454.STAMP_RE`.

## Undo
```
\cp -p /root/finance/porders_s454.py.bak_S561_72e7fd56 /root/finance/porders_s454.py && \cp -p /root/finance/order_sheet_pdf.py.bak_S561_d0735df8 /root/finance/order_sheet_pdf.py && systemctl restart clinic-finance
```
Then check that healthz answers 200 and read the two md5s back.
