# S690_AMIR_BATCH_FIX — the voucher pair, the Batch Stock every visit, the confirmation

*Sanjeevni session 369 · 01-Nov-2026 · on the owner's "MOCKUP IS GOOD" of 31-Oct 13:11 IST (the mock-up: `https://claude.ai/artifact/21JkxRFCaqVL9J2eGDbXYV`).*

## For the owner
Amir's "batch theek karein" list becomes ready-made Marg vouchers. For each wrong batch: a **STOCK RECEIVE** of the minus into the
minus batch and a **STOCK ISSUE** of the same quantity from the batch that has the stock — the system picks the batch (the same batch
typed differently when there is one, else the earliest expiry with stock; split when short), max 6 lines a voucher, the Receive set
then the Issue set. **He never opens a sale bill.** He saves the Batch Stock (whole store) at the end of every visit — it is now the
third report of his step 4, with the same steps as before. The server rechecks within five minutes and his card says, line by line:
*theek ho gaya* (gone the next day) · *abhi baaki* · *Receive ho gaya, Issue baaki* (or the reverse) by batch · and on step 4
*poore store ki nahi thi — WHOLE chun kar dobara* for a partial print. A sale made with no batch lands on his card as the same pair.
Today's 14 wrong batches become 6 vouchers (3 Receive, 3 Issue) the moment the kit is installed. Nothing holds his day open.

## What changes
`/root/finance/expiry_watch.py` **23e0a5bf → b68cda86** and `/root/finance/amir_day.py` **a0907b74 → 10a5f9c4** (`make_s690.py`,
10 + 4 anchored edits), and **one line in the crontab** (every 5 minutes: `expiry_watch.py run --if-new`; nothing else touched):
- a table `stock_batch_fix`: one row per minus batch — its Receive, its Issue batch, the figures it was asked on, its state;
  **frozen once made** (D542); a minus that moved while nothing of its row was done is remade from the new report (one round).
- `fixes_judge` at a run on a NEW report: Receive done when the minus batch's printed figure is no longer below zero; Issue done when the
  issue batch's printed figure has dropped by the voucher beyond its sales between the two reports; an item bought between is judged on
  the Receive. `fixes_create` names what is still wrong and uncovered.
- `fixes_rows` (his card), `batch_stock_state` (step 4: none / wait / ok / bad), `fixes_owner_line` (your expiry page, section 4),
  `new_batch_stock` (`run --if-new`: the watch runs only when a Batch Stock newer than the newest run has reached the door).
- The monthly "Batch Stock card" on step 3 goes (the report is step 4's third now); the owner's Needs-you lines are unchanged.

Untouched: the matcher, every stock figure, the expiry / near / dump / new / out-of-stock lists (proved byte-identical), Darpan's tab,
the pair's gate and heads on step 4, every other page.

## The proof
`walk_s690.py`: **39 of 39 green** on its own rows (a fresh finance db and spine in scratch, two made-up reports served to the module —
the split, the same-batch choice, the no-batch pair, 6 lines a voucher, done / receive_only / bought-between / open / new / superseded,
the card's words, step 4's four states, `--if-new`, the owner line); the control on the live files **1 S690 check(s) red · 0 green**
(the live file has none of it). The proof on the 1-Nov database copy, the real spine and the real archive: **old 110 lines / new 110
lines · IDENTICAL · report 49bf9b51 · fixes 14**. The two real reports (26-Oct, 31-Oct) walked through the judge by hand: 13 rows
asked on the first, all judged *open* on the second (nothing was fixed between — true), ROSIKA superseded and remade at its new figure,
TRAMAVIN new. The installer was rehearsed on a made-up root with a fake crontab: dry, install (the cron line added beside the old one),
again (ALREADY INSTALLED), a forced red at [8/8] (both files back, the cron line removed, the old line kept), a moved pin (STOP), a
corrupt kit (refused); the lock released every time. **An independent cold review** found one blocker — the Issue half could be called done on a print taken before the day's sales had
reached the server — and four should-fixes; all mended before placing: the Issue is judged only once the server holds the report day's
sales (his card says *Issue ki jaanch kal subah* until then; the Receive is confirmed at once), a half-done line asks for the minus as it
stands now, the fixes never roll back the lists, the crontab is read to a file and kept before one line is added.

## Install (the server)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s690kit && cp -rp /root/deploy/repo/deploy_kits/S690_AMIR_BATCH_FIX /tmp/s690kit && bash /tmp/s690kit/install_S690_AMIR_BATCH_FIX.sh
```
Gates → pins 23e0a5bf / a0907b74 → rebuild from the box's bytes → compile on both pythons → walk + control + proof on copies → backups
`*.bak_S690_<from8>` → place → read back → restart clinic-finance → healthz 200 → `/finance/amir/step/4` 302 → journal clean →
the cron line → the watch run once → walk on the placed files → lock released. Red after placing: both files back, the cron line
removed, finance restarted.

**Undo:** `\cp -p /root/finance/expiry_watch.py.bak_S690_23e0a5bf /root/finance/expiry_watch.py && \cp -p /root/finance/amir_day.py.bak_S690_a0907b74 /root/finance/amir_day.py && (crontab -l | grep -F -v -- 'expiry_watch.py run --if-new' | crontab -) && systemctl restart clinic-finance`

## Named, not done
- Whether Marg accepts a STOCK RECEIVE on a blank batch shows on Amir's first voucher; if Marg refuses, the blank-batch minus is cleared
  Marg's own way and the next Batch Stock confirms it the same.
- A Batch Stock saved during the visit stands for that day: the Receive is confirmed within five minutes; the Issue is confirmed the next
  morning, once that day's sale export has reached the server (the line says so meanwhile).
- The purchase-batch tie (new stock on its batch from the purchase report, 83 % tie uniquely) is the plan's step 3 — a separate kit.
- A no-batch sale of a medicine whose every batch is empty on the report has no Issue batch: it stays on the owner's page only.
