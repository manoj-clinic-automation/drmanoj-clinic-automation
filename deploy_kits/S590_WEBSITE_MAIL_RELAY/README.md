# S590_WEBSITE_MAIL_RELAY — the website's mail sent through the clinic Gmail

**Why.** The Growth chat's `growth_S320_1` item 1 (16-Oct-2026): the VPS sends no e-mail — the WordPress password-reset mail never
arrived, so the contact forms on drmanojagarwal.com are probably silent. S588's read-only check (18:14 IST 18-Oct) found why: WordPress
hands its mail to this box's postfix, which sends it **direct** (no relay); the doors to Gmail are open, but Gmail refuses mail from this
box under the website's name as unauthenticated (`550-5.7.26 … blocked`); the site has no SMTP plugin (S589's v2 check: only
mailchimp-for-wp). The owner, 18:27 IST: *"Why not do this now, if possible?"* Board `_numbers` v503 → v504: kit S590.

**The route (the assistant's call, D-free: it changes no workflow and nothing he sees but mail arriving).** postfix relays through
`smtp.gmail.com:587`, signed in as the clinic Gmail — **the account and app password the daily health mail already uses**
(`/root/wa/.env`, `WATCHDOG_SMTP_*`). Nothing new is asked of the owner and no new secret exists: the same password is written into
postfix's own map, `/etc/postfix/sasl/sasl_passwd` (root, 600) and its `.db`. WordPress keeps sending the way it does today (PHP `mail()`
→ postfix) and never sees the password. Gmail writes the clinic Gmail address as the sender; the contact form's own Reply-To (the
visitor) is kept, so a reply goes to the visitor.

**Why not an SMTP plugin inside WordPress:** the password would sit where the website (the most exposed program on the box) can read it.
**Why not the website's own Zoho mail:** it would need a new mailbox password from the owner; this route needs nothing from him.

**What it does.** Checks (postfix active; no relay set today — any → stop; the env file's login signs in to Gmail, nothing sent) →
keeps `/etc/postfix/main.cf` and `postconf -n` in `/root/s590_backup/` → writes the map (600), `postmap`, sets `relayhost`,
SASL on, TLS required, `postfix check`, reload → **two tests to the clinic inbox**: (1) `sendmail` as root, (2) PHP's own `mail()` run as
the website's user with the website's PHP (the road WordPress takes); each must show `status=sent … relay=smtp.gmail.com` in the mail log
within 90 s. Test 1 red → `main.cf` put back, the map removed, postfix reloaded. `relay_s590.py` holds the two steps that touch the
password, so it is never on a command line or on the screen.

**Run (the owner, after publishing):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S590_WEBSITE_MAIL_RELAY/install_S590_WEBSITE_MAIL_RELAY.sh`
(`DRY=1` in front: every check including the Gmail sign-in, nothing changed.)

**UNDO (one line):** `\cp -p /root/s590_backup/main.cf /etc/postfix/main.cf && rm -f /etc/postfix/sasl/sasl_passwd /etc/postfix/sasl/sasl_passwd.db /etc/postfix/sasl/sasl_passwd.lmdb && systemctl reload postfix`

**Known limits.** CyberPanel can rewrite `main.cf` on an upgrade of itself; if the website's mail stops after one, run the install line
again (it says ALREADY INSTALLED when nothing is needed). Gmail's sending limit (~2,000 a day) is far above the website's few a day.
The mailbox `drman1045@` on the website's domain does not exist at Zoho (two bounces in the log) — that is the website user's own
system mail, not the contact form; it is left as it is.

**Proof.** `relay_s590.py` compiled; `check` / `write` / `to` run on a made-up env file (the map written 600 with the right line, the
address masked on screen, a missing password refused). The installer rehearsed with stand-in postfix tools: DRY, a full run (both tests
green), a second run (ALREADY INSTALLED), a relay already set (STOP), a failed sign-in (STOP), test 1 not sent (main.cf restored).
`bash -n`; no number in any file (NO_PHONE_NUMBERS).
