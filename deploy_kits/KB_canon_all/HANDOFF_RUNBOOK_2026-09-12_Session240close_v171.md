# HANDOFF RUNBOOK — v171 — at the S240 close, 12-Sep-2026

**Supersedes v170 (S239 close).**

## 0 · WHAT HAPPENED

Two calendar days, three compactions, **fifteen kits**; every VPS change installed by the owner from one
line and read back GREEN, every PC-side file moved through the file bridge and verified by md5 after
staging back. Three chapters.

**The Sanjeevni wave** finished the S239 plan — router and signature fixes, the sale-bill door, the
purchase app, Rung 2's attributed discount, the stock count gate (R1 turned from a RED refusal into an
amber COUNT CHECK that names what to count), late-keyed bills, clipped names resolved without renaming
anything (D466), and the Docterz day page made readable on a phone.

**D467 — the server does the work.** Analysed and documented before a line of code, on his instruction.
The medical PC now only exports and pushes; manojz leaves the data path and stays for development; the
manual upload to the VPS is the worst-case fallback. Built in phases, each proved live before the next
was written: the server collects and classifies (`MARG_INGEST`), computes expected stock itself and
agrees with the PC **374/374** (`MARG_SHADOW`), takes every export through **one door** whatever leg it
arrives on (`MARG_DOOR`), serves that door over HTTPS (`MARG_API`), and the medical PC pushes into it
(`MEDICAL_PUSH`). **56 exports pushed automatically in the first eight minutes; export → server measured
at five seconds.**

**Amir's day** was ruled (D468 … D473) and drawn: seven screens, a 1 → 7 banner, a confirmation per step,
a visible DAY CLOSED screen. Nothing built yet — it waits on his approval of the picture.

**The salary detour.** His suspicion about August's leave deduction was right about the page and wrong
about the money: **F-435**, the footnote said ÷30 while the engine divides by 30.5, and the odd rows were
Sunday weighting behaving correctly. Fixed the same hour. Then D474 (Amir flat ₹2,500), D475 (Darpan off
the common sheet), D476 (his own two sheets, with the month's advance deduction on his), and D477 (**NET
PAYABLE cut to the last ₹10, towards zero**). **August's money never changed** — only what is printed,
who is on which sheet, and the last digit of the net.

**D463 … D477 minted; F-429 … F-438, four of them the assistant's.**

## 1 · WHERE THINGS STAND

**Canon:** Archive **v1.87** · Register **v5.90** · Fault Register **v2.72** (F-0 … F-438) ·
**START_HERE_SESSION_241** · `S240_BUILD_BRIEF` · `CANONICAL_MANIFEST.md` · `MD5SUMS_ALL.txt`.
Next free **D478 · F-439**.

**Live pins (read back from the box):**
`/root/staff_register/salary_policy.py` **92aecbe3** (c7577174 → aabd90fb → d42842e4 → 21b9cd00 →
92aecbe3, four kits) · `/root/finance/finance_app.py` **81db4854** · `marg_door.py` **598ba2df** ·
`/root/marg_ingest/marg_ingest.py` **1a7f266f** · `marg_shadow.py` **4568b4a3** · `marg_take.py`
**4bcf0243** · `stock_app.py` **0b965da4** · `finance_clinic_day.py` **56fb7619** · `purchase_app.py`
**8090ca20** · `push_purchases.py` **a316c345**.
**manojz:** `marg_router.py` **da8fc928** · `signatures.json` **65d1e1ee** · `push_expected.py`
**4b3b700c** · `REGISTER_DOCTERZ_PICKUP.bat` **f2ae1169** · `.gitignore` **911345d9**.
**Medical PC:** `marg_push.py` **630fc5ef** · `marg_watch.py` **581ff3a7** · `medical_agent.py` live
**70d5c4e3** (S205.1) — **the repository copy is still the stale S203.3.**

## 2 · WHAT TO START ON

**`START_HERE_SESSION_241`.** In order:

1. **Reprint August and lock it.** The money is settled; the nets now end in a zero.
2. **D467 phase 2 remainder** — the medical PC starting at power-on instead of logon (one visit, one
   double-click, plus a single-instance lock in `medical_agent.py`) · the Drive copy of each capture and
   the `FromMedical` share · the "no export today" alarm (2c).
3. **Then phase 3** (retire manojz's data jobs) and **phase 4** (manojz = development only).
4. **Amir's seven-step PWA** once he approves the picture, and the claim queue on Darpan's PWA.
5. Carried: the stale repo `medical_agent.py` · the unmasked `marg_report.py` on manojz and the medical
   PC (replace with **eeab5605**) · ~300 stray `marg_watch.py.before_*` files on the medical PC (deleting
   is his) · manojz's Task Scheduler to be read back when the device shell works · the DECA +5 · F-436's
   purchase serial (parked at his word).

## 3 · THE TRAPS THIS SESSION EARNED

- **Prove a file complete by its own content, never by a vendor's footer string (F-429).**
- **Every `schtasks` task clears the battery flag in the same breath (F-430).** F-314 repeating.
- **Liveness is the last COMPLETION, never the last start (F-431).**
- **Run `git check-ignore` over every new kit file before naming a publish (F-432).** A blanket `*.json`
  silently kept a kit file out of the repository while `SUMS.md5` said it was there.
- **Both sides of a comparison need independent provenance (F-433).**
- **An explanation that merely fits the number is a hypothesis (F-434).**
- **A number and the sentence that explains it are one deliverable (F-435).**
- **Tell a helper where the live module is; never let it infer from where it was launched (F-437).**
- **A proof asserts exactly what the change claims — no more (F-438),** or a correct change is rolled
  back by its own guard. It rolled back cleanly both times, which is the part that worked.
- **A file that arrives is not a file that arrived intact** — a Drive upload was corrupted by a typed
  `&lt;&lt;`; the byte count caught it.
- The device shell still mounts nothing. Stage → container → commit → re-stage → md5 worked every time.

## 4 · THE BOUNDARY

**Changed this session:** the VPS finance app (ingest door, marg API, stock gate, day pages, purchases),
the VPS staff register's `salary_policy.py`, manojz's router/signatures/push_expected and the Docterz
pickup task, and the medical PC's `marg_push.py` and `marg_watch.py`. **Not changed:** the staff ledger,
the reconciler, the portal, the attendance core, `medical_agent.py`. **Marg is never written to.**
Deleting files on his machines is still his, never the assistant's.

*HANDOFF_RUNBOOK v171 · S240 close · 12-Sep-2026.*
