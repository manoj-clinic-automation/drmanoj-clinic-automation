# S818_WA_AWAITING_CHATS — WhatsApp awaiting, judged per chat · the parent · session 447 · 13-Nov-2026

**For the owner, in two lines.** Your Call Console gets a WhatsApp block: **"Awaiting a reply · N chats"**, one line per chat, each with Reply · Call · **Done — no reply needed** · **Not a patient**, and under them "Answered today", and the two undo lists. A chat you have answered no longer shows as awaiting — not when the sender then writes "ok", not when the reply went out after midnight, not when MyOperator never sent the "delivered" tick.

**Goes on top of S817_CALLS_FOLLOWUP_LINES. S817 must be installed first** — the installer checks it and says so.

**F-1323.** The page judged every incoming MESSAGE alone; a message counted as answered only by a later reply whose status had reached "delivered"; and only the messages of the page's own days were read. So an answered chat still read "awaiting" when (1) the sender wrote again after the reply ("ok", thanks); (2) the reply fell on the other side of midnight; (3) the reply stayed at "sent" in the store — the Inbox writes "sent" when MyOperator accepts a message and "delivered" only when a status ping arrives, and the pings are not arriving.

## What you approved, and how each is built
| approved | built |
|---|---|
| a. Awaiting is judged per CHAT. A chat awaits only while the last word is the sender's and nothing went back since: a reply MyOperator ACCEPTED (sent / delivered / read; not failed, not queued) or an answered call as today's rule has it | `wa_chat()` — the one place. A reply counts when its status is `sent`, `delivered` or `read` and it is OUR reply (`wa_is_reply()`, below) — never a template or an automatic message; `failed`, `retrying`, `unsure` ("may have gone") and `pending` (test mode) never count. The call rule is D820's — answered, 30 s or more spoken, within 2 clinic hours — measured from the sender's LAST message before the call |
| b. "ok / thanks / a greeting" after our reply does not reopen; anything else does; when in doubt it reopens. Ruled 13-Nov: the same after a template | `wa_is_ack()` and the lists `WA_ACK_PHRASES`, `WA_ACK_HONORIFICS`, `WA_ACK_EMOJI` — one place in the code (below) |
| c. Midnight does not cut a chat; the look-back is bounded | the chat is read **7 days** before the page's days and every day after them up to today (`WA_BACK_DAYS`, `wa_load()`) |
| d. Two buttons, doctor only, with an undo list each | the block; the door `POST /portal/console/api/wa-mark`; the store `/root/portal/wa_awaiting.db` |
| e. The same rule wherever the figure is shown; nothing new on a staff screen | every reader below goes through `wa_chat()`; no word or control is added to any staff screen |

## The acknowledgement list, exactly as built
A message is a **bare acknowledgement** only when it is typed text (never a photo, a voice note, a file or a sticker), 40 letters or fewer, and — with the honorifics set aside — it is **one to three of these phrases and nothing else**, or **nothing but emoji of the short list**:
- **ok:** ok · okay · okk · okey · oky · k · kk · ओके · ओक
- **thanks:** thanks · thank you · thankyou · thank u · thanku · thanx · thnx · thx · tq · ty · thanks a lot · thank you so much · thank you very much · dhanyawad · dhanyavad · dhanyabad · bahut dhanyawad · shukriya · bahut shukriya · धन्यवाद · बहुत धन्यवाद · शुक्रिया · थैंक्यू · थैंक यू · थैंक्स
- **alright:** theek hai · thik hai · theek h · thik h · theek · thik · accha · acha · achha · ठीक है · ठीक · अच्छा
- **a greeting:** hi · hii · hello · hey · namaste · namaskar · pranam · good morning · good afternoon · good evening · good night · gm · gn · ram ram · radhe radhe · jai shri krishna · jai shri ram · salam · salaam · assalamualaikum · नमस्ते · नमस्कार · प्रणाम · राम राम · राधे राधे · जय श्री कृष्ण · जय श्री राम · सलाम
- **honorifics set aside:** ji · jee · sir · doctor · dr · doc · sahab · saab · sahib · saheb · madam · mam · maam · जी · सर · डॉक्टर · डाक्टर · साहब · मैडम
- **emoji:** folded hands · thumbs up · OK hand · the smiling faces · a heart · flowers · the tick · handshake · clapping · raised hands

**Everything else reopens the chat** — "haan", "yes", "no", "ji" alone, "doctor sahab" alone, any digit, any question, any other word, any other emoji (a crying face), a photo, a voice note. **A question mark makes it a question:** "ok?", "ok ?", "Hello?", "theek hai?", "ठीक है?" (also the Urdu and the full-width mark) are never a bare acknowledgement — after a reply and after a template alike.

