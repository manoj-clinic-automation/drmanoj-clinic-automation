# Claude Code brief — S414_RULES_PAGE_UX (the buying-rules block on the owner's approvals page: no redraw on tap, real editors, ticks that stay)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S414 · fault F-635** (claimed on the System Board).
Follow-up to S410. The owner tried the page and could not proceed; his words: "I clicked one item in never-reorder, the list closed and it
shows only the item I clicked; the other items vanished and are hard to find again. Same for on-demand." **Owner-facing, English.**

## 1 · The fault, read from the live page (S283 in the owner's browser, 15:2x IST)
`finance_ui/finance_approvals.html` (as S410 left it — read live): `poPost()` → on success `loadPORules(); loadNeeds();` — `loadPORules()`
fetches `/finance/porders/api/rules/state` and **rebuilds the whole `#poRules` block by innerHTML**. Every `<details>` inside (the 23
supplier lines, "Never re-order — candidates (42)", "On demand — candidates (15)", "Your item rules", "last changes") is rendered closed,
so one tap on a candidate closes the list; the ticked item then appears only under "Your item rules (N)". `poEdit(sn)` uses `prompt()`
asking the owner to type a field name (cadence / order_days / blocked_days …) — unusable for him. `poFreeze` uses `prompt()`, `poApprove`
uses `confirm()`. Server side (`order_rules.py`, S410) is fine: the item rule lands; nothing here changes an API except where §2 says.

## 2 · The build (finance_approvals.html — clinic file, declared; `order_rules.py` only for the two small API additions in §2.5)
1. **Never redraw on a tap.** Item ticks, supplier edits, pause, freeze, approve: update the DOM in place from the API's answer (or
   re-fetch state and patch only the changed row/counts). If a full rebuild is ever needed, **remember every open `<details>` and the
   scroll position and restore them** after the rebuild (a small helper used by every path).
2. **Candidates as check-lists that stay put.** Both candidate tables become rows with a checkbox at the left: tick = saved at once (a
   small green tick + "saved" fades in on the row; the row stays where it is, greyed with the rule name); untick = removed (no confirm
   dialog; the audit row records it). A count at the top of each list: `12 of 42 ticked` · **Tick all shown / Untick all** · a filter box
   (type part of a name) · sort by stock value (default) or name · "Show ticked only". The list stays open while he works; his ticks are
   visible in the same list, never only in another block.
3. **Per-supplier editor, inline.** "edit" opens the supplier's own row into a small form (no dialog): cadence (weekly / fortnightly /
   monthly / custom) · order days (Mon–Sat checkboxes) · Thursday ok (toggle) · Sunday blocked (toggle, default on) · lead days · safety
   days · cover cap · single-source extra (toggle) · review date + target · pause (toggle + reason) · note — **Save** / **Cancel**. The
   line above the form re-renders in plain words at once. Every field carries a one-line hint of what it does.
4. **Freeze / Approve** as inline confirmations (a second button "Yes, approve" appears beside the first for 10 s), no `confirm()`/`prompt()`.
   The freeze reason is a text box that appears inline.
5. **"Your item rules"** grouped by rule (never re-order · on demand · keep-in-stock · max on shelf · internal use), each row with a ✕
   to remove and, for keep/max, an inline number. The add box gets an autocomplete over item names (new small API `GET
   /finance/porders/api/rules/items?q=` returning ≤ 20 names from the stock master; the second addition: `POST …/rules/item` returns
   the updated counts so the page needs no re-fetch).
6. **Order of the block**: Approve rules (with a one-line summary "23 suppliers · N never · M on demand · frozen: no") at the TOP of the
   block as well as the bottom · shop-wide line · suppliers (collapsed by default, "Kedar" first) · the two candidate lists · item rules ·
   last changes (collapsed). Phone width: the tables scroll horizontally inside their card, never the page.
7. Nothing else on the approvals page changes; S410's server rules are untouched.

## 3 · Pins — `finance_ui/finance_approvals.html` as S412 left it (read live; clinic — declared); `order_rules.py` as S410 left it
(read live; the two API additions, anchored). Restart `clinic-finance` only.

## 4 · The walk (scratch copy; a headless check of the page's JS is enough for the DOM behaviour — node or the browser on the box if present;
otherwise assert on the rendered HTML/JS text and the APIs)
A tick posts the item rule and the response carries counts · the items API filters and caps at 20 · the state API is unchanged · the page
source contains no `prompt(` / `confirm(` in the rules block · every S410 walk re-run green.

## 5 · Done means
Kit `deploy_kits\S414_RULES_PAGE_UX\` · installed · published · `claude_code_briefs\REPORT_S414.md` — owner lines first, in this order: what
happens now when he ticks an item, how he edits a supplier, where Approve rules is; ending with `https://followup.dr-manoj.in/finance/approvals`.
