# S649_READER_PHOTO_SIZE — a large phone photo is shrunk for the reader (F-1003)

**Why.** F-1003 (found S341, 22-Oct-2026): phone photos of about 4.5 MB and more came back *"read failed"* on the desk, and
*Re-read* failed the same way; since S635 the month end's photos meet it too. START_HERE_SESSION_352 B2. Board `_numbers` v685 → v686
(kit S649). Built in the Scan App chat, session 352.

**The cause (read in the code).** `claude_reader._block()` sends a photo over `IMAGE_MAX` (3.7 MB) through `_smaller()`, which
imports Pillow **in the service's own python** — the system `python3`, which has no Pillow (the file's own note at `TURN_PY`: *"the
service python has neither"*; F-53). On the ImportError `_smaller()` returned the photo whole, `_block()` answered *"photo too large
to send"*, and the paper's reading was marked failed. `turn_file()` in the same file already solves this for turning a scan: it uses
the venv python (`/root/wa/venv/bin/python3`, which has Pillow) when this one cannot.

**What changes.** `_smaller()` does the same: Pillow in this process when it imports, else the venv python's (`TURN_PY`, run with
`-I`, the photo on its standard input, a JPEG of at most `IMAGE_MAX` back — longest side 2400 px, quality 85 → 70 → 55, exactly the
in-process steps). **The stored scan is never changed**; only the copy sent to the reader is smaller. A photo under the limit and
every PDF go as before, byte for byte. When neither python can do it, the old answer stands (*"photo too large to send"*). A paper
that says *read failed* can be read again with its **Re-read** button.

Also, by K1: such a photo now reaches the reader's *how does each page lie* check (S618) too; a sideways one in the pharmacy lane is
then turned upright as a **new** stored file, the old one kept — as smaller photos already are. **Still not read:** a HEIC photo (the
reader takes JPG, PNG, WEBP and PDF) — a known gap, unchanged. The installer prints, read only, how many papers Claude could not read
so far and why (the evidence for the cause on the live data); the walks run in the python the running service uses.

**Files and pins (FROM → TO).** `/root/assetapp/claude_reader.py` `10118909` → `1277e80d`, the kit's whole file (3 counted edits,
`build_s649.py` in the session's working papers; VERSION S550.2 → S550.3). No other file; no data step. Its callers are not
changed: `asset_register.py` (the desk's reading, check_scan / lie_pass), `procroom.py` (the month end's photos), `claude_reread.py`.
Read only, pinned: `procroom.py f6578535` (S648), `sorting_desk.py ca9fda74`, `asset_register.py 068440f7`, `clinic_papers.py
89a3cd0a`, `claude_reread.py ed7023d2`, `asset_machine.py 7dbd5e0c`, `stationery.py b6ce217a`, `batteries.py bb082b4c`,
`xray_costs.py 5823bae2`.

**Kit.** `make_s649.py` · `claude_reader.py` · `walk_s649_reader.py` (A0, C1–C9: made-up photos of 8.6, 8.1 and 4.8 MB (MID.JPG), a small one, a
PDF, a broken file; run in the service python, the venv python as TURN_PY; no key, nothing sent; `--expect-red` on the live reader:
only A0, C1, C7, C8, C9 red — this is also the box's own proof of the cause) · `walk_s648_app.py` (S648's walk of the whole app, run with
the new reader in it) · `install_s649.sh` (gates: the venv python has Pillow; both walks and the control before anything is placed;
after the restart the reader's walk again on the placed file) · `rehearse_s649.sh` (R1–R8) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S649_READER_PHOTO_SIZE/install_s649.sh`

**UNDO (one line):** `\cp -p /root/assetapp/claude_reader.py.bak_S649_10118909 /root/assetapp/claude_reader.py && systemctl restart assetapp`
