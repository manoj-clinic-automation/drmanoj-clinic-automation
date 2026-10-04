# S478_MANOJZ_SETUP_PYTHON — session 294, 04-Oct-2026 (the parent) — installer S459.2

**What was wrong (found by reading, before any Windows run).** `setup_pc.py` of Dr Manoj's PC's kit (S459) asked `python -m pip freeze` by the bare name. The setup file the *Clinic PCs & phones* page hands out runs the installer under the kit's own Python (`pyportable\python.exe`), and Windows looks for a bare program name in the calling program's own folder **before** the PATH. So "python" was the kit's Python — which has no pip — and step 5 would have said *this PC has no Python on its PATH* on a PC that has one, and installed no package after a real reinstall. The offline walk could not see it: it stands in for `run()`.

**What changed.** One function, `system_python()`: the PATH is walked, this program's own folder left out, the Microsoft Store's stand-in (`…\WindowsApps\python.exe`) taken only when nothing else is there; step 5 asks pip through that full path. Nothing else in the installer moved. `VERSION` S459.1 → S459.2.

**Files here:** `setup_pc.py` (S459.2) · `test_setup_manojz.py` (35 checks: the 29 of S459, one that pip is never asked by the bare name, five on `system_python()`) · `pack_manojz_kit.py` (the version line) · `README_REINSTALL_MANOJZ.txt` and `pc_state_backup.py`, both unchanged copies of S459's (the test needs them beside the installer).

**Repacked:** `deploy_kits/PC_KITS/manojz/kit.zip` and `KIT_INFO.txt`:

```
python3 -B deploy_kits/S478_MANOJZ_SETUP_PYTHON/pack_manojz_kit.py deploy_kits 2026-10-04
```

The server hands out the new kit after its next `git pull` (any server line carries one). **No server file changes; nothing on any PC changes.** The Medical PC's kit (S458) never calls Python by name and is not touched.

**Proof on a real Windows:** kit S477's rehearsal (the last step of the 03:10 nightly on Dr Manoj's PC) runs this kit as the setup file runs it, into a scratch folder; its report is `D:\Downloads\_kbtools\PC_KITS_REHEARSAL_LATEST.txt`. Step 5 must read *all N already here*.

**Undo:** repack from `deploy_kits/S459_MANOJZ_PC_KIT/` (`python3 -B deploy_kits/S459_MANOJZ_PC_KIT/pack_manojz_kit.py deploy_kits 2026-10-03`), which gives the S459.1 kit byte for byte.
