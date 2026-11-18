# S887_AGILUS_ACCOUNTANTS — the parent, S486, 18-Nov-2026 (his word 20:25-20:29)
The Agilus figures are the NET amount. The detailed ledger stays his internal one; the accountants get a running ledger of net amounts against the invoices only -- the ledger alone, no invoice PDFs.
- agilus_ledger.py 41412d2d -> TO: accountants(month) -- date, Bill of Supply No., net, running total, brought forward; the paper's net from its TOTAL line when the header's is not read; the check names why a paper differs in figures only and compares the paper with the mail's figure.
- payment_ledgers.py d227bd74 -> TO: 'For the accountants' on the Agilus page, an xlsx per month or every month (Date, Bill of Supply No., Net amount, Deposit blank, Running total).
Install: cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s887kit && cp -rp /root/deploy/repo/deploy_kits/S887_AGILUS_ACCOUNTANTS /tmp/s887kit && bash /tmp/s887kit/install_S887_AGILUS_ACCOUNTANTS.sh
Walks: walk_s887 44/44 (control: the live files, red); S884 28, S885 31, S886 34, S882 54 on the new files.
