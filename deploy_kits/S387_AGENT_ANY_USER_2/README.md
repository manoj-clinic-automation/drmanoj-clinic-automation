# S387_AGENT_ANY_USER_2 — the Marg agent runs whichever Windows account is signed in (Sanjeevni, S281, 24-Sep-2026) · F-618

Supersedes **S386** (frozen, never installed). The owner ran S386 at the medical PC as SET at about 15:0x IST, 24-Sep. **Its own on-machine proof refused it, 7/8.** The check *"an agent from the old launcher appears → the guarded one steps back"* failed. The installer took its files back out and touched no start-up folder, so nothing changed.

**The defect it found (real, not a slow PC).** After stepping back for an agent started by the old launcher, the guard read its own stopped agent as "gone" and started it again at once, so the two kept restarting in turn. Windows reports a stopped process as ended immediately. The build box (Linux) keeps an unreaped child visible, which hid the fault. Reproduced here once the guard reaps its children the way Windows behaves: the same single check failed, 10–12 agents in 4 seconds. **Fix:** a guard that steps back forgets its own agent (`_agent_guard.child` → 0) and stands aside for as long as the other agent's heartbeat is fresh. **Test sharpened:** it waits for the guard's own "stepped back" line, then samples for four seconds that exactly one agent beats. The old logic under the final test: RED (10 agents). The new logic: GREEN, 5 runs of 5.

Everything else is as in S386; see `deploy_kits/S386_AGENT_ANY_USER/README.md` for the cause (the only launcher was in SET's own start-up folder) and the design.

**Install:** double-click at the medical PC, from the SET account:
`F:\My Drive\Clinic Data Archive\ToMedical\_kit\S387_AGENT_ANY_USER_2\INSTALL_S387.bat`
It checks the files (md5), places them, proves the guard on that machine (8 checks), and refuses and restores if anything is red. It then installs the all-users start-up entry, retires every account's old `MargAgent.cmd`, opens `D:\SendToClinic` to every account, and starts the guard. **Restart the medical PC once afterwards**, so that every account signs in through the new starter; an account already signed in when the install ran has not started it.

**Undo:** delete `C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp\MargAgent.cmd` and rename `C:\Users\SET\...\Startup\MargAgent.cmd.replaced_S387.bak` back to `MargAgent.cmd`.
