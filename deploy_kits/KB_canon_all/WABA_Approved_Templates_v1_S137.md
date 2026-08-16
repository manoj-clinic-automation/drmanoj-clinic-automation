# WABA Approved Templates — Dr. Manoj Agarwal Clinic
**v1 · Session 137 · pulled LIVE from the MyOperator panel on 11 Jul 2026 (14 of 14 templates)**
**Supersedes** `Final_WABA_Utility_Templates_Branded_Links.docx` (pre-rename names — historical only).

> **The one rule that matters when sending:** the five `drmanoj_*` templates use **NUMERIC**
> placeholders — send `body:{"1":"…","2":"…"}`. The other seven use **NAMED** placeholders —
> send the exact key shown (`var_1`, `date`, etc.). Mixing them up = failed send.

---

## GROUP 1 — The follow-up ladder (numeric placeholders: "1", "2", "3")

### 1. `drmanoj_post_visit` — same-day after visit *(D213: the seen-today message)*
**Variables:** {{1}} = patient name
**Buttons:** Book Appointment (book.dr-manoj.in) · Call Clinic (+919358008080)

> Namaskar {{1}} ji,
> Dr. Manoj Agarwal Clinic (Orthopedics & Joints) mein aaj aapki visit complete hui.
> शीघ्र स्वास्थ्य लाभ की शुभकामनाएँ। 🙏
>
> Prescription & Reports / पर्चा और रिपोर्ट के लिए Docterz app par registered mobile se login karein.
> दवाइयाँ, निर्देश ( Instructions ) और Follow-up / अगला फॉलो-अप Date आपके पर्चे पर है
>
> Android: app.dr-manoj.in
> iPhone / आईफोन: ios.dr-manoj.in
> Save Contact / संपर्क सेव करें: save.dr-manoj.in
>
> Consultation Timings / परामर्श समय:
> Mon–Sat: 10:00 AM–1:30 PM │ 6:30 PM–8:30 PM
> Sunday: Emergency only
> Helpline / हेल्पलाइन: 8065293652 │ WhatsApp: 9358008080

*Footer: Dr. Manoj Agarwal Clinic │ STOP reply karein opt-out ke liye*

### 2. `drmanoj_followup_tomorrow` — due tomorrow
**Variables:** {{1}} = name · {{2}} = date
**Buttons:** Book Appointment · Call Clinic

> Namaskar {{1}} ji,
> Dr. Manoj Agarwal Clinic ki taraf se yaad dilana chahte hain — aapka follow-up kal scheduled hai.
>
> Follow-up Date / फॉलो-अप तिथि: {{2}}
>
> Samay par follow-up aapke शीघ्र स्वास्थ्य लाभ ke liye zaroori hai. Ane se pehle call karke apna time confirm karein.
>
> Consultation Timings / परामर्श समय:
> Mon–Sat: 10:00 AM–1:30 PM │ 6:30 PM–8:30 PM
> Sunday: Emergency only
> Helpline / हेल्पलाइन: 8065293652 │ WhatsApp: 9358008080
> Location / पता: map.dr-manoj.in

*Footer: Dr. Manoj Agarwal Clinic │ STOP reply karein opt-out ke liye*

### 3. `drmanoj_followup_due` — due today / grace 0–3 days *(D216: the 3rd-strike message)*
**Variables:** {{1}} = name · {{2}} = date
**Buttons:** Book Appointment · Call Clinic

> Namaskar {{1}} ji,
> Dr. Manoj Agarwal Clinic ki taraf se:
> Aapka follow-up {{2}} ko tha jo abhi tak nahi hua. 📋
>
> Samay par follow-up treatment ki safalta ke liye zaroori hai. Kripya jald clinic aayen ya appointment book karein. Ane se pehle call karein aur apna time confirm karein.
>
> Consultation Timings / परामर्श समय:
> Mon–Sat: 10:00 AM–1:30 PM │ 6:30 PM–8:30 PM
> Sunday: Emergency only
> Helpline / हेल्पलाइन: 8065293652 │ WhatsApp: 9358008080
> Location / पता: map.dr-manoj.in

