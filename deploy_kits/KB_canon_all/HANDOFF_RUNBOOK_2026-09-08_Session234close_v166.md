# HANDOFF RUNBOOK — v166 · written at the S234 close, 08-Sep-2026 (20:00 IST)

*Tier 0. Supersedes v165 (S233 close). Read with `CANONICAL_MANIFEST.md` and
`START_HERE_SESSION_235.md`.*

---

## §0 · WHAT HAPPENED

**The D432 detour closed whole, in one attended day.** All five items done: three kits built, walked
and **installed live**; two canonical documents corrected; the fifth item answered by measurement
rather than left open.

| # | item | outcome |
|---|---|---|
| 1 | Payment Register as a real VPS table | **LIVE** · `payments_register.py` `fa12a0a1…` · 250 rows · cron 02:05 |
| 2 | The third personal book into the backup | **LIVE** · 5 books, 10 rows, 2 files in the shipped bundle |
| 3 | The two renewal registers reconciled | **DONE** · `Renewals_And_Vendor_Register_v2_S234` |
| 4 | Weekly script re-export + drift check | **LIVE** · `gas_export.py` `072a9411…` · Sunday 02:20 · 3 projects |
| 5 | The duplicate + the orphaned trigger | **DONE** and **ANSWERED** |

**Also cleared at the open:** `KIT_ID.txt`, stale by seven sessions, and `deploy/push_kit.bat`,
which was the only file inside canon and outside its own hash gate. Gate **435 → 436 rows, exit 0**,
rebuilt from the previous row list and diffed per F-374 — added one, dropped none, one hash changed.

**New fault codes:** **F-377** · **F-378**.
**Decisions:** **D433 · D434 · D435 · D436**.
**No SOP change. No surveillance-scope change. No screen changed behaviour.**

---

## §1 · MENTAL MODELS — the four this session paid for

**1 · Intact is not even unchanged.** A0 already says *intact is not valid*. F-377 extends it: the
Payment Register sheet is byte-perfect, hash-green and complete, **and 95 of its 250 rows mean a
different date from the one its author wrote**, because Google re-read an appended day-first string
as month-first. Nothing is corrupt. Everything is intact. The meaning moved. **Ask what a file means,
not only whether it survived.**

**2 · A refusal that reads like a note is worse than a crash.** F-378 printed *"there is no
repository copy to compare against"* three times, in the calm part of the output, while the copy sat
right there and half the kit did nothing. **When a check reports "nothing to do", make it say WHY
there was nothing, and put a test on the case where there was something.**

**3 · The fixture shares the defect's blind spot.** F-378 sat behind 24 selftests and a 26-check
walk because every fixture was built by the exporter's own writer, so both sides always had the meta
file the real world lacked. **A green selftest proves the kit, not the join** — and the join is
whatever the fixture did not think to be.

**4 · A wrong instruction beside a right date is worse than a wrong date.** Both renewal registers
carried *"auto-renew is ON — just verify the charge"* for a domain that had none. **A wrong date gets
noticed when nothing happens; a wrong instruction gets obeyed.** The nag prints the note verbatim.

**And the standing one, proved twice more:** ⭐ **his challenge to a plan is data, not an objection.**
He was right about the auto-renew, and right that Bhawna's licence expiry was already in his own
`govt ID` tab — **the assistant asked him for a value he already held.** *Search the whole of what he
has before asking him for anything.*

---

## §2 · THE LIVE BACKLOG

### ⭐1 · NEXT — Sanjeevni steps 2+3, clubbed (D432's own order)

Derivation off the screens; the four lanes pointed at the **item spine built at S229 that nothing
reads yet**. Every derived number carries its **coverage as data, not as a sentence**. **No screen
changes behaviour.** S229's reason they club: *"separately they each look like churn with nothing to
show, and together they are the moment the screens stop disagreeing."*

Then **step 4 — sections as jobs**, screen by screen, **with him: he asked to be part of it.** Six
role maps (`S230_SURFACE_AND_ROLES` §6), not forty-two tiles. Three cheap fixes ride along: one Stock
Check tile sending three people to the same wrong door · no list of counts and no "start a new count"
· six English money-tile names a Hindi-first staff member cannot tell apart.

