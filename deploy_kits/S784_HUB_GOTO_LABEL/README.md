# S784_HUB_GOTO_LABEL — the Hub's "Go to" link to the Purchase bills page, renamed

**Session 426 (the Sanjeevni chat), 11-Nov-2026; the owner's go 06:38 IST.** In the Sanjeevni Hub (`https://followup.dr-manoj.in/finance/approvals`), *Go to ▾ → Purchases & dealers*: "Scan register (bills ↔ Marg)" now reads **"Purchase bills — in Marg · scanned · differences"** — the page S781/S783 built. One line of `/root/finance/finance_ui/finance_approvals.html` (`dcd94412` → TO); the link's address is unchanged. A page file: no restart.

**Proofs:** `walk_s784.py` 5/5 (the new name once, the same address, the old name gone, exactly one line differs, the same place); its control on the live file red; `rehearse_s784.sh` 5/5.

**Install:**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s784kit && cp -rp /root/deploy/repo/deploy_kits/S784_HUB_GOTO_LABEL /tmp/s784kit && bash /tmp/s784kit/install_S784_HUB_GOTO_LABEL.sh
```
