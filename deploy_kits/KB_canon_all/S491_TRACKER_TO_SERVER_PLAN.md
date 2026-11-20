# S491 — THE FOLLOW-UP TRACKER MOVES TO THE SERVER — THE PLAN (19-Nov-2026, the parent)

*For the owner's OK. Nothing is built before it (D1021). Counts only; no patient detail. Follows S443 §7 (which wins over §5), S442's findings, S287's proven replay method, and his rulings in memory (flow and display identical for staff; exports by the server path; F-1503 — the follow-up log is the source of dates).*

## What moves
The tracker's engine — the PC's own `processor.py`, byte for byte, with S892's "follow-up log alone" rule and the doctor-off-day rule — runs on the server instead of on manojz. It runs within minutes of each Docterz export arriving, every day, whether or not he is sitting. Its twelve data files move with it, seeded once from the PC.

It keeps making everything the PC makes today: the day's call list (`Staff_Action_Today`), the visit ledger and patient master, the Day Revenue tab and `Day_Tenders.csv`, the 08:00 Patient_Master mirror. At 9:45 pm, if either evening report has not arrived, he gets one push (S443 §7.2).

## What stays IDENTICAL for staff
The Call Console, its rows and sections, its Hindi, the ladder, the Callback Tracker's tab, the timings. They read the same workbook they read now — it is simply made on the server. Staff are told nothing because nothing they see changes.

## How the two evening exports reach the server
They already do: reception's consultation report and follow-up log land on the server first. Today the PC fetches them back, runs, and sends the list up again. After the move that round trip ends — the server runs on them where they land. His own Clinical data report pickup is untouched.

## The proof before any switch — the replay
The past month's evenings archived in `D:\Downloads\DocterzArchive` (about 22 consultation evenings, 24 follow-up logs) are replayed with the server's code, each from the PC's own before-run snapshot, on his own machine (patient files never leave it). Pass: every evening's list identical, cell for cell, to what the PC made that evening; the data files identical apart from the input file's name. Any difference is explained and fixed before the switch.

## One switch
One evening, after the PC's own run, its data files go to the server once; from the next export the server makes the list. The PC's task stays installed and keeps making its list quietly as the spare — it feeds nothing. If both ever send, his console shows it in red. Next morning: the call list is checked against the PC's spare.

## Nothing deleted
The PC tracker, its data and the manual way all stay. Undo = the PC sends again.

F-1316 closes here.

## Size
About three sessions: (1) the replay and the server kit; (2) the install and the switch evening; (3) the next-day check and a week's quiet watch, then the record.

## What he does
Says OK. Adds one folder to this chat in the Claude app: `C:\followup_tracker_local_test_kit` (the replay needs the PC's before-run snapshots). Nothing else.
