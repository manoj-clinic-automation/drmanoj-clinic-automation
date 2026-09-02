# S220_OWNER_ENGLISH — the owner's console speaks English

**Ruling (02-Sep):** the owner's consoles and pages are English; staff-facing pages stay Hindi.

A sub-agent read the live code. The hub page is 100% English. Three checker-only API responses were not:

| endpoint | what it said | done |
|---|---|---|
| `/finance/darpan/api/coverage` | five romanised-Hindi explanations in a field named `hindi`, **rendered on the owner's hub** (Marg coverage table) | **English** — *"filed, report in, applied"*, *"the day is filed, but there is no Marg report"* … field name kept, page untouched |
| `/finance/darpan/api/corrections` | *"Marg: bill X ka payment mode CASH se UPI kijiye"* — the owner reads it and relays it to Darpan | **English first, Hindi in brackets** for the relay |
| joiner `/api/reset_password` | *"<name> ka password reset ho gaya hai"* — the text the owner reads OUT to the staff member | **left as it is** — a message to staff, staff-facing by purpose (owner's own rule); recorded so nobody hunts for it again |

Proven: selftest 11/11 through the real blueprint on a copy of the db (40 coverage rows, none in Hindi;
every correction instruction English-first). One pin predicted. No page change, no table, no write.
