# S961_RECEPTION_FAST_UPLOAD — session 528, 26-Nov-2026 — D1080 (kit B of the Morning Match), F-1687

**Why.** The reception agent posted a Docterz report to the server only right after its 5-minute heartbeat. The reception
PC is usually switched off soon after the evening export, so from 16 to 25 Nov none of the five evening exports came by
this road; they arrived the next morning (or by the Drive pickup).

**What changed (agent S456.1 `d3d4b67b` → S961.1 `5896d665`, `C:\ClinicAgent\reception_agent.py`).** Every 5-second tick
a *fast lane* looks at the two export folders (Docterz exports on the clinic Drive, and Downloads) — names, sizes and
times only, nothing opened. When a Docterz report has changed and stood still for 20 seconds it is posted at once through
the same signed upload and the same checks as before (name AND first line, the sent-ledger by md5). The 5-minute pass
stays as the fallback. The lane runs only after the server has accepted a heartbeat since the start and while heartbeats
are not failing; a refused post waits 60 s, doubling to 30 minutes on repeated refusals; a report that cannot yet be read
is looked at again for two minutes; `"fast_upload": false` in `config.json` turns it off. The heartbeat gains four
fields under `direct_upload` (`at_once`, `sent_at_once_since_start`, `last_sent_at_once`, `last_seconds_after_save`) —
counts and times only, no names. Nothing on the server changed: the report door (`reception_door.py`) and
`docterz_pickup.take()` — which since S960 starts the evening check — are untouched.

**Proof.** `walk_s961.py <agent>` 31/31 on S961.1, red on S456.1 (the control) · `walk_s961_main.py` the real loop 3/3
(a report posted 1 s after it stood still), red on S456.1 · the kit's own `tests/test_kit.py` 158/158 ·
`rehearse_s961.py` 7/7: the guard runs S456.1, job j48 run BY the agent, the agent takes its own update and comes back as
S961.1 with `.prev` = S456.1, a broken update refused · a cold review (0 MUST, 7 SHOULD built in) and a second look
(0 MUST, 2 SHOULD built in). Live: j47 read the PC first (S456.1 `d3d4b67b` running); j48 wrote `.new` 15:36:24;
the agent restarted under its guard 15:36:27; j49 read S961.1, `.prev` S456.1, heartbeat accepted, no error.

**Delivery.** `j48_agent_S961_1.py` is the job as sent (the agent zlib+base64 inside; it writes nothing unless the running
agent is S456.1, compiles the new one first, and the guard restores `.prev` if the new one dies). The signed copies and
the read-backs are in `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S528\reception_jobs\`.

**Undo.** A signed job that copies `C:\ClinicAgent\reception_agent.py.prev` to `reception_agent.py.new` (the agent takes it
the same way), or `"fast_upload": false` in `C:\ClinicAgent\config.json` to switch only the fast lane off.

The living reinstall kit `deploy_kits/S448_RECEPTION_AGENT/` and `deploy_kits/PC_KITS/reception/kit.zip` carry S961.1.
