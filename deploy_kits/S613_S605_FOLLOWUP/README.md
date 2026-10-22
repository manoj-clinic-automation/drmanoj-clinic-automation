# S613_S605_FOLLOWUP — the orthotic sizes' figures across the split, bills matched by size, the old page's Yuvika door shut, the call row, three WhatsApp loose ends

**Brief:** `claude_code_briefs/S613_S605_FOLLOWUP.md` (v2, Sanjeevni session 335, 22-Oct-2026), with its independent read R1
(`03_WORKING_PAPERS/S335/S613_R1_REVIEW.md`, 5 blockers and 15 corrections folded in). It repairs what S605 left (S605 ran from its brief v1).
No D-number. One restart of `clinic-finance`.

## Pins (FROM → TO)

| file | FROM | TO | what |
|---|---|---|---|
| `/root/finance/stock_figure.py` | `51e1fc63…` | `8c66b6b1…` | F-951: `split_of`, `split_members`, `split_share`, `split_moves`; `shelf`, `marg`, `spine_move`, `carried` / `_taken_split` / `_family_bill` read them (18 anchored edits) |
| `/root/finance/order_sheet.py` | `17fa1fdb…` | `c7fe2561…` | F-960: `withdraw_late` from `handed_at`, the guarded withdrawal; `on_message_done`'s late no (`_s613_unconfirmed_now`, `_s613_late_no`); the one rule `_s613_phone_said_no`; the owner's line (8 edits) |
| `/root/finance/porders_s454.py` | `7ca91d4f…` | `34bab464…` | F-962: the call row's count in `home()` only; `_done_today`'s numbers through `OS.book_card` (2 edits) |
| `/root/finance/porders.py` | `e5a5c4d4…` | `b1736494…` | F-959: `api_send` refuses (409 `ortho_via_order_page`), its body retired (1 edit) |
| `/root/finance/porders.html` | `7a6799ae…` | `cbe1a46a…` | F-959: the Yuvika button, `send()`, `dq`, `ps`, `QTY`, `PICK`, the `send` / `sizes` words gone (9 edits) |

Full md5s in `PINS.sh`. Read only and pinned (must not move): `supplier_msg`, `stock_watch`, `shelf_figure`, `order_rules`, `stock_app`, `purchase_app`,
`amir_day`, `amir_salts`, `darpan_kal.py/.html`, `order_sheet_pdf`, `marg_order_pdf`, `item_alias`, `spine/spine_build.py`, `spine/spine_read.py`,
`spine/spine_rules.json`; proved unmoved: `finance_app.py`, `portal.py`, `tile_grants.json`, the crontab. **`finance.db`: no DDL, no DELETE, no hand edit,
no setting. `spine.db`: not edited, not rebuilt. DUTY_MAP: no change** (no duty added, moved or removed).

## What it does

- **F-951, the split read only where a reader spans dates.** `key_of` is unchanged (stock_app's count-voucher proof keys stay — R1-B1). `split_of`
  reads S605's `sp_alias` `rename_family` note by the strict pattern `\(split (\d{4}-\d{2}-\d{2}) from `; the old key through `sp_item` (the rules family
  `KNEE IMMOBILI?ER UNI (family)` included), cross-checked against the rename memory and the old key's `RENAME_SPLIT` date; anything missing or
  disagreeing = no split + one stderr line. A split size's moves = the old key's up to 10-10 × its counted share + its own key's after (one helper,
  `split_moves`). The share's members are the old key's members in the newest usable capture on or before the split day **whose every member reaches a
  counted item** (11-10 09:52's capture prints `SHOULDER IMMOBILISE L UNISON`, a spelling no count holds; S605's figure gave each shoulder size the whole
  family's history). Old and new name give the same figure; `approx` stays True while the base (the 6-Sep count) is before the split; no boundary.
- **Bills by size across the split (R1-B3).** `carried()` for a split size reads its new key's lines (as today) and its old key's lines matched by printed
  name only (a sibling size's line never matches); rule (b), branch (a) and the family-bill words likewise; the family-bill words span the old family
  (old key to 10-10, each sibling size's new key after) — order 20's L S BELT … XXX names bill 738 of 18-10 again.
- **F-959.** `POST /finance/porders/api/send` → 409 `ortho_via_order_page` for any login (Hindi for staff, English for the owner); nothing written.
  The old page (`?old=1`) keeps its orthotic table read-only. Named for later: `purchase_app` `/api/order` action `staff_send` (a third door).
- **F-962.** *Aaj ke order — call karo* = today's s454 orders still `sent` (WhatsApp, call, WhatsApp+call; never paper), counted in `home()` only.
- **F-960.** A handed message waits from `handed_at` and is never withdrawn by `queued_at`; the never-handed withdrawal is guarded (`handed_at IS NULL AND
  status='queued'`). A late "could not send" on an order unconfirmed in this cycle: nothing arrived → draft again, `sent_by` NULL, its lines `in_line`,
  reception's card *WhatsApp nahi gaya — call kijiye*, audit `s454_whatsapp_unconfirmed_no`; goods in → unchanged, audit `s454_whatsapp_unconfirmed_no_arrived`
  and the owner's line *"<SUPPLIER> — the reception phone said it could not send the order of HH:MM, but goods have already come in on it. Nothing was
  changed."* (the order may also be `received`). "May it be sent again" = `_s613_phone_said_no`: the newest cycle audit row is the phone's own no, and the
  message is skipped, never sent, handed. Once per no, never after a silence.
- **F-957.** `walk_s604_v2.py`: S604's purchase-page scenarios on its own January-2030 data (its own push payloads, its own twin rows, found by key);
  green on today's `purchase_app`, every control red on `purchase_app.py.bak_S604_60f2d846`. The reader-side controls (`marg_txt.py`) are not re-walked:
  their OLD (a59a222f) is the medical PC's and is not on the box.

## The kit

`make_s613.py` (the anchored builder) · `walk_s613.py` (the walk; `--facts` = the installer's read-only live facts) · `walk_s604_v2.py` ·
`install_S613_S605_FOLLOWUP.sh` · `PINS.sh` · `SUMS.md5` · `KIT_ID.txt`. Install (VPS, 08:02–23:49 IST):

    rm -rf /tmp/s613kit && cp -rp /root/deploy/repo/deploy_kits/S613_S605_FOLLOWUP /tmp/s613kit && bash /tmp/s613kit/install_S613_S605_FOLLOWUP.sh

`DRY=1` first runs every gate, the live facts and every walk, writing nothing. **Undo:** the installer prints the line (the five `.bak_S613_<from8>`
files back, one restart of clinic-finance).
