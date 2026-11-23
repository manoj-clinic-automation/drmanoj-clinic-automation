# S505 BUILD BRIEF — the Sanjeevni chat, 23-Nov-2026 morning (for Dr Manoj)

**What changed (one kit, S934, live 09:11)**

- **Count now or Next list.** Your Count button on the Stock check now asks which: **Count now** puts the medicine on Darpan's count screen at once (his "Abhi ginti" card); **Next list** puts it on the next morning's list as before. Your open asks show under "Your open asks", each with a two-tap Withdraw. The twelve you had raised were cleared at install, as you said.
- **Counts placed to the last bill.** With a Count now, Darpan keys the last sale bill number. The system then waits for that day's sale report and judges his count exactly: the stock at the end of the day plus whatever was sold after that bill. Deliveries that arrive after his count are not expected on his shelf; a delivery dated that day shows the gap but never books a loss.
- **The morning reports.** Monday's three reports reached your Stock check about twenty minutes after your last export, read correctly as "the end of 22-11". Nothing to touch.

**Found this morning (not yet fixed — first work next session)**

- **TRAMATEE P.** On Saturday Darpan counted 9:4 but missed the carton of Mannat's bill 502 (40 strips, delivered Friday evening). The system took 9:4 as the shelf, booked a false loss of 32:12, and **today's 09:30 order list asks Mannat for 50 strips of TRAMATEE on "on hand 4:0"**. Mannat is not due today, and the next list will read today's count (44:0); the real gap against Marg is only −2:12. Fix next session: a count that is short by about a fresh delivery is held as **"recount"**. It is not used for orders or losses, and it goes back to Darpan as a Count now. The false loss will be removed.
- **The bill number.** Darpan counted all eleven at one bill (4938) and keyed it once. Next session the card will ask for the bill **once per sitting**, not once per medicine. The ten counts that went in without it will be placed to 4938 after a check.
- **TYRO BR** (51:5 to bill 4938) will be judged tomorrow morning, once today's sale report is in.

**Checked before install:** 46 offline checks (the old files fail 40 of them); the stock record rebuilt on copies of the live data came out identical, row for row. A separate reviewer found two faults that would have booked false losses (judging too early; counting later deliveries). Both were fixed, and its second look passed. The installer was rehearsed, including a forced failure and an undo.

**What waits on you**
- The publish of today's records (below).
- Kit 2 (every other page on the one stock record) waits, as you said, for Darpan's counts and a look at the page together.
- Ram Singh: the Stock Register report in Shavez's Marg login. The packs page: the 25 card shops; the card and ICICI passwords.

**Your Stock check page:**
```
https://followup.dr-manoj.in/finance/stockcheck/
```
**Publish:**
```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```
on manojz — nothing follows it.
