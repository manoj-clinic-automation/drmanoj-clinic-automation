# HANDOFF RUNBOOK — v149 · S216 close · 01-Sep-2026
*Supersedes v148 (S215 close). Tier 0.*

## §0 · WHAT HAPPENED

**The consent session.** Asked for a deep analysis of CP-1's consent screen, the assistant read the
page's own code first and found the consent was **clinically wrong**, not merely ugly.

Driven against the live bytes in a real browser: an elective-THR estimate plus the polio `thr_fnf`
module **generated with no objection, said "worn-out joint", and never said "broken"** — while the
polio module in the same signed document said fracture neck of femur.

Two causes, both in the page:
1. `cpGuessProc()` matched only the estimate TITLE. "Total Hip Replacement" contains neither
   *fracture* nor *neck*.
2. `fmApplyOpening()` inserts fracture wording by rewriting `टूट गई है।` — which **no elective
   opening contains**. The fracture panel was structurally unable to add a fracture to `thr`, `tkr`,
   `acl`, `cubitus`, `implrem` or `osteo`. *That* is why the fracture could not be added.

**S215's 17/17 render test could never have caught it — it hand-picks `thrneck`.**

**Seven kits, all owner-installed the same day, every pin == kit bytes:**
GUARD 19/19 · CONTRAST 9/9 · AYUSH_NAMES 14/14 · STEPPER_BACK 12/12 · SMART 21/21 · TONE 16/16 ·
ORDERS (server **19/19 on the box**) 26/26.

Page `903b915e…` → **`d5d4a3e7…`**. Portal `3146bdbf…` → **`760e8c36…`** — its first move since S215.

**New on the box:** `/root/wa/casepack/med_list.csv`, seeded once from his own template.

## §1 · MENTAL MODELS EARNED THIS SESSION

- **A green test proves the mechanism along the path the test chose to walk.** The render test was
  green because it selected the correct template by hand. Ask every green check what question it
  answers — and what path it took to get there.
- **Intact is not correct, and correct-looking is not clinically right.** 32 selftests and 17 render
  checks all passed over a consent that described the wrong disease.
- **Read the screen's code first.** Both the "missing back button" and the white dropdowns were in
  the page's own CSS and DOM; the server was never involved.
- **A warning that cries wolf is worse than none.** The first transliteration draft would have
  raised the amber warning even when the online engine answered correctly.
- **A field with no edge is not a field.** Contrast maths said 9.5:1 and the box still looked wrong,
  because its fill matched the panel behind it. A sub-agent reading the rendered screen caught what
  no ratio could.
- **Measure before you promise.** The tone draft told the owner three loose English words remained;
  a re-measurement found five.
- **When a gate refuses three times, examine the gate.** The kit gates' PHI check was stricter than
  the project's real rule and was refusing correct builds.

## §2 · THE LIVE BACKLOG

1. **THE AUGUST CLOSE — first item of S217.** Due (Shivani ₹3,774.84 recovery · Arjun's July
   actual-paid · July top-ups ₹4,519 · AF-3 duplicate-advance scan) but **Surendra's ₹516.08 gap is
   still recorded UNEXPLAINED**. Settle that first; a closed month is hard to argue with.
2. **PRAVESH — exit 31 Aug, settlement due now.** Zero rows in the live staff ledger; only the
   **₹569** July top-up outstanding unless August moves it. Owner to rule on the system question:
   a staff member left without ever appearing in the ledger meant to hold her money history.
3. **CASEAPP (D360)** — findings A–D signed; build ordered **after** the remaining Marg work.
   CA-1 first: the case becomes a record in `caseapp.db`.
4. **Five S216 candidates** await the owner's ruling (below), plus the eight carried from S214/S215.
5. Carried: Vaapsi Desk kit 2 · the 360 strip · stock Phase B · F-244 · token rotation.

## §3 · INSTALL DISCIPLINE — reaffirmed and extended

- Anchored patches only; every anchor asserted to match **exactly once**, or the build aborts.
- The kit rebuilds byte-identically from its recorded base, and the gate proves it.
- **Verify a kit gate from INSIDE its own folder.**
- **NEW at S216:** a kit gate must not write `__pycache__`. `python -m py_compile` writes a `.pyc`
  BY DESIGN and `-B` cannot stop it; `.gitignore` excludes it and `PUBLISH_ALL` rightly REFUSES.
  Check syntax **in process** with `compile()`.
- **NEW at S216:** kit gates use the project's real PHI rule — `(?<!\d)[6-9]\d{9}(?!\d)` from
  `tools/phi_scan.py` — never a homemade `\d{10}`, which refuses md5 hashes.

## §4 · THE BOUNDARY

Unchanged. The owner's residual work in a close is ONE double-click of `PUBLISH_ALL.bat` plus the
on-box installs and the pin paste. Everything else is the assistant's.

*v149 · written at the S216 close, 01-Sep-2026.*
