# SESSION HANDOFF — 24 July 2026 — Asset Register build & deploy

**Project:** Website / SEO / Content project (build spilled over from a register discussion)
**Duration:** Design → build → deploy in one session
**Outcome:** Asset Register v1.1.0 live at https://assets.dr-manoj.in

---

## What happened, in order

1. **Requirement raised:** a system for assets (equipment, batteries) with purchase, warranty and AMC/CMC details, spanning NK Path, clinic, and personal assets of both doctors.
2. **Platform debated:** Notion proposed → rejected (unfamiliar) → Google Sheet in Drive built instead, with folders for invoices. Ownership settled on the **personal** Google account, not the clinic account, because the register spans personal items and clinic accounts are staff-accessible.
3. **Sheet built and delivered.** First Drive upload arrived corrupted (base64 transfer through the Drive connector damaged the zip); re-delivered as a direct download. *Lesson recorded: deliver binary files as downloads, not via the Drive connector.*
4. **Scope widened.** A driving licence was added, revealing that the register was drifting into "documents with expiry dates". Ruled: personal identity documents stay in the existing GAS system; this system holds equipment and staff records.
5. **Platform reconsidered — correctly.** The manager will operate it routinely on the clinic PC, which changes the usage profile that justified a spreadsheet. Decision: build a Flask app.
6. **Access model designed:** three identities, two roles, location-class visibility, per-asset `hidden` and `hide_price`, with file access following the price rule.
7. **Built v1.0.0** (34 checks passing), then **v1.1.0** adding the built-in browser scanner (41 checks). One P0 caught in testing: page bodies were being HTML-escaped by nested template rendering.
8. **Deployed** — systemd unit, DNS, OpenLiteSpeed proxy, SSL, passwords changed, backup cron. All verifications passed.
9. **Backlog OCR discussed.** Sarvam Vision identified as the right future engine (existing vendor, Indic-first, strong benchmarks) but gated on a trial batch, per the sarvam-105b precedent.

---

## Decisions made (durable)

- Personal Google account owns this system's backups; the clinic account never touches it.
- VPS is primary storage for files; Drive is for encrypted backup only.
- Uniform 60-day amber threshold for warranties, AMC and CMC.
- Staff module built in v1, data loaded later — the point is continuity through manager transition.
- Notion gets **one register row**, not a parallel copy of the data.
- Backlog invoices are read in chat, not through a built OCR pipeline; a one-time import script is worth writing only if the backlog exceeds roughly 50 items.

---

## Open items, in priority order

| # | Item | Where it belongs |
|---|---|---|
| 1 | Enter first real assets; attach one scanned invoice end-to-end | This project — do before anything else |
| 2 | Manager sets his own password; walk him through his first entries | Clinic operations |
| 3 | rclone encrypted nightly push of `/root/backups/` to **personal** Drive | Clinic Systems & Automation |
| 4 | WhatsApp cron consuming `/api/due` → renewal alerts | Clinic Systems & Automation |
| 5 | Trial batch of ~10 bills: upload here **and** through Sarvam playground; compare | This project |
| 6 | Decide import script vs manual entry based on backlog size | After #5 |
| 7 | v1.2 scan-first asset creation | After a week of real use |
| 8 | Retire the interim Google Sheet; archive the Drive invoice folders | After #1 succeeds |
| 9 | v1.3 Sarvam Vision autofill | Only if entry volume proves the need |
| 10 | GAS document-system migration | Deferred indefinitely; revisit after months of stable use |

---

## Files produced

**Git kit** (repo folder `assetapp/`): `app.py`, `smoke_test.py`, `DOSSIER.md`, `DEPLOY.md`, `CHANGELOG.md`, `README.md`, `.gitignore`

**Session documents:** this handoff, `COLD_START_KIT_AssetRegister.md`, `NEXT_SESSION_PROMPT.md`

---

## Carried-over context worth keeping

- The Drive connector corrupts binary uploads — always deliver files as downloads.
- The interim Google Sheet and its three invoice folders still exist in personal Drive. They become the migration source, then archive. Do not let them become a second live register.
- The clinic's physical asset files remain the accountant's primary reference; the app is the working reference and the continuity insurance.
