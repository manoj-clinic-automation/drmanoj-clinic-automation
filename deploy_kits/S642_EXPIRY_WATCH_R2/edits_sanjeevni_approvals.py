# S638 anchored edits for /root/finance/sanjeevni_approvals.py (FROM 792f4a9a)
# D780: the owner's Expiry watch page (/finance/sanjeevni/expiry, checker only) and its Needs-you lines (fail-soft).
EDITS = []
EDITS.append(('''#  v1.11 (S428, D633, 27-Sep-2026): the Month section gains''', '''#  v1.12 (S638, D780, 24-Oct-2026): the owner's EXPIRY WATCH -- GET /finance/sanjeevni/expiry (the page, expiry_watch.owner_page) and
#  POST /finance/sanjeevni/expiry/settings (its thresholds), checker only; Needs you gains expiry_watch.needs_you_lines (what is expired or
#  stops selling next month; the month's Batch Stock not received), each line carrying href to the page. Fail-soft: without the module
#  or its tables nothing here changes. NEEDS_YOU_WITHOUT_S638=1 leaves the lines out -- set only by an older kit's frozen walk re-run.
#  v1.11 (S428, D633, 27-Sep-2026): the Month section gains'''))
EDITS.append(('''VERSION = "1.11"''', '''VERSION = "1.12"'''))
EDITS.append(('''            lines.extend(amir_day.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 7 · the statement's age (a word, not a fault)''', '''            lines.extend(amir_day.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 16 · S638 (D780): the expiry watch -- expired batches, batches Marg stops selling next month, the month's Batch Stock (fail-soft)
    if os.environ.get("NEEDS_YOU_WITHOUT_S638") != "1":
        try:
            import expiry_watch  # noqa: PLC0415
            lines.extend(expiry_watch.needs_you_lines(con))
        except Exception:  # noqa: BLE001
            pass
    # 7 · the statement's age (a word, not a fault)'''))
EDITS.append(('''@bp.route("/finance/approvals/old")
def page_old():''', '''@bp.route("/finance/sanjeevni/expiry", methods=["GET"])
def page_expiry():
    """S638 (D780): the owner's Expiry watch -- expired, near expiry, dump (orthotics and medicines), wrong batch, new products,
    out of stock. Read-only; the list is made every night by expiry_watch.run (spine/near_expiry.py)."""
    u, err = _require("checker")
    if err:
        return err
    import expiry_watch  # noqa: PLC0415
    return expiry_watch.owner_page(_db())


@bp.route("/finance/sanjeevni/expiry/settings", methods=["POST"])
def page_expiry_settings():
    """S638: the page's thresholds (the owner's rule of 26-Sep: every threshold a setting he alters on the screen). Audited."""
    u, err = _require("checker")
    if err:
        return err
    import expiry_watch  # noqa: PLC0415
    con = _db()
    saved = expiry_watch.save_settings(con, request.form, u.get("user") or "owner")
    return expiry_watch.owner_page(con, saved=saved)


@bp.route("/finance/approvals/old")
def page_old():'''))
