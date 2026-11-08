# S403 — KIT 5 "ONE SOURCE, ONE LANGUAGE" (S749) — the plan of record — 08-Nov-2026

*The owner's rulings 05:13 – 05:56 IST 8-Nov (Sanjeevni chat, S403), on a live read of the five purchase pages, the code bundle of 08-Nov and the records. His "go" 05:56 IST. The mock first (his screens change). This paper supersedes nothing; it sits beside `S391_PURCHASE_RECONCILE_PLAN.md` (kits 1–4) and `S402_ORDER_LIST_PLAN.md`.*

## 1 · What the check found (08-Nov, 05:0x – 05:5x IST)

Kits 1–3 of the S391 plan are live (S726 pairing, S736 reception's list and the owner's second look, S738 Amir's corrections, S740 returns). The older payment machinery is live (the pay sheet S261/S264, the Marg cross-check and the lock S604, the advice/letter/file S265–S267, the cheque register S270, the bank SMS and the suppliers' WhatsApps S405/S407).

**Five pages say the same month five ways:**
- the step view `/finance/purchase/page/check` — the scan register's states (S726); no way in from the app (no tile, no link — reached only from the briefs);
- the register `/finance/purchase/page/scans` — the same states in the builder's words (*verified · has its scan · paired on bill number and date · D839 S740 seed*); the read-quality block; the legacy link;
- the audit page `/finance/purchase/page/month/<M>` (S224) — Correct/Wrong verdicts, its own Correct/Wrong buttons on the 4 flagged bills (a second place to decide), the pairing grade as its scan column (*exact · confirmed · auto · probable*), no month strip;
- the hub `/finance/purchase/page/hub` — all-time counts (*480 Marg bills with no scan · 20 scans with no Marg bill*, April–September included);
- the pay sheet `/finance/purchase/page/pay/<M>` — `_lock_gate` (S604) reads Marg's three reports and Marg-vs-Marg plus WRONG verdicts; it does not read the register (an unscanned bill, a scan with reception, a pending return hold nothing by themselves); Step 2 needs a tap;
- Amir's English summary `/finance/amir/day` — *Marg sudhar — not yet · corrections awaiting Marg: 0* while the step view has 3 corrections and 1 return on his list (S738/S740 never reached it).

**October's lock is held by a reading defect:** the 4 "no item lines" bills (Gunina GPPL2678591, GPPPL3679039; Kedar A000207_; Yuvika YS0706202627) have their 8 lines on the server as *undated* — Marg's item-wise export clips a long bill number (`L2678591`, `L3679039`, `A000207_TYRO BR`, `06202627ANKLE BINDER …`); the amounts equal the bills to the rupee (₹2,513 · ₹8,729 / 8,730 · ₹7,400 · ₹1,958).

