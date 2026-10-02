# S453_RECEPTION_SERVER_DOOR — session 290, 02-Oct-2026 — D661

**Why.** The reception agent ran jobs that reached it by one road only: Google Drive for desktop on that PC. That is
the thing that failed there on 01-Oct. With the Claude app gone from that PC and Drive down, the heartbeat would still
arrive (the direct road, S449) and nothing could be done about it (F-689). This kit is the second road.

**The rule it is built on: the server relays, the PC decides.**

| who | holds | can do |
|---|---|---|
| the owner's PC (manojz) | the SECRET job key (`D:\Downloads\margsync\_config\reception_agent_key.txt`) | sign a job, sign a read |
| this server | that key's PUBLIC half (`reception_job_keys.txt`) and the PC's PUBLIC upload key | queue a correctly signed job, hand it to the PC, keep its output |
| the reception PC | the PUBLIC job key in its own `authorized_keys.txt`; its own upload secret | fetch, **verify again**, run, answer |

So a clinic login, this server, or anyone who took this server over cannot make that PC run a job; the walk proves
it with a key the server's list knows and the PC's does not, and with a job altered on the server's own disk.

## The five doors (all under `/finance/api/reception/jobs/`, all `POST`, none needs a login, each proves itself)

| path | who calls | proof | answer |
|---|---|---|---|
| `submit` | the sender | JSON `{name, job (base64), sig}` — the job key's signature over the name and the bytes | `QUEUED` / `ALREADY` / refused |
| `next` | the PC, once a minute | signed with the PC's upload key (kind `jobs-next`) | `JOB` with name, bytes, signature — or `NONE` |
| `ack` | the PC | kind `jobs-ack`, the job's name; body `taken` or the reason it refused | `NOTED` |
| `result` | the PC | kind `job-result`, the job's name; body = the output | `KEPT` |
| `read` | the sender | JSON `{name, ts, sig}` — the job key's signature over the name and the time, good 15 minutes | the state and the output |

A name carries its signing time and is used once; a job older than 48 hours, over 256 KB, or of a type the PC does not
run is refused at the door. The queue is `/root/finance/reception_jobs/` (mode 700; files 600; cleared after 14 days;
`log.txt` has every step and never a job's text).

## How a chat sends a job by this door

1. Write the job; in the manojz VM: `python3 -B <kit>/reception_sign.py sign <key file> <job>` → the stamped job and its `.sig`.
2. From the assistant's browser, on any page of `https://followup.dr-manoj.in` (the login page will do), `fetch`
   `POST /finance/api/reception/jobs/submit` with `{name, job: base64 of the stamped file, sig}`.
   (Neither the manojz VM nor the cloud workspace can reach the server; the browser can.)
3. Within about a minute the PC takes it. To read: `python3 -B <kit>/reception_sign.py read-token <key file> <stamped name>`
   → one line of JSON → `POST /finance/api/reception/jobs/read`.

The Drive door is unchanged and stays the usual road; a job sent by both runs once (one list of used names).

## What this kit changes on the server

* `/root/finance/reception_door.py` — replaced (dfd557bc → the kit's): the five handlers; S449's two are untouched.
* `/root/finance/finance_app.py` — one anchored edit (e8dbf77e → a92baae4): the five paths join `PUBLIC_PATHS`.
* `/root/finance/reception_job_keys.txt` — new: one PUBLIC key, `parent-manojz`.

## The PC's side

Agent **S453.1** (`deploy_kits/S448_RECEPTION_AGENT/` and `deploy_kits/PC_KITS/reception/kit.zip`, 90e8e94e): asks
`next` once a minute, holds a server job to exactly the Drive door's rules, keeps a finished job's result on disk
(`server_results.json`) until the server has it — so an agent restart no longer loses it. It reaches the PC by a signed
job after this install; the Clinic PCs page serves it for any later reinstall.
Found while testing: the agent read at most 64 KB of any server answer, which would have cut a job of more than about
45 KB; the reader's cap is now the caller's (2 MB for `next`).

## Proof

`walk_s453.py` — the real `finance_app.py` over a scratch copy of `finance.db`, the kit's own agent unpacked from
`kit.zip` over real HTTP: 51 checks, and the box as it is (S451) showing all five doors shut by the gate. The kit's own
offline tests: 144 checks. The Windows side is proven after the install by a real job sent through this door.

## Install

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S453_RECEPTION_SERVER_DOOR/install_S453_RECEPTION_SERVER_DOOR.sh

Eight steps; restarts `clinic-finance` only; red after placing → both files put back. `DRY=1` places nothing.
