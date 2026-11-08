# S754_SUMMARY_RECOGNISE — a dealer's month summary recognised by its content (08-Nov-2026, the Scan App chat's session 409)

**The owner's word (17:27 IST 08-Nov, from the Sanjeevni chat's S408; it supersedes D870's "staff rescan it"):** staff scan a dealer's month summary on the pharmacy lane like any bill — tick or no tick. The system recognises it.

**What went wrong today.** Of reception's thirteen summary scans, six missed the tick: B-0297 Mannat, B-0298 Gunina, B-0299 Deepam were filed as pharmacy bills; B-0291 Shraddha, B-0292 Drug Deals, B-0293 A.A. Pharmaceuticals went to the clinic lane as drafts on the desk. B-0296 (L.K. Drug House, no seller name printed) was joined to Janta's B-0295 as its "page 2" by the forgotten-page rule. B-0303 (Daanshi) was read with the buyer's name (Sanjeevni Medicos) and dated 02-11, so it counted under November.

## What changes — three files, one appended section each (nothing above the sections is edited, except two counted lines in scan_checks check 1)

- **`/root/assetapp/claude_reader.py`** (8e1ae6bf → ce3868ed): `read_pharmacy()` — the one Claude call a pharmacy-lane paper gets anyway, now with one more paragraph: decide first whether the paper is a dealer's statement (a heading such as statement / due list / sales book / ledger / transaction register / outstanding, a period or an "as on" date, several bill numbers each with a date and an amount, a total). A statement is answered in the summary shape, a bill in the bill shape. **No second call.** The summary reader (ticked papers too) now: the dealer is the SELLER on the letterhead, never Sanjeevni Medicos in any spelling (the S439 buyer rule, copied in) — null when no seller is printed; the period comes from the bills when it is missing, one day, or the "as on" date (then the first to last day of the month most bills fall in); a printed period is kept.
- **`/root/assetapp/asset_register.py`** (dfa0955c → 74043cdb): a pharmacy paper scanned **without** the tick is read by `read_pharmacy`; a statement lands exactly as a ticked summary (S750): kind **Summary**, doc_kind **summary**, audited `summary` *via recognised (S754)*, the row lent only the dealer, the period's last day and the figure. A bill stays a bill. **The tick still wins.** The clinic lane and the other lanes are untouched. The kind changes before the after-checks run, so the month, the double guard and the page rule see a Summary.
- **`/root/shared/scan_checks_s441.py`** (10787cbf → 59d5cb1c): the forgotten-page rule never joins a **complete statement** (a Summary, or a reading with two or more numbered bill lines and a total) to the scan before it. A page that only continues a statement's table (no heading, no seller, no buyer block) may still join — a Summary only. Everything else is judged as before. *(The finance app imports this file too but only reads questions; it loads the new file at its own next restart — nothing it calls changed.)*

## What a Summary looks like on the scan app's screens (spec item 7, S750's question answered)

