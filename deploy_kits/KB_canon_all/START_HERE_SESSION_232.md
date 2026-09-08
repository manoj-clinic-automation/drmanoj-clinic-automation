# START HERE — SESSION 232

Hi Claude. Continuing the clinic-automation project — **Session 232**.
I'm Dr. Manoj Agarwal, orthopaedic surgeon, **Dr Manoj Agarwal Clinic**, Bareilly (D424).
Solo practice, older Hindi-first semi-urban patients.

---

## §0 · THE STANDING OWNER RULINGS — these govern every session

1. **Publishing is HIS double-click.** Name one file, full path: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
2. **FULL PATHS ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...` in prose.
3. **ONE LINE PER COMMAND.** A multi-line paste has twice been cut in transit. Use `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS from him = urgent.**
6. **Mask patient numbers (last 4 only) and never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics, investigations or A/B tests to run.** Do the background work; ask
   for the one action nobody else can do — a GUI step, a credential, a decision — in one line.
10. **When a screen is wrong, read the screen's code FIRST.** The server is the last suspect.
11. **Do not put technical or architectural choices to him.** Make the call, state it in one line,
    proceed. He weighs in on what he can SEE: a screen, a wording, a workflow, a priority.
12. **English in his console and in chat.** Hindi is a staff-facing requirement only.

---

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · CHECK THE CONNECTIONS AND PROMPT HIM BY NAME. Before anything else.**

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, **no ClaudeCowork** — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** | the close cannot mirror or take a cold kit |
| **the assistant's browser** | no live-page reads |

⚠ **`F:` never mounts in the device shell — that is NOT unreachable.** The file-transfer tools read
and write it perfectly. ⚠ **`D:\Downloads` has been missing at the open of the last three sessions.**
Ask for it by name; do not work around it.

**2 ·** Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin).

**3 · Verify every row by md5, from INSIDE `deploy_kits/KB_canon_all/`.** A mismatching row halts
work. *A row absent from one store is not a failed row — halt on hash mismatch only.*

**4 · Read only Tier 0:** manifest · START_HERE_PROMPT_v8 · KB Register **v5.81** · Runbook **v163** ·
`OWNER_TODO_LIVE.md` · any open incident.

**5 ·** Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and read
`03_WORKING_PAPERS\S231\S232_BUILD_BRIEF.md`. **One brief replaces ten papers.**

**6 ·** Confirm, then start on **⭐1 below** unless he says otherwise.

---

## THE FIRST THING TO DO, AND WHY

**⭐1 · BUILD THE SECRET GATE IN THE PUBLISH.** On 08-Sep a **live** MyOperator WhatsApp credential
was found in the public repository, where it had sat for **84 days** in a file called
`python test_send.py` — a filename containing a literal space, saved by a mistyped command and never
noticed. The rotation of that token is the owner's to arrange with MyOperator. **The gate is ours,
and it is the part that stops the next one.**

Refuse on: a `Bearer <literal>`, a `-----BEGIN` block, a bare 10-digit number, and secret-shaped
assignments carrying a literal value. **It must NOT flag `os.environ.get("X", "")`** — 69 of those
exist and they are the correct pattern. `deploy_kits/NO_PHONE_NUMBERS.py` is the machinery to widen.

---

## NEXT FREE NUMBERS

**D425 · F-369 · Session 232.**

---

## CURRENT CANON

| | |
|---|---|
| Archive | **v1.78** (§S231 appended; prefix proven, +10,652 → 1,235,895) |
| Fault Register | **v2.63** (F-364 … F-368; +7,142 → 513,423) |
| KB Register | **v5.81** |
| Runbook | **v163** |
| Close-out routine | `END_OF_SESSION_PROMPT_v13.md` — self-contained, A17 mandatory |
| Evergreen prompt | `START_HERE_PROMPT_v8.md` |

---

## WHAT IS OPEN AND NOT CLOSED

🔴 **F-365 — the WABA token is CONTAINED, NOT REVOKED.** The file is out of the repository, but the
published token keeps working until MyOperator revokes it. Blocked on their reply about whether old
and new tokens overlap. Inventory: `claude/S231_WABA_TOKEN_ROTATION_INVENTORY.md`.

🟠 **The staff advance policy document is wrong in BOTH stores** and the owner knows it is — rebuild
from the live code, never from either copy.

🟠 **F-368** — six stale `.env` copies and three stale code copies in live VPS folders.

**Standing holds, unchanged:** Apps Script work is PARKED until Phases 1 and 2 are done — **the ICICI
bank ingest is LIVE and load-bearing**, and **the callback tracker is not to be touched at all.**
NEFT: nothing is SENT without his word. The hub's shape is not reopened.

---
*START_HERE_SESSION_232 · generated at the S231 close, 08-Sep-2026. Next free: **D425 · F-369**.*
