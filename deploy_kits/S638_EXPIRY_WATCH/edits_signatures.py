# S638 anchored edit for /root/marg_ingest/signatures.json (and manojz D:\Downloads\margsync\MargPull\signatures.json, the same bytes)
# F-1008 / D771: Marg's Batch Stock (WHOLE STORES, one row per batch) is filed under its own name, BATCH_STOCK, never as a closing stock.
EDITS = []
_A = '''    {
      "_comment": "S195: closing stock. Title carries the store name before the phrase, so the regex is store-agnostic. Dated by the AS ON date in its own title.",
      "type": "STOCK_CLOSING",
      "variant": "DEFAULT",'''
EDITS.append((_A, '''    {
      "_comment": "S638 (F-1008, D771, 24-Oct-2026): Marg's Batch Stock, WHOLE STORES -- one row per batch (S.No. Description | Batch | Expiry | Stock Unit). It prints the closing stock's own title, so it is matched HERE, before the batch-wise STOCK_CLOSING DEFAULT below, and filed under its own name -- never a closing stock. Read only by the expiry watch (/root/finance/spine/near_expiry.py). The spine never took the batch-wise layout as a closing (marg_read.identify: Total Stock heads only) and push_snapshot's reader refuses it; a VERIFIED file already filed is never re-judged, so the two old STOCK_CLOSING DEFAULT files stay where they are.",
      "type": "BATCH_STOCK",
      "variant": "BATCHWISE",
      "title_regex": "WHOLE\\\\s+STORES\\\\s+CLOSING\\\\s+STOCK\\\\s+AS\\\\s+ON",
      "header": [
        "S.No. Description",
        "Batch",
        "Expiry",
        "Stock Unit"
      ],
      "deep_verify": "structural",
      "uploadable": false,
      "end_marker": "TOTAL"
    },
''' + _A))
