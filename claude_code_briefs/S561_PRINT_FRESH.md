# S561_PRINT_FRESH — brief for Claude Code (v2 — after an independent read, R1 (1 blocker, 5 corrections), all taken in)

*Written 15-Oct-2026 by the Sanjeevni chat (session 316) at the owner's word (14:29 IST: "your method will not be sustainable at staff level, need to find a proper solution"; 14:31: "Use the api credits for this build"). Read `claude_code_briefs/SANJEEVNI_BUILD_CHARTER.md` (v1.1), `CLAUDE.md` and `deploy_kits/KB_canon_all/BUILD_NORM_v1.md` first. Kit shape: S537's (no data step). Line numbers: the live bytes of the 15-Oct 01:35 IST bundle.*

## 0 · For the owner

1. **What happened (15-Oct 14:24).** On his phone, *Print the order sheet* opened a sheet headed *"Order: 12-10-2026 · Darpan (Marg) · 14 supplier · 35 dawa"* — the layout from before S543 (14-Oct 08:35): "strip" units, CHYMORAL AP, "XGESIC LA purana, 17-09". At the same minute the server gave the right sheet to every request (31 of 31 fetches, 37,170 bytes, *"Marg ka khula order: 15-10-2026 14:12 · 14 supplier · 44 dawa"*), with `Cache-Control: no-store`, and the old wording exists nowhere in the live code. So the phone reopened a copy it already held. The button opens the same address every time and the file name is the same all day (`order_sheet_2026-10-15.pdf`), so any phone can do this on any day.
2. **After this kit, a phone has nothing old it could reopen:**
   - both buttons (*Order sheet print karo* / *Print the order sheet*, and *Marg ka order (PDF)*) open an address that carries the export's stamp and the moment of the tap — a new address at every tap;
   - the file's name carries the export's time — and, for the order sheet, the print's time too, because its ticks change during one export: `order_sheet_15-10_1412_143107.pdf`, `marg_order_15-10_1412.pdf` (no export: `order_sheet_15-10_<HHMM>_<HHMMSS>.pdf`, `marg_order_15-10_<HHMM>.pdf`, both from the print's time);
   - the order sheet's foot carries *"chhapa: 15-10-2026 14:31  ·  Sanjeevni"* on every page, as Marg's PDF already does.
3. Nothing else changes: the same buttons, the same words, the same sheet.

## 1 · Numbers and pins

- Kit **S561_PRINT_FRESH** (claimed 14:3x IST 15-Oct, board `_numbers` v430 → v431, with its PLANNED line). No D or F number. Project: **Sanjeevni**.
- **FROM pins (read first; a different byte = STOP that file, report):**
  - `/root/finance/porders_s454.py` **72e7fd56** (S543) — §2.1, §2.2
  - `/root/finance/order_sheet_pdf.py` **d0735df8** (S543) — §2.3
  - `/root/finance/marg_order_pdf.py` **c9cd44a5** (S543) — read; edited only if §2.2 needs it (it should not)
- **Read only:** `order_sheet.py` (`newest_sheet`, `now`, `today`; 247eeb48, S556), `DUTY_MAP.json`/`.md` (no duty changes — no edit).
- Services: `clinic-finance` restarted once. The build lock. Scratch `_scratch\S561_PRINT_FRESH\` and the server's `/tmp`. F-185: the walk prints no cell of an export and no PDF text with a phone number (assert no run of 10 digits in its output).

## 2 · The edits

### 2.1 The two buttons (porders_s454.py, `order_list` 605–607)
- `href` = `P + "/s454/sheet.pdf?s=<stamp>&t=<server now, YYYYMMDDHHMMSS>"` and `P + "/s454/marg.pdf?s=<stamp>&t=…"`, escaped with `esc()` (so the HTML reads `&amp;t=`). `<stamp>` is `OS.newest_sheet(con)["stamp"]` when it matches the regex `_stamp_text` uses (order_sheet.py 736; shape `%Y%m%d-%H%M%S`, written by marg_watch/marg_router), else empty (older sheets have `''`) — never a sliced cleaned string. The page is already `no-store`.
- **And at the tap:** both links get `data-fresh="1"`, and once per page, after line 607, the inline script `<script>document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a[data-fresh]');if(a){var u=new URL(a.href);u.searchParams.set('t',Date.now());a.href=u.href;}},true);</script>` (inline scripts and `onclick` already work on this page — `JS` in `shell()` 205–231; no CSP). No `preventDefault`, no `window.open`: `target="_blank"` keeps working on Android. No change to any other button.
- Search the live `/root/finance/*.py`, `*.html` and `/root/portal/` for any other link to these two routes (the repository copies show none outside 605–607) and give it the same treatment; name them in the report.

