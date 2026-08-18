# Clinic Master KB / Systems Register — v1.27

**Dr. Manoj Agarwal Clinic · Bareilly · Owner: Dr. Manoj Agarwal · Maintained with: Claude**

> **Delta document for v1.27.** Carries forward everything in v1.26 (and all prior versions) unchanged and adds the **Session 59 block (§59)** with decisions **D99–D100**, plus a **new §ATT — Attendance Subsystem** stanza (the attendance service was previously undocumented in KB/Runbook/GitHub — this session records it for the first time). **Code WAS touched this session (full EOS):** the attendance dashboard moved to HTTPS on its own subdomain and its login was rebuilt from HTTP Basic Auth to a signed-cookie session so an iPhone Home-Screen icon stays logged in. File changed: `att_dashboard.py`; one config line added: `att_config.py` (`SECRET_KEY`). **The follow-up/callback dashboard was NOT touched this session — it remains v18.18.** **KB wins on any conflict.**
>
> *(Session 58 was an EOS-light fold-in — no code — propagating the S57 close-out across Notion/Drive/GitHub. No §58 stanza was added to the KB; it is captured in Runbook v38. This KB advances v1.26 → v1.27 to cover the S59 code changes.)*

---

## §ATT ATTENDANCE SUBSYSTEM — first formal KB record (as of Session 59)

**Why this section exists:** the biometric-attendance web view has been running in production for some time but had **no entry in the KB, Runbook, or GitHub**. Session 59 changed its URL and login, which made the documentation gap urgent. This stanza is the canonical record going forward.

**What it is:** a small, **read-only** Flask web page that shows daily and monthly staff attendance, computed from biometric punch data. It is entirely separate from the follow-up/callback automation — different code, different service, different port. It reads punch + staff CSVs only; it never writes.

**Where it lives (VPS `93.127.195.49`, work as `root`):**

| Item | Value |
|---|---|
| Web view code | `/root/att_dashboard.py` (Flask) |
| Config (secrets) | `/root/att_config.py` — holds `DASHBOARD_USER`, `DASHBOARD_PASSWORD`, `DASHBOARD_PORT` (8042), `EXCLUDE_IDS`, and (new S59) `SECRET_KEY` |
| Shared logic | `/root/att_core.py` (`compute_day`, `load_staff`, `load_punches`) |
| Capture service | `attlistener_v2.py` — Secureye device proxy + punch capture (**untouched this session; do not disturb**) |
| Web systemd service | `attendance-dashboard` (`systemctl restart attendance-dashboard`) |
| Capture systemd service | the `attlistener`/Secureye unit (separate) |
| Internal port | **8042** (Flask binds `0.0.0.0:8042`) |
| **Public URL (new, S59)** | **`https://attendance.dr-manoj.in`** |
| Fallback URL | `http://93.127.195.49:8042/` (still works) |
| Backup of pre-S59 code | `/root/att_dashboard.py.bak-s59` |
| Backup of pre-S59 vhost | `/root/vhost.conf.attendance.bak` |

**HTTPS front door (new, S59):**
- GoDaddy DNS: **A-record `attendance` → `93.127.195.49`** (added S59; propagation verified via Google public DNS).
- CyberPanel website `attendance.dr-manoj.in` with **Let's Encrypt SSL** (auto-renews; the ACME `/.well-known/acme-challenge` context is preserved in the vhost so renewal keeps working).
- OpenLiteSpeed **reverse proxy** in `/usr/local/lsws/conf/vhosts/attendance.dr-manoj.in/vhost.conf`: an `extprocessor` of `type proxy` → `127.0.0.1:8042`, and `context /` handing all traffic to it. `:8042` itself was not changed.
- Restart after any vhost edit: `/usr/local/lsws/bin/lswsctrl restart`.

