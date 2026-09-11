# S240_STOCK_GATE — the count gate (Sanjeevni item 5 · S228 Phase 1, item 2)

**11-Sep-2026, Session 240, on the owner's "GO".** Phase 1 item 1 — the three columns (shelf · Marg · ours) on
every line of a count — is already live since S228 (`S228_THREE_WAY`, `stock_app.py` 55cd610e). This kit adds
the other half: **a count refuses when Marg's stock export is older than the day's last entry.**

The server cannot see Marg's keying times; it can see the order of Marg's own exports. Three rules:

| rule | red when |
|---|---|
| R1 nothing keyed after the stock | an item-wise purchase export taken after the stock export carries a bill, dated inside what the earlier item-wise exports covered, that none of them carried |
| R2 purchases exported to the stock day | item-wise purchase exports do not reach the day before the stock's as-on date |
| R3 it is Marg's stock | the newest stock day has no Marg STOCK CLOSING export — only our own computed figure |

Red → the counter's page says, in Hinglish, "Abhi stock count shuru mat kijiye" and why; a staff submit is
refused with nothing recorded. The owner sees the reasons in English and may open the count anyway.
Now / Drift pages show the reasons as "COUNT GATE" lines. No template changes.

**Checked against history:** the 05-09 stock (taken 06-09 01:26) → RED, a bill of 01-09 keyed after it (the S228
residue case); the 06-09 stock the real count used → GREEN; the 02-09 stock → AMBER (nothing earlier to compare).
**On the 11-Sep 01:05 nightly copy:** RED — the newest stock day (09-09) is our own computed figure, and purchases
were exported only to 06-09. A count opened then would have measured us against ourselves. The installer prints
the gate on the live data as it stands at install.

**Install — one line on the VPS:** `bash /root/deploy/vps_deploy.sh S240_STOCK_GATE`
**Undo:** `\cp /root/finance/stock_app.py.bak_S240_55cd610e /root/finance/stock_app.py` then restart
`clinic-finance.service`. Emergency switch-off without code: `STOCK_GATE=off` in the service environment.
