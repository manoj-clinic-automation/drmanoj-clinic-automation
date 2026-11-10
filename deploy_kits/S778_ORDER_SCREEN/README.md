# S778_ORDER_SCREEN — the order screen: old orders at the top, Ab nahi milta, the wrong-dealer check

**Session 425 (the Sanjeevni chat), 10-Nov-2026. D890: the owner's mock approved 15:08 IST; "Go" 18:27 IST.** Mock: `https://claude.ai/artifact/4gc42Z3vi67DUhrEBNz2Mk`.

| file | from → to | what |
|---|---|---|
| `/root/finance/porders_s454.py` | `cd2feeb3` → TO | the S778 block appended (wraps `order_sheet.entries` / `order_supplier` / `cron_pass` and `order_rules.needs_you_lines`; redraws `order_list`, `_card`, `supplier_page`; adds `/s454/abnahi` and `POST /api/s778/{again, na, na_answer, dealer_ok, move}`); `api_qty` accepts an S778 line |
| `/root/finance/order_s778.py` | NEW | the logic and its HTML pieces |

Read, unchanged, pinned by the installer: `order_sheet.py 53abf461` · `order_track.py 6f4746c5` · `order_rules.py bdefd058`.

**(a) Old orders at the top of *Order karna hai*.** A red box: every medicine ordered and not come 3 working days after its order (Sundays not counted), one line per dealer + medicine, oldest first — the age big (orange under 7, red from 7), item · quantity, dealer · order date, *Dobara order karo* / *Ab nahi milta*. Sources: the open carries, the late orders' open lines, Marg's old group. A line already on today's dealer card is tagged *PURANA · N din* on that card instead. It leaves the box when its bill comes, it is ordered again (by anyone), or *Ab nahi milta* is tapped. The bottom link *Purane pending: N* is not repeated while the box shows.

**(b) Ab nahi milta.** Off today's list at once (the card, Marg's open order as the papers read it). The doctor's Needs-you line *"<staff> says <ITEM> is no longer available (last bought <date>)"* opens `https://followup.dr-manoj.in/finance/porders/s454/abnahi`: *Stop it everywhere* (an `order_item_rule` 'never' marked *S778 until a bill brings it* — held from the plan, its proposals, Darpan's list and the comparison; lifted by itself by the first new Marg PURCHASE bill of the medicine, the rule it replaced put back) · *Keep ordering* · *Undo*.

**(c) The wrong-dealer check.** A line to a dealer who has never billed the medicine while another has: a warning on the card (*<X> ke card par bhejo* / *<dealer> hi sahi*, remembered), a count line at the top, and in the box (*<X> ko order karo*). Each catch is listed on the doctor's page for a week, and in his Needs-you as information.

**Writes:** its own tables `order_s778_again`, `order_s778_na`, `order_s778_dealer_ok`, `order_s778_wd`; `order_item_rule` only on *Stop it everywhere*; `s454_line_edit` (reasons `s778_na`, `s778_moved`); `order_carry.dropped_*` (`s778_na`, `s778_moved`). Never Marg, `purchase_line`, or the rules' JSON lists. Every wrapper is fail-soft: with `order_s778` unreachable every screen is as before.

**Proofs:** `walk_s778.py` 44/44 green on made-up rows (the box and its ages, Sundays, Dobara → card → ordered → gone, *<X> ko order karo* once only, Ab nahi milta → Stop → a RETURN does not lift → a new bill lifts and restores the doctor's own rule, Keep, Undo, move / *hi sahi*, the week's catches, the quantity and remove doors on an S778 line, the freeze, S778 unreachable, the undo's lift); the CONTROL on the live file red (5/44). Cold code review: 1 must-fix + 6 should-fix, all fixed and walked. Screen review (phone 390 px and PC, made-up data): the new pieces' findings fixed. `rehearse_s778.sh` 5/5. `proof_s778.py` on the device's copy of the 10-Nov database: red box 7 (+8 on today's cards); TOLTRIS PLUS Ab nahi milta → stop → undo; XGESIC LA Dobara → Drug Deal's card → ordered → gone; PRETOL 8 moved Shivaaz → Kedar.

**Install (the owner's paste):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s778kit && cp -rp /root/deploy/repo/deploy_kits/S778_ORDER_SCREEN /tmp/s778kit && bash /tmp/s778kit/install_S778_ORDER_SCREEN.sh
```
**Undo:** the installer prints the one line — the kit's holds lifted first (`order_s778.py <db> --lift-all`), then the backup back, the new file removed, finance restarted.
