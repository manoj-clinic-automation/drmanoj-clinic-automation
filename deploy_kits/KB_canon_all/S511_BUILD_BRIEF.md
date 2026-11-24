# S511 BUILD BRIEF — Sarvam's new model, and the first phase of the Call Console build — 24-Nov-2026 (the parent, Fable)

**For you, in one paragraph.** Sarvam's mail was about their speech-to-text model: the old one is now "legacy" and the new one, Saaras v4, costs the same. Only one program on your server sends call recordings to Sarvam, and it now asks for v4 — proven with your own key before the change was made. The call webhook (MyOperator → your server) never speaks to Sarvam, so nothing there needed an upgrade. The other Sarvam mails were a sales mail (their new chat models — not something you use) and a failed ₹2,360 top-up on 7-Nov that did not stop anything (your calls kept being transcribed and judged). Then the first phase of the Call Console build went in whole, four small pieces, none of which staff can see: your console's System section now shows one line a night about the server itself (disk, memory, load; today 28 % used, 76 GB free, 5.1 GB memory free, nothing to warn about); the transcriber stops re-trying the fourteen very short recordings it has failed on every night since July; an old one-off script holding 41 full patient numbers has left the live code folder and the nightly backup; and the follow-up tracker's program (the one that moved to your server on Saturday) is now in the nightly code backup like everything else.

## What you will see
- On your console (`https://followup.dr-manoj.in/finance/console`), open **System**: a line beginning "Server:". Amber only when the disk passes 80 %, memory drops under 1 GB, or the load stays high.
- Nothing else changes for you or the staff.

## What happens next
Tomorrow's nightly backup proves the last two pieces; then the rest of the leftovers (48 July calls, the 1,374 debris rows, a "judged within 15 minutes" watch), and the first screen of phase 1 — the staff's Call Console page — shown to you briefly before it is built.

## Your one action
None now — everything is installed. (The fixture numbers in the selftests of five live files are made-up shapes, not patients; two doubtful ones get checked and masked in a small later kit.)

## Numbers
D1057 · A-D132 – A-D135 · F-1637 – F-1641 (F-1639 open) · kits S942 – S945, all live · session 512 reserved.