- **All papers:** Kind *Summary*, lane Pharmacy, status *Filed*; the date is the period's last day (October's papers show the *late — belongs to 2026-10* badge, as Janta's B-0295 already does). The Kind filter has no *Summary* entry — choose *Kind: all* (as for challans).
- **The desk never opens it** (the pharmacy lane is not the desk's).
- **Re-lane — decided:** a paper read as a summary (doc_kind *summary*) that is on the pharmacy lane is **kind Summary**, whichever road put it there (the lane button, the desk's Save, a *Scan ka kaam* answer): healed after every POST, after every reading and at start — except a *recognised* paper a person moved after the recognition (the way back from a wrong recognition, below). Moved **off** the pharmacy lane it takes that lane's kind (it is then not a dealer's summary for Sanjeevni), but it is **never approved as spend** — Approve refuses doc_kind *summary* ("belongs on the Pharmacy lane"), as S560 refuses a receipt or a statement. The papers page's history rule (`clinic_papers.auto_home`) never moves a summary.

## The data step — today's eight papers (fix_s754.py, DRY first)

| paper | today | after |
|---|---|---|
| B-0297 Mannat · B-0298 Gunina · B-0299 Deepam | Pharmacy bills | kind Summary, re-read as a summary |
| B-0291 Shraddha · B-0292 Drug Deals · B-0293 A.A. Pharmaceuticals | clinic drafts on the desk | pharmacy lane, Filed (off the desk), kind Summary, re-read; B-0291's open lane question answered by the server |
| B-0296 L.K. Drug House | "page 2" of B-0295, set aside | unjoined, Filed, kind Summary, re-read; **B-0295 gets its own single file back** (S441 kept both originals) |
| B-0303 Daanshi | Summary with the buyer's name, November | re-read: dealer null or Daanshi, period October |

A re-read clears what the old bill reading lent the row (vendor, bill no, date, figure — kept in the `reread_summary` audit row) and fills it from the summary through the app's own reading. **Every paper is guarded**: id + stamp + scanned 08-Nov by Alisha + the vendor and amount as read on the screen + the state it was found in; it **refuses on any decision a person made** (an audit row by a person after the scan, a question answered by a person, a payment, a machine, a procedure-room line, stationery, a warranty, item lines, an outside paper pointing at it; on finance.db — read only — a link to a Marg bill, a person's pairing decision, s736 / s749 / s750 decisions; B-0303's dealer chosen on the Sanjeevni side is kept and wins). **Any refusal: nothing changed.** REAL backs up `assets.db` first (`assets.db.bak_S754_<stamp>` beside it), changes the rows in ONE transaction, one audit row each, then re-reads one by one. A re-read the reader could not finish is said so; **running the same line again carries on** (rows already right are skipped). finance.db is never written. Live read before the build (a read-only look at the nine pages, 19:1x IST): ids = the stamp numbers, no item lines, no person's decision shown.

## Proven

- **walk_s754.py** (the real app, a made-up database, the reader stubbed): every check green on the kit's files; **CONTROL on the live files: 21 red, all S754's**.
- **walk_fix_s754.py** (nine made-up papers shaped like today's): DRY writes nothing; REAL puts all nine right, backup made, finance.db untouched; a second REAL says ALREADY DONE; a re-read cut short after the row was cleared carries on; **eleven CONTROLS** (an amount off by ₹2, another scanner, another day, a person's move, a person's answer, an item line, B-0296 not a page, B-0295's file not the merged one, an outside double, a Marg link, a person's pairing decision) each **REFUSE with nothing changed and no backup**.
- Earlier kits' walks on the kit's files: **S750's walk_s750_app green** (the tick, the summary reader), **S651's walk_s651_app 15 green** (the S441 checks).
- **Rehearsed** (rehearse_s754.sh) on a made-up root with a stub reader: DRY (nothing written) · REAL (the TO pins placed, the nine rows right, a backup) · a second run (the code step skipped, ALREADY DONE) · a forced red at [6/7] (the FROM files back, no row changed).

**Cold review (independent, before placing): SAFE TO INSTALL**; its should-fixes built — a printed period kept (only a missing / one-day / "as on" period is taken from the bills); a person's move undoes a wrong recognition; the kind flip retried on a busy database and healed from the reading; Approve's guard after the login; a cut-short re-read carries on; B-0295's own file accepted as an upright copy; the data step's refusal no longer stops the code going in; the backup labelled for disaster recovery only. *Known, not built:* at start-up the papers page's own heal (`heal_auto`) runs before S754's guard is installed (a pharmacy summary's dealer is almost never all-clinic in history); a continued statement page whose head is still being read is judged once.

## The two lines (the owner's, after his publish)

The DRY first — paste its output (F-1153), then the real line:

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s754kit && cp -rp /root/deploy/repo/deploy_kits/S754_SUMMARY_RECOGNISE /tmp/s754kit && DRY=1 bash /tmp/s754kit/install_S754_SUMMARY_RECOGNISE.sh
```

```
bash /tmp/s754kit/install_S754_SUMMARY_RECOGNISE.sh
```

## The way back

- **The code:** the installer prints the one undo line (`\cp -p` each `.bak_S754_<old md5>` back, then `systemctl restart assetapp`).
- **Without an undo:** settings `read.summary_recognise` = `off` (the scan app's assets.db) — every pharmacy paper is read as a bill exactly as before.
- **The data:** every change is an audit row with its from / to (`relane`, `summary`, `s441_page_unjoined`, `s441_page_unmerged`, `reread_summary` with what the bill reading had lent) — a row is put back by hand from those. `assets.db.bak_S754_<stamp>` (named in the output) is for disaster recovery only: copying it back loses every scan made since.
- **A wrong recognition** (a real bill read as a statement): move the paper off the Pharmacy lane and back — a person's move is respected for a recognised paper; it stays *Pharmacy*. (A ticked summary is always kept a Summary on the Pharmacy lane.)

## For the Sanjeevni chat (keys of `claude_reading.data`, doc_kind 'summary')

Kept as they were: `is_summary, dealer, period_from, period_to, lines[{kind, no, date, amount}], total_bills, opening, closing` (+ S750's `doc_kind, handwritten, date_as_read`). **Added:** `continued` (a page that only continues a table), `as_on` (the printing / "as on" date), `period_by` (`paper` | `bills`), `period_from_as_read` / `period_to_as_read` (when the period was taken from the bills), `dealer_was_buyer` (true when the buyer's name was read and dropped), `recognised` (true when found without the tick). `dealer` is null when no seller is printed — S753's fallback finds it from the bills.

*Known, not built here:* `claude_reread.py` (the one-time bulk reader) still reads with the bill prompt; nobody runs it now. The slip shown at the Save cannot say "summary" for an untick paper (it is recognised seconds later).
