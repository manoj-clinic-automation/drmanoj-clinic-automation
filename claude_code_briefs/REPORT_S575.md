# REPORT_S575 — S575_BATTERY_SETUP (built, walked, rehearsed; not installed, not published)

**For Dr Manoj (plain English):**
- The battery setup kit is built and tested. It is ready in `deploy_kits\S575_BATTERY_SETUP\`. **Nothing on the server was changed.**
- Once installed, the **Batteries** page gets a **"First setup"** fold (yours only). It lists every place with no battery recorded yet,
  one line each: type the date the battery was fitted, choose the bill, and press Save. An old battery with no bill is
  **"Old battery — no bill"**. It never shows "bill awaited".
- "New battery fitted" takes any past date, up to 15 years back. To link an existing bill or warranty card, you can open **"Show older
  / other papers"** or type its stamp (B-0162, B162 …) in **"Find by stamp"**. Linking never moves or changes the paper.
- Each online UPS with no count shows **"How many batteries? — set"**. It opens that place's "Change this place". The list then reads
  "set of N".
- Every test is green, and every new test fails against today's file, as it must. Reception, the sorting desk and Shavez's screens are
  unchanged.

---

## For the chat

**Read first (07:29–07:31 IST, the runner's log starts 07:29:48):**
- The brief v2 whole, and `S575_BRIEF_R1.md` whole: md5 read `9905724981a369d517cb7029db7b54e0` = the brief's `99057249…`.
- `S571_BATTERIES.md` (v2), `S571_BRIEF_R1.md` (read later, 07:59, before the last round; nothing in it changed the build) and
  `REPORT_S571.md` with its fix round.
- The whole S571 kit (batteries.py, make, install, rehearse, walk, browser walk, README, KIT_ID, SUMS) and `KB_canon_all\BUILD_NORM_v1.md`.
- From the live box (copies in `_scratch` only): `sorting_desk._s566_stamp_form`, `_by_stamp`, `_visible`, and
  `asset_register.page()` / the flash layout.

### The FROM pins as read (07:30:43 IST, srv1746119 — S571 is installed)
| file | live | brief |
|---|---|---|
| `/root/assetapp/batteries.py` | `9a0054ac073ccaa1252b426c5a9d408f` | `9a0054ac` (S571's TO) |
| `/root/assetapp/sorting_desk.py` | `110335eac5a9792ebe52620ee676a13c` | `110335ea…` — read only, not edited |
| `/root/assetapp/asset_register.py` | `c39c084eabf52daa0da9cc6720fc7aa7` | `c39c084e…` — read only, not edited |
| read only: `clinic_papers.py 6db07c12` · `stationery.py d11d7183` · `asset_machine.py 7d4fdffc` · `scanner_widget.js 10a8bb29` · `claude_reader.py 3894dc23` · `claude_reread.py d9b75e78` · `/root/finance/packs.py e46264b8` | all as pinned | — |

These were read again at 07:58:10 and 08:04:50 IST, after every run, and were all unchanged. No `.bak_S575` file is in
`/root/assetapp`, there is no build lock, and assetapp is active.

At 07:30 the live database held 15 battery places, all seeded and unedited, with **0 fittings** and 0 upkeep rows. The three online UPS
have no count (counts only were read; no row content).

### The counted edits (`make_s575.py`, `batteries.py` only — 31 edits, each anchor exactly once on the live bytes)
| edit | carries |
|---|---|
| BT1 | the docstring |
| BT2 | the mark `SETUP = "S575"` (VERSION stays "S571", which S571's walk W2 needs), `NO_PAPER = "none:old-battery"`, `WIDE_LIMIT = 300`, `FLOOR_MONTHS = 180` |
| BT3 | the helpers after `fit_of_paper`: `no_paper` / `no_bill` (C1); `_wide_ok`, `wide_candidates`, `_pickable_wide` (C4/N5 — `dup_of`, `rejected`, `page_of`, the desk's `_visible`, `patient_paper`); `stamp_form` (through `sorting_desk._s566_stamp_form`, with the regex fallback) and `by_stamp` (the one refusal line, C5); `_choice` (stamp → wide → select; two different papers refused) |
| BT4 | `place_view`: the count `n = (cur.set_n if cur else None) or p.set_n`, `ask_n` for `grp == 'online_ups'`, "set of N" before a battery is recorded (C7) |
| BT5 | `place_view`: no `await` for an old battery with no bill — so no badge, no reminder and no `tot.awaited` (C1) |
| BT6 | `save_fit`: the date is required with `back=first`, never in the future, and not more than 15 years back (N4, C6) |
| BT7–BT9 | `save_fit`: `none` is handled before `_pickable`; the stamp, wide and select order; stored as `NULL` + the marker; the audit line has `no_bill` / `no_card` (C1/C4) |
| BT10 | `link_paper(…, stamp, wide)`: the stamp and wide paths; the 90-day wording unchanged on the usual path (C3/C4/C5) |
| BT11 | `desk_offer`: an old battery with no bill is not offered a paper (C1) |
| BT12 | the CSS |
| BT13 | the list row "How many batteries? — set" (owner only), linking `?edit=1#s571edit` (C7) |
| BT14 | the owner-only fold `#s571first` "First setup" (C6) |
| BT15 | `#s571links`: "Show older / other papers" with `paper_any` and `paper_stamp` (C3/C4) |
| BT16 | the history cells "no bill (old battery)" and "no card (old battery)" |
| BT17 | `#s571edit` opens on `edit=1` |
| BT18 | for an online UPS, "Batteries in the set" is the first field (the two later `set_n` fields are wrapped `{% if not online %}`) |
| BT19 | the B.L. form: "Old battery — no bill", plus a fold with `bill_any` and `bill_stamp` |
| BT20 | the Jasoria form: "Old battery — no bill" and "Old battery — no card" (C2), plus a fold with `bill_any`, `bill_stamp`, `card_any` and `card_stamp` |
| BT21 | `page_main`: the First setup lines, decided by `current_fit` (C6), each with its supplier's `candidates()` (N7) |
| BT22 | `page_place`: the history flags, the links box's wider list, `edit_open` |
| BT23 | `page_fit`: with `back=first`, both the save and the refusal go back to `/batteries?first=1#s571first`; the refusal names the place; "The one before is in the history." only when there was one |
| BT24 | `page_fit`: `online`, `wide` |
| BT25 | `post_link` passes `paper_stamp` / `paper_any` |

