# S592_CONTACT_FORM_VIA_WPCLI — the website contact form mails the clinic only (D742)

**The owner, 18:41 IST 18-Oct:** *"remove"* — the website contact form (Elementor Pro, post 91, form `ff75886`) was copying every
enquiry (the patient's name, mobile, treatment) to an outside marketing firm's address at `arrowmarketing360.com` (F-940).

**Why a second kit.** S591 carried the change and stopped at its first check: the `mysql` program refused the login read from
`wp-config.php` (F-938). Nothing was changed. S589 had already reached the same database through WordPress's own command tool
(wp-cli). S592 is S591's logic whole; only the road to the database is new.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S592_CONTACT_FORM_VIA_WPCLI/install_S592_CONTACT_FORM_VIA_WPCLI.sh

`DRY=1` before `bash` shows what would change and changes nothing. `--undo` at the end puts every changed row back.

**Roads, in order — the screen says which one was used:**
- **A** — WordPress's own database connection, through wp-cli (`wp eval-file wpdb_s592.php`, as root with `--allow-root --skip-plugins --skip-themes`, exactly as S589 ran wp-cli). The statement is passed in a root-only file in `/root/s592_tmp/`, deleted after each use.
- **B** — the CyberPanel MySQL root (`/etc/cyberpanel/mysqlPassword`, read root-only, never printed) into the database named in `wp-config.php`.
- **C** — the `wp-config.php` login (S591's road: socket, then 127.0.0.1:3306).

**What it changes, and only this:** the e-mail address fields (Email to / cc / bcc; Email 2 to / cc / bcc) of every Elementor form in
every page, post and template that is not a revision lose any address at the firm's domain. A "to" left empty gets the clinic Gmail.
Each changed row is kept byte-exact (hex) in `/root/s592_backup/` (root, 600) first, and written only if it is still the bytes read.
Everything else that mentions the domain — other form settings, old revisions, posts, site options, users — is **listed, never changed**.
If the site keeps a persistent object cache, the changed pages' cached settings are cleared (`wp cache delete <post> post_meta`).

**Housekeeping (S326 close, B8):** removes `/tmp/s578kit` and `/tmp/s581kit` if present.

**Rehearsed offline (S329), on MariaDB 10.11 with Elementor-shaped page data written by PHP's own `json_encode`:**
control — S591's logic alone on a refused wp-config login: STOPPED (red, as on the box) · road A answered (a PHP notice printed
before the rows was ignored) · A refused → B taken · A, B, C all refused → STOPPED, nothing changed · real run on A: two rows changed,
only the address text differs byte-for-byte, the revision untouched, the Hindi text's escapes kept · second run: nothing to change ·
`--undo` on A and on B: every row back to its original MD5 · object cache present: `wp cache delete` called for each changed post.

**Proof (rule 35):** one test through the form's own handler, the site's answer *"Your submission was successful."*, and that mail read
in the clinic Gmail with its recipients — only the clinic Gmail.
