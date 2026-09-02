# START HERE — SESSION 220 · entry point written at the S219 close, 02-Sep-2026

Hi Claude. Continuing my clinic-automation project — **Session 220**.
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

---

## §0 — THE STANDING OWNER RULINGS (restated every session)

1. **Publishing is MY double-click.** Name one file, full path:
   `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
2. **Full paths ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Use `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4); never print secrets or tokens. F-185: no number at all in the
   repository.**
7. **Nothing live is rebuilt without my OK; the manual path stays the fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand me diagnostics to run.** Ask for the one action nobody else can do, in one line.
10. **When a screen is wrong, read the screen's own code FIRST.** The server is the last suspect.
    *(This paid for itself at S219: F-278 was caught before shipping.)*

**Two holds are standing.** **AUGUST PURCHASE IS PROVISIONAL** until I say the words — enforced by
`_PROVISIONAL_AUGUST_PURCHASE.md` markers in `MargArchive\`. **NEFT portal WAITS.**

**D361 — THE PAST IS ACCEPTED.** From 02-Sep-2026 we work each day's Marg export forward.
Historical returns keep their verdicts and their money and remain the detector's baseline; they
raise no task. The line is the setting `returns.act_from`, not a constant.

---

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · CHECK THE CONNECTIONS AND PROMPT ME. Before anything else, every time.**

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, **no ClaudeCowork** — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** (1 TB SSD) | the close cannot mirror or take a cold kit |
| **the assistant's browser** | no live-page reads, no portal verification |

⚠ **`F:` never mounts in the device shell — that does NOT mean unreachable**: the file-transfer
tools read and write it perfectly. ⚠ **The assistant's browser is stuck in the F-242 login loop.**

**2 ·** Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin).
**3 ·** **Verify every row by md5.** Halt on a hash mismatch, never on absence from one store.
Verify a kit gate **from inside its own folder**.
**4 ·** **Read only Tier 0:** manifest · `START_HERE_PROMPT_v8` · **KB Register v5.67** ·
**HANDOFF_RUNBOOK v151** · `OWNER_TODO_LIVE.md` · any open incident.
**5 ·** Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and read
`03_WORKING_PAPERS\S219\S219_BUILD_BRIEF.md`.
**6 ·** Then confirm, and start ⭐1-1 below unless I say otherwise.

---

## ⭐1-1 — THE FIRST BUILD OF THIS SESSION, BY MY RULING

**THE INGEST NAME-CHECK (F-277).** My words at the S219 close: *"the Marg ingest which you will
build is a good thing, and this one we should do in the next session as the first thing so as to
polish out and complete the entire marg system."*

**The fault, measured.** `finance_ingest.resolve_patient()` states it in its own docstring —
*"Clinic ID first, name only as a hint"* — and never compares the bill's name with the master's.
**5 of 43 August returns (12%)** carry a clinic ID belonging to someone else: `762` is Daljeet
Singh while the bill is Paramjeet Kour's; `638` is Saloni Shrivastav; `782` is Trishna; `7837`
disagrees with the books; `212` is not in the Docterz master at all. The stranger is attached
**silently**, and every audit afterwards judges her returns against his purchases with complete
confidence. **This is worse than F-273's WALK-IN pooling, which at least announces that it does not
know.**

**The shape to propose to me first** (it is a money-path change): a disagreement becomes a
**finding**, not a tiebreak. Verdict **"identity disputed"** — amber, routed to Darpan, never a
money verdict — on the same principle as S219's stub-guard. The evidence is
`D:\Downloads\returns_docterz_match_Aug2026.csv` (built at S217/218; **search it before deriving
anything new** — F-276 was minted for exactly that omission).

**Then ⭐1-2: the scanner A5 vertical resize.** My report: *"the a5 button doesn't do vertical
resize."* Diagnosed at S219 — `fitAspect()` covers the content box in BOTH directions, so a too-tall
box keeps its height and widens instead of shrinking. Deferred by me, not forgotten.

Everything after that: **HANDOFF_RUNBOOK v151 §2** and `OWNER_TODO_LIVE.md`.

---

## NEXT FREE NUMBERS

**D362 · F-280 · Session 220.** The S214, S215 and S216 candidate sets and F-244 still await my
ruling.

---
*START_HERE_SESSION_220 · written at the S219 close, 02-Sep-2026. The evergreen
`START_HERE_PROMPT_v8` remains the custom-instructions template; this is the session entry point.*
