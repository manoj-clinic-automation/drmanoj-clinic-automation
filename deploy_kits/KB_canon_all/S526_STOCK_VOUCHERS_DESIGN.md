# S526 — STOCK VOUCHERS FROM MARG'S OWN REPORTS — the design for the next Sanjeevni build (26-Nov-2026)

*Written at the S526 close (the Sanjeevni chat, Opus 5.5, EOS-light, no code changed). His words are quoted from the chat; every figure below was measured this session on the two real exports and the 26-Nov nightly database copy (read in the device VM only, D656). No person's name is in this paper.*

## 1 · What he asked (D1083, D1084)

- **13:00 —** "any stock vouchers etc or unexplained stk movements shd be clearly flagged in stk and item ledger pages" (with the Stock check narration: short tags, not sentences).
- **13:39 —** "taken by Marg / not taken by Marg ... seem confusing — we have the stk voucher number and date of voucher frm export?" The answer was no: until now Marg sent no voucher list; a correction was read as "done" only from Marg's closing stock moving, a guess shown as a fact (F-1693).
- **14:49 —** registers item by item are "a very cumbersome method ... I select the period and only the stock vouchers with their items get generated as a report." **Decision (D1084): stock vouchers are read from Marg's two period reports — Stock Issue and Stock Receive — not from one-item Stock Registers.** The one-item Stock Register (S837) stays only as a fallback.
- **The look he saw and did not object to:** mock-up v3 `https://claude.ai/artifact/W3U9BfeW9K5QKpsgZ6YoqF` (copy `03_WORKING_PAPERS\S526\S526_STOCKCHECK_MOCK_v3.html`). He did not say "ok" to the screen itself — **show him the screen again, now fed by the reports, before building it (his rule).**

## 2 · The two Marg reports (how he takes them)

Marg (medical PC): **Transactions › Stock Issue › Modify** → Alt+P → Report/Challan = **Report** → **Detail+Items** → the period → text. The same from **Transactions › Stock Receive › Modify** (proven 15:47 26-Nov). Both land as `C:\Users\Public\MARG\17476\report.txt` (and a `user_*.txt` twin) on the medical PC. Today the medical PC's text reader does not know them: the census `marg_text_census.txt` (Drive `FromMedical`) says **NOT TAKEN: not a report the reader knows** — correct, fail-closed; nothing reached the server.

## 3 · The layout (both reports, measured)

```
                    STOCK ISSUE FROM 01-10-2026 TO 26-11-2026          (or STOCK RECEIVE FROM ...)
------------------------------------------------------------------------------------------------
 CHALLAN NO. PARTY NAME                 GROSS AMOUNT TRADE DIS.  CR/DR  PACKING  FREIGHT  SALES TAX  OTHER ± BILL VALUE
------------------------------------------------------------------------------------------------
04-10-2026                                                   <- a date line sets the day of the vouchers under it
 L000001     .CASH                 4302.00  0.00 ... 4302.00 <- voucher head: number, party, 8 money columns
             ANKLE BINDER M BAMBOO    1   (qty) ITE  344.00  688.00     <- item line, at column 13
             BIO D3 MAX               1*15  18262008A  3:4 CAP Apr-29  442.40  1445.17
                                                                ( 49 CAP )   <- total units of the line above
...  Continued..2 / SANJEEVNI MEDICOS / <title> Page No..2 / Stock Issue (or Stock Receive) / dashes   <- page break
TOTAL   108064.41   1385.94   0.00 ...   106678.00
*** End of Report ***
```