`candidates()` and `_pickable()` are byte-for-byte unchanged (C4). `sorting_desk.py` and `asset_register.py` needed no edit.

### The TO pin (rebuilt on the box from the live bytes; = `PIN_TO_batteries.txt`)
**`/root/assetapp/batteries.py` `9a0054ac` → `40eb8a916aee48ef5a49337d3c4cc81d`**. It compiles on `/usr/bin/python3` and
`/root/wa/venv/bin/python3`.

Two earlier rounds of this run were walked and rehearsed GREEN, then replaced:
- `edfb6cc8`: changed after a screenshot showed long place names pushing a First setup line out of column. The name column is now a
  fixed 240 px.
- `308db3f9`: changed because after a First setup save the message said "The one before is in the history." when there was none.

### The walk and the control (box, backup-API copy of the database, made-up rows only; final bytes, 07:59:50 IST and in the rehearsal 08:00–08:03)
**`walk_s575.py` on the TO file: 8 checks: 8 GREEN, 0 RED.** The walk adds its own nine places through "+ Add a battery place" and its own
papers. Each paper gets a stamp `B-9nnn` that no paper of the copy has. Everything is found by name, stamp or id, and totals are
compared before / after. Made-up today is 15-06-2031.
- **W1** imports from the scratch folder on the copy.
- **W2** `SETUP` = S575, and every S571…S551 mark is kept.
- **Z1 (structural)** S571's tables were already there; no new object, row or setting.
- **I1 (item 1)**
  - Both forms have "Old battery — no bill". The Jasoria form has "— no card"; the B.L. form has no card select.
  - The online UPS battery fitted 15-06-2024 (C8, seven years back) has `bill_id` NULL and the marker.
  - It shows no `await` and no bill reminder.
  - Till is 15-06-2025 and life 15-12-2026, the badge is "Due for replacement" and the reminders are life and upkeep (the warranty has
    passed, so it is not a reminder).
  - The B.L. bill awaited total went 0 → 1, counting only the walk's one awaited battery.
  - The history reads "no bill (old battery)", and the audit has `no_bill: true`.
  - The Jasoria battery with no bill and no card shows both words.
  - A date 16 years back is refused, with nothing saved. 14 years 11 months back saves.
  - A new B.L. paper on the desk is offered to the awaited UPS, and not to the old battery.