*Footer: Dr. Manoj Agarwal Clinic │ STOP reply karein opt-out ke liye*

### 4. `drmanoj_followup_missed` — missed 4–10 days
**Variables:** {{1}} = name · {{2}} = date
**Buttons:** Book Appointment · Call Clinic

> Namaskar {{1}} ji,
> Aapke treatment plan mein {{2}} ko ek follow-up scheduled tha. 📋
>
> Aapki sehat ki chinta hai. Bina follow-up ke treatment ka poora faida nahi milta. Kripya jald clinic aayen ya sampark karein. Agar better hain — ek baar zaroor batayein.
>
> Consultation Timings / परामर्श समय:
> Mon–Sat: 10:00 AM–1:30 PM │ 6:30 PM–8:30 PM
> Sunday: Emergency only
> Helpline / हेल्पलाइन: 8065293652 │ WhatsApp: 9358008080
> Location / पता: map.dr-manoj.in

*Footer: Dr. Manoj Agarwal Clinic │ STOP reply karein opt-out ke liye*

### 5. `drmanoj_followup_dropout` — dropout, more than 10 days
**Variables:** {{1}} = name · {{2}} = date · {{3}} = days overdue
**Buttons:** Book Appointment · Call Clinic

> Namaskar {{1}} ji,
> Aapke treatment plan mein {{2}} ko ek follow-up scheduled tha — ab {{3}} din ho chuke hain, aur follow-up abhi tak nahi hua. 📋
>
> Aapki sehat ki bahut chinta hai. Orthopedic conditions mein regular follow-up zaroori hota hai. Agar bilkul theek hain — ek baar zaroor batayein. Agar koi takleef hai — kripya turant clinic aayen ya call karein.
>
> Consultation Timings / परामर्श समय:
> Mon–Sat: 10:00 AM–1:30 PM │ 6:30 PM–8:30 PM
> Sunday: Emergency only
> Helpline / हेल्पलाइन: 8065293652 │ WhatsApp: 9358008080
> Location / पता: map.dr-manoj.in

*Footer: Dr. Manoj Agarwal Clinic │ STOP reply karein opt-out ke liye*

---

## GROUP 2 — Panel-native call automations (no variables; fired by MyOperator itself)

### 6. `new_post_call_message` — after-call registration message (LIVE, panel automation)
**Buttons:** Book Appointment (www.dr-manoj.in) · View on Maps · Call Clinic

> Namaskar! धन्यवाद — आपका नंबर Dr. Manoj Agarwal Clinic (Orthopedics & Joints) mein register ho gaya hai, appointment aur service updates ke liye.
> Clinic Address / क्लिनिक पता: G-15, Rampur Bagh, "Anand Ashram ke barabar wali gali, nikat Vikas Bhawan, Bareilly"
> Consultation Timings / परामर्श समय: Mon–Sat: 10:00 AM–1:30 PM | 6:30 PM–8:30 PM
> Sunday: Emergency only
> Website: web.dr-manoj.in
> Clinic Details / विवरण: contact.dr-manoj.in
> Helpline / हेल्पलाइन: 8065293652 | WhatsApp: 9358008080
> Save Contact / संपर्क सेव करें: save.dr-manoj.in

*Footer: Agar yeh registration aapne nahin kiya hai, to STOP reply ka*

### 7. `eng_missedaftercall` — missed-call apology, language tag **en** (LIVE, panel automation)
### 8. `missedaftercall` — missed-call apology, language tag **hi** — SAME BODY as #7
**Buttons (both):** View On Maps · Call Clinic

> Namaskar! हमें खेद है कि व्यस्तता के कारण आपका फोन नहीं उठा पाए। हम जल्द ही आपसे संपर्क करेंगे।
> Clinic Address / क्लिनिक पता: G-15, Rampur Bagh, "Anand Ashram ke barabar wali gali, nikat Vikas Bhawan, Bareilly"
> Consultation Timings / परामर्श समय: Mon–Sat: 10:00 AM–1:30 PM | 6:30 PM–8:30 PM
> Sunday: Emergency only
> Website: web.dr-manoj.in
> Clinic Details / विवरण: contact.dr-manoj.in
> Helpline / हेल्पलाइन: 8065293652 | WhatsApp: 9358008080
> Save Contact / संपर्क सेव करें: save.dr-manoj.in

