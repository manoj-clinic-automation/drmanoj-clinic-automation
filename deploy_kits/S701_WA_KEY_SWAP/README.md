# S701_WA_KEY_SWAP — the WhatsApp fix · the parent · session 382 · 03-Nov-2026

**For the owner, in two lines.** One server line does two things: (1) a WhatsApp reply MyOperator refuses keeps retrying by itself until the patient's 24-hour window closes (not for one hour only); (2) after all its checks are green it says *NOW press Regenerate* — you copy the new key from MyOperator's API page, paste it, and it goes into every place on the server that held the old one.

## Why
Ticket 691386: since 21-Oct MyOperator's gateway refuses our sends on and off (HTTP 500, `AuthorizerConfigurationException`); since 30-Oct 0 of 83 inbox sends were accepted, while the same key is accepted from Postman and, minutes apart, from the server (S381). The owner, 14:27 IST 02-Nov: *"it's been 2 weeks, need to sort it out on top priority."* A fresh key is the one step left on our side; the longer retry carries each reply through the gateway's bad spells.

## Files
| live file | FROM | TO | what |
|---|---|---|---|
| `/root/portal/portal_inbox.py` | 58d5318e | f89ad282 | 10 counted edits (`make_s701.py`, re-run on the box): `RETRY_FOR_MIN` 24 h (the window check decides), `retry_gap()` — 2 min in the first hour, 10 min after; `refresh_link()` — a photo / PDF / voice note's public link renewed before each retry (it lives 6 h); the page's words; health says S701. Nothing else. |
| `/root/wa/swap_key_s701.py` | — | see SUMS | NEW: `find` (read-only) · `apply` · `undo` |
| every live file holding the old key | by value | by value | found by reading, not by a list: `/root/wa/.env`, `/root/wa/wa_approve.env`, the portal's settings, any unit override, the crontab, any other live file. Backup copies are listed and never changed; media and virtualenvs are not read. **If the key is also in a log, a data file, the repository copy or anywhere else the tool does not change, it STOPS before asking for Regenerate** (Claude looks first). |

**The test of the new key.** Only an HTTP 200 proves a key (S600: a made-up key also gets 500). Written when MyOperator accepts the new key once in six tries; or when it accepts neither and the new key has the old one's length (the old is revoked by the Regenerate) — then exit 3, *written, not yet proven*. Never written when MyOperator answers 401/403 to the new key, or still accepts the old key and not the new (a wrong paste). **Order:** every check runs before the line says *NOW press Regenerate*; after it only the paste can be refused, and the same line is simply run again. Run again after a good swap it says *ALREADY*. The key is never printed — only its length and an 8-character fingerprint.

**Restarts** `clinic-portal`, `wa-approve`, `wa-send-api` (they read the key at start), any service started with the old key in its environment, any service whose unit names a changed file, and any service whose own script names the key's settings or imports the senders; `systemd` reloaded first when a unit file changed. Cron's own jobs are never a reason to restart cron.

## Proven (S382, the cloud workspace, python3 + flask, on the 03-Nov bundle's bytes)
`walk_s701.py` **32 of 32 green** (S666's checks carried; the new: retried past the hour, the 10-minute gap after it and held, kept going until the window closed then one NOT-delivered mail, the last call to MyOperator before the window's close (by its time), a 5-hour-old job inside the window tried, a photo accepted 7 hours on with its link still opening, the page's words, health S701). **Control** on the live file: 8 S701 red · 0 older red · 24 green. Mutants 5 of 5 caught.
`walk_swap_s701.py` **31 of 31 green** on a made-up server in /tmp (made-up keys; stand-in systemctl, crontab, /proc, MyOperator): find names the live holders (live code in /root/state_backup included) and the backup copies; bad paste, same key, Enter alone, old still accepted, another shape, a 401 — each stops with nothing changed; *Regenerate* is asked only after every check; the swap — every live holder new, the rest of each file byte-identical, modes kept, the crontab, backups 600 in a 700 folder, daemon-reload before the restarts, the right services (a script that reads the key included; not cron, not call-hook), nothing left holding the old key, the inbox reads the new key; run again → ALREADY; undo byte-identical; undo leaves a crontab edited since; not-yet-proven exit 3; disagreeing keys stop; a failed write puts everything back; a log or the repository copy holding the key stops before Regenerate; no key ever printed. Mutants 14 of 14 caught. The walk refuses to run unless every path is inside /tmp.
Installer rehearsed on a made-up root: DRY, install + swap, again (ALREADY), Enter to skip, undo, forced red after placing (restored byte-identically), changed live file refused.
Independent cold review R1: NOT SAFE — 2 blockers (a photo retried past 6 h sent with a dead link; the README asked for Regenerate before the checks) and 9 should-fix; all built in except one, carried to the next inbox kit: a *Stop retrying* button for a reply that would be stale if it went hours late. Round 2: SAFE TO INSTALL; its should-fix built in: only services with a running process are restarted (a finished one-shot is never re-run); after Regenerate a newly appeared holder no longer stops the swap (reported instead); a 401 is believed only after about a minute of asking; a failed write says WhatsApp stays down until the line runs again; ALREADY says when the last swap was not proven.

## Install (on the server, after the publish; window 04:00–23:30 IST)
Open `https://in.app.myoperator.com/integrations/developer-api/whatsapp` in another tab, but do **not** press Regenerate yet. Run:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s701kit && cp -rp /root/deploy/repo/deploy_kits/S701_WA_KEY_SWAP /tmp/s701kit && bash /tmp/s701kit/install_S701_WA_KEY_SWAP.sh
```
When it says **NOW press Regenerate**: press it, copy the new key, paste it and press Enter (it does not show). Enter alone = the key is left as it is.
## Undo
The key: the same line with `UNDO=1 ` before `bash`. The inbox file:
```
\cp -p /root/portal/portal_inbox.py.bak_S701 /root/portal/portal_inbox.py && systemctl restart clinic-portal
```
