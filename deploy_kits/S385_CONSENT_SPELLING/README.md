# S385_CONSENT_SPELLING — the Hindi name and address, corrected once, everywhere

**The owner, 24-Sep-2026:** he corrected the machine's Hindi spelling of a patient's name and address in one place of a
consent; the print showed the wrong spelling everywhere else.

**The fault (read from his archived consent):** the consent text is editable, but the name appears in several
paragraphs, and the header printed at the top of every page is built from the generated values, never from the edited
text. So an edit changed one place only — his saved consent carries the first name in two spellings.

**Now:** after **Generate consent**, a small **Hindi spelling** box lists the patient's name, the relative's name and the
address. Correct them there and press **Apply everywhere**: every place in the consent and the header on every page
change together, and the spelling is **remembered** (a small file beside the case ledger on the server), so the next
consent for that name or place is spelled right by itself. If a name is changed by hand in some places but not all,
**Print** asks first.

**Proof.** `walk_s385.py` 10/10 in headless Chromium (the owner's case shaped: a name and a place the machine spells
wrongly → corrected once → every place + the printed header → remembered → a fresh page spells it right → a one-place
hand-edit is caught); the live page is the negative control. `check_s385.py` repeats the server half on the VPS.
`casepack_page.html` d5d4a3e7 → 08807cdf · `casepack_portal.py` 760e8c36 → cbbd392d. Restarts clinic-portal.
