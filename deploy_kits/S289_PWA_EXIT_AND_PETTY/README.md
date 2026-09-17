# S289_PWA_EXIT_AND_PETTY

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S289_PWA_EXIT_AND_PETTY/install_S289_PWA_EXIT_AND_PETTY.sh
```

## What it gives, in the owner's words of 17-Sep-2026

1. **Staff: "Mark my exit".** On the staff page, after their shift end, a staff member who punched in can tap *Mark my exit* at the moment of leaving: why (tap), who they told (tap). The server's clock is the punch-out. The doctor approves on the Staff Register review page — at once or later, no deadline. Approved exits count in the month report as a punch-out (the out-time carries a `*`). The staff page stays **today only**.
2. **Manoj Bhati: the petty book (Hinglish, tap only).** `https://followup.dr-manoj.in/finance/petty`
   - available today / tomorrow;
   - money in hand, what he should hold (Rs 10,000) and what he needs;
   - "paise mile" from Dr Manoj / Dr Bhawna (the doctor confirms with one tap);
   - Darpan's and Shavez's diaries topped up (Rs 3,000 each), diary-page photo;
   - renovation: Hari Om Ji · Nanne · Bhavani · Ilyas · Mittal Electric · Raja · cartage · *koi aur* (the only typing);
   - Rahul, social media manager, Rs 5,000 pre-filled, month paid / not paid;
   - his own loan (taken / repaid), kept apart from spending, OK'd by a doctor;
   - the physiotherapy tick: reception's entry is right.
3. **The doctors' check page (English)** at the same address: Bhati today · what needs a tap · the three (holds, last top-up, last count, "Counted — matches" or the shortfall) · Bhati's loan · payments by payee this month and all time · every entry with its photo, cancellable.
4. **Reception** (Shavez, Shivani, Alisha): tile *Bhati aaj* — one line, nothing else.

Separate from Sanjeevni and clinic money: its own tables (`petty_*`), its own server unit (`petty`); the walk proves no Sanjeevni or clinic table moves when it writes.

## The owner's one action after install

Create Manoj Bhati's login in **Manage Users** on the portal: username `bhati`, role `staff` (or `manager` — his tiles are the same two either way), a password of your choosing.

## Proof

- `staff_register.py --selftest` — the S289 block: shift-end opening + fallback + roster OFF, tap-only choices, server-time punch-out, one per day, in-punch or present request required, verify optional, doctor decides from pending, approved exit = punch, audited. Negative control: removing the too-early guard turns it red.
- `att_month_report.py --selftest` — approved exit = punch-out, OT candidate, `*` on the out-time, pending changes nothing, pre-S289 register DB reads empty. Negative control: not folding the exits turns it red.
- `walk_s289.py` — the real patched `finance_app.py` over a scratch copy of the real `finance.db`: 70 checks (gate, every role, arithmetic, photo, confirm/OK/count rules, independence, the rest of the app still 200). Negative controls: a wrong balance formula (red at 37), the unpatched app (red at 1).
- The installer runs all three **on the box** before placing anything, and restores every file on any red after placing.

## Known and accepted

- Photos are kept at `/root/finance/petty_uploads/`; the nightly code and database bundles do not carry that folder (entries are in `finance.db`, which is backed up). Named at the close as a gap to close.
- A phone photo larger than the web server's upload limit is refused by the server with an error page; the entry is not saved and can be retaken.
