# S334 BUILD BRIEF — the Sanjeevni chat · 20-Oct-2026 14:53 IST → 22-Oct-2026 05:45 IST

*The one paper for the next chat (session 335) and for you. Plain words; the detail is in the Archive §S334 and the Book §15S.*

## What you asked

On 20-Oct you reported four things on the purchase-orders page. The printed order sheet carried Yuvika goods that were not on Darpan's sheet. Alisha said the WhatsApp went by itself when she opened the page. Some distributors got the WhatsApp more than once. And the Call screen was gone, leaving only *Maal aaya*.

## What we found

- **The Yuvika lines** came from the system's own orthotic list. It was added to Darpan's order on its own: on reception's card, in "Sab ko WhatsApp bhejo" and on the printed sheet. Both lines were wrong. The system had Ankle Binder M at −1 (Marg has 1), and Rib Belt at 1 (Marg has 2).
- **The "automatic" WhatsApp:** Alisha tapped "Sab ko WhatsApp bhejo" once, at 12:43. The reception phone sends only while it is unlocked, so the messages went from 13:25, when someone unlocked it.
- **Repeats:** each supplier got one message on 20-Oct. The repeats on record are from 12-Oct. The server handed a message to the phone again every 10 minutes whenever the phone's "done" did not come back. A.A., Deepam and Gunina got that day's order at least twice.
- **The Call screen** was hidden once every supplier had been sent a WhatsApp.

## What is done

- **Your rule (D749):** the system's orthotic list goes to Yuvika only after Darpan says yes on his Kal ka hisaab, and only the lines he keeps.
- **Your mock-up, approved in three steps:** Darpan's section, the "WhatsApp bhejna hai?" screen, the call row, and the numbers beside every dealer and on both printed sheets.
- **The build (S605), by your API credits ($32.04), live 18:45 IST 20-Oct:**
  - Darpan's yes or no on the orthotic list.
  - One WhatsApp per order: the phone gets each message once, and you get one line if the phone never confirms it.
  - "Sab ko WhatsApp bhejo" now asks once.
  - "Aaj ke order — call karo" stays on reception's home.
  - Call and WhatsApp numbers on the screens and both PDFs.
  - The orthotic sizes now keep their own stock code in the spine.
  - Two older tests now use their own test days.
- **The night bundle of 22-Oct confirms every file** of the last two builds (13 of 13).

## What went wrong on my side

The build used the first version of my instructions, not the corrected one (F-963). Three things follow:
- The orthotic sizes change went in early. Its checks passed and no other item moved.
- The old Purchase orders page still has its own "Yuvika ko order bhejo" button. Only you and Shavez can reach that page.
- The call row's count includes orders that have already arrived.

Nothing on Darpan's or reception's flow is unsafe, and all three go into the next small build. From now on the instructions are read back on your PC before you get the line.

## What comes next

1. **One small build:**
   - the orthotic sizes on the stock reports;
   - the old page's Yuvika button;
   - the call row's count;
   - the last of the older tests.
2. **From Sunday 25-Oct:** the buying model (Kit II), then the plan's remaining steps.

## Your actions now

1. **The publish** of this record, one double-click on your PC:

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Lock September** with the FINALISE button on its month page, still open:

```
https://followup.dr-manoj.in/finance/purchase/page/month/2026-09
```

*S334 · 22-Oct-2026 · the Sanjeevni chat.*
