# S642_EXPIRY_WATCH_R2 — S638 again, its walk corrected (F-1020)

**Why a second number:** S638's install (his server line, 22:41:51 IST 24-Oct, after his publish 91b008d1) stopped at [5/9] with NOTHING
placed: one walk check looked for the sentence "ki bikri report" on Shivani's Aaj ki reports page -- a line that shows only while a morning
report is still due; tonight every report was in. The check now asserts the page itself (its heading, not the refusal page). The twelve TO
files are S638's, byte for byte (the same `TO_PINS.md5`); S638's folder is frozen (F-512). Everything below is S638's README, with the
install line and the walk's file name changed.

# (S638) the expiry, dump and stock-out watch (D771 / D777 / D780), with F-1008, F-1009, F-1014, F-1015 and D778

**Project:** Sanjeevni (session 348, 24-Oct-2026). Built IN THE CHAT. The specification is `S340_BUILD_BRIEF.md` Part B plus
`S344_BUILD_BRIEF.md` Part B; the screens are the mock-up the owner approved, rev 3 (`03_WORKING_PAPERS\S348\S348_EXPIRY_WATCH_MOCKUP.html`;
his "yes", 21:47 IST, D780). Charter v1.1.

## What changes, for whom

- **The owner (English) — `https://followup.dr-manoj.in/finance/sanjeevni/expiry`** (a link on his approvals page, and every Needs-you line of
  it opens it): 1 Expired medicines · 2 Near expiry (by the day Marg stops selling the batch) · 3 Dump — no sale and no purchase in 60 days,
  Orthotics and Medicines as closed sections; in medicines the expiring-soon first, earliest first, `(mm/yy)` in amber, bold at 5 strips or
  more, grey under 1 strip, the rest `(mm/yy)` in blue; expired batches only in section 1 · 4 Wrong batch · 5 New products (the month open,
  earlier months folded; Amir's orthotic renames left out; "created in Marg" as a list) · 6 Out of stock — waiting / arrived again. Settings
  (the eight thresholds) at the foot. **Needs you:** "Expiry watch: N expired batches · M stop selling on 1-<Mon>", and after the 7th
  "<Month>'s Batch Stock not received yet".
- **Darpan — his order tab:** "In batches ko pehle bechein", grouped "1 Nov se band", "1 Dec se band": each medicine with its batch and stock.
  Nothing to tap.
- **Amir — his Marg sudhar card:** "Mahine ki report: Batch Stock (poora store) text mein save karein" with the eight steps (until the
  month's file is received); "Marg mein expiry write-off ya stockist ko return karein:" with each batch; "Marg mein in N dawaon ka batch
  theek karein" (folded list). None of them holds his day open.
- **Shivani:** "Aaj ki reports" on her home (D778), the same page and steps as Shavez.
- **Reception — "Order ka maal nahi aaya":** an order where nothing came names each medicine and its quantity (F-1015).
- **The owner's pay page:** an SMS-seen NEFT not yet confirmed shows "Seen in bank SMS — confirm and tell the suppliers"; his Needs-you OK on
  such a NEFT now also queues the suppliers' messages (F-1014).

## Files (FROM → TO; full md5s in `TO_PINS.md5`)

| file | FROM | TO | how |
|---|---|---|---|
| /root/finance/sanjeevni_approvals.py | 792f4a9a | bf86c8c8 | 4 anchored edits — the page, its settings POST, Needs-you |
| /root/finance/darpan_kal.py | 6159b75b | a64353c0 | 2 — the payload's `sell_first` |
| /root/finance/darpan_kal.html | 81dbb26a | b89ca3ad | 1 — `sellFirst(j)` at the top of the tab |
| /root/finance/amir_day.py | 2c99c29e | 3b7dae35 | 4 — `S.expiry` read once, card rows |
| /root/finance/porders_s454.py | 647f2925 | 673883e8 | 3 — F-1015 |
| /root/finance/supplier_msg.py | 4e3911a7 | f208d2b5 | 1 — F-1014, the pay card's button |
| /root/finance/bank_sms.py | aa527840 | 4ddbdd16 | 2 — F-1014, the OK queues (a final month with a NEFT portion only) |
| /root/finance/finance_ui/finance_approvals.html | b32da7ff | a7016a4e | 2 — a line's `href`; the link row |
| /root/finance/spine/near_expiry.py | 627a3915 | c12284f3 | replaced whole — the nightly runs the expiry watch (F-1009) |
| /root/finance/expiry_watch.py | NEW | fed23760 | the watch |
| /root/portal/tile_grants.json (**the parent's file**, a PLANNED line on the board) | 6498a916 | 11385907 | 3 — v38, Shivani's tile |
| /root/marg_ingest/signatures.json | 21604e0f | 50ca61f4 | 1 — BATCH_STOCK before the batch-wise STOCK_CLOSING (F-1008) |
| manojz `D:\Downloads\margsync\MargPull\signatures.json` | 21604e0f | 50ca61f4 | the same edit, placed on manojz after the server install |
| Drive `ToMedical\_kit\marg_txt.py` → medical PC `D:\SendToClinic\marg_txt.py` | e8a60d9d (S604) | 18fa8a83 | 5 — the reader takes the Batch Stock |
| Drive `ToMedical\_kit\KIT_MANIFEST.txt` | ddd0eadb | 48c6c1e1 | the reader's md5 on its line — kept here with LF (the repository pins .txt to LF); delivered to Drive with CRLF, which is 48c6c1e1 |

Read only (printed by the installer, not pinned): stock_figure.py, purchase_app.py, order_track.py, section_map.py, marg_take.py,
marg_router.py. Not touched: finance_app.py, portal.py, the crontab (the 23:57 line of S343 runs the new near_expiry.py), stock_figure.py.
finance.db gains two tables (`stock_expiry_run`, `stock_expiry_line`) and eight `expiry.*` settings, made by the first run.

## How

- **The reader (medical PC, F-1008).** Marg's Batch Stock prints the closing stock's title over the expiry report's column heads; it was
  refused ("a closing stock the reader cannot take", 23-Oct 05:10). The STOCK_EXPIRY spec now takes that whole-store title too. Every text
  taken before converts to the same bytes (the 23-Oct near-expiry and not-sold texts: c24ad142, d3ace983 — unchanged).
- **The door (F-1008).** `signatures.json` matches BATCH_STOCK before the batch-wise STOCK_CLOSING DEFAULT: the file is filed as
  `BATCH_STOCK_BATCHWISE__…`, never in STOCK_CLOSING (where it would also have triggered the closing's rename verification). The spine never
  used the batch-wise layout (`marg_read.identify`); push_snapshot's reader refuses it. A VERIFIED file already filed is never re-judged.
- **The watch.** Nightly: the newest Batch Stock that lists at least `expiry.whole_fraction` (0.9) of the items the newest closing holds in
  stock (a filtered batch print — Marg's batch-wise dump — is kept, never used, and said so); each batch lowered by the spine's own sale
  lines after its day (a sale beyond a batch, or with no batch, named the next day); the six sections from the spine (sales, purchases,
  closings) and finance.db (the order lines and carries, purchase_new_item, marg_item_rename, stock_item_section). Orthotics: the owner's
  sections first, then the shared word list for single pieces only (`section_map.is_orthotic` takes DYNAPAR QPS PLUS by "DYNA" — named, not
  changed). A batch that fills its 12 places runs into its expiry in Marg's print ("LGP11/244/0710/2027"); the reader splits it.
- **Proved on the real files of 23-Oct** (working papers, never in the repository): the Batch Stock reads 362 batches, 240 items, serials
  unbroken, units re-add to Marg's TOTAL 27,299 exactly (S340's 27,301 was a reading slip, not the file); 4 expired, 14 near (3 on 1-Nov, 7 on
  1-Dec, 4 on 1-Jan), 30 wrong-batch medicines — S340's figures; the batch-wise dump (122 items) is judged a filtered list.

## Install (the owner's one server line, after his publish)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S642_EXPIRY_WATCH_R2/install_S642_EXPIRY_WATCH_R2.sh
```

Gates → lock → pins → rebuilt from the box's bytes → walk NEW (green) + OLD (`--expect-red`) on copies → backups (files and finance.db) →
placed + read back → one restart of clinic-finance → healthz → the first pass (the nightly once) → lock released. Then, by the chat:
manojz's signatures.json, and the medical PC's reader through Drive (after the server, so a Batch Stock never meets the old signature).

**Undo:** the line the installer prints (the eleven `.bak_S642_<from8>` back, expiry_watch.py removed, one restart). The two tables and the
settings are inert without the code. Medical PC: `marg_txt_S604.py.superseded` and `KIT_MANIFEST_S604.txt.superseded` back on Drive.

## The walk

`walk_s642.py` — 45 checks, 28 controls, green on the new files; the negative control (`--expect-red`) red on every control on the old (25: the
watch's four rule checks are one control there, the module being absent). Its own
made-up Batch Stock (TEST letterhead) built from the spine's newest closing, converted by the kit's reader, taken by the scratch door; the
nightly run as cron runs it; every screen rendered through the real finance app as the owner, Darpan, Amir, Shivani and reception; the stock
figure of every item byte-identical before and after (the witness, 681 lines); the spine never written; F-1014 on its own SMS event (20
messages queued; a second OK adds none). A re-install after an undo stays a fair control (the walk clears the inert tables in its copy). The made-up file carries a page break, a
batch run into its expiry and a bottle item; on scratch copies of the spine the watch's rules are proved: a credit note puts its units
back on its batch; a batch Marg's closing shows written off leaves Amir's list (never asked twice); an oversold batch is named; after a
re-supply only Marg's printed minus counts. The witness is taken BEFORE the file reaches the door.

## The independent read (before placing)

A cold read by a separate agent (no part in the build) found 14 points; fixed: the SUMS gate; credit notes subtracted instead of added
back; a re-supply in the same batch drifting below zero; a batch already written off asked again (Amir's double write-off — now
dropped once Marg's closing shows it); the 31st's run read on the 1st (a near batch whose month has begun reads as expired); the export
card cleared by any file (now only a whole-shop export of the month, or one not yet judged); later stock-outs hidden behind the first
short; the owner's sections missed for punctuated names; the write held open during the run; the SMS-NEFT queue without neft_done's
guards (now a final month with a NEFT portion only, rolled back on error); the journal probe's case; the window re-checked before
placing; the first pass checked. Kept as the owner approved: strips:tabs ('3:2') on Darpan's and Amir's lines (his mock-up, D780).
Named, not changed: section_map.is_orthotic takes DYNAPAR QPS PLUS by "DYNA"; Shavez's monthly 'Stock expiry' export is no longer read
by anything (the old reader is retired) — the owner decides whether it leaves his list.

## Not in this kit (decided)

- **F-1016's permanent half** (a start-with-the-PC task for the medical agent) waits for Monday 26-Oct's read (booked in S344): the guard the
  owner enabled in "user" (15:35 24-Oct) stands by while SET's guard holds the lock; if it takes over once SET signs out, no task is needed.
- Shavez's copy of the Batch Stock card waits for Ram Singh's report button in his Marg login (Y143).
