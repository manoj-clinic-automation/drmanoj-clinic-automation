# S886_AGILUS_ROWS_ANY — the parent, S486, 18-Nov-2026
S885 read 28 of 83 Agilus papers whole (20 differ, 35 no line, 60 rows not read): their rows carry no HSN column, or the HSN after the test.
- /root/finance/agilus_ledger.py 86d2761d -> TO: HSN optional and anywhere; the patient = the first words after the client code; the amount = the column that adds up to the paper; rows still not read reach /finance/ledgers/agilus/check fully masked (every letter X, every digit 9).
Install: cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s886kit && cp -rp /root/deploy/repo/deploy_kits/S886_AGILUS_ROWS_ANY /tmp/s886kit && bash /tmp/s886kit/install_S886_AGILUS_ROWS_ANY.sh
Walks: walk_s886 34/34 (control S885's reader red 30/34); S884's 28/28 and S885's 31/31 on the new reader.
