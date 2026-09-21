# START HERE — SESSION 280 — written at the S275 close, 21-Sep-2026

**Project: Sanjeevni — Pharmacy & Marg.** Open in a fresh chat in this project. Run `SANJEEVNI_START_HERE_PROMPT_v1_1` (the project's custom instructions) Phase 0 first, then this file. **Read `S275_BUILD_BRIEF.md` §0 for the mandate and §1 for what is live.**

*FIRST ACT: take your session number from `board/_numbers` by a version-pinned write (`NUMBERS_PROTOCOL_v1`). 280 is reserved there for this chat (279 is the parent's). If the pinned write fails, re-read and take what it says. Every kit, D and F number is taken the same way — never from this file, the Register or `deploy_kits\`.*

---

## 0 · THE MANDATE, IN HIS ORDER

The owner's approval section works now; the **page** it lives on does not. He ruled on its rebuild at 05:5x on 21-Sep (D591, D592, D593) and named one blocker he hits himself:

1. **F-603 FIRST — the Yes Bank statement upload refuses both PDF and CSV**, and its tile's message is wrong. *"upload bank statement didnt accept the pdf and csv, both formats for yes bank, fix it also when you fix this page, also fix the message on its tile."* Nothing is known about the cause yet: read the door's code first (his standing rule), get both of his real files, and find out what the door expects. This is before the rebuild — it is the one thing on the page he cannot work around.
2. **The approvals page rebuilt to D591.** The day panel in his order — sale (bill range → bills → items) · returns (count and amount → each credit note, its bills and items, every flag in **words**) · paid online (the bank's MPR against Marg's own bill-wise UPI, collapsed, the difference in a sentence) · billed without cash (home and procedure by bill number → items) · cash and the drawer · then *Needs you*, in words, at most two lines. **[Approve]** and then **[Log cash → me / Dr Bhawna / bank]** on the same panel (D592). Then the page's own faults: one drawer figure not two (F-604), the always-zero variance line gone (F-605), the ₹87,205 carried cash on its own line, the review queue no longer asking for names on classified label bills. Everything that is audit and not approval moves to an audit page one link away — kept, not deleted.
3. **The log window opens at 17-Aug-2026** (D593): change `setting darpan_kal.log_from` to `2026-08-17` **and** teach `_pending_days` to skip a day that already has a `cash_movement` of its own — August's six existing movements (20-Aug, 25-Aug, four on 31-Aug) must not be asked about again. Until that second half exists, do **not** move the setting.
4. **Then the carried work:** the spine's seven nights (D566/D572 — count them from `spine_state.json`, 20-Sep is night one), the first real morning on Shavez's tile, the category-list signature to the VPS (`b2dcb211` → `a987a08e`), the rung-4 paper.

**Do not** touch the stock-check screens or tables until count #1 is closed. **Do not** move any screen onto the spine before seven clean nights of `gate 13/13` and his word.

---

## 1 · THE CURRENT CANON — the manifest wins, this is only the index

| what | file |
|---|---|
| Register | `KB_Register_v5_119_S275close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_116_S275close.md` |
| Fault → Action Register | `Fault_Action_Register_v2_104.md` (F-0 … F-606) |
| Runbook | `HANDOFF_RUNBOOK_2026-09-21_Session275close_v199.md` |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| Sanjeevni Book | `SANJEEVNI_SYSTEM_BOOK_v1_7_S275.md` |
| the contract · the reference | `MARG_REPORT_CONTRACT_v1.md` · `S270_CORE_DATA_VERIFICATION_REFERENCE.md` |
| live pins | `live_pins_S275close.txt` |
| build brief | `S275_BUILD_BRIEF.md` |

**Next free (a mirror — the board's `_numbers` is the source): D597 · F-607 · A-D25 · kit S360 · Session 280 (this file) / 279 (the parent).**

---

## 2 · WHAT IS LIVE THAT WAS NOT, AS OF THIS CLOSE

`day_resync.py a4e53adc` (S356/S357, cron `*/30 7-23`) · `darpan_kal.py 2072e290` + `darpan_kal.html 4f115f44` + `darpan_month.html c4e81f7c` (S357/S359) · **the parent's, declared:** `finance_app.py 29819879 → 4a399f30`, `finance_ui/finance_approvals.html aa79b181 → c940c46f`, `tile_grants.json v24 7296bbd2` · two new `setting` rows (`noncash.home_words`, `noncash.proc_words`). Pins in the Register §S275.

**Frozen, never install:** `S355_DAY_TRUTH`, `S358_CASH_LOG` (F-512).

## 3 · THE PIN CHECK AT YOUR OPEN

The 21-Sep 01:35 bundle was built **before** tonight's installs, so `day_resync.py` is absent from it and `darpan_kal.py`, `finance_app.py` and `finance_approvals.html` will read at their **predecessor** hashes — expected, not drift. The 22-Sep bundle carries them all. The spine folder is in the bundle since S347 (the parent) but `spine.db` and `readings/` go to the **state backup**, not the code bundle.

## 4 · LESSONS FROM THIS SESSION, kept short

1. An installer may curl only a path in `PUBLIC_PATHS`; every other proof is an import or a database read. Third occurrence (F-602).
2. A surface that reports "none" is making a claim — check what it counts, not whether it renders (F-601).
3. When a form is replaced by an automatic filler, list what the form used to write. `day_noncash_bill` went unwritten for a month because nobody did (F-600).
4. A figure taken "as known at that moment" from a feed that arrives later is a wrong figure with a timestamp (F-599).
5. A check whose two sides became the same source prints a pass forever (F-605).
6. His spellings belong in the setting table; the day he writes a new one, it is one row, not a kit (D595).
