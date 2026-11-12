# S800_WA_SEND_KNOCK — a send refused at MyOperator's gateway is tried again at once (F-1031)

**What S799's probe showed on the server (12-Nov-2026 12:05 IST, nothing sent):** of 24 requests in a row, the first four were
refused (HTTP 500 from MyOperator's authorizer) and the twenty after them accepted — whichever way they were sent, with the
made-up key and with the real one. Not the program that sends, not its User-Agent: **the first requests after the gateway has
been idle are refused; the same request about two seconds later is accepted.** The Inbox's own send log says the same over 30
days: a try 10–60 s after another is accepted about half the time; a try minutes after another, almost never (the retry
worker's 2- and 10-minute spacing is why 5 of 667 retries got through); a refusal answers in about a tenth of a second.
The owner's test template of 11:31 IST was refused this way.

**The change.** In the two senders a request refused at the gateway is sent again after 2.5 s (then 3, 4, 6 s — five tries at
most, about 16 s in the worst case):
- `/root/portal/portal_inbox.py` 06e2c28e → 35bf3208 — `myop_send` (the Inbox's replies, media, and the S666 retry queue);
- `/root/portal/portal_wa.py` 34994b23 → ceb06c26 — `send` (the approved templates).

A refusal comes **before** MyOperator's message service, so trying again can never deliver a message twice (the same reason
the S666 retry is safe). An acceptance is never followed by another request; "no answer at all" is not tried again (its
outcome is unknown). What is still refused after the fifth try goes to the S666 queue exactly as before.

**Proved before it is placed.** `prove_s800.py` calls the changed Inbox sender on the live gateway with the real key, an
**empty number and empty text** (nothing can be delivered) and prints what each try got. Placed only on **PROVEN** — a first
try refused, a later try of the same call not. If the gateway happens to be warm it waits 150 s and tries again (three calls
at most). After placing, the installed sender is tried once the same way; refused at the end → both files go back.

**The kit carries no copy of the two files** (portal_wa.py holds the clinic's number in its page text — F-185): the installer
makes both on the box with `make_s800.py` from the live bytes and checks them against the pins.

**Walk** 27/27 against a stand-in gateway on the same machine that refuses for a short while after idle; the CONTROL red on
the live files (18 of 27).

**Cold review** (a reviewer who did not write it): SAFE AFTER FIXES — built: the caller is given the LAST try only (a refusal
followed by "no answer" is reported as unknown, never as a refusal — so nothing that may have gone is queued again); the
template sender calls a refusal the gateway's only with their authorizer's header (HTTP 500 with the same words from anywhere
else is not tried again); tries after a refusal wait at most 10 s for an answer (worst case about 26 s, inside the portal's
60 s); the proof counts only the proper answer to an empty number (HTTP 400). Known and left: the page already blocks its
Send button while a send is in flight; a second device sending the same text during those seconds is not guarded.

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s800kit && cp -rp /root/deploy/repo/deploy_kits/S800_WA_SEND_KNOCK /tmp/s800kit && bash /tmp/s800kit/install_S800_WA_SEND_KNOCK.sh
```
Undo: `bash /tmp/s800kit/install_S800_WA_SEND_KNOCK.sh --undo`.
