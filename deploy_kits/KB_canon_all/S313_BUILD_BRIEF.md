# S313 BUILD BRIEF — the parent, 13 → 14-Oct-2026

*The one paper for Dr Manoj. Plain English. What you asked, what came of it, what the next chat does first, and what needs you.*

## What you asked, and what came of it

| you asked | what happened |
|---|---|
| "Split" off every page (12-Oct preview approved, then *"everywhere this part of split bill does not come"*) | **Live 08:05, 13-Oct.** The day page, month table, day PDF, accountants' pack and Morning match show each line as it was paid. A booked visit's procedure line is no longer counted as Razorpay money. |
| The command console showed no amounts, and stale messages after a refresh | **Live 08:05, 13-Oct.** It reads Docterz's own day total and refreshes when you open it or come back to it. |
| **URGENT:** the WhatsApp alerts on the staff phones had stopped since 7-Oct | **Live 19:27, 13-Oct.** The old notifier had frozen on a Google sheet while it still looked "running". The alert is now made by the server itself the moment a message arrives, with retries and a warning if it ever fails. Your test alert came. |
| Use the $200 API credits (until 17-Oct) for the builds | A build runner on your PC now uses them. It costs about $4–7 per build. The credits do not cover Claude Code (your forwarded mail; my first answer was wrong). |
| Bhati's physiotherapy register | **Live 05:29, 14-Oct**, and you opened it for him. Clinic slips (₹250) are matched with reception's daily totals, and differences are flagged. Home visits (₹500) are in a separate report and never in the accountants' income. You get day-, patient- and month-wise reports. |
| His daily slip entry on his duty list; the old overlapping line off | **Live 05:59.** The old line was switched off at your "yes". |
| He backfills from 1st October | **Live 07:04.** Every day from 1-Oct can be entered and is matched. |
| The after-call list: patients who register under another number, and an IVR call button for no-shows | Analysed; nothing built yet. Your answers: **any staff may link · the second number is remembered.** It is the next chat's first job (below). |

## What the next chat does first

**S558 — the after-call list.**
- Staff link a no-show to the patient who came under another number (suggestions plus a search; undo the same day). The list then shows *Aa gaye*, and the next call from that number shows the patient as known.
- Each no-show gets an **IVR call** button: your staff member's phone rings first, then the patient is joined, as in the Callback Tracker.
- Both come in switched off. You see them on the page and switch them on.
- It is one line from you on your PC, built on the API credits.

## What needs you

1. **Publish** — one double-click: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (this record and the S558 brief; nothing changes on the server).
2. **The packs page** — name the 25 card shops, and type the card and ICICI statement passwords: `https://followup.dr-manoj.in/finance/packs`
3. In the next chat: the one runner line for S558, and switching its two features on after you have seen them.

## What went wrong on my side

- I said your API credits would pay for Claude Code. They don't; your mail showed it, and the builds moved to the runner the same hour.
- The WhatsApp notifier had been silently stuck for six days, because the watchdog only checked that it was "running". That kind of check is now the rule: a job is watched by what it produces.

*S313 · written at the close, 14-Oct-2026.*
