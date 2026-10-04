# S477_PC_KITS_REHEARSAL — session 294, 04-Oct-2026 (the parent) — Dr Manoj's PC only; no server file

**Why.** Two setup kits on *Clinic PCs & phones* had never run on a Windows: the Medical PC's (S458) and Dr Manoj's PC's (S459). Their buttons were held back until both were rehearsed in a scratch folder on a real Windows. The owner's standing rule: a step that is not his goes into the nightly.

**What it is.** `rehearse_pc_kits.py`, run by `NIGHTLY.bat` as its **last** step on Dr Manoj's PC. It does what `ClinicSetup_<PC>.cmd` does after its download, with the same Windows tools — `certutil` for the md5, `tar.exe` to unpack, the kit's own Python 3.11.9 to run `setup_pc.py` — from the repository's `deploy_kits/PC_KITS/` copies (the bytes the server hands out), with every place the installers write pointed at a scratch folder through the knobs the installers already have:

- **the Medical kit:** `CLINIC_SETUP_TARGET / _ALLUSERS / _MINE` → scratch; `--no-start` (no agent is started). Checked: every tool placed and read back, the unpacked Python runs and every Python tool compiles under it, the start-up entry lands in the *scratch* start-up folder, this PC's real start-up folders are untouched, a second run places nothing.
- **Dr Manoj's kit:** `CLINIC_SETUP_C / CLINIC_SETUP_D` → scratch; the state zip and the knowledge-base mirror are **read** from the SSD. The installer's `run()` is wrapped: a `pip install` or a `schtasks /Create` is **not run** and is written down (none is expected on this PC). Checked: every file of the ten folders back byte for byte against the zip's own CRC, the knowledge base restored, packages *all already here*, tasks *0 made again*, a second run restores nothing.

**What it changes on this PC:** nothing outside `D:\Downloads\_r477`, which it removes at the end (and first thing on any later night, if a cut run left it), and its report `D:\Downloads\_kbtools\PC_KITS_REHEARSAL_LATEST.txt` — counts and names of tools, folders and steps only. The restored copy of this PC's state (patient data, keys) exists only inside that scratch folder, on the same disk, for the minutes the run takes. A run that overruns 70 minutes is stopped with its whole process tree. It never changes the nightly's exit code.

**It runs once:** while the report is not there. To run it again (after a kit changes), move the report aside:

```
D:\Downloads\_kbtools\PC_KITS_REHEARSAL_LATEST.txt
```

**Placed on Dr Manoj's PC by the assistant (the nightly is the assistant's own):** `D:\Downloads\_kbtools\rehearse_pc_kits.py`, `NIGHTLY.bat` (the old one kept as `NIGHTLY.bat.bak_S477_ac5c2b7c`), `S477_SUMS.md5`, `S477_README.md`, `S477_KIT_ID.txt`.

**Proved offline** (not Windows — `tar.exe`, `certutil` and the kit's `python.exe` are not exercised there; Python stands in): 40 checks green on stand-in zips; a package the PC lacks is blocked and reported red, nothing installed; no SSD is red; a scratch name that is not its own is refused and nothing is deleted; a left-over scratch folder is swept on the next call. Read by an independent agent before placing: a timeout now stops the whole process tree, and a failed clean-up is retried on every later night.

**Undo:** put `NIGHTLY.bat.bak_S477_ac5c2b7c` back as `NIGHTLY.bat` (or simply move `rehearse_pc_kits.py` away — the nightly's line runs only while that file is there).
