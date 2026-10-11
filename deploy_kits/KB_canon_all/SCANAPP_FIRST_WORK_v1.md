# SCAN APP — FIRST WORK — v1 — what the scan-app project's first session does

*Written at S305 (the parent), 11-Oct-2026, with the starter pack. For the scan-app project's first session only; from
its close on, that project's own build brief replaces this file.*

## 0 · The open

Run Phase 0 of `SCANAPP_START_HERE_PROMPT_v1.md` (§4) — the session number from the board first. Then read
`SCANAPP_SYSTEM_BOOK_v1.md` whole; it is short. Read `asset_register.py` and `clinic_papers.py` from the newest bundle
and hash them against their pins before any design.

## 1 · The owner's two asks, in his order (D689, 07-Oct-2026)

**1 — Four new sections on the papers page:** *Resumes* · *Miscellaneous documents* · *Construction work* · *Personal*.
(He asked whether a Personal section existed: it does not — *Dr MK expense* is the nearest. Tell him so in one line if
he asks again.)

**2 — The challan flow.** Suppliers send goods on a challan and the bill later. A challan is kept as *goods received,
bill awaited*; when its bill is scanned it is joined to the bill; *"shd be able to delete challans when the bills
come."* **Medicine suppliers' challans are the Sanjeevni chat's side** — the scan app sends them down the pharmacy lane
marked as challans and tells that chat; it does not reconcile them with Marg.

## 2 · How to do it — mock-up first, then one kit each

1. **A mock-up he can look at and edit** (an artifact; reads only; no live data, made-up rows): where the four sections
   sit on the papers page and how a paper reaches each one; the challan's life — scanned as a challan at intake (one
   choice, no extra tap for staff when it is a plain bill), the *bill awaited* list with its age, the suggestion when the
   bill arrives (same supplier, near date and amount), the one tap that joins them, and the delete. Put to him only what
   he can see — the names, the place, the wording — never a technical choice (decide those and say them in one line).
2. **His word on the mock-up → one kit for the sections, one for the challan flow**, each by `BUILD_NORM_v1.md`, each
   switched off for staff until he turns it on if it changes a staff screen.
3. **Decided here, not asked (the assistant's call, stated in one line when building):** the sections are kept as data
   on the bill's row like D664's groups (no new database file); a deleted challan keeps its stamp number reserved and
   its file in the nightly backup's retention, so a delete is never the loss of the only copy of a paper; the challan
   suggestion never joins by itself — a person taps.
4. **Before the challan kit:** a PLANNED line on the board for any shared file; one line to the Sanjeevni chat on the
   board about the pharmacy-lane challans (D646, and his rule that overlapping builds are known both ways).

## 3 · In the background, no word needed

- A warranty date offered from the scan's reading on a Dr MK expense (S466 left it to a person).
- The scan app's pins held against each nightly bundle at every open (§4 step 5 of the prompt).

## 4 · Not to be raised

- The clinic / MK expense split (D664) — his, *"overlapping category, so not finalised yet"*; never guessed.
- Anything the owner has parked in the parent project (the staff's loud WhatsApp alerts; the mailbox clean-up).

---
*SCANAPP_FIRST_WORK — v1 · S305 (the parent), 11-Oct-2026.*
