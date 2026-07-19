# S149 GIT KIT — one unzip, one commit

## GitHub (3 steps, from your local repo root)

1. **Unzip this kit into the repo root.** It overwrites 4 files in `canonical-docs/` and adds 3 new
   ones (`KB_Register_v2_2_S149.md`, runbook v87, `START_HERE_SESSION_150.md`). Say yes to overwrite.

2. **Run the tidy** (dry-run first shows the 41 planned moves, changes nothing):
   ```
   powershell -ExecutionPolicy Bypass -File .\Repo_Trim_Phase2_S149.ps1
   powershell -ExecutionPolicy Bypass -File .\Repo_Trim_Phase2_S149.ps1 -Execute
   ```
   It archives 41 superseded docs (old Register/START_HERE/runbook versions + 35 historical `docs/`
   files) and deliberately leaves 12 clinic/reference docs in `docs/` for you to rule on later.

3. **Commit + push** (message is in `COMMIT_MESSAGE.txt`):
   ```
   git add -A
   git commit -F COMMIT_MESSAGE.txt
   git push
   ```
   (You can `git rm Repo_Trim_Phase2_S149.ps1 COMMIT_MESSAGE.txt READ_ME_FIRST.md` first if you
   don't want the kit's helper files in the repo — or leave them, harmless.)

## Project knowledge (drag-drop, same 7 files)

- **ADD:** `KB_Register_v2_2_S149.md` · `START_HERE_SESSION_150.md` · `HANDOFF_RUNBOOK_2026-07-19_Session149_v87.md`
- **REPLACE:** `CANONICAL_MANIFEST.md` · `Fault_Action_Register_v2_1.md` · `KB_History_Archive_v1_1_S148.md`
- **DELETE:** `KB_Register_v2_1_S148.md` · `START_HERE_SESSION_149.md` · `HANDOFF_RUNBOOK_2026-07-19_Session148_v86.md`

## Verify (md5 of the 7 canonical files in this kit)

| File | md5 |
|---|---|
| `CANONICAL_MANIFEST.md` | `13e48ca9a9e7cafa1dd64b81dd062c91` |
| `KB_Register_v2_2_S149.md` | `6870b51fefb45e7b924067e24968f1c5` |
| `KB_History_Archive_v1_1_S148.md` | `15196ec30d18af846f55fea12b1a6f39` |
| `Fault_Action_Register_v2_1.md` | `3bfeac72fe82c14aa2feb0d44a43ae2e` |
| `HANDOFF_RUNBOOK_…Session149_v87.md` | `d0e2e5b3e692db702337831f80080e8e` |
| `START_HERE_SESSION_150.md` | `c1dbbe7b06a3934b50d6dfccc6a77e7d` |
| `README_CANONICAL_SET.md` | `04dd5667ddfdfd159c83f7ee29cbff5f` |

**Housekeeping is CLOSED at S149.** Next session starts on real work only.
Next free: **D248 · F-46 · Session 150.**
