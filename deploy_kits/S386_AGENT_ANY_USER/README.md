# S386_AGENT_ANY_USER — the Marg agent runs whichever Windows account is signed in (Sanjeevni, S281, 24-Sep-2026) · F-618

**What went wrong (24-Sep).** The medical PC's agent does the capture, the sending and the offsite backup. It was started by one file only: `C:\Users\SET\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\MargAgent.cmd`, the start-up folder of the Windows account **SET** (CENSUS of 26-Aug, section 17). The PC restarted into SET at 07:31. SET was signed out about 08:14, and the staff account **"user"** (where Shavez works and exports from Marg) has no start-up entry. Heartbeat frozen at 08:13:56, last send 08:17:58, nothing captured after. The 23-Sep bill-wise sale was still missing at 14:50 IST.

**What this does.**
- `D:\SendToClinic\agent_guard.py` (NEW) is started at every sign-in, in every account. Only one guard can hold a lock on `D:\SendToClinic\_agent_guard.lock`, so only **one agent** runs however many accounts are signed in. The others **stand by** and take over within a minute when the running account signs out.
- It **stands aside for the old launcher**. A fresh heartbeat (< 7 min) not explained by its own stopped agent means an old unguarded agent is running. The guard waits for it to stop, and steps back if one starts later. Two agents never fight.
- It restarts the agent if it stops (growing pause, max 5 min). `D:\SendToClinic\_off\AGENT_OFF.txt` stops it; deleting the file brings it back. It writes to `D:\SendToClinic\agent_guard.log`.
- `START_AGENT.cmd` (NEW) runs the guard with the same python the old launcher used.
- **medical_agent.py and marg_watch.py are not changed.**

**Install — one double-click at the medical PC, best from the SET account:**
`F:\My Drive\Clinic Data Archive\ToMedical\_kit\S386_AGENT_ANY_USER\INSTALL_S386.bat`
It checks the files (md5), places the two files, and **proves the guard on that machine** (8 checks with a stand-in agent). If the proof is red it takes the files back out and touches nothing else. With administrator rights it writes `MargAgent.cmd` into the all-users start-up folder (`C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp`), renames every account's old `MargAgent.cmd` to `.replaced_S386.bak`, and opens `D:\SendToClinic` to every account (Users: modify). Without administrator rights it installs for that account only and says to run it once in the other account. It then starts the guard and prints what the guard says.

The Drive kit folder's own `_kit` channel never reads this subfolder; it is only a way to put the installer in front of the medical PC.

**Proof at build time (Linux stand-in):** the guard's selftest ran 8/8 four times. The installer ran against a stand-in `D:\SendToClinic` in both branches (all-users and per-account), placing the files, backing up and replacing an old per-account launcher, and running the proof.

**Known limit:** under "user", Google Drive may not be signed in. If so, the agent's offsite backup and the Drive kit channel wait for SET, while capture and sending (direct to the server) work in either account.

**Undo:** delete `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\MargAgent.cmd` and rename `C:\Users\SET\...\Startup\MargAgent.cmd.replaced_S386.bak` back to `MargAgent.cmd`.
