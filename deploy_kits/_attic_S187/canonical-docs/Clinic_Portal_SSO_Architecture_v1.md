# CLINIC PORTAL + SINGLE SIGN-ON — ARCHITECTURE (design only)

**Owner:** Dr. Manoj Agarwal · Bareilly · **With:** Claude (Clinic Automation) · **07 Aug 2026 · v1**
**Status:** DESIGN — no code written. Nothing live changes until each step below is approved.
**Grounded in:** the actual auth code of `launcher/portal.py`, `attendance/att_dashboard.py`,
`staff_ledger/staff_ledger.py`, `assetapp/app.py` (read from the repo this session), + the Master
Estate Inventory v1.1.

---

## 1. Goal

- **Two portals**, one per person, each showing only the apps that person uses:
  - **Doctor portal** — the existing `/portal`, gaining a Salary/Ledger tile; keeps everything else.
  - **Manager portal** — NEW: Attendance + Asset Register + Staff Ledger **(entry only)**.
- **Single sign-on:** log in once at your portal → you are already signed in to every app its tiles
  open. No second password per app.
- **Hard line (F-31):** the manager never sees salary figures or the APPROVE button. Salary stays
  doctor-only. *(Already enforced in the ledger — see §5.)*

**In scope:** the clinic VPS Flask apps (portal, attendance, ledger, asset).
**Out of scope:** the Apps Script cockpit (Google-hosted — link-only, §6); the personal cluster
Rx/GutLog/FitLog (different trust class, its own switcher bar).

---

## 2. Why this needs a real (but small) build — the current auth reality

Each app authenticates differently today, with its own secret and its own idea of "who you are":

| App | Session mechanism | Secret | Per-user identity / roles |
|---|---|---|---|
| Portal `/portal` (:8099, followup.) | custom device-trust cookie `clinic_portal_device` after a PIN | `PORTAL_TOKEN_SEED` (env) | **none** — one PIN unlocks it |
| Attendance (:8042, attendance.) | custom HMAC cookie `att_session` (+ Basic-Auth fallback) | `cfg.SECRET_KEY` | **none** — single access |
| Ledger `/ledger` (:8043, attendance.) | Flask `session["u"]` | file `/root/staff_ledger/secret_key` | **yes** — `users.json`; roles `maker_full` / `maker_limited` / `checker` |
| Asset (:8030, assets.) | Flask `session["uid"]` + auth-epoch | DB `settings.secret_key` | **yes** — users table; roles owner / manager |

Consequences:
- **No shared secret, no shared identity.** A cookie scoped to `.dr-manoj.in` would *reach* all
  subdomains, but each app would reject it — it isn't signed with that app's secret and carries no
  identity that app understands. So SSO = give them all **one thing to trust**.
- **The role split already half-exists** (ledger + asset). Attendance and portal have no roles yet.

---

## 3. The design — an SSO broker + a shared verify-shim

One new small piece + a tiny addition to each app. Nothing is rewritten.

### 3.1 The SSO broker (the login owner)
The **portal grows into the broker** (simplest — it is already the login surface):
- Holds the **clinic user list + roles** — the single source of who can log in and as what.
  Two clinic roles to start: **`doctor`** and **`manager`** (extensible later, e.g. extra makers).
- Shows the **one login** (username + password; the current device-trust convenience can stay on top).
- On success, sets **one signed cookie**, `clinic_sso`, scoped to the whole family:
  `Domain=.dr-manoj.in; Secure; HttpOnly; SameSite=Lax`, ~30-day, carrying a signed token:
  `{ user, role, epoch, issued_at, expires_at }` — signed (itsdangerous/HMAC) with **one shared
  secret** (`CLINIC_SSO_SECRET`, env only, on every app; never in git/chat — F-31 family).
- A **"sign out everywhere"** control bumps a stored `epoch`; every app rejects older tokens at once
  (same idea the portal's "forget all devices" and the asset app's auth-epoch already use).

### 3.2 The shared verify-shim (what each app gains)
A ~15-line shared module, `clinic_sso.py`, imported by each VPS app. In the app's existing
`login_required` / access check, it does, in order:
1. If a valid `clinic_sso` cookie is present (signature OK, not expired, epoch current) →
   treat the request as **logged in** as `{user, role}`. Map that role to the app's local powers (§4).
