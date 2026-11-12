# S442 — WHATSAPP TEMPLATE FEATURES — what a template can carry, what we use, what to build next
*The parent, 13-Nov-2026. Asked by the owner at 04:30 IST: "there are many features in templates which we aren't using, such as headers and custom replies; we can explore a post-visit feedback system; find what uses of custom replies can be done, staying in utility templates." A study — no code, nothing changed. Sources at the end; what is not verified is marked.*

## 1 · What a template can carry (Meta's own page, read 13-Nov)
| part | what it is | limits |
|---|---|---|
| **Header** (optional, one) | a line of text, OR a picture, a video, a document (PDF), OR a map pin | text: 60 characters, 1 blank · the file or the pin is supplied at sending, so it can differ for every patient |
| **Body** (required) | the message | 1,024 characters, any number of blanks |
| **Footer** (optional) | one small grey line under the body | 60 characters, no blanks |
| **Buttons** (optional) | up to 10 in all | **Reply buttons** (the patient taps, a fixed word comes back to us): up to 10, 25 characters each · **Link button**: up to 2, the link may end in ONE blank (a different link per patient) · **Call button**: 1 · **Copy-code button**: 1 |
Three things about buttons that decide the design: more than 3 buttons → only 2 show and the rest hide behind "See all options"; reply buttons mixed with link/call buttons **do not show on WhatsApp on a computer** (phones only); reply buttons must sit together.
A tap on a reply button reaches us as an ordinary incoming message carrying the button's words — it would land in the Inbox like a typed reply.

## 2 · What our templates use today (the panel, read 13-Nov)
Body text only, with one to three blanks, and two buttons on each patient message: **Book Appointment** (a link) and **Call Clinic**. No header, no footer, no reply button. The timings, the helpline, the map link and "STOP reply karein" are all inside the body. Our sender fills the body's blanks only.

## 3 · Staying inside "Utility" — the line Meta draws
A utility message must be **non-promotional AND tied to the patient's own visit, appointment or account**. A feedback question is utility **only when it is about a specific visit** — "a general request for feedback will not be approved as utility". Anything that promotes, recommends, greets, or mixes the two is Marketing: a Google-review ask, health tips, festival wishes, a camp or an offer. A utility template that turns out to be marketing is moved to Marketing by Meta; repeated misuse brings a warning, then slower sending, then utility templates suspended for 7–30 days. So: every template names a visit or a date, and carries nothing else.

## 4 · What I suggest, in the order I would build
**A. Reply buttons on the follow-up reminders — the largest gain.** Today the message says "Agar better hain — ek baar zaroor batayein" and waits for a typed reply that older patients rarely send.
- *Follow-up is tomorrow:* **Aaunga** · **Date badalni hai**
- *Date passed (next morning, day 5, long overdue):* **Aaunga** · **Ab theek hoon** · **Call karein**
What each tap would do on our side: "Ab theek hoon" closes that follow-up on the Patients page (no more reminders for that date); "Date badalni hai" / "Call karein" makes a call-back line for reception; "Aaunga" is noted. This turns the reminders from one-way notices into the follow-up assessment you asked for on 11/12-Nov — who is better, who is lost, who needs a call — without staff phoning everyone. Three buttons, no link/call button on these (the helpline stays in the text), so they also show on a computer.

**B. A post-visit feedback question — the next morning, three taps.** A new utility template tied to the visit: "Kal [date] ki visit kaisi rahi?" → **Achha** · **Theek-thaak** · **Pareshani hui**.
- "Pareshani hui" → a line for you that same morning (name, visit), before it becomes a bad review.
- "Achha" → the patient's tap opens WhatsApp's 24-hour reply window, in which we may answer in our own words: a thank-you with the Google review link (the Review Assist page already drafts these). **The review ask must be in that reply, never in the template** — in the template it would make it Marketing.
- It is a seventh list on the messages page with its own switch, under the same rules (one message a number a day, the stop list, the ceiling).

**C. A "Stop messages" reply button** on every patient template, beside the typed STOP. One tap is easier than typing an English word. It uses one of the three button places, so it competes with A — on the reminders I would keep A's three and leave STOP as text; on the post-visit and feedback messages there is room.

**D. X-rays and reports as the message itself.** Since September these are on our server, not in Docterz. A template can carry a **document or a picture as its header** — "Aapki [date] ki report / X-ray" with the PDF or image attached. It would replace what the Docterz upload used to give the patient. **This one is yours to rule on**, not mine: it sends a medical file to whatever phone holds that number (families share numbers), and patient files have so far never left the server.

**E. Tidying with header and footer.** Clinic name as a text header; "STOP likhkar bhejein — messages band" as the footer. The body gets shorter and every message looks the same. Worth doing only when a template is being remade anyway (each change goes back to WhatsApp for approval).

**F. Later, larger:** a link button whose link differs per patient (a page for THAT patient — his next date, his reports; no such patient-facing page exists yet) · a map pin as the header of the new-patient message · WhatsApp's in-chat forms ("Flows": star rating plus a comment) for feedback, if MyOperator supports them.

## 5 · Not verified yet — my work before any of this is built, none of it yours
1. What MyOperator hands our receiver when a button is tapped (the words, the kind of message) and whether the STOP listener hears a tapped "Stop". One test template to your own phone settles it.
2. Whether MyOperator's sending door accepts a header file and a per-patient link (our sender sends body blanks only today).
3. The charge: a utility template is charged per message; as far as I know it is free when sent inside an open 24-hour window. The current India rate is not checked here.
4. Whether the panel lets an approved template be edited, or only copied (you copied — which suggests copy).

## 6 · What this does not change
The sending built tonight (kits S808, S809) goes ahead with the templates as they are (D946). Everything above is new templates — each needs your wording, WhatsApp's approval, and a small build of its own.

*Sources: Meta — Template components (developers.facebook.com/documentation/business-messaging/whatsapp/templates/components) · Meta — Template categorization (…/templates/template-categorization) · Meta — button messages webhook (…/webhooks/reference/messages/button) · the MyOperator panel's template list, read as the owner 13-Nov 04:33 IST.*
