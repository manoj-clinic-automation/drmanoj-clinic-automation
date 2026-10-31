# S688_XRAY_FILM_LOG — the X-ray film log

*The parent, session 372 · 31-Oct-2026 · on the owner's rulings, his mock-up "X-ray film log" (31-Oct), and his ruling of 20:23 IST:
the Fuji machine's screen shows the FILMS LEFT in the loaded box, per size — that figure is what is typed (no counter, no box tap).
Cold review rounds 1, 2, 3 and 4 folded in; the weekly film-stock tick retired (20:20 IST). Built on S687's TO bytes.*

## For the owner
Reception's *Aaj ka kaam* gets **X-ray film: machine mein kitni film bachi hain, likhiye (dono size)** each morning (Mon–Sat, from
1-Nov-2026) until both figures are saved; Shavez gets **X-ray film ginti: reception nahi hai to aap likhiye** from 11:00 if it is
still not saved. The morning page (Roman Hinglish, phone-first) says **"Machine ki screen par jitni film bachi dikh rahi hain, wahi
likhiye."**: one number per size, one Save, the Saved card. When a size's films left last under 10 days and no spare box is on the
shelf, Shavez's list (and your page and console) shows **8×10 film mangwaiye — 1 box** (or 11×14), with a WhatsApp button to the
films supplier. Your page:

```
https://followup.dr-manoj.in/finance/slips/film/log
```

It holds both sizes (films left, days left, spare boxes, the order), this month (days with a gap, mornings not counted), the
contacts, the film bills seen in the Scan App, the box loads the machine's figures showed, **correct, void or un-void any past
morning**, the counts saved, the settings (incl. the spare stock), and each X-ray's film size, films and "both sides on one film".
The X-ray list from 1-Oct (replaces the X-ray Excel; the old one is left alone) is `/finance/slips/film/list`. Both pages download
as Excel.

## The rulings, as built
- **The figure.** Films left per size, 0–150 (setting `box.films`). Staff are refused a figure above 150, and a figure **higher
  than the last count** unless that count was 20 or less (setting `load.max_left`) **and** "Haan, naya box lagaya gaya" is
  ticked — a typo one film up must never become a box load ("Pichhli ginti mein X film bachi thi — badhi kaise? Dr Manoj se
  confirm karaiye"). The owner may save either: above 150 with a note; a higher figure with the tick or a note. The old
  200-used rule is **removed** — with these two rules staff can never reach it. A figure that means **more films used than 3×
  the 30-day average AND more than 30** (a typo too low: 118 typed as 18) is not refused but asked once: staff tick **"Haan,
  machine par yahi dikh raha hai"** and Save (the typed figures come back in the fields; no average yet, no question). Films
  left = the newest figure. The count is to be taken before the first X-ray (the page says so).
- **Films used** between two counts: previous − today when today is not higher. When today is **higher**, a new box went in
  between: ONE automatic box load on that day, shown as **"naya box (machine se pata chala)"**, and used = previous + (150 − today).
  A missed morning is never typed later (the next count spans it, "joined to the next count"). A box load across more than 3
  uncounted days says **"check"** on your page (two boxes could have gone in). A **late count** (the day's FIRST staff save at
  or after 11:00, a stand-in after X-rays started — never the time of your correction, void or un-void) is shown with the next
  span as ONE — "der se ginti — do din milake" (yours: "late count — two days combined") — never as two misleading gaps. Until
  the next count comes, the newest late count reads **"der se ginti — kal ki ginti ke saath judegi"** to staff (no gap, not in
  the gap days, on the log, the morning page, the Saved card and the Excel); yours shows its figures with "late count — joins the
  next count".
- **Corrections.** The owner corrects, voids or un-voids any past morning: append-only (new rows, the old figure kept), audited
  with the old and the new figures. Used, box loads, the gap, the 30-day average and the spare stock are all worked out from the
  figures each time, so a correction moves every one of them.
- **Days left** = films left ÷ the 30-day average daily use (counts at least 3 days apart, else "too little data" and no line).
- **Spare boxes** per size from a **start day** (default the install day, set by the data step): the **opening spare boxes** you
  set + every box billed on or after the start day (a bill of N boxes counts N; no quantity read counts 1) − one per box load the
  figures show on or after it. Until you save the opening boxes of a size (a 0 typed counts as saved; saving other settings never
  sets them) your page says **"Opening boxes not set — set them so ordering is right"** and the order card says **"(Dr Manoj ne
  shuru ka stock abhi nahi bhara)"**. **Not floored**: below 0 shows **"N box ka bill abhi nahi aaya — pehle bill scan karaiye,
  phir order dekhiye"** (yours: "N box(es) loaded with no bill yet — scan the bill first, then see about the order"), and a
  later bill first pays for those boxes. **A bill read as more than 10 boxes** (setting `bill.max_boxes`; a sheet count read as
  boxes?) is HELD — not counted — and listed on your page under **FILM BILLS: CHECK QUANTITY** with one tap to confirm or a box
  to correct (append-only `xf_bill_qty`, audited). Bill dates only decide the start-day cut; a bill with no readable date uses
  its scan date.
