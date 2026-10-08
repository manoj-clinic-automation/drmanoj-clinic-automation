# S300 BUILD BRIEF — 07-Oct-2026 (the parent)

Session 300, one chat on 07-Oct, 12:55 pm into the evening. One kit live: S496. One more designed and final, to be built next: S497. Numbers from the board: D691 … D693; F-791 … F-798. *No patient number, no salary figure, no password and no notification topic name is written here — this file goes into the repository.*

## What you asked for, and where each stands
| what you asked | where it stands |
|---|---|
| "URGENT, BUILD TODAY" — when the bank's daily statement has not come, staff give the POS machine's UPI total on the same screen; it counts only after your confirmation | **Done and live since 1:42 pm.** Darpan has one optional box in *Kal ka hisaab*; the clinic has it on the counter sheet and the morning match. Your Confirm / Reject line is on your approvals page and on *Clinic money*. The bank's statement replaces the figure by itself. **Nobody has needed it yet:** the bank's statements for 6 Oct came in 14 minutes after the install. |
| Staff are not getting the notifications you get; make WhatsApp alerts loud on their mobiles and PCs; add the set-up to the Clinic PCs tile. "For now … the staff mobiles only and park this build" | **Mobiles: done by you** with the message I gave you. **The loud-alerts build is parked** and kept in my memory with the two topics. I will not raise it; you will. |
| After a call, staff tap "Appointment book ho gaya" and then see nothing. They need a list: whose appointment, booked by whom, at what time | **Designed and final; not built yet.** You saw the table mock-up and made three changes: full mobile numbers, weekdays in English, room left for a WhatsApp appointment message. You said "it is final … to build in fresh chat". It is the first job of the next chat. |
| "Now, right below what all needs to be done or built now" | Given at 2:01 pm. You have not picked between Voicenotes by itself, the renewal reminders and the scan app. I ask once, after the after-call list is in your hands. |

## What needs you
1. **One double-click — the publish.** Today's record only; nothing changes on the server.

```
D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat
```

2. **Open a fresh chat in this project and say "start".** It builds the after-call list from your final mock-up and shows you the real screens before anything is installed.

3. **When a POS figure is typed, your Confirm line appears here** (nothing is waiting now):

```
https://followup.dr-manoj.in/finance/approvals
```

4. **Everything else is on your board**, short, in order.

```
https://claude.ai/artifact/EtwtRpK4nAbmY98KB4yijk
```

## The after-call list, as it will be built
- **A tile "Call ke baad"** for the staff who hold Call Tracker, and for you.
- **One table in three parts.** *Nahi aaye* on top — booked, and Docterz shows no visit; a row stays until the patient comes or staff press *Phir call kiya — naya din* or *Ab nahi aayenge*. *Aane baaki* — the day has not come. *Aa gaye* — filled by itself from the Docterz export; nobody ticks anything.
- **One new optional tap on the card after the call:** *Kis din aayenge?* — Aaj · Kal · Parso · Aur din. Without a day, a patient counts as not come after 3 days.
- **Full mobile numbers; weekdays in English.**
- **WhatsApp appointment message:** a place is kept for it, switched off. Nothing is sent until you ask for it.
- **Installed switched off for staff.** You turn it on from the page.

## Good to know
- **The POS box is shown to staff only after 10:00 am** on the next morning, and only while the bank's statement is missing. You can change that time, and the ₹100 tolerance, on *Clinic money* and on your approvals page.
- **NK Pathology has no daily page**, so its POS figure is typed by you on *Clinic money*.
- **Until you confirm a figure, the day reads exactly as before.** After, it says *provisional — POS total, bank not in*.
- **Your console shows the new flag as "pos diff"** if a confirmed figure and the bank differ by more than the tolerance. Proper words for it come with the console's small job.
- **The staff's lists after their first day were not read today.** Tell me what the staff said when you can.

## What went wrong on my side
- **I wrote clock times from memory instead of reading the clock** — on the board and in two messages to you, wrong by up to an hour and a half. I corrected them on the board and told you. Nothing was installed on a wrong time.
- A test file of mine was wiped by my own edit script and had to be written again before the kit was placed.
- My first draft of the shared lookup wrote to the database when it should only read. Found and mended before the kit was placed.

## Waiting on your word (you said "later")
The staff's loud alerts (parked) · the WhatsApp appointment message to patients · the follow-up tracker on the server ("ask next week") · the MyOperator key · contacts · the mail flood · the portal tiles · Tailscale.