- **I2 (item 2)**
  - The usual picker does not have the old B.L. paper (90 days, unchanged).
  - "Show older / other papers" lists 40 papers for the owner and 39 for the manager:
    - the old B.L. paper, the other supplier's paper and the new paper are in it, newest first;
    - the Personal paper is listed for the owner only;
    - pharmacy, set-aside, second-scan and page papers are never listed;
    - the line reads `B-n · Other Supplier WALK575 two · 03-03-2029 · ₹6,100`.
  - Picked from the wider list on the fitted form → it is that battery's bill.
  - The old battery's bill was linked later by stamp, typed `B` + digits, through "The battery now — its papers". The marker is gone
    and the history shows the stamp.
  - The manager's stamp lookup for the Personal paper and for a stamp nobody has both give **the same line**, "No paper B-n that you
    may link here. Nothing was linked.". On JSON it is 400 with the same line.
  - The owner's stamp lookups for pharmacy, set-aside, second-scan, page and not-found papers give that line every time.
  - The owner linked the Personal paper as a card by `b` + digits; the card marker is gone.
  - Two pickers filled with different papers are refused: "Pick the paper in one place only." (link) and "Pick the bill in one place
    only." (form).
- **I5 (D664)** The three linked papers have lane, section and status unchanged — `clinic/None/draft` ×2, `owner_expense/personal/captured`
  — and every whole row is unchanged.
- **I3 (item 3)**
  - The online UPS row with no count asks "How many batteries? — set", with href `/batteries/place/<id>?edit=1#s571edit`.
  - The small UPS does not ask, and the manager's list does not ask.
  - `?edit=1` opens the edit form.
  - After setting 4 the row reads "set of 4" (no battery recorded yet) and no longer asks; the warranty is unchanged.
  - On the online UPS form, `set_n` comes before `fitted_on`.
- **I4 (item 4)**
  - The fold lists the three new places, but not the places that have a battery.
  - The first small UPS's badge is "Backup check due" and it is still listed (decided by `current_fit`, not the badge — C6).
  - Its line carries `back=first`, the supplier and warranty 12, and the date is `required`.
  - The manager has no fold.
  - An empty date is refused: "WALK575 First small UPS: Type the date this battery was fitted (dd-mm-yyyy). Nothing was saved." and
    no fitting is made.
  - **Three saved in a row** (302 ×3), each back to `/batteries?first=1#s571first`. The fold is then open and the three have left it.
  - The small UPS has warranty 12 (till 01-03-2024). The online UPS has set 6 and its bill was found by stamp.
  - The message speaks of "the one before" only on a second battery.

**Negative control on the live FROM file (`--expect-red`): 8 checks: 2 GREEN, 6 RED — "CONTROL must-be-red: W2, I1, I2, I3, I4, I5 --
all RED"; structural W1 GREEN, Z1 GREEN.**

### The earlier walks (the rehearsal's outcome 1, final bytes, 08:00:03–08:03:41 IST; also a DRY=1 run on the live paths at the first round)
| walk | result |
|---|---|
| **S571** | **12/12** |
| S568 | **14/14** |
| S566 | **12/12** |
| S563 | **17/17**, plus its tidy fetch (102 answers each side, **none differing**) |
| S560 | **37/37**, plus pack **9/9** |
| S548 | **8/8** |
| S559 | **43/43** |
| S557 | **41/41** |
| S555 | **19/19** |
| S551 | **87/87** |

