# S747_CALLS_REVIEW_CARDS — your review buttons, each person's own call card, the reception mobile · the parent · session 400 · 07-Nov-2026

**For the owner, in three lines.** On the Call Console, every call behind a staff figure now has your buttons (*Ask to log · Mark reviewed · Staff right · AI right · Note to staff*). It also shows its log line, its recording and its transcript, which opens in place. Each person sees their own card in Hindi on *Aaj ka kaam*: the same figures, every call they handled with its recording (staff never see transcript text — the owner, 09:23 IST), your asks and notes, and a *Galat hai?* tap that sends you one line, which you *Accept* or say *It stands* to. A call on the reception mobile counts to the phone staff member on duty at that minute.

## Why
D856 (Build B part 2), on the owner's mock-up https://claude.ai/artifact/LNNtTvacjz3v9Nf77sJfhB (v2). He asked at 08:52 IST on 07-Nov: "All transcripts should be available here inline, expandable as in the call console, all logs already." F-1168: the Reception mobile card could not count missed calls, because the reception line was not credited to the person on duty.

## Files
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/calls_console.py` | 40200409 (S745) | df484c7d | the review buttons and their store; the disputes; the staff routes (`/portal/console/api/mycard`, `myrec/<jk>`, `dispute` behind the portal's login; `card/<login>`, `review2`, `dispute-answer` behind the doctor gate); the reception credit |
| `/root/finance/aaj_kaam.html` | 9f8fb9df | dc684e46 | *Mere calls*: the person's own card (read per request, no restart) |
| `/root/state_backup/clinic_state_backup.py` | 37ed5524 (S719) | fd1647de | one line: the review store in the encrypted nightly |
| `/root/portal/call_review.db` | — | new | made empty by the installer **before** the backup line is placed; `chmod 600` |

Settings, none required: `PORTAL_CALL_REVIEW_DB` (default `/root/portal/call_review.db`), `PORTAL_RECEPTION_AGENT` (default `reception`, the agent's first word), `PORTAL_CARD_LOGINS` (`login:key,...`; default: the login's first word).

## Proven (S400, made-up data only)
`walk_s747.py`: **98 of 98** (S745's 71 checks, plus X1–X5 for the reception mobile, V1–V8 for the review buttons, Q1–Q14 for the staff routes; Q2 and Q3 prove staff get the recording of their own calls and no transcript text). The control on the live page turns 26 of 27 new checks red and keeps the 71 earlier ones green. An independent cold review found the kit SAFE TO INSTALL. Its three should-fix items are built: a login that is not exactly a first name reads no card; a first name two agents share gives no card; a failed backup preflight puts all three files back; and the checks behind a transcript or a dispute reuse a card made in the last minute. `walk_s745.py` on the new page: 71 of 71. `browser_s747.js` (Chromium, 1366 and 390 px): **28 of 28**; the control on the live staff page goes red. The installer runs the walks, the control and a read-only proof on the live stores (`proof_s747.py`, counts only) before writing anything. The proof checks that the call figures, the follow-ups and Call ke baad are identical, that each call total across the cards is the same, that missed calls and WhatsApps per person are identical, and that each phone staff member's own card equals the owner's. It also prints the agents' first words (F-1168).

## Install (after the publish; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s747kit && cp -rp /root/deploy/repo/deploy_kits/S747_CALLS_REVIEW_CARDS /tmp/s747kit && bash /tmp/s747kit/install_S747_CALLS_REVIEW_CARDS.sh
```
## Undo
```
bash /tmp/s747kit/install_S747_CALLS_REVIEW_CARDS.sh --undo
```
