# S716_FLOWS_LAST_GOOD — S388 (Sanjeevni), 06-Nov-2026

**Why.** S714's live read (09:3x IST): the in-app Marg reports list said the sale report was *refused 05-11 14:46*, although that day's sale
report had come in at 10:32 and been taken — the line showed the newest file, whatever it was. And F-1110: a refused report should point to
its own steps.

| file | from | to | what |
|---|---|---|---|
| `/root/finance/reports_tile.py` | cb0d5e0c | TO_PINS | the list's reading: the newest GOOD file, and a refused one that came after it; every report line on *Aaj ki reports* (not the morning pair, which has *Kaise banayein*) carries *Steps dekhiye* to its flow |
| `/root/finance/marg_flows.py` | 7af3f3ec | TO_PINS | the list says the later refusal underneath (English for the owner, Roman Hindi for the staff) |

F-1110's other half — the plain cause of a refusal (MAIN STORE instead of WHOLE, M.R.P. instead of Purc. Rate) — is said by the medical PC,
which refuses the file before the server sees it; that is a medical-PC kit, on the owner's word.

**Proofs.** walk S716 9 ok (with S714's walk 16 ok inside) on the real finance_app with a made-up database; control on the live files 4 ok,
5 red. Installer rehearsed on a made-up server tree.

**Install (one server line, after the publish):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s716kit && cp -rp /root/deploy/repo/deploy_kits/S716_FLOWS_LAST_GOOD /tmp/s716kit && bash /tmp/s716kit/install_S716_FLOWS_LAST_GOOD.sh
