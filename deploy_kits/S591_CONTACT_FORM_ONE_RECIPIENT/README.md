# S591_CONTACT_FORM_ONE_RECIPIENT — patient enquiries from the website go to the clinic Gmail only (D742)

**Why.** The S590 contact-form test (18:40 IST 18-Oct-2026) arrived in the clinic Gmail addressed to two recipients: the clinic Gmail
and an outside marketing firm's address (domain `arrowmarketing360.com`). Every enquiry from the website — the patient's name, mobile
number and treatment — was being copied to them. The owner, 18:41 IST: *"remove"* (**D742**). Board `_numbers` v504 → v505.

**What it changes, and only this.** In the website database, the Elementor page data (`_elementor_data`) of every page, post and
template that is not a revision: in each Elementor form widget, the e-mail address fields — Email: to / cc / bcc; Email 2: to / cc /
bcc — lose any address at that domain. A "to" left empty gets the clinic Gmail (an e-mail action with nobody to send to fails). The
page data is read and written as hex, and each change is a match on the stored `"key":"value"` pair, so no other character of the
page is re-encoded (the `\/` escapes, the unicode, the spacing stay as they were). Each changed row is kept first, byte-exact, in
`/root/s591_backup/` (root, 600); a row is written back only if it is still the bytes that were read.

**What it lists, never changes.** Every other place in the database that mentions the domain: old revisions, other page settings,
post text, site options, users, user settings — so anything else the firm still receives is named, and decided on separately.

**Run (the owner, after publishing):**
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S591_CONTACT_FORM_ONE_RECIPIENT/install_S591_CONTACT_FORM_ONE_RECIPIENT.sh`
(`DRY=1` in front: finds and says what would change; nothing changed.)

**UNDO (one line):** `/usr/bin/python3 -B /root/deploy/repo/deploy_kits/S591_CONTACT_FORM_ONE_RECIPIENT/fix_s591.py --undo`

**Proof.** Rehearsed against a stand-in database (SQLite behind a stand-in `mysql`, with the HEX / UNHEX / MD5 the script uses, and a
database password holding a double quote, a dollar sign and an escaped single quote — the login only succeeds when it is read whole):
the PHP-shaped page data (no spaces, `\/` escapes) and a spaced one; DRY lists and changes nothing; the run changes the two live pages
(one "to" left empty → the clinic Gmail), leaves the revision and the other mentions alone, writes 600 backups and reads back; a
second run finds nothing to change; `--undo` puts the page back byte-exact. After the install the assistant sends one more test
through the form and reads its recipients in the clinic Gmail.
