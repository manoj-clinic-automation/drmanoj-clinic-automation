# S388_ENABLE_USER_ACCOUNT — the staff account "user" starts the agent too (Sanjeevni, S281, 24-Sep-2026) · F-618

S387 was installed at the medical PC at 15:15:56 IST as **SET**, with its proof 8/8 on the machine. **SET has no administrator rights**, so it took the per-account branch: SET's own `MargAgent.cmd` is now the guarded starter, and the old one is kept as `.replaced_S387.bak`. The staff account **"user"**, where Shavez works, is not covered yet, and it cannot run the installer: Google Drive starts only from SET's `HKCU\...\Run` (CENSUS §5), so `F:\My Drive` does not exist in "user".

**This kit:** `ENABLE_AGENT_THIS_ACCOUNT.bat` is delivered by the Drive kit channel. It is one line in `_kit\KIT_MANIFEST.txt`, md5-gated; SET's running agent installs it into `D:\SendToClinic\`. Run once in "user", it:
1. proves the account can write in `D:\SendToClinic` (and stops, changing nothing, if it cannot);
2. copies `D:\SendToClinic\START_AGENT.cmd` (S387) into that account's own start-up folder, byte-checked;
3. starts the guard and prints its last lines. With SET's guard holding the lock, it reads *standing by*. When SET signs out it takes over within a minute.

`KIT_MANIFEST.txt` here is the whole manifest as placed in the Drive `_kit` folder: the previous content byte-for-byte, plus four lines.
