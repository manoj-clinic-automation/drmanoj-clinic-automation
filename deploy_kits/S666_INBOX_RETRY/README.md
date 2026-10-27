# S666_INBOX_RETRY — the WhatsApp Inbox retries MyOperator's gateway refusal · the parent · session 358 · 27-Oct-2026

**For the owner, in two lines.** When MyOperator's gateway refuses a reply at its sign-in check (the error of ticket 691386), the message now shows *MyOperator busy — retrying* and the server sends it again every 2 minutes, for up to an hour, while the patient's 24-hour window is open. Any other failure is shown at once, as before, and never retried — so a patient can never get the same message twice.

## Why
Since 21-Oct, 11 of 19 free-text replies from the inbox were refused: HTTP 500 `{"message":null}`, `x-amzn-ErrorType: AuthorizerConfigurationException`, in 56–226 ms — stopped at MyOperator's API Gateway authorizer, before their message service. The same customer, text and key were accepted minutes later (one customer on 24-Oct: refused 08:36:57, accepted 09:04:19). The owner, 12:23 IST 27-Oct: the build *"ready beforehand"* for the 15:30 IST call with MyOperator's technical team; the evidence mail with this plan went to the ticket at 12:2x IST.

## Files
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/portal_inbox.py` | e25bed25 | 58d5318e | E1 table `retry_q` (additive); E2 `gateway_refusal()` (that refusal only), `run_retries()` (an hour over is given up BEFORE any call; the window re-checked before every try; 2-minute gap; anything else gives up at once; accepted is recorded first; MyOperator's echo arriving first leaves one row; a crash mid-try or a try ending in an error is *unsure* — 'may have gone, check' — never tried again), `_mail_gaveup()` (NOT delivered / may have gone); E3 a retry's own log lines send no mail each; E4 `queue_retry()`; E5/E6 the text and photo/PDF/voice sends queue that refusal, and refuse the SAME message (or a second photo/PDF/voice) by hand while one is retrying; E6b the first mail says *being retried*; E7 the page: *retrying*, *may have gone*, the toast; health says S666 |
| `/root/portal/inbox_retry.py` | — | d6718b9a | NEW: the runner |
| crontab | — | one line | `*/2 * * * * /usr/bin/flock -n /root/wa/wa_inbox/retry.lock /root/wa/venv/bin/python3 -B /root/portal/inbox_retry.py >> /root/wa/wa_inbox/retry.log 2>&1 # S666_INBOX_RETRY` — added by copying the crontab, counting it, and putting the copy back on any mismatch |

Templates and the follow-up batch are not touched. Restarts `clinic-portal` only.

## Proven (S358, manojz's VM, python3 + flask, on the 27-Oct bundle's bytes)
`walk_s666.py` **23 of 23 green** against a stand-in MyOperator on 127.0.0.1 (made-up numbers, temp store): an accepted send unchanged; any other 500 fails at once, nothing queued; the authorizer refusal kept (*retrying*, one job), the first refusal still mailed; nothing before 2 minutes; refused again → still retrying, no mail; accepted → *sent* with MyOperator's id; every try in the send log; another error on a retry → NOT delivered + one mail; 60 minutes → stops; the window closing → stops without calling MyOperator; a photo kept with its file and sent on the retry with the same link; the same text by hand while retrying refused (MyOperator not called), a different text goes; a job 5 hours old given up without a call; MyOperator's echo first → one delivered row; a try that errors → *unsure* + mail; a crashed *busy* job *unsure*, never sent again; the header in lower case with a suffix kept; the runner runs on its own; the page words. **Control** (`--old`): 19 S666 red · 0 older red · 4 green. Installer rehearsed on a made-up root: DRY, install (the runner under the venv python finds the key and the store, runs once under flock; the crontab 2 → 3 lines), ALREADY INSTALLED, forced red with no key (file back, runner removed, crontab back to its 2 lines). Independent cold review round 1: NOT SAFE (1 blocker: a hand re-send while retrying could reach the patient twice; 5 corrections) — all built in. Round 2: SAFE TO INSTALL (0 blockers; the undo line now removes only this kit's cron line; a chat row lagging behind an accepted retry catches up on the next pass; the service's own environment read for INBOX_ settings; a crontab without a final newline handled).

## Install (on the server, after the publish)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s666kit && cp -rp /root/deploy/repo/deploy_kits/S666_INBOX_RETRY /tmp/s666kit && bash /tmp/s666kit/install_S666_INBOX_RETRY.sh
```
## Undo
```
\cp -p /root/portal/portal_inbox.py.bak_S666 /root/portal/portal_inbox.py && crontab -l > /root/portal/crontab.now && grep -vF S666_INBOX_RETRY /root/portal/crontab.now > /root/portal/crontab.new && crontab /root/portal/crontab.new && rm -f /root/portal/inbox_retry.py && systemctl restart clinic-portal
```
