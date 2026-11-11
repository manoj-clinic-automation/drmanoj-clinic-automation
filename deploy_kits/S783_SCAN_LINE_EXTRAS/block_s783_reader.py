


# ---- S783 (11-Nov-2026, Sanjeevni session 426, kit S783_SCAN_LINE_EXTRAS; the owner's word 05:51 IST: "Add the scanner lines") ------
#  A pharmacy-lane bill read by read_pharmacy() gives four more figures on each item line -- free goods, MRP, discount (%) and GST (%) --
#  so the Purchase bills page (finance provisional_s781) shows them beside the line. Only PHARMACY_PROMPT asks for them, and only
#  clean_pharmacy() keeps them (numbers or null) on a bill's items in claude_reading.data. read(), PROMPT, clean(), to_bill(), bill_items,
#  dealer statements, challans and claude_reread's re-reads are unchanged (they never carry the four figures).
#  The longer answer: a pharmacy reading may use up to S783_MAX_TOKENS; if a very long bill still runs out, it is asked once more with
#  the prompt as it was before S783 -- so no bill that read before S783 fails because of it.
#  Papers already read are not read again. Planned on the board (D646) by the Sanjeevni chat; the Scan App chat owns this file.
S783_ITEM_KEYS = ("free", "mrp", "discount", "gst")
S783_MAX_TOKENS = 16000
_S783_PROMPT_BEFORE = PHARMACY_PROMPT
PHARMACY_PROMPT = PHARMACY_PROMPT + """

For a single bill (not a statement), give each item four more keys, read from that line of the bill:
 "free": the free quantity given on the line (number or null), "mrp": the MRP per unit in rupees (number or null),
 "discount": the line's discount in percent (number or null), "gst": the line's GST rate in percent, CGST and SGST added (number or null).
Numbers only, no % sign. Never guess -- null for any you cannot read on that line."""


def _s783_num(v):
    if isinstance(v, str):
        v = v.replace("%", "").strip()
    return _num(v)


_clean_pharmacy_before_s783 = clean_pharmacy


def clean_pharmacy(data):                                            # noqa: F811 -- S783: + free / mrp / discount / gst on a bill's items
    out = _clean_pharmacy_before_s783(data)
    if not out or not isinstance(data, dict) or out.get("doc_kind") == "summary" or out.get("is_summary"):
        return out
    raw = [it for it in (data.get("items") if isinstance(data.get("items"), list) else []) if isinstance(it, dict) and _txt(it.get("name"))]
    for it, src in zip(out.get("items") or [], raw):                 # the same order and filter as clean() itself
        for k in S783_ITEM_KEYS:
            it[k] = _s783_num(src.get(k))
    return out


_post_before_s783 = _post


def _s783_with_prompt(body, text, max_tokens):
    msgs = []
    for m in body.get("messages") or []:
        content = []
        for c in m.get("content") or []:
            content.append(dict(c, text=text) if isinstance(c, dict) and c.get("type") == "text" and c.get("text") == PHARMACY_PROMPT else c)
        msgs.append(dict(m, content=content))
    return dict(body, messages=msgs, max_tokens=max_tokens)


def _post(body, key):                                                # noqa: F811 -- S783: the pharmacy reading's longer answer
    try:
        is_ph = any(isinstance(c, dict) and c.get("text") == PHARMACY_PROMPT for m in (body.get("messages") or []) for c in (m.get("content") or []))
    except Exception:                                                # noqa: BLE001
        is_ph = False
    if not is_ph:
        return _post_before_s783(body, key)
    code, js, text = _post_before_s783(_s783_with_prompt(body, PHARMACY_PROMPT, max(int(body.get("max_tokens") or 0), S783_MAX_TOKENS)), key)
    if code == 200 and isinstance(js, dict) and js.get("stop_reason") == "max_tokens":
        return _post_before_s783(_s783_with_prompt(body, _S783_PROMPT_BEFORE, max(int(body.get("max_tokens") or 0), S783_MAX_TOKENS)), key)
    return code, js, text
# ---- S783 end -------------------------------------------------------------------------------------------------------------------------
