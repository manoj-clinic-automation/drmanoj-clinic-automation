# S935_ONEWAY_OUT_CALLS — staff app calls on the Call Console (the parent, S498, 23-Nov-2026)

**Why.** On 23-Nov Alisha made 8 follow-up calls from her own MyOperator app (09:56–10:14 IST). MyOperator reports such a
call as category `oneway`, direction `outgoing`. The call hook (`/root/wa/call-hook/call_hook_capture.py`, v3.2) kept only
`incoming` calls and the Callback Tracker's own dialler calls (`obd` with a client_ref_id); everything else went to the raw
log only, as since July. So the Call Console showed "follow-ups called 0 of 9".

**What changes.**
The kit carries no copy of the two files (their own selftest fixtures hold made-up 10-digit numbers the repository refuses): the installer runs make_s935.py on the live bytes and requires the TO pins.

| file | FROM | TO | change |
|---|---|---|---|
| /root/wa/call-hook/call_hook_capture.py | 2d25fe7b | see TO_PINS | `oneway` + `outgoing` kept as one row keyed `OUT-<session id>` (call.end and call.summary share it), phone10 = the patient's last 10 (customer_number, else the customer leg); log line "receiver v3.3" |
| /root/wa/portal_console.py | a8d050ef | see TO_PINS | `derive_direction('oneway')` = Out |

Then, once: the hook's own `backfill_call_durations.py` (unchanged, insert-only) replays every raw log through the new
hook and appends the keys the tab lacks — today's 8 calls and every app call since July.

**Proof.** walk_s935 23/23 on made-up payloads shaped as the live ones (field names read from the 23-Nov raw log, no
values); control (the live files) red 12/23; the hook's selftest 69/69 and the console's selftest 54/54 on the new files;
the backfill's own dry run inside the installer.

**Install.** `cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s935kit && cp -rp /root/deploy/repo/deploy_kits/S935_ONEWAY_OUT_CALLS /tmp/s935kit && bash /tmp/s935kit/install_S935_ONEWAY_OUT_CALLS.sh`
**Undo.** `bash /tmp/s935kit/install_S935_ONEWAY_OUT_CALLS.sh --undo` (the rows already added stay — they are real calls).
