# S224_STOCK_ANCHOR_FIX — the spot count gets its bill anchor

**The owner, 04-Sep-2026 (urgent, verbatim):** *"IN VAAPSI PAGE, THE STOCK CHECK SECTION DOES NOT HAVE ANY LAST SALE BILL NUMBER ENTRY BOX, PLEASE FIX IT. CHECK THE PWA FOR ALL STAFF ALSO."*

## Root cause — read from the page's own code first
The "stock check section" of the Vaapsi page is the third group of the S221 **jaankari** card, heading **गिनती करनी है** — `returns_desk.html`, `jkSpot()` (live L516–L525) and `jkCount()` (L560–L567). It renders one number box per flagged item and posts `{kind:'spot', answer:'counted', value}` to `/api/jaankari/answer` (`returns_desk.py` L959–L990), which stores it. **No bill anchor anywhere** — the page never asked, the server never required. Introduced by **S221_JAANKARI (03-Sep-2026)**, which built the D365 spot list as a *question* rather than a *count*; the counting page (`stock_check_live.html` L150, S207) and `stock_app.py /api/count` (L686–L690) have required the last sale bill since S208. Parked at the S223 open as `S223_PARKED_SPOTCOUNT_HAS_NO_ANCHOR`; un-parked by this order.

Not (a) the count page hiding the input for a role — it is unconditional for checker/maker/viewer; not (c) an S222/S223 change — S222 left `returns_desk.html` byte-identical (6d98e1b0); not (d) a JS error — the page runs clean in jsdom.

## The fix — two files, the smallest change
* `returns_desk.html` (page): `jkAnchorBox()` — ONE box under the spot heading, Hindi label **आख़िरी सेल बिल नंबर (Marg)**, placeholder `A003195`, the why-line in Hindi; `jkCount()` refuses without it (focus + Hindi line, nothing posted), upper-cases it, sends `anchor_bill`, keeps it across the list re-render.
* `returns_desk.py` (server): `_con()` adds `jaankari_answer.anchor_bill TEXT` once (PRAGMA then ALTER, the V8_COLS pattern); `/api/jaankari/answer` refuses `spot`+`counted` without an anchor — 400 `anchor_required`, Hindi message; stores the anchor in its own column; `_rd_answers()` reads it back.
* Server-side refusal in `stock_app.py` untouched (pin 4e929d0b stays).

## Provenance (F-299)
Live bytes reproduced from the repo chain, each link md5-checked: `returns_desk.py` afc8b0d0 → 1dc1fd62 → **3296eca0**; `returns_desk.html` 32c4b8cc → **6d98e1b0**. Patchers applied to those; the kit's full files are the result. `selftest_anchor_s224.py` re-proves it.

## Evidence
* `RENDER_TEST_anchor_s224.py` — **99/99**: Flask + jsdom (node 22) running the page's own JS for darpan, shavez, alisha, shivani, amir, manoj: anchor present and Hindi-labelled; "गिन लिया" refused without it; accepted with it; the row carries the anchor; the server refuses without the page; the counting page's `#bill` present for every login and `Start counting` disabled at load; `stock /api/count` without `bill_no` → 400 for every login. Amir refused at the desk in Hindi (F-296). *jsdom, not chromium — the PC has no browser runtime; stated honestly.*
* `selftest_anchor_s224.py` — **22/22**. `EVIDENCE_selftest_S214_rerun_s224.txt` — the standing S214 desk selftest on the new file, **44/44**.

## Install
`INSTALL.txt` — one paste; guards both live prefixes, backs up, copies, restarts `clinic-finance.service`, self-rolls-back.
