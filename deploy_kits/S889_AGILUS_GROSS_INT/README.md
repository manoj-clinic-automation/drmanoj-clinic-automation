# S889_AGILUS_GROSS_INT — the parent, S486, 18-Nov-2026 (his word 20:43: fix the 8 papers now)
The 8 Agilus papers whose lines did not add up print a line's gross as a whole number (no paise) with no HSN column; the reader took it for the HSN and the line had no gross.
- agilus_ledger.py e81d58f6 -> TO: a whole number is a gross reading too; when no single column adds up, each row's net is chosen row by row, and only when exactly ONE set of readings adds up to the paper (two sets = not guessed). The accountants' file is unchanged (the paper's own net).
Install: cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s889kit && cp -rp /root/deploy/repo/deploy_kits/S889_AGILUS_GROSS_INT /tmp/s889kit && bash /tmp/s889kit/install_S889_AGILUS_GROSS_INT.sh
Walks: walk_s889 51/51 (control S888's reader red 49/51: C3 = the live papers' shape); S884 28, S885 31, S886 34 on the new reader.
