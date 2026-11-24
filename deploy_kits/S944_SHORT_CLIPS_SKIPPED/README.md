# S944_SHORT_CLIPS_SKIPPED — the leftover loop stopped (roadmap S510 phase 0, A2 · F-1633)

*The parent · S511 · 24-Nov-2026.* Builds on S942 (FROM = S942's TO 6b72038d). Fourteen clips ≤ 30 s fail at Sarvam every night and were re-tried every night (1,530 failed rows in Call_Transcripts; 14 API calls a night for nothing).

| file | pin | what changes |
|---|---|---|
| wa/recordings-archive/call_transcription.py | 6b72038d → a9466c22 | Two rules before the download: a clip of **10 s or under is never sent** (one `skipped` row, "too short (10 s or under): not sent"); a clip of **30 s or under that Sarvam itself refused on three different days** (`transcribe:` failures; a Drive failure or one bad hour never counts) gets one `skipped` row ("too short: Sarvam refused it on N days, not re-tried") and is never re-tried. A `skipped` row settles the call like `done`. The summary line counts them. The verdict stage reads only `done` rows — a skipped call is never judged (no change there). The 14 settle themselves on the first run (one row each) — no one-off. |

Not in this kit (A2's remaining parts, next session): the 48 July calls marked "not judgeable — before the stage"; the 1,374 August FAILED verdict rows removed after an owner-only CSV backup; the "AI judged within 15 min" freshness leg; `callhook_watchdog.py` (its access-log glob `/home/*/logs/*access*` looks like another host's — scheduling vs retiring is decided after a `--json` read on the box).

## Proof
- `walk_s944.py` (made-up rows): **WALK 17/17** — the two rules on nine durations/refusal counts, the settled/refused-days reading on a stub tab (Drive failures and same-day repeats never count), the block before the download, the summary, the model still v4, the diff confined to the five anchors, compiles. Control (the FROM) red 2/17.
- `rehearse_s944.sh` on a made-up root: dry · install (a stub `--dry-run` must print its counts line) · again · undo · forced red · dry-run red after placing → restored · tampered kit · wrong live pin · lock held — **13/13**.
- On the box the installer runs the placed script's `--dry-run` (reads the tabs only) and restores the file if it does not answer.

## Install (his one server line, after S942 is live)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s944kit && cp -rp /root/deploy/repo/deploy_kits/S944_SHORT_CLIPS_SKIPPED /tmp/s944kit && bash /tmp/s944kit/install_S944_SHORT_CLIPS_SKIPPED.sh
```
Undo: `bash /tmp/s944kit/install_S944_SHORT_CLIPS_SKIPPED.sh --undo`.

Fallback if a clip reported ≤ 10 s was in truth longer (implausible — MyOperator's duration is the call's own): delete that call's `skipped` row in Call_Transcripts and the next run sends it.
