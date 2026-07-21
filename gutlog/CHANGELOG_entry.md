## v3.2.0 - 21 July 2026 - Owner-key lock on the Account page

### Added
- **Owner key** - a second private secret (`settings.owner_hash`, Werkzeug-hashed),
  separate from the login password. Set once via a "Create your owner key" screen
  on the first visit to `/account`.
- **Change owner key** action on the Account page (requires the current owner key).

### Changed
- Every Account action now **requires the owner key**: change password, sign out
  all other devices, and rotate the owner key. The change-password form no longer
  asks for the current login password - the owner key is the sole authorisation.

### Security
- The login password now only unlocks the diary; it no longer grants control.
  Someone who knows only the login password can use GutLog but **cannot** change
  the password or lock the app. Only the owner key can.
- Forgotten owner key is recoverable server-side only (owner is root): write a new
  `owner_hash` into `settings`, or delete it to re-expose the create screen. No
  restart needed.

### Notes
- New settings key: `owner_hash`. No schema migration, no dependency change.
- Set the owner key immediately after deploy - whoever sets it first owns it.
- Still a single shared diary (not multi-user); per-user data isolation is future v4.

---

## v3.1.0 - 21 July 2026 - Account & multi-device sign-out

### Added
- **Account page** (`GET/POST /account`, login required) reachable from an
  **Account** link in the app header, next to Lock. It provides:
  - **Change password** - requires the current password; the new one must be
    8+ characters and different from the old. A checkbox (ticked by default)
    signs out all other devices at the same time.
  - **Sign out all other devices** - a standalone button that ends every other
    logged-in session (phone, tablet, browser) while keeping the current device
    signed in. No password change, no data affected.

### Changed
- `login_required` now also verifies a **session epoch**. Logins stamp the
  session with the current `settings.auth_epoch` token; the decorator re-checks
  it on every page and API request.

### Security
- Password changes and "sign out other devices" both **rotate `auth_epoch`**,
  which instantly invalidates every existing session on every device. This
  replaces the previous SSH-only remote-logout (delete `health3.db.secret` +
  `systemctl restart gutlog`). No diary data is read or written by either action.

### Notes
- First deploy of this build logs every device out **once** (existing sessions
  predate the epoch). Log in again and normal operation resumes.
- New settings key: `auth_epoch` (created automatically on first request).
- No schema migration, no dependency change (reuses Flask sessions + Werkzeug).
