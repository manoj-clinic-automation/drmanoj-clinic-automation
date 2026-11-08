# S750_MONTH_END — kit 4, the month end (Sanjeevni session 406, 08-Nov-2026)

**D849 · F-1175 · the plan `S406_KIT4_MONTH_END_PLAN.md` · the mock https://claude.ai/artifact/G7giUj7RrbiJAv2w8kHwvb approved 09:45 IST with the owner's words: *summary*, not *statement*; our statement is never sent to the dealers routinely — it is kept as the dealer ledger, monthly reconciliation built in, months and item lines collapsed and expandable, item quantities by month and by financial year.**

## What changes on the screens

- **Reception's scan screen** (`/scanapp/intake`, the pharmacy lane): a second button beside *CHALLAN HAI?* — **📋 DEALER KA MAHINE KA HISAAB (SUMMARY) HAI?** A scan saved with it lands as `kind='Summary'`, `doc_kind='summary'` (the challan's own road), so the register never takes it for a bill scan. The slip: *SUMMARY — dealer ka mahine ka hisaab liya. Doctor sahab ki list par chala gaya.* A summary and a challan on one scan: the challan wins. The clinic lane ignores the tick.
- **The reader** (`claude_reader.read_summary`): a Summary is read with its own prompt — the dealer, the period, every bill line (number · date · amount), credit notes and payments, the printed totals — into `claude_reading` as `doc_kind='summary'`; the bills row gets the dealer's name, the period's last day and the figure, no items. Sarvam never reads a summary.
- **Your step view, row 7 — Dealer summaries** (`/finance/purchase/page/check`): one line per dealer of the month in your columns (dealer · the summary's figure, scanned, scan, what, whose · next), the summary folded (*Show summary*: its lines beside Marg's bills). *Agrees ✓* when the summary = Marg's bills less Marg's purchase returns, to the rupee. *Summary ₹X more/less than Marg* with the *why* bill by bill: a bill on the summary we do not have · a bill in Marg the summary does not list · an amount only the dealer has wrong · a credit note (matched to Marg's purchase return or to row 6's pending return). A difference rows 2 or 6 already carry says *Nothing for you here*. An unexplained one is **yours**: *Ask the dealer* (waits, *asked dd-Mon*) · *Carry to <next month>* (the amount shows under next month's *Carried in*) · *Accept the dealer's figure* (the figure stands on the sheet; Amir's card asks him to enter the bill when its paper comes). *Awaited*: *Ask reception to scan it* · *<Dealer> gives no summary* (a standing word from that month on). A summary that could not be read: *Ask reception to rescan*. A summary naming no dealer of the month: *Pick the dealer*. An owner-confirmed dealer: your Confirm on row 3 counts. Every answer with Undo, audited; *Your answers* listed under the row.
- **Row 8 — Lock & NEFT**: *opens when rows 2–7 are clear and Marg's re-export after the last correction is in*; *Holding:* names the dealers' holds; the D849 line.
- **The payment sheet**: the column **Dealer's summary** (the figure · *agrees* / *differs · yours* / *differs · rows 2/6* / *awaited* / *none given* / *accepted* / *carried* / *your Confirm*). **Payable follows the dealer's figure** when the line agrees or you accepted it; an amount you carried shows under next month's *Carried in* (*carried by you (row 7)*) when nothing was typed there. Your typed values are never rewritten. The NEFT total and the bank advice follow Payable as before.
- **The dealer ledger** (`/finance/purchase/page/ledger`, `/page/ledger/<dealer>`; you and the senders): the financial year first (April–March: purchases, returns, payable, paid, balance; **items × quantity** for the year), then one month per fold (newest open): *Reconciliation: purchases − returns (+ carried in) = payable · paid · balance*, the dealer's summary and its verdict with the paper, *Paid:* the NEFT with the bank's reference / the cheques / what was typed, the bills (each a fold with its item lines: item, batch, qty, rate, net), *Items this month*. *Print* opens every fold. From row 7, the sheet and the hub.
- **Amir's page**: one card for a bill you accepted from a summary that Marg does not carry — *Dealer ke hisaab par yeh bill hai, Marg mein nahi — kaagaz aane par Marg mein entry karein*; it leaves when Marg carries the bill.
- **Aaj ka bill kaam**: *Dealer ka hisaab (summary) scan karo · N* — *<Dealer> ka <month> ka hisaab (summary) scan karo* / *… ko dobara scan karo*, the scan link (lane Pharmacy, the dealer filled in) and the one instruction (press the summary button). The card leaves when the scan comes.

## The files (FROM → TO in `TO_PINS.md5`)

`finance/scan_register.py` (S750 section: `s750_summary_scans`, `_s750_dealer_of`, `s750_answers`, `s750_carried_in`, `s750_dealers`, `_s750_explain`, `s750_open`, `s750_lock_reasons`, the wrappers of `s749_month_open` / `s749_lock_reasons` / `s749_rows`, `s750_answer_put`, `s750_undo`, `s750_dealer_pick`, `s750_reception_asks`, `s750_amir_enter`, `s750_sheet`; tables `s750_answer`, `s750_dealer_of`) · `finance/purchase_app.py` (`_pay_rows`, `_pay_sheet_table`, `_s749_hub_scan_card` wrapped; `s750_ledger`, the two ledger pages, the three doors `/api/s750/answer|undo|dealer_of` — the doctor only) · `finance/amir_day.py` (`state`, `_card_rows` wrapped) · `finance/porders_s454.py` (`s736_model`, `billkaam_page` wrapped) · **the Scan App's** `assetapp/asset_register.py` (the anchored edits in `make_s750.py`: the signature, both call sites, the kind on the pharmacy lane, the button and its JS, the hidden field, the slip, the two kind whitelists; the section wraps `_s550_claude`) and `assetapp/claude_reader.py` (`SUMMARY_PROMPT`, `clean_summary`, `read_summary`, `summary_to_bill`) — PLANNED on `board/_numbers` v1066, the Scan App chat told at the close.

**The lock gate** needs no new wrapper: S749's `_lock_gate` reads `s749_lock_reasons`, which S750 wraps — one line per hold, never twice. `s749_month_open` keeps every key (the parent's `month_read.py` reads it) and gains `dealers` / `dealer_words`; `open` and `words` carry the dealers.

## Proof

- `walk_s750.py` (S749's fixture, extended: five made-up summaries — one agrees, one agrees through Marg's purchase return, one with a bill we do not have, one naming no dealer, one unread; the answers and their Undo; the sheet, the ledger, reception's list, Amir's card; a stranger, Amir and Shavez refused the doors) — **green on the rebuilt files**; **CONTROL on the live files: 82 of 82 S750 checks red.**
- `walk_s750_app.py` (the real scan app on a made-up empty database; the reader's HTTP call replaced): **green**; control on the live files: 15 of 15 red (three S750 checks are true on the live files too: a challan wins, the clinic lane ignores the tick, the reader off sends nothing).
- The earlier kits' walks on the rebuilt files: S749's shows two counting lines only (the dealers now count in the strip — allowed in the installer); S740, S738, S736, S726, S711: no red beyond the live files' own.
- `proof_s750.py` on a copy of the 08-Nov database by the live files and by the kit's: 2 counted months · 33 dealer lines (21 October awaited, 12 November *month running*) · no summary scanned yet · **payable changed 0** (nothing moves on the sheet until you answer) · 27 ledgers read in ~1 s.
- The installer rehearsed on a made-up root with stubs (`rehearse_s750.sh`): DRY · placed and DONE · the two tables made · ALREADY INSTALLED · a forced red at [7/8] restored the six FROM files.
- A cold review until SAFE (its findings in the build brief).

## The install (his one line, after his publish)

```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s750kit && cp -rp /root/deploy/repo/deploy_kits/S750_MONTH_END /tmp/s750kit && bash /tmp/s750kit/install_S750_MONTH_END.sh
```

No DRY line is required by F-1153 (nothing live is re-paired or re-stated — the kit adds two empty tables and reads), but `DRY=1` before `bash` prints every gate and the proof without writing.

## Named limits

- Row 7 waits for every dealer of a counted month **that has ended** until a summary is scanned or you mark the dealer *gives no summary* (once, standing). The running month reads *Month running — the summary comes after the month ends*; nothing is awaited and nothing holds for it (the owner, 11:30 IST). On the day of the install October shows 21 dealers awaited: the lock is held by them until you have marked the dealers who never send one.
- The summary's month is its period's last day; when the reader read no period, reception's confirmed month; else the month before the scan day.
- A summary's figure is its bills less its credit notes when lines were read; else the printed total of bills; else the closing less the opening. An opening balance (an earlier month unpaid) is shown, not compared.
- The dealer is matched by the intake's vendor, then the reading's name against Marg's supplier keys, learned spellings and aliases; when none fits, you pick (kept in `s750_dealer_of`).
- *Accept* records the dealer's figure for the month; it does not create a Marg bill — Amir enters it when the paper comes, and his card leaves when Marg carries it.
- The ledger's *paid*: what was typed on the sheet; else the NEFT when the month's bank SMS came (the month's payable, for a NEFT dealer); else the cheques recorded. A month paid partly by hand and not typed shows a balance until it is typed.
- The reception card names the dealer in Roman letters as Marg spells it (title case).
