# S300_ATTENDANCE_AND_OPENING

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S300_ATTENDANCE_AND_OPENING/install_S300_ATTENDANCE_AND_OPENING.sh
```

## What it gives, in the owner's words of 17-Sep-2026 evening

1. **Staff page (Meri attendance), Hinglish, tap only.**
   - *Mujhe present lagao*: the reason is tapped from five choices — machine did not read the finger · machine off · out on clinic work · forgot to punch · other (told reception). Typing is refused. The doctors read the reason in English on the review page.
   - *Mark my exit* is now **Mark overtime**: two buttons, **Told Dr Bhawna** and **Told Dr Manoj**. One tap; the time of the tap is the punch-out once the doctor approves. The review card is called *Overtime requests*.
   - The *My month* link is gone. The page stays today only (past days: not needed).
2. **Petty book — Manoj Bhati's opening balance.** On the doctors' page (English) two new sections: *Bhati's cash* and *Bhati's loan*, each with its opening figure (what he held / already owed when the book started), set or corrected by Dr Manoj or Dr Bhawna, every change audited. Both are added into his in-hand and loan figures. Bhati sees them on his page and cannot change them.

`https://followup.dr-manoj.in/finance/petty` · `https://followup.dr-manoj.in/register/me`

## Proof

- `staff_register.py --selftest` — green, with the S300 checks; four negative controls each turn it red (typed reason accepted · reception offered · old reason accepted · My month link back).
- `walk_s300.py` — the live finance app files + this petty_book over a scratch copy of finance.db: 103 checks (the S289 walk's 70 unchanged + 33 opening checks). Negative controls red: the S289 file (68), opening not added (79), keeper allowed to set (71).
- `walk_sr_s300.py` — this staff_register over a scratch copy of the live staff_register.db: every mapped staff login's page, refusals write nothing, the doctor's pages 200. The S289 file turns it red.
- The installer runs all of it **on the box** before placing anything and restores both files on any red after placing.
