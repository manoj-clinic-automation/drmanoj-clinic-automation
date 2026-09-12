# S240 BUILD BRIEF — the one document to read before Session 241

*12-Sep-2026 IST · replaces reading the sixteen `S240_*` working papers.*

## THE HEADLINE

**The medical PC stopped being a link in the chain, and the salary sheets became signable.**

## 1 · D467 — THE ARCHITECTURE, IN ONE PICTURE

```
Marg (medical PC)  --export-->  marg_watch captures  --marg_push (HTTPS)-->  |
                                      |                                      |
                                      +--> Drive copy (leg 2) --------------> |  marg_take()
                                                                              |  ONE DOOR
manojz 10-min pull (leg 3) -------------------------------------------------> |  md5 de-dup
the owner's browser upload (leg 4, worst case) -----------------------------> |
                                                                              v
                                                              the VPS does ALL the processing
```

- **The medical PC only exports and pushes.** It computes nothing.
- **manojz leaves the data path** and stays for development and the publish.
- **The manual upload is not a special case** — it is the same door, so the fallback cannot rot.
- **`marg_take(bytes, name, source)`** is the only way an export enters the server. Same file by two legs
  = taken once (md5). Statuses: `TAKEN | ALREADY | REFUSED | BUSY`.
- The capture stamp survives the leg: the pusher renames to `MEDICAL__<stamp>__<slot>__<md5-8>.XLS`
  because the server's `STAMP_RE` is what dates an export.
- **Measured live:** 56 exports pushed automatically in the first eight minutes; **export → server = 5
  seconds**.

**What made it safe:** `MARG_SHADOW` proved the server could already compute the PC's answer — **same 374
· differ 0** — *before* anything was taken off the PC.

**Left to do:** power-on start (not logon) with a single-instance lock · the Drive leg's `FromMedical`
share · the "no export today" alarm · then retire manojz's data jobs.

## 2 · THE SALARY CHAIN — four kits, one file, in order

`salary_policy.py` **c7577174 → aabd90fb → d42842e4 → 21b9cd00 → 92aecbe3**

| kit | what it did |
|---|---|
| `S240_SALARY_NOTE` | footnote prints the live divisor (÷30.5, F-435); Amir's leave working removed (D474) |
| `S240_DARPAN_OWN_SHEET` | Darpan off Sheets 3 and 4 (D475) |
| `S240_DARPAN_SHEETS` | his SHEET 5 (owner, full advance story) + SALARY SLIP (his month, advance cut shown) — D476 |
| `S240_NET_ROUND10` | NET PAYABLE cut to the last ₹10, towards zero (D477) |

Each kit refuses unless the previous pin is live, proves itself by rendering August before and after on
the real data, and restores its backup on any failure. **August's money never changed** — only what is
printed, who is on which sheet, and the last digit of the net. **Reprint before locking.**

## 3 · AMIR'S DAY — drawn, not built

Seven screens · a 1 → 7 banner · an on-screen confirmation after each step · a bill list with a per-bill
drop-down of what to enter, enterable and skippable · a visible **DAY CLOSED** screen. Attendance is the
punch, with a recorded reception override as fallback — **and an override does not pay the day** (D473).
A deficient bill becomes a **claim**: Amir raises, Darpan chases in his PWA, the owner monitors (D471).
Waiting on his approval of the picture.

## 4 · THE FIVE RULES THIS SESSION PAID FOR

1. Prove a file complete by its own content, never by a vendor's footer (F-429).
2. `git check-ignore` every new kit file before naming a publish (F-432) — a blanket `*.json` kept a kit
   file out of the repository while `SUMS.md5` said it was there.
3. An explanation that merely fits the number is a hypothesis (F-434).
4. A number and the sentence that explains it are one deliverable (F-435).
5. A proof asserts exactly what the change claims — no more (F-438).

## 5 · HOW HE WANTS TO BE TALKED TO

He said it twice this session. **Draw the screens; do not describe them.** Do not ask for details he has
already given. Do not put technical choices to him. Keep chat short.

*S240_BUILD_BRIEF · project knowledge · `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S240\` · loose on
`F:\ClinicBackup\DrManojClinic_Automation\03_BUILD_BRIEFS\`.*