- **The order line** (two duties, one per size, so the line names its size): days left < `order.days` (10) **and spare ≤ 0** — it
  errs toward asking. It clears as soon as a bill brings spare to 1, or the figure rises (a box load: films left back up). An Aaj
  line's text is fixed, so its help only points to the page — "Kholiye: 8×10 ka haal wahin likha hai — supplier ka WhatsApp
  button, aur koi bill abhi scan hona baaki ho to woh bhi." — and the order card on that page carries the live words (a bill owed,
  the opening boxes not set). A bill whose lines name no size is **size unknown** (the
  "small film" group holds 8×10 and 10×12): listed beside the order cards on your page with one tap each — **8×10 / 11×14 / not
  film** (audited) — and then counts in that size (or nowhere); the "11 x 14" group alone names its size. A film bill kept on a machine record that is ALSO on the desk counts once, on the desk (xray_costs' own
  match: the record's bill link; else the same supplier's first word, the same date, and the paper's total within 1 of the
  record's typed lines or its price).
- **The gap.** Per day, films used per size against the films on that day's PAID X-ray slips (series xp, state ok, paid
  cash/UPI). Shown to everyone who has the page, never with a reason asked.
- **Films per study.** `xf_study`, seeded once from the owner's words: 11×14 where his "(11 x 14)" tag or wrist / pelvis both hips /
  femur / frog-leg is named; Knee studies (K/S) two 8×10; a one-part "AP & Lateral" one 8×10; every other study **size not set**.
  **Side B** takes twice the study's films unless he marks it "both sides on one film"; a study whose name starts with "Both"
  never doubles.
- **The Scan App's film bills** are copied into `xf_purchase` whenever any film page loads (a bill rejected later is marked gone;
  a re-read size, date or box count is updated). Reception's morning page loads every morning, so the copy is at most a day old.
  **Scan App schema read (assets.db, mode=ro, never written):** `bills` (id, created_at, vendor, bill_date, subgroup, status, dup_of,
  total_amount), `bill_items` (bill_id, item_name, quantity), `xray_film_line` (id, asset_id, asset_created_at, size, boxes, amount,
  voided_at), `assets` (id, created_at, purchase_date, vendor, price, bill_id).
- **Contacts.** Seeded: Nigam, Jugnu Medicos (Fuji), films supplier, no number. Numbers live in the database only (F-185), never in
  a URL. +91 only before a ten-digit mobile (6–9); any other number dialled as typed (a leading 0 or 1800 kept), no WhatsApp button.
- **Retired: "X-ray film ka stock giniye (dono size)"** (Reception's weekly tick; the owner, 20:20 IST: the machine shows the films
  loaded). Taken off Reception's panel in the seed and out of the duties file; the data step takes it off any SAVED panel and
  records where it was, so a red install puts it back exactly. Its `duty_tick` history rows are kept.

