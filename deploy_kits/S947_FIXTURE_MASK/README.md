# S947_FIXTURE_MASK — F-1639 + F-1648 (the parent · S513 · 24-Nov-2026)

The ten-digit phone-shaped fixtures in four live call-audit scripts become made-up numbers. Selftest data and docstrings only — no behaviour moves, nothing restarted.

| file | from → to | runs masked (unique) |
|---|---|---|
| `/root/wa/recordings-archive/call_verdict.py` | 539ea68f → 0e4a7ab1 | 21 (2) |
| `/root/wa/recordings-archive/daily_digest.py` | 8140f543 → 8dc2d87b | 25 (6) — one was a **real patient number** (F-1648) |
| `/root/wa/recordings-archive/flag_investigator.py` | a9baa6ca → 8a744e8e | 10 (4) |
| `/root/wa/recordings-archive/verdict_review.py` | 280eb2ce → 1f644121 | 12 (3) |

**The rule (`make_s947.py`).** Every run of ten digits starting 6–9 (the shape `NO_PHONE_NUMBERS.py` refuses), with or without a `+91`/`91` in front (the prefix stays), becomes `500000` + its own last four; two different runs with the same last four become `500001…`. One mapping across the four files. Every `mask()` expectation (`******1234`) stays true untouched, the files keep their length, only digits inside those runs change. Epoch seconds and short ids are not touched.

**The kit carries NO FROM bytes** (they hold the numbers). `FROM_PINS.md5` names them; on the box the walk's FROM is the live files themselves, md5-checked first.

**How F-1648 was found (counts only, nothing printed).** The two real-looking numbers named in START_HERE_SESSION_513 were counted in the device VM against the Docterz exports (`D:\Downloads\DocterzArchive\`, 431 files) and the nightly database copy: …6698 — 0 anywhere (a fixture); …8409 — 13 rows in the exports' `Mobile` / `Mobile No` columns (a patient). Every other run in the four files: 0 in the exports. In the published repository tree only `recordings-archive/daily_digest.py` carries …8409 (code folders, `canonical-docs/`, `project_kb/`, `deploy_kits/` searched; `_scratch/`, `_to_delete_S*/` are git-ignored). This kit's publish also replaces the repository's four copies with the TO bytes.

**`make_force_keys.py` (retired, S510) is NOT in this kit.** Its `TRIPLES` list is real call data (10 of its 37 numbers are in the Docterz exports) with each call's date and time; masked, it would still put date + time + last four of real calls into this public repository. It stays on the box only — retired, never run, not in the nightly bundle (`_retired/` is not bundled).

**Proof.** `walk_s947.py` 27/27 (per file: same length · every changed character an ASCII digit inside a run · last four kept · no 6–9 run left · compiles · its selftest — call_verdict 42/42, daily_digest 81/81, flag_investigator 51/51, verdict_review 144/0 — then `NO_PHONE_NUMBERS --files-from` over the four: exit 0, 0 lines · the four judged · one mapping, no two originals folded); CONTROL — the FROM files judged — red. `rehearse_s947.sh` 17/17 on a made-up root (live files 0755): DRY · install (modes kept, nothing left behind) · ALREADY · undo · undo twice · re-install after undo · an emptied or missing backup refuses undo · a drifted live file stops · forced red at [4/5] and [5/5] restore with modes kept · killed mid-[4/5] puts back · the build lock held stops · undo refuses a later kit's file · a corrupt kit stops · no gate on the box stops. Cold review by a sub-agent that had not seen the build: no MUST; 3 SHOULD (restore atomic with the mode kept; undo checks its backup and reads back; a killed run puts back) all built in; second look after: 2 SHOULD (a second signal during the put-back; a missing backup on undo) built in.

**On the box.** One line:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s947kit && cp -rp /root/deploy/repo/deploy_kits/S947_FIXTURE_MASK /tmp/s947kit && bash /tmp/s947kit/install_S947_FIXTURE_MASK.sh
```
Undo: `bash /tmp/s947kit/install_S947_FIXTURE_MASK.sh --undo` (backups `.bak_S947_<from8>`, 0600, beside each file; the nightly bundle takes no `.bak`).

**For Fable's look at the next gate:** the repository's git HISTORY still carries …8409 (public repo); a history rewrite (force-push) would break the box's `git pull --ff-only` and every clone, so it is not done. Old code bundles on Drive carry it too (owner-only).
