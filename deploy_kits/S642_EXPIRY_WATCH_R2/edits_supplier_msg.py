# S638 anchored edits for /root/finance/supplier_msg.py (FROM 4e3911a7)
# F-1014: the pay card offers the confirm for an SMS-seen NEFT not yet confirmed -- the same neft_done call (it confirms the SMS
# event and queues the messages).
EDITS = []
EDITS.append(('''    if ev and owner and st["can_undo"]:
        h.append('<div class="noprint muted" style="margin:6px 0"><button class="sm" onclick="neftUndo407()">Undo (within 24 h)</button></div>')''',
              '''    if ev and owner and ev.get("source") == "sms" and not ev.get("confirmed_by"):       # S638 (F-1014): an SMS-seen NEFT, unconfirmed
        h.append('<div class="noprint" style="margin:8px 0"><div class="muted">The bank\\'s SMS showed this NEFT on %s; it is not confirmed yet, so the '
                 'suppliers have not been told.</div><button class="p" onclick="neftDone407()">Seen in bank SMS — confirm and tell the suppliers</button></div>'
                 % _esc(_dmy(ev.get("date") or ev.get("created_at"))))
    if ev and owner and st["can_undo"]:
        h.append('<div class="noprint muted" style="margin:6px 0"><button class="sm" onclick="neftUndo407()">Undo (within 24 h)</button></div>')'''))
