# S589_FTP_VENDOR_OFF — the website vendor's FTP login removed, FTP switched off (D741)

**Why.** S588's read-only check (18:14 IST 18-Oct-2026) found the website vendor's FTP login `admin_approids` still active, pure-ftpd
running and door 21 open to the internet; nothing in the clinic uses FTP (every program and kit searched). The owner, 18:18 IST: *"yes"*
— remove it and switch FTP off (D741). Board `_numbers` v500 → v501.

**What it does.**
1. **Checks first, stops on any doubt:** the CyberPanel database answers; the FTP accounts are the vendor's one only (any other account
   → stop and ask); no website on the box is set to update itself over FTP (`FS_METHOD` ftp or `FTP_USER` / `FTP_PASS` / `FTP_HOST` in a
   `wp-config.php` → stop and ask); pure-ftpd exists.
2. **Keeps what it removes**, root-only, in `/root/s589_backup/`: the account's row (`ftp_admin_approids.sql`, mode 600 — it holds the
   account's password hash, so it never leaves the box) and pure-ftpd's enabled state (`pure-ftpd.was`).
3. **pure-ftpd stopped, disabled and masked** (it cannot start again by itself), then the account row deleted from CyberPanel's FTP table.
4. **Reads back:** no vendor row, pure-ftpd not active, nothing listening on 21, the portal and the website still answer.
5. Runs **`probe_s589.py`** — S588's read-only check, v2: the website's database password is read to its matching quote, the TCP door
   is tried when the socket refuses, and WordPress's own `wp` tool is the last resort — and shows its WordPress lines (administrators,
   mail plugins), so the next mail fix is built from facts.

Nothing of the clinic's own programs is touched or restarted. The SSH keys (both the owner's), the CyberPanel login (`admin` only) and
the mail program are left exactly as they are.

**Run (the owner, after publishing):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S589_FTP_VENDOR_OFF/install_S589_FTP_VENDOR_OFF.sh`
(`DRY=1` in front: every check, nothing changed.)

**UNDO (one line, only if FTP is ever wanted back):**
`systemctl unmask pure-ftpd && systemctl enable --now pure-ftpd && MYSQL_PWD="$(cat /etc/cyberpanel/mysqlPassword)" mysql -u root cyberpanel < /root/s589_backup/ftp_admin_approids.sql`

**Proof.** `probe_s589.py` compiled and run in the assistant's workspace (sections that cannot read say so; the run completes); the
password reader unit-tested on four made-up `define()` shapes (a double quote inside single quotes, an escaped quote, a single quote
inside double quotes, plain). The installer's shell syntax checked (`bash -n`). No number in any file (NO_PHONE_NUMBERS).
