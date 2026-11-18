# S885_AGILUS_ROWS_WIDE — the parent, S486, 18-Nov-2026
S884 read all 83 Agilus papers but no line: the real rows run past the rate (more columns after it; the masked layout showed only 170 columns).
- `/root/finance/agilus_ledger.py` 5395d324 -> TO: a row is read by its columns (2+ spaces apart) whatever follows the test; its amount is the column that adds up to the paper (the rate after the test's comma, or the line's last figure); the check (`/finance/ledgers/agilus/check`) carries the rows' shapes in classes only (D, A, C, W, H, S, M, Q -- never a word). Every paper is read again at install.
Install (server): `cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s885kit && cp -rp /root/deploy/repo/deploy_kits/S885_AGILUS_ROWS_WIDE /tmp/s885kit && bash /tmp/s885kit/install_S885_AGILUS_ROWS_WIDE.sh`
Walks: walk_s885 31/31 (S884's + rows with Qty/Rate/Discount/Amount after the test; control S884's reader red 26/31); S884's walk 28/28 on the new reader.
