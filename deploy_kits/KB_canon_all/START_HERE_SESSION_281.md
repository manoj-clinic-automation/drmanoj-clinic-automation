# START HERE — SESSION 281 — written at the S280 close, 21-Sep-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project. Run `SANJEEVNI_START_HERE_PROMPT_v1_1` (the project's custom instructions) Phase 0 first, then this file. **Read `S280_BUILD_BRIEF.md` §0 for the mandate and §1 for what is live.**

*FIRST ACT: take your session number from `board/_numbers` by a version-pinned write (`NUMBERS_PROTOCOL_v1`). 281 is reserved there for this chat. The parent's S279 was open at this close; if it has taken 281, re-read and take what the board says. Every kit, D and F number is taken the same way — and a kit number is claimed BEFORE its scratch folder is named (F-515, F-611).*

---

## 0 · THE MANDATE, IN HIS ORDER

1. **F-612 FIRST — his Yes Bank CSV is still refused.** His words at the S280 close: *"the Yes Bank statement is not picking up the CSV. Again, it is giving an error … Didn't try the PDF. So add it for the next session."* The door (`finance_yesbank.py` v1.1, S360) refuses, **by design**, a CSV with no `Statement Period` line and points at the PDF (F-112). Do this, in order: (a) find his real Yes Bank files in `D:\Downloads` (newest `*.csv` / `*.pdf` whose name starts with the bank's pattern — never print the account number, only its last four) or ask for them once; (b) run both through the module offline and read the exact message; (c) if the PDF passes, tell him to load the PDF — one line, the full workbench URL in a copy block; (d) make the CSV usable without breaking F-112: the page asks for the From / To dates when the file does not state them, and the reconciler treats only that range as seen. Build → walk on a scratch copy → kit → his publish. The pool's two deposits read *unevidenced* until a statement lands.
2. **The ₹200 of 04-Sep** — filed ₹23,675, Marg's bills ₹23,875. The day panel puts it to him in words. Find which bill makes the ₹200 (read `sale_bill` for 04-Sep against the filed day line) and put the one-line answer to him; he rules.
3. **The rest of D591** — the approvals page's *Needs you* strip at the top, the sections in his order, and the audit apparatus moved to its own page one link away. The day panel (D601) is done and live.
4. **Carried:** the spine's seven nights (D566/D572, from 20-Sep — count from `spine_state.json`) · the first real morning on Shavez's tile · the category signature `b2dcb211 → a987a08e` · the rung-4 paper.

**Do not** touch the stock-check screens or tables until count #1 is closed. **Do not** move any screen onto the spine before seven clean nights and his word. **Do not** ask him to log August or September days (D598).

---

## 1 · THE CURRENT CANON — the manifest wins, this is only the index

| what | file |
|---|---|
| Register | `KB_Register_v5_120_S280close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_117_S280close.md` |
| Fault → Action Register | `Fault_Action_Register_v2_105.md` (F-0 … F-612) |
| Runbook | `HANDOFF_RUNBOOK_2026-09-21_Session280close_v200.md` |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| Sanjeevni Book | `SANJEEVNI_SYSTEM_BOOK_v1_8_S280.md` |
| live pins | `live_pins_S280close.txt` |
| build brief | `S280_BUILD_BRIEF.md` |

**Next free (a mirror — the board's `_numbers` is the source): D602 · F-613 · A-D25 · kit S366 · Session 281 (this file) / 282.**

---

## 2 · WHAT IS LIVE THAT WAS NOT, AS OF THIS CLOSE

`finance_yesbank.py 825016c0` · `sanjeevni_cash.py 8e58691b` NEW · `sanjeevni_day.py 7f6ea583` NEW · `darpan_app.py 2c22822d` · `darpan_kal.py 19b9c0e8` · `darpan_month.html cee5478b` · **the parent's, declared:** `finance_app.py 70cff498`, `finance_ui/finance_approvals.html 6c668ccc`, `finance_ui/finance_workbench.html 601d5a77` · tables `cash_anchor`, `cash_handover_cover`, `cash_bill_ruling`, `cash_period_close`, `cash_pool_deposit` · `setting darpan_kal.log_from = 2026-08-17` · `poppler-utils` on the box. Pins in the Register §S280.

**Withdrawn, never published:** `S362_CASH_SCREENS` (in `D:\dr-manoj-git\_to_delete_S280`).

## 3 · THE PIN CHECK AT YOUR OPEN

The 21-Sep 01:35 bundle was built **before** every S280 install, so all nine files read at their **predecessor** hashes (or absent, for the two new ones) — expected, not drift. The 22-Sep bundle carries them. Before convicting anything from the bundle, read the live surface (v16 rule 1).

## 4 · LESSONS FROM THIS SESSION, kept short

1. A kit that needs a system binary asks for it in its first step; never assert a package is on a box you have not asked (F-608).
2. A time goes into canon only when read — the S359 time was six hours early (F-609).
3. The screen shows the figure he checks by hand, built the way he builds it. His ₹11,291 was right and the panel was not (F-610).
4. Claim before you name the folder — for the fifth kit of the day as for the first (F-611).
5. When he says "only answer, don't code", the plan is the deliverable; when he rejects a design (S362's day-by-day logging), withdraw it whole rather than patch it.
