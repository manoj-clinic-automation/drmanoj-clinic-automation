# S752_XRAY_CHECK_RETRY — the parked X-ray pictures filed by themselves

**The owner, 08-Nov-2026 14:46 IST:** *"build it"* — after Alisha found 41 October X-rays showing *photo baaki*.

**What was wrong.** The pictures had come. 33 of last night's 38 October ones were in Drive's **X-ray check**
folder (100 parked since 20-Sep), put there once and never looked at again; no Check karein answer was ever given.
- 9 had the right clinic ID, but the filing run (~17:40) came before Shavez's X-ray slip (~19:30);
- 17 were saved on the X-ray PC with the patient's name and no clinic ID;
- 6 had the ID typed one digit wrong.

**What changes.** On every mailbox run, each picture in the check folder that nobody has answered is planned again:

| the picture | what happens |
|---|---|
| its ID is now on that day's X-ray list (slip or Docterz) | **filed**, exactly as the inbox files it |
| no number, the day is over (its slips all in), its name is word for word that of ONE X-ray patient of that day (*Kumar*, *Devi*, *Begum*, *Lal* … count), and no other patient of that day shares a word of it; never a *baby of / master* picture | **filed** under that patient |
| an ID one keystroke off exactly one unfiled X-ray patient of the day, or a strict name match | **never filed by itself** — Check karein shows *Shayad ID …* with the ID already in the box: one tap on *Sahi ID lagayein* |
| a looser name match | *Shayad ID …?* in words only — the box stays empty |
| anything else | stays on Check karein, as before |

A picture a person has answered is never touched. A re-try that no longer places (the slip cancelled) goes back
to the list. The Drive side (`VPS_Lab_Files.gs` `_fileXray`) is unchanged — it already files any picture the plan names.

**Proof on last night's database (in the PC's sandbox, counts only):** of 100 parked pictures, 48 would be filed
(29 by their ID, 19 by name), 16 get a suggestion (9 already in the box), 36 stay for a person. October *photo baaki*:
**38 → 18**. The installer re-runs this proof on the live database before placing.

**The cold review (S404) — R1 NOT SAFE, all built:** a name-only picture could be filed while the day's slips were not
all in, on a one-sided word match, a prefix ('Mohan' / 'Mohanlal') or a child's 'baby of' name → now only after the day,
whole words, no other patient sharing a word, never a child's picture; a failing re-try rolled back the run's own inbox
rows → they are committed first; weak suggestions pre-filled → words only; re-tried rows stuck 'planned' → swept after a
day; two pictures could get one name → numbering counts the rows on their way; the re-try used Drive's time → the stored
one; one read per day per page. Also mended, as they bear on these pictures: an unreadable check folder no longer marks
every parked picture 'gone'; the ID box comes before *Yeh X-ray nahi*, so Enter in it means the ID.
**R2 NOT SAFE, built:** the strict rule still dropped the name-part words, so 'KAMLESH KUMAR' could be filed on the day's
only Kamlesh Devi ('SITA RAM' on Sita Devi, 'RAM PRAKASH' on Om Prakash) → for filing and for a pre-filled box those words
now count, and so do two-letter words. **Known, not changed:** an inbox picture can repeat a name a re-try used for the
same patient and day (inbox-to-inbox repeats were possible before); a picture the mailbox filed whose report never arrived
is swept to 'gone' after a day — its patient's *file nahi aayi* item comes back, the Drive copy stays unlinked.

**Files.** `/root/finance/records.py` 5b325c6f → a6ec1052 (`make_s752.py` from the live bytes: seven counted edits +
`s752_block.py` appended). Restarts `clinic-finance`.

**Walks.** `walk_s752.py` 50/50 (control on the live file red at the first S752 check); S373's own walk 20/20 on the
new file (the filing as it was). On the box both run on a scratch copy of `finance.db` in `/tmp`.
