# S833_READER_TOLD — a stopped paper reader is told to him at once (F-1404); a summary is never moved at start (F-1194)

**Why.** F-1404 (S410): on 13-Nov the reader's key expired; the reader stopped itself and read nothing for ~21 hours, and nothing told
the owner; the card said "refused", not "expired". F-1194 (S409): at the scan app's start, `clinic_papers.heal_auto` runs before S754's
guard is installed at the foot of the app, so the start-up pass could move a dealer's summary between the clinic and pharmacy lanes.
Board `_numbers` v1485 → v1486 (kit S833; this project's own files). Built in the Scan App chat, session 461, 14-Nov-2026.

**What changes.**
- NEW `/root/assetapp/reader_watch.py`, every 5 minutes by cron (`# S833_READER_WATCH`, the venv python): reads the reader's own switch
  (`claude_reader.state`) and, once per stop, pushes **"Scan app · paper reader STOPPED"** with the reason in words (the key expired /
  refused — expired or revoked / the credit run out / no key) to his clinic app (the estate's Web Push road, `ring_common.push_user`),
  else the private ntfy topic; once more **"reading again"** when it is back. His own OFF tap is never announced. It writes only its own
  state file (`reader_watch_state.json`), never the database. Switches: the estate's `ALL_OFF`; the setting `reader_watch.on = off`;
  to whom: `reader_watch.to` (default `manoj`). The install sends one message to prove the road.
- `claude_reader.py`: a refused key is named — "the key has expired" when the answer says so, else "the key was refused (expired or
  revoked)" (three places: read, read_summary, S754's one call). His admin card shows the words.
- `clinic_papers.py`: `auto_home` never moves a dealer's summary (kind Summary / doc_kind summary) — the start-up pass included.
- Nothing on any staff screen.

**Files and pins (FROM → TO).** `claude_reader.py` `1c9e952e` → `a7df99bb` (4 counted replacements) · `clinic_papers.py` `89a3cd0a` →
`b8f551c4` (1) · NEW `reader_watch.py` `5ba95fce`. Read only, pinned: `asset_register.py 63eba920`, `procroom.py 38c5bbaa` (S831),
`sorting_desk.py baa7c6aa`, `asset_machine.py 7dbd5e0c`, `stationery.py cfb3d8b5`, `batteries.py bb082b4c`, `xray_costs.py 5823bae2`,
`claude_reread.py ed7023d2`.

**Kit.** `edits_s833.py` · `make_s833.py` · the three whole files · `walk_s833_app.py` (A0, R1–R2, W1–W4, C1–C2 on the REAL app; the
reader's call replaced, the watcher's message to a stub; `--expect-red` on the live files: every new check red, A0 and C2 green) ·
`install_s833.sh` · `rehearse_s833.sh` (R1–R7, a crontab file) · `PIN_*.txt` · `KIT_ID.txt` · `SUMS.md5`.

**Install (the owner, after publishing):** `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S833_READER_TOLD/install_s833.sh`

**UNDO:** `\cp -p /root/assetapp/claude_reader.py.bak_S833_1c9e952e /root/assetapp/claude_reader.py && \cp -p /root/assetapp/clinic_papers.py.bak_S833_89a3cd0a /root/assetapp/clinic_papers.py && mv /root/assetapp/reader_watch.py /root/assetapp/reader_watch.py.off && crontab -l | grep -v S833_READER_WATCH | crontab - && systemctl restart assetapp`
