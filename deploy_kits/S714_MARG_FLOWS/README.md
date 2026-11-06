# S714_MARG_FLOWS — S388 (Sanjeevni), 06-Nov-2026 · D827, D830

**Why.** The owner (05-Nov, D827): one phone-first flow per recurring Marg report, the field to change ringed, Roman Hindi, collected in one
place, **each flow shareable on its own with anyone at any time** (Ram Singh, any staff, himself); D830: Shivani's Marg reports in her own app
login, with the server's confirmation. His "Go" 08:44 IST 06-Nov.

**What he sees.**
- `https://followup.dr-manoj.in/finance/flows` — every flow, one link each; **opens on any phone without a login**; kept out of search engines.
- `https://followup.dr-manoj.in/finance/flows/<flow>` — one page per report (valuation, batch, salt, items, purchase-bill, purchase-item,
  order-sheet, category, sale, stock): the rules, the ring legend, the steps with Marg's own screens, **WhatsApp par bhejiye** (the page's
  own address only). The two morning reports use the in-app guide's own steps (S500).
- Inside the app: *Aaj ki reports* (the tile the owner, Amir, Shavez and Shivani already hold) carries **Marg reports: har report ke steps**
  → `/finance/reports/flows`: every flow with its page, its WhatsApp share, and **the server's word on its last report** (received / refused,
  with the time). The owner's view in English.

| file | from | to | what |
|---|---|---|---|
| `/root/finance/finance_app.py` (**the parent's** — PLANNED line, board v940) | 00cc4935 | TO_PINS | one line in `_gate`: GET/HEAD of the three flow pages (matched by their endpoints, not by path) pass without a login |
| `/root/finance/reports_tile.py` | 0598072c | TO_PINS | the four routes; the card on *Aaj ki reports* |
| `/root/finance/marg_flows.py` | NEW | TO_PINS | the flows (the S384 steps, D827 settings), the pages, the share link, the picture lookup (only pictures a step shows) |
| `/root/finance/marg_flows_pics.py` | NEW | TO_PINS | 56 pictures as hex text (the number gate reads hex as hex) |

**F-185.** Every picture was read for numbers and Marg's title-bar line before it went public: Marg's `USER / BUSID / WALLET / MAIN COMPUTER`
line blanked in b1, c1, i1, p1, s1, v1, the "Payment Successful — Paid Amount" card in b1, c1, i1, o1, p1, s1, v1, and the twelve supplier firm names in i5 (the cold review); read again clean (an
independent reader, every picture, twice); the guide's 13 pictures read clean, its stock-result picture is not served publicly. A public
page reads no database, carries no name and no figure.

**Not done, and why (one line each):** no new portal tile — the four people named already hold *Aaj ki reports*, which now carries the
list (no parent portal file touched); **who made a report is not named** — the medical PC's file carries the Windows account, not the Marg
login, so the server cannot tell the person; the S702 messages already tell the owner when each report arrives.

**Proofs.** walk S714 16 ok on the real finance_app (its own gate) with a made-up database; control on the live files 4 ok, 12 red. Chromium
(`js_s714.py`): three flows at 390×844 and 1366×768 — no sideways scroll, every picture loads, the WhatsApp button near the top. Installer
rehearsed on a made-up server tree.

**Install (one server line, after the publish):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s714kit && cp -rp /root/deploy/repo/deploy_kits/S714_MARG_FLOWS /tmp/s714kit && bash /tmp/s714kit/install_S714_MARG_FLOWS.sh
