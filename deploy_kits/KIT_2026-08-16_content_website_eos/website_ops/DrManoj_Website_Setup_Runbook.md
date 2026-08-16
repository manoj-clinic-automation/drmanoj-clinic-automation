# drmanojagarwal.com — Setup Runbook (Foundation Actions)
**Purpose:** turnkey, click-level steps for the items that need *your* logins (I can't reach GA4, GTM, Hostinger, the registrar, UptimeRobot, or WordPress from here). Do these in order; each is independent and safe.
**Pair with:** the Baseline Audit (what to fix) + website_monitor.gs (the code for Step 4).

---

## STEP 1 — External uptime + SSL + domain monitoring (UptimeRobot) — *~20 min*
This is Tier 1 (must be external to the VPS). Free plan is enough to start.
1. Create a free account at uptimerobot.com.
2. **Add monitors** (type = HTTPS): `https://drmanojagarwal.com/`, `https://nkpathology.com/`, and one for a key short-link (e.g. `https://map.dr-manoj.in`).
3. For each drmanojagarwal.com / nkpathology.com monitor, **enable SSL certificate expiry monitoring** (UptimeRobot alerts ~30/14/7 days before expiry).
4. **Enable domain-expiry monitoring** for drmanojagarwal.com, nkpathology.com, dr-manoj.in, and — per the audit — **drmanojagarwal.in** (so the retired-but-held domain never silently lapses).
5. **Alert contacts:** add your email (drmka.ortho@gmail.com) and, if you want phone alerts, the mobile/WhatsApp option.
6. Set check interval to 5 min.
> Covers: uptime, SSL expiry, domain expiry — the three highest-risk items — with near-zero maintenance.

## STEP 2 — WordPress security + backup — *~20 min*
1. In WordPress admin → Plugins → Add New → install & activate a security plugin (**Wordfence** is the standard).
2. Run the initial **scan**; enable the **firewall** and **file-change/integrity** detection; turn on **login-attempt limiting**.
3. Confirm a **backup** solution is running (host-level Hostinger backups or an UpdraftPlus schedule) and that a restore point exists. Note where backups land.
> Covers: malware/defacement/file-integrity + backup verification (Tier 3).

## STEP 3 — GA4 hygiene — *~20 min* (analytics.google.com → your property, ID G-XV7PPY194Q)
1. **Internal traffic filter:** Admin → Data Streams → (web stream) → Configure tag settings → Show more → **Define internal traffic** → add rule with your clinic + home **IP addresses** (traffic_type = internal). Then Admin → **Data Settings → Data Filters** → set the "Internal Traffic" filter to **Active**.
2. **Unwanted/self referrals:** Admin → Data Streams → web stream → Configure tag settings → **List unwanted referrals** → add your own booking/payment domains (e.g. docterz.in) so they don't count as referrals.
3. **Key events (conversions):** mark appointment-click, call-click (tel:), WhatsApp-click, and contact-form submit as **key events** so Ads can later optimise to them.
> Prerequisite before any Google Ads spend.

## STEP 4 — GTM cleanup + deploy the monitor
**4a. GTM (tagmanager.google.com) — ~5 min:**
1. Confirm **GTM-PQG6VNXZ** is the live container (verified already — it fires on the site).
2. **Delete the unused GTM-P9HNQ3NH** container (it was never installed).
3. Later, add Google Ads conversion tags inside **GTM-PQG6VNXZ** when Ads is set up.

**4b. Deploy website_monitor.gs (Apps Script) — ~15 min:**
1. Create a **blank Google Sheet**; copy its ID from the URL (the long string between `/d/` and `/edit`).
2. Go to script.google.com → **New project** (standalone). Paste the contents of `website_monitor.gs`.
3. Set `LOG_SHEET_ID` to your sheet's ID; confirm `ALERT_EMAIL` = drmka.ortho@gmail.com.
4. Run **`setup`** once → authorize when prompted (it creates the log tab + does a first pass).
5. Triggers (clock icon) → **Add Trigger** → function `runMonitor`, time-driven, **every 30 minutes** (or hourly).
6. (Optional) run `scanLinks` manually now and then for a 404 sweep.
> Covers: uptime + content-assertions (incl. branding-rule guard) + redirect health + logging (Tier 2).

## STEP 5 — Content & branding fixes (WordPress — vendor or in-house) — from the Audit
Apply the audit's P1/P2 edits:
1. **Remove all "Best …" superlatives** (titles, metas, H1/H2) → "experienced / senior / trusted," "30+ years."
2. **/about-us/:** remove "Bareilly Orthopaedic Centre," fix the contradictory clinic naming → "Dr. Manoj Agarwal Clinic," delete the duplicated paragraph.
3. **Standardise experience to "30+ years"** across all pages.
4. **De-duplicate** the repeated homepage blocks (Elementor).
5. **Verify/implement schema** (LocalBusiness/Physician + FAQ) via Rank Math/Yoast.
6. Run **PageSpeed Insights**; action the top Core Web Vitals fixes.
> The monitor (Step 4) will then alert you if the removed branding strings ever creep back.

## STEP 6 — Off-site NAP cleanup (local SEO) — ongoing
Correct the major directory listings to the **canonical NAP** (see Audit §4): Practo, Lybrate, Drlogy, Eka, DocIndia, and the incorrect **cardiologistindia** listing (wrong specialty + "Dr. Dr."). Enforce "Dr. Manoj Agarwal Clinic," 30+ years, correct address/phone; remove old clinic names.

---

## Sequence & ownership
- **Today (fast, protects the asset):** Steps 1, 2, 4 (monitoring live).
- **This week:** Step 3 (GA4), Step 4a (GTM), begin Step 5 (P1 edits with vendor).
- **Ongoing:** Step 5 P2/P3, Step 6 NAP cleanup.
- **Who:** Steps 1–4 you/assisted; Step 5 vendor (scoped FTP+WP) or in-house; Step 6 you/staff.
- **Then:** Google Ads readiness (only after Step 3 done + conversion tags in GTM), language selector (post-audit), and content Phase 0 (Knee OA v3) in parallel.

*Runbook v1 — 16 Aug 2026. Companion: Baseline Audit + website_monitor.gs + Website Ops/SEO/Monitoring Handoff.*
