S228 CENSUS -- read-only. Changes nothing, writes nothing, prints one table.

WHY IT EXISTS
  Everything up to the server door is measured and proven good: the Marg purchase
  exports cover all 159 days of the financial year on the PC; all 21 were pushed and
  every one came back HTTP 200; and the server's own parser, run offline here, reads
  fifteen TRAMATEE P purchase lines for the year with correct bills, quantities,
  rates and suppliers. The finding page shows four. The loss is on the server side
  of the door, and nothing anywhere reports what the server actually holds.

WHAT IT PRINTS
  1  purchase_export by type -- how many, what periods, HOW MANY ARE SUPERSEDED
  2  purchase_line rows by bill month
  3  purchase_line rows HIDDEN as superseded, by month   <- the decisive number
  4  purchase_bill rows by month
  5  sale_line_item rows by month
  6  stock_feed days by sender (ours vs Marg)
  7  stock_snapshot days, and which sender wrote each
  8  every TRAMATEE P purchase line the server holds

HOW TO READ IT
  If (3) shows April, May and June -- the exports are on the server and are being
  hidden as superseded. That is a rule to fix, not data to re-send.
  If (2) has no April/May/June rows at all -- the lines were never written despite
  the 200, and the ingest endpoint is the fault.
  Either way (8) says it in one glance: fifteen lines expected, and what is there.

TO RUN
  One paste on the VPS. It is in CENSUS.txt, one line.
