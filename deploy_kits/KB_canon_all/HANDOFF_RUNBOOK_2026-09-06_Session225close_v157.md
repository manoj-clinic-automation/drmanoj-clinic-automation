# HANDOFF RUNBOOK — S225 close · 06-Sep-2026 · v157

*Supersedes v156 (S224 close). §0 what happened · §1 the models it earned · §2 the live backlog (the live list is `OWNER_TODO_LIVE.md`; this is the close-time snapshot) · §3 install discipline · §4 the boundary. Full narrative: Archive §S225. Pins: Register v5.74, `live_pins_S225close.txt`.*

---

## §0 · WHAT HAPPENED

**Fifteen attended hours, 04-Sep 13:00 → 06-Sep 04:00, two calendar days, a model switch at 20:00 (the owner's opus budget at 99 %; Sonnet to ~00:30, then Fable).**

1. **The readback fold** (v5.73): fourteen values from the box; **F-320** raised and closed in one sitting (the box ran a kit's rev 1, republished as rev 2 five minutes later and never reinstalled).
2. **The owner's dictation** (`S225_OWNER_RULINGS_04SEP`) → D371 (advances unparked, loans view first), D372 (August close terms), the ₹3,00,000 deposit, the tracker study before its parser fix, three purchase-flow rulings. **His answers on the procedures draft** → D373 (`S225_PROCEDURES_RULED`). **The tracker read whole** (`S225_FOLLOWUP_TRACKER_STUDY`).
3. **The seven §8 kits** — `purchase_app.py` revs 6 → 11b, each from one line, each read back: staff order page · phone book (+ the owner's rounding rule moved into the engine) · arrival flow · live cross-check + stock in transit · new-items log · Amir's salt work list with Marg's own list beside it · the stock snapshot on capture (manojz). **F-321** on the way (a walk that ran after the copy) — answered: every walk on a probe copy. **The salt list rebuilt** after the owner caught it re-asking his 154 answers.
4. **The loans view** (`staff_ledger.py` rev 3; D374 approve-then-attach) · **the bank-MPR line on the Day Revenue page** (`finance_clinic_day.py` `713bdf3a…`).
5. **The NEFT vendors** (ALL CAPS, 19:55): `S225_NEFT_IMPORT` — 24 verified vendor accounts from the PC-side NEFT master written into the phone book (5 updated, 19 created bank-only), **D375**; lengths 24/24 proven. Then **rev 12 `3adad7f9…`**: full bank details to the three editors, bank named from the IFSC, inline forms, no popups (353/353, walk 31/31).
6. **The stock check made ready** (`S225_STOCK_CHECK_READINESS`): the drift page said *never received*; the cause read from the logs (**F-323**); offline 372/373; `S225_EXPECTED_ON_CAPTURE` built (12/12) and **chained into the 10-minute pull** — proven unattended at 02:50; **day 1 on the page**; both gaps read to the unit from the owner's own Marg ledger (a duplicate item merged; bill A003396 entered after its day's report → **D376**, the two-day morning export); **F-322** (the pusher's fewer-rows rule) raised. The wall card updated. How staff reach the count page: their own card.

**Canon:** Archive v1.71 (+16,855 → 1,154,675, prefix proven) · Register v5.74 · Fault v2.56 (F-322, F-323; F-320/F-321 closed) · this runbook · `START_HERE_SESSION_226` · `S225_BUILD_BRIEF` · `live_pins_S225close.txt`. **Next free D377 · F-324 · Session 226.**

---

## §1 · MENTAL MODELS THAT EARNED THEIR PLACE THIS SESSION

- **The event, not the clock.** Every feed that waited for a fixed hour failed when the PC was asleep at that hour; every feed that fires on arrival worked. Marg's side (S225 morning) and ours (S225 night) both moved to *on capture*, and then into the pull cycle itself — the one job that already runs whenever the machine is awake.
- **A hung instance is a silent scheduler.** Under the default 72-hour limit a stuck run blocks every later start of the same task and nothing says so. Every task gets an execution limit at registration.
- **A difference on the drift page has one of four causes, and the ledger tells which:** arithmetic (same gap every run) · the shelf (a gap after agreement) · a duplicate item master (one product, two names) · **a bill entered after its day's report was exported** — invisible to the books by timing alone. The last is why the sale report is now exported for the last two days.
- **"Fewer rows" is not "a filter".** A merge, a discontinued item, a rename all shrink a report. The router's ≤ 60 % SUBSET test is the rule; a threshold must be a proportion, never "any fewer".
- **A machine never grants VERIFIED (D370) — except when the owner's written ruling is the verification (D375).** The exception is executed once, logged with the ruling's name in `bank_verified_by`, and the door stays shut afterwards.
- **A gate that refuses the assistant is doing its job.** F-185 caught dummy phone numbers in a selftest; the publish caught `.pyc` files; both fixed at source, neither suppressed. Test data carries no digit-runs; test runs sweep their cache.
- **Read the page's data, then act.** The owner's ruling for the drift and count pages: the readiness lines (last bill number, purchases current to, export time) come **before** any result — *"read first, know the data."*

---

## §2 · THE LIVE BACKLOG (snapshot; `OWNER_TODO_LIVE.md` is the live truth)

**⭐0 — the owner's own actions:** the wall-card reprint (F-310; the card now carries D376) · the August advances on the ledger's New-entry page (Surendra ₹13,000 with schedule; Darpan ₹15,000; Parvesh's exit) · one word on the S182 tiles · FINALISE September and August on the Marg Purchases tile · the delete lists (`_to_delete_S224\`, `_to_delete_S225\`, `_stale_git_locks_S225\` per drive root) · the nightly's 30-minute limit (one PowerShell line, another account's task) when convenient.

**⭐1 — build next, in his order:**
1. **The drift and count pages open with data-readiness lines** (sale report current to *date* + last bill no · purchases current to *date* + that day's bills as bill-wise lists them · stock export date/time and processing time), and **every check result is logged** with counted vs expected, the horizon lines, and *"all sale returns up to CN ___ dated ___ processed"* (extends `S221_STOCK_AUDIT_FINDING_DESIGN`). Which figure the staff order page shows ("Stock now" = ours, not Marg's) said on the page.
2. **The computation moves to the server** — `S226_EXPECTED_ON_SERVER`: port `push_expected.compute()` and the S206 sale-line reader beside `stock_app.py`, run on the server's own accept event, baseline pinned in a `setting` row; prove byte-equal against the PC side on the same day before the PC leg retires. After rev 2 proves one morning (Sunday 06-Sep).
3. **The S208 kit revision** — F-319 wording · F-322 the SUBSET rule · F-323 cache-first / bounded token read. Walk against the archive's real twins.
4. **Marg pending:** the SALT WISE ITEM LIST signature (and `push_salts.py` reading the archive) · the scan-form pre-fill (asset app) · a "backdated / edited voucher" class on the drift page · a fourth movement type if Marg's issue/transfer vouchers ever appear.
5. **Phone numbers for the 17 bank-only stockists** (inline *add numbers*, or Marg's party master export if it carries mobiles — the owner's call).
6. **NEFT files:** verify July's Marg purchases against the July bulk NEFT file (Shavez folder, Drive) · store April–June bulk files on the VPS when the owner provides them · then the NEFT readiness work from the FINALISED supplier-wise statement (nothing sent).
7. **Then:** the staff PWA loans view (after he has seen `/ledger/loans`) · the loan form · a final-settlement concept · the procedures module as ruled (D373) · the S223 dawn specifications in his order · the tracker parser fix, then the diagnosis export as a third daily upload.

**Parked by him:** the bank-name dropdown · the spot-count bridge · attendance under the main domain.

**Standing holds:** NEFT — readiness work may proceed, nothing is SENT without his word · the hub's shape is not reopened.

---

## §3 · INSTALL DISCIPLINE — what S225 added

- **The walk runs on a PROBE COPY (F-321).** `rm -rf /tmp/<kit>_probe && mkdir … && \cp -r /root/finance/*.py *.sql … && \cp <new> walk_*.py /tmp/<kit>_probe/ && FIN_DIR=/tmp/<kit>_probe FIN_DB=/root/finance/finance.db … walk … && \cp <new> /root/finance/`. The live folder is written only after green; rollback BY PIN to the previous rev.
- **A data import is not an install.** Dry run by default (reports every row, masked), `--apply` writes after a timestamped db backup, `--delete-source` removes the real-data file from the box; the script carries no real value; the source stays outside the git tree; a length-only manifest proves completeness without moving a digit.
- **Test data carries no digit-runs; test runs sweep their cache** (F-185, the `.gitignore` check). `PYTHONDONTWRITEBYTECODE=1` or `python -B` — and `py_compile` still writes; move `__pycache__` out afterwards.
- **A live `.bat` on manojz is patched by anchor with CRLF preserved and a backup beside it**, then the record copy goes in the kit; the pin is hashed on manojz.
- **Every scheduled task registers with an execution limit** (10 minutes for a pusher) and the battery flags (F-314). A PowerShell registration is handed as a `.bat` that runs a `.ps1` beside it and **pauses** — a pasted line that runs in a window that closes is unverifiable.
- **F-233 stands and was breached:** `git status` against the mounted repo leaves a stale `index.lock` the bridge cannot delete. Look at the tree with `ls`/`find`, never `git`; if a lock appears, rename it into `_stale_git_locks_S###\`.
- All of S224's and S223's rules stand.

---

## §4 · THE BOUNDARY

- **The publish is the owner's double-click**: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
- **Patient data is not in this project. No number in the repository (F-185)** — vendor phones and bank accounts live in `finance.db` on the box and, for the NEFT master, in `D:\dr-manoj-git\NEFT_Vendor_Master\` outside the git tree. **Full account numbers are shown on exactly one page, to exactly three people (D375); everywhere else, last-4.**
- **Nothing here ever writes to Marg, sends to a bank or a vendor, or leaves the server** (D325). The NEFT file, when it is built, is generated for a person to sign and send.
- Nothing live is rebuilt without his explicit OK; the manual workflow stays as fallback.
- **ClickUp is parked (D17).**

---
*HANDOFF_RUNBOOK v157 · S225 close · 06-Sep-2026 04:00 IST.*
