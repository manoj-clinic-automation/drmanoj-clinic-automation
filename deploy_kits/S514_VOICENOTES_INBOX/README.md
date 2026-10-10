# S514_VOICENOTES_INBOX — Voicenotes' to-do lists reach the task box by themselves

Session 304 (parent), 10-Oct-2026. The owner's second pick (D689): *Voicenotes sending its to-do list into the task
section.* Until now he pasted the list.

## What it does

- **One public door**, `POST https://followup.dr-manoj.in/finance/api/voicenotes-push?key=…`, opened only by the key in
  `/root/finance/voicenotes.key` (made by the installer, mode 600, never printed). Voicenotes posts there on
  *To-Do List Creation*.
- A to-do list becomes **one waiting line per item** (Markdown, HTML or a list; tick-boxes and list marks taken off;
  `10.30 baje` and `2.5 kg` kept as written; at most 40 lines a list, 300 characters a line). The same list sent twice
  is stored once. A summary, a note or any other Voicenotes event is answered 200 and stored as nothing but its name.
- On his panel, **https://followup.dr-manoj.in/finance/aaj → Tasks**, the lines wait above *Give a task*:
  *Put the ticked ones in the box below* (then he picks who gets them and presses **Give**, as today) or *Remove*.
  **Nothing becomes a task by itself.**
- Below it, *Voicenotes sending here by itself — set up once*: the address to paste, with a Copy button, and the last
  post received.

## Files

| file | what |
|---|---|
| `voicenotes_inbox.py` | NEW in `/root/finance/`: the door, the owner's inbox (`/finance/aaj/api/vn`), tables `vn_inbox`, `vn_seen` |
| `make_s514.py` | `finance_app.py` ec5b3ab1 (S513) → 0d713b14: the door public (the module checks the key), the inbox identity-only (the module checks the owner), the module mounted guarded and counted (30 parts); `aaj_panel.html` 898c42e1 → 36bd57bc |
| `walk_s514.py` | old and new, an empty database, made-up logins and key |
| `install_S514_VOICENOTES_INBOX.sh` | gates → lock → pins → walk → backups + key → place → restart clinic-finance → checks → restore on red |

## Run (after S513)

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S514_VOICENOTES_INBOX/install_S514_VOICENOTES_INBOX.sh

## The one step that is his

In Voicenotes: picture (top right) → Integrations → Webhooks → Add Webhook → paste the address from the panel → tick
**To-Do List Creation** → Create.

## To take it back

    \cp -p /root/finance/finance_app.py.bak_S514_ec5b3ab1 /root/finance/finance_app.py && \cp -p /root/finance/aaj_panel.html.bak_S514_898c42e1 /root/finance/aaj_panel.html && mv /root/finance/voicenotes_inbox.py /root/finance/voicenotes_inbox.py.off_S514 && systemctl restart clinic-finance
