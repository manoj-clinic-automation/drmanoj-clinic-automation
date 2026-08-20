# S194_EMAIL — ⭐5 ping-pong Gmail query agent

Email the clinic Gmail a command; the box runs the READ-ONLY `dr_query` and
replies in the same thread within ~3 minutes.

## Safe by construction
- Runs **only** the `dr_query` allowlist (`day/marg/cash/custody/flags/tables/sql`);
  `dr_query` opens `finance.db` **mode=ro** (cannot write) and its `sql` mode is
  SELECT/WITH only. Anything else (`rm -rf /`, an UPDATE) is refused.
- Processes **only** UNSEEN mail whose From is in the `trusted` list and whose
  subject starts with the trigger (`Q:`). Everything else is left untouched.
- Replies **only to the matched trusted address**, never the raw From — a spoofed
  From cannot exfiltrate anything.
- The Gmail app password lives **only** in the root-only config on the box; it is
  never printed, logged, or committed.

## Install (stages it; does NOT start — it needs your app password)
```
cd /root/deploy/repo && git pull
cd deploy_kits/S194_EMAIL && bash install_s194_email.sh
```
Then, to go live (the installer prints this too):
```
cp /root/deploy/email_agent.example.json /root/deploy/email_agent.json
nano /root/deploy/email_agent.json        # paste the 16-char app password
chmod 600 /root/deploy/email_agent.json
python3 /root/deploy/email_agent.py --selftest      # expect SELFTEST OK
python3 /root/deploy/email_agent.py --once          # one live poll
systemctl enable --now email-agent.timer            # 3-min polling
```

## Use it
Email **drmka.ortho@gmail.com** from a trusted address, subject:
`Q: cash 30` · `Q: custody` · `Q: day 2026-08-19` · `Q: marg 2026-08-19` ·
`Q: flags` · `Q: sql SELECT COUNT(*) FROM day_entry`. The answer comes back
in-thread.

## Verified offline
Router proven: allowed commands return correct output against the seed; a `sql`
UPDATE is refused by dr_query; `rm -rf /` is refused by the allowlist; `--selftest`
passes with a real config and fails on the placeholder password. IMAP/SMTP are
tested live once the app password is in place (needs the box + network).

## Trusted senders
Defaults to `drmanojkragarwal@gmail.com` and `drmka.ortho@gmail.com` — edit the
`trusted` list in the config to add/remove.
