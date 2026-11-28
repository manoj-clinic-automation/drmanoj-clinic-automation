# S979_BATCH_SWAP — the batch swap (kit A of S543_BATCH_SWAP_DESIGN; D1113, F-1752)

**28-Nov-2026 · Sanjeevni session 546 · by Opus · his mock-up v7 (final):** https://claude.ai/artifact/6hxWjVT8fH9JcsayFvShXX

**The fault (F-1752).** Near expiry shows only the expiring batch. When the item also holds a newer batch, the old batch exists only on
paper in nearly all cases: the counter sells the newer batch while Marg keeps stock on the old one, and the old batch would expire in Marg as
a false loss. On the 28-Nov copy: 5 cases (TRUECEPROL OD, OXFLIN-OZ, HISTOCALAMIN LOTION — last selling day 30-11 — C2CAL SYP, ZUBOGESIC TAB).

**The flow.** Every run of the Expiry watch finds the cases (an expiring batch with stock and no sale since the Batch Stock export, beside a
batch of the same item with a later expiry and stock; one batch printed two ways is never a partner). Darpan gets one push a day from
08:30 and a card on Stock milaan: *Nahi hai* → the two STOCK bills; *Hai, N* → those N never swapped, the batch stays on Near expiry marked
"Darpan found it"; no answer by 13:00 on the day he was asked → the bills are shown anyway (amber "not reconfirmed" for the owner). He makes
ONE sale bill named STOCK (old batches) and ONE sale return named STOCK (newer batches, same rate) and taps *Dono bill bana diye*. The next
morning's sale report closes each item when the sale on the old batch and the return of the same quantity on the newer batch are both seen.
One half only → red, Darpan told. Red push to the owner (once a reason): last selling day within 2 days and the sale not in Marg; one half
missing; the last selling day passed unswapped (judged only after that day's report is in). Amir, vouchers and extra exports are out.

| file | FROM → TO | what |
|---|---|---|
| `/root/finance/batch_swap.py` | NEW → 5ed7cdc7 | the cases (`expiry_swap_case`, every write audited), the answers, the judge on `mi_sale_line`, the pushes (`order_rules._push`), the owner's section, the Near-expiry marks, the Needs-you line |
| `/root/finance/expiry_watch.py` | 5db83cbc → 38805560 | `run()` calls `batch_swap.after_run` after `stock_batch_now` (never a push; its own rollback); `owner_page` draws *Batch swaps* collapsed above Near expiry and marks Darpan's *Hai*; `needs_you_lines` one red line |
| `/root/finance/stockmatch.py` | 91b5193f → ffcbe936 | `st["swap"]` in the state; `POST /api/swap`, `POST /api/swap/bills` through `_auth` |
| `/root/finance/stockmatch.html` | bc67e102 → 21339d07 | the card above Aaj ki ginti |
| root crontab | + `# S979_BATCH_SWAP` | every 10 min 08:00–21:50 IST: judge, missed, the pushes |

Settings (table `setting`): `swap.on` 1 · `swap.push_to` darpan · `swap.owner_push_to` manoj · `swap.push_at` 08:30 · `swap.answer_by` 13:00 ·
`swap.red_days` 2. Off: `/root/finance/_off/S979_OFF` (or ALL_OFF, spine/OFF), or `swap.on` = 0.

**Not in this kit.** STOCK as its own section beside Home and Procedures (kit B — the parent's `finance_app.py` / `finance_ingest.py`); until
then a STOCK pair is a sale and an equal return on the same day (net zero in cash). The judge matches by item, batch and quantity, not yet by
the bill's name STOCK (kit B reads the names). Darpan's sell-first list still names the paper batch. The monthly-export pushes (kit C).

**Proof.** `walk_s979.py` 74/74 (twice; 72/72 on a machine without node, the two drawing checks skipped), the control red at A1 on the live files; S976's, S975's, S973's, S971's, S969's, S967's and S965's
walks the same on old and new files; the watch's own run on a COPY of the live database with the old and the new files: every list and every
batch identical, the new run finds the cases (28-Nov copy: 5). Rehearsal on a made-up root: dry · red@4 · red@5 · install after a red ·
again · undo · reinstall · wrong FROM · a read pin moved · the lock · a corrupt kit. NO_PHONE_NUMBERS clean.

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s979kit && \cp -rp /root/deploy/repo/deploy_kits/S979_BATCH_SWAP /tmp/s979kit && bash /tmp/s979kit/install_S979_BATCH_SWAP.sh

Undo: `bash /root/deploy/repo/deploy_kits/S979_BATCH_SWAP/undo_s979.sh` (the table `expiry_swap_case` stays; nothing reads it).

S979_BATCH_SWAP · 28-Nov-2026 · Sanjeevni session 546 · D1113 · F-1752