- **Voucher numbers:** issues `L000001` … (one letter + 6 digits); receives `AD00001` … (two letters + 5 digits).
- **Party:** `.CASH` or `CASH (.CASH)` for Amir's corrections; **2 issue vouchers (L000018, L000033) carry a person's name** → the reader keeps only "cash / named party", never the name (as S837's register reader never reads the Patient column). The issue report therefore follows the medical PC's patient rule: read name-free at the door.
- **Item line:** name (Marg's cut, up to 24 characters; the receive report sometimes 15 — `KNEE IMMOBILIZE`), packing (`1*10`, `1*10.`, `1*15`, `2ML`, `75GM`, `5GM`, `VAIL`, `200ML.`, `2.3ML`, `1`), batch (may be empty), quantity (`3:4` strips:tabs, `5`, `2:1+0:4` / `1:0+0:2` with a free part), unit (may be empty), expiry `Mon-YY` (may be empty), rate, value, sometimes a GST column (`5.00`, `0.00+5.00`).
- **Units:** strips:tabs × pack, the free part added; the `( N UNIT )` line under it is Marg's own total — the witness.
- **Witness (both reports, proven):** the item values add up to the report's gross TOTAL — issue 181 lines = 108,064.41; receive 73 lines = 38,535.38; vouchers' bill values = 106,678.00 / 38,955.00.
- **The parser that proved it:** `03_WORKING_PAPERS\S526\parse_stock_vouchers_s526.py` (md5 e41590891ab7ddbc0d2da03ba505f7d4) — name-free, 0 unread lines on both. The two exports: `user_ab2305943413.txt` (issue, md5 49b9b0f4; holds two names — stays on the PC) and `S526_STOCK_RECEIVE_01-10_to_26-11.txt` (md5 6c5e24a5). **Never into the repository or the cloud workspace.**

## 4 · What the two reports showed (01-10 → 26-11, against the 26-Nov database)

- **37 issue vouchers (L000001–L000038; L000005 missing — deleted in Marg), 16 receive vouchers (AD00001–AD00016).**
- **Everything the system asked is in Marg** — the 06-Sep count's vouchers (04-10 orthotics, 15-10 medicines: AXIMAL 200 = L000008, 15-10, 28:6 — also proven by the one-item Stock Register 14:39), FOLITRAX / OSTOVAXL L000030 (18-10), ZIBON EXTRA / GEMCAL XT L000037 (22-11, the S894 asks), and the wrong-batch fixes of the Expiry watch (`stock_batch_fix`, asked 01-11 → 21-11) as issue + receive pairs L000032–36 / AD00011–15, L000038 / AD00016 — **except KT ROS DT 6:11** (asked 15-10 as "voucher 14"; L000014 holds five other items; his "done" taps 18-10 and 19-11 left nothing) and VINBACTUM DS (his word: ignore).
- **Keyed twice (F-1691):** PRETOL 8 13 tabs (L000033 + L000034, AD00012 + AD00013), DISPERZYME CD 1, GEN D3 NANO 1, PEMZOLE D 1, TRAMATEE P 38 against 26 asked — each extra issue has its matching extra receive, so Marg's item totals are unchanged but its **batch** figures are off; ROSIKA: 10 issued from plain ROSIKA, 12 received into ROSIKA FORTE — possibly the wrong item.
- **Amir's own, nobody asked (F-1692):** 25-10 — L000031 (KNEE SUPPORT L, CAST SHOE L issued) and AD00010 (KNEE IMMOBILIZER ×2, CAST SHOE M, ENZOMAC ointment ×2, **NORTIMER TAB 9:0 received**). The NORTIMER receive most likely explains its gap (he took NORTIMER out of the count on 12-10; Marg 6:2 against Darpan's 0:2 on 23-11) — **his to decide; nothing told to Amir yet.**
- **Who keyed them:** all by Amir (his word 15:43).

## 5 · The build (one kit, Sanjeevni's own files — the FROMs read from the newest bundle first, F-472)

1. **The medical PC's text reader** (`marg_txt.py`, by Drive `ToMedical\_kit`, the md5 allow-list) learns the two titles `STOCK ISSUE FROM` / `STOCK RECEIVE FROM`; the issue report is sent **name-free** (the party cell blanked to `cash` / `party` on the PC) or, if the reader cannot blank it, withheld as today. Read the live `marg_txt.py` bytes first.
2. **The server's door** (`/root/marg_ingest/`): a new kind (e.g. `STOCK_VOUCHERS`), read by a new name-free reader into two tables — one row per voucher (number, day, kind issue/receive, cash/party flag, value) and one per line (item, packing, pack, batch, units, rate, value); the witness (lines = TOTAL) or the file is stored as *not read*; a later report of an overlapping period replaces those days' rows (never doubles).
3. **The judge:** every voucher line matched to what the system asked — `stock_voucher_line` + `stock_voucher_entered` (the count rounds), `amir_job` (taps), `stock_batch_fix` (wrong batches) — by Marg's item name (exact, then the 20-letter cut, then the word set; the orthotic renames) and units. States: **asked and in Marg (voucher no. · date)** · **asked, not in Marg** (after the period covers Amir's tap) · **in Marg, nobody asked** · **keyed twice** (more than asked, or a second identical pair). A batch fix is an issue + receive pair, judged as a pair.
4. **The pages (mock-up v3, shown to him again first):** the Stock check's two boxes — *Marg's stock changed — nobody asked* and *Corrections asked of Amir* (Waiting on Amir · In Marg: Issue L000008 · 15-10) — short tags in the item list; the item ledger's voucher lines with their Marg number and date, amber / green / red. Plus **F-1690**: a one-item Stock Register he takes without an ask is shown too (today it is read into `mi_register` and shown nowhere).
5. **When the report is taken:** he chose to export it himself for a period ("I select the period"). The system asks for it on his own list only when something waits on it (a correction Amir tapped done; a change nobody asked) — never a new daily export (his 18-Nov rule: reduce exports).

## 6 · Open with him

- NORTIMER TAB — Amir's own receive of 9:0 on 25-10 against his 12-10 settlement (F-1692).
- KT ROS DT 6:11 — still on Amir's card as 7:11 (Darpan's 23-11 count).
- The doubled batch pairs (F-1691) — Amir's batch fix to be put right once the kit can show it.

*S526 · 26-Nov-2026 · the next Sanjeevni session builds §5 after his look at the screen.*
