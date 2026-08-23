# INCIDENT — Marg push failed with 401 (21 Aug 2026, evening) — RESOLVED

Reception could not send the Marg report. Two independent faults stacked; both are
now understood, one is permanently fixed, one still needs work.

## Timeline
- Morning 21 Aug: report sent successfully by the usual `SEND_TO_CLINIC.bat`.
- The Hub reported **"loaded nothing — re-load from Marg"**, so a fresh Marg report
  was generated.
- Sender then reported **NO REPORT FOUND**; dragging the file gave **HTTP 401
  `not_signed_in`**.
- 09:24 and 12:16 that day, `clinic-finance` had been restarted by the S195_ENTRY
  and S195_NCSCAN deploys.
- 22:12 — resolved; push **ACCEPTED-FOR-REVIEW**, then **loaded 22:14**.

## FAULT 1 (root cause of the 401) — the Marg token was never in the unit file
`MARG_TOKEN = os.environ.get("FINANCE_MARG_TOKEN", "")`, read at import. The gate
opens the push path only `if MARG_TOKEN and header == MARG_TOKEN`; when it does not
match, the request falls through to the identity check and returns **401
`not_signed_in`** (NOT 401 `bad_token`, and not 403 — a useful signature to remember).

`/etc/systemd/system/clinic-finance.service` contained FINANCE_DB, UI_DIR, SCAN_DIR,
PORT, CRON_TOKEN, SSO_DIR, PORTAL_LOGIN — **and no FINANCE_MARG_TOKEN at all**. The
value the process had been serving with came from somewhere transient, so it survived
only until the next restart. Today's deploy restarts triggered it, but **any restart
or reboot by anyone would have done the same** — this was a latent landmine, not a
consequence of the deploy's content (the `marg-push` handler is byte-identical
before and after; verified by diff).

**Fixed:** `Environment=FINANCE_MARG_TOKEN=…` added under `[Service]`, then
`daemon-reload` + `restart`. Token now durable across restarts and reboots.
Client `token.txt` was aligned to it (verified by comparing MD5 of both sides —
server `843d3eec…`; never exchanging the value itself).

**Diagnostic worth keeping:** compare the two sides without exposing the secret —
```
tr '\0' '\n' < /proc/$(systemctl show -p MainPID --value clinic-finance)/environ \
  | sed -n 's/^FINANCE_MARG_TOKEN=//p' | tr -d '\n' | md5sum
```
`d41d8cd98f00b204e9800998ecf8427e` (md5 of empty) means the running process has no
token at all.

## FAULT 2 (why "NO REPORT FOUND") — the sender is blind to the file Marg writes
`SEND_TO_CLINIC.bat` scans only `users\*\report\REPORT_1.XLS`. On the box today:
- `users\50018\report\` — **empty**, the old REPORT_1.XLS is gone
- `users\61376\report\REPORT_2.XLS` — the fresh export
- `users\61376\report\REPORT_7JJ0J0TR7.XLS` — Marg emitting an arbitrary filename

So the sender found nothing. Worked around by dragging the file onto the .bat
(which sends `%~1` directly). **Not yet fixed.** The S195b explicit-path change
(macro passes the exact file as a 3rd argument) addresses this; the router +
watcher address it generally by identifying reports on content.

## Still open
1. **Deploy the explicit-path sender path** so nobody has to drag files.
2. **₹20,000 August salary advance** (17 Aug) — left the drawer, recorded nowhere.
3. **18 Aug entered ₹1,297 short** — copy and Marg both say 25,176, books say 23,879;
   correcting it lands the drawer at ₹3.
4. **`FINANCE_CRON_TOKEN` was pasted into a chat** during diagnosis — rotate it
   (`openssl rand -hex 24`, replace the line, daemon-reload + restart).

## Lesson for future deploys
A restart is not a no-op when a service's environment has drifted from its unit file.
Before restarting a live service, check that every variable it needs is actually
declared in the unit — `systemctl show -p Environment` reflects the FILE, while
`/proc/<pid>/environ` reflects what the process is really running with. The two
disagreeing is the warning sign.
