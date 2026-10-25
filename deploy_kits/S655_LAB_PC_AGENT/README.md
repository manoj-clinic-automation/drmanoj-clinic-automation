# S655_LAB_PC_AGENT — the NK Pathology lab PC's road to the server (D784)

*Session 351, the NK Pathology chat, 25-Oct-2026. Built in the chat on the 25-Oct bundle's bytes; walked on loopback (30 checks, the old reception door as the negative control goes RED); not yet installed anywhere.*

## What, in the owner's words
"Go ahead with the lab PC agent. Do not withdraw the extra drive shares. Set up the lab PC so that I can uninstall the Claude PC app from here and also remove my own login from Chrome. Plan a direct upload to the server from this PC also. This PC is switched off when the staff leaves and switched on in the morning around 8:30." (25-Oct-2026 21:39 IST)

## What it does
- **On the lab PC (LABPC):** `C:\ClinicLabAgent\lab_agent.py` runs at every logon (the S448 reception agent, derived by anchored edits — `build/make_lab_agent.py` — with the reception-only watches switched off by `config.json`). Every 5 minutes a heartbeat (counts and dates only) goes to the clinic Drive `FromLab\` and, signed, to the server. **The snapshot (job 8):** ~5 minutes after switch-on and every 3 hours while the PC is on, `E:\Labmate982\lab.mdb` and `Captdata.mdb` are copied, zipped (`labpc_YYYYMMDD_HHMM.zip`, ~12 MB) and posted to the server in signed 4 MB parts; the server joins them and keeps the file only when its SHA-256 equals what the PC signed. A dropped line keeps the zip on the PC and the next try (20 min later) sends only the parts the server lacks. Labmate is never opened or stopped; the staff's own `Backupdata.exe` zip is untouched. Jobs from the owner's PC reach it through the Drive door (`ToLab\jobs`) or the server relay, signed with the lab job key (`manojz/lab_sign.py`; secret `D:\Downloads\margsync\_config\lab_agent_key.txt`).
- **On the server:** `/root/finance/lab_door.py` (this project's file, derived from the parent's `reception_door.py` by `build/make_lab_door.py`): `/finance/api/lab/heartbeat`, `snap/status`, `snap/part`, `snap/finish`, `snap/list`, and the job relay `jobs/submit|next|ack|result|read`. Store `/root/labdata/incoming/` (mode 700, 30 days kept), keys `/root/labdata/lab_keys.txt` (the PC's public key) and `lab_job_keys.txt`, queue `/root/labdata/lab_jobs/`. **Two anchored edits to the parent's `finance_app.py`** (`server/make_S655_finance_app.py`): the lab doors in `PUBLIC_PATHS`; the guarded mount after the S449 block.

## Pins
| file | FROM | TO |
|---|---|---|
| `/root/finance/finance_app.py` (the parent's) | `f2e86ca7919abc9e660b1bd5e811eebf` (25-Oct bundle) | built from the live bytes at install; predicted `1dd66af3dee7f5724b360e8737c74f0a` |
| `/root/finance/lab_door.py` | — (new) | see `SUMS.md5` |
| `C:\ClinicLabAgent\lab_agent.py` | — (new) | see `SUMS.md5` |

## Install — three actions, in this order
1. **Lab PC** (Drive `H:\My Drive\Clinic Data Archive\ToLab\_kit\` holds the `labpc` folder): double-click `INSTALL_LAB_AGENT.bat`. It unpacks Python, places the agent, starts it, prints this PC's **PUBLIC KEY** and copies it to `Clinic Data Archive\FromLab\lab_public_key.txt`. Until step 3 the server answers its posts 503 NO_KEY — expected.
2. **Publish** from manojz (`PUBLISH_ALL.bat`).
3. **Server, one line** — the chat gives it with the key filled in: `cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S655_LAB_PC_AGENT/install_S655_LAB_PC_AGENT.sh <public key>`.
Then, when the lab PC's heartbeat on the server says "last accepted": `REMOVE_CLAUDE_APP.bat` on the lab PC (it refuses to run before that), and the owner signs Chrome out there (profile picture → Sign out).

## Undo
Server: `cp -p /root/finance/finance_app.py.bak_S655_f2e86ca7 /root/finance/finance_app.py && systemctl restart clinic-finance` (healthz 200). Lab PC: delete `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ClinicLabAgent.cmd`, end python from `C:\ClinicLabAgent`.

## Not in this kit (named, by the owner's word or by scope)
- The LAN shares `\\LABPC\C…G` stay (the owner: "do not withdraw").
- The health-page row (`lab_door.health_row`) is written but NOT wired — one line in `finance_app.py`'s health list, the parent's, later.
- `pc_kits.py`'s "Pathology lab PC" entry stays *planned* (its one-time-code enrolment is reception-shaped).
- The DTH laptop's Labmate: the same kit, a week after the lab PC runs clean.
- The day page that reads the snapshots (mdbtools on the server): the next kit.