### 2.2 The routes (porders_s454.py `r_sheet_pdf` 1024–1034, `r_marg_pdf` 1037–1050)
- Both ignore `s` and `t` for what they build (always the newest sheet, as today).
- **One clock:** each route takes `n = OS.now()` once (not `OS.today()`, which follows the `ORDER_TODAY` setting, order_sheet.py 124) and passes it on: `order_sheet_pdf.build(con, now=n)`.
- `Content-Disposition`: `inline; filename="order_sheet_<dd-mm>_<HHMM>_<HHMMSS>.pdf"` — the export's `dd-mm_HHMM` from the newest sheet's stamp (`20261015-141250` → `15-10_1412`) and the print's `HHMMSS` from `n`; `"marg_order_<dd-mm>_<HHMM>.pdf"` from the export alone (its content is the export). No sheet or a stamp that does not match → `n.strftime("%d-%m_%H%M")` (and `_%H%M%S` for the order sheet).
- Headers on both: `Cache-Control: no-store, max-age=0`, `Pragma: no-cache`, `Expires: 0`.
- The audit rows (`s454_sheet_printed`, `s454_marg_pdf_printed`) also record the file name.

### 2.3 The printed time on the order sheet (order_sheet_pdf.py)
- One more foot line on **every** page: the exact string of marg_order_pdf.py 121/129, `"chhapa: %s  ·  Sanjeevni"` (two spaces each side of the dot) with `now.strftime("%d-%m-%Y %H:%M")`, size 8, regular.
- **Placement (R1-7): do not grow `_foot_h`.** Draw it at the last `FOOT2` baseline − 3.6 mm, inside the space already reserved (1.3 mm above the bottom margin today), so `_measure`, `rows_per_page` and the page count do not change. marg_order_pdf imports only `SP.width`, `SP.wrap`, `SP._Page`, `SP._build` — untouched.
- `build(con, lay=None)` (408) takes an optional `now=None` for the walk; nothing else in the layout changes (the heading line, the bands, the rows, the tags).

## 3 · The walk (`walk_s561.py` — S537's shape; a scratch copy of finance.db; rows by key)
1. The order page as `shavez` and as `manoj`: both links carry `s=<the newest stamp>`, `&amp;t=` and `data-fresh`; with `OS.now` patched to two fixed times, two renders give two different `t`; the click script is present once.
2. Each route, with `OS.now` fixed, gives the same bytes with any `s`/`t` or none: 200, `filename="order_sheet_<dd-mm>_<HHMM>_<HHMMSS>.pdf"` / `"marg_order_<dd-mm>_<HHMM>.pdf"` built from the install-day sheet's stamp (read, not typed) and the fixed now, the three no-cache headers.
3. A copy with no `order_sheet` rows: the file names fall back to today's `dd-mm` and the `HHMM` of a fixed `now`.
4. The sheet's PDF text: "chhapa: <fixed now>" once on every page; the heading line unchanged byte for byte against the OLD file's layout line; the page count and the rows on each page the same as the OLD file's for the install-day sheet and for a made-up sheet of 120 lines; the last row's bottom ≥ the foot's top on every page.
5. **Controls on the OLD files:** (1) no `s`/`t`; (2) `filename="order_sheet_<yyyy-mm-dd>.pdf"`; (4) no "chhapa" → red.
6. S543's walk, read-only, on the new files: its markers stay green except two expected reds — `C: 9 heal` (REPORT_S556) and the check at walk_s543.py 353 for the exact `href="/finance/porders/s454/marg.pdf"` (the link now carries `?s=`); re-check that one as `href="/finance/porders/s454/marg.pdf?s=`.
7. Assert no run of 10 digits in the walk's own output.

## 4 · Install, publish, report
Gates → FROM pins → compile both pythons → walk + controls → backups (`porders_s454.py.bak_S561_72e7fd56`, `order_sheet_pdf.py.bak_S561_d0735df8`; `finance.db.bak_S561_<stamp>` by the backup API) → place → md5 read-back → ONE restart of `clinic-finance` → healthz 200 → on the live box, read-only: `/finance/porders/s454/sheet.pdf` with a session of the walk's own (never a staff login's secret) gives the new file name and "chhapa". Red: restore, restart, healthz, report. Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`; `claude_code_briefs/REPORT_S561.md` (3–6 plain lines on top; FROM → TO; the walk with every control red; Charter — retired: the one-name-a-day file name; left for later / seen, not touched: what the build finds); publish again.
