# START HERE — SESSION 329 — written at the S326 close (the parent), 18-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, on manojz.
1. Run `START_HERE_PROMPT_v10`'s Phase 0 (the project's custom instructions) first, then this file.
2. **One build is carried over by his word — D742, first (§0 A).** He said at 18:47 IST 18-Oct: *"do EOS now and continue this job in a fresh chat in this project."* Do the open's short checks (§0 B 1–3), then S592 at once — do not ask him which item to start; after it, the rest of the open's work (§0 B 4–8), then ask him for the next item (Runbook v244 §2A is the order).
   - The Runbook is v244 (§2A: the order; §1S: what S326 made live).
   - The owner's paper is `S326_BUILD_BRIEF.md`.
   - The build norm is `BUILD_NORM_v1.md` (D704 — binding). The close routine is `END_OF_SESSION_PROMPT_v18.md`.

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **329 is RESERVED for the parent at this close.** 328 is RESERVED for the Sanjeevni chat; 323 is the Scan App chat's, open. Take what the board says and say so in your first line.
- At this close: D743 · F-942 · A-D25 · kit S592 · session 330 next.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- `device_bash` worked through S326. **Never run `git` in it (F-511)** — read `.git/logs/HEAD`, the refs and loose objects (python's `zlib`).
- `.gitignore` is last-match-wins and blocks `*.json` — ship `.json.kit`.
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate runs in the device shell (F-810).
- **A D or F number is taken on the board the moment it is minted, never held (F-920; S326 took five late, at the close).**
- **Every commit to the PC goes from a fresh staged path and is read back by hash before the publish is named (F-924).**
- **A published kit folder never changes (F-512)** — S591 is published: the fix is a new kit.
- **The device shell cannot delete** — move to `_to_delete_S###\` with a `WHY_SAFE.txt`.

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE CARRIED BUILD — D742: the outside marketing firm's address off the website contact form (S592).**

*Why:* the S590 contact-form test (18:40 IST 18-Oct) arrived addressed to the clinic Gmail **and** an address at `arrowmarketing360.com` — every website enquiry (the patient's name, mobile, treatment) is copied to that firm (F-940). His word, 18:41: *"remove"*. S591 (`deploy_kits/S591_CONTACT_FORM_ONE_RECIPIENT/`, published `72b1739b`) stopped at its first check at 18:46: the website database refused the login read from `wp-config.php` (F-938). **Nothing was changed. Until S592 is installed the firm still receives every enquiry — this is the session's first build.**

1. **Find the road that works, from what the box already proved — no new probe line for him if the bundle answers it:** the 19-Oct bundle (`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz`) carries `/root/finance/*.json` — read `s589_probe.json` (`wordpress[0].read_by`, `db_password_shape`, the administrators list it got) and `s588_probe.json`. S589's probe v2 listed the WordPress administrators, so one of its roads reached the database: the TCP retry or WordPress's own `wp` tool run as the site user (`drman1045`, at `/home/drmanojagarwal.com/public_html`).
2. **Build S592** (take the kit number on the board first; a PLANNED line naming the website database's `wp_postmeta` rows of `_elementor_data`):
   - carry `fix_s591.py`'s logic whole (hex read and write, the regex on the stored `"key":"value"` pair for `email_to`, `email_to_cc`, `email_to_bcc` and their `_2` versions, an empty "to" → `drmka.ortho@gmail.com`, the root-only 600 backups in `/root/s592_backup/`, the MD5-guarded write, `--undo`, every other mention listed and not changed);
   - reach the database by, in order: **`wp db query` as the site user** (`sudo -u drman1045 -- wp --path=/home/drmanojagarwal.com/public_html db query`, SQL on stdin) → **the CyberPanel MySQL root** (`MYSQL_PWD` from `/etc/cyberpanel/mysqlPassword`, root-only, never printed, into the WP database name read from `wp-config.php`) → the wp-config login. Say on screen which road was used;
   - the rehearsal includes a stand-in that **refuses the wp-config login** (the S591 failure) and proves the next road is taken; DRY first; the walk and a control (the S591 logic alone, red on the refused login).
3. **His one line** (after the publish): `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S592_<NAME>/install_S592_<NAME>.sh`.
4. **Prove it:** one contact-form test through the form's own handler (`https://drmanojagarwal.com/wp-admin/admin-ajax.php`, action `elementor_pro_forms_send_form`, form `ff75886`, post 91 — a made-up name, no real number, the message saying it is a test); the site must answer *"Your submission was successful."*; then read that mail in the clinic Gmail and state its recipients — **only the clinic Gmail**. Not a click (F-939).
5. **Tell the Growth chat** on the board (a message): the website's mail works (S590), the vendor's FTP is off (S589), the form now mails the clinic only (S592) — and that the WhatsApp widget loads a `-dev` script and an image from `drmanojagarwal.in`, which is being retired (theirs to decide).
6. One line to him: done, and what else in the database still mentions the firm (if anything) — his decision on each.

**B · THE OPEN'S FIRST WORK (v18).**

1. **Read the System Board:** every item with a `note`, every message with `read:false` — one line how many. **Remind him of the packs page (name the 25 card shops; type the card and ICICI passwords) — every session until done (D713).**
2. **Verify the S326 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main`; this close's files in the tree (Register v5.164, Archive v1.161, Fault v2.149, Runbook v244, this file, `S326_BUILD_BRIEF.md`, `S326_CLOSE_REPORT.md`, `live_pins_S326close.txt`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. Not landed → name the file once.
3. **The three nightly reports** — exists · clock time · verdict, each.
   *(Then A — the carried build. Then:)*
4. **The SMS test (F-903):** the first ICICI settlement SMS of 19-Oct (~07:00) — in `bank_sms_settlement` (the fix worked) or in `bank_sms_ignored` with fields `{sms_message},from,text` (the server needs a small reader fix — brief it). Read from the bundle's database copy. One line to him.
5. **The pin list `live_pins_S326close.txt` against the 19-Oct bundle.** The parent's DECLARED-PENDING is **8**: `/root/portal/portal.py` 25cb73e7 · `/root/finance/surgery_cases.py` 7effc05e · `/root/finance/finance_app.py` f2e86ca7 · `/root/wa/casepack/casepack_page.html` 2dfe4221 · `/root/deploy/clinic_doctor.py` 45de587b · `/etc/systemd/system/clinic-watchdog.service.d/s578-doctor-first.conf` 473eaf2a · `/root/finance/slip_log.py` 2419c536 · `/usr/local/bin/clinic-doctor` e22da9c9. Hash `/root/portal/tile_grants.json` in the bundle and record it. State the three counts (match · mismatch · not in the bundle).
6. **Punch step 2 (D713 (4)) is eligible from 19-Oct** — every punch 12–17 Oct carried ONE MARK; tell him in one line and ask only if he wants it now.
7. **The rest:** the SSD mirror listed back · the sweep · the measured project-knowledge size · the four numbers · what no store holds · the cold kit when due · the watcher's health (`lastOk`, `pendingPush`, `log` — never read out `HOSTINGER_KEY` or `NTFY_TOPIC`).
8. **Housekeeping in the next kit's install:** `/tmp/s578kit` and `/tmp/s581kit` on the server.

**C · THEN ASK HIM WHICH ONE ITEM TO START** — Runbook v244 §2A items 6–12 are the assistant's list in order.

**ON HIS WORD ONLY — not raised:** a *send to Shavez* button for the bank check (D717 (1)) · the follow-up tracker on the server (*"later"*, D717 (2)) · Bhati's later features (D724) · mending `patient_ref`'s first-seen names (F-918) · the Case Pack's link opening in the same tab.

**PARKED AT HIS WORD — NOT TO BE RAISED; he raises it:** the staff's WhatsApp alerts made loud (D692 — a topic name is a key: never in the repository, a kit, a page, the board or a chat line) · club C — the mailbox clean-up (D702) · the tracker's move (D717 (2)). **Held:** the Callback Tracker move (D634). **The unattended scheduled run: kept off** (his *"you decide"*, 15:18 18-Oct) — do not re-enable it; quiet the nightly pull's daily WARN about it.

**Owner-side, on his board:** the publish · **the packs page (shops and passwords — remind every session)** · the Marg engineer's restore test · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence (November).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything listed so in `START_HERE_SESSION_326.md` stands, and four are added:
- **D739** — the portal home in ten groups, the eight tiles retired, Dr Bhawna's seven: settled and live (S586);
- **D741** — the vendor's FTP login removed and FTP off (S589); `admin_fix` is his (18:26);
- **the website's mail** — through the clinic Gmail (S590), his *"Why not do this now"*; done;
- **D742** — *"remove"* is given: do not ask again whether to remove the firm's address — only build, install line, prove.

**Before any owner-only or staff-only step in the assistant's browser:** read `https://followup.dr-manoj.in/finance/api/whoami`. **The assistant does not type credentials for him.** **An account-access grant (OAuth consent) is his hand even when he says yes in chat.** **Patient files never pass through the assistant's workspace (D656).** **No phone number in the repository (F-185) — a walk or a form test uses made-up numbers.** **Never print the clinic Gmail app password, the CyberPanel MySQL password or any wp-config value.**

**Standing owner rulings (restated):** rules 1–34 of `START_HERE_SESSION_326.md` stand whole. One is added:

35. **A form or a mail is proven by what arrived, never by what was clicked or configured** — the site's own answer and the mail read in the inbox with its recipients (F-939, F-940).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_164_S326close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_161_S326close.md` (§S326) |
| Fault → Action Register | `Fault_Action_Register_v2_149.md` (§7.83 = F-937 … F-941) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-18_Session326close_v244.md` (**§2A the order; §1S what S326 made live**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S326close.txt` (the parent's DECLARED-PENDING 8) |
| build brief | `S326_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers` — at this close: **D743 · F-942 · A-D25 · kit S592 · session 330 next; 329 RESERVED for the parent; 328 RESERVED for the Sanjeevni chat; 323 the Scan App chat's, open** |

## 2 · WHAT THIS SESSION MADE LIVE — the short map

| what | where | state |
|---|---|---|
| The portal home in ten groups with submenus; eight tiles retired; Dr Bhawna seven (S586, D739) | `https://followup.dr-manoj.in/portal/` · `portal.py` 25cb73e7 · `tile_grants.json` | live ~16:20 18-Oct |
| The bank SMS macro (F-903) | his fold phone; `deploy_kits/PC_KITS/macrodroid/foldphone/macros.template.mdr` cccba9aa | fixed 18:04 18-Oct; test ~07:00 19-Oct |
| The vendor's FTP login removed, FTP off (S589, D741) | `pure-ftpd` masked; `/root/s589_backup/` | live ~18:24 18-Oct |
| The website's mail through the clinic Gmail (S590) | postfix `[smtp.gmail.com]:587`; `relay_s590.py check` | live ~18:34 18-Oct; both tests delivered |
| The contact form to the clinic Gmail only (D742) | — | **NOT DONE — S591 stopped at the login; S592 is this session's first build** |

*Written at the S326 close, 18-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **The Scan App (323, open at this close):** its entry point `START_HERE_SESSION_323.md`.
- **Sanjeevni (328, reserved at its S327 close):** its entry point `START_HERE_SESSION_328.md` — a different chat's file; ours is `START_HERE_SESSION_329.md`.
- **For all, from this close:** the parent's `portal.py` is at `25cb73e7` (S586 — the groups); `finance_app.py` at `f2e86ca7`; `clinic_doctor.py` at `45de587b`. Build only from those bytes, and append a PLANNED line before touching them. A new tile now goes into one of the ten groups of `GROUP_ORDER` (S586) — read `portal.py` 25cb73e7 for how a tile names its group.