**Dead end:** Kedar A000211 — *whose: You* (the owner's answer with Shavez, 22-Oct, `amount_state = owner`); no page has a button for that state.

## 2 · The owner's rulings (to be minted D at the close)

1. **"Has its scan" goes.** Row 1 is *Paper matches* (verified + has-its-scan). The read quality stays the server's.
2. **Every difference, ₹1 included, goes to Amir** — *Marg mein bill ₹X kijiye (round-off)*; a bill settles only when Marg = paper to the rupee; the sheet pays Marg's figure = the paper's. Row 4 *Rounding* folds into row 3. Supersedes "rounding — the supplier's figure paid" (S726, F-1140 road) and kit 4's "the NEFT on the suppliers' figures".
3. **The "You" state goes** — every difference is Amir's; a dispute comes to row 5 with the owner's two buttons. Kedar A000211 → Amir's card.
4. **Ravi Medical Agency is an owner-confirmed supplier**: no scan asked, never *no scan*; one *Confirm* line to the owner per bill; a scan that comes pairs as usual; a per-supplier setting the owner can extend.
5. **One source** — the scan register's states feed every page; **one language** — *Paper matches · Difference → Amir · Return pending · Confirm (yours) · No scan*; each open line says what, next, whose; build and decision numbers never on his screens.
6. **One way in** — the Marg Purchases tile opens the step view; the console month page carries *Purchase check — <month> · …* per month; the register and the audit page are "the full list" under it; the same month strip on all three.
7. **The audit page's Correct/Wrong buttons come off the owner's view** — one place to decide.
8. **The one lock gate** reads rows 1–5 and 8 (row 6 joins in kit 4) plus Marg's reports; Step 2 runs itself.
9. The hub counts counted months only (October onward).
10. Amir's summary reads his list (*Marg sudhar n · Wapsi baaki n · proved ✓ n*, the bills).
11. Old months (June, July PROVISIONAL): his word if he wants them locked; nothing else.
12. **The mock approved (06:04 IST) with one addition — everything inline on his step view.** Each line carries its own scan (folded open, as S738 built it) and every action that line can take — *Confirm*, the second-look pair, the return answers, *Not this bill → pick the right bill* (a re-pair, audited), *Accept without paper*, *Ask reception to rescan*, *Undo* — so he never leaves the page. **A Marg correction is still proved only by Amir's export (F-1162), never by a tap.**
13. The build runs in a fresh session (his word 06:04: "if this has been a long session, end it and build fresh").

## 3 · The build (S749_ONE_SOURCE)

| # | what | files (this project unless named) |
|---|---|---|
| 1 | `register()` states → one vocabulary (`STATE_EN`); *Paper matches*; `band_p` → every difference counted (₹1 → `amount_differs`); `owner` astate → Amir; the Ravi setting (`purchase.owner_confirm_suppliers`, a *Confirm* door, audited, Undo) | `scan_register.py`, `porders.py` |
| 2 | the step view: rows renamed; row 4 gone; the *Confirm* lines; plain words; the month strip | `scan_register.py` |
| 3 | the register: plain words; read-quality and legacy folded; the month strip | `scan_register.py` |
| 4 | the audit page: the state column from the register; Correct/Wrong hidden for the doctor; the month strip; the clipped item-wise bill numbers matched by number tail + amount (the 4 bills close) | `purchase_app.py` |
| 5 | the hub: counted months only; the row's status words from the register | `purchase_app.py` |
| 6 | the pay sheet: `_lock_gate` + the register's open rows (1–5, 8); Step 2 run by the server | `purchase_app.py` |
| 7 | the tile → the step view | `portal/portal.py` (the parent's — PLANNED line, told) |
| 8 | the console month line *Purchase check — <M>* and the register link per month | `finance/month_read.py` (the parent's — PLANNED line, told) |
| 9 | Amir's English summary reads `s738_tracked` / `s740_track` | `amir_day.py` |
| 10 | Amir's card wording for a round-off correction | `amir_day.py` |

**Proof:** `py_compile`; a walk on a made-up root with a CONTROL that goes red; DRY on the box for anything that re-states a live bill (the ₹1 bills, Kedar A000211, the 4 clipped bills) — read before install (F-1153); a cold review until SAFE; the pages read live after the install, signed in as manoj. The 24-Oct rule for the four files: read whole before patching (`scan_register.py` +3, `purchase_app.py` +3, `amir_day.py` +2 — drift).

## 4 · After kit 5

**Kit 4 (the month end):** the dealers' month summaries (row 6; the Scan App's statement kind on the pharmacy lane — PLANNED line, told); the issues list (*accept / ask the supplier / carry*); the server-built bill-wise and supplier-wise statements (D849); row 7 — the lock and the NEFT when Marg = papers = summaries. **Then the order-list kit** (`S402_ORDER_LIST_PLAN.md`).

**People, before October locks:** Amir — the 11 waiting November bills; Yogendra 19612, Shivaaz 3854 (then Kedar A000211, 234); the October item-wise re-export to 31-10. Reception — Janta's revised bill when it comes. Shavez — the Bass ₹1,597 cheque. The owner — ZUPRINOR 5 (row 8); the two unsent September supplier messages (A.A., Deepam).

*S403_KIT5_ONE_SOURCE_PLAN · the Sanjeevni chat · 08-Nov-2026 · the mock follows; nothing live changed by this paper.*
