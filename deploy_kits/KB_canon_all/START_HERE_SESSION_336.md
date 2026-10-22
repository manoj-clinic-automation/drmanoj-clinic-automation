# START HERE — SESSION 336 — written at the S331 close (the parent), 22-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, on manojz.
1. Run `START_HERE_PROMPT_v10`'s Phase 0 (the project's custom instructions) first, then this file.
2. **A carried build, at his word: D753** (§0 A) — after the open's checks (§0 B).
   - The Runbook is v252 (§2A: the order; §1U: what S331 made live).
   - The owner's paper is `S331_BUILD_BRIEF.md`.
   - The build norm is `BUILD_NORM_v1.md` (D704 — binding). The close routine is `END_OF_SESSION_PROMPT_v18.md`.

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **336 is RESERVED for the parent.** 335 is the Sanjeevni chat's (open since 06:01 IST 22-Oct); 323 is the Scan App chat's, open. Take what the board says and say so in your first line.
- At this close: D754 · F-973 · A-D25 · kit S614 · session 337 next.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- `device_bash` worked through S331. **Never run `git` in it — read-only included (F-511, F-947)** — read `.git/logs/HEAD`, the refs; test `.gitignore` by reading it, last match wins — **over every unpublished folder in `deploy_kits/`, any chat's (F-971)**.
- `.gitignore` blocks `*.json` and `*.mp3` — ship `.json.kit`; a binary travels as base64 text, MD5-checked at install (F-944, F-945).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate runs in the device shell (F-810).
- **A D or F number is taken on the board the moment it is minted, never held (F-920). Read the board's newest line before taking one.**
- **Every commit to the PC goes from a fresh staged path and is read back by hash before the publish is named (F-924).**
- **A published kit folder never changes (F-512)** — S611 and S612 are published; D753 is a new kit (S614 or later) pinned on `staff_ledger.py` 92885f3b.
- **The device shell cannot delete** — move to `_to_delete_S###\` with a `WHY_SAFE.txt`. **`pkill -f` matches its own shell — stop a test server by its pidfile (S331).**

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

---

## 0 · THE WORK — in the owner's order

**A · D753 — THE CARRIED BUILD (his words 05:57 / 06:01 IST 22-Oct; F-967).** *"I am not seeing the 3000 advance of 21st October from November 2026 salary to be cut in November in the top section. Another thing is, while issuing a fresh advance, I should know what are the pending advances. Of that staff."* · *"Build seems okay, but it's been a long session. Do EOS here, and this should be in next session."* On `/root/staff_ledger.py` **92885f3b** (S612; DECLARED-PENDING until the 23-Oct bundle — hash it there first):
1. **The top section** of `https://followup.dr-manoj.in/ledger/statement` — under *Advance remaining after <month>*, one line per advance that makes it up: what is left and when it is cut (*from November 2026 salary* for a quota advance against a later month — `against_month`; *from the monthly amount, oldest first* for the waterfall; the loan with its interest named apart). For Surendra today: Rs 3,000 of 21 Oct — from November 2026 salary · Rs 2,000 left on 17 Aug — from the monthly amount.
2. **New entry** (`https://followup.dr-manoj.in/ledger/`) — when a doctor picks a staff member, in place of the blue *current position* box's two totals: every open advance (date, amount, left, when cut), what this month's close will cut, what is already booked against the chosen *Against which month* (Surendra: Rs 3,000 against November) and the room under the ceiling. The figures are the statement's own (`month_plan()`, `loans_view()`, `advance_month_taken()`, the existing `posmeta` / `advmeta`); no figure changes.
3. The norm: exact counted edits from the live bytes; a walk with the made-up shapes **and** the chain check on scratch copies of the live ledger and register (F-965); a control on 92885f3b that goes red; a rehearsal; a screen review of both pages at phone width by a sub-agent. Then his publish and his one line.

**B · THE OPEN'S FIRST WORK (v18).**

