# COLD START KIT — Asset Register

*Everything a fresh Claude session (or a new person) needs to work on this system without re-explaining anything. Written 24 July 2026, system v1.1.0.*

---

## 1. Who and what

Dr Manoj Agarwal — solo orthopaedic surgeon, Bareilly UP, 30+ years. Runs the clinic plus NK Pathology (Dr Bhawna Agarwal, MD). Manages all digital infrastructure personally. Non-technical with code: needs **numbered furniture-assembly steps**, **full-file replacements only**, and **design approval before any build**.

**Asset Register** is a Flask + SQLite app on his VPS holding equipment, contracts, renewal dates, staff records and scanned documents. Live at https://assets.dr-manoj.in since 24 July 2026.

---

## 2. The five facts that explain most design choices

1. **The system exists to survive a manager transition.** Asset files sit in cabinets the current manager and accountant use. If he leaves, the knowledge leaves. That is why staff records were built in v1 even though data loads later.
2. **The manager operates it daily; the doctors own it.** Two roles, three identities — a shared login was considered and rejected because it gives no audit trail.
3. **Personal assets share the system but not the visibility.** Location classes hide owner-only rows from the manager entirely; `hide_price` hides money on assets he can otherwise see. **An invoice is a price disclosure — file access follows the price rule.**
4. **VPS is primary storage; Google Drive is backup only.** Live files in Drive would sit outside the app's permission gates. Backups go to his **personal** Google account, never the clinic one.
5. **Stability over features.** No new vendors, no fragile scraping, no app sprawl. Every custom service carries a documentation and maintenance tax that must be earned.

---

## 3. Access and infrastructure

| Thing | Value |
|---|---|
| VPS | 93.127.195.49 — Hostinger, AlmaLinux 9, CyberPanel / OpenLiteSpeed |
| App root | `/root/assetapp/` |
| Service | `assetapp.service`, gunicorn 2 workers, `127.0.0.1:8030` |
| gunicorn binary | `/usr/local/bin/gunicorn` |
| Domain | `assets.dr-manoj.in` (GoDaddy A record → VPS), Let's Encrypt SSL |
| Backups | `/root/backups/assetapp_YYYY-MM-DD.tar.gz`, nightly 02:30, 14-day retention |
| Users | `manoj`, `bhawna` (owner) · `manager` (manager) — passwords changed 24 Jul 2026 |
| Reminder API | `GET /api/due?token=…` — token on the Admin page |
| Repo | `D:\dr-manoj-git\drmanoj-clinic-automation`, folder `assetapp/`, pushed via GitHub Desktop |

Other clinic systems that touch this one's world: follow-up tracker (local Flask, VPS migration planned), attendance listener (port 8041, dashboard 8042), MyOperator WABA `9358008080`, existing **GAS document system** (holds personal identity documents — *not* this system's job).

---

## 4. Working rules with Dr Manoj

- **Design before code.** Present the plan, get explicit approval, then build.
- **Numbered steps, one action each,** with ✓ verification checkpoints. Quote exact commands.
- **Full-file replacements.** Never "change line 240" — hand over the whole file.
- **Deploy pattern:** WinSCP the file, `systemctl restart`, verify with `systemctl status` and a `curl`.
- **Test before deploy:** `smoke_test.py` must report `41 passed, 0 failed`.
- **PHI and staff financial data never reach cloud, chat or GitHub.**
- **Four-destination file workflow** for non-sensitive files: local download → Google Drive → NotebookLM → GitHub.
- **Every session ends with a durable markdown handoff and a carry-forward prompt.**
- Push back honestly when a proposal costs more than it returns — he wants the reasoning, not agreement.

---

## 5. Where things stand (as of 24 July 2026)

**Done:** app built (v1.1.0), 41/41 tests, deployed, SSL live, passwords changed, backup cron running, built-in scanner working.

**Not yet done:** rclone encrypted push to personal Drive; WhatsApp reminder cron consuming `/api/due`; first real assets entered; backlog invoice capture; Notion register row; GitHub push.

**Deliberately deferred:** scan-first asset creation (v1.2), Sarvam Vision invoice autofill (v1.3, gated on proven typing burden), migration of the GAS document system, retirement of the interim Google Sheet.

---

## 6. Do not do these

- Do not move live file storage to Google Drive.
- Do not add a second copy of asset data anywhere (Notion holds one *register row*, not the data).
- Do not put personal identity documents in this system — they live in the GAS system.
- Do not upload or overwrite `assets.db` or `uploads/` during a deploy.
- Do not build the Sarvam autofill before a trial batch proves accuracy on real Bareilly vendor bills — the sarvam-105b retirement is the precedent.
- Do not reuse the seeded `change-me-*` passwords anywhere; they are burned.
