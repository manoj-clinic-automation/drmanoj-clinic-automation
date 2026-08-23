# S198_P5 — duplicate Payment Register tile removed (owner, 23-Aug)

portal.py e2484429cfb0217cb6b8d6f3a44ce5c8 -> 43ec35b1e87075ef942946e918db82f9.
The Inbox Janitor tile already opens the same sheet; its desc now says so
('Payment register — view · print · export'). PAYMENT_REGISTER_URL stays readable
in config for any later surface. Gate 6/6.

    cd /root/deploy/repo && git pull
    bash deploy_kits/S198_P5/INSTALL_S198_P5.sh
