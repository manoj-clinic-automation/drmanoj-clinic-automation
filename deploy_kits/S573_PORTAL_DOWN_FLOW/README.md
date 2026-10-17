# S573_PORTAL_DOWN_FLOW — `clinic-doctor` (kit S573, session S319, 17-Oct-2026)

**Why.** On 16-Oct-2026 the portal was off from 18:52 to 19:18 IST. Hostinger shut the server down from its side ("hypervisor initiated
shutdown"), and it came back by itself. The owner's word, 17-Oct 15:32 IST: *"a flow of what all troubleshoot needs to be done in a simple
way, which I can also do on VPS without escalating it to you here. And when those fail, then only I should reach out to you."*

**What it is.** One word the owner types on the server: `clinic-doctor`. It checks:
1. the machine (disk, memory);
2. each web service of the portal: is it running, and does its port answer?
3. the web server, end to end, the way a phone reaches it (each address resolved to this machine).

It restarts **only** what is stopped or not answering, each at most once per run, and checks again. It ends with one verdict:
- **ALL GOOD**
- **FIXED** (it names what it restarted)
- **NOT FIXED — send a photo of this screen to Claude**

`clinic-doctor --check` looks and restarts nothing.

**Never:** it deletes nothing, edits no file, touches no database and changes no setting. A full disk (95 % or more) is reported and
nothing is restarted. Any reply from an app counts as alive; only no reply or a gateway error (502/503/504) counts as down.
Each run appends one line to `/root/deploy/clinic_doctor.log` (IST).

**Files placed (both new; nothing existing is edited):**
- `/root/deploy/clinic_doctor.py`
- `/usr/local/bin/clinic-doctor`

No service is restarted by the installer.

The rest of the flow lives off the server, so it works when the server is off:
- the outside watcher (Google Apps Script, a 5-minute check; its alert names the step);
- the one-page guide (a claude.ai artifact).

## Install (on the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s573kit && cp -rp /root/deploy/repo/deploy_kits/S573_PORTAL_DOWN_FLOW /tmp/s573kit && bash /tmp/s573kit/install_S573_PORTAL_DOWN_FLOW.sh
```
- `DRY=1` before `bash` runs every gate and the walk, and writes nothing.
- The installer takes the build lock and runs the walk on the server's own Python.
- It ends with one read-only `clinic-doctor --check`.
- Housekeeping: it removes old build scratch `/tmp/s554kit`, `/tmp/s554probe`, `/tmp/s562kit`, `/tmp/s562probe` and `/tmp/s564kit` if present.

## The walk (`walk_s573.py`, 22 checks)
The real script runs against a made-up server: a fake `systemctl` and a fake `curl` that read one state file and record every call.

| check | scenario |
|---|---|
| A | all good |
| B | a stopped service |
| C | a service running but hung |
| D | a hang a restart cannot cure |
| E | the web server stuck while the apps are fine |
| F | a full disk |
| G | `--check` restarts nothing |
| H | a 500 / 308 reply counts as alive |
| I | a missing unit is skipped, and a stopped database is started |
| J | a 502 counts as down |
| K | a second copy is refused |
| L | no secret-shaped word is printed |

Two broken versions of the script turn 8 and 5 checks red, so the walk can fail.

## Undo
```
rm -f /usr/local/bin/clinic-doctor /root/deploy/clinic_doctor.py
```