**Login (new, S59):**
- Was **HTTP Basic Auth** (browser popup). iPhone **Home-Screen icons run in iOS standalone mode**, which does **not** replay Basic Auth credentials saved in Safari — so the icon rejected logins.
- Now a **cookie session**: a `/login` form (mobile-friendly) sets a **signed 30-day cookie** (`att_session`), signed with `SECRET_KEY` via Python's built-in `hmac`/`hashlib` (no new library). `/logout` clears it.
- `authed()` accepts **either** the valid cookie **or** Basic Auth (fallback) → the old IP URL and any saved-password bookmark keep working. Unauthenticated visits **redirect to `/login`** (no more Basic Auth popup) — this is what makes the Home-Screen icon work.
- Cookie flags: `secure=True, httponly=True, samesite="Lax"`, `max-age = 30 days`. Same shared username/password as before (in `att_config.py`).
- `SECRET_KEY` was generated **on the server** (`secrets.token_hex(32)`) and appended to `att_config.py` — never seen in chat.

**Recovery (if the attendance web view breaks):**
1. `systemctl restart attendance-dashboard` → check `systemctl is-active attendance-dashboard`.
2. If it fails: `journalctl -u attendance-dashboard -n 30 --no-pager`.
3. Roll back code: `cp /root/att_dashboard.py.bak-s59 /root/att_dashboard.py && systemctl restart attendance-dashboard`.
4. Roll back the HTTPS proxy: `cp /root/vhost.conf.attendance.bak /usr/local/lsws/conf/vhosts/attendance.dr-manoj.in/vhost.conf && /usr/local/lsws/bin/lswsctrl restart`.
5. The raw fallback `http://93.127.195.49:8042/` bypasses the proxy entirely and answers directly from Flask.

**Still not in GitHub:** the attendance code (`att_dashboard.py`, `att_core.py`, `attlistener_v2.py`) is **not yet in the repo**; `att_config.py` must **never** go to GitHub (holds secrets). See §59 "Carried to next session" — committing the non-secret attendance code (with `att_config.py` gitignored) is a recommended follow-up.

---

## §12 STATE — what is live right now (updated at Session 59 close)

- **Follow-up/callback dashboard remains v18.18 LIVE — NOT touched this session.** All §12 state from v1.26 stands verbatim (WhatsApp tap-to-call D97; stale-list top-bar guard D98; duration gate D82; `call-hook` service D80; `Call_Durations` tab; per-agent logins D76; caller-ID save SOP D93; D66 vanish-on-file verified live; diagnosis normalisation flowing; key rotation critically overdue; `AKEY_14` flagged; PHI base swap deferred; Task Scheduler watcher failure parked with manual `python push_followups_today.py --push` fallback).
- **Attendance web view is now HTTPS + cookie-login LIVE (D99, D100).** Public URL `https://attendance.dr-manoj.in`; iPhone Home-Screen icon opens already-logged-in (owner-verified end-to-end). Old IP URL retained as fallback. See §ATT for the full record.
- **Session 58 (EOS-light) housekeeping stands:** S57 close-out fully propagated across Notion + Drive + GitHub; Drive holds the current canonical set as a cold backup (Drive connector cannot write — future Drive updates are an owner PC-side drag-drop).

**Known open (top of next backlog):** **"Agent shows as Staff" attribution bug** (still open — parked again this session in favour of the attendance work; not yet diagnosed; needs a read of the server-side agent-field build in `CallConsole.gs`/`OutcomeLog.gs`). Then the data pass: **Docterz periodic fill** → **one-month follow-up data analysis** → **tier/track finalisation + track-first flowchart**. Then **P1–P10 lock (D83–D92)** and **D78 sticky-on-staff counter** (after the data pass). Parallel: 🔴 service-account key rotation (Lokesh); `AKEY_14` rotation; PHI base swap; Sarvam auto-retry; Call_Feed D61; `call_transcription.py` GitHub commit; **(new) commit non-secret attendance code to GitHub.**

---

## §59 SESSION 59 — Attendance HTTPS migration + cookie-session login (04 Jul 2026)

