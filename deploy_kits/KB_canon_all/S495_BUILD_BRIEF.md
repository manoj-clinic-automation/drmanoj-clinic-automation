# S495 BUILD BRIEF — the Follow-up Tracker's move to the server, session 3 of 4 — 20-Nov-2026, 20:59 → 22:1x IST (the parent, Fable)

**For you, in one paragraph.** The server's copy of your call-list engine now runs on its own Python (the same library versions as your PC) and is your PC's engine byte for byte — the one extra line it carried for the server's older Python is gone — and the server made last month's lists again from your ledgers: identical to the proof of last session on all 24 evenings. A dry run on a copy showed it would pick up today's exports correctly without touching anything live. Then, at your word, the console line you asked about: from the first server evening your command console will say "Call list: 120 of 143 due calls on the sheet — 23 wait for tomorrow"; until then it says the clinic PC makes the list. Nothing has switched: your PC still makes and sends the list. **You named the evening: Saturday 21-Nov, after your PC's 21:xx run.**

## What stands tonight (runner still OFF)
- `/root/followup_tracker/processor.py` = your PC's engine, plus one line on both machines that reports the 120-cap count (64824680 on the server and on your PC; backups beside each).
- The server's runner now uses `/root/followup_tracker/venv` (Python 3.11) — still switched off by the `OFF` file.
- Your console's work section: "Call list: the clinic PC makes it until the switch; how many fit under the 120-call cap shows here from the server's first run".
- Your PC's engine changed once by me (22:04) — the same one line; `processor.py.bak_S911_6929fc15` sits beside it.

## Saturday evening — the switch (session 4)
After your PC's 21:xx run and sends: I pack that evening's ledgers to the server and set the spare flag on your PC; **you paste one line** on the server (the seed taken again, then `OFF` removed). From Sunday's export the server makes the list; Sunday/Monday morning your console shows "server N · PC N · same". Undo at any point: the flag off your PC and `touch /root/followup_tracker/OFF`.

## Two things that went red tonight and righted themselves
- S910's first version would have compared the server's replay against a report it had itself just written — the cold reviewer caught it before the install; rebuilt and proven.
- S911's first server run stopped on a check of mine that could never pass (the test harness keeps the engine's printed lines to itself) and put everything back untouched; the check was dropped and the second run installed.

## Numbers
D1028 · A-D104, A-D105 · F-1529 – F-1532 · kits S910, S911 · session 496 reserved (THE SWITCH).
