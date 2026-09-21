# S275 BUILD BRIEF — the night the approval figures became true, 20–21-Sep-2026

*Written at the close, 21-Sep-2026 (clock read). S275 opened 21:55 IST on 20-Sep on one line from the owner. Next Sanjeevni session: **S280** (reserved on the board; 279 is the parent's).*

## 0 · THE MANDATE FOR S280 — in his order

1. **F-603 first — the Yes Bank statement upload.** It refuses both PDF and CSV, the two formats his bank gives him, and the tile's message describes something else. *"fix it also when you fix this page, also fix the message on its tile."* Nothing is known yet: read the door's code, get his two real files, find what it expects. It is the one thing on the page he cannot work around.
2. **The approvals page rebuilt (D591, D592).** The day panel in his order — sale (bill range → bills → items) · returns (count, amount → each credit note, its bills and items, every flag **in words**) · paid online (bank MPR vs Marg's own bill-wise UPI, collapsed, the difference in a sentence) · billed without cash (home and procedure by bill no → items) · cash and the drawer · *Needs you* in words, two lines at most. **[Approve] then [Log cash → me / Dr Bhawna / bank]** on the same panel. Then: one drawer figure not two (F-604), the always-zero variance line gone (F-605), the ₹87,205 carried cash on its own line, the review queue no longer asking for names on classified label bills, and everything that is audit rather than approval moved to its own page one link away.
3. **The log window to 17-Aug (D593)** — `setting darpan_kal.log_from = 2026-08-17` **only together with** `_pending_days` skipping days that already carry a `cash_movement` (August has six).
4. **Then the carried work:** the spine's seven nights (20-Sep is night one), the first real morning on Shavez's tile, the category signature `b2dcb211 → a987a08e`, the rung-4 paper.

**Standing rules unchanged:** nothing onto the spine before seven clean nights and his word; the stock-check screens untouched until count #1 closes.

## 1 · WHAT S275 DID

| item | kit | live | what |
|---|---|---|---|
| the UPI half | **`S356_DAY_TRUTH_2`** (S355 frozen) | 22:17 | `day_resync.py` NEW: an unapproved autofiled day takes its UPI from the bank statement, cash = net − UPI, audit row, exception re-judged. **9 days fixed, ₹69,444, every exception closed** (F-599) |
| the home/procedure half | same kit, pass 2 | 22:17 | every label bill (`HOME MEDICINE`, `PROSIJER …`) becomes a `day_noncash_bill` row by word lists in the `setting` table. **7 days, 11 bills, ₹15,960 home + ₹1,337 procedure** (F-600, D595) |
| the credit note | **`S357_DAY_TRUTH_3`** | 22:27 | a label credit note is **+₹2,300 back to the drawer** (11-Sep `CN00208`), not a hole; Darpan's page reads the same adjustment (D594) |
| the cash log + the month table + the hub card | **`S359_CASH_LOG_2`** (S358 frozen, F-602) | ~23:0x | `api/pending` + `api/log` (both doctors, one day or a backlog, the log is the *received* stamp — D596) · `/kal/month` · the hub's card reads the day books at last (F-601) · `tile_grants.json` v24 (Dr Bhawna) |
| the page's own faults | — | — | named, not built: F-603 (open), F-604, F-605, F-606; the rebuild is D591/D592 |

**Live pins:** `day_resync.py a4e53adc` · `darpan_kal.py 2072e290` · `darpan_kal.html 4f115f44` · `darpan_month.html c4e81f7c` · **the parent's, declared:** `finance_app.py 4a399f30`, `finance_ui/finance_approvals.html c940c46f`, `tile_grants.json v24 7296bbd2`. One cron line (`# S356_DAY_TRUTH_2`, `*/30 7-23`). `clinic-finance` restarted three times, `clinic-portal` once.

**September, as the night ended:** sale ₹3,77,565 · UPI ₹1,38,053 · cash ₹2,39,512 · − home ₹11,023 · − procedure ₹1,337 · ± adjustment +₹2,300 · **net cash ₹2,29,452** · handed ₹0 (17 days waiting to be logged).

## 2 · THE RULES THIS SESSION ADDED

**An installer may curl only a path in `PUBLIC_PATHS`** — every other proof is an import or a database read (F-602, third occurrence). · **A surface that says "none" is making a claim; check what it counts** (F-601). · **When a form is replaced by an automatic filler, list what the form used to write** (F-600). · **A word list his staff generate lives in the `setting` table, not in code** (D595). · **Approve first, log the cash after** (D592).

## 3 · NUMBERS

Taken from `board/_numbers` this session: session 275 · kits S355 … S359 · D591–D596 · F-599–F-606 · session **280** reserved for the next Sanjeevni chat. Mirror at this close: **D597 · F-607 · A-D25 · kit S360 · Session 280 (Sanjeevni) / 279 (the parent)**.

## 4 · OWED TO THE PARENT (one line each)

- `finance_upi.py` writes its resolution text as a literal format string (F-606).
- The autofile's root cause: the bank-statement handler could call `day_resync.py` on arrival instead of waiting for the half-hour (F-599).
- Three of its files moved and were declared: `finance_app.py 29819879 → 4a399f30`, `finance_ui/finance_approvals.html aa79b181 → c940c46f`, `tile_grants.json` v23 → v24 `7296bbd2`. One root cron line. `clinic-finance` ×3, `clinic-portal` ×1.

## 5 · WHERE THINGS ARE

Working papers `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S275\` (`kit_build\`, `close\`, this brief, the close report) · kits `02_SESSION_KITS\S275\` (five) · canon snapshot `00_CANON_SNAPSHOT_S275\` · project knowledge: `claude/S275_BUILD_BRIEF.md`, `claude/SANJEEVNI_SYSTEM_BOOK_v1_7_S275.md` (v1.6 removed there, the canon copy proven) · the board keys `kit_S35x`, `session_S275`, `close_S275` · this close's canon in `KB_canon_all\` (Register v5.119 · Archive v1.116 · Fault v2.104 · Runbook v199 · `START_HERE_SESSION_280` · Book v1.7 · `live_pins_S275close.txt`).

---
*S275_BUILD_BRIEF · close 21-Sep-2026 · the mandate is §0.*