**Code changed. Full EOS.** Decisions **D99–D100**. File changed: `att_dashboard.py`. Config line added: `att_config.py` (`SECRET_KEY`). No follow-up-dashboard change (still v18.18). No new VPS Python service (reused existing `attendance-dashboard`); one new CyberPanel website + one OpenLiteSpeed reverse-proxy vhost.

### The problem (owner-reported)
Staff open the attendance page on an **iPhone**, but the page (served as raw `http://93.127.195.49:8042/`) **loaded poorly in Safari** — bare-IP `http://` pages stall/blocked. After moving to HTTPS and saving the login in Safari it worked, but a **Home-Screen shortcut refused the login** (showed the box, rejected correct credentials).

### Root causes
1. **Bare IP over HTTP.** iOS/Safari handle a raw `http://IP:port` badly; and a normal SSL certificate **cannot be issued to a bare IP** — it must be a domain name.
2. **Basic Auth + iOS standalone mode.** A Home-Screen icon runs in a **separate credential jar** from Safari and does not replay saved HTTP Basic Auth — so the icon's login failed even with the right password.

### Part A — HTTP → HTTPS on a subdomain (D99) — LIVE
Routed the attendance page through the existing domain's SSL instead of trying (impossibly) to certify a bare IP:
- Added GoDaddy A-record `attendance.dr-manoj.in → 93.127.195.49`; verified public propagation via Google DNS.
- Created CyberPanel website `attendance.dr-manoj.in` + issued Let's Encrypt SSL.
- Wrote an OpenLiteSpeed reverse-proxy vhost → `127.0.0.1:8042`, preserving the ACME challenge context for auto-renewal. `:8042` service itself untouched.
- Verified: `https://attendance.dr-manoj.in` returns the app (initially `401`, then after Part B, `302 → /login`). Old `http://93.127.195.49:8042/` retained as fallback.

