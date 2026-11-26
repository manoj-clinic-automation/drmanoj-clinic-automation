# S523 — what changed for you (26-Nov-2026, the parent)

**Only the attendance machine can now put a punch into attendance (live 09:40).** Until today the server accepted a punch from anyone who could reach it, and a punch feeds the register and the month's salary. Now it accepts a punch only when it carries the machine's own serial mark — every real punch in the last 45 days carried it. A punch without it is not stored and not lost: it is kept aside in its own file, and the health page's line **"punch door"** turns red (the hourly health alert names it). If that ever happens, tell me — I read what came and, if it was genuine (for example a replaced machine), take it back in.

**Who is on duty now comes from the punches.** Punched in today = on duty for the shift; a punch at least two hours after the first = gone. If nobody at all has punched by 09:30, or the machine stops talking to the server, the duty roster stands in — but never on a day the staff register marks the clinic closed. The staff call-back reminders follow this.

**One small leak closed:** the machine's serial had been going out every night in a backup copy; from today it goes out as its length only. The older copies stay in your private stores (Drive, the SSD) — nothing for you to do.

**The first install stopped itself** at its own check (my test had read the clinic's real staff list on the server); I fixed the test and the second run went in.

**Next session:** staff WhatsApp replies from their Call Console (B2, with your Accept button's label); then the new-number screen for your look.

**Waiting on you:** the publish of these records: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`. Still open from before: the packs page (the 25 card shops; the card and ICICI passwords).
