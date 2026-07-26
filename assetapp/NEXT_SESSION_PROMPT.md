# NEXT SESSION — CARRY-FORWARD PROMPT

*Paste this at the start of the next session in the **website / SEO / content** project.*

---

Continuing from the 24 July 2026 session. Context files in project knowledge: `Asset_Register_DOSSIER.md`, `COLD_START_KIT_AssetRegister.md`, `HANDOFF_2026-07-24_AssetRegister.md`.

**Where we are:** Asset Register v1.1.0 is live at https://assets.dr-manoj.in — Flask + SQLite on the VPS, three users (manoj / bhawna as owners, manager), location-class visibility with `hide_price` extending to invoice files, built-in browser scanner, staff module present but empty, nightly local backups running, 41/41 smoke tests passing.

**Pick up with whichever applies:**

1. **First real data.** I have entered the first assets / attached the first scanned invoice. Here is what worked and what did not — help me fix the friction.
2. **Backlog trial batch.** Here are photos of ~10 bills. Extract vendor, purchase date, price, serial into a review table with an uncertainty flag on anything doubtful. I will add location, category, warranty and AMC details myself. Also tell me whether the volume justifies a one-time import script.
3. **v1.2 scan-first flow.** Real use has shown create-then-scan is the wrong order. Build "+ New from scan": scan first, form second, attachment automatic on save.
4. **Sheet retirement.** The app has proven itself — walk me through archiving the interim Google Sheet and the three Drive invoice folders without losing anything.
5. **Something broke.** Here is the exact screen text or log output.

**Not in this project** — these belong in *Clinic Systems & Automation*: the rclone encrypted backup push to my personal Drive, and the WhatsApp cron consuming `/api/due`.

**How I work:** numbered furniture-assembly steps, one action each, with verification checkpoints. Full-file replacements only. Design and approval before any build. Test suite must pass before deploy. Push back honestly if something costs more than it returns.
