# Claude Code brief — S452_AMIR_PANEL_FIXES (what the live walk of Amir's panel found on 02-Oct, and two rulings of the same evening: the "bills to put into Marg" list must hold only bills that are not in Marg; the reception phone's key must not be readable by a staff login; step 7's list in Roman Hindi; the voucher board in Roman Hindi with every duty on his card; NEFT shown to him as one line and a PDF, only once confirmed; medicine vouchers 12 a visit, more on request)

Written 02-Oct-2026 by the Sanjeevni chat (S283 post-close); §3.5 and §3.6 added the same evening at the owner's word, before any build. Read `CLAUDE.md` first. **Kit S452 · faults F-686, F-687** (System Board `_numbers`; D650 and D648 are the decisions it serves — no new one). Runs AFTER S446_AMIR_STAGES_BILLS (live 02-Oct 06:15 IST) and builds ON its files — read every FROM pin live. S438_COUNT_BOOK stays HELD. Staff pages Hindi (Roman), owner pages English.

**Touches (declared):** `/root/finance/purchase_app.py`, `amir_day.py`, `supplier_msg.py`, `stock_app.py`, `stock_amir.html` — all Sanjeevni's; **`packs.py` — THE PARENT'S, declared (PLANNED on the board): one anchored edit to Amir's NEFT route only (§3.5)**; `claude_code_briefs/DUTY_MAP.md` + `.json`. **READ ONLY:** the asset app's store (through `purchase_app`'s existing door), `porders.py`. Restarts `clinic-finance` only. **Not in this kit:** the medical PC's refusal note (its own kit, after 04-Oct, when the watcher's retry window for the two refused texts has passed).

## 1 · How this was found

The owner signed in as amir in the chat's browser on 02-Oct, 19:48 IST, and the chat walked every page, read only. S446 shows as built: the login lands on his day, every step carries only "Orthotic voucher baaki: 7", his board lists the 7 vouchers, the August pack opens, the 14 scan files download. Four things are wrong. The first is the brief's own fault — S446 built the list exactly as S446's brief described it.

The owner's ruling this serves (01-Oct): "The scanned medicine bills are simply made available to him at one place so he can upload them in the digital entry part of Marg … That will be the final entry of the bill."

**The owner's words of 02-Oct evening, after the walk (§3.5, §3.6):**

- "For the paid NEFT sheet, even a PDF is sufficient because he will not be able to modify it in any way. So change it to PDF."
- "Individually, we do not need to send him a list of each name and baaki … Remove this long detail from there. We can only say that the NEFT August 2026 bank work done on this date."
- "He gets the NEFT done line only after the bank SMS is read by the system or I personally enter the NEFT provisionally in the system. Before that, he does not get it and he does not get the sheet also, the vendor payment sheet."
- "He will enter the payments only when he sees the bank statement."
- "You had limited five vouchers to each visit. Make it 10, 12 vouchers for each visit so that the work is done quickly and it does not stall … He can optionally add and enter even more vouchers if he has time."

## 2 · What the chat read on the live pages — REPORT the same facts first

- **F-686 — the list invites double entry.** Step 2's "Marg mein daalne ke bill (14)" is every captured pharmacy scan with no row in `purchase_scan_link` (`scans_to_enter`, S446). That includes scans reception has not yet answered in *Scan ka kaam*: near-matches (*Yahi bill hai?*) and unread suppliers (*Supplier chuno*).
  - Five of the 14 show the shop's own name as the supplier: B-0054, B-0078, B-0079, B-0080, B-0082.
  - Five carry a year the bill cannot have: B-0033 (2024), B-0042 (2024), B-0048 (2025), B-0088 (2024), B-0100 (2023).
  - The download names repeat the misreads: `YUVIKA_SURGICALS_nobill_09-09-2026.pdf`, `BAAS_PLASMA_DISTRIBUTORS_PVT_LTD_GST202324412_20-05-2023.pdf`.
  - Most are September bills, and September's purchases are already keyed in Marg. A bill uploaded again into Marg's digital entry is a second purchase.
- **F-687 — a staff login reads the reception phone's key.** `/finance/purchase/page/phone-setup` answers 200 to amir, and the page carried the key on both opens the chat checked (the key itself was never printed). The route admits `checker`, `maker` and `viewer` (`supplier_msg.page_phone_setup`, S407), and its "shown once" rule did not hold: read live why (`supplier_msg.token_shown`), and say. With that key, `/finance/api/supplier-msg/next` hands out messages that carry full account numbers.
- **Step 7 lists what is left in English:** "bills not confirmed entered" · "Item-detail purchase report and Bill-wise purchase report not verified" · "salt and name list not ticked" · "count #1 stage A: 7 orthotic vouchers not entered in Marg". The last one sits among the reasons the day is open, though the code does not gate on it.
- **Two scripts.** His day is Roman Hindi. His board (`stock_amir.html`) is Devanagari.
- **A duty only inside the board:** "(b) Rate daalo" — FINGER COT SPILNT REMEDE and SOFT COLLAR BODY AID S need a selling rate in Marg. His card does not say so.
- **Small:** step 6 prints the heading "Marg sudhar" twice; the board's salt block still lists LINVIZ 600, already "Marg में हो गया".
- **The NEFT block at the foot of every step** (`supplier_msg`'s card, S407) reads "NEFT August 2026 · bheja 24-Sep-2026 — bank se confirm baaki" and then eighteen supplier names, each "baaki". The pack offers "Paid NEFT sheet (Excel)" (`/finance/amir/pack/2026-08/neft`, an .xlsx, served by `packs.py`).
- **Stage C** releases 5 medicine vouchers a visit (`amir.vouchers_per_visit` = 5, S446); 30 wait.

## 3 · The build

### 3.1 The list holds only bills that are not in Marg (F-686) — `purchase_app.py`, `amir_day.py`

- **A scan is listed only when the server finds no likely Marg bill for it and its supplier is known.** That is S440's *Marg ka intezaar* group, as `purchase_scan_state` holds it. A scan with a near-match, an unread supplier, the shop's own name as supplier, or an open amount question is NOT listed: it stays with reception's *Scan ka kaam* until answered.
- **One grey line under the list, no download:** "N scan abhi reception ki jaanch mein hain — Marg mein mat daaliye". N is the count held back.
- **Each listed line shows what is known, not what was guessed:** the stamp, the supplier (the chosen or matched name, else as read), "scan: dd-mm, <who>", and the bill date only when it lies within 60 days of the scan day. Otherwise: "bill ki tareekh scan par saaf nahi".
- **The download name starts with the stamp:** `B-0044_YOGENDRA_AGENCIES_<billno>_<dd-mm-yyyy>.pdf`. A bill number that is not read is left out (no "nobill"); a date outside the 60 days is replaced by the scan day.
- **A second guard at download:** if a Marg bill has arrived since the page was drawn that the matcher links to this scan, the download answers a small page instead — "Yeh bill Marg mein aa chuka hai" — and the line is gone on reload.
- The zip of today's follows the same rule. `scan_file_users` and the owner's access stay as they are.
- **The owner's Scan links page** gets one line: "Amir's list: N to enter · M held for reception".

### 3.2 The phone key (F-687) — `supplier_msg.py`

- **The setup page is for the owner and a checker.** A maker or viewer gets the login gate's refusal, as on any page that is not theirs.
- **The key is shown to the owner and to a checker**, each showing audited (who, when). A checker already sees the same account numbers on Vendor payments. The "shown once" setting is retired; say in the report why it did not hold.
- **A new key at install.** The old one was readable by a staff login, so it is replaced; the old key answers 401 from that moment. The phone's macro is not collecting today (REPORT_S446), so nothing working is broken.
- **The page says, in one Hindi line at the top, what state the phone is in:** when it last asked, with which answer (200 / 401), and how many messages wait.
- **Never print the key** in the walk output, the report or the repository.

### 3.3 Step 7 in Roman Hindi — `amir_day.py`

- Every line of "Abhi baaki" in Roman Hindi, the older three included. For example: "Bill daalne ki pushti baaki hai" · "Dono purchase report ki jaanch baaki hai" · "Salt aur naam ki list tick nahi hui" · "Ginti #1: 7 orthotic voucher Marg mein daalne baaki".
- The count's line is shown apart from the reasons the day is open, with "(din band karne se nahi rukta)". The same for the stage B and stage C lines and the salt-list line.
- The owner's own views keep English. Read which callers show `_s446_left` / `_s444_left` to whom, and give each its language.

### 3.4 The board in Roman Hindi; every duty on his card — `stock_amir.html`, `stock_app.py`, `amir_day.py`

- **Every fixed word of his board in Roman Hindi**, matching his day's wording: "Voucher — Marg mein daalne hain", "Marg mein daal diya", "Marg ka voucher number", "Marg se 3 nag → tak 1 nag", "Closing stock nikaaliye", "Server ko bhejo" and so on. Item names stay as Marg prints them. No Devanagari is left on the page he is served.
- **"Rate daalo" on his card while due:** "2 item ka rate Marg mein daalna hai — kholiye", opening the board at that block. Added to `DUTY_MAP` with its `due_sql`.
- **A salt line already done in Marg leaves the block.**
- **Step 6's heading once.**

### 3.5 NEFT for Amir: one line and a PDF, only once confirmed — `supplier_msg.py`, `amir_day.py`, `packs.py` (the parent's, one edit)

- **A month's NEFT is confirmed when either is true:** the bank's SMS for it has been read by the system, or the owner has entered the NEFT himself (his "NEFT done" entry with its date — provisional counts). Read live which rows carry each (S405 / S407) and state them in the report.
- **Before that, Amir sees nothing of that month's NEFT:** no line, and no vendor payment sheet in his pack. The pack's bank statements stay as they are.
- **Once confirmed, he sees one line and one file, nothing else:**
  - the owner's entry only: "NEFT August 2026 — payment 24-09 ko ho gaya (Doctor sahab ne darj kiya)";
  - the bank's SMS read: "NEFT August 2026 — bank ka kaam ho gaya, <dd-mm>";
  - the paid NEFT sheet as a **PDF** (same rows and totals as today's sheet), named `NEFT_paid_<yyyy-mm>.pdf`. The link reads "Paid NEFT sheet (PDF)".
- **The list of supplier names with "baaki" / "bata diya" is removed from his steps.** Shavez's and the owner's pages keep theirs.
- **Amir's NEFT route answers the PDF and obeys the same gate:** `/finance/amir/pack/<month>/neft` gives the PDF when confirmed and the login gate's refusal when not. He gets no .xlsx by any address. The accountant's pack and the owner's downloads are unchanged.
- **Today (state it in the report):** August was entered by the owner on 24-Sep and the bank's SMS has not been read, so Amir sees the first wording and the PDF.

### 3.6 Medicine vouchers: 12 a visit, more on request — `stock_app.py`, `amir_day.py`

- `amir.vouchers_per_visit` becomes **12** (the setting row is updated at install only if it still reads 5).
- Under the lot, one button: **"Aur voucher kholiye"**. It opens the next 12 at once, as often as he taps it, until none is left. Each tap is audited (who, when, how many).
- The order of D649 stays: nothing of Stage C before Stage B is verified.
- **The proof no longer holds the next lot back.** Every closing-stock export checks whatever he has entered so far and names any item still wrong, with its voucher. A lot left unverified stays listed; the next visit still opens 12 more.
- The card reads "Dawa voucher: aaj ke 12 (baaki 18) — kholiye". The owner's stage line counts entered, released and verified.

## 4 · Pins — S446's TO, read live

| file | pin |
|---|---|
| `purchase_app.py` | `176fc6ea` |
| `amir_day.py` | `cd8f4659` |
| `stock_app.py` | `ec6b1ce8` |
| `supplier_msg.py` | `02b4a9ed` (the 02-Oct bundle; read live) |
| `stock_amir.html` | `1ec8663d` (the 02-Oct bundle; read live) |
| `packs.py` (the parent's; one edit) | `6a1cf6ce` (read live) |

Not touched: `sanjeevni_approvals.py`, `darpan_kal.py`, `porders.py`, `portal.py`, `clinic_sso.py`, `tile_grants.json`, the crontab, the medical PC.

## 5 · Walk (scratch copies; rows keyed W452*; dates from today)

- **The list.**
  - On the box's own data: the listed count equals the *Marg ka intezaar* scans; none of B-0054, B-0078, B-0079, B-0080, B-0082 is listed; the grey line's N plus the listed count equals the 14 of today (or today's figure, stated).
  - A crafted near-match scan is held back; when reception answers "Nahi" it joins the list; when a Marg bill links it, it leaves.
  - A crafted scan with a 2023 bill date: the line says the date is not clear, and the file name carries the scan day.
  - Every download name starts with its stamp; none contains "nobill".
  - The download guard: a scan linked after the page was drawn answers "Marg mein aa chuka hai".
- **The key.**
  - amir, darpan and the reception login get the refusal on the setup page; the owner and a checker get 200.
  - The old key gets 401 on the queue door; the new one 200.
  - Each showing writes one audit row. The key string appears nowhere in the walk's output.
- **Step 7.** As amir: no English phrase from the old list ("not confirmed", "not verified", "not ticked", "not entered"); the count's line carries "din band karne se nahi rukta". As the owner: English kept.
- **The board.** As amir: no code point in the Devanagari block in the served page; the 7 vouchers, their boxes and buttons still work (one marked entered: 6 left). The rate line shows on the card while due, and goes when a crafted export carries the rates. Step 6 has one heading.
- **NEFT.**
  - A month with neither the owner's entry nor a bank SMS: no NEFT line on any step, no sheet in the pack, the route refuses amir.
  - The owner's entry only (today's August): the first wording, the PDF link; the file is a PDF (`%PDF`), its rows and total equal the old sheet's.
  - A crafted bank SMS read: the second wording with its date.
  - No supplier name and no "baaki" in the NEFT block on any of his seven steps. Shavez's and the owner's pages unchanged.
  - No address gives amir an .xlsx.
- **Stage C.** After a crafted verified Stage B: 12 on the board, "baaki 18"; one tap on "Aur voucher kholiye": 24; a third lot: 30 and the button gone; each tap one audit row. An export with one wrong item names it and does not stop the next lot. Nothing of Stage C shows before B is verified. The setting is 12; a box where the owner had set another figure keeps his.
- **Staff-eye walk** (CLAUDE.md, "Every duty has a door") for amir, shavez and the owner.
- **Earlier walks re-run:** S446 41/41 and S444, each adjustment named (the list's rule, the Roman strings, the setup page's roles, the lot of 12, the NEFT line); S407's walk on the setup page and the NEFT card; S408's and S434's on Amir's pack route.
- **Negative control** on the box as it is.

## 6 · Done means

Kit `deploy_kits\S452_AMIR_PANEL_FIXES\` · installed · published · `claude_code_briefs\REPORT_S452.md`, owner lines first:

- How many bills Amir's list now shows, and how many are held for reception.
- That the phone key is new, who can see it, and the one step to set the phone up.
- Amir's step 7 and board as he will read them.
- The NEFT line he sees for August, and that the sheet is a PDF.
- Medicine vouchers: 12 a visit, and the button for more.

Ending with:

```
https://followup.dr-manoj.in/finance/amir/day
```

```
https://followup.dr-manoj.in/finance/purchase/page/phone-setup
```
