# S426 CLOSE REPORT — the Sanjeevni chat, 11-Nov-2026 (for the assistant; CLOSE_ROUTINE_v1, A17 kept)

**Connected this session:** `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup` — the device shell until 05:2x IST, then file tools only (F-1255); Google Drive (the medical heartbeat); the built-in browser (read only, as manoj); the cloud workspace (code only: the 11-Nov bundle's `root/finance`, `root/shared`, `root/assetapp`, `root/portal` code; S425's `schema_only.json` — the tables' layout, no rows; made-up review pages; board JSON).
**Agents:** an order-screen reader; a code mapper of `scan_register` / `section_count` / `claude_reader`; a reader of five scans' lines; two cold reviewers of S781 (+ one of its additions), one of S783; screen reviewers (S781 four rounds, S783 one); live readers after each install; a reader of the unlinked scans — nothing pressed by any.

| # | step | state |
|---|---|---|
| 0 | Numbers first | **DONE** — session 426 (v1208); kits S781 (v1209), S783 + PLANNED on `claude_reader.py` (v1211), S784 (v1213); D900, D901, F-1255 – F-1257, CLOSING, 429 RESERVED (v1217). |
| 1 | Archive | **PART WRITTEN** — `archive.md` (§S426); placed at the next open. |
| 2 | Fault Register | **PART WRITTEN** — `fault.md` (§7.178); placed at the next open. |
| 3 | KB Register | **PART WRITTEN** — `reg_h1.md`, `reg_sections.md` (4 DECLARED-PENDING; D900, D901). |
| 4 | Manifest + its four surfaces | **PART WRITTEN** — `man_narr.md`, `close.json` (DRAFT: the anchors filled at the next open from the CURRENT manifest). |
| 5 | Runbook + START_HERE | **PART WRITTEN** — `rb_section.md`; `START_HERE_SESSION_429` also written to project knowledge now so the next chat can start. |
| 6 | OWNER_TODO_LIVE | **PART WRITTEN** — `todo.md`. |
| 7 | Live pins + row + canon sums | **NOT DONE — waits for the shell (F-1255)**; the next open runs `close_build.py`. |
| 8 | The one board batch | **DONE** — `_numbers` (CLOSING, 429 RESERVED); `_page` (this project's yours / tell). `_claude_status` left to the canon build. |
| 9 | The page's code | **Not republished.** |
| 10 | Papers | The brief and START_HERE to project knowledge now (by content — the shell is down; no patient data in either); the report, the Runbook, the pins, the to-do and the Book at the next open, by file. |
| 11 | New live files (A12b) | finance.db `purchase_s781_mark`; `/root/finance/provisional_s781.py` NEW; `claude_reading.data` items' four keys. |
| 12 | The publish gates | S781 (05:47, 44597671), S783 (06:10, 043c9b10), S784 (06:42, 840e7650) — each landed, main = origin/main. This close's canon gates: at the next open. |
| 13 | Publish | **Not named now** — nothing of this close is in canon yet; the next open names it after `--place`. |
| 14 | Prompts | **To the Scan App chat:** S783 appended a block to `/root/assetapp/claude_reader.py` (PLANNED v1211): `PHARMACY_PROMPT` asks for `free`, `mrp`, `discount`, `gst` per item; `clean_pharmacy` keeps them; `_post` lets a pharmacy reading run to 16000 tokens and retries a too-long bill with the old prompt; `read()`, `PROMPT`, `clean()`, `to_bill()` untouched. **To the parent:** S784 changed one line of `finance_approvals.html` (the Go-to label); S781 reads `section_count` (S771) and posts to its door from the Purchase bills page — no key the parent reads changes. |
| 15 | Rules learned | four (Runbook §2B *The lessons*). |
| 16 | The four numbers | drift `purchase_app.py` 2, `claude_reader.py` 1, `finance_approvals.html` 1, `amir_day.py` 5, `section_count.py` 3, `porders_s454.py` 1; dead 0; stale 0; folders `03_WORKING_PAPERS\S426\` (screen, close_parts), `_to_delete_S426\`, the VM's `/tmp/s781w` (F-1255). |

**Install outputs (as he pasted them):** `S781_PROVISIONAL_BILLS: DONE…` (05:48) · `S783_SCAN_LINE_EXTRAS: DONE…` (06:11) · `S784_HUB_GOTO_LABEL: DONE…` (06:44).

**Read live after each install (as manoj):** S781 — tiles ₹1,23,655 / 25 = the register's chip; provisional 0; one difference (Yuvika 803, ₹16; XL/XXL quantities; on Amir's list since 08-Nov; the S771 line table and the scan shown); no console error. S783 — "Newest bill scanned: 08-Nov 8:44 AM · Marg's bills on the server reach: 07-Nov · No bill scanned for 3 working days…"; an older scan's lines "Not read on this scan: free goods, MRP, discount, GST"; both healthz OK. S784 — the new name, the same address, the old name nowhere.

**The build (close_build.py):**
```
FROM: KB_Register_v5_260_S428close.md · KB_History_Archive_v1_257_S428close.md · Fault_Action_Register_v2_244.md · HANDOFF_RUNBOOK_2026-11-11_Session428close_v340.md · live_pins_S428close.txt · START_HERE_SESSION_426.md
TO:   KB_Register_v5_261_S426close.md · KB_History_Archive_v1_258_S426close.md · Fault_Action_Register_v2_245.md · HANDOFF_RUNBOOK_2026-11-11_Session426close_v341.md · live_pins_S426close.txt · START_HERE_SESSION_429.md
Archive v1.258: prefix 2,880,504 B = KB_History_Archive_v1_257_S428close.md b42bb16d PROVEN; 2,886,089 B eda285b796d9f8373286f107f3baf764
Fault v2.245: prefix 1,431,632 B = Fault_Action_Register_v2_244.md 2568525e PROVEN; 1,434,960 B 3499964049355192b8edfc8e233e4205
Register v5.261: 2,269,504 B 03720532643a58805eee4b4b3d6d6935
Runbook v341: 267,312 B 2e23f430c30b218584bd6c7b1e40f5e7
START_HERE_SESSION_429.md: 5,358 B a6cb836aa673bdbf7cf9daa6a0be3696
S426_BUILD_BRIEF.md: 1,860 B 515b5bc23cb7d8f2a1bafa6f77f56dbf
OWNER_TODO_LIVE: 284,715 B 9e3c3defdcdc88fbadb7c05f1ff07b64
SANJEEVNI_SYSTEM_BOOK_v1_60_S426.md: 523,946 B ddd674d3623bfb1c2bb9702dba45dcb0
```
