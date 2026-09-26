# REPORT_S404 — S404_ORTHO_STOCK_CLOSE (close the orthotic section of the 06-Sep stock check)

Installed on srv1746119 on **26-Sep-2026, 06:17–06:21 IST** (times read from the installer's log). Published with PUBLISH_ALL.bat.

## For Dr Manoj (plain English)
- **Darpan has a new tile, "Stock milaan"** (phone or PC). It shows only the orthotic part of the 06-Sep count, in Hindi.
  Card 1, *Adla-badli?*: 9 pairs where one size is short and another is over — he taps **Haan** (billed as the other size) or **Nahi**.
  Card 2, *Kam kyun?*: the 22 orthotic lines still short or over — he taps one reason chip (*Galti se bill nahi bana · Toota/kharab ·
  Vaapas nahi aaya · Pata nahi*; on a surplus *Bill bana, diya nahi · Pata nahi*). One tap saves (big green card); a repeat tap does nothing twice.
  A pair you already answered is greyed for him. His progress line reads *Orthotics: N mein se M ho gaye*, then *Sab ho gaya — ab Amir ke vouchers*.
- **Your hub** (`/finance/stock/page/hub?count=1`) gains a card **"Orthotics section"**: his answers beside each orthotic line with one-tap change,
  a **Make the orthotic round** button (it also runs by itself the moment Darpan finishes — orthotic lines only; the medicines wait for their own round),
  and the line **"Orthotics section: CLOSED on <date>"** that turns green only when all four hold: every line answered (your word where Marg must move),
  the orthotic vouchers entered by Amir, the proof green on Marg's next export, and all 22 renames seen in Marg.
- **Amir's board** gains **"Naam badlo (22)"**: old name → new name, one tick each *Marg mein badal diya*. The server does not trust the tick:
  it reads Marg's next stock export and marks each name **seen in Marg** by itself; a name ticked but not seen in two exports turns amber
  (*Marg mein abhi dikha nahi*). Sales, purchases and stock under a new name land on the old item — one item, two names, never two.
- Everything was proved on a copy of the live database (65 checks, plus the S400 and S402 checks re-run, all green) before a byte was placed.
  The live count, your two earlier answers and every money record are untouched. Nothing was ticked or answered for real yet.
- Darpan's page: **https://followup.dr-manoj.in/finance/stockmatch** · your hub: **https://followup.dr-manoj.in/finance/stock/page/hub?count=1**

## For the chat
### Live files FROM → TO (md5 read back on the box after placing, 26-Sep-2026 06:21 IST; re-read 06:25 IST identical)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_app.py | 1b473fbf586dea13edd40a6a993cb2ba | 586ae78ae6437f806692c2a1e4eeeb37 |
| /root/finance/stock_hub.html | c4f3280b2d005b39c02d3f6eed13c3ec | 68d11419e7fb9a8e5fec74095b60b255 |
| /root/finance/stock_amir.html | 14024b8dfc64c76959ec12f43e0a4f88 | c2ea41b2db7e2b337e0a97426aaed763 |
| /root/finance/section_map.py | b05b0f08ad65519675e21c9a6f4e90a0 | 9bf9b98fbfe64276b46c0a56ee9719e0 |
| /root/finance/spine/spine_build.py | 1378c87de2f8d4b3796cd92c7ca50d8d | ce99bedf60194a84fe93455927a336e2 |
| /root/marg_ingest/marg_take.py | 75b8056cc43ad6f3034ea1fa819ed7a8 | 21e37b0e6fa6505a8825b32b7c24d41d |
| /root/finance/finance_app.py (clinic — unit line + guarded mount only) | d7ee72c51564a397f4e847e98eb80ddc | 186a500a862a7f77da45e1e39b504f2e |
| /root/portal/portal.py (clinic — the tile only) | 592ccf99d02c361d4d5eb580995599c3 | 4a5b505e0274e37ab576fa0bc7852420 |
| /root/portal/tile_grants.json (clinic — v26 → v27, one grant + note) | 9231cefad0897a64aa127ce4a448f4fe | 9e3124e02fd79d3e1ef01e52bdc5cc76 |

New files: `/root/finance/item_alias.py` 5168c3c05df63a674a8dcab59f74365f · `/root/finance/stockmatch.py` d37c674b6b7435966f048503c40622df ·
`/root/finance/stockmatch.html` c5db7067fc18cf9a6bd29c48f4c1540d. Every FROM pin matched the brief when read live at 05:33 IST; the
built files were produced on the box by `make_s404.py` from the live bytes (anchored edits, each anchor exactly once) and matched the kit's TO pins.

### Backups made
`/root/finance/finance.db.bak_S404_20260926_061718` (sqlite backup API) · `.bak_S404_<from8>` beside each of the nine files:
`stock_app.py.bak_S404_1b473fbf`, `stock_hub.html.bak_S404_c4f3280b`, `stock_amir.html.bak_S404_14024b8d`, `section_map.py.bak_S404_b05b0f08`,
`spine/spine_build.py.bak_S404_1378c87d`, `marg_ingest/marg_take.py.bak_S404_75b8056c`, `finance_app.py.bak_S404_d7ee72c5`,
`portal/portal.py.bak_S404_592ccf99`, `portal/tile_grants.json.bak_S404_9231cefa`.

### Services restarted · health
`clinic-finance` and `clinic-portal` only (both active). `/finance/healthz` 200; `/finance/stockmatch` 302 and the hub 302 to a plain curl
(login gate, expected); the journal shows no "NOT mounted" and no traceback (only gunicorn's SIGTERM lines from the restart). Public probes
at 06:25 IST: healthz 200, stockmatch 302, hub 302.

### Data changes (seed, INSERT-only)
`business_unit` +1 (`stockmatch`, 'Stock milaan') · `unit_role` +2 (darpan maker, manoj checker) · `marg_item_rename` +22 (the S268 v2 list,
longest new name 29, no collision at 20/27/29 across the 373 count names — re-proved by the seed). Read back on the live database at 06:25 IST:
`stock_match` still 2 rows (the owner's two NOs), `stock_voucher_line` 0, the 31 orthotic `stock_diff` causes all UNEXPLAINED, `stock_item_section`
373, no alias row, no W404 row, no `stock_section_close` table yet (created on first read of the hub) — the walk's writes stayed on the scratch copy.

### The walk (walk_s404.py, on a scratch copy; the real round 1; pairs and lines found by the names the API returns; crafted rows keyed W404*)
`WALK_S404 GREEN -- 65/65`. In short: unit/gate (darpan 200, manoj 200, bhati/shavez/amir/alisha/stranger 302; hub still refuses darpan/bhati/
shavez) · Darpan sees 9 orthotic pairs and 22 open orthotic lines of round 1, no medicine leaks · his Haan on ANKLE BINDER BAMBOO L / ANKLE BINDER
L TYNOR lands a `stock_match` row by_user darpan, the hub shows it YES (Darpan) with the swap vouchers ISSUE+RECEIVE at once, the report shows the
swap on both lines; a second Haan 409 · the owner's NO on the next pair is greyed and locked for him (409) · a reason chip stores once (one audit
row), the same chip again = already (no write), a different chip within 10 minutes = his correction, an unknown reason 400, a surplus chip on a
shortage 400, the owner's change through the same door locks the line for him · progress counts; all done → *Sab ho gaya — ab Amir ke vouchers*
and the orthotic round made itself (3 lines, all Orthotics; the 29 pending medicine lines untouched); a second make = nothing waiting; a Medicines
round on request carries medicines only · Amir's entered tick on both orthotic batches · the 22 seeded exactly; a tick follows into the section
map (new name → Orthotics, source rename), the item spine (kind alias on the old item), the S229 rename task (closed); undo/re-tick · a ticked
rename maps a crafted sale line (20-char clip `KNEE SUPPORT XL HING`), purchase line (27) and stock row onto the OLD item in item life, reconcile
and the feed reader; an unticked one maps nothing · verification: the first export with the new name and not the old marks verified_at + md5;
two exports without it → amber on Amir's board and the hub; the `/api/snapshot` door verifies by itself; marg_take's door on a real archived
closing export (STOCK_CLOSING_TOTALS as on 25-09, captured 26-09 04:58): an export from before the tick counts for nothing, after a tick it counts
one sighting; a verified rename cannot be unticked · the spine reads a ticked rename as an alias new→old at the 20-char clip · the verdict stayed
OPEN through each of the four conditions and flipped CLOSED (stored once, same date on re-read) only when the last one held; Hindi on Darpan's page.
Full output: the installer's log (kept in this session), lines 19–96.

### Negative controls (the box as it was, its own scratch copy)
No Stock milaan page (404), unit medical, nothing mounted, no `match_answer`; the old hub has no `ortho`, the old Amir board no `renames`; the old
cause door refuses DONT_KNOW (400); the old make ignores `{section: Orthotics}` and vouchers Medicines and Orthotics together (31 lines); the old
reconcile does not see a new-name snapshot; no alias helpers. **S400's walk re-run: 63/63 green; S402's walk re-run: 16/16 green.**

### What I did NOT do, and why
- `sale_bill.py` — not touched: it keeps bill money only, no item name, nothing to alias.
- `finance_ingest.py` — not touched: it does not write the sale lines; `finance_returns.py` does (`sale_line_item`), which the brief does not name.
  The alias is therefore applied where the count/stock lanes READ the sale, purchase and stock rows (stock_app), which is what the brief asks for
  ("resolves to the row keyed by old_name for the count and stock lanes"). The raw stores keep the new name as Marg prints it.
- `spine/marg_read.py` — not touched: it reads files and keys nothing; marg_take now uses its `read_file()` for the closing export.
- `pad_receipt.py` — not needed.
- The spine was not built from this kit (clinic hours); the alias applies from its next scheduled run (every 10 min 08–23 and nightly, own lock).
- Nothing was answered, ticked or vouchered on the live round — that is Darpan's, Amir's and the owner's to do.

### Outside the brief, noticed (not changed)
- The old orthotic names are already ambiguous at 20 characters TODAY: the sale lanes count 0 sales for e.g. KNEE SUPPORT HINGED XL because the
  36 sale lines sit under the clipped key `KNEE SUPPORT HINGED`. That is the fault the renames fix; nothing in this kit re-attributes past sales.
- `marg_task` holds 24 S229-era rename rows with older spellings (e.g. `L S BELT L CONT GRAY UNISON`, a 30-character `KNEE SUPPORT XXL HINGED
  UNISON`, and `LINTIDE 145 MCG`); a tick on the S268 list closes the matching task by old name so Amir's salt page stops asking for the same rename.
  `KNEE IMMOBILISER UNISON M` and `LINTIDE 145 MCG 1*1` are on that S229 list but not on the owner's 22 — left open, untouched.
- The proof (D543) needs a day where our computed feed's `pur_to` reaches the export day; the last such live day is before 23-Sep (the 23–25 Sep
  expected feeds carry pur_to=22-09). Not a fault of this kit, but the section's proof will wait for the purchase export to catch up.
- Marg's closing exports arriving through marg_take are the TOTALS variant; the spine's reader identifies and reads them (378 items, as on the
  previous day) — the rename verification uses that door and the PC's push_snapshot door both.

### Kit
`deploy_kits\S404_ORTHO_STOCK_CLOSE\` — item_alias.py, stockmatch.py, stockmatch.html, seed_s404.py, make_s404.py, walk_s404.py,
install_S404_ORTHO_STOCK_CLOSE.sh, README.md, KIT_ID.txt, SUMS.md5. Ran from a copy at `/tmp/s404kit/S404_ORTHO_STOCK_CLOSE` (md5sum -c OK
before the run); the repository copy is byte-identical (SUMS verified on the box after `git pull`). No `__pycache__`/`.pyc` in the kit.
The NO_PHONE_NUMBERS gate: clean. Build lock `/root/deploy/.claude_code_build.lock` held 06:07–publish, then removed.

### Undo (if the owner says so)
Put back the nine `.bak_S404_<from8>` files, remove `item_alias.py`, `stockmatch.py`, `stockmatch.html`, `systemctl restart clinic-finance
clinic-portal`, healthz 200, read the md5s back. The seeded rows (unit, roles, 22 renames) are data and harmless; `finance.db.bak_S404_20260926_061718`
is used only if the owner asks for the data change to be reversed.
