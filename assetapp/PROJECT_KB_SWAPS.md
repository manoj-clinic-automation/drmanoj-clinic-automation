# PROJECT KB SWAPS — after 24 July 2026 session

Actions for the **website / SEO / content** project knowledge base.

## ADD (upload to project knowledge)

| File | Why |
|---|---|
| `Asset_Register_DOSSIER.md` | Canonical description of the live system — the one file that must be present in any future session |
| `COLD_START_KIT_AssetRegister.md` | Lets a fresh session work without re-explaining infrastructure, roles or rules |
| `HANDOFF_2026-07-24_AssetRegister.md` | Session narrative, decisions and the open-items list |

*(Rename `DOSSIER.md` → `Asset_Register_DOSSIER.md` on upload, so it does not collide with dossiers of other systems.)*

## KEEP

- `Pilibhit_City_Page_FINAL.docx` — city-page template, still the active pattern for Budaun / Shahjahanpur / Rampur / Moradabad
- `END_OF_SESSION_PROMPT.md` — session-close convention
- Surgical case-pack and TPA files — separate active workstream, untouched this session

## RETIRE / DEMOTE

| File | Action | Why |
|---|---|---|
| `vCard_Hosting_Handover.md` | Verify then remove | `save.dr-manoj.in` has been live for some time; the handover document is stale and risks misleading a future session |
| `Asset Register.xlsx` (interim Sheet, in Drive not KB) | Archive after first real app entries succeed | Superseded by the app; must not become a second live register |
| `Docterz_Followup_Tracker_Project.md` | Move to *Clinic Systems & Automation* | Belongs with VPS and pipeline work, not website/content |

## GIT

Push the folder `assetapp/` (7 files: `app.py`, `smoke_test.py`, `DOSSIER.md`, `DEPLOY.md`, `CHANGELOG.md`, `README.md`, `.gitignore`) to `drmanoj-clinic-automation` via GitHub Desktop. Commit message:

```
Asset Register v1.1.0 — initial release + built-in scanner

Flask/SQLite asset, contract and staff-document register with
two-role access control, location-class visibility, hide_price
extending to invoice files, browser-native document scanner,
and a token-gated /api/due endpoint for WhatsApp reminders.
Deployed to assets.dr-manoj.in. 41/41 smoke tests passing.
```

Confirm the root `.gitignore` still blocks `*.db` and `uploads/` — the folder-level `.gitignore` covers it, but belt and braces.

## DRIVE

Upload the same seven files to the Drive backup folder for the repo, plus the three session documents. Sensitive files: none in this set — no PHI, no credentials, no staff financial data. The API token and passwords are **not** written into any of these documents by design.
