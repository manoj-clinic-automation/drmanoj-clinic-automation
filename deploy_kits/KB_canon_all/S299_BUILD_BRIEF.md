# S299 BUILD BRIEF — the Sanjeevni chat's close, 07-Oct-2026 (opened 07:23, closed in the afternoon)

*The one paper for the owner. Also in the Sanjeevni project (`claude/S299_BUILD_BRIEF.md`) and in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S299\`.*

## 0 · Where it stands

**One build went live today (S494, 12:33 pm), from your one paste line.**

- **Reception is told when Darpan's order sheet arrives.** The message had failed every time. The cause was found in the code and proved on the server: the part that was sending it is not able to send messages. It is now sent by the part that sends every other message, within ten minutes. **Not yet seen on a real sheet** — Darpan's next order sheet is the first test, and the next session reads it.
- **The stock flags are judged again when the day's reports arrive.** "Marg and the shelf figure moved apart" fell from 81 items to 10 at the newest closing (77 to 7 and 52 to 15 on the two days before).
- **The spot-count line shows once** on your list, not twice.
- **Amir's one-time jobs are on his own page**, under *Ek baar ke kaam*, each line gone when its work is done: the bill to scan for Rama Medicose and for Kushagra Medical Agency, and the ₹310 cash entry for Kedar in Marg. Agarwal Surgicals closed by itself — its bill was already scanned.

**Your three notes of 24 September are done.**

- **Kedar's old July balance** — you typed Paid ₹98,240 on July's vendor sheet yourself (₹97,930 by NEFT + ₹310 cash adjustment). I read it back from the page.
- **The four appliances** — you corrected their category in Marg yourself. Marg's own list of 1:47 pm shows all four under ORTHOTICS, so they never reach Amir's page.
- **The name-check sheet** — your aliases of 14 September had settled fourteen of its names; the rest are the bill-scan lines now on Amir's page.

**The bank's statements did not come this morning.** The pharmacy's day already goes ahead on Marg's own figures, marked provisional. Your design — the total typed from the POS machine at the moment of posting, on the same screen, counted only after you confirm — was built this afternoon by the clinic chat for the pharmacy and the clinic together.

**Amir's work stays in this project, on his own page.** His *Aaj ka kaam* list stays switched off, as you said; I add nothing to it.

**Other reads of the morning.** The first weekly order score: of what was bought last week, 30% had been on the list beforehand; 2 medicines ran out and neither was listed in time. The report refused at 5:30 am was a whole-month statement that stopped at page 86 — refused rightly. The two missing days of September were taken, so the bill chain has no gap.

### Mine, said plainly

- While finding out why that report was refused, I opened two files in a way that showed me two bill lines with a patient's name and number, and one row with an account number. Nothing was written, sent or kept. I now read such files by their shape only.
- The last session's notes said I would save the Kedar entry. I cannot save a money figure on a live page, and I should not have promised it. You typed it; that is how it stays.
- The first two drafts of today's build had four serious faults. Two independent reads caught them before you were given the paste line.
- Four of today's changed server files are confirmed by the installer's own check, not yet by the nightly copy. Tomorrow's copy confirms them; the next session reads it first.

## 1 · What needs you

1. **The publish** — this close's record. One double-click:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **When you have a minute, not urgent:** type the bank details for Agarwal Surgicals and Medicals — its bill is scanned.

```
https://followup.dr-manoj.in/finance/purchase/page/book
```

**On the staff's own screens, not yours:** Amir — his two orthotic corrections (ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST), then his 22 renames, and the three lines under *Ek baar ke kaam*.

## 2 · What is still to build, in order

1. **The buying model** — parked until the fresh analysis after Saturday night. System ordering follows only after three good scored weeks.
2. **Bills keyed later than their date** — 15 of the 19 remaining "Marg has more stock" flags are this. Small. Analysis first.
3. **Amir's flow made calendar-safe** — the remaining half.
4. **The bill chain replaces the calendar** on the screens that still say "missing" by weekday.
5. **The next medical-PC build** — a refused report read again after a fix, and long exports captured whole.
6. **Small items** — an answered salt reaching Amir's sheet, the new limits on your settings card, the order sheet's remarks, two wrong wordings.
7. **The remaining screens onto the single source of truth**, one build each.
8. **Stock check** — count #2 by section, the count page's defects, the internal-use register.
9. **Near-expiry screen and returns desk phase 2.**
10. **Scanned bills into Marg without waiting for Amir** — your aim; not designed yet.
11. **Last** — the old duplicate parts retired, and the pharmacy as its own program.

**The next session starts on item 2 at your "go"**, after it has checked tomorrow's server copy and read the order-sheet message on a real sheet.

## 3 · Rules earned (binding)

- A message is sent by the part of the system that can send it (F-767).
- A stock flag, once judged again, can only be cleared — never raised a second time (F-765).
- A bill belongs to the stock of the day it was keyed, not the date printed on it (F-787 — to be built).
- A money figure on a live page is your own hand; I show the row and read it back (F-785).
- A file that holds patients is read by its shape, never by its first lines (F-784).
- Amir's work lives on *Amir ka kaam* only (D690).
- What you can put right yourself in two minutes is offered to you before it is queued for staff.

## 4 · Numbers

Session 299 · kit S494 · D686, D690 · F-771, F-784 … F-789. **Next free: D691 · F-790 · kit S498 · session 302 (301 reserved for this project's next chat; 300 is the clinic chat's, open).**

## 5 · Papers (`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S299\`)

`S299_OPEN_NOTE.md` (every read of the day) · `S494_AMIR_JOBS_NOTICE_FLAGS.md` (the brief; its two drafts beside it) · this brief · the Book v1.14 · the start file for session 301 · the close report. The kit is in the repository: `deploy_kits\S494_AMIR_JOBS_NOTICE_FLAGS`, with `claude_code_briefs\REPORT_S494.md`.
