# HANDOFF RUNBOOK — v175 · S244 close · 13-Sep-2026 IST

## §0 · WHAT HAPPENED

**One Sunday, ~09:30 → evening, in two Cowork chats at once. Eleven kits reached the repository and nine
are live, each installed by the owner from one line, each walked offline and again on the box, each with
a backup beside every file. The kit counter ran to S254 inside Session 244 — the next session is S255.**

1. **Amir's day (S244 → S246).** Step 4 had one message for a file still crossing and a file never
   made; he exported the same pair three times. Now: *processing → processing done → what is left*, and
   he is never held (D497). The bill check became one tap per bill (D498); bills from 1-Sep only, a
   flagged bill staying until he clears it (D499); *Din band* reopenable (D500). A duplicate-count defect
   in the close gate found and fixed on the way (F-461). **S246's read-back was lost across a compaction
   — re-hash `amir_day.py` at the open.**
2. **The ledger (S247).** Alisha's 25-Aug advance was falling to September because August had been
   closed on the 20th. One narrow control — *Collect against a month that is already closed* — in the
   ledger, never in the sheet (D501). Installed; the August desk read *advance ded. 5,000* the same day.
3. **Two raises (S248).** Awdhesh 10,000 → 10,500, Sandip 7,400 → 8,000 from August (D502); July is a
   test case, never reconciled (D503). The box read-back carried is SHORT — re-hash `staff_master.csv`.
4. **The second chat (S250).** `Staff Register` unmasked for Shivani, Alisha and Shavez — one mask line,
   nothing else (D496). Named at this close *S244-B — Staff Register tile for reception & Shavez (S250)*.
5. **The clinic's money (S249 → S251 → S254).** From the owner's brief in his own words: the reconciler
   with four passes and an explanation layer; the staff match card; a named checker by setting; flags that
   persist until reconciled; the owner's four flags; other UPI when ICICI is down; the float that is never
   revenue; physiotherapy as its own unit with Bhati a viewer of it alone (D504 · D505 · D507). S249 was
   refused at the currency gate because S250 had moved the grants file (F-462) — re-issued as S251, live
   13:27. Then three of his readings, each a kit within the hour: the float flow with no taps on a normal
   day (S252, D506); the match card in one plain sentence (S253, D508, with his ₹50 blood-sugar
   correction); the counter sheet readable on a phone (S254, D509).
6. **Written, not built:** the Razorpay / Yes Bank channel — Docterz's Wallet / Patient APP / Net Banking
   rows are not in the ICICI file; a payment-email relay from his Gmail and settlement recognition from
   the Yes Bank statement. Three steps, first item of S255.

**New fault codes:** F-459 … F-464 (F-460 and F-463 the assistant's). **SOP changes:** reception makes
the morning first pass on *Morning match* and answers every flag; Shavez makes the second pass, or the
only pass when reception is away; the owner opens `/finance/clinic/money` and sees four things; when
ICICI UPI is down the sheet's *Paid to another UPI* box is used; the float lives on the counter sheet
and is counted only when short. **Surveillance scope:** unchanged (no new unit, no new cron).

## §1 · MENTAL MODELS THIS SESSION EARNED

- **A published kit is frozen.** The one time it was rebuilt in place, the pin gate refused and the
  owner paid a step (F-460). The next change takes the next number, against the pin that is live.
- **Read the reserved line before minting.** Seven decisions and two findings were numbered from kit
  numbers and collided with S241 and S243 (F-463). A kit number is a kit number.
- **Name the shared file when two chats run.** `tile_grants.json` moved under S249's feet (F-462); the
  gate caught it, a re-issue cost an hour. Fold the parallel chat into the same close under a name.
- **The owner reads the screen, the assistant reads the code.** Three of his readings in one afternoon
  — friction, arithmetic, box size — each became a kit within the hour; none needed a design meeting.
- **One function per figure.** Two "our online" sums disagreed on a split-bill day (F-459).
- **Every install line carries the pull.** The deploy clone never pulls itself (F-464).

## §2 · THE LIVE BACKLOG

**Needs the owner**
1. Bhati's login at `/portal/users` — parked by him; his tile and unit rows wait.
2. Tell reception: *Morning match* every morning, answer every flag; Saturday 12-Sep's first pass is
   still open. Tell Shavez: second pass after theirs.
3. Reprint August and LOCK it — the raise and Alisha's collection are in it now. Amir's password.
4. Rotate the F-456 keys with the MyOperator rotation. Delete `/root/_retired/S243_…` after a cycle.
5. The procedure-medicine customer word in Marg.

**Claude builds next**
1. **The Razorpay / Yes Bank channel** (D507 step 1–3): stop expecting channel 4 in the ICICI file;
   the payment-email relay (Apps Script on his Gmail → `portal_payment`); Yes Bank settlement recognition.
2. Re-hash `amir_day.py` and `staff_master.csv` on the box at the open; correct the two not-pass rows.
3. Bhati's itemising (lookup, not browse) · the learning step (answered patterns become
   auto-explanations) · the physiotherapy system proper — in that order, when he asks.
4. Carried from S243: D493 phase 2 · F-458 gate improvement · F-450/F-453/F-454 pin rows · F-451 cron
   · Darpan's claim tab · Phase 3 of Book §11.4.

## §3 · INSTALL DISCIPLINE — what this session confirms

Build offline on the byte-exact live code → walk in live shape through the app's own front gate → the
installer proven on a mock four ways → the owner installs from one line → the page read back as every
role. Eleven kits; two correct refusals (F-460, F-462); zero rollbacks. `finance_app.py` is patched on
the box against a predicted md5 because F-185 keeps it out of the repository.

## §4 · THE BOUNDARY

The device shell on manojz is still dead (F-443); every file moved through the file tools. The VPS stays
his, one pasted line per change; today he installed eleven lines. Two chats at once worked, with one
cost (F-462); the cure is naming the shared file, not stopping the second chat.

---
*v175 · supersedes v174 · written at the S244 close. Next free: **D510 · F-465 · Session 255**.*
