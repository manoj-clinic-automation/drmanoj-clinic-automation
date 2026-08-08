# START HERE — SESSION 161 (session-specific entry point, regenerated at S160 close)

Hi Claude. Continuing the clinic-automation project — **Session 161**. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Bareilly. Solo practice, older Hindi-first semi-urban patients.

**Do Phase 0 FIRST (D247), before anything else:**
1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 linchpin) and **md5-verify every row**. A mismatch halts work until reconciled (D172/D188). The S160 set: Register **v3.3** (`89d060bf…`), History Archive **v1.12** (`5c3cfd29…`), Runbook **v98** (`8cbff4c4…`), Fault Register **v2.6** (`6e90861e…`), this START_HERE, the new Tier-1 dossier `Staff_Daily_Register_Dossier_v1_0.md` (`84fe26dd…`, **DRAFT**).
2. Read into context only **Tier 0** (manifest, this file, KB Register v3.3, Runbook v98). Open Tier 1 only if the task touches it. Tier 2 is hash-verified, never read in the loop.
3. Confirm, then ask which **HANDOFF_RUNBOOK §2** backlog item to start.

**Where S160 left it (Runbook §0 has the detail):**
- Portal live at `81c2baef…` (health tiles + sectioned mobile layout).
- **D270** Case Pack → VPS (off-Drive) decided; build parked behind a phase-3 strategy hard-bake.
- **D271** Staff Daily Register subsystem designed; **dossier v1.0 `84fe26dd…` is a Tier-1 DRAFT awaiting owner sign-off.**

**Most likely first moves this session (owner's call):**
- **Sign off the dossier** → start the **Staff Daily Register build** (page-first: SQLite store + maker/checker/override screen). *(Runbook §2 item 1.)*
- Or the **phase-3 local-apps strategy doc** (gates Case Pack build; §2 item 2).
- Or the queued list: repo commits (portal + dossier) · WABA operationalise · Callback polish · cold-kits.

**Working protocol (strict):** plain language; ONE step at a time, wait for explicit OK; full-file replacements only; mask patient numbers (last-4) and all secrets; nothing live rebuilt without OK; build offline → `py_compile` on `/root/wa/venv/bin/python3` → **for live Flask, a test-client route hit (F-63)** → owner installs → md5 verify. ALL-CAPS from me = urgent.

**Parked (do not raise unless I ask):** F-56 service-account key rotation + CALLHOOK Steps 3–4 (Lokesh); SSO passthrough for the 3 health apps.

**Next free: D272 · F-64 · Session 161.**
