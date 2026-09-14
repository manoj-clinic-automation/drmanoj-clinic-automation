# S257_LIVE_TOOLS — the manojz files as they actually are, captured at the S257 close

**A11.** These are the bytes **running on manojz**, staged back off the machine and hashed here —
not the copies this session built and hoped were installed. The two agree; both figures are in the
close report.

| file | destination on manojz | what it is |
|---|---|---|
| `rebuild_manifest.py` | `D:\Downloads\_kbtools\` | rebuilds/checks `ClaudeCowork\MANIFEST.md5` with no POSIX shell |
| `build_papers_index.py` | `D:\Downloads\_kbtools\` | builds the paper shelf; reads only |
| `REBUILD_MANIFEST.bat` | `D:\Downloads\_kbtools\` | **what the nightly task runs** |
| `CHECK_MANIFEST.bat` | `D:\Downloads\_kbtools\` | verify only; writes nothing to the tree |
| `INSTALL_KBTOOLS.bat` | `D:\Downloads\_kbtools\` | one run: python check → selftests → register the task → rebuild |
| `PAPERS.bat` | `D:\Downloads\_kbtools\` | rebuilds the shelf and opens it |

**Scheduled task:** `KB Manifest Rebuild`, **daily 03:10**, running as the owner's own login on
manojz. Registered by `INSTALL_KBTOOLS.bat` with `schtasks /create … /f`.

**Credentials needed: none.** These tools read and write only `D:\Downloads\ClaudeCowork\` and their
own folder, and reach no network and no other machine.

**Install order, if this ever has to be redone:** put all six files in `D:\Downloads\_kbtools\`, then
run `INSTALL_KBTOOLS.bat` once. It refuses to rebuild anything if the selftests do not all pass.
