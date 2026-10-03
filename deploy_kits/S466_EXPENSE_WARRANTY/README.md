# S466_EXPENSE_WARRANTY — D664 slice 3 of 3: a Dr MK expense keeps its warranty

Session 292 (parent), 03-Oct-2026. Built on the owner's word "build." Needs S465_PAPERS_JOIN installed first.

## What it does, in plain words

1. **On a Dr MK expense paper's own page: "Keep the warranty".** What it is (offered from the first item read on the
   bill), warranty till (typed once, from the card), and "Remind me": 30 days before · 7 days before · No reminder.
   Save; later "Save the change" or "Remove the warranty". Optional — a paper with no warranty needs nothing.
2. **It shows on the asset app's "Renewals & warranties" page, to the owner only.** By default only while it is inside
   its own reminder window (amber, "20 days"); under "show all upcoming" every warranty, in date order. A warranty that
   has ended is never "overdue" (nothing is owed) and drops off 60 days after its date. Each row opens the paper; the
   bill's number opens the PDF (bill and cards together once they are joined — S465).
3. **The way in.** On the list, "Move to Dr MK expense" now lands on the paper's own page, where the card is. On the
   app's bill page a Dr MK expense paper shows "Warranty: not noted · note it".
4. **Nothing goes out on WhatsApp.** `/api/due` is not touched; the walk holds its answer byte for byte with six
   warranties saved. The manager's Renewals page is byte for byte what it was.

Not built, said plainly: the plan's "offered from the scan when readable" — no scan reads a warranty date today, so
the date is typed. The owner's daily health page (finance) gets the same reminder by its own kit, S467.

## Files

| file | what |
|---|---|
| `built/clinic_papers.py` | S466.1 — replaces `/root/assetapp/clinic_papers.py` (231cd6a9, S465.1) |
| `apply_s466.py` | three exact edits of `/root/assetapp/asset_register.py`: b0e0915e → e774be89 |
| `walk_s466.py` | old / new / guard / half-way, on empty scratch databases with made-up papers; dates counted from today |
| `figure_s466.py` | the real papers on a COPY of assets.db, and one real save rehearsed there and removed |
| `install_S466_EXPENSE_WARRANTY.sh` | gates → lock → pins → walk → real-papers check → backups → place → restart → checks → restore on red |

Database: one new table `d664_warranty(bill_id, what, till, remind_days, set_by, set_at)`.

## Run (after S465, on the same line)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S465_PAPERS_JOIN/install_S465_PAPERS_JOIN.sh && bash /root/deploy/repo/deploy_kits/S466_EXPENSE_WARRANTY/install_S466_EXPENSE_WARRANTY.sh

## To take it back

    \cp -p /root/assetapp/asset_register.py.bak_S466_b0e0915e /root/assetapp/asset_register.py && \cp -p /root/assetapp/clinic_papers.py.bak_S466_231cd6a9 /root/assetapp/clinic_papers.py && systemctl restart assetapp

Warranties already saved stay in `d664_warranty`; the older code does not read them.

## The three D664 kits on one line (S465, then S466; S467 whatever those two did)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S465_PAPERS_JOIN/install_S465_PAPERS_JOIN.sh && bash /root/deploy/repo/deploy_kits/S466_EXPENSE_WARRANTY/install_S466_EXPENSE_WARRANTY.sh ; bash /root/deploy/repo/deploy_kits/S467_WARRANTY_ON_HEALTH/install_S467_WARRANTY_ON_HEALTH.sh
