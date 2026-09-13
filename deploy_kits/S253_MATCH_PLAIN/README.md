# S253_MATCH_PLAIN — the morning-match card in plain words (clinic_money.py 1.1 → 1.2)

**The owner, 13-Sep-2026:** *"Your match page data is very taxing and cumbersome for me also, not only
staff, to understand your mathematics. If you can simplify it, then it is much better."* And: *"50 rupees
was a blood sugar payment."*

Built on the live `clinic_money.py` `9cc6bb7ab5a9eacaf9ecfaee20e44763` (S252). **One file changes.**
No data change, no portal, no grants.

| | before (S251/S252) | now |
|---|---|---|
| top of the card | "1 thing needs a person; everything else is explained." + a nine-row Counter/Docterz/Diff table with minus signs | **one sentence**: *Saturday 12-Sep: the counter sheet has ₹650 more than Docterz. Everything else matches or is explained.* |
| the flag | "counter is ₹650 higher. Where: consultation +₹600, X-ray −₹50 … How: cash +₹1,700, UPI −₹450, card −₹600." | *The counter sheet has ₹600 more than Docterz — consultation ₹600 more. Most likely: ₹600 paid by card was written as cash; the counter has one consultation more than Docterz.* + a one-line Hinglish nudge, then the two buttons |
| everything else | always on screen | folded: **Explained (n)** · **Waiting for the bank (n)** · **Show the numbers** — open only when tapped; the links to the sheet, Docterz entries and the MPR live inside the last fold |
| the ₹50 | a "−₹50" on X-ray | **explained by name** — *₹50 blood sugar test — Docterz counts it under X-ray, the counter under procedures. Same money.* — and netted out before any difference is judged (`HEAD_MOVES`, one line per such fact) |

The arithmetic underneath is unchanged and still available under *Show the numbers*.

## Proof — `EVIDENCE_S253.txt`
`walk_s253.py` — **143 checks, 143 ok**: the S252 walk with the card expectations rewritten (one
sentence on top; no "Needs a person" card on a clean day; the folds present; no minus-sign arithmetic
before the first fold; the numbers still complete inside it) plus the real Saturday shape — a ₹50 blood
sugar under X-ray in Docterz and under procedures on the counter, a ₹600 card written as cash, one
consultation extra — giving the one plain flag above. Mock install GREEN; re-run ALREADY INSTALLED.

## Install — ONE line on the VPS, after the owner's publish
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S253_MATCH_PLAIN/install_S253_MATCH_PLAIN.sh
```
Refuses unless `/root/finance/clinic_money.py` is exactly `9cc6bb7a…`. Restarts `clinic-finance` only.
