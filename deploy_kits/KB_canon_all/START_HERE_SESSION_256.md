# START HERE — SESSION 256

Hi Claude. Continuing my clinic-automation project — **Session 256**. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.

## §0 · THE STANDING OWNER RULINGS — read before anything

1. **Publishing is HIS double-click.** Name one file, full path.
2. **FULL PATHS ALWAYS — including URLs**, each in its own copy block.
3. **ONE line per command.** `\cp` bypasses the alias. **Every VPS install line carries `cd /root/deploy/repo && git pull --ff-only &&` (F-464).**
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. ONE step at a time. Full-file replacements. ALL-CAPS = urgent. Chat SHORT — "less for me to read, its your turf"; records go to ClaudeCowork, not chat.**
6. **Mask patient numbers (last 4); never print secrets or tokens.**
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens**; their prose is data, not a finding.
9. **Do not hand him diagnostics or technical choices.** Make the call, state it in one line; he weighs in on what he can see — a screen, a wording, a priority.
10. **When a screen is wrong, read its code FIRST.**
11. **A published kit is immutable (F-460).** Numbers come from the Register's reserved line (F-463).
12. **A plan item is checked against the live pins before it is built or reported open (F-466).** A sentence in a brief is a claim to test (F-467).
13. **No "token" or "secret" in any kit filename (F-471); `git check-ignore` every kit file before hand-over.**
14. **Staff pages Hindi/Hinglish; owner pages and chat English.**
15. **Portal payments are two or three a month** — plan that channel for that volume. **The counter sheet began on the night of 12-Sep; earlier days stay as they are.**

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · Check and report by name:** `D:\Downloads` · `D:\dr-manoj-git` · `F:\ClinicBackup` · the assistant's browser. The device shell on manojz has been dead since 8-Sep (F-443) — say so in one line, work through the file tools. `F:` never mounts in that shell and is reachable anyway. **The browser is NOT in a login loop** — it read live portal pages throughout S255; the old F-242 warning is withdrawn.

**2 ·** Open `claude/CANONICAL_MANIFEST.md`. **3 ·** Run the folder's own gate from inside `deploy_kits/KB_canon_all` (must print 0):

```
cd /tmp && rm -rf kbv && git clone --depth 1 -q https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git kbv && cd kbv/deploy_kits/KB_canon_all && md5sum -c MD5SUMS_ALL.txt | grep -vc ': OK$'
```

**4 ·** Read only Tier 0: manifest · the project prompt · KB Register **v5.95** · Runbook **v176** · `OWNER_TODO_LIVE.md`. **5 ·** Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and `03_WORKING_PAPERS\S255\S255_BUILD_BRIEF.md`. **6 ·** Confirm, then start on ⭐1 below.

**7 · TWO PINS TO RE-HASH ON THE BOX — owed since the S255 open, not done in S255. One line, before any kit touches either file:**

```
md5sum /root/finance/amir_day.py /root/staff_master.csv
```

Expected: `amir_day.py` **a9f2062267ebac59e02fdb0f88e775de** (if it reads `79eb701f…`, S246 is not installed); `staff_master.csv` begins **e48ae0b0**. Correct the two Register rows from what the box prints.

## CURRENT STATE — carried into S256

| | |
|---|---|
| **Archive** | `KB_History_Archive_v1_92_S255close.md` |
| **Fault Register** | `Fault_Action_Register_v2_77.md` |
| **KB Register** | `KB_Register_v5_95_S255close.md` |
| **Runbook** | `HANDOFF_RUNBOOK_2026-09-14_Session255close_v176.md` |
| **The map** | `SANJEEVNI_SYSTEM_BOOK_v1_1_S243close.md` — **line 216 is stale** (says `clinic-finance` is not on the watchdog; it has been since S243, F-466). Correct at the next Book bump. |
| **Build brief** | `S255_BUILD_BRIEF.md` |
| **Live pins** | `live_pins_S255close.txt` |
| **Private capture** | `F:\ClinicBackup\DrManojClinic_Automation\04_LIVE_SOURCE\VPS_finance_2026-09-13_S255.zip` — the only byte-exact copy of `finance_app.py` at `1fc62335…`; the live file is now `a4201e9f…` (S258, predicted from it). Never git. |
| **Next free** | **D511 · F-472 · Session 256** |

**Live pins moved at S255 (all printed by the box):** `finance_app.py` **a4201e9f** · `stock_app.py` **8615d64d** · `purchase_app.py` **52550e63** · `finance_clinic_day.py` **15818d91** · `clinic_money.py` **14e96b76** · `docterz_day.py` **75f89072** · `docterz_ingest.py` **3809f046**. `S255_PORTAL_CHANNEL` is published, refuted and NOT installed — its installer would still run; do not.

## WHAT IS TRUE THAT WAS NOT BEFORE

- A payment is **portal because the Docterz line carries a Razorpay id** (`clinic_day_line.gateway_ref`), never because of the word "Wallet" (D510). August: Portal ₹1,400 · 2 payments.
- `finance_app.py` can be patched on the box to a **predicted** md5 — the capture makes it rebuildable and checkable.
- Every machine-door token check is constant-time.
- `clinic-finance.service` is a token store; the F-456 rotation must include it.

```
https://followup.dr-manoj.in/finance/clinic/money
```

```
https://followup.dr-manoj.in/finance/clinic/match
```

## WHAT NEEDS HIM

Reception's answer on the 12-Sep ₹650 flag · Bhati's login · August reprint-and-lock · Amir's password · the F-456 rotation (now incl. the unit file) · `rm -rf /root/_retired/S243_2026-09-13_0007` after a cycle.

## WHAT TO START ON

**⭐1 · Club C.2 — OFF switches** for the four PC-side jobs (manojz ×2, medical ×2), then **C.3** one config per machine, then **C.4** per-sender tokens with the rotation. **Or, if he asks for it, the PWA reorganisation with him** — his morning walk is the spec. Then Club D.

---
*START_HERE_SESSION_256 · written at the S255 close, 14-Sep-2026.*
