# S338_SPINE_HEALTH — the spine on the health page

**Project: Sanjeevni — Pharmacy & Marg · session S274 · 20-Sep-2026.** D567 **item 4**: *"The spine on the health page (`spine_read.py status`, one line); name `spine.db` + `readings/` to the parent for the nightly backup."*

## What changes

- **`/root/finance/spine/spine_build.py`** `f5907fd4` (S331) → `1378c87de2f8d4b3796cd92c7ca50d8d` — anchored edits, the rest byte-identical: after every build it writes **`spine_state.json`** beside the spine (atomically): `at`, `gate` ("14/14"), `passed`, `failed` (the blocking checks that did not hold), `status` (the one line `spine_read.Spine().status()` prints, or *GATE FAILED n/14 … the last good spine is still in place*), and **`last_success_iso`, which moves only when the gate passed**. A failing gate therefore lets the health leg go stale and red on its own — the page needs no code change to say the spine is unwell.
- **`/root/finance/freshness_legs.json`** — the parent's file, **a data edit, declared**: two legs appended, nothing else touched (`apply_legs_s338.py`, pinned to `0e56aa9e`, backup `.bak_S338_0e56aa9e`, idempotent):
  - **Marg spine gate (S331)** — `state_json` on `spine_state.json` field `last_success_iso`, window 26 h. The note carries the one line to read: `/root/wa/venv/bin/python3 -B /root/finance/spine/spine_read.py status`.
  - **Marg spine compare (S331)** — `file_mtime` on `spine_compare_latest.txt`, window 26 h (23:55 nightly).
- No service restart: the build (every 10 min 08–23) and the freshness collector are cron jobs. The installer runs one build now under the spine's own lock to write the first state file, then applies the legs, then proves the result with `freshness.py`'s own `load_legs()` (no bad declaration) and reads the state back (`passed True`).

## Why the page shows the leg and not the sentence

The health page (parent's `freshness.py`) prints a leg's static note, its age and its verdict; it shows `detail` only on NEVER/ERROR. Putting the live sentence on the page would mean changing the parent's renderer. So the **verdict** carries the health (green while the gate passes within 26 h, red when it does not), the **note** carries the command, and the sentence itself sits in `spine_state.json` for anything that reads it — the `--status` line, the next kit's card, the Book.

## Named to the parent (not done here)

- `code_bundle.py` (`/root/state_backup/`): carry `root/finance/spine` — `*.py`, `*.json` (incl. `spine_state.json`, `spine_rules.json`), `spine_compare_latest.txt` — in the nightly code bundle (01:35).
- The state backup: `spine.db` and `readings/` (PHI-free by construction; rebuildable from the Drive archive, but a copy costs nothing and the pin check needs it).
- Two root crontab lines `# S331_SPINE` (S272) and one `# S336_QUARANTINE` (this session) — already declared on the board.

## Proof

- `selftest_s338.py` 14/14 in the cloud on a fixture; on the PC / the box it also runs `freshness.py`'s loader over the edited legs file (17 checks): a passed gate writes the state; **a failed gate keeps `last_success_iso` and names the failed check**; the timestamp parses as `read_state_json` parses it; a wrong pin is refused; the right pin appends exactly two legs and changes no other leg or key; ALREADY on a second run; `load_legs` finds no bad leg; `read_state_json` reads the file the build wrote.
- Installer rehearsed on a fake root: install (one real `spine_build.py` run on the rehearsal readings), rerun ALREADY, wrong pin refused, forced red → `spine_build.py` restored byte-identically, state file removed, legs restored from the backup.

## The one line (the owner's)

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S338_SPINE_HEALTH/install_S338_SPINE_HEALTH.sh
```
