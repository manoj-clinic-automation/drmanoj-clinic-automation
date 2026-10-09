# S302 BUILD BRIEF — 08 → 09-Oct-2026 (the parent)

Session 302, one chat from 5:56 am on 8 Oct to the close on the morning of 9 Oct. Two kits live: S497 (the after-call list) and S499 (the pen-drive backup). Numbers from the board: D696 … D698; F-806 … F-811. *No patient number, no salary figure, no password and no notification topic name is written here — this file goes into the repository.*

## What you asked for, and where each stands
| what you asked | where it stands |
|---|---|
| "the pharmacy PC pen drive mark backup issue you need to find out and correct it" | **Found and corrected; live since your double-click on 8 Oct (its own report of 6:40 pm confirms it).** The backup on the pen drive was made only when someone said *Yes* to Marg's prompt on closing — nobody's duty. Marg's own automatic backup never reached the pen drive. Now the pharmacy PC copies it there every hour, and its report says truthfully how old each copy is. It shouts only if the pen drive has had no backup at all for 3 days. The "prune is not working" warning you have seen for two weeks was false — gone. |
| — and one thing it found | **The automatic backup and the hand-made one are not the same file** (34 parts against 29). Until the Marg engineer has tried restoring the automatic one, **keep a hand-made backup onto the pen drive about once a week.** |
| The after-call list, built from your final mock-up | **Live since 2:36 pm 8 Oct; you switched it on at about 2:39 pm.** Alisha, Reception, Shavez and Shivani have the tile *Call ke baad*. Nothing older than the day you switched it on is shown. A patient is marked *Nahi aaye* only after the Docterz export has reached that day, so nobody is called absent the day they came. |
| The medical PC .bat — "do it yourself", G: not visible in your Remote Desktop | Sent to `D:\SendToClinic\_s499\` on that PC through its own delivery channel; you double-clicked it there. |
| The X-ray upload shortcut on the reception PC is gone — "Do the needful" | **Put back at 8:42 pm 8 Oct.** Made in a way Windows does not clear away when Google Drive is briefly missing (the likely cause). |
| The daily health mails — you delete them yourself | Noted for good. The night check no longer reports mails in Trash. |
| Your hold — nothing new built before Saturday 10 Oct, 10:30 pm | **Honoured.** The next builds wait for it. |

## What needs you
1. **One double-click — the publish.** Today's record only; nothing changes on the server.

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Ask the Marg engineer to test-restore Marg's automatic backup** (from `D:\MARGERP\serverbackup` or the pen drive's `MargAuto_by_agent` folder) on a spare PC. Until then, a hand-made backup onto the pen drive about weekly.
3. **Tell me what the staff say** about their lists and the after-call list:

```
https://followup.dr-manoj.in/portal/ring/list
```

4. **Everything else is on your board**, short, in order.

```
https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk
```

## Next — after Saturday 10:30 pm, in this order
1. **Reception's missing tiles** — Docterz collection, Morning match, *Check karein*; Morning match lists every October day still waiting, oldest first; its verdict names only what has actually answered.
2. **Your console's small fixes** — it follows your panel, shows tasks, says how fresh it is, and words the new POS flag.
3. **Your three picks:** renewal reminders 45 days ahead (ends the arms-licence false red) · Voicenotes into the task section · the scan app as its own project.
4. **Before October's salary:** the one-button skipped loan month and the sheet fixes.

## What went wrong on my side
- **My first build of the after-call list** would have shown staff old bookings from 27 Sep and called yesterday's patient absent until the evening export. A fresh check caught both; fixed before you saw anything.
- **A check I ran on your PC** left a stray file in my own working space (not on your disk). Rule written so it does not recur.

## Waiting on your word (you said "later")
The staff's loud alerts (parked — stays parked) · the WhatsApp appointment message to patients · the follow-up tracker on the server (I ask once next week) · the MyOperator key · contacts · the mail flood · the portal tiles · Tailscale.
