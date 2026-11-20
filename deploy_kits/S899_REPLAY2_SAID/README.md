# S899_REPLAY2_SAID — Replay 2 says why the engine did not import, and runs again (the parent, S493, 20-Nov-2026)

S897's install seeded the box and ran Replay 2: **0 pass, 24 fail** — every run `KeyError: 'processor'`: the engine's import
raised under the venv and S492's harness swallowed the reason (F-1515). Nothing in S895 had imported the engine under the venv
(its runner starts it as a subprocess). This kit replaces one file, `/root/followup_tracker/replay2_s897.py` a6e66a47 → S897.2:
an import that fails is said (module and error); `--import-check` tries every engine module under the running python first.

Install (server, one line):
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s899kit && cp -rp /root/deploy/repo/deploy_kits/S899_REPLAY2_SAID /tmp/s899kit && bash /tmp/s899kit/install_S899_REPLAY2_SAID.sh
```
Undo: `bash /tmp/s899kit/install_S899_REPLAY2_SAID.sh --undo`. The runner stays OFF; nothing else touched.
