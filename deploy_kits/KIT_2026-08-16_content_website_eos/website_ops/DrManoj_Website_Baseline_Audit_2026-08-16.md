# drmanojagarwal.com — Baseline SEO & Site Audit
**Date:** 16 August 2026 · **Method:** live fetch of homepage + /about-us/ + search-result inspection · **Auditor note:** grounded in what was actually verified on the live site; items needing account access to confirm are marked *(verify)*.

> Feeds Part A2 of the *Website Operations, SEO & Monitoring Handoff*. Pair the fixes here with the Setup Runbook (execution steps) and the Apps Script monitor (ongoing guard).

---

## 1. Verified — working well (leave alone)
- **Platform:** WordPress + Elementor 4.1.2; site is **live and indexed** (homepage, /about-us/, /blogs/, and a full set of /services/ pages are crawled).
- **Search Console:** verified (site-verification meta present).
- **Tag Manager:** exactly **one** container fires — **GTM-PQG6VNXZ**. This confirms the plan: **keep GTM-PQG6VNXZ** (use it for Ads conversion tags) and **delete the never-installed GTM-P9HNQ3NH**.
- **Canonicals:** correct — self-referencing, non-www .com.
- **The .in domain:** **drmanojagarwal.in redirects to drmanojagarwal.com with the correct canonical.** This is the intended retirement, working correctly — no problem. (Decision below on holding vs lapsing the .in.)
- **Mobile:** viewport set.
- **Existing architecture is strong:** a full service-page tree already exists (fracture, sports injuries, arthritis, spondylitis, gout, tennis elbow, frozen shoulder, joint/knee/hip/shoulder replacement, rotator cuff, limb lengthening, ACL, arthroscopic knee, **paediatric orthopaedic**, slip disc, spine).
- **Facilities already surfaced on the homepage:** Fuji digital DR X-ray, full-time MD pathologist, advanced physiotherapy, osteoporosis management, equipped OT, patient app, digital clinic — validating the facilities-awareness direction.
- **Ayushman/PM-JAY + cashless** prominent; **Docterz app** (Android/iOS) + **short-links** (map.dr-manoj.in, booking) live; WhatsApp 9358008080; Google reviews via Trustindex.

## 2. Priority findings & fixes

### P1 — Compliance & correctness (do first)
1. **"Best" superlative language is site-wide** — title tags, H1/H2, OG and meta descriptions repeatedly say "Best Orthopedic Surgeon/Specialist in Bareilly" ("Our Specialities as Best Orthopedic Surgeon," etc.). **NMC concern.** Replace with defensible framing: "experienced / senior / trusted orthopedic surgeon," "30+ years," "advanced joint care." Site-wide edit (titles, metas, headings).
2. **"Bareilly Orthopaedic Centre" still present on /about-us/** (your branding rule = remove entirely), **and the page contradicts itself** — one paragraph says "his own Clinic and Dhanwantari Tomar Hospital," another says "Dhanwantari Tomar Hospital and Bareilly Orthopaedic Centre." Standardise to **"Dr. Manoj Agarwal Clinic"**; keep **Dhanwantari Tomar Hospital**; remove "Bareilly Orthopaedic Centre." (The /about-us/ paragraph is also duplicated — deduplicate.)
3. **Experience number is inconsistent** — homepage says "30+ years," /about-us/ says "over 29 years." Standardise to **"30+ years / three decades"** everywhere.

### P2 — Quality & local SEO
4. **Content duplication (Elementor):** the homepage repeats blocks verbatim (the "30+ years of trusted orthopedic care" paragraph ~3×, the app-download section 2×, several headings 2×). Clean up — it hurts quality signals and readability.
5. **NAP inconsistency across directories** (a real local-SEO drag). Observed: experience listed as 20 / 25 / 29 / 30 / 31 / 35 years across sites; clinic named "Bareilly Orthopaedic Centre" (Drlogy, fee ₹200) and "Bareilly Arthritis Centre" (Practo, DocIndia); one listing (cardiologistindia) has the **wrong specialty ("Cardiologist") and a doubled "Dr. Dr." name.** Correct the major citations to the canonical NAP (table below).
6. **Blog section is thin** — /blogs/ exists but sparse; the content system (Master Vision v2) fills it. Enforce the service-vs-blog split (§3).

### P3 — Technical *(verify — needs tool/account access)*
7. **Schema markup** *(verify)* — JSON-LD isn't visible in the fetched HTML (extraction strips it), so presence is unconfirmed. Verify **LocalBusiness/Physician + FAQ** schema; implement via Rank Math/Yoast if absent.
8. **Core Web Vitals / speed** *(verify)* — heavy Elementor build; run PageSpeed Insights and optimise (image sizes, caching) as needed.
9. **GSC coverage** *(verify — needs GSC login)* — confirm sitemap submitted, no coverage errors, no manual actions.
10. **GA4 hygiene** *(needs GA4 login — Runbook)* — internal-traffic filter + referral exclusions not yet done.
11. **GTM cleanup** *(needs GTM login — Runbook)* — delete GTM-P9HNQ3NH.

## 3. Service-page vs Blog intent (critical for the content system)
Many planned blog topics **already exist as commercial service pages** (gout, frozen shoulder, sports injuries, spondylitis, arthritis, paediatric, spine/slip-disc, ACL, replacements). To avoid the two competing in search:
- **Service pages = transactional intent** ("gout treatment Bareilly," "knee replacement surgery").
- **Blog pages = informational intent** ("what is knee osteoarthritis," "OA vs inflammatory arthritis," "haldi for knee pain").
- Each **blog cross-links down to its matching service page** (blog educates → service converts); assign each a **distinct primary keyword**; never point two pages at the same query.
- Note: a **paediatric-orthopaedic service page already exists** — so paediatric *educational* content (Pillar 3) is on-brand and supported by existing site structure.

## 4. Canonical NAP (enforce everywhere — site + directories + GMB)
| Field | Canonical value |
|---|---|
| Name | Dr. Manoj Agarwal |
| Clinic | **Dr. Manoj Agarwal Clinic** |
| Address | G-15, Near Vikas Bhawan, Behind Anand Ashram, Rampur Garden, Bareilly, Uttar Pradesh 243001 |
| Phone | +91-9358008080 |
| Experience | 30+ years |
| Qualifications | MBBS — King George's Medical College, Lucknow (1990); MS Orthopaedics — GSVM Medical College, Kanpur (1995) |
| Hospital (keep) | Dhanwantari Tomar Hospital |
| **Remove everywhere** | "Bareilly Orthopaedic Centre", "Bareilly Arthritis Centre" |

## 5. The .in retirement — one decision
The redirect is correct. Decision to make: **hold the drmanojagarwal.in domain defensively** (keep renewing + 301 to .com for ≥6–12 months, ideally long-term — it's cheap brand protection and preserves link equity) **vs let it lapse.** Given the earlier loss of a domain to expiry, holding it is the safer default; the monitor (below) will alert if the redirect ever breaks.

## 6. What I did vs what needs your login
- **Done here (live):** platform, indexing, GTM, canonical, .in status, on-page NAP/branding/superlative/duplication findings, service-vs-blog analysis.
- **Needs your account (Runbook covers step-by-step):** GA4 internal filter + referral exclusions; delete GTM-P9HNQ3NH; GSC coverage check; schema + CWV verification; the content/branding edits in WordPress (vendor or in-house).

---
*Baseline audit v1 — 16 Aug 2026. Next: apply P1 edits, then P2; deploy the monitor; work the Runbook.*
