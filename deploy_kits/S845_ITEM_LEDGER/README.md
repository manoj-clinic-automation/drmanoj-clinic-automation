# S845_ITEM_LEDGER — the Item ledger (16-Nov-2026, Sanjeevni session 470; D992)

**What he asked (16-Nov, 07:54–09:46 IST; "ok" on mock-up v2, https://claude.ai/artifact/Sp2SJZtrNrX6P5RzNHZXLi):** a search box that opens an
item's ledger, its latest stock, every sale / purchase / return against its bill number and every voucher against its number, the purchase's
scanned bill inline, scanned bills not yet in Marg with their read lines and the expected stock, the full ledger and a date range, and the
stock discrepancies flagged — so that he need not open Marg's item ledger every time.

**The page** `https://followup.dr-manoj.in/finance/sanjeevni/ledger` — the doctor only (checker). From the Hub's **Go to**: a search box at the
top of the panel and the link "Item ledger" under Stock & expiry. **Read only: it writes no table, no setting, no file.**
- **Search:** 2 letters or more of a name, the stock record's items (starting with the letters first); one item holding them opens straight.
- **Marg stock** (the latest closing) · **Expected stock** (Marg + what arrived and is not in Marg yet) · **Needs a look** (the Marg watch's counted moves).
- **Arrived — not yet in Marg:** the Purchase bills page's own list of scans waiting for their Marg bill (`provisional_s781.provisional`, this
  month and last — one list, never a second), the scan inline and its read lines. A line is this item only by the order tracker's own matcher
  (`order_track.match_lines`); it is added to the expected stock only when its units are proven from Marg's own purchase lines (M1: an unproven
  factor is never taken as 1); a scan "probably already in Marg" is shown, never added.
- **The ledger**, newest day first: sale / sale return / purchase / purchase return against the bill number (the stock record's own lines);
  Amir's stock vouchers against their Marg voucher number (the spine's own rule for a filed voucher). Each day opens on Marg's closing of the
  day before, runs through the day to the expected closing, beside Marg's own. A purchase row opens its paper (`/api/bill`: the Purchase bills
  page's own parts — the scan, its lines beside Marg's).
- **The flags — one rule:** a red day is the Marg watch's own counted move (`marg_hand_change`, read through its own readers), with its own
  "Ask Marg's Stock Register" button (the existing door `/finance/sanjeevni/marg-watch/api/register/ask`). Explained moves are green; one he
  closed is grey. A bill Marg keyed late reads "had not taken in bill N yet" and, later, "took in bill N at this closing" — never red. Any other
  difference reads amber ("not counted by the Marg watch"); before 16-Oct, grey.
- **Last 30 days · Full ledger** (from the stock record's opening) **· Date range**; one totals line for the period; "Only days that need a look".

**Files:** NEW `/root/finance/item_ledger.py` · `/root/finance/sanjeevni_approvals.py` cd5174d6 → TO (one fail-soft block mounting it) ·
`/root/finance/finance_ui/finance_approvals.html` 9f629585 → TO (Go to: the box and the link). The two live files are rebuilt on the box from
their live bytes (`make_s845.py`, every anchor once, FROM pins first).

**Proof.** v1.0 on the device VM (the 16-Nov bundle and database copy; a stock record built on the bench from Marg's real exports,
`D:\Downloads\margsync\MargArchive`, 404 readings, gate green): `walk_s845.py` 42/42 over every item that moved in 30 days (173) — each day
opens where the day before ended and adds up; the period ends on Marg's closing; sales equal the record's own lines; every bill number is a bill
Marg reported; the red days equal the Marg watch's counted moves; every filed voucher on its item with its number; the 25 busiest full ledgers;
arrivals; every page 200; the doctor only; nothing written. `--control` red; the live files red; `walk_s803` GREEN on the rebuilt Hub;
`rehearse_s845.sh` 12/12 (dry, install, again, undo, install; red at [4/6], not mounted, drift, corrupt kit, lock, a foreign file).
**v1.1 / v1.2** (the two cold reviews, while the device VM was down from ~10:4x IST 16-Nov). First review: a counted move on a day with no
closing of the item is red (M1); a key whose members differ in strip size reads plain units, the search the same (S2); the Marg watch's rows
read once per page; the scan opener guarded; owed bills by identity and trimmed; the search a form; stale suggestions dropped; q capped.
Second review: the Marg watch's own walk gets a COPY of the database (it opens it read-only anyway); the walk builds the Hub with its OWN
init and asserts the four doors are mounted; after the restart the installer also reads the service's log for "item_ledger NOT mounted"
(the healthz door answers 302 to an anonymous call either way); the walk on the box (`--box`) holds no check of frozen data (any item,
any counts; F-1427); the walk reads with sqlite3.Row as production does and never imports from the kit folder (so the control on the live
files is red at the import); undo checks the live files are at S845's TO pins and takes the build lock; an interruption while placing
restores; the app gets 60 s to start; a paired scan preferred when two bills share a number; the suggestion list ranks before formatting.
**Proof of v1.2:** `synth_s845.py` 19/19 (made-up data); `walk_s845.py --box` 45/45 on made-up databases, `--control` red, the live files red;
`rehearse_s845.sh` 16/16 on a stand built from the 16-Nov bundle with made-up databases (A1–A5; B1 red at [4/6], B2 not mounted, B3 drift,
B4 corrupt kit, B5 lock, B6 a foreign file, B7 the log says not mounted, B8 undo after a later kit refused, B9 interrupted while placing —
the Marg watch's walk stubbed on the stand; it ran GREEN on the real schema on the VM for the same two built files). **The real-data walk
of v1.2 runs on the server as the installer's step [3/6]** on copies of the live databases, and stops before anything is placed on any
red. Number gate clean; none ignored. Known limit (S3): Amir's vouchers are matched by the 20-letter key and the record's aliases, not the
record's date-aware rename split — the sizes of one family share one key today, so nothing is misplaced.

**Install:** the owner's publish, then the one server line in the installer's head. `DRY=1` first runs every gate and walk and writes nothing.
**Undo:** `bash /root/deploy/repo/deploy_kits/S845_ITEM_LEDGER/undo_s845.sh` — the two backups back (checked against their FROM pins), the page
removed, clinic-finance restarted.