1. **Read the System Board:** every item with a `note`, every message with `read:false` — one line how many (at this close: the eleven old notes A4 … G6 were answered on 15-Sep and are the Sanjeevni chat's; the two unread messages are the Growth and Scan App chats'). **Remind him of the packs page (name the 25 card shops; type the card and ICICI passwords) — every session until done (D713).**
2. **Verify the S331 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main`; this close's files in the tree (Register v5.172, Archive v1.169, Fault v2.157, Runbook v252, this file, `S331_BUILD_BRIEF.md`, `S331_CLOSE_REPORT.md`, `live_pins_S331close.txt`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. Not landed → name the file once.
3. **The three nightly reports** — exists · clock time · verdict, each.
4. **The pin list `live_pins_S331close.txt` against the 23-Oct bundle.** The parent's DECLARED-PENDING is **5**: `/root/staff_ledger.py` 92885f3b (S612 — must be in the 23-Oct bundle) and the four outside every bundle (`/root/deploy/clinic_doctor.py` 45de587b · the drop-in 473eaf2a · `/usr/local/bin/clinic-doctor` e22da9c9 · `/root/portal/static_inbox/lame.min.js` 5a6238f8). State the three counts and the pending count.
5. **MyOperator (F-968):** read ticket 691386 (clinic Gmail thread `1a15248a6b19387e`) and the scheduled task's latest run; one line to him if they gave a cause. **Do not change the senders or the key to work around it (rule 36).**
6. **The SMS test (F-903):** from the newest database copy — `bank_sms_settlement` or `bank_sms_ignored`. One line to him.
7. **The rest:** the SSD mirror listed back · the sweep · the measured project-knowledge size · the four numbers · what no store holds — **`/root/wa/wa_logs/` (AF-19), `/root/wa/wa_inbox/send_log.jsonl` (S608) and `/root/att_config.py` (F-972) are in no backup** · the cold kit when due · the watcher's health (never read out `HOSTINGER_KEY` or `NTFY_TOPIC`).

**C · THEN D753 (§0 A); after it, ask him which one item next** — Runbook v252 §2A items 4–12 are the assistant's list in order.

**ON HIS WORD ONLY — not raised:** the staff's replies typed in the MyOperator app itself shown in the inbox · a *send to Shavez* button for the bank check (D717 (1)) · the follow-up tracker on the server (*"later"*, D717 (2)) · Bhati's later features (D724) · mending `patient_ref`'s first-seen names (F-918).

**PARKED AT HIS WORD — NOT TO BE RAISED; he raises it:** the staff's WhatsApp alerts made loud (D692 — a topic name is a key: never in the repository, a kit, a page, the board or a chat line) · club C — the mailbox clean-up (D702) · the tracker's move (D717 (2)). **Held:** the Callback Tracker move (D634). **The unattended scheduled run: kept off.**

**Owner-side, on his board:** the publish · **the packs page (shops and passwords — remind every session)** · the Marg engineer's restore test · Ranjeet's login · the reception PC's Windows · the Docterz report export · the arms licence (November).

**CLOSED BY HIS WORD — DO NOT RAISE AGAIN:** everything listed so in `START_HERE_SESSION_331.md` stands, and these are added:
- **D750** — the two-touch joining whatever phone, the machine step watched (S606, S607): done;
- **D751** — MyOperator handled from the clinic Gmail without him, the send log: live (S608, the scheduled task);
- **D752** — the statement month by month for every staff member, *"advance remaining"* (S611, S612): live;
- **Surendra's seven no-punch October days** (1, 11, 12, 13, 18, 19, 20) — *"he was not present or he did not punch. He was not working anywhere else."* They stay **A**.

**Before any owner-only or staff-only step in the assistant's browser:** read `https://followup.dr-manoj.in/finance/api/whoami`. **The assistant does not type credentials for him.** **An account-access grant (OAuth consent) is his hand even when he says yes in chat.** **Patient files never pass through the assistant's workspace (D656).** **No phone number in the repository (F-185) — a walk uses made-up numbers.** **Never print the WhatsApp key, the clinic Gmail app password, the CyberPanel MySQL password or any wp-config value.**

**Standing owner rulings (restated):** rules 1–36 of `START_HERE_SESSION_331.md` stand whole. Two are added:

37. **A figure on his screen says what it is made of** — a *remaining after* names the advances in it and when each is cut; interest is never shown as advance repaid (F-964, F-966, F-967).
38. **A statement or salary kit is walked on scratch copies of the live store as well as on made-up data, and a red walk explains itself on his screen** (F-965).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_172_S331close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_169_S331close.md` (§S331) |
| Fault → Action Register | `Fault_Action_Register_v2_157.md` (§7.91 = F-964 … F-972) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-22_Session331close_v252.md` (**§2A the order; §1U what S331 made live**) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S331close.txt` (the parent's DECLARED-PENDING 5) |
| build brief | `S331_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers` — at this close: **D754 · F-973 · A-D25 · kit S614 · session 337 next; 336 RESERVED for the parent; 335 the Sanjeevni chat's, open; 323 the Scan App chat's, open** |

## 2 · WHAT THIS SESSION MADE LIVE — the short map

| what | where | state |
|---|---|---|
| Add staff in two touches (S606, S607, D750) | `https://followup.dr-manoj.in/finance/staff/new` · `staff_easy.py` c5344291 · `staff_easy.html` 05c1f7b8 · `staff_pages.py` 856644e9 | live 18:36 / 19:47 20-Oct |
| The WhatsApp send log (S608, D751) | `https://followup.dr-manoj.in/portal/inbox/sendlog` · `portal_inbox.py` e25bed25 · the scheduled task *MyOperator ticket follow-up* | live 12:46 21-Oct; F-968 with MyOperator |
| Attendance on the salary sheet's rules (S610) | `https://attendance.dr-manoj.in/month` · `att_dashboard.py` 53e215e2 | live 19:39 21-Oct |
| The staff statement, month by month (S609, S611, S612, D752) | `https://followup.dr-manoj.in/ledger/statement` · `staff_ledger.py` 92885f3b | live 05:52 22-Oct |

*Written at the S331 close, 22-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **The Scan App (323, open at this close):** its entry point `START_HERE_SESSION_323.md`.
- **Sanjeevni (335, open since 06:01 IST 22-Oct):** its entry point `START_HERE_SESSION_335.md` — a different chat's file; ours is `START_HERE_SESSION_336.md`.
- **For all, from this close:** the parent's `staff_ledger.py` is at `92885f3b` (S612), `att_dashboard.py` at `53e215e2` (S610), `portal_inbox.py` at `e25bed25` (S608), `staff_pages.py` at `856644e9`, `staff_easy.py` at `c5344291`. Build only from those bytes, and append a PLANNED line before touching them. **Any chat placing a kit with a `.json` in it: its exact-path `!` line in `.gitignore` in the same breath (F-971).**
