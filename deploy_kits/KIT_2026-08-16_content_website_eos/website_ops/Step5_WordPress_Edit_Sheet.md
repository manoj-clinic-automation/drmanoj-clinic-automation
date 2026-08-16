# Step 5 — WordPress Edit Sheet (in-house, easiest automated method)
**Site:** drmanojagarwal.com (WordPress + Elementor 4.1.2) · **Backup:** confirmed auto-backup to clinic Google Drive — take a fresh one before starting.

> **Easiest automated method:** the bulk text changes below are all done with **one plugin — Better Search Replace** (Plugins → Add New → "Better Search Replace"). It edits the whole database at once, handles Elementor's serialized data correctly, and has a **dry-run** mode. The structural items (dedupe, schema, speed) are a short manual pass after.

---

## A. Bulk text swaps — run in Better Search Replace
**Procedure:** Tools → Better Search Replace → enter each pair → select *all tables* → tick **"Run as dry run"** first → review counts → untick dry-run → **Run**. Then clear cache + regenerate Elementor CSS (Section C).

| # | Find (exact) | Replace with | Why |
|---|---|---|---|
| 1 | `Best Orthopedic Surgeon in Bareilly` | `Experienced Orthopedic Surgeon in Bareilly` | NMC — drop "Best" |
| 2 | `Best Orthopedic Specialist in Bareilly` | `Senior Orthopedic Specialist in Bareilly` | NMC |
| 3 | `Best Orthopedic Specialist Bareilly` | `Experienced Orthopedic Specialist, Bareilly` | NMC (title/meta form) |
| 4 | `Best Orthopedic Doctor in Bareilly` | `Trusted Orthopedic Doctor in Bareilly` | NMC |
| 5 | `Our Specialities as Best Orthopedic Surgeon` | `Our Orthopedic Specialities` | NMC |
| 6 | `the best orthopedic specialist Bareilly` | `an experienced orthopedic specialist in Bareilly` | NMC (meta description) |
| 7 | `Bareilly Orthopaedic Centre` | `Dr. Manoj Agarwal Clinic` | Branding rule — remove old name |
| 8 | `Bareilly Arthritis Centre` | `Dr. Manoj Agarwal Clinic` | Branding rule |
| 9 | `over 29 years` | `over 30 years` | Standardise experience |
| 10 | `29 years` | `30+ years` | Standardise (run after #9) |

**Notes**
- Run the pairs **top to bottom** (do #9 before #10 so "over 29 years" isn't half-changed).
- If a "Best…" phrase count comes back higher than expected in the dry run, it may be catching image **alt text** or **SEO titles** too — that's fine, those should change as well.
- Case-sensitive: if any appear lowercase (e.g. "best orthopedic…"), add a lowercase pair.

## B. SEO titles & meta (if not caught by A)
Some title tags/meta descriptions live in **Rank Math/Yoast** custom fields with their own keys. If the dry-run in A didn't show them changing:
- Rank Math → Titles & Meta (and the per-page SEO boxes) → replace any remaining "Best…" in title templates and key pages by hand (few minutes).
- While there: set the homepage/title brand suffix consistently to "Dr. Manoj Agarwal Clinic".

## C. After the bulk swaps (do every time)
1. Elementor → Tools → **Regenerate CSS & Data**.
2. Clear any caching plugin + host cache.
3. Spot-check the homepage and /about-us/ visually.
4. In Search Console, request re-indexing of the edited key pages.

## D. Manual pass — structural (not find-replace)
1. **De-duplicate homepage blocks** — the "30+ years of trusted orthopedic care" paragraph appears ~3×, the app-download section 2×, some headings 2×. In Elementor, delete the duplicate sections.
2. **/about-us/** — remove the leftover contradictory paragraph (the one still pairing the clinic with "Bareilly Orthopaedic Centre" before swap #7 fixes the name), so the page reads once, cleanly: "his own **Dr. Manoj Agarwal Clinic** and Dhanwantari Tomar Hospital."
3. **Schema** — Rank Math → Titles & Meta → set **LocalBusiness / Medical (Physician)** schema for the site + **FAQ** schema on pages with Q&A. (Toggle-level, no code.)
4. **Speed** — install a caching plugin + image optimiser; run PageSpeed Insights; action the top items.

## E. Verify (closes the loop with the monitor)
- After edits, run the Apps Script monitor's `runMonitor()` once. It should pass with **no "SHOULD-NOT-BE-PRESENT" hits** — confirming "Bareilly Orthopaedic Centre"/"Bareilly Arthritis Centre" are gone site-wide. The monitor will keep guarding this going forward.

---

### If you'd rather use Claude-in-Chrome for the clicking
It can drive the WP admin to install Better Search Replace and run the pairs, but the plugin UI is simple enough that manual is usually faster and safer than browser automation here. If you do use it, apply your known caveats (navigate first, then execute JS in a separate step; synchronous XMLHttpRequest; return boolean flags). The **swap table above is the source of truth** either way.

*Step 5 sheet v1 — 16 Aug 2026. Backup first; dry-run first; regenerate CSS after.*