*(One process note: pasting large text into `nano` truncated twice; the reliable method was a single `cat > file << 'EOF' … EOF` heredoc, then verify by line-count + last-line + a grep for the key marker before restarting. Recorded for future VPS file edits where WinSCP isn't in hand.)*

### Part B — Basic Auth → signed-cookie session login (D100) — LIVE
Rebuilt `att_dashboard.py` auth so a Home-Screen icon stays logged in:
- Added `SECRET_KEY` (generated on-server, `secrets.token_hex(32)`) to `att_config.py`.
- New `/login` mobile form + `/logout`; login sets a **signed 30-day `att_session` cookie** (`hmac`/`hashlib`, no new dependency).
- `authed()` accepts **cookie OR Basic Auth** (zero regression: old IP URL + saved bookmarks still work). Unauthenticated → **redirect to `/login`** (kills the Basic Auth popup that iOS standalone couldn't satisfy).
- Everything else in the file — attendance logic, month view, CSS, auto-refresh — is **byte-for-byte unchanged**. Added a small "Sign out" footer link.
- Build discipline: built offline, `py_compile` OK, delivered as a downloadable file, uploaded via WinSCP, **md5-verified on the VPS** (`225d6d9d049cf65a8974422ca3fb594e`) before restart. Backup at `/root/att_dashboard.py.bak-s59`.

### Verification (owner-confirmed)
- Service `active` after restart.
- `https://attendance.dr-manoj.in/` → `302 → /login`; `/login` → `200`.
- iPhone: login form (not the old popup) shows; sign-in works; **Home-Screen icon opens already-logged-in.** Owner: "all working now."

### Login for staff (owner question, answered)
The attendance page's staff-login need is **fully met** by the shared cookie login above — staff open the URL, sign in once with the shared credentials, Add to Home Screen. **Individual per-person logins were not needed** (shared login is the right level for a solo practice). A staff login for the **launcher portal** (`followup.dr-manoj.in/portal`) was noted as a **future** need and parked — a separate build when the owner is ready.

### Carried to next session
1. **[Open bug] "Agent shows as Staff"** — still the top open follow-up-dashboard item; parked again this session; not yet diagnosed.
2. **[New] Commit non-secret attendance code to GitHub** (`att_dashboard.py`, `att_core.py`, `attlistener_v2.py`); `att_config.py` gitignored (secrets). Removes the single-point-of-failure of attendance code existing only on the VPS.
3. Data pass (unchanged): Docterz fill → one-month analysis → tier/track → flowchart.
4. P1–P10 lock (D83–D92); D78 sticky counter (after the data pass).
5. Parallel tracks unchanged (key rotation, AKEY_14, PHI base swap, Sarvam retry, Call_Feed D61, call_transcription.py commit).

---

## DECISIONS ADDED THIS SESSION

| # | Decision |
|---|---|
| **D99** | **Attendance moved to HTTPS on its own subdomain (LIVE).** `https://attendance.dr-manoj.in` via GoDaddy A-record + CyberPanel Let's Encrypt SSL + OpenLiteSpeed reverse proxy → `127.0.0.1:8042`. A bare IP cannot hold an SSL cert, so the fix is a subdomain on the existing domain's certificate, not certifying the IP. ACME challenge context preserved for auto-renew. `:8042` service untouched; raw IP URL retained as fallback. **Rule:** any internal `http://IP:port` service that must open cleanly on an iPhone gets a subdomain + reverse proxy, never a bare-IP cert attempt. |
| **D100** | **Attendance login rebuilt: Basic Auth → signed-cookie session (LIVE).** iOS Home-Screen (standalone) mode won't replay HTTP Basic Auth, so the icon rejected logins. New `/login` form sets a signed 30-day cookie (`SECRET_KEY` in `att_config.py`, `hmac`, no new library); `authed()` accepts cookie **or** Basic Auth (fallback, zero regression); unauthenticated redirects to `/login`. **Rule:** for any small internal web page that needs an iPhone Home-Screen icon, use a cookie-session login, not Basic Auth. |

---

## CHANGELOG
- **v1.27** (04 Jul 2026, Session 59 — full EOS, code changed): +§59, +§ATT (first formal record of the attendance subsystem). Decisions **D99–D100**. `att_dashboard.py` changed; `att_config.py` gained `SECRET_KEY`. Attendance moved to `https://attendance.dr-manoj.in` (subdomain + Let's Encrypt + OpenLiteSpeed reverse proxy) and its login rebuilt to a signed-cookie session so the iPhone Home-Screen icon stays logged in — owner-verified end-to-end. **Follow-up/callback dashboard NOT touched — still v18.18.** All prior D-series (D1–D98) in force verbatim.
- **v1.26** (04 Jul 2026, Session 57 — full EOS, code changed): +§57. Decisions **D97–D98**. `Dashboard.html` + `CallConsole.gs` changed. Dashboard v18.16 → **v18.18** (three deploys). WhatsApp tap-to-call (D97) + stale-list top-bar guard (D98) shipped & owner-verified live. D66 vanish-on-file verified already-live. Stamp discrepancy reconciled: live is v18.18. P1–P10 remain reserved as D83–D92. All prior D-series (D1–D96) in force verbatim.
- **v1.25** (04 Jul 2026, Session 56 — EOS-light): No code changed. +§56. Decisions D93–D96. §12 updated. P1–P10 reserved as D83–D92.
- **v1.24** (03 Jul 2026, Session 55 — EOS-light): No code changed. +§55. P1–P10 proposed. Lifecycle Tree v1.0.
- **v1.23** (03 Jul 2026, Session 54): Dashboard v18.16 LIVE (duration gate). +§54. D80–D82.
- **v1.22** (03 Jul 2026, Session 53): Dashboard v18.15 live. +§53. D76–D79.
- **v1.21** (03 Jul 2026, Session 52): Dashboard v18.14 live. +§52. D70–D74.
- **v1.20** (03 Jul 2026, Session 51): Dashboard v18.8 live. +§51. D67–D69.
- **v1.19** (Jul 2026, Sessions 46–50): +§46–§50. D62–D66.
- **v1.18** (02 Jul 2026, Sessions 31–45): as previously recorded.
