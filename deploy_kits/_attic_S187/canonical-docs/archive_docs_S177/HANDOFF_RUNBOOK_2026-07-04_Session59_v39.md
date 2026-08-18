# HANDOFF RUNBOOK — 2026-07-04 — Session 59 — v39

## §0 — What happened this session (full EOS, CODE CHANGED)

**Attendance subsystem: HTTPS migration + login rebuild.** The follow-up/callback dashboard was **not** touched — it stays **v18.18**. All work this session was on the separate **attendance web view** (`/root/att_dashboard.py`, port 8042).

**The problem:** staff open attendance on an iPhone. Served as raw `http://93.127.195.49:8042/`, it loaded badly in Safari, and after switching to HTTPS a **Home-Screen shortcut refused the login**.

**Two root causes, two fixes:**

1. **Bare IP + HTTP** → moved to **HTTPS on a subdomain** (D99).
   - GoDaddy A-record `attendance.dr-manoj.in → 93.127.195.49` (public propagation verified).
   - CyberPanel website + **Let's Encrypt SSL**.
   - OpenLiteSpeed **reverse proxy** vhost → `127.0.0.1:8042` (ACME challenge context preserved for auto-renew).
   - New public URL **`https://attendance.dr-manoj.in`**; old IP URL kept as fallback.
   - A bare IP can't hold an SSL cert — the fix is a subdomain on the existing cert, not certifying the IP.

2. **HTTP Basic Auth + iOS standalone mode** (Home-Screen icons don't replay Basic Auth) → rebuilt login as a **signed-cookie session** (D100).
   - `SECRET_KEY` added to `att_config.py` (generated on-server, never seen).
   - New `/login` form + `/logout`; sets a signed **30-day** `att_session` cookie (`hmac`, no new library).
   - `authed()` accepts **cookie OR Basic Auth** → zero regression (old IP URL + saved bookmarks still work). Unauthenticated → redirect to `/login` (kills the popup iOS standalone couldn't satisfy).
   - Rest of the file byte-for-byte unchanged; added a "Sign out" footer link.

**Build discipline:** built offline → `py_compile` OK → downloadable file → WinSCP upload → **md5-verified on VPS** (`225d6d9d049cf65a8974422ca3fb594e`) → backup `/root/att_dashboard.py.bak-s59` → restart → verified. Owner confirmed **"all working now"**: the iPhone Home-Screen icon opens already-logged-in.

**Also this session:** the attendance subsystem got its **first formal documentation** — new **§ATT** stanza in KB v1.27 (it was previously undocumented in KB/Runbook/GitHub).

**Owner's login question, answered:** the attendance page's staff-login need is fully met by the shared cookie login (staff sign in once, Add to Home Screen). A staff login for the **launcher portal** was noted as **future** and parked.

## §1 — System state

- **Follow-up/callback dashboard v18.18 LIVE — unchanged this session.** Manual push fallback unchanged (`python push_followups_today.py --push`). All prior open issues carry forward verbatim.
- **Attendance web view LIVE at `https://attendance.dr-manoj.in`** (HTTPS + cookie login). Internal Flask on `:8042` unchanged; `attendance-dashboard` systemd service; `attlistener_v2.py` capture untouched. Fallback `http://93.127.195.49:8042/` still works.
- **Backups on VPS:** `/root/att_dashboard.py.bak-s59` (pre-S59 code), `/root/vhost.conf.attendance.bak` (pre-S59 vhost).
- **Archive:** project knowledge + GitHub are source of truth; Notion decisions log current through S59; Drive holds the current canonical set as cold backup (Drive connector cannot write — owner PC-side drag-drop from the cold-backup zip).

## §2 — Backlog / NEXT (priority order)

**TOP OPEN DASHBOARD BUG (carried, parked again this session):**
1. **"Agent shows as Staff"** — escalation tiles show a wrong/generic agent name. NOT yet diagnosed. Read the server-side agent-field build in `CallConsole.gs`/`OutcomeLog.gs` (candidate causes: literal-label vs stale-attribution). Highest-value open follow-up-dashboard item. **Recommended first task for Session 60.**

**NEW this session:**
2. **Commit non-secret attendance code to GitHub** — `att_dashboard.py`, `att_core.py`, `attlistener_v2.py`. `att_config.py` gitignored (holds secrets). Removes the risk of attendance code existing only on the VPS.

**The data pass (owner action first):**
3. [Owner] Run the Docterz periodic fill — must precede analysis.
4. [Next] One-month follow-up data analysis (aggregate only).
5. Decide PHI-access method (PHI-stripped export recommended).
6. Finalise tier/track assignments → draw the track-first flowchart.
7. Define clinician-set phase/severity capture (visit-workflow step).

**Pending lifecycle block (from §55):**
8. Lock P1–P10 as D83–D92.
9. Taxonomy tier-mapping sheet.
10. Pick 3rd-strike WABA template.
11. D78 sticky-on-staff cross-day counter (AFTER the data pass).

**Parallel-track:** 🔴 service-account key rotation (Lokesh); AKEY_14 rotation; PHI base swap; Docterz sentinels; Sarvam auto-retry; Call_Feed (D61); verify call_transcription.py commit.

**Future (parked, owner-noted this session):** staff login for the launcher portal (`followup.dr-manoj.in/portal`).

## §3 — Deploy verification (this session)
- `att_dashboard.py` md5 on VPS = `225d6d9d049cf65a8974422ca3fb594e` (matches built file).
- `systemctl is-active attendance-dashboard` → `active`.
- `https://attendance.dr-manoj.in/` → `HTTP/2 302`, `location: /login`; `/login` → `HTTP/2 200`.
- iPhone Home-Screen icon opens already-logged-in — owner-confirmed.
