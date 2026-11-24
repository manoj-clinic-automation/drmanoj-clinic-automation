# S942_SAARAS_V4 — the call transcriber moves to Sarvam Saaras v4

*The parent · S511 · 24-Nov-2026.* Sarvam's mail of 16-Oct-2026 ("Action needed: move fully to Saaras v4"): v3 is legacy; **one change — the model name**; same request, same price. The ONE place the estate sends speech to Sarvam is `call_transcription.py` (the at-hangup worker and the 03:00 timer each start it afresh; no service restart). The call hook never talks to Sarvam — no webhook change. Both of the script's doors (short calls: `speech_to_text.transcribe`; long calls: `speech_to_text_job`) accept `saaras:v4` with the same `mode` / `language_code` / codec (Sarvam's API reference, read 24-Nov).

| file | pin | what changes |
|---|---|---|
| wa/recordings-archive/call_transcription.py | ee8d3e41 → 6b72038d | `SARVAM_MODEL = "saaras:v4"` and the docstring's word. Nothing else. |

## Proof
- `walk_s942.py` (kit vs live bytes): **WALK 9/9** — exactly the two lines differ; both doors still send `model=SARVAM_MODEL`; mode/language/codec/threshold/chunk untouched; compiles. Control (nothing changed) red 5/9.
- `probe_s942.py` **on the box, before the file moves**: a 1.2-second made-up tone to the short door with `saaras:v4` + one batch job initiated (never started, nothing billed) using the live key — a 400 on the model/mode/codec stops the install with v3 intact.
- `rehearse_s942.sh` on a made-up root: dry · install · again · undo · forced red · probe red (nothing changed) · tampered kit · wrong live pin · lock held — **13/13**.

## Install (his one server line — combined with S943 below)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s942kit /tmp/s943kit && cp -rp /root/deploy/repo/deploy_kits/S942_SAARAS_V4 /tmp/s942kit && cp -rp /root/deploy/repo/deploy_kits/S943_SERVER_RECORD /tmp/s943kit && bash /tmp/s942kit/install_S942_SAARAS_V4.sh && bash /tmp/s943kit/install_S943_SERVER_RECORD.sh
```
Undo: `bash /tmp/s942kit/install_S942_SAARAS_V4.sh --undo` (v3 back for the next run).
