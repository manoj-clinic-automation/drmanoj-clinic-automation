# S295 BUILD BRIEF — the Sanjeevni chat's close, 05-Oct-2026 (opened 04-Oct 18:06)

*The one paper for the owner. Also in the Sanjeevni project (`claude/S295_BUILD_BRIEF.md`) and in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S295\`.*

## 0 · Where it stands

**Four builds went live today, each from your one paste line.**

- **Every Marg report is now read as text (S480, 07:25).** One reader for all of them; the method was proven cell for cell against Marg's own Excel on three reports before the build. A report with no rows — a day with no sale — is now taken as an answer, not as a broken export. That is why the orthotic proof ran by itself this morning: **26 of 28 right, two for Amir to correct** (ANKLE BINDER BAMBOO M, TYNOR WRIST SPLINT RT M ELAST). The salt page no longer shows the shop's own name as a salt.
- **The chain of bill numbers (S482, 09:44).** The system now knows a sale export is missing because a bill number is missing — not because of the day of the week. Your rule is built in: a gap is shown with its dates and numbers and exported again, never presumed a cancelled bill. **It found one gap: one sale bill and one credit note between 08-Sep and 09-Sep.** It shows on Shavez's tile and on your line until those two days are exported again from Marg.
- **The spine (S484, 11:35).** The morning's new text sheets tripped the spine's own check and it stopped building at about 08:10. The first fix stopped itself in testing (S483 — nothing was installed); the second went in and the spine has built normally since 11:37.
- **Darpan's order tab (S485, 15:24)** — *आज का ऑर्डर* on his *Kal ka hisaab*, as you approved on the mock. It is installed. **You have switched ordering back to Darpan's Marg sheet, so the tab is not in use**, and that is the right state until the logic is final.

**The ordering logic — measured, then parked at your word.** On your instruction I ran each ordering method over the shop's real sales from May to October:

| | days a medicine was at zero | average stock | supplier orders a week |
|---|---|---|---|
| The shop as it was (Darpan's sheets) | 173 | ₹2.28 lakh | 18 |
| The system as it stands today | 246 | ₹1.59 lakh | 24 |
| The refined model | 100 | ₹2.03 lakh | 20 |

Your judgement was right: the system as it stands is worse than Darpan's sheets. The refined model is better than both, and its build is written (S486). **It is parked, not started**, until it has been analysed again on Fable after Saturday night. Nothing changes for staff meanwhile.

### Mine, said plainly

- The order tab went live in the middle of the afternoon on a list Darpan had not been shown, because my brief assumed the day's orders were already made and I did not re-check. No order was lost. The rule is now in every brief: the installer reads and prints what staff will see next, and when (F-740).
- I gave you a server line for a kit that had not been built yet (*No such file*). Nothing was harmed. You get only the Claude Code line from me.

## 1 · What needs you

1. **The publish** — this close's record. One double-click:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Nothing else today.** Two things sit on the staff's own screens, not with you: Shavez's page asks for the sale reports of **08-Sep and 09-Sep** to be exported again from Marg (the gap closes by itself), and Amir has his two orthotic corrections. Not urgent.

## 2 · What the next chat does, in order

1. Checks today's 18 changed server files against tonight's backup copy. 2. Reads the morning: the first weekly order score on your card, Amir's proof, Darpan's sheet arriving by itself. 3. Builds the small kit you said *"Go"* to — dates shown right on three stock lines, Amir's waiting card saying since when and why, your own overdue line, a wrongly learnt item name struck off, and patient-bearing refused reports kept off Drive. It touches none of the ordering files. 4. After Saturday night, on Fable: the fresh analysis of S486, a few lines to you on what changed, then its paste line.

## 3 · Rules earned (binding)

- An empty report is an answer; the chain of bill numbers, not the calendar, says what is missing; a gap is re-exported, never presumed (D675).
- A Marg item is renamed only where the system cannot tell it apart, and the words staff type never change (D676).
- An ordering rule is chosen on the shop's own months before it is built; no hurry to switch at the cost of poor logic.
- A new road for a report is proved against every reader of that report before it goes live (F-734).
- A brief that changes what staff see says when it becomes visible, from a state read at install (F-740).
- An approval step is enforced on every page that can do the approved act, old pages included (F-738).

## 4 · Numbers

Session 295 · kits S480, S482, S483 (built, not installed), S484, S485 · S486 briefed, parked · D675 … D678 · F-728 … F-740. **Next free: D680 · F-741 · kit S488 · session 297 (296 reserved for this project's next chat).**

## 5 · Papers (`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S295\`)

`S295_TEXT_READERS_ANALYSIS.md` · `S295_ORTHOTIC_RENAMES_CHECKED.md` · `S295_CALENDAR_GLITCH_AUDIT.md` · `S295_ORDER_MODEL_REPLAY.md` (+ `replay\`) · `S295_PENDING_BUILDS_05OCT.md` (everything still to build, by the decided architecture) · the six briefs `S480 … S486` and the five reports `REPORT_S480 … S485` · `darpan_order_mock_K3.html` · this brief · the Book v1.12 · the canon files of this close.
