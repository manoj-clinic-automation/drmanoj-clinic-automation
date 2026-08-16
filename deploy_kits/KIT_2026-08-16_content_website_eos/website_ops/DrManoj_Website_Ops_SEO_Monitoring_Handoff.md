# drmanojagarwal.com — Website Operations, SEO & Monitoring Handoff

**Primary site:** drmanojagarwal.com (WordPress on Hostinger VPS; restored from Drive backup)
**Canonical:** https://drmanojagarwal.com (non-www) · **Canonical clinic name:** "Dr. Manoj Agarwal Clinic"
**Analytics stack:** Search Console + GA4 (property 540951406, measurement ID G-XV7PPY194Q) + Google Business Profile — all linked
**Tag Manager:** GTM-PQG6VNXZ (old .in container — loads but inert; reserved for Google Ads conversion tags) · GTM-P9HNQ3NH (.com container — never installed; to be deleted)
**Domains in the estate:** drmanojagarwal.com (canonical) · dr-manoj.in (GoDaddy 301 short links) · nkpathology.com (co-located lab)
**Vendor access:** scoped — dedicated FTP + WordPress login only
**Companion docs:** *Patient Education Content System — Master Vision v2* · *NK Pathology Website Handoff*

> **How to use this in the Project.** This is the operations + SEO + monitoring base for the primary website. Part A consolidates the existing planned website/SEO backlog. Part B is a new development spec for an automated website (digital-estate) monitoring system. Part C sequences everything. It is self-contained and complements the content and NK docs.

---

## PART A — Website Planned Work (SEO & Infrastructure Backlog)

### A0. Current state & context
- Site is **live** on Hostinger VPS, restored from a Drive backup.
- GSC + GA4 + GMB are linked; GMB is the **priority acquisition channel** per overall strategy (Found > website > social > retention).
- The **old .in domain expired** (JustDial blocked renewal) — a burned lesson that directly motivates the monitoring system in Part B.
- Two GTM containers exist; only one is needed. Vendor has scoped FTP + WP access only.

### A1. Analytics & Tag Hygiene *(foundation — do first)*
1. **GA4 internal-traffic filter** — define internal IP list (clinic, home) and activate the filter so staff/self visits don't pollute data. *(Prerequisite before any Google Ads spend.)*
2. **Referral exclusions** — exclude unwanted/self referrals in GA4.
3. **GTM rationalisation** — **delete GTM-P9HNQ3NH** (never installed); **verify GTM-PQG6VNXZ is actually firing on the .com site** and designate it the single container for Google Ads conversion tags. End state: exactly one correct, verified container.
4. **Verify linkage** — GA4 ↔ GSC ↔ (future) Google Ads; define key events/conversions (appointment click, call click, WhatsApp click, form submit).

### A2. SEO Audit & Core Fixes *(the "core audit" prerequisite referenced across the content plan)*
- **Technical:** crawl + GSC coverage review; XML sitemap; robots.txt; canonical (enforce non-www); site speed / Core Web Vitals; mobile usability; broken links & redirects; HTTPS integrity.
- **Structured data:** LocalBusiness / Physician schema; FAQ schema on content pages.
- **On-page hygiene:** title tags, meta descriptions, heading structure, image alt text.
- **NAP consistency:** name/address/phone identical across site, GMB, citations; canonical clinic name "Dr. Manoj Agarwal Clinic"; branding rules honoured ("Advanced Orthopaedic Surgery Centre" = logo graphic only; "Bareilly Orthopaedic Centre" removed; Dhanwantari Tomar Hospital kept as hospital name).
- **Local SEO:** GMB optimisation (primary channel), local citations.
- **Deliverable:** a baseline audit report + prioritised fix list (quick wins vs strategic).

### A3. City Landing Pages
- **Status:** Pilibhit (live & indexed) · Budaun (built — publish/verify indexing) · **Shahjahanpur, Rampur, Moradabad (pending build)**.
- **Template rule:** a **bold location-clarity statement in the hero, body, and FAQ** on every city page.
- **Quality guard:** real, substantive, NMC-safe content per page — avoid thin "doorway" pages (which harm SEO); each must genuinely serve that city's readers.

### A4. Google Ads Readiness *(gated — prerequisites first)*
- **Do not spend until:** GA4 internal filter + referral exclusions live (A1) **and** conversion tracking configured via the single GTM container.
- Then: campaign setup; budget guideline ~**3% of net annual professional income, weighted digital**.

### A5. Content System Integration
- The blog clusters (*Content Master Vision v2*) publish on this site; **language selector (TranslatePress) rolls out *after* the A2 audit fixes**, top pages first.
- NK Pathology funnel cross-links activate with content Phase 2.

### A6. Vendor Coordination
- Vendor scope: FTP + WordPress edits within their remit.
- In-house / assisted: GA4/GTM config, GSC, content, monitoring, Apps Script.
- Define clearly who executes each item to avoid overlap.

---

## PART B — Automated Website Monitoring System *(new development)*

### B0. Why — and the burned lesson
The **.in domain was lost to expiry**. That must never recur for any asset. Beyond domains, a patient-facing medical site that silently goes down, shows an expired-certificate warning, gets defaced, or drops out of Google is a direct loss of patient trust and reach — and a solo doctor won't notice manually in time. This system watches the whole **digital estate** automatically and alerts early.

### B1. Scope (digital estate)
- **Primary:** drmanojagarwal.com
- **Short links:** dr-manoj.in (book/map/app/contact/save/web/appt redirects must resolve)
- **Lab:** nkpathology.com
- **Key VPS apps (secondary):** assets.dr-manoj.in, attendance dashboard, WABA endpoint — availability only

