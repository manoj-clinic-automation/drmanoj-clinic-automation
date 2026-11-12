# S802_WA_SEND_HEADERS — the Inbox and the template sender reach MyOperator the way the tracker's relay does (F-1031)

**Two live runs on 12-Nov-2026, read together** (both sent nothing):
- **12:05 IST (S799's probe):** urllib was refused (HTTP 500 at MyOperator's authorizer) until an `http.client` request had
  been let through; after that every request was accepted, urllib's too.
- **12:37 IST (S800's proof):** five urllib tries in 16 seconds, no `http.client` request before them — all five refused.

So it is not timing and not the User-Agent (both were this session's wrong readings; each kit asked first and changed
nothing). What differs between the two programs on the wire is the **header names**: urllib re-cases them —
`X-MYOP-COMPANY-ID` leaves the server as `X-Myop-Company-Id` (checked on manojz against a local listener) — and `http.client`
sends them as written. The gateway refuses the re-cased form at its authorizer, and keeps an authorisation per key for a
while, which is why a urllib send got through only just after a properly-cased one (the tracker's relay, `wa_send.py`, has
always used `http.client`). It also fits the month's log: the Inbox's rare successes come in clusters.

**The change — one request each, nothing else:**
- `/root/portal/portal_inbox.py` 06e2c28e → 973cc74f — `myop_send`: the request goes through `http.client`, header names as
  written. Same answer handling, same trace for the log, same "could not reach" on no answer. One try; the S666 retry queue is
  untouched and still recognises a real refusal.
- `/root/portal/portal_wa.py` 34994b23 → e8b27db9 — `send` (the approved templates): the same.

**Proved before it is placed** — `prove_s802.py`, nothing sent. Every request uses a **fresh made-up key** (no earlier request
can help it; its proper answer is 401/403): the old road, `http.client` as written, `http.client` with the company header
named as urllib sends it, `http.client` with urllib's `Connection: close`; then the changed Inbox sender with fresh made-up
keys and once with the real key and an empty number (proper answer 400). Placed only on **PROVEN**: the old road refused, the
as-written road and the changed sender answered properly. NOT-SHOWN (the old road is not refused right now) or FAILED →
nothing is changed. After placing, the installed sender is checked once more (real key, empty number → 400), else both files
go back.

**The kit carries no copy of the two files** (portal_wa.py holds the clinic's number in its page text — F-185): the installer
makes both on the box with `make_s802.py` from the live bytes (each replaced block checked by its md5) and checks the results
against the pins.

**Walk** 29/29 against a stand-in gateway on the same machine that behaves as both live runs did; the CONTROL red on the live
files (11 of 29).

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s802kit && cp -rp /root/deploy/repo/deploy_kits/S802_WA_SEND_HEADERS /tmp/s802kit && bash /tmp/s802kit/install_S802_WA_SEND_HEADERS.sh
```
Undo: `bash /tmp/s802kit/install_S802_WA_SEND_HEADERS.sh --undo`.