### 2 · OWED BY THE OWNER — one value each

- **The expiry on ICICI credit card ·9012.** `dr-manoj.in` now auto-renews onto it (D436); an
  auto-renew pointed at a dead card fails silently, which is the risk that replaced the old one.
- ~~Bhawna's driving-licence expiry~~ — **ANSWERED at this close: 09-Jan-2030**, from the `govt ID`
  tab and confirmed against the physical licence.

### 3 · PARKED BY HIM, EXPLICITLY, AT THIS CLOSE

**Three date inconsistencies in the `govt ID` tab** — Gauri's passport action date day/month swapped
against the array; Raghav's DL action date a month *after* its expiry; Bhawna's DL carrying one day's
lead instead of thirty. **His words: park it until one source of truth gets populated everywhere.**
Do not fix these piecemeal.

### 4 · BLOCKED ON ONE ANSWER

🛑 **The WABA rotation**, on Ms. Khushi Jain / MyOperator: **do the old and new tokens overlap, and
for how long?** Still the only thing blocking anything. `/root/_quarantine_S232_F368_20260908_111131/`
**must not be deleted until after that rotation.**

### 5 · OPEN, AND ASKED FOR BY HIM

**A v14 of the close-out routine.** He asked at the end of this session whether EOS is necessary and
how far it can safely be shortened. The evaluation was given with measurements and **no ruling was
made**; the offer of a written v14 proposal stands, uncommissioned. The finding behind it: the
routine does two jobs — *prove and pin*, to which every recorded disaster traces, and *narrate*,
which is **seven renderings of one story** of which this session's own open read two.
⚠ **`END_OF_SESSION_PROMPT_v13` is not in `KB_canon_all`** (the folder holds up to v11; the manifest
row reads *project-side*), so the routine enforcing hash verification is the one canonical document
with no hash gate.

### 6 · HELD BY HIM, NOT BLOCKED

The PWA install · the Sanjeevni/Marg project split · getting the encrypted bundle out of Google ·
the call recordings (**still no copy outside Google Drive — the largest unprotected thing in the
estate**) · the raw vehicle-tracker pull · retiring the email side of the legacy scripts.

### 7 · STILL OWED FROM S233, and still owed

**The recording-archive size is an ESTIMATE** from a ten-file sample on one day, not a measurement.
Say so if it is quoted, or measure it. *(The other two S233-owed items were cleared at this open.)*

---

## §3 · INSTALL DISCIPLINE — what this session confirmed

- **Two lines, never one.** The deploy pull, then the installer (F-375). Used three times today,
  worked three times.
- **An installer that touches settings copies them aside first and restores byte for byte on ANY
  failure.** Both of today's installers refused at preflight on their first run — a sheet not shared,
  three projects not shared — and both times **the nightly ran exactly as the night before**.
- **`py_compile` to a temp `cfile`** (F-376). It bit nobody today because it was obeyed.
- **Never run `git` against the mounted repo (F-233).** `rmdir` and `rm` are refused there by design;
  move aside instead, and say so.
- **The publish gate's `.gitignore` check is scoped to `deploy_kits · logo · canonical-docs`** — read
  from `PUBLISH_ALL.bat`, not assumed. A `_to_delete_S###\` at the repo root sits outside it.
- **A prepared kit is proven only by a LIVE-SHAPE walk.** Twice today the live shape found what the
  gates could not: 95 re-dated rows, and a comparison doing nothing.

---

## §4 · THE BOUNDARY

**His:** the publish double-click · every VPS line · every Google GUI action (sharing a sheet, a
registrar setting) · priorities · what a screen should say.

**Mine:** everything else — the reading, the measuring, the building, the walking, the records. He
said it plainly and it still governs: *"My need should be very sparing."*

**And the one added today, by his own correction:** before asking him for a value, **search the whole
of what he already has.** He keeps more of it than the record remembers.

---
*HANDOFF_RUNBOOK v166 · S234 close · 08-Sep-2026. Supersedes v165.*
