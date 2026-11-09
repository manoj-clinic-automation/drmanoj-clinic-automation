# S762_STAFF_CARDS_R2 — staff cards, round 2 · the parent · session 415 · 09-Nov-2026

**For the owner, in two lines.** On your Call Console, a call missed before a phone staff member punches in now counts on her card, marked "before punch-in". A call missed while two people were answering for it shows once, on a "Both on duty" line, and still appears on each person's own card. Staff now see "aaj abhi tak: N log" on their folded *Mere calls* line.

## The owner's rulings (09-Nov)
- **09:27 IST.** Your console keeps Today. The staff card keeps Kal, with the Aaj and 7 din tabs (his word at 09:32: do not block the current day).
- **09:27 IST, (a).** A call missed before punch-in counts on that person's card.
- **09:27 IST, (b).** A call missed while both are on duty shows once on his page, and each person sees it in her own workflow.
- **09:46 IST.** Yes to today's net missed on the staff's folded line.

## Decisions made in the build
- **"Before punch-in"** means she punched in later that same day, or it is today and she has not punched yet. A past day with no punch at all is not hers.
- **Covering colleague.** A miss before her punch-in, while a colleague was covering (on duty by his punch), is answered for by two people. It goes on the shared line the same way.
- **The shared line** has Call back and the recording only. Review buttons stay on each person's own calls.
- **Agreeing words.** A verdict "Mismatch" between the same English words, or between "to the doctor" and "coming" / "booked", now counts as agreed. The live 7 days held 7 of Shivani's 9 like this.
- **Plain words.** Outcome codes the live read found raw (UNCLEAR, resolved_on_call, in_enquiry_only, on_medication, in_will_come…) now read as words. Any future code reads with its underscores turned to spaces.
- **Order.** Every list on every card is newest first.
- **Links.** Each person's card has a link to her own card (`/finance/aaj?as=<name>`), and there is a "staff cards ↓" jump link.
- **"Call ke baad"** stays: it is the name you use.

## Files
| live file | FROM | TO |
|---|---|---|
| `/root/portal/calls_console.py` | f233b851 (S748) | see TO_MD5.txt |
| `/root/finance/aaj_kaam.html` | 791fbf8b (S748) | see TO_MD5.txt |

## Proven (S415, made-up data only)
- `walk_s762.py`: 36 of 36, with the control on the live page 28 red. Cold review R1 found 1 must-fix (an unreadable punch log charged both phone staff) and 6 should-fix; all built. R2: SAFE TO INSTALL; its 3 should-fix built.
- S745's, S747's and S748's walks on the new page are red only where `EXPECTED_REDS.txt` names. Those are the counts the rulings change on purpose.
- Browser walk at 1366 and 390 px: 18 of 18, with the control red.
- The installer was rehearsed on a made-up root: DRY, install, already installed, undo, changed-live STOP, and a forced red that restores.

## Install (after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s762kit && cp -rp /root/deploy/repo/deploy_kits/S762_STAFF_CARDS_R2 /tmp/s762kit && bash /tmp/s762kit/install_S762_STAFF_CARDS_R2.sh
```
## Undo
```
bash /tmp/s762kit/install_S762_STAFF_CARDS_R2.sh --undo
```
