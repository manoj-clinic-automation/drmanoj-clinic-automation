# S508 BUILD BRIEF — the Sanjeevni chat, 23-Nov-2026 evening (for Dr Manoj)

**What changed (two kits, both live)**

- **WhatsApp all works again (S937, 17:42).** Today's orders did not go out because one dealer's name had "&" in it (RADHA MEDICAL & SCIENTIFIC). The confirm screen then refused every press and reloaded, so nothing reached the reception phone. The phone itself was fine. Reception phoned all eight dealers at 17:22. The list now goes through with any name.
- **The order sheet is one tap from your tile.** Your Purchase orders page has a blue **"Today's order sheet — Print · WhatsApp →"** button at the top, there all day, also after everything is ordered.
- **An accidental "Out of stock" tap can be taken back (S938, 18:23).** Under reception's red box: today's taps, each with **Undo** (two taps). On your page: **"Tapped by mistake — put back"**. Once you have given your word on a tap, staff cannot undo it. Alisha's ten taps of 17:22 – 17:24 are back in the red box, LANZOL JUNIOR included.

**Checked before install:** both changes walked on a copy of the database (the old files fail the checks), installers rehearsed with an undo and a forced failure. No separate review this time (small changes); the next build gets one.

**The new order flow — your mock-up OK, built next session**
Darpan makes the list final after deciding the old lines; reception can only send a line up to him; WhatsApp all opens only after that; each dealer keeps "WhatsApp sent 13:10" until the goods come; messages to you, Darpan and reception at each step, each opening its page. The four suggested extras (late, reminders, 20:00 summary, wrong bill) wait for your yes or no.

**The mock-up:**
```
https://claude.ai/artifact/4zjaEK7xSi91y8e9kGVjWG
```
**Your Purchase orders page:**
```
https://followup.dr-manoj.in/finance/porders/flow
```
**Publish:**
```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```
on manojz — nothing follows it.
