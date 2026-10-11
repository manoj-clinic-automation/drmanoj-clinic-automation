# S303 BUILD BRIEF — the Sanjeevni close of 11-Oct-2026 (the dawn)

*Session 303, the Sanjeevni chat: opened 07:18 IST 09-Oct on manojz, closed at the owner's word "eos" at 05:21 IST 11-Oct. Routine `END_OF_SESSION_PROMPT_v18`. The next Sanjeevni chat is **session 307, reserved on the board at this close**; it starts from `START_HERE_SESSION_307.md`. The parent's session 305 is open (since 04:50 IST 11-Oct).*

## 0 · What the owner asked for, and what he got

| when (IST) | his words | what came of it |
|---|---|---|
| 09-Oct 07:17 | *"start"* | Phase 0 only. His hold (D695) kept every build to Saturday 22:30. |
| 10-Oct 12:26 | Darpan typed the TRUECEPROL count wrong in Stock milaan; *"check and tell whether anything else needs to be done"* | The correction never landed: the morning list refuses a second answer with a success-looking *"Pehle hi likha hai"* (**F-812**). |
| 10-Oct 13:31 | *"lot of old stock count data still populating here … the later one … is the correct one … the TYRO BR sentences … very confusing"* | Three findings. The 12:01 count went into the sealed 06-Sep count through *Dobara ginna hai* (**F-813**). TYRO BR's 70:7 line was a stale loss line that was never re-judged (**F-814**). Darpan's page still carried the finished 06-Sep work (**F-815**). |
| 10-Oct 17:24 / 17:26 | *"AMIR BUILD PENDING … CAN BE CLUBBED?"* · *"OK"* to the mock-up | S502 briefed; one run with S500. **D699.** |
| 10-Oct 20:22 | *"aligned with our Sanjeevni architecture revamp … spine as the main source everywhere … avoid duplicacies and wrong population … a final way forward for all future builds and corrections"* | The build charter (`claude/S303_BUILD_CHARTER.md`; builder's part `claude_code_briefs\SANJEEVNI_BUILD_CHARTER.md`). **D705.** |
| 10-Oct 22:30 → 23:20 | his paste line to Claude Code (Fable 5.1) | **S500 live 22:56** (morning reports checked, short closing refused, Amir's proof on the newest closing). **S502 live 23:20** (Darpan's page = today's work, same-day correction, TRUECEPROL 13:7, the 06-Sep count put back, TYRO BR's line voided and the item asked for Monday). |
| 10-Oct 23:10 | *"thoroughly check Amir's live page"* | His card told him to "correct" the LS belt vouchers that were right (**F-830**). **S520 live 23:45** (proven on the first or the newest closing). His renames opened. |
| 11-Oct 04:45 | S520 done | The board page Amir opens from his card still said *2 to correct* (**F-838**). **S521 live 05:07.** Card and board now say the same. |

## 1 · Live at this close

| kit | live | what it does | pins (FROM → TO) |
|---|---|---|---|
| S500_REPORT_CHECK | 22:56 10-Oct | *Aaj ki reports* says right or wrong for each morning report, with two tries; the owner is told only on failure; a short closing is refused 409; Amir's proof reads the newest closing | `reports_tile` 6f7cf490 → 01f67f4d · `stock_app` cc06dac9 → bfc2a40b · `amir_day` 59b035da → f1ce78e8 · `order_rules` ee17c187 → 79f21c1e · NEW `reports_watch` a8bbd95e, `reports_guide` 20a05704, `reports_guide_pics` d7f4f331 |
| S502_STOCK_MILAAN_TODAY | 23:20 10-Oct | Darpan's Stock milaan shows only today's work; *Galat likha? Badlo*; *Dobara ginna hai* closed to staff; data fixes | `stock_watch` d78c902e → c960f6c8 · `stockmatch.py` f09d9516 → fc1caf44 · `stockmatch.html` 0dc4d303 → 02826136 |
| S520_AMIR_PROOF_ANY_CLOSING | 23:45 10-Oct | an orthotic or medicine voucher is proven when the FIRST or the NEWEST closing after it shows the right move | `stock_app` bfc2a40b → 1f43f47e |
| S521_AMIR_BOARD_STAGE_PROOF | 05:07 11-Oct | Amir's board shows the stage's proof and renames, as his card does; his step-6 rename duty uses the same check | `stock_app` 1f43f47e → c0f0623f (**DECLARED-PENDING** until the 12-Oct bundle) |

S500, S502 and S520 equal the **11-Oct 01:35 bundle** (read at this close: ten files, ten equal).

**Data changed on the live database (S502, 23:20:19 IST):**
- TRUECEPROL OD point 377 (33:7, a slip) was superseded by point 379 (13:7, gap 0); roster 11 now reads 137.
- The 12:01 recount row was moved off the 06-Sep count (`count_id` −1).
- TYRO BR loss line 2 (70:7, Rs 13,079.50) was voided; trace 30 was set seen; TYRO BR was asked for Darpan's next morning list.

**Checked live by the chat, read-only:**
- Darpan's state (13:7, `can_fix`, only ZUPRINOR 5 in the last 7 days).
- Amir's card: *Orthotic: sab sahi ✓ · Naam badlo: 22 naam*.
- His board: the same line and the green chip; 23 renames listed with buttons; no medicine voucher for him in stage B.

## 2 · The charter (D705) — how every Sanjeevni build is made from now

- **Three kinds of data.** Marg's facts come from the spine. People's entries are written once. Conclusions are computed, never kept as truth.
- **One fact, one place.** Two named stock figures, the Marg figure and the shelf figure, are never mixed in one judgment.
- **A stored conclusion follows its inputs.** A correction is a new row that replaces the old one. A closed count is sealed.
- **One door per action. One screen, one person, one job.** Staff words are Roman Hindi with no system jargon.
- **Retire what you replace.** Repairs go through the system's own doors, never by DELETE.

It sits beside the parent's `BUILD_NORM_v1` (D704) and does not relax it.

**The order:** S486 re-read against the charter → **rung 4b, stock on the spine** (one module for the two figures; loss lines, flags and traces computed; the three count tables read through one view; `push_expected`, `marg_shadow` and `expected_units` retired after a side-by-side week) → late bills (S498) → Amir's flow and the bill chain (4c) → 4d, 4e, 4f → rung 5 and P4/P5.

## 3 · What the next chat does first (detail in `START_HERE_SESSION_307.md`)

1. **Phase 0.** Verify this close's publish landed.
2. **S521's pin against the 12-Oct bundle** (`stock_app.py` c0f0623f).
3. **Monday 12-Oct:**
   - read Darpan's answer for TYRO BR on his morning list;
   - read Amir's renames as they are ticked and proved by the next whole closing.
4. **The small ones the builds named:**
   - Amir's step 6 says twice that the salt list has not come (**F-839**).
   - The orthotic section's close-by-rule still judges by `_proof_state` (**F-840**).
   - The Loss desk's pile cache of count 1 has been stale since 29-Sep (**F-841**).
5. **Then the charter's order** (§2), S486 first, on Fable.

## 4 · Numbers

- **Session 303 used:** kits S502, S520, S521 · D699, D705 · F-812 … F-815, F-830, F-838 taken during the session; F-839, F-840, F-841 at this close.
- **Not used:** F-816 … F-829 (stepped over at 23:1x 10-Oct, when the board's kit counter was found behind the repository, F-831).
- **Next free (the board's `_numbers`, written once at this close):** D706 · F-842 · A-D25 · kit S523 · **session 307 RESERVED for the Sanjeevni chat**; 305 is the parent's, open; 306 is the new Scan App project's (opened 05:28 IST 11-Oct); 308 is the next unreserved.
