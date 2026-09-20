# S340_CHECK_KAREIN

Records step 3 (owner, S271_BUILD_BRIEF §2.5). **Check karein** — one reception queue in Hindi (Alisha, Shivani, reception; Shavez the checker), one-tap answers with who and when, oldest first. Items now: a blood test ordered with no report after 2 days (not tested / asked the lab — "asked" comes back after 3 days if nothing arrives) · a lab report for an ID the clinic never issued (confirm, or type the right ID — the file moves to that patient) · a lab e-mail with no PDF. X-ray and WhatsApp items join when those steps go live. The doctors see **one collapsed line** on the records page — "Patient records: all clear" or "N need a look · oldest D days" — opening to the items and the last 7 days' answers. Walk: 131 checks.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S340_CHECK_KAREIN/install_S340_CHECK_KAREIN.sh
```

```
https://followup.dr-manoj.in/finance/checks
```

Pins: `records.py` `dcb49d8c…` → `0f3e48caa2aa0b7200c54fe2be4bbb4d` · `finance_app.py` `3a871f53…` → `7866b1ee6e70d19b5c096ef1b0099bd3` (patched on the box) · `portal.py` `b7b0e43c…` → `d9a9dc409b203a4d8dcdd623aa54565f` · `tile_grants.json` v22 → v23 `a5f8b3b1ef40047052b65d9735f02e3f`.
