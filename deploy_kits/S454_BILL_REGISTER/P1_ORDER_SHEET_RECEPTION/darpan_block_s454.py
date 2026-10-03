# ------------------------------------------------------------------ S454 (D666): the order sheet on Darpan's card
def _s454_sheet_safe(con):
    """'Order sheet': when the newest came, how many medicines and suppliers, that it has reached reception -- or that the newest file was
    refused. Read from order_sheet in-process; never breaks the page."""
    try:
        import order_sheet                                   # noqa: PLC0415
        return order_sheet.darpan_card(con)
    except Exception as e:                                   # noqa: BLE001
        return dict(ok=False, error=str(e)[:80])