*Footer: Dr. Manoj Agarwal Clinic | STOP reply karein opt-out*
**Note:** these two are duplicates (en/hi tags). Which one the panel automation actually fires — worth confirming with Khushi/Lokesh someday; no urgency.

---

## GROUP 3 — Appointment set (NAMED placeholders: var_1, var_2)

### 9. `appointment_confirmation_ortho` — booking confirmed
**Variables:** var_1 = name · var_2 = date & time · no buttons

> *Hi {{var_1}}, your appointment with Dr. Manoj Agarwal is successfully booked* 😊
>
> 🗓️ Date & Time: {{var_2}}
> 📍 Location: G-15, Near Vikas Bhawan, Behind Anand Ashram, Rampur Garden, Bareilly
>
> 📝 Please carry:
> • Previous X-rays / MRI / reports (if available)
>
> ⏱️ Kindly arrive 15 minutes early.
>
> We look forward to helping you feel better 🦴

*Footer: Team Dr. Manoj Agarwal | Bareilly*

### 10. `appointment_reminder_1day_ortho` — appointment tomorrow
**Variables:** var_1 = name · var_2 = date & time · no buttons

> Hi {{var_1}}, gentle reminder 😊
> *Your appointment with Dr. Manoj Agarwal is scheduled for tomorrow.*
>
> 🗓️ Date & Time- {{var_2}}
> 📍 G-15, Near Vikas Bhawan, Behind Anand Ashram, Rampur Garden, Bareilly
>
> 📝 Carry previous medical reports if any.
> ⏱️ Please arrive 15 minutes early.
>
> See you soon!

*Footer: Team Dr. Manoj Agarwal | Bareilly*

### 11. `reschedule_confirmation` — appointment moved (language: hi)
**Variables:** var_1 = name · var_2 = new date/time · no buttons

> नमस्ते {{var_1}},
>
> आपका अपॉइंटमेंट सफलतापूर्वक reschedule कर दिया गया है।
>
> 👉 नया समय: {{var_2}}
>
> Team Dr. Manoj Agarwal

### 12. `welcome_template` — enquiry acknowledgement (language: hi)
**Variables:** var_1 = name · **Button:** Call Clinic

> नमस्कार {{var_1}},
> डॉ. मनोज अग्रवाल से संपर्क करने के लिए धन्यवाद।
>
> यह संदेश आपकी हड्डी रोग संबंधी परामर्श की पूछताछ की पुष्टि के लिए है।
>
> हमारी टीम जल्द ही आपसे संपर्क करके परामर्श से संबंधित विवरण साझा करेगी।

*Footer: Team Dr. Manoj Agarwal*

### 13. `decline_acknowledgement_manoj` — opt-out / no-further-messages acknowledgement
**Variables:** var_1 = name · no buttons

> Hi {{var_1}},
> Thank you for informing us.
>
> We will not send further messages regarding this inquiry.

*Footer: Team Dr. Manoj Agarwal*

---

## GROUP 4 — Not clinic-related

### 14. `daily_account_summary` — vehicle/collections summary (looks like a demo or another business's template)
**Variables (named):** date · vehiclesummary · collectionsumma · totalamount · no buttons

> Your daily account summary for {{date}} is ready.
> Vehicle usage: {{vehiclesummary}}
> Collections summary: {{collectionsumma}}
> Total collection: {{totalamount}}
> This is an internal account update notification.

**Do not use.** If ever tidying the panel, this is the one to remove (Lokesh/panel item).

---

*Source: live `GET /chat/templates` pull, both pages, 11 Jul 2026 (Session 137). Raw JSON snapshots:*
*`templates_snapshot.json` + `templates_snapshot_p2.json` (going into project knowledge at the S137 swap).*