## Who reaches what
`/finance/slips/film/...` is unit **slips** by `_unit_for_path`: shavez, alisha, shivani the Hinglish pages; manoj and Dr Bhawna the
English pages — only **manoj** changes contacts, settings, film sizes or past counts. Other slips logins (awdhesh, bhati, sukhveer)
403 inside the module; darpan and any login with no slips row 302 at the gate. The shared login `reception` has no slips row.

## What changes — four files (`make_s688.py`, 6 counted edits, each anchor found exactly once; a refusal exits 1, nothing written)
| live file | from → to | what |
|---|---|---|
| `/root/finance/finance_app.py` | 9ce1b67f → 2f604fee | ONE inserted mount block (`xray_film`), after S687's |
| `/root/finance/aaj_duties.json` | 0adf1a84 → c5c80c37 | four `extra` duties (kind sql, xf_* only); the weekly film-stock tick taken out |
| `/root/finance/aaj_seed.py` | 73b8556a → dc7050d5 | Shavez's three lines, Reception's one, on; the weekly film-stock line off |
| `/root/finance/xray_film.py` | NEW → c08a1016 | the pages and the eight `xf_*` tables (made on the first request) |

**Before anything is placed:** the three FROM pins, S687's `month_jobs.py` (33fa557f, read only), the duty map (78b5f07e), S687's
walk (8a5a9a09, run on these files), then a database backup `finance.db.bak_S688_<stamp>`, mode 600.
**Data step** (`cfg_s688.py`, idempotent): the `xf_*` tables and the spare stock's start day (every list unread 0 from the first
minute, F-1024); where a panel is SAVED for shavez or reception, the new lines appended switched on (a line the owner took off stays
off); the retired weekly line taken off every saved panel. It records what it did; **a red after placing takes the added lines off
and puts the retired line back where it was**, with the four files. **Intended writes to existing tables:** `audit_log`, `aaj_cfg`.
Never written: slip, slip_item, owner_service, duty_tick, DUTY_MAP.json, /root/assetapp/*, month_jobs.py.

## Proof (device VM, a copy of the 31-Oct database and a MADE-UP assets.db with the asset app's real schema — no copy of the real assets.db exists; never the cloud workspace, D656)
- `walk_s688.py`, the REAL finance app: **114 of 114 green** — 60 S688 checks (incl. 300 random histories, some bills held, on
  which the order duty's SQL and the module agree on films left, the average, the spare stock and the line), S687's own walk on
  these files, 9 builder checks, 5 list checks (every other Aaj line and console line unchanged, the retired tick gone), **39
  mutants caught**
  (WALK_JOBS=2 at a time). Made-up figures and slips are dated March 2027, so a live copy's own November never mixes in.
- **Control** on the S687 files: `57 S688 check(s) red . 3 green`. The walk on the placed files: `61 of 61 green`.
- `rehearse_s688.sh` on a made-up root: DRY · forced red at [8/9] · journal red · saved panels + red (panels back exactly, the
  retired line in its place) · changed duty map refused · install · ALREADY INSTALLED · changed live file refused.

## Install
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s688kit && cp -rp /root/deploy/repo/deploy_kits/S688_XRAY_FILM_LOG /tmp/s688kit && bash /tmp/s688kit/install_S688_XRAY_FILM_LOG.sh`
(`DRY=1` before `bash`: every gate, the rebuild, the walk and the control; nothing written.)

## Undo
`\cp -p /root/finance/finance_app.py.bak_S688_9ce1b67f /root/finance/finance_app.py && \cp -p /root/finance/aaj_duties.json.bak_S688_0adf1a84 /root/finance/aaj_duties.json && \cp -p /root/finance/aaj_seed.py.bak_S688_73b8556a /root/finance/aaj_seed.py && rm -f /root/finance/xray_film.py && systemctl restart clinic-finance`
(The `xf_*` tables stay; nothing reads them after the undo. A saved panel the data step changed keeps its new lines — they read
as unknown once the files are back; the one-line undo does not reverse the panel step, a red install does.)
