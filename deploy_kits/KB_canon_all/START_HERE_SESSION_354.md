# START HERE — SESSION 354 — written at the S349 close (the parent), 25-Oct-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this project, on manojz.
1. Run `START_HERE_PROMPT_v10`'s Phase 0 (the project's custom instructions) first, then this file.
2. **The first work: the open's checks (§0 A), then D786 — the month-end attendance correction flow, live before 1-Nov (§0 B).**
   - The Runbook is v269 (§2A: the order; §1X: what S349 made live **and D786's build notes**). The Register §S349 holds D786 verbatim, D787 and the six new rows.
   - The owner's paper is `S349_BUILD_BRIEF.md`. The build norm is `BUILD_NORM_v1.md` (D704). The close routine is `END_OF_SESSION_PROMPT_v18.md`.
   - **The specification is the mock-up he ruled on:** `https://claude.ai/artifact/8gg5NKJThNmSMJXPgeUNHM` (six artboards; rev 2 + the fallback). Read it (Artifact `read`) before any code.

*FIRST ACT: take your session number from the System Board `board/_numbers` by a version-pinned write (NUMBERS_PROTOCOL_v1).*
- **354 is RESERVED for the parent.** 353 is RESERVED for the Sanjeevni chat (its S350 closed 08:4x IST 25-Oct); 351 is the NK Pathology chat's and 352 the Scan App chat's (open at this close). Take what the board says and say so in your first line.
- At this close: D788 · F-1025 · A-D25 · kit S649 · session 355 next.

*Connect `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.*
- **Never run `git` in the device shell — read-only included (F-511, F-947, F-1019).** Read `.git/logs/HEAD` and `.git/refs/remotes/origin/main` as files; test `.gitignore` by reading it, last match wins.
- `.gitignore` blocks `*.json` and `*.mp3` — ship `.json.kit` unless an allow line exists (`!deploy_kits/*/tile_grants.json` does); a binary travels as base64 text, MD5-checked at install (F-944, F-945).
- Set `SANJ_CONFIG_STORE=$HOME/mnt/Downloads/margsync/_config` before the number gate runs in the device shell (F-810).
- **A D or F number is taken on the board the moment it is minted (F-920).** Read the board's newest line before taking one — four chats write it now.
- **Every commit to the PC goes from a fresh staged path and is read back by hash before the publish is named (F-924).** A published kit folder never changes (F-512). The device shell cannot delete in a connected folder — move to `_to_delete_S###\` with a `WHY_SAFE.txt`. Stop a test server by its pid (`pkill -f` matches its own shell).
- **The device shell works** (S349: `python3`, `tar`, `md5sum`; `pip install --user flask` was needed once to load `portal.py` offline). The 01:35 bundle and the nightly database copy are in `D:\Downloads\_kbtools\vps_code\`; a database copy carries patients — keep it in the device VM (`$HOME/...`), never in the cloud workspace (D656), and remove it at the close.
- **Before saying a new duty line arrives OFF or ON, read whether that person's panel was ever saved** (S347, S349: reception's and Shavez's were not — the seed governs).

***Every time you write is read first — the clock tool, a commit stamp, a file's time or a program's own line (F-510).***

---

## 0 · THE WORK — in the owner's order

**A · THE OPEN'S FIRST WORK (v18).**
1. **Read the System Board:** every note, every message with `read:false`. **Remind him of the packs page (the 25 card shops; the card and ICICI passwords) — every session until done (D713).**
2. **Verify the S349 close's publish landed:** `.git/logs/HEAD` = `refs/remotes/origin/main`, a commit later than `c79ff2e3` (08:26:20 IST 25-Oct) — it carries the Sanjeevni chat's S350 close too; this close's files in the tree (Register v5.189, Archive v1.186, Fault v2.173, Runbook v269, this file, `S349_BUILD_BRIEF.md`, `S349_CLOSE_REPORT.md`, `live_pins_S349close.txt`, the manifest, `OWNER_TODO_LIVE.md`, `MD5SUMS_ALL.txt`); `md5sum -c MD5SUMS_ALL.txt` from inside `KB_canon_all`, with the count. If not landed, name `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
3. **The three nightly reports** — exists · clock time · verdict, each.
4. **The pin list `live_pins_S349close.txt` against the 26-Oct bundle (01:35 IST)** — the three rows of S645 … S647 (`aaj_seed.py` 98f63364, `portal.py` 844166b1, `tile_grants.json` 025f8ab9) must match: **DECLARED-PENDING 7 → 4**. State the counts. A mismatch is a halt.
5. **Read reception's and Shavez's lists live** (read only, as `manoj`): no *Poori list* banner; reception's late-order line reads *Order ka maal nahi aaya — supplier ko call kijiye*. `https://followup.dr-manoj.in/finance/aaj?as=reception`
6. **The rest:** the SSD mirror listed back · the sweep · the measured project-knowledge size · the four numbers (`aaj_seed.py` is at drift 4) · what no store holds · the cold kit when due (last: the S343 open, 23-Oct) · MyOperator 691386 (one line if they gave a cause).

**B · D786 — THE MONTH-END ATTENDANCE CORRECTION FLOW, LIVE BEFORE 1-NOV.** His word at 08:40 IST 25-Oct: build it in this fresh chat. Runbook v269 §1X has the notes: the staging table that counts for nothing until *Approve & save*; *Present* through D338's existing already-approved `present_request` (duty start as the in-time), *Leave* as a sanctioned leave, *Absent* no row; the day list = no machine punch + Sundays; the A4 sheet; four screens (reception, with Shavez and him as fallback; Shavez corrects; his page edits any day and approves); a Save with an on-screen *Saved* everywhere; the salary lock waits; the duty lines. Read `staff_register.py`, `salary_engine.py`, `salary_policy.py` whole from the bundle first; PLANNED line; walk on made-up staff with a control; his publish and one server line; then show him the live screens.

**C · THEN, in order (Runbook v269 §2A):** Shavez's procedure-room line when the Scan App's S648 door is live · F-1022 if he has answered (else ask once) · the nightly's UNREAD count · Zerodha (F-1007) · the Tally check when the accountants reply · the SBI papers · the rest. Ask him which one item only when A and B are done.

**ON HIS WORD ONLY — not raised:** as `START_HERE_SESSION_343.md`. **PARKED AT HIS WORD:** as `START_HERE_SESSION_343.md`. **The unattended scheduled run: kept off.**

**Owner-side, on his board:** the publish · **F-1022's answer** · **the packs page (shops and passwords — remind every session)** · the two finance passwords (Y106) · the SBI downloads · Raghav's Zerodha papers · the Marg engineer's restore test · Ranjeet's login · the reception PC's Windows · the Docterz report export (2022 onward) · the arms licence (November).

**Before any owner-only or staff-only step in the assistant's browser:** read `https://followup.dr-manoj.in/finance/api/whoami`. **The assistant does not type credentials for him.** **Patient files never pass through the assistant's workspace (D656); patient names and clinic IDs never enter the repository.** **No phone number in the repository (F-185) — a walk uses made-up numbers.** **Never print a key, a password or a token.**

**Standing owner rulings (restated):** rules 1–43 of `START_HERE_SESSION_349.md` stand whole (1–42 from `START_HERE_SESSION_347.md`). Two are added:

44. **A new tile goes only to the people an ask names** (D787 — S646 masked both procedure-room tiles for Dr Bhawna).
45. **On every staff and owner screen that changes data, a Save button and an on-screen *Saved*** (D786 — *"a save button with a on screen saved is a must everywhere"*).

## 1 · THE CURRENT CANON — the manifest wins

| what | file |
|---|---|
| Register | `KB_Register_v5_188_S349close.md` (clone only, D550) |
| History Archive | `KB_History_Archive_v1_185_S349close.md` (§S349) |
| Fault → Action Register | `Fault_Action_Register_v2_172.md` (§7.107 = F-1024) |
| Runbook | `HANDOFF_RUNBOOK_2026-10-25_Session349close_v269.md` (**§2A the order**, §1X) |
| close routine | `END_OF_SESSION_PROMPT_v18.md` |
| build norm | `BUILD_NORM_v1.md` (D704) |
| live pins | `live_pins_S349close.txt` (the parent's DECLARED-PENDING 7) |
| build brief | `S349_BUILD_BRIEF.md` |
| numbers | System Board `board/_numbers` — at this close: **D788 · F-1025 · A-D25 · kit S649 · session 355 next; 354 RESERVED for the parent; 353 RESERVED for the Sanjeevni chat; 351 the NK Pathology chat's, 352 the Scan App chat's (open)** |

## 2 · WHAT THIS SESSION MADE LIVE

Three kits: **S645_RECEPTION_ORDER_FLOOR** (reception's list whole; the order duties read the lines the staff floor hid — F-1024) · **S646_PROCROOM_TILES** (*Kal ke procedures* for Shavez, *Procedure room* for him) · **S647_RECEPTION_ORDER_WORDS** (her late-order line in his words). Where things are: Runbook v269 §1X.

*Written at the S349 close, 25-Oct-2026.*

---

## THE OTHER CHATS — a pointer, not a carried section

- **Sanjeevni (its S350 closed 08:4x IST 25-Oct — S644_BUYING_MODEL live 08:22; 353 reserved):** its entry point `START_HERE_SESSION_353.md`.
- **The Scan App (352, open — its S648_PROCROOM_OPEN_DOOR in hand, the count door the parent's Shavez line will read):** its entry point `START_HERE_SESSION_352.md`.
- **NK Pathology (351, open — its first session; D784):** its own project.
- **For all, from this close:** `aaj_seed.REWRITE` now floors `reception.order_arrival`, `shavez.order_followup` and `reception.bill_scan` on `main.purchase_order_line` — **a chat that changes one of those duties' `due_sql` in DUTY_MAP re-runs the parent's REWRITE fit and walks the list for `unread = 0`** (F-1024).
