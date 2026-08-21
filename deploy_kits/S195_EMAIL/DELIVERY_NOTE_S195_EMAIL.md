# S195_EMAIL — ⭐5 Gmail query agent, hardened

Follow-up you asked for after S194. Two changes, nothing else touched.

## What changed (and why)
1. **Answered mail is tracked by a Gmail label, not the read/unread flag.**
   The old agent searched `UNSEEN SUBJECT "Q:"`. If you *opened* a `Q:` before
   the 3-minute poll, it was already "seen" and the agent skipped it forever —
   that's why the 18:27 `Q: sql …` never got a reply. Now the poll asks Gmail
   for `subject:Q: -label:clinic-agent-done`, so read-or-unread doesn't matter —
   only whether it has been answered yet. The label is applied **only after** a
   reply is actually sent, and every message is re-checked for the label before
   replying, so nothing is ever answered twice.

2. **It always replies — even on an error.** If a command is wrong, or the query
   itself blows up, you now get an email back explaining what went wrong instead
   of silence. A message is marked done only when a reply truly left; if sending
   fails (network blip), it's left for the next poll to retry.

Still safe by construction: only the read-only `dr_query` allowlist runs
(`day/marg/cash/custody/flags/tables/sql`), the DB is opened mode=ro, replies go
only to the matched trusted address, and the app password never leaves the box.

## Install
```
cd /root/deploy/repo && git pull
cd deploy_kits/S195_EMAIL && bash install_s195_email.sh
```
Your existing `/root/deploy/email_agent.json` is kept as-is — the new
`done_label` defaults automatically, so there's no config edit to make. The
previous agent is backed up as `email_agent.py.bak_s195`. If the 3-min timer is
already enabled from S194, the next poll runs the hardened agent; nothing else
to do.

## Test it
Email **drmka.ortho@gmail.com** from a trusted address, then OPEN it before the
poll (that's the case that used to fail):
`Q: cash 30` · `Q: custody` · `Q: day 2026-08-19` · `Q: sql SELECT COUNT(*) FROM day_entry`
The answer comes back in-thread, and the mail picks up a `clinic-agent-done`
label. To force a re-answer, remove that label in Gmail.

## Verified offline
`py_compile` clean. Router proven against a stub: `help`/`cash 30`/`sql SELECT …`
run; a `sql UPDATE`, `rm -rf /`, and any non-allowlisted verb are refused. Label
parser correctly detects `clinic-agent-done`. IMAP/SMTP + the live label round-trip
are exercised on the box (`--selftest`, then `--once`).
