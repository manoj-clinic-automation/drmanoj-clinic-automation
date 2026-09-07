# START HERE — SESSION 230

Hi Claude. Continuing my clinic-automation project — **Session 230**.
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

---

## §0 · THE STANDING OWNER RULINGS — restated every session

1. **Publishing is HIS double-click.** Name one file, full path.
2. **Full paths ALWAYS — including URLs**, each in its own copy block. Never a bare `/finance/...`.
3. **ONE line per command.** Use `\cp` to bypass the alias.
4. **Token-lean working — never at the cost of verification.**
5. **Plain language. One step at a time. Full-file replacements. ALL-CAPS = urgent.**
6. **Mask patient numbers (last 4); never print secrets or tokens.** F-185: no number at all in the repo.
7. **Nothing live is rebuilt without his OK; the manual path stays as fallback.**
8. **Sub-agents read screens** — screenshots never enter the main conversation.
9. **Do not hand him diagnostics to run.** Ask for the one action nobody else can do, in one line.
10. **When a screen is wrong, read the screen's code FIRST.** The server is the last suspect.
11. **English to him, always.** Hindi is a staff-side requirement only.
12. **Do not put technical or architectural choices to him.** Make the call, state it in one line, proceed.
13. **Chat output SHORT.** Long write-ups belong in project documents.

**And one earned at S229, which outranks a script:** *when the owner tells you something about his
own shop, check it against the data before restating what a tool says.* He corrected the assistant
four times in one session and was right four times, every time from data already on his disk.

---

## PHASE 0 — CONNECTIONS, then verification, then work

**1 · CHECK THE CONNECTIONS AND PROMPT HIM. Before anything else.**

| needed | what breaks without it |
|---|---|
| **`D:\Downloads`** | no Marg archive, no `_config`, no ClaudeCowork — the KB extension |
| **`D:\dr-manoj-git`** | no repository, no kits, no publish |
| **`F:\ClinicBackup`** | the close cannot mirror or take a cold kit |
| **`H:\My Drive\FinanceDB_Backups`** | **new at S229** — the VPS's nightly `finance.db`, so nothing has to be copied by hand |

⚠ **`F:` and `H:` never mount in the device shell — that does NOT mean unreachable.** The
file-transfer tools read and write both perfectly. ⚠ **The assistant's browser is still in the F-242
login loop**; neither browser reached the portal at S228 or S229. The owner supplied the one live
page read himself, by saving the page and uploading it — that route works and is worth offering.

⚠ **`D:\Downloads` was NOT connected at the S229 open.** Check it by name; it can be requested.

**2 ·** Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin). The one live copy is
`deploy_kits/KB_canon_all/CANONICAL_MANIFEST.md`; the project-knowledge copy is a replica.

**3 · Verify every row by md5, from INSIDE `KB_canon_all`.** Halt on a hash mismatch only; a row
absent from one store is not a failed row.

**4 · Read only Tier 0:** manifest · this prompt · KB Register **v5.79** · Runbook **v161** ·
`OWNER_TODO_LIVE.md` · any open incident.

**5 ·** Open `D:\Downloads\ClaudeCowork\00_INDEX.md` and read **`S230_BUILD_BRIEF.md`** — one brief
instead of ten papers.

**6 ·** Confirm, then start.

---

## ⚠ THE FIRST ACT OF SESSION 230

**Read back the two DECLARED-PENDING spine pins from the box.** They are predictions from published
kit bytes, not passes:

```
md5sum /root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py
```

Expected `9a08b2c4c9adc2283fb371f350bbb043`. And the schema, expected `a39b2fccf7f2069390d5a8d97f2d9b29`.
**A pin not read from the box is not a pass** — S224 and S228 both carry rows that crossed a close
unverified.

**Also read back the spine's own first build**, which nobody has looked at:

```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S229_ITEM_SPINE/marg_spine.py --db /root/finance/finance.db --report
```

The figures on record were measured on the 06-Sep backup; the live build ran against a database that
also carries the 07-Sep April–June purchase push, so **the live numbers should be better** and have
never been seen.

---

## WHAT S229 LEFT — the state in six lines

- **The item spine is LIVE** on the VPS: seven new tables, populated, **and nothing reads them.** No
  screen changed. The undo is one line, recorded in the Register.
- **`marg_spine.py` in the repository is NEWER than what is installed** (`b5956f59…` vs
  `9a08b2c4…`) — the VINTAZ merge registration, unpublished. Publish carries it; until then they are
  different files and must not be confused.
- **manojz** runs 17 signatures and the F-351 fix, both hashed at the close.
- **The corrections worklist is with Amir** — 12 stock adjustments in two vouchers, 24 renames, 65
  salt names. 101 lines of typing, none of it the owner's, no export needed.
- **No stock data since 06-09 morning.** Every stock screen shows that day until the next export.
- **Twelve items are negative in Marg's own books** and clear by STOCK RECEIVE vouchers, not reports.

## NEXT FREE

**D413 · F-353 · Session 230.**

## THE BACKLOG POINTER

`HANDOFF_RUNBOOK_2026-09-07_Session229close_v161.md` **§2**, and `OWNER_TODO_LIVE.md` ⭐1.
**⭐1 is the derivation step — approved, needs no further word from him.**
