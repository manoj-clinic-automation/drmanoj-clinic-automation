# S837_STOCK_REGISTER_ONE_ITEM — Marg's Stock Register for one item (built at Sanjeevni session 463, 14-Nov-2026; fixed at 468)

**What it does (the owner's "Mockup is good" of 20:28 IST on `s463_stock_register_mock_v1.html`, with his word: keep it with me, a switch for
Shavez starting OFF, a flow from the portal in more than one way — D989; the rules A-D56):**
- **Asking.** From any section A row of the Marg watch (*Ask Marg's Stock Register — ITEM, d to d*: the day before the move to its closing), or
  from his own list `https://followup.dr-manoj.in/finance/sanjeevni/marg-watch/take` (any item, any days up to 92). New kind `REGISTER` in
  `marg_watch_report`, one added column `item`.
- **Kept with him.** The ask shows on his list page, on the Sanjeevni Hub's **Needs-you** (group *Marg & bank details*, opening the list) and
  on the Hub's **Go to** (*Marg reports for you to take — Stock Register*, with a count), and in the Marg watch's *Reports asked for* strip.
  The Hub's count and Needs-you line only READ (no table change, no closing, no rollback on the Hub's connection); the Marg watch's
  five-minute tick closes the asks that have come.
- **Shavez's switch** (`mwr.reg_shavez`, **OFF** to start; a button on the list page and on the strip). ON: the ask also shows on his *Aaj ki
  reports* (a Hindi card, read only); his owner's Needs-you line then waits a day. Turn him on once Ram Singh has added Stock Register to
  his REPORT login in Marg. No duty-map change.
- **The door reads it name-free.** NEW `/root/marg_ingest/marg_register.py`, called by `marg_take.take()` and `marg_ingest.run()` for a
  VERIFIED `STOCK_ITEM_LEDGER` before the file is deleted (S186, unchanged): one row per item (`mi_register`) and per entry
  (`mi_register_line`: day, number, kind, batch, quantity, value, balance, and the balance step not explained by the entry). The Patient and
  Doctor columns are never read. Witness: every balance = the previous ± the entry, and Marg's Received / Issued footers = the rows (`ok`).
  A row with only a date sets the day of the entries under it; Issue Return comes in, Receive Return goes out. Only the TEXT layout is read;
  any other is stored as *not read*, with the reason; a failed re-read leaves none of an earlier read's lines.
- **On the row.** An ask closes itself only when a SOUND register (its own footers agree, `ok = 1`) covering its item and days is in. The
  register shows inside a counted row as a table (date, entry, in, out, balance; the move's days marked), with Marg's word under it. A
  voucher-type entry only Marg holds (not sale / purchase / their returns), equal to the move in PROVEN units, takes the row out of the
  count — it then sits under *Explained after all › An entry only in Marg's Stock Register* with that note (the note, not the table). A
  balance that moved with no entry stays counted: *No entry in Marg either*, with Marg's proof.
- **Never settled by a guess (F-1423, the cold review of the first build):** a pack of more than one whose units Marg's balance does not
  prove (strips or loose) settles nothing — never taken as 1 (M1); a register whose own footers disagree is shown but settles nothing and
  closes no ask — he may ask again (M2); an item is the same item only by its exact name, or by Marg's 20-letter cut where exactly one item
  the stock record knows carries it (M3).
- **"Explained" is the Marg watch's own view.** The Expiry watch, the section count and `owner_notice` read `marg_hand_change` as before and
  still see such a row as open; they do not read the register (S1).

**Files** (rebuilt on the box from the live bytes by `make_s837.py`, checked against `TO_PINS.md5`):
| file | from | to |
|---|---|---|
| `/root/finance/marg_billwatch.py` | 960b5309 (S815) | 9edda626 |
| `/root/finance/reports_tile.py` | 163a869a (S815) | c0aed54f |
| `/root/finance/sanjeevni_approvals.py` | ae29e2bc | cd5174d6 |
| `/root/finance/finance_ui/finance_approvals.html` | 82f459ef | 9f629585 |
| `/root/marg_ingest/marg_take.py` | 5cad2d24 | bc621caf |
| `/root/marg_ingest/marg_ingest.py` | 828c4dad | b11099ff |
| `/root/marg_ingest/marg_register.py` | NEW | f411da07 |

**Proof (device VM; the database copy never left it):** the 14-Nov bundle and database copy (live pins = the S463 pin list). `walk_s837.py`
70/70 on the real Stock Register of 05-Oct (its kinds Purchase, Sale Return, Sale; footers agree; the patient and doctor cells never read)
and 70/70 on a made-up one (`mkreg_s837.py`, stdlib .xlsx, used on the box — no real file is ever kept there); its controls red (one quantity
changed by one unit; no title; another item's register; days not covered; a voucher of other units; M1 an unproven pack; M2 footers that
disagree; M3 two names agreeing in 20 letters, a suffixed name); the first build (S463) goes red on S3, S4, M1, M2, M3 (42/51); the control
on the live files red. `walk_s815` 60/60, `walk_s814` 44/44, `walk_s803` GREEN, `reports_tile --selftest` 55/55 on the built files.
`walk_s812` needs the box's spine: the installer runs it — as a REGRESSION check since S468 (the first install, 22:05 IST 14-Nov, stopped itself there at 60/61, nothing installed): that walk holds frozen expectations of the mid-November stock data, so it runs on the live files and on the rebuilt ones, each on its own copies, and stops the install only when a check that passes on the live files fails on the rebuilt ones, when the two runs differ in their number of checks, or when either does not finish; a frozen check red on both is named on screen. `rehearse_s837.sh` 15/15 (PART A: dry, install, the switch, again, `undo_s837.sh` with an open ask and Shavez ON, install again; PART B: a red at [4/7] and [5/7], his list page answering 404 after the restart, drift, a corrupt kit, the lock; PART C: the S812 walk judged against the live files — the same red on both installs, a red only on the rebuilt stops, a walk that does not finish stops).

**Install:** the owner's publish, then one server line (in the installer's head). `DRY=1` first runs every gate and walk and writes nothing.
**Undo:** the installer's line [6/7] — `bash /root/deploy/repo/deploy_kits/S837_STOCK_REGISTER_ONE_ITEM/undo_s837.sh`: the six backups back
(each checked against its FROM pin first), the new reader removed, every open Stock Register ask closed ('S837 undone' — the older Marg
watch would show them on Shavez's sale card), clinic-finance restarted. Installing again after an undo works with Shavez's switch either way.

**Reviews:** the first build NOT SAFE (S463, F-1423: M1–M3, S1–S6 — all fixed above). The second cold review (S468, the installer read in
full) SAFE TO INSTALL; its should-fixes taken: a full name of exactly 20 letters is never its longer sibling; the "Arrived" list shows sound
registers only; the known-names list no longer cut at 3,000; the undo closes open asks (`undo_s837.sh`); Shavez ON accepted on a reinstall;
after the restart the installer checks his list page is mounted (not 404); a copy failure while laying out the walk says so. Not taken:
proving the factor for a pack of one — a pack of one has one unit, and a wrong unit there already shows as balance steps and footers that
disagree, which settle nothing (M2).