Every count is as the brief and R1 N1 give them. The adapted lines are those S571 ran, nothing new, all in `/tmp` copies. **One call for
S571's walk:** it was written for a database *before* S571 — its Z1 counts S571's new tables and `batteries.since`, its I1 / I2 / I4
count the 15 seeded places and its own totals. So it is given its own scratch copy at S571's install-day shape:
- `s571_copy_s575.py` takes out S571's three tables and `batteries.since` on that copy only, and refuses any path outside `/tmp`;
- its mount makes them again;
- **no line of S571's walk was changed**;
- it stays green even after the owner has started recording real batteries.

### The browser walks (the PC's headless Chrome, 08:03:49–08:04:14 IST; pages rendered on the box from the final build, made-up rows)
- **New `walk/browser_batteries_s575.py`: 3/3 GREEN.**
  - **F1** the owner's page with First setup open, at 1366 × 768 (viewport 1342 × 669) and 1366 × 620. The four totals are on the
    first screen. Every row's "New battery fitted" and all 5 "How many batteries? — set" links are inside the width. 16/16 First setup
    lines have place, date (required), bill, stamp and Save on screen. Nothing is wider than the screen.
  - **F2** the three fitted forms at 1366 × 768. Every field outside the closed fold, and Save, is on one screen. The online UPS's first
    field is `set_n`. Opened, the folds' 2 / 2 / 4 fields are in reach, and Save is still in reach.
  - **F3** "The battery now — its papers" with the fold open: paper, paper_any, paper_stamp, as and Link are all inside the width.
  - **Its control** (the First setup lines forced to one 1900 px row): **F1 RED**, as it must be.
- **S571's browser walk** (R1 N2): **3/3 GREEN**, its control B1 RED. It ran through `lines_s575.py browser571` — one line, in a copy
  in `_scratch`: B3 measures the fields outside the closed fold, which by design have no size until opened. S575's F2 opens the fold
  and checks those fields.
  - A first run of it was RED on B2. The cause was the walk's made-up "Old Car" place, which was not marked "yours only", so it showed
    on the manager's page. The walk now adds it as owner-only, as every real vehicle is. This was not a product fault.
- **S560's desk layout: 7/7 GREEN** (S568's one line, nDest 16). **S568's staff screen: 2/2 GREEN.**

All are recorded in `walk/walk_results_s575.txt`. A screenshot of the First setup fold at 1366 × 768 was looked at, and it led to the
fixed name column.

### The rehearsal (made-up root `/tmp/s575reh/root`, final kit bytes, 08:00:03–08:03:41 IST) — `REHEARSAL GREEN`
| outcome | result |
|---|---|
| 1 | Green. `batteries.py` at `40eb8a91`, with `batteries.py.bak_S575_9a0054ac` beside it (the FROM bytes). The read-only files and packs.py were untouched. The database backup was taken, and **every row of all 38 tables, settings included, read back unchanged — no data step**. The lock was released, and the undo line names assetapp only. |
| 2 | ALREADY INSTALLED |
| 3 | forced red after placing → restored |
| 4 | `/desk` 404 → restored |
| 5 | `/desk` 200 → restored (302 only) |
| 6 | `/batteries` 404 → restored |
| 7 | `batteries.py` moved → REFUSED |
| 8 | `sorting_desk.py` moved → REFUSED |
| 9 | no `batteries.py` (S571 not installed) → REFUSED |
| 10 | `packs.py` moved → REFUSED |

The end guard is K2's: `*.py *.html` in `/root/finance` and `*.py *.js` in the live scan app, never a folder listing. It was unchanged.
The run was timed between two :35 `freshness.html` rewrites (see S571's report). The first two rounds (07:45:45–07:49:07 on
`edfb6cc8`, 07:52:50–07:56:15 on `308db3f9`) were also GREEN.

