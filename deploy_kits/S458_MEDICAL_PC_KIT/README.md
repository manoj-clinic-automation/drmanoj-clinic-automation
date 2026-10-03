# S458_MEDICAL_PC_KIT — session 292, 03-Oct-2026

**The owner, 03-Oct:** *"do the housekeeping part for the medical PC first and then for the clinic PC tile."* His direction of 02-Oct: every PC's kit on the server, a tile on his portal, one click after a reinstall.

**What it is.** The Medical PC's setup kit for the *Clinic PCs* page: `setup_pc.py` (the installer), `README_REINSTALL_MEDICAL.txt`, and `payload/` — the tools **exactly as the working PC runs them**, read from the owner's PC's mirror of `D:\SendToClinic` (`D:\Downloads\margsync\medical_SendToClinic`; the hashes equal the PC's own heartbeat of 03-Oct 11:48 IST). Packed by `pack_medical_kit.py` into `deploy_kits/PC_KITS/medical/kit.zip` + `KIT_INFO.txt`; the button is S460's.

**The one rule: it only fills what is missing.** A file that is in `D:\SendToClinic` is never replaced. So: on the working PC it changes nothing (that is how it is rehearsed there); a tool the Sanjeevni side updates later (S454: `marg_txt.py`, `marg_watch.py`, `marg_push.py`) is never overwritten by this kit; and after a real reinstall the agent's own road — the clinic Drive's `ToMedical\_kit` — brings the current tools.

**None of the Sanjeevni side's files is edited, and nothing was placed on that PC.** The kit holds copies. Repack after a tool changes on that PC (the mirror must show it first):

```
python3 -B deploy_kits/S458_MEDICAL_PC_KIT/pack_medical_kit.py <the mirror folder> deploy_kits
```

**Not packed, on purpose:** `token.txt` (never); the August manual-send trio `GUARD_AND_SEND.bat` / `guard_and_send.py` / `marg_report.py` — retired, and **`marg_report.py` on that PC carries two real numbers with names in its worked examples** (F-704; the Sanjeevni side's file, told on the board); `AutoHotkey64.exe`.

**Proved offline:** `test_setup_medical.py <kit.zip>` — 21 checks: a fresh PC gets everything; a second run rewrites nothing; on a stand-in for the working PC the two newer tools are kept, the token, the captures and the heartbeat are untouched, a running agent is not started again; a tampered kit and a missing Python part stop before anything is touched.

**Owed:** the Windows-only steps (its real paths, the start of the agent) on a real Windows — a scratch-folder rehearsal by a signed job on the Reception PC at 08:30 on a clinic day; then, at a quiet hour and after S454 has landed, the button pressed once on the Medical PC itself, where it must report *0 placed*.