## What counts as OUR reply — an automatic message never answers a chat
An outgoing row answers a chat only when ALL of this holds (`wa_is_reply()`; when in doubt the chat STAYS awaiting):
- MyOperator accepted it (`sent` / `delivered` / `read`) and the store's type (`mtype`) is not `template`;
- its text does not begin "Template:" (a template echoed back under another type);
- its type is a plain message type — `text`, `image`, `document`, `audio` (what the Inbox's own sender writes) or `video`; `hsm`, `interactive`, `button` and any unknown type never answer;
- it is not an automatic message: a row with **no sender recorded** (the store's `sent_by` — the Inbox's own sender always records one) that came **within 60 seconds** after the incoming message it would answer.

So a reply typed in the MyOperator panel that reaches the store without a sender counts when it came more than a minute after the patient's message; an automatic greeting a few seconds after it does not. An outgoing row that is not our reply behaves like a template: it answers nothing, and a bare acknowledgement within 24 hours after it opens no chat. On the people list such a row is no "try" either: the person stays rose, awaiting.

**One limit, on the cautious side, and one ruling.** (1) A bare acknowledgement stays closed only **within 24 hours** of what went back; a "thank you" or a "hello" later than that opens the chat — a greeting days later is usually the start of something new (your ruling, 13-Nov: keep). (2) **After a template** (your ruling, 13-Nov): a bare acknowledgement within 24 hours after ANY message MyOperator accepted to that number — a template included — opens no chat, so the "ok" and "thank you" replies to the daily patient templates do not fill the block. A template still answers nothing: a real message followed only by a template is still awaiting (and a "thanks" written after that template is part of the same unanswered chat); anything that is not a bare acknowledgement after a template opens the chat; an "ok" later than 24 hours after the template opens it.

## The look-back: 7 days, and why
Seven days is the longest window the staff's own card has (Aaj · Kal · 7 din) and the page's own "7 days" tab, so every chat on a 7-day card is judged whole; and after a week an unanswered WhatsApp is no longer something a reply can mend (WhatsApp allows free replies for 24 hours only) — the follow-up list and a call are the route. The awaiting block always reads the last 7 days and today, whatever day the page shows. **On the first day the block will therefore list the past week's unanswered chats at once.**

## The two buttons
- **Done — no reply needed**: the chat as it stood — every message up to the one the page showed you — leaves awaiting. A message that arrived after the one shown is not covered. The chat comes back when the sender writes something new that is not a bare acknowledgement.
- **Not a patient**: the NUMBER leaves the awaiting lists (the block, the people's "awaiting", Needs you). On the staff cards its WhatsApps are in no figure and its missed calls are left out, so it never shows as a missed call-back on a card (the mock-up's sentence); a call that was ANSWERED from that number stays on the card as before. Its missed calls therefore also leave the card's "rung" figure (answered + missed) and "answered X/Y". It still appears among the people, grey, "not a patient"; the strip's call counts still count its calls. **A marked number is never hidden silently:** when it writes again after the mark, the folded "Not a patient" line says "1 wrote again" and its row says "wrote again · N since" (N = its incoming messages after the mark) — your screen only.
- Both ask for a **second tap** ("Tap again to confirm"; a second tap inside 0.7 s is ignored; an untouched first tap goes back after 6 s — the pattern of the stop list on /portal/messages). **Undo** is one tap, in the two folded lists.

## The door and its guards
`POST /portal/console/api/wa-mark` `{phone, act, upto}` — `act` = `done` · `undo_done` · `not_patient` · `undo_not_patient`.
- behind the page's own doctor gate (`doctor_required`): no login → the login page; any other role → 403;
- POST only — a GET is 405; no link reaches it;
- only the page's own script sends the header `X-Call-Console: 1`; without it → 400;
- the number is never one typed anywhere: a Done or a Not-a-patient is recorded only for a number the Inbox holds an incoming WhatsApp from in the last 7 days — and a Done only for the very message the page showed; otherwise 409, nothing written.

## The store: its own file, and why
`/root/portal/wa_awaiting.db` (setting `PORTAL_WA_AWAITING_DB`). **Not in console.db**: `portal_console.py --build` (cron, every 10 minutes) builds console.db whole in a temporary file and replaces the old one (`os.replace`), so any table written into it would be gone within ten minutes.
- created on the first tap (not by the installer); WAL; mode 600;
- one table, `mark(id, phone, act, upto, by_whom, at)`; **every action is a new row with who and when; an undo is a new row; no row is ever changed or erased**; the write lock is taken (`BEGIN IMMEDIATE`) before what stands is read;
- **If the block itself cannot be made** the page says, in its place, "The WhatsApp awaiting list could not be made — open WhatsApp Inbox" (a link) — it never just vanishes.
- **missing or empty → no marks. Locked or corrupt → no marks, and the block says "Your Done and Not-a-patient marks could not be read just now — every chat shows as awaiting until they can."** Never a 500, never a hidden chat. A tap on a store that cannot be written answers "try again" (503) and leaves the file as it was.
- **Its place in the nightly backup is a later small kit** (`clinic_state_backup.py`, beside `call_review.db`; a WAL store goes through the sqlite backup, not a file copy). Until then the marks are on the server only. The store holds numbers and no names.

## What changed in `/root/portal/calls_console.py` (and nothing else)
- `wa_chat()` (new) — the chat rule. `wa_is_ack()` (new) and its lists. `wa_is_reply()` (new) — what counts as our reply.
- `wa_answer()` — the same name and arguments; now answers by the chat rule.
- `person_state()` — "no reply needed" for a chat closed by your mark; when the first unanswered thing is a WhatsApp, a reply still "retrying" is "tried" and one "sent" is an answer (or not ours); when it is a MISSED CALL the line is exactly as before — a WhatsApp at "sent" after a missed call is still amber "tried · not reached".
- `wa_item()` / `wa_items()` — each message also carries its type, its text, its message ID, whether it is a bare acknowledgement, and your marks for its number.
- `wa_load()` (new) — the page's WhatsApps, the 7 days before, the days after, the answered calls of those days (`_ans_calls()`, read small).
- `build_people()` — judges each person's chat whole (two new optional arguments); a Not-a-patient number is grey.
- `strip_counts()` — one line: WhatsApp replies counted when accepted (was: delivered).
- `staff_cards()` — the WhatsApp loop counts chats (`_wa_eps()`); a Not-a-patient number's WhatsApps and missed calls are skipped (one condition on the line that gathers the calls).
- `_card_for()`, `page_data()` — read through `wa_load()`; `page_data()` adds the block (`wa_awaiting()`).
- the store: `wz_read()`, `wz_write()`, `wa_mark_check()`; the door in `register()`.
- the page: the block, its look, its script (`waMark`); four sentences reworded (the strip's tooltip, the people's "nobody has replied" line, the staff section's "WhatsApp chats on duty", the foot).
- **Not touched:** `fu_row_state`, `fu_return_day`, `fu_advice`, `followup_list` and their page parts; every call rule; `portal_inbox.py` and every other file.

## Every reader of what changed, and how its figure moves
| reader | reads | how its figure changes |
|---|---|---|
| your page — **the people** (state, "WhatsApp awaiting", the Awaiting chip) | `person_state` → `wa_answer` → `wa_chat` | a person's WhatsApp is awaiting only while the CHAT is. Fewer people rose. A person with no WhatsApp is judged exactly as before. Calls, counts and timelines are unchanged |
| your page — **the strip** ("N people nobody has answered", the bar; "replies") | `strip_counts` | follows the people. The small reply figure counts replies MyOperator accepted (was: delivered). Every call figure and "WhatsApps received" unchanged |
| your page — **Needs you** | `needs_you` (the people's state) | fewer "WhatsApp not answered" lines; the other lines unchanged |
| your page — **the staff cards** "WhatsApp chats on duty · N → M" | `staff_cards` → `wa_chat` | counts CHATS that needed a reply, not messages: N falls (several messages of one chat are one; a bare acknowledgement is none; a chat you marked Done is none). M = chats answered. Every CALL figure unchanged — except that the MISSED calls of a number you mark Not a patient leave the card (missed, not called back, net missed, and so "rung" and "answered X/Y") |
| **STAFF SCREEN — Aaj ka kaam, "Mere calls"** (`/portal/console/api/mycard`, `/api/card/<login>`) | `_card_for` → the same card | the line **"WhatsApp aaye → jawab diye"** shows the same two numbers as your card — now chats; the rows behind it are one per chat (the first message of the chat on her duty). **No word, no button, no field added or removed** — `aaj_kaam.html` is not touched. "Galat hai?" on a WhatsApp row and your earlier answers to disputes work as before (a dispute you accepted on any message of a chat keeps that chat off her card) |
| your page — **the follow-up pill** "Wrote back · to call" | `fu_row_state` (untouched) → `wa_answer` | the pill goes when the reply was accepted ("sent" counts) or the patient only wrote "ok" after it. Every follow-up FIGURE (called, reached, the folded lines, today's line) is unchanged. The pill still judges the chat from the due day on, as before |
| the Call-ke-baad block, the week's unknown callers, earlier days, the old console page, the Callback Tracker, the Inbox | none of it | unchanged |

## Where the page differs from the mock-up (the mock-up's wording and layout were followed everywhere else)
- **The number is shown in full** (the mock-up masks it as 98XXXXXX03) — as everywhere on this page (D819).
- **The wait is counted in clinic hours** (07:00–23:00, the page's rule) from the FIRST unanswered message; past one clinic day it reads "2 days". The mock-up's two examples have one message each, where "last message" and the wait agree.
- **Red or amber**: under one clinic hour amber, from one hour red (the mock-up shows 40 min amber, 3 h 10 min red).
- **Extra words, only when they apply**: "· 3 messages since 9:00 am" on a chat with more than one unanswered message; "N from an earlier day" after the sub-heading; "A reply was tried 9:12 am by Shivani — NOT delivered" on a chat whose reply failed or is still retrying.
- **Curly quotes** round the message (the page's own), not straight ones.
- **The block is a section of the Call Console** (left column, under "Needs you"), not a screen of its own; "CALL CONSOLE · WHATSAPP" is its section heading.
- **"Or a call to that number was answered."** is the mock-up's sentence, kept word for word; the exact rule (30 s or more, within 2 clinic hours of the last message) is in the page's foot.
- At 400 px "Done — no reply needed" wraps onto two lines inside its button.

## Decisions made in the build
- **The call rule runs from the LAST message** before the call (per chat), not from each message.
- **A call made while no chat is open answers nothing** and does not make a later "hello" a bare acknowledgement.
- **A template never answers a chat.** By your ruling of 13-Nov it does one thing only: a bare acknowledgement within 24 hours after it opens no chat.
- **Done reaches the message the page showed**, not the moment of the tap.
- **Not a patient and the staff cards — the narrow reading.** The approved words say "the NUMBER leaves the awaiting lists and the staff cards"; the mock-up's sentence says "never shows as a missed call-back on a staff card". Built: the number's WhatsApps and its MISSED calls leave the cards; its answered and outgoing calls stay (counted, and "not logged" when nothing was filed). This is the one place the kit reaches a call figure, only for a number you marked, and it is one condition on one line of `staff_cards()` — taking the number off the cards whole would be the same line, shorter.
- **The people list stays the page's own days.** A chat of an earlier day that is still unanswered is on the block (and counted there), not added to "People today" or to today's "WhatsApps received".
- **Staff cards do not carry a chat over to the next day's card**: a chat is on the card of the day its messages arrived on her duty (as a missed call is).
- **A status word other than sent / delivered / read** on a reply (should a source ever write one) does not count.

## Files
| live file | FROM | TO |
|---|---|---|
| `/root/portal/calls_console.py` | 49a3633d (S817) | see `TO_MD5.txt` |

Kit: `calls_console.py` (the new file, whole) · `install_S818_WA_AWAITING_CHATS.sh` · `walk_s818.py` · `proof_s818.py` · `oldwalks_s818.sh` + `walk_s748.py`, `walk_s762.py`, `walk_s817.py` (unchanged from S817's kit) + `EXPECTED_REDS.txt` (the same eight S817 named; this kit adds none) · `KIT_ID.txt` · `TO_MD5.txt` · `SUMS.md5`.

## Left for a later kit (known, not in this one)
- the store's place in the nightly backup (`clinic_state_backup.py`) and in the restore drill;
- the missing "delivered" pings themselves (the Inbox's receiver) — this kit only stops depending on them;
- `--undo` takes no build lock and does not check the portal's health first (as S817's);
- the timeline still words a reply at "sent" as "sent, not yet delivered", and an automatic outgoing row as "WhatsApp reply" (wording only, not an awaiting figure);
- an incoming WhatsApp whose time cannot be read stays "open" for its person and is in no chat on the block or a staff card (as before this kit; the Inbox always writes a time).

## Proven (S447, made-up data only)
- `walk_s818.py`: 78 of 78 on the new page; CONTROL on S817's page red on the reported case; 30 mutations of the new page each red; 14 comparisons with S817's page on the same stores as they must be — calls, people, follow-up sections, strip call counts, staff-card call figures, each person's own card, Call ke baad identical; the awaiting figures differ exactly as named.
- S748's walk (103) on the new page: red only where `EXPECTED_REDS.txt` names (the same eight). S762's walk 36 of 36. S817's walk 48 of 48, its ten mutations red.
- The page in a headless browser at 400 and 1100 px against the real door on made-up stores: no script error, nothing off-screen, the block as the mock-up, both buttons (two taps) and both undo lists working.
- The installer rehearsed on a stand-in root: dry · install · already · undo byte-identical · a kit file altered · the live file not the pinned one (S817 not installed: says so) · red after placing puts the old file back.

## Install (after the publish, and after S817; window 04:00–23:30 IST)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s818kit && cp -rp /root/deploy/repo/deploy_kits/S818_WA_AWAITING_CHATS /tmp/s818kit && bash /tmp/s818kit/install_S818_WA_AWAITING_CHATS.sh
```
## Undo
```
bash /tmp/s818kit/install_S818_WA_AWAITING_CHATS.sh --undo
```
The undo puts S817's file back and leaves `/root/portal/wa_awaiting.db` as it is (the older page does not read it; a re-install finds your marks again). It refuses when a later kit already sits on top of this file.
