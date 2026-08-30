# HANDOFF RUNBOOK — Session 207 close · 28 August 2026 · v141

**Tier 0. Read at Phase 0 with the manifest, the Register and any open incident.**

---

## §0 — WHAT HAPPENED

**A build session that ran from 27-Aug 23:55 to 28-Aug ~15:00 IST.** It began unattended on the
owner's instruction and became the longest in the project. **Nine kits staged. Nothing installed.
The VPS was never touched, and `assetapp/scanner_widget.js` carries the same md5 it had at the
start.**

### Built

| kit | what it is | checks |
|---|---|---|
| `S207_REINSTALL_VERIFY` | read-only `VERIFY.bat` per machine — **live-proven** | 33 + 41 |
| `S207_STOCK_CHECK` | the staff count page, every item, alphabetical | 32 |
| `S207_STOCK_VPS` | the stock ledger — difference → cause → closed | 37 |
| `S207_PO` | purchase orders, cover-based, phones built in | 23 |
| `S207_RETURNS` | the returns lifecycle + the evidence-graded expiry list | 49 + 31 |
| `S207_JOINER` | adding a person, and removing one | 65 |
| `S207_SCANNER` | scanner v2 — autocrop, layout, tap targets | 53 |
| `S207_SALT`, `S207_FEFO` | alternatives, and sell-this-batch-first | 11 |

### The three times this session was wrong in public

**1. The expiry list was withdrawn.** Twenty-eight items reported as flagged and still held, with a
nine-item cluster read as *"one return that never went."* The owner challenged the source and was
right: `read_expiry` unioned every export held, the oldest **3-June-2025**, and **Marg's
closing-stock export carries no batch column at all** — so a match could only prove the ITEM had
stock, never that THAT BATCH was there. **The cluster was an artefact of the method.** A fresh
export the same day returned **one row: VINBACTUM DS.**

**2. F-185 was broken by this session's own kit** — eighteen supplier numbers committed inside the
repository, with **every existing guard passing.** Caught before publish.

**3. The scanner's first detector was 26% wrong on every case** — it thresholded the card's own
border away and locked onto the text block. Three more wrong turns followed, plus one in the test
harness itself.

### What the owner ruled — R1 … R11

Two change how the clinic works, not just what the code does:

- **R6 — the manual expiry-removal method is retired.** Every removal is now a **Marg stock
  adjustment voucher**. *This also explains three items holding units that appear on no current item
  list: the same removal seen from the other side, with nothing written down.*
- **R11 — an employee code is never reissued.** `punches.csv` is append-only and keyed on
  `(user_id, datetime)`; the name behind a code lives only in `staff_master.csv`, which holds only
  rows that still have one, **every one written `active="Y"`.** A reused code silently rewrites a
  departed person's history.

---

## §1 — MENTAL MODELS EARNED THIS SESSION

- **An empty or small result is not good news.** A list that should have rows and comes back with
  none is a fault until proved otherwise. This session's worst answer read as a clean shop.
- **A path in a document is not provenance.** `D:\ClaudeCowork\` was written into three canonical
  places and is wrong in all three; the folder is at `D:\Downloads\ClaudeCowork\`.
- **"May lag" is not "may be skipped".** Marking the biometric step late-ok let the staff-master
  step be signed off without it — the exact hole the register exists to close.
- **A rule that depends on remembering it is not a rule.** F-185 was read and broken within the
  hour. It is now a program that fails the build.
- **A wrong answer that reads like good news is the one nobody questions.**
- **Vendors settle by the month, so a deadline is a date, not a day count.**

---

## §2 — OPEN BACKLOG (the live list is `OWNER_TODO_LIVE.md`; this is the close-time snapshot)

**Owner actions**

1. **Publish** — `PUBLISH_ALL.bat`. Nine S207 kits plus `S205_B` staged. **Run
   `deploy_kits\NO_PHONE_NUMBERS.py` first.**
2. **Install the stock ledger** — two lines in `finance_app.py`. Everything downstream waits on it.
3. **Amir** — steps 1–4 of the joiner today; biometric on his next visit.
4. **Pravesh leaves 31-August** — three days. First run of the exit side.
5. **Seed the employee-code register** from `punches.csv` **and** the roster, before anyone is
   enrolled.
6. **Token rotation** — still the oldest open item.
7. **`RUNVACE TP` expires next month**; `ASTOFEN R` is minus 3 strips 8 and cannot be returned until
   counted.
8. **Ratify or renumber the F-series fork.** F-218 … F-236 are candidates; none minted.
9. **Rule on §S205's missing narrative** — reconstruct, or record as permanently lost.

**Next to build**

Bake the scanner in · the exit flow · persist the PO · the ladder into the engines · the exchange
path · staff onto the portal · the corrections tile.

---

## §3 — INSTALL DISCIPLINE

**Nothing in `deploy_kits/S207_*` is installed.** Each kit carries its own README with the install
lines and its selftest. **Publishing is an attended action** and always has been.

**`assetapp/scanner_widget.js` was NOT swapped.** `S207_SCANNER/BASELINE.md5` records the file v2
was cut from, so the rollback is exact.

**Contact numbers live in `D:\Downloads\margsync\_config\`, outside the repository (F-185).**

---

## §4 — THE BOUNDARY

The VPS was not touched and no credentials for it exist in this environment by design. No live file
on either PC was swapped. Nothing was published to GitHub. `MargArchive` was not written to — it is
the record, and the watcher owns it.

**Two things this close could not do:** the Notion connector and the Drive mirror are reported
honestly in the close report rather than assumed.

---
*v141 · S207 close · supersedes v140.*