### Kit identity
- `deploy_kits\S575_BATTERY_SETUP\` holds 30 files: 29 plus `SUMS.md5`.
- The final 29 files were sent to `/tmp/s575dev/final` on the box: `md5sum -c SUMS.md5` gave **29 of 29 OK**.
- Every program file — make, walk, install, rehearse, `s571_copy`, lines, the browser walk and the two batteries PIN files — is
  `cmp`-identical to the bytes that walked and rehearsed.
- The kit has no `batteries.py` of its own: like S566, it rebuilds the file from the live bytes.

### Calls made where the brief left room (with reasons)
- **The fitted form's stamp refusal** ends "Nothing was saved." instead of "Nothing was linked." — the first sentence is the same one
  line. On that form it is the save that is refused. The link box gives C5's line exactly.
- **A number alone in "Find by stamp"** ("162") is read as B-0162, as the desk's own `_by_stamp` reads it.
- **First setup's bill choice** is Old battery — no bill (the default), the supplier's papers, or find by stamp, as item 4 lists. There
  is no "Bill awaited" in the fold; the full form keeps it. There is no card or warranty field in the fold: a Jasoria place's warranty
  months come from the place (empty until typed on the place or the full form).
- **"Batteries in the set" in First setup** is shown for the online UPS only (C6). Other places take their own count.
- **A First setup refusal names the place** ("WALK575 First small UPS: …"), since the fold holds many lines.
- **The database is still backed up** by the installer although there is no data step (CLAUDE.md rule 6). S571's `--ensure` line was
  dropped (R1 N3).
- **The wider list** is up to 300 papers, built at each form load. The Jasoria form lists it twice (bill and card).

### Not done, and why
- **Not installed, not published** — the brief overrides CLAUDE.md for this run. No live file was placed, no service restarted, no live
  row written, and no build lock taken. The rehearsal used a made-up lock path; the DRY=1 run used `/tmp/s575dev/lock`.
- **DUTY_MAP not changed.** This kit adds, moves or removes no staff duty: First setup and the count prompt are the owner's, and
  Shavez's view is unchanged. The walk signs in as both logins it affects (owner and manager) and checks the manager has no fold and no
  prompt.
- **N6 (as R1 says):** once an old battery is replaced, its bill can no longer be linked, because the papers box serves the battery in use
  only. Nothing more was built.
- **Cost:** the runner's own log, `D:\Downloads\_kbtools\agent_build\logs\S575_BATTERY_SETUP_20261018_0729.log` (started 07:29:48,
  "model opus · budget $40.00"), had no cost line when this report was written. The runner writes its DONE / cost line when the run
  ends, so read it there.

### Seen outside the brief (not touched)
- `/root/finance/purchase_app.py` is now `98f7d9f0`, not the `147201dd` S571's PIN held. It is Sanjeevni's and read only here: the
  installer only notes it, as S571's did, and S568's walk ran its query as it is now (14/14). Another kit moved it after 16-Oct.
- R1 N14 still stands: battery reminders, computed when read, do not reach the home dashboard's due list or `/api/due`.
- S572–S574 and S576 kits are in `deploy_kits\` on the box (other chats' builds). There was no build lock at any reading.
- **Box scratch cleared** (08:04:54 IST): `/tmp/s575dev`, `/tmp/s575reh`, `/tmp/s575probe` were removed by a script limited to
  `/tmp/s575*` paths whose parent is `/tmp`. **0 left.**
- **PC scratch left:** the rendered test pages in `_scratch\S575_BATTERY_SETUP\pages*`. The permission list refused deleting them, so
  they are left; the folder is git-ignored. The battery pages' "older papers" lists show real paper stamps, suppliers and amounts (no
  patient paper, no phone number). They are safe to delete.

### Gates (run last on the PC, finished 08:06:18 IST on the PC clock; re-run after this line was written, same words), over 32 files — the 30 kit files, this report and the brief
- `.gitignore` (last match wins): `git check-ignore -v --no-index --stdin` (GitHub Desktop's git) — **none ignored** (exit 1). There is no
  nested `.gitignore` and no `__pycache__` / `.pyc` in the kit.
- Contact-number gate: `NO_PHONE_NUMBERS.py --files-from`, run from a copy in `_scratch\S575_BATTERY_SETUP` (md5 = the repository's),
  printed **`NO_PHONE_NUMBERS: clean -- 32 staged file(s) checked (numbers and credentials).`**
- `SUMS.md5`: 29 of 29 OK on the box (`/tmp/s575dev/final`) and on the PC.

**nothing installed, nothing published.**
