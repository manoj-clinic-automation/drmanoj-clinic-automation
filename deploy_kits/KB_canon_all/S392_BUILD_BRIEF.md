# S392 BUILD BRIEF — the Scan App project (papers & bills), 06-Nov-2026

*For Dr. Manoj. One page: what changed for you, and what waits on you.*

## What changed

**1 · Why B-0250 was never read — found and fixed (live since 17:1x IST).** Reception scanned Variety's challan with the Challan button on the **Other document** lane (the one marked *bill nahi*). That lane is never sent to Claude, so the paper said *read failed* at once. Moving it on the desk didn't read it either. Now:
- a **challan** is read by Claude whichever lane reception presses (letters, resumes, personal and patients' papers stay unread, as before);
- a paper that was never read gets read **by itself** once it is sorted on the desk or its lane is changed.

**2 · B-0250 is sorted:** VARIETY STATIONERS, challan 2787, three Clinic lines dated 05-Nov, on Variety's account and in the stock.

**3 · Other lines on the sorting desk (live since 17:5x IST).** A paper sorted to **Others** now has lines: what it is, quantity, unit and rate, *+ Add a line*, × to remove, each line's amount and the total against the paper. It starts from what was read and saves only if you change it.

**4 · X-ray film lines are not needed.** As you said: all 11 film bills since April were read with their size and boxes, so nothing was built for them.

## What waits on you

**1 · The publish** — this close's record (papers only; nothing follows it on the server):
```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

**2 · Your X-ray film log says "Opening boxes not set".** Until you enter the spare boxes on the shelf, it counts them as 0. (That page is the clinic chat's.)

**3 · Variety's phone number** on your Vendors page, so the monthly statement goes to them by WhatsApp in one tap.

## What I do next (a fresh session, in your order)

1. Check Variety's statement-and-bill flow end to end on the live page.
2. Draw the *recent scans by date* mock-up for you.
3. Build Yuvika's goods into the Procedure room lines, and show it to you first.
4. Write the plan for the NK share, for the clinic chat and the NK Pathology chat.
