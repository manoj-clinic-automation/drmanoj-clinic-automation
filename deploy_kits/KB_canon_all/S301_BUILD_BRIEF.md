# S301 BUILD BRIEF — the Sanjeevni chat's close, 09-Oct-2026 (opened 7 Oct, 7:33 pm)

*The one paper for the owner. Also in the Sanjeevni project (`claude/S301_BUILD_BRIEF.md`) and in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S301\`.*

## 0 · Where it stands

**Every remaining build waits until after 10:30 pm on Saturday 10 October, as you said.** The first one then is the morning-reports build (S500), already written and checked.

**One fix went live on your PC (S501, 8 Oct, 10:01 am).** The PC's own stock figure had stopped going to the server, because Marg's item-wise purchase report prints only the first eight characters of long bill numbers. It now finds the full bill in the bill-wise report, and the figure goes again.

**Built and waiting for Saturday (S500):**

- **The two morning reports from your REPORT login.** Whoever is on morning duty follows the card's steps. The page *Aaj ki reports* says of each report whether it is right or wrong, and gives the step to redo. You get one phone message only if a report is wrong twice, or not right by 10:00.
- **A short stock list is refused.** The stock list of 6 Oct came without its zero-stock items (250 items instead of 379) and was taken as whole. Now a list that short is refused, and the staff are told to export it again.
- **Amir's orthotic banner.** The check of his seven vouchers looked only at the first stock list after them, so a correction made in Marg later could never be seen. It now reads the newest list. **Once S500 is in, his renames open by themselves.**
- **No more "Excel" on Amir's salt card.** It wrongly said the server cannot read text exports. It can, and the card will say so.

**Bills keyed later than their date** (most of the remaining "Marg has more stock" flags): I measured it and tried three rules. None was safe enough, so none went in — a flag cleared by mistake stays cleared. The next design matches each flag to one bill, used once.

**A repeated salt list is dropped without a word.** Your 1:31 pm salt list was the same as the morning's, so the medical PC dropped it silently and Amir's salt tick stayed. Nothing was lost. The fix — the PC tells the server "same as before" — comes after Saturday.

### Mine, said plainly

- I asked you for an Excel salt or category list on Thursday morning because a screen said so. The server reads text exports, and I should have checked first.
- I first gave Amir a step to re-type his voucher numbers. You found it cumbersome, and the real fault was in the system — now fixed in S500.
- While reading an exported sheet I printed its top lines, which include the pharmacy's name and part of its phone number. Nothing was saved. I now read these files below their header.
- The last close said a clinic-chat folder was not yet published. It had been. Corrected here.

## 1 · What needs you

1. **The publish** — this close's record. One double-click:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Saturday after 10:30 pm — the S500 build.** Paste this one line into Claude Code on this PC (the next session checks it first and gives you the same line):

```
Read D:\dr-manoj-git\drmanoj-clinic-automation\claude_code_briefs\S500_REPORT_CHECK.md and carry it out.
```

3. **When you have a minute, not urgent:** bank details for Agarwal Surgicals and Medicals.

```
https://followup.dr-manoj.in/finance/purchase/page/book
```

**The staff's, on their own screens:** morning staff — the two reports from the REPORT login, by the card. Amir — his renames once S500 is in; the two bills to find (Rama Medicose, Kushagra Medical Agency); the ₹310 Kedar entry in Marg.

## 2 · What is still to build, in order (from Saturday night)

1. **S500 — the morning reports, the short-list refusal, Amir's banner, the salt card.**
2. **The medical PC: say "same as before" instead of dropping a repeat;** with it, a long export captured whole.
3. **The buying model (S486)** — the fresh analysis on Fable, as you said on 5 Oct.
4. **Bills keyed later than their date** — the new design, analysis first.
5. **Small items:** the staff duty list's two wordings, the five new limits on your settings page, an answered salt reaching Amir's sheet.
6. **Amir's flow made calendar-safe — the remaining half;** then the rest of the pending list, in its order.

## 3 · Rules earned (binding)

- A whole report is judged against the reports before it, not only by its own shape (F-799).
- A check that waits for a later state reads the newest state (F-801).
- A reader that cannot place a row says which row and why (F-800).
- A machine that decides not to send says so where the sender will look (F-802).
- A rule that clears a flag for good is tested against the worst case, not only against the history that suggested it.
- An export asked of you or the staff is checked against what the server reads (F-805).
- Fix at the root, never by a staff step.

## 4 · Numbers

Session 301 · kits S498 (not built), S500 (waiting), S501 (live) · D694, D695 · F-790, F-799 … F-805. **Next free: D696 · F-806 · kit S502 · session 304 (303 reserved for this project's next chat; 302 is the clinic chat's, open).**

## 5 · Papers (`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S301\`)

`S301_OPEN_NOTE.md` (every read of the session) · `S301_LATE_BILLS_ANALYSIS.md` · `S498_evidence\` (not for building) · `S500\` (the brief, the staff card, the mock-up) · this brief · the start file for session 303 · the close report. The S500 brief and its parts are in the repository: `claude_code_briefs\S500_REPORT_CHECK.md`, `claude_code_briefs\S500_parts\`; the S501 kit in `deploy_kits\S501_PURCHASE_BILL_FRAGMENTS`.
