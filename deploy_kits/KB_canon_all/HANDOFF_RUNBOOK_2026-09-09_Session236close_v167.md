# HANDOFF RUNBOOK — v167 — at the S236 close, 09-Sep-2026

**Supersedes v166 (S234 close).** No runbook was written at the S235 close.

## 1 · WHERE THINGS STAND

**Canon:** Archive **v1.83** · Register **v5.86** · Fault Register **v2.68** (F-0 … F-388) ·
**START_HERE_SESSION_237** · `CANONICAL_MANIFEST.md` · `MD5SUMS_ALL.txt`. Next free **D442 · F-389**.

**Live systems:** unchanged in behaviour. Nothing was installed on the VPS this session; **no live
pin moved**, so `live_pins_S234close.txt` still stands.

**In the repository, published, NOT installed:** `deploy_kits\S236_DISCOUNT\` — the owner's ruling
table (T1). 43 selftests, kit gate green, live-shape walk clean. Nothing reads its tables yet.

**Changed on the owner's machines:** four scheduled tasks on manojz now run hidden (F-388) ·
`D:\Downloads` organised, 218 items · three personal-app passwords reset and in Bitwarden.

**Changed on the VPS by the owner:** `drmanojagarwal.com` and `followup.dr-manoj.in` certificates
renewed and now valid to 08-Dec-2026 · three personal-app login passwords.

## 2 · WHAT TO START ON — see `START_HERE_SESSION_237` §3

**⭐ Marg changed the sale bill on the evening of 09-Sep — a much wider item-name field and three new
per-line columns (rate, discount, net).** Measure the new export before building anything on it.
F-385's cause is removed and F-380's urgency with it.

**Then the certificates.** F-387 is exposed *now*: `attendance.dr-manoj.in` is in no renewal list,
six of nine sites are missing from the renewal run, the ACME challenge 404 is unresolved, and nothing
watches an expiry date.

## 3 · THE TRAPS THIS SESSION EARNED

- **The device shell mounted nothing all session.** Stage → edit in the container → commit back →
  **verify by md5.** One overwrite reported success and kept the old bytes.
- **A silent SUCCESS is as dangerous as a silent failure** (F-383). Four systems in one day reported
  success while the world disagreed.
- **`Mv`, `Cp`, `Ls`, `Rm` are aliases in Windows PowerShell and outrank your function.**
- **A fixture cannot contain a defect the platform does not have** — PowerShell on Linux has no `mv`
  alias, and `[System.IO.Path]::GetFileName` does not split Windows paths there.
- **A kit whose payload is a `.json` needs its own `.gitignore` exception**, added when the kit is
  built and not when the publish refuses (F-300, third recurrence).
- **The manifest keeps TWO indexes of the same documents.** Both must name the same version (F-384).

## 4 · OWED AT THIS CLOSE

**Notion · SSD · KB extension · live pins · reduction tranche** — none done, the close ran late and
the owner ended it. All five are named in `START_HERE_SESSION_237` §4. **Canon itself is complete.**

---
*HANDOFF_RUNBOOK v167 · S236 close · 09-Sep-2026.*
