# S588_WEBSITE_MAIL_AND_ACCESS_PROBE — READ ONLY: why the website sends no mail, and whether the website vendor still has a way in

**Why.** The Growth chat's board message `growth_S320_1` (16-Oct-2026), Runbook v241 §2A item 5: (1) the VPS sends no e-mail — the
WordPress password-reset mail never arrived, so the contact forms on drmanojagarwal.com are probably silent; (2) the website vendor set
up access on the VPS in June 2026 (their WordPress login was deleted on 15-Oct at the owner's word) — check for any FTP, SSH or
CyberPanel login of theirs. The owner, 18:09 IST 18-Oct: *"Now the website's mail part"*. Board `_numbers` v499 → v500: kit S588.

**What it is.** One Python file, `probe_s588.py`, run once as root with the system python. It answers both questions from the box itself:

- **Mail:** the mail program's settings (relay or direct), whether the server can reach Gmail's doors 25 / 587 / 465, the queue, the mail
  log's sent / deferred / bounced counts and the reasons, the SPF record of drmanojagarwal.com, the website's active plugins and any mail
  (SMTP) plugin or setting.
- **Access:** Linux logins with a shell, the recent and ever logins, every SSH key (type, fingerprint, name — never the key itself), the
  SSH settings, FTP users, CyberPanel users, WordPress administrators, the doors open to the world and the firewall.

**What it does not do.** Change any setting, file, user, key or database row; restart anything; send any mail. It writes one file, its own
report, `/root/finance/s588_probe.json` (mode 600) — the nightly backup carries `/root/finance/*.json`, so the full report is read the next
morning. It never prints or stores a password, a key body or a token; database passwords are read only to log in and handed to `mysql`
in its environment. E-mail addresses are masked to the first letter and the domain.

**Run (the owner, after publishing):**
`cd /root/deploy/repo && git pull --ff-only && /usr/bin/python3 -B /root/deploy/repo/deploy_kits/S588_WEBSITE_MAIL_AND_ACCESS_PROBE/probe_s588.py`

The screen shows about twenty lines; a photo of it is enough. **The fix comes after** — built from what this shows, offline, in its own kit.

**Proof.** Compiled; run in the assistant's workspace (no mail program, no CyberPanel, no WordPress): every section either read or said
"could not read" and the run finished with its report written — no section can stop the others. No number in the file (NO_PHONE_NUMBERS).
