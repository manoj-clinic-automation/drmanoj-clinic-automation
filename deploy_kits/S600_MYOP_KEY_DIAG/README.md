# S600_MYOP_KEY_DIAG — why MyOperator refuses the WhatsApp key (read-only)

The owner, 09:09 IST 19-Oct: *"find out the cause and rectify it or escalate it to the My Operator support team"*.

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S600_MYOP_KEY_DIAG/install_S600_MYOP_KEY_DIAG.sh

Reads the key's shape (length, first 4 characters, stray spaces, file date — never the key), makes four read-only calls to
MyOperator (templates and phone numbers with the key; the key as x-api-key; a made-up key as the control), and counts the
sender's answers by hour for 48 hours. Sends no message. Writes `/root/finance/s600_myop_diag.json`.
