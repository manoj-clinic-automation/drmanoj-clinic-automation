# START HERE — SESSION 271 — written at the S269 close, 19-Sep-2026

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open in a fresh chat in this
project. Run `START_HERE_PROMPT_v10` (the project's custom instructions) Phase 0 first, then this file.

*Why 271: the Sanjeevni chat took Session 270 at its S268 close and wrote its own entry point. Claim
271 on the System Board before you name a scratch folder (F-509 · F-515); if the board has moved
past it, take the next free number and say so in your first line.*

---

## 0 · HIS FIRST TASK FOR YOU, IN HIS OWN WORDS

> *"first task in next session — confirmation on how slips get logged"*

Everything else waits behind that one answer. **Do not design it for him and do not hand him
options.** Read what is already recorded — the paper slip flow is written up in the project memory
and in the S265–S267 papers: the numbered carbon book in his chamber, reception marking a slip
*paid* with the mode and signing it, the X-ray/procedure room keeping a day-wise notebook, Shavez
collecting the slips next morning, and his standing rule that **system numbers run ALONGSIDE the
physical slip numbers, never replace them**. Then ask him the ONE thing that is genuinely his: how
the slip number is to reach the system, given that the Docterz screen reception types into has no
field for it.

The chamber screen is built on his answer, not before it.

---

## 1 · THE CURRENT CANON — the manifest wins, this is only the index

| what | file |
|---|---|
| Register | `KB_Register_v5_111_S269close.md` |
| History Archive | `KB_History_Archive_v1_108_S269close.md` |
| Fault → Action Register | `Fault_Action_Register_v2_96.md` |
| Runbook | `HANDOFF_RUNBOOK_2026-09-19_Session269close_v191.md` |
| close routine | `END_OF_SESSION_PROMPT_v16.md` |
| evergreen prompt | `START_HERE_PROMPT_v10.md` (the project's custom instructions) |
| live pins | `live_pins_S269close.txt` |
| build brief | `S269_BUILD_BRIEF.md` |
| paper policy | `PAPER_POLICY_v1.md` |

**Next free: D557 · F-548 · A-D25 · kit S324 · Session 272.**

**The Register is no longer in project knowledge (D550).** Read it from the clone at
`deploy_kits/KB_canon_all/`, exactly as you already read the manifest (D528). Its absence there is by
design, not a fault.

---

## 2 · WHAT IS LIVE THAT WAS NOT, AS OF THIS CLOSE

| machine | file | pin |
|---|---|---|
| VPS | `/root/finance/owner_sheets.py` | `b354d89326116ce71ef2c7adeda6b23a` |
| VPS | `/root/state_backup/code_bundle.py` | `598e55a4255fef130366eb3c37d78363` |
| VPS | `/root/finance/finance_app.py` | `0191de01e569edc32b8d7c2d67f53471` |
| manojz | `D:\Downloads\_kbtools\canon_sums.py` | `8ad03ef42dc8a4f49e223ccfaa7a3c9c` |

His page: `https://followup.dr-manoj.in/finance/clinic/sheets` — 20 X-ray lines (priced from his own
tariff, D551) and 37 procedure lines (fibre cast / fibre slab pairs named shorthand-first, D552).
Procedure prices are deliberately empty: they are his.

---

## 3 · THE BACKLOG, IN ORDER

1. **The slip-logging confirmation** (§0) — then the chamber screen.
2. **His approvals and the procedure prices** on the page above.
3. **The phonebook work** from the two contact exports of 19-Sep: 7,418 contacts (bocbareilly) and
   2,972 (the clinic account), both in `D:\Downloads`. **They hold patient numbers — F-185: never in
   the repository**, read into `finance.db` or `D:\Downloads\margsync\_config\` only.
4. **The freshness page** (F-540): nothing serves `/root/finance/freshness.html`, so the one surface
   that dates all thirty watched legs has never been readable in a browser. A small owner-gated route
   in the clinic namespace fixes it and makes S310's printed link true.
5. **The `watcher` kit** (D554 / F-547).
6. **The last four units into the bundle** (D555): `fitlog`, `gutlog`, `rxguard`, `email-agent.timer`.
7. **Fault injection for `backup` and `outbox`** — closes D525.
8. **“Attendance report not received”** on the daily report for a week while the attendance mails
   arrive beside it — four unattended nights have named it; no close has taken it.
9. **PARKED until he says otherwise:** the bank-SMS feed.

---

## 4 · THE SIX THINGS THIS SESSION LEARNED THE HARD WAY

1. **The nightly bundle is 01:35 evidence and nothing later** (F-539).
2. **A page kit's walk clicks the page's own buttons** the way a browser resolves them (F-544).
3. **A safety rule that can do nothing must print what it skipped and why** (F-545).
4. **Run `deploy_kits/NO_PHONE_NUMBERS.py` over new kit folders before naming the publish** (F-542),
   and add the `!deploy_kits/…` allow line whenever a kit carries a blanket-ignored file type.
5. **A URL is a live route or it is not printed** (F-540).
6. **`device_bash` WORKS — do not inherit the §4 warning that says it does not** (F-548). At the S269
   close it started on the first call and mounted all three connected roots, **`F:\ClinicBackup`
   included**. The evergreen `START_HERE_PROMPT_v10` §4 still says it refuses to start since the 8-Sep
   Windows update and that `F:` never mounts there: **both halves are stale.** Use it — it reads, greps,
   edits and runs `python3` on manojz, which is the cheapest way to do every PC-side step. Two limits
   are real: a file **cannot be deleted** in a connected folder until he grants it once (rename a stray
   to `*.tmp`, already ignored at `.gitignore` line 108), and **F-511 stands — never run `git` in that
   shell against a connected folder.** This is the second warning in this prompt to outlive its fault;
   the first cost nineteen sessions of the browser. **Re-test a §4 warning at the session that reads it.**

---

## 5 · WHAT IS WAITING ON HIM — and keep it this short

1. `D:\Downloads\_kbtools\NIGHTLY.bat` — one double-click. The 19-Sep catch-up died inside the SSD
   mirror at ~04:03 IST and left a `.new`; the three reports still read 18-Sep (F-546).
2. The publish, when this close names it: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`.
3. The slip-logging answer.

**And how he wants to be spoken to, restated because it was said sharply on 19-Sep:** *"This is a lot
you are writing to me and asking from me. Whatever you want to ask, make it simple, short, and human
readable."* One or two lines. Decide the technical questions yourself. Give him one paste or one
double-click, never a sequence.

---

*Written at the S269 close, 19-Sep-2026. Canon: Register v5.111 · Archive v1.108 · Fault v2.96 ·
Runbook v191 · routine END_OF_SESSION_PROMPT_v16 · pins live_pins_S269close.txt.*
