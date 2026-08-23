# S198_H2 — health page: the owner's three findings (23-Aug)

One file: finance_app.py 4ae49536309dad169441f7dc8fed7012 -> 2c99b2c6c719091deada5603fc295c90.
1. worst-first sorted FOR REAL (the docstring had claimed it since S195 — F-45 family,
   recorded) + the hero names the culprit checks.
2. Marg-push age is Sunday-aware (D322: the shop is closed; each intervening Sunday
   buys 24 quiet hours; detail says 'Sunday closed' when applied) — today's false
   'Something is wrong' at 30h was exactly this.
3. Renewals row is now a door to the Renewals Master v2 sheet (same target as the
   portal tile).
Offline differential: 563/673 -> 569/679, +6 exactly, fail set byte-identical.
Live projection: 674 -> 680.

    cd /root/deploy/repo && git pull
    bash deploy_kits/S198_H2/INSTALL_S198_H2.sh
