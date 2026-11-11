# S428 — X-ray photos still waiting: why, and the plan to match them by every pipeline

**Asked:** the owner, 11-Nov-2026 09:41 IST — *"review thoroughly, analyze the issues and bring a plan so that maximum patients can be
matched through all the data pipelines that you have, and we only flag those here which really need to be flagged."* — 09:45 IST:
for the patient not registered anywhere (B.P.), *"such cases indicate that there could be a payment gap. So they should also be highlighted."*
**Read:** every photo still parked on the 11-Nov database copy (03:15 IST), after the S787/S788 rules were run on it (5 more filed).
25 cards remain (≈ the 23 on his page). Counts and initials only — no patient name, number or clinic ID in this paper.

## 0 · Why a "filed" rule has not acted yet
The filing plan runs when the clinic mailbox script asks for it — **every 15 minutes** (corrected at the close, F-1260; the earlier
"13:10 and 18:10" was read from the times runs had new work). Rules installed at 09:27 acted at the next run (S.W., 24-Oct, filed by S788).

## 1 · What the 25 cards are
| # | kind | cards | examples (initials, day) | today |
|---|---|---|---|---|
| A | the name IS one X-ray patient of the day, spelt another way the rules do not know | 6 | H.S.A. 24-Oct (a 2-letter word dropped) · K.K. 21-Oct (vowels left out; the film reads the right ID) · B.S. 23-Sep (letters swapped) · K.G. 19-Oct (two numbers in the name; the film read garbage) · R.K. 10-Oct (number one digit off, film garbage) · A. 5-Oct (two digits of the ID swapped) | waits |
| B | the number on the file AND on the film agree, the patient came that day, the name is his (a shorter or longer form) | 3 | K.T. 25-Oct (a re-upload) · N.A. 24-Sep (no X-ray slip) · Dr B. 26-Sep (staff) | waits |
| C | the name is exactly one X-ray patient, the number points to someone who came WITHOUT an X-ray (typed wrong at the machine) | 1 | V.D. 21-Sep | waits |
| D | only the first name was written, and only one patient of the day has it | 2 | B. 16-Oct (X-ray patient) · R. 28-Sep (came, no X-ray slip) | waits |
| E | a sound-alike the rules cannot safely call (M/N, S/K, H/N) — the X-ray patient's photo is already filed or several are missing | 3 | A. 23-Oct · Y. 28-Sep · N. 21-Sep | waits |
| F | nobody who came within a day has the name — the patient IS registered (one match in the patient list) | 2 | A.M. 10-Oct (came late: no slip, no Docterz) · S. 20-Sep | flagged as "no clinic ID" — wrong flag |
| G | not registered anywhere — **a likely payment gap** (an X-ray taken, no registration, no slip, no Docterz line) | 2 | S.A. 5-Nov (on "Not in Docterz") · B.P. 15-Oct | flagged as "no clinic ID" |
| H | truly ambiguous: a common name with many registered matches, conflicting number and name, or a day with no clinic at all (20-Sep had no slip and no Docterz line: the file's date is wrong) | 6 | S. · K.D. · S.A. · V. · R. ×4 · S. | a person |

## 2 · The plan — new rules, in this order, each written as a "system" answer the next filing run files
1. **The number decides when it is double-confirmed (B).** The number in the file name and the number read on the film are the same, and
   that patient came on the film's day ±1 → file to him, whatever form the name takes. No X-ray slip that day → the photo is filed AND
   the X-ray goes on "X-ray taken, no X-ray slip" (the existing billing flag) — never left as "no clinic ID".
2. **The name, spelt the ways staff spell it (A).** Compare names (a) with spaces and short words kept, (b) by consonants when vowels are
   dropped or swapped; numbers: ignore a film number that is no real ID (junk OCR), accept two swapped digits as well as one wrong digit.
   Exactly ONE patient of the day ±1 may match, as now.
3. **The name decides over a number that points to someone without an X-ray (C)** — the owner's 09:14 rule widened: the name is exactly
   one X-ray patient's; the number is a patient who came that day with no X-ray.
4. **First name alone (D)** — only when exactly one patient who came that day ±1 has that first name (and no other visitor shares it); an
   X-ray patient → filed; no X-ray slip → filed + the billing flag.
5. **Another photo of a patient filed that day, by sound (E, part)** — rule E of S787 with the wider spelling of rule 2; the photo is that
   patient's second view. The rest of E stays for a person, with that patient placed first.
6. **Registered, but no slip and no Docterz entry that day (F)** — the name matches exactly ONE patient in the whole patient list (strict
   spelling, not a common name) → file to him, and flag **the missing slip / Docterz entry** (Shavez's list) instead of the photo.
7. **Not registered (G) — a payment gap, highlighted.** When the name matches no one in the patient list and nobody who came that week, the
   photo goes to "Not in Docterz" by itself, and the X-ray is raised as a **possible payment gap**: a red line on his console's Needs-you
   ("X-ray taken for someone not registered — no slip, no Docterz entry: N"), the same item on Shavez's list to bill or explain, and on his
   X-ray page the "Not in Docterz" tile in red with the count. Closed only by a person: billed (a slip made / registered and the photo
   filed), or explained (staff / family / free — one tap with a word).
8. **What stays on Check karein (H)** — only: two or more possible patients; name and number disagree in a way no rule settles; a day the
   clinic shows nothing (the file's date is wrong — the card says so and offers the days around it).

**Expected on today's data:** about 15 of the 25 settled by themselves (A 6, B 3, C 1, D 2, F 1–2, part of E), 2 moved to "Not in
Docterz" and raised as payment gaps, 6–8 left for a person — each with a reason that says what is unsure.

## 3 · Safety kept
Every rule needs ONE candidate and stops when a second fits; every filing is written as a "system · S7xx" answer (who and which rule —
seen on his "Filed by themselves" tile, with "Wrong patient? Move" there); nothing is deleted; the walk tests each rule on the real copy
plus made-up second namesakes. The filing itself stays with the mailbox script (the only Drive writer).

## 4 · Also in the same kit (F-1264)
The S788 lines in `check_screens.py`'s docstring that name a patient and two clinic IDs are rewritten without them; the S787 / S788 kit
papers scrubbed and their SUMS remade.

*Written at S428, 11-Nov-2026 ~09:50 IST; rule 7 widened at the owner's 09:45 word; names and IDs taken out and §0 corrected at the close.
The owner's word to build: 09:57 IST ("first, complete this X-ray and lab report section") — session 430, one kit.*
