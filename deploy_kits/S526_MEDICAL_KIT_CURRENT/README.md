# S526_MEDICAL_KIT_CURRENT — the Medical PC's setup kit brought to what that PC runs today

Kit of session 305 (the parent), 11-Oct-2026. Number claimed on the System Board (`_numbers` v353).

The setup kit the *Clinic PCs & phones* page serves for rebuilding the Medical PC (`deploy_kits/PC_KITS/medical/kit.zip`,
packed 03-Oct) carried three tools that have since been replaced on that PC. Repacked with the bytes the PC runs:

| member | was | now (the live pin) |
|---|---|---|
| `payload/medical_agent.py` | `70d5c4e3` S205.1 | `d91fa79a` S499.1 (08-Oct) |
| `payload/marg_watch.py` | `81145aa7` | `0a78ae15` (S491) |
| `payload/marg_txt.py` | `70f920c4` | `7fa5136d` (S490) |

Each new file is the byte copy in Drive `ToMedical\_kit\` and the live pin; `repack_s526.py` refuses unless the old zip
and every new file are exactly their pins. Every other member is copied byte for byte, in the same order with the same
dates; `MD5SUMS.txt` inside changes in those three rows only; the zip is read back member by member against it.
`kit.zip` `83922881` -> `54e76aa411fd5763b4920a7d41513c20`; `KIT_INFO.txt` says so (the page checks it before serving).

**Nothing changes on the Medical PC** — the kit is used only to rebuild that PC. Nothing to install on the server: the page
serves the repository copy after the next `git pull`. Proven: the zip tested whole, the three files compile; the nightly
on manojz rehearses the kit on real Windows again (its rehearsal report was set aside so it runs tonight).

`verify_medical.py` (S207) was read against today's S499.1 heartbeat: every field parsed — no change needed now. Its one
overstated sentence (*"exists in one place"*, F-808) goes with the next agent re-issue.

Undo: the two files from the previous commit (`git checkout HEAD~1 -- deploy_kits/PC_KITS/medical/`).
