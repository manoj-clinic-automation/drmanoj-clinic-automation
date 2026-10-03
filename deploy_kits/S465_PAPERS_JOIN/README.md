# S465_PAPERS_JOIN — D664 slice 2 of 3: one purchase, one PDF

Session 292 (parent), 03-Oct-2026. Built on the owner's word "build." Follows S464_CLINIC_PAPERS (live 03-Oct).

## What it does, in plain words

1. **Joins papers that were scanned separately.** A battery bill and its two warranty cards came in as three papers.
   On *Clinic papers to sort*, a scan with nothing read on it now says which bill it was scanned after and offers
   **Join into B-xxxx**. The join page shows the bill and the papers scanned beside it, with the blank ones already
   ticked; any other paper can be added by typing its number.
   - The bill keeps its number. Each joined page keeps its own number and reads "a page of B-xxxx".
   - The PDFs become one NEW file; the original files stay on disk.
   - **Undo the last join** puts the bill's own file back and makes each page a paper of its own again.
   - A photo (not a PDF) is linked to the bill but cannot go into the file — the page says so.
   - A pharmacy scan is never joined, either way. An approved bill is never made a page of another.
2. **Corrects the suggestions, from the first 29 real papers:**
   - medicine bills found on the clinic lane (tablets, capsules; a pharma / drug-house supplier) → "Move to Pharmacy
     purchase", through the app's own lane door;
   - "DHL 8*10 150 SH" → X-ray films, small film;
   - Yuvika's and Agarwal Surgicals' handwritten slips (no bill number, no amount) → Procedure room, even when the
     items were read as garble;
   - F-710: "Agarwal Surgicals" never matched its own rule in S464 (the name was tested as a whole word). Fixed.
   - Nothing is guessed for electrical fittings, plumbing or implants.

Owner and manager only. The scanning staff see nothing new.

## Files

| file | what |
|---|---|
| `built/clinic_papers.py` | S465.1 — replaces `/root/assetapp/clinic_papers.py` (46cfdf8c) |
| `apply_s465.py` | ONE line of `/root/assetapp/asset_register.py`: 6dd5f3ab → b0e0915e |
| `walk_s465.py` | old / new / guard / half-way, on empty scratch databases with made-up papers and hand-made PDFs |
| `figure_s465.py` | the real papers on a COPY of assets.db, and one real join rehearsed on copies of two real scans |
| `install_S465_PAPERS_JOIN.sh` | gates → lock → pins → walk → real-papers check → backups → place → restart → checks → restore on red |

Database: one new table `d664_join` (what was joined, for the undo). Nothing else changes shape.

Not touched: lanes, intake, `scanner_widget.js`, `shared/scan_checks_s441.py` (its `_merge_pdf` is called, not changed),
the pharmacy hand-over, every finance file.

## Run (one line; it carries its own pull)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S465_PAPERS_JOIN/install_S465_PAPERS_JOIN.sh

`DRY=1` in front of `bash` runs every gate and places nothing.

## To take it back

    \cp -p /root/assetapp/asset_register.py.bak_S465_6dd5f3ab /root/assetapp/asset_register.py && \cp -p /root/assetapp/clinic_papers.py.bak_S465_46cfdf8c /root/assetapp/clinic_papers.py && systemctl restart assetapp

Joins already made stay as they are in the database (the bill points at the joined file; the pages read "a page of").

## The three D664 kits on one line (S465, then S466; S467 whatever those two did)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S465_PAPERS_JOIN/install_S465_PAPERS_JOIN.sh && bash /root/deploy/repo/deploy_kits/S466_EXPENSE_WARRANTY/install_S466_EXPENSE_WARRANTY.sh ; bash /root/deploy/repo/deploy_kits/S467_WARRANTY_ON_HEALTH/install_S467_WARRANTY_ON_HEALTH.sh
