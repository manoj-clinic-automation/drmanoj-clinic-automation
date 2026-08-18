# Dr. Manoj Agarwal — MyOperator IVR + WhatsApp API Project
**Platform:** MyOperator (IVR + WhatsApp Business API)
**Context extracted from:** Digital infrastructure planning session, May 2026

---

## 1. CLINIC COMMUNICATION PROFILE

| Field | Detail |
|---|---|
| Clinic | Dr Manoj Agarwal Clinic, Bareilly |
| Doctor | Dr. Manoj Agarwal — Bone, Joint & Spine Specialist |
| Primary phone / WhatsApp | +91-9358008080 |
| Helpline | +91-8065293652 |
| Consultation hours | Mon–Sat: 10AM–2PM · 6:30–8:30PM · Sunday: Emergency only |
| **Primary comms channel** | **WhatsApp — dominates all patient communication** |
| Email | Not a priority — WhatsApp handles everything |
| Language | Hinglish primary / Hindi / English |
| Patient base | Bareilly + surrounding UP districts |

---

## 2. WHATSAPP — CURRENT ROLE IN PRACTICE

Confirmed in planning session:
- Appointments booked via WhatsApp
- Follow-ups via WhatsApp
- Reports shared via WhatsApp
- Referrals via WhatsApp
- Family members communicate on behalf of patients
- **Email has been explicitly deprioritised** — WhatsApp is the single communication backbone

---

## 3. GMB REVIEWS — CURRENT PROCESS

- Reviews post only to Google My Business (GMB)
- **Personally requested by Dr. Manoj — only during physical in-clinic encounters**
- This is a deliberate practice, not a gap — authenticity of personal ask is the point
- Majority of patients need assistance framing the review in language
- A GMB Review Assist tool has been built (HTML, offline) to solve this exactly
- Tool generates Hinglish / Hindi / English drafts from tick-box selections
- Patient reads, edits personally, posts from their own phone
- **WhatsApp share button** lets patient send the draft to themselves for posting
- **No automation of review requests — by design**

---

## 4. GMB REVIEW ASSIST TOOL — ROLE CLARITY

The tool (`GMB_Review_Assist_DrManojAgarwal.html`) generates 3 review versions (Short / Medium / Long).

**Workflow:**
1. Dr. Manoj personally identifies a satisfied patient during consultation
2. Makes personal request face-to-face
3. Staff opens the review tool, ticks relevant clinical details
4. Tool generates a natural draft in patient's preferred language (Hinglish / Hindi / English)
5. Patient edits / personalises — posts from their own phone
6. WhatsApp share button sends the draft to patient's own WhatsApp for easy access

**Not a MyOperator integration point** — review solicitation is intentionally personal and manual. WhatsApp API should not touch this workflow.

---

## 5. PATIENT COMMUNICATION LANGUAGE

From extensive work on the review tool:

- **Hinglish is the dominant natural language** for patient communication
- Short sentences, conversational, not formal
- First-person personal: "Mere/Meri/Mujhe" openers
- Natural UP/North India phrasing preferred
- Avoid literary Hindi ("गतिशीलता" → "चलना-फिरना")
- WhatsApp message templates should follow the same tone

---

## 6. DIGITAL TOUCHPOINTS RELEVANT TO MYOPERATOR

| Touchpoint | Detail |
|---|---|
| Primary phone / IVR | +91-9358008080 |
| Helpline | +91-8065293652 |
| WhatsApp (WABA) | +91-9358008080 |
| Website | drmanojagarwal.in |
| GMB listing | Active, under drmka.ortho@gmail.com |
| Instagram | ortho.dr.manoj |
| Facebook | ortho.dr.manoj |
| Google Maps short URL | map.dr-manoj.in (already live) |
| vCard short URL | dr-manoj.in/vc (planned) |
| Other short URLs | dr-manoj.in/fb, /ig (planned) |
| Google Tag Manager | GTM-PQG6VNXZ (active on website) |
| GA4 | Property p513765081 |

---

## 7. KNOWN PATIENT JOURNEY (current, pre-optimisation)

```
Patient hears of Dr. Manoj
        ↓
Calls +91-9358008080 OR WhatsApp message
        ↓
Appointment booked (WhatsApp / phone)
        ↓
Visit clinic (Rampur Garden, Bareilly)
        ↓
Consultation
        ↓
Follow-up via WhatsApp
        ↓
GMB review ← personal in-clinic request by Dr. Manoj (deliberate — not a gap)
        ↓
Language assistance via Review Assist tool (for patients who need framing help)
```

---

## 8. OPTIMISATION OPPORTUNITIES (for MyOperator project scope)

1. **vCard distribution via WhatsApp** — send digital vCard to new patients on first contact
2. **IVR call tracking** — identify which channel (GMB, Instagram, website, referral) drives inbound calls
3. **Appointment confirmation via WhatsApp** — reduce no-shows with day-before reminder
4. **Post-visit care instructions** — condition-specific WhatsApp messages (exercises, precautions)
5. **Report / prescription follow-up** — structured WhatsApp flow for test result queries

**Explicitly excluded from MyOperator scope:**
- Review requests — personally solicited by Dr. Manoj only, face-to-face, never automated

---

*Extracted from Dr. Manoj Digital Infrastructure planning session. Cross-reference with full project context document for hosting/website decisions.*
