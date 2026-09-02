# S220_CARD_PARKED_BILLS — the parked bills expand on Darpan's card (F-282b)

**The owner, 22:55:** *"bina pehchaan ke bill (7) — are they supposed to expand to the bill details?"* and
*"should include ID and mobile entered?"* Yes to both, within what the parked row holds.

The line becomes a tap, exactly like *CN bills*: **bill · naam (as typed) · ID (as typed; — when none was) ·
phone ke aakhri 4 · ₹** (a parked return shows negative). The parked row keeps only the phone's last four
digits, so that is what can be shown; the full number lives with the D355 lookup work, not here.

Proven: selftest 6/6 through the real card API on a copy of the live db (the bills list, rupees adding to the
parked total, no whole number leaves the API, an empty day lists none); Darpan's page rendered in Chromium with
the block open, 4/4, no JS errors. Two pins predicted.

| file | what |
|---|---|
| `patch_darpan_parked_bills_s220.py` | darpan_app.py — 2 anchors |
| `patch_darpan_card_parked_s220.py` | darpan_card.html — 1 anchor |
| `selftest_parked_bills_s220.py` | 6 checks |
