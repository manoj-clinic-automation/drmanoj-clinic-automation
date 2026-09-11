# S240_STOCK_GATE_R2 — the owner's correction to the count gate (11-Sep-2026)

*"Ravi bill date is 6 but it arrived late, don't confuse, the physical stock was the actual inventory at that time."*

A purchase bill keyed into Marg after the stock export, with an invoice date on or before the stock day, is either
goods that were on the shelf and keyed late (the export is short) or goods that arrived later (the export is right).
The invoice date cannot tell them apart. So R1 no longer refuses a count: it **names** the bills (amber, a
"COUNT CHECK" line on the Now / Drift pages) for a person to look at. The two refusals that remain are the ones
the server can know: **no Marg STOCK CLOSING for the day** (our own computed figure) and **purchases not exported
up to the stock day**.

The S240 statement that Ravi bill 7617 explained the DECA INSTABOLIN 50 difference of the 06-09 count is
**withdrawn**: those goods arrived after the count; the count was the real shelf.

Install: `bash /root/deploy/vps_deploy.sh S240_STOCK_GATE_R2` · undo: `\cp /root/finance/stock_app.py.bak_S240R2_5227c1d1 /root/finance/stock_app.py` + restart.