### B2. What to monitor (checklist)
1. **Uptime / availability** — HTTP status at intervals; alert on downtime
2. **SSL certificate expiry** — alert well before expiry (scary browser warnings destroy trust)
3. **Domain registration expiry** — all domains; the core lesson — alert 60/30/14 days out
4. **Performance** — response time / Core Web Vitals degradation
5. **Security** — malware / defacement / file-integrity change; Google Safe Browsing blacklist status
6. **Broken links / 404s** — grows in importance with many blog + city pages and heavy internal cross-linking
7. **Search / indexing health** — GSC coverage errors, manual actions, sudden indexing/traffic drops
8. **Content-assertion checks** — key pages still contain expected text and do **not** contain wrong text (would have caught the NK 24-hour-turnaround error; catches silent breakage)
9. **Backup verification** — confirm scheduled backups actually ran

### B3. Architecture *(tiered — aligned to standing principles: stability supreme, low-maintenance wins, off-the-shelf where reliable, Apps Script for custom, external where independence is required)*

**Tier 1 — External off-the-shelf (uptime · SSL · domain).**
- Use a reputable external monitor (e.g. **UptimeRobot free tier** to start; upgrade only if needed).
- **Must be external to the VPS** — a monitor hosted on the VPS cannot detect its own server going down. This is the one place where off-the-shelf + external beats self-built.
- Covers items 1, 2, 3 with near-zero maintenance.

**Tier 2 — Google Apps Script (custom · free · Google-native · fits the existing automation stack).**
- Standalone (not container-bound), time-driven triggers.
- Handles: **content-assertion checks** (item 8), **broken-link scan** (item 6), **GSC indexing pulls** (item 7), **domain-expiry cross-check** (item 3 backup), sitemap presence.
- **Alerts** to the hub Gmail (drmka.ortho@gmail.com); **optional WhatsApp** via the existing WABA / MyOperator.
- **Log** results to a Google Sheet or Notion for history.
- No PHI involved (public sites only) → cloud/Apps Script is safe here; secrets excluded from GitHub.

**Tier 3 — WordPress / VPS.**
- **Security plugin** (Wordfence-type) for malware scan, firewall, file-integrity/defacement, login hardening (item 5).
- **Backup verification** (item 9) and basic server-resource alerts.

### B4. Alerting model
- **Immediate (critical):** site down · SSL expiring ≤14 days · domain expiring ≤60 days · malware/defacement/blacklist · key content-assertion failure.
- **Digest (daily or weekly):** performance, broken links, indexing summary, backup confirmation.
- **Channels:** email (hub Gmail) + optional WhatsApp; consolidated to avoid alert fatigue.

### B5. Dashboard / log
- A simple **status log** (Google Sheet or Notion) with history; optional lightweight status page later. Consistent with existing local-hub / Notion-console patterns.

### B6. Build phases
- **M0 (MVP — protect the asset, fast, low effort):** Tier 1 external uptime + SSL + domain monitor · Tier 3 WordPress security plugin + backup verification. Covers the highest-risk items (down / cert / domain / hack) immediately.
- **M1:** Apps Script content-assertion + broken-link checks + email alerts.
- **M2:** GSC indexing integration + traffic-anomaly detection + WhatsApp alerts + digest + status log.
- **M3:** refinements; extend coverage across the full estate (short links, lab, VPS apps).

---

## PART C — Sequencing / Rollout (how A and B interleave)

**Guiding logic:** *protect and measure the foundation before building more on top of it.* Monitoring and analytics hygiene come first, then SEO fixes, then growth (content, city pages, Ads).

1. **Immediate (foundation):**
   - B: **M0 monitoring** (uptime + SSL + domain + security plugin) — protect the asset now
   - A1: **GA4 internal filter + referral exclusions + GTM rationalisation** — clean measurement
   - A2: **run the baseline SEO audit** → prioritised fix list
2. **Next:**
   - A2: execute core SEO fixes
   - A3: publish Budaun; build Shahjahanpur / Rampur / Moradabad
   - B: **M1 monitoring** (content-assertion + broken-link — valuable as pages multiply)
   - Content: **Phase 0 (Knee OA v3 prototype)** → Phase 1
3. **Then:**
   - B: **M2 monitoring** (GSC + anomaly + WhatsApp + digest)
   - A5: **language selector** (post-audit), top pages first
   - A4: **Google Ads readiness** → controlled spend
   - Content Phase 2+ and NK funnel cross-links
4. **Ongoing:** M3 estate-wide monitoring; sustainable content cadence; GMB review growth.

---

## PART D — Open Questions / Decisions

- VPS/hosting access details and **who executes each item** (vendor vs in-house vs Claude-assisted, esp. the Apps Script builds)
- Preferred uptime service (UptimeRobot free vs a paid tier) and any budget for paid monitoring
- WhatsApp alerting via the existing WABA — confirm number/feasibility for system alerts
- GTM: confirm GTM-PQG6VNXZ is live on .com before wiring Ads tags; confirm deletion of GTM-P9HNQ3NH
- Run the **baseline SEO audit now** as the first concrete action? (I can produce it.)
- Which content-assertion strings to watch on key pages (e.g. clinic name, timings, phone, canonical claims)

---

## Project Document Set (index)

1. **Patient Education Content System — Master Vision v2** (content architecture, blogs, Hindi/SEO, tools, facilities, phasing)
2. **NK Pathology Website Handoff** (lab revival + diagnostic funnel)
3. **drmanojagarwal.com — Website Operations, SEO & Monitoring Handoff** (this document)
   - *Background to attach:* prior NK business case + ERBA EM200 project; existing SEO/audit notes

---

*Handoff v1. Immediate next actions: M0 monitoring + GA4/GTM hygiene + baseline SEO audit — in parallel with content Phase 0.*
