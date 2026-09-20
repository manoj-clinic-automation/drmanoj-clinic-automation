# S347_SPINE_BACKUP — the pharmacy spine into the two nightly stores

*Session 276 (parent) · 20-Sep-2026 · kit S347 claimed on the System Board before this folder was named (F-515).*

## The one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S347_SPINE_BACKUP/install_S347_SPINE_BACKUP.sh
```

## Why

The pharmacy spine (`S331_SPINE`, live 20-Sep-2026 07:19 IST) lives under `/root/finance/spine/` and was in **no store**:
the 01:35 code bundle's `root/finance` entries are non-recursive by design, so a new sub-folder is invisible until
named, and the 01:50 encrypted state bundle names its sources outright. The Sanjeevni chat named both to the parent
at its S274 close. At the S276 open the bulk pin check confirmed it: all fifteen spine pins were **absent** from the
20-Sep bundle.

## What changes — two files, both run by cron only, no service restarted

| file | from | change |
|---|---|---|
| `/root/state_backup/code_bundle.py` | `598e55a4` (v1.6, S318) | v1.7: one NEW `SOURCES` entry — `root/finance/spine` · `*.py *.json *.txt` · **non-recursive**. Code, the two rule files the owner edits (`spine_rules.json`, `order_rules.json`), the state file and the nightly witness text. `readings/ orders/ expiry/` are data and stay out; `spine.db` is walled off by the existing `"*.db*"` hard exclude. |
| `/root/state_backup/clinic_state_backup.py` | `fba57985` (v3, S233) | v4: two rows — `SRC_FILES += /root/finance/spine/spine.db` (sqlite online-backup api, integrity-checked, FATAL 40 like every database here) · `SRC_DIRS += /root/finance/spine/readings` (append-only, one PHI-free `<md5>.json` per Marg export). |

**Why `readings/` and not the whole spine folder in the state backup:** the store walk takes every data file one level
down, and `orders/` and `expiry/` are nightly outputs a later kit may legitimately prune — a pruned file would read as a
*vanished source* (FATAL 41) and refuse the whole night's backup. Named narrowly, on purpose. The TO pins are read
back at install, never predicted (F-472).

## Proof

- `selftest_s347.py` — **49 checks** on copies of both live files against a fake root shaped like the box (spine
  folder, real sqlite `spine.db` plus a `.tmp` and a `.failed` beside it, `readings/`, `orders/`, `expiry/`).
  Four negative controls, each turning a green check red: the code-bundle entry removed (nothing carried); the entry
  made recursive (`readings/` would leak in); the two state-backup rows removed (nothing carried); a corrupt `spine.db`
  (the gather REFUSES with exit 40; with the fatal switch off it skips that one file and says INTEGRITY FAIL).
  A live file that already carries S347 is un-patched by reversing the exact replacements, so a re-run proves the same
  49 things instead of going red on "nothing to apply".
- Installer rehearsed whole on a fake root: install (49/49, both APPLIED, read-back ALREADY, both compile, the
  read-only proof lists exactly the spine's code/rule/text files and 0 data files) · re-run (ALREADY on both, 49/49 by
  reversal) · `--restore` (both files back byte-exact, `598e55a4` / `fba57985`) · a file without S318 refused before
  anything is touched · no spine on the box refused before anything is touched · a doubled anchor caught at the
  selftest gate with nothing changed. The [5/7] all-or-nothing branch (second file refuses → first put back) is shell
  the selftest gate makes unreachable in practice; it was read, not exercised.
- The installer's live proof is read-only: a `gather()` of the patched code bundle (no bundle written) and the state
  backup's own `preflight` (every source present, `spine.db` integrity, Drive reachable, **nothing shipped**).

## After the install

Tonight's 01:35 bundle carries `root/finance/spine/*.py|json|txt`; the 01:50 encrypted bundle carries `data/spine.db`
(+ its schema dump) and `data/readings/`. Read on the PC tomorrow:
`D:\Downloads\_kbtools\vps_code\code_nightly.tar.gz` → `root/finance/spine/`, and the pin check at the next open expects
the seven S331 pins, `order_rehearsal.py`, `order_rules.json`, `near_expiry.py` and `spine_rules.json` **present**.

## Not done here

`spine_compare_latest.txt` rides the code bundle (it is text); `orders/` and `expiry/` are in neither store by design —
both are rebuilt nightly from the spine.