2. Else → **fall back to the app's own existing login** (unchanged). So every app still works
   standalone, and the manual login is the permanent fallback (your rule).

Result: log in once at the portal → the `.dr-manoj.in` cookie rides to attendance, ledger, and asset
→ each shim accepts it → no second password. Log out once → gone everywhere.

### 3.3 Why not just share Flask sessions?
Ledger and asset both use Flask sessions, but with *different* secrets and the default cookie name.
Forcing them to share one raw session cookie couples their code versions, lets any app rewrite the
session, and doesn't carry roles cleanly. The signed-token broker keeps each app independent and the
role explicit. (Rejected alternative, recorded.)

---

## 4. Role → powers, per app (the permission map)

| App | `doctor` sees / can | `manager` sees / can |
|---|---|---|
| Portal | full doctor tile set | manager tile set only (attendance, asset, ledger-entry) |
| Attendance | full (view + month report) | full (same — no sensitive split here) |
| Asset Register | maps to **owner** role (all rows, prices, edit) | maps to **manager** role (its existing limited view) |
| Staff Ledger | maps to **checker** — approve, direct-enter, issue loans, **`/salary`** | maps to **maker** — enter events (pending); **no `/salary`, no APPROVE** |

The ledger and asset already *have* these roles, so the shim maps the SSO role onto the existing one —
little new permission logic. Attendance gains only "is there a valid SSO cookie?".

---

## 5. The F-31 salary line — already safe

`/salary` in `staff_ledger.py` is **checker-only** in the current code. A manager carries `role=manager`
→ mapped to **maker** → the ledger's own guard refuses `/salary` and the APPROVE action. So the manager
portal simply won't show a salary tile, and even a hand-typed `/ledger/salary` URL is refused by the
existing role check. No salary figure ever reaches a manager session. **No new enforcement needed —
we rely on the guard that's already there and verify it.**

---

## 6. The Apps Script boundary (doctor portal only)

The Callback/Call-Console cockpit is Google-hosted; we cannot set our cookie there. Its tile stays
**link-based** — it opens `/exec?k=DASH_KEY` already-unlocked via the key baked into the doctor tile.
That is sign-on-**by-link**, not true session SSO, and it's doctor-only. The manager portal has no
Apps Script tile, so the manager side is 100% true SSO with no exception.

---

## 7. Roll-out order (safe, one app at a time, fallback intact throughout)

Each step is independently testable; every app keeps working standalone after each step.

1. **Broker** — extend the portal: add the clinic user+role store, issue the `clinic_sso` cookie,
   add "sign out everywhere". Verify: doctor login sets the cookie; nothing else changes yet.
2. **Portal reads roles** — doctor vs manager tile sets driven by the token's role. (Manager can log
   in but their apps don't trust the cookie yet — they'll just show their own login; harmless.)
3. **Attendance shim** — accept `clinic_sso`; keep `att_session` + Basic-Auth as fallback. Verify:
   after portal login, attendance opens with no second login.
4. **Asset shim** — accept `clinic_sso` → map to owner/manager; keep its own login as fallback. Verify.
5. **Ledger shim** — accept `clinic_sso` → map to checker/maker; keep its own login as fallback.
   Verify a **manager** session cannot reach `/salary` (F-31 re-proven live).
6. **Manager portal tiles** — turn on the manager tile set; onboard the manager login.

Rollback at any step = remove the shim import from that one app; it returns to its own login. No app
is ever left unreachable.

---

## 8. Decisions I need from you before step 1

1. **Who is the manager, and how many manager logins?** One shared "manager" login, or a named login
   per person (e.g. Shavez, Alisha — who are already ledger makers)? Named is cleaner for audit; one
   shared is simpler. *(This also sets whether the manager role = ledger `maker_full` or `maker_limited`.)*
2. **Single user store or keep each app's users too?** Recommended: the broker becomes the **one**
   clinic login list; ledger/asset local users become fallback only. Confirm, or keep them independent.
3. **Doctor tile for the Apps Script cockpit** — keep the current key-in-link behaviour (recommended),
   yes/no.
4. **Personal cluster** — confirm it stays entirely out of the clinic SSO (recommended), or you want a
   single link-out "Personal" tile on the doctor portal.

Once these are set, I build **step 1 (the broker) offline**, you install and verify it, and we move
down the list one app at a time.

---

*End — Portal + SSO Architecture v1 (design). No live change until approved step by step.*
