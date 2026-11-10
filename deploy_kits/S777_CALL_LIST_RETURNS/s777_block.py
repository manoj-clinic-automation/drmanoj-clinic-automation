# ── S424 · F-1226 (the owner's two rules, 10-Nov-2026) ─────────────────────────
# (a) A visit from HALF the advised period before the due date closes the follow-up
#     (7-day advice: from 3 days before; 30-day: from 15 days before) — but never the
#     visit at which that follow-up was PRESCRIBED. Docterz's Appointment ID is the
#     prescribing appointment and rises day by day, so the prescribing day is read
#     from the IDs of follow-ups whose prescribing visit is certain (the patient's
#     only visit in the 120 days before due). Unknown -> the old rule (visit on or
#     after the due date), i.e. the patient stays on the list.
# (b) One visit closes EVERY open follow-up of that patient it qualifies for
#     (same Patient UID only; never on a name or a mobile).
EARLY_RETURN_SHARE = 0.5   # the owner, 10-Nov 18:39 IST: the window scales with the advice
_ANCHOR_WINDOW_DAYS = 120
_ANCHOR_K = 3


def _prescribing_day_bounds(fu_ledger: pd.DataFrame, visit_map: dict):
    """Anchors (appointment id, prescribing day) -> a function giving, for an id,
    the LATEST day its prescription can be (median of the K anchors just above it),
    or None when there are fewer than K anchors above (the newest ids)."""
    anchors = []
    for _, row in fu_ledger.iterrows():
        try:
            aid = int(str(row.get("Appointment_ID", "")).strip())
        except ValueError:
            continue
        uid = str(row.get("Patient_UID_Resolved", "")).strip()
        due = parse_date(row.get("Due_Date"))
        if not uid or not due or uid not in visit_map:
            continue
        near = [vd for vd, _ in visit_map[uid]
                if due - timedelta(days=_ANCHOR_WINDOW_DAYS) <= vd < due]
        if len(set(near)) == 1:
            anchors.append((aid, near[0]))
    anchors.sort()
    ids = [a for a, _ in anchors]

    import bisect

    def latest_day(aid):
        if aid is None:
            return None
        j = bisect.bisect_right(ids, aid)
        above = [d for _, d in anchors[j:j + _ANCHOR_K]]
        if len(above) < _ANCHOR_K:
            return None
        return sorted(above)[len(above) // 2]
    return latest_day


def recalculate_statuses(
    fu_ledger: pd.DataFrame,
    visits: pd.DataFrame,
    today: date,
    processed_on: str
) -> pd.DataFrame:
    """
    For every follow-up row, determine current status using the Visit Ledger.

    S424 (F-1226, the owner's rules of 10-Nov-2026) — replaces P0-01's
    one-visit-one-follow-up rule:
      (a) a visit from half the advised period (due - prescribing visit) before
          the due date (at least 1 day) counts as the return, unless it is the visit at which the follow-up was prescribed
          (the patient's latest visit on or before the prescribing day read from
          the Appointment ID). When the prescribing day cannot be read, the old
          rule stands: only a visit after the log date (due - 1) counts.
      (b) one visit closes every open follow-up of the same Patient UID that it
          qualifies for. Terminal (Returned*) rows are never re-evaluated.

    60-day expiry rule (P0-02 fix): unchanged.
    """
    fu_ledger = fu_ledger.copy()

    # Build lookup: uid -> sorted list of (visit_date, visit_id)
    visit_map: dict[str, list] = {}
    visit_id_by_key: dict[tuple, str] = {}   # (uid, date_str) -> visit_id (legacy retro-claim)
    for _, vrow in visits.iterrows():
        uid = vrow["Patient_UID"]
        vd  = parse_date(vrow["Visit_Date"])
        vid = str(vrow.get("Visit_ID", "")).strip()
        if uid and vd:
            visit_map.setdefault(uid, []).append((vd, vid))
            visit_id_by_key[(uid, date_to_str(vd))] = vid
    for uid in visit_map:
        visit_map[uid].sort(key=lambda t: (t[0], t[1]))

    presc_latest_day = _prescribing_day_bounds(fu_ledger, visit_map)

    # Terminal statuses — never re-evaluated
    TERMINAL = {"Returned Early", "Returned On Time", "Returned Late"}

    # ── Pass 1: legacy terminal rows get their Matched_Visit_ID backfilled ───
    for idx, row in fu_ledger.iterrows():
        if row.get("Followup_Status") not in TERMINAL:
            continue
        vid = str(row.get("Matched_Visit_ID", "")).strip()
        if not vid:
            uid = str(row.get("Patient_UID_Resolved", "")).strip()
            mdate = str(row.get("Matched_Return_Visit_Date", "")).strip()
            vid = visit_id_by_key.get((uid, mdate), "")
            if vid:
                fu_ledger.at[idx, "Matched_Visit_ID"] = vid

    # ── Pass 2: identity-problem rows (status fixed, but they can expire) ────
    pending_idx = []
    for idx, row in fu_ledger.iterrows():
        if row.get("Followup_Status") in TERMINAL:
            continue

        due_date = parse_date(row.get("Due_Date"))
        conf = row.get("Identity_Confidence", "")

        if conf in ("Invalid Mobile", "Unresolved", "Ambiguous"):
            if due_date and (today - due_date).days > EXPIRY_DAYS:
                fu_ledger.at[idx, "Followup_Status"]   = "Expired Unresolved"
                fu_ledger.at[idx, "Days_Overdue"]      = str((today - due_date).days)
                fu_ledger.at[idx, "Suggested_Action"]  = "Archived (>%d days)" % EXPIRY_DAYS
            elif conf == "Invalid Mobile":
                fu_ledger.at[idx, "Followup_Status"]   = "Invalid Mobile / No Contact"
                fu_ledger.at[idx, "Suggested_Action"]  = "Correct mobile number in Docterz"
            elif conf == "Unresolved":
                fu_ledger.at[idx, "Followup_Status"]   = "Identity Unresolved"
                fu_ledger.at[idx, "Suggested_Action"]  = "Check registration / mobile in Docterz"
            else:
                fu_ledger.at[idx, "Followup_Status"]   = "Ambiguous Mobile"
                fu_ledger.at[idx, "Suggested_Action"]  = "Verify patient identity before contacting"
            fu_ledger.at[idx, "Last_Status_Update"] = processed_on
            continue

        if not due_date:
            fu_ledger.at[idx, "Followup_Status"]    = "Invalid Due Date"
            fu_ledger.at[idx, "Last_Status_Update"] = processed_on
            continue

        pending_idx.append(idx)

    # ── Pass 3: each pending follow-up takes its earliest qualifying visit ───
    for idx in pending_idx:
        row      = fu_ledger.loc[idx]
        uid      = str(row.get("Patient_UID_Resolved", "")).strip()
        due_date = parse_date(row.get("Due_Date"))
        log_date = parse_date(row.get("Followup_Log_Date"))

        # the earliest visit that may count, and the prescribing visit to skip
        floor = None          # visits must be strictly AFTER this day
        start = None          # ...and on or after this day
        if log_date:
            try:
                aid = int(str(row.get("Appointment_ID", "")).strip())
            except ValueError:
                aid = None
            p_day = presc_latest_day(aid)
            presc = []
            if p_day is not None and p_day < due_date and uid in visit_map:
                presc = [vd for vd, _ in visit_map[uid]
                         if due_date - timedelta(days=_ANCHOR_WINDOW_DAYS) <= vd <= p_day]
            if presc:
                # skip the prescribing visit (the latest on or before its day)
                floor = presc[-1]
                advised = (due_date - floor).days
                start = due_date - timedelta(days=max(1, int(advised * EARLY_RETURN_SHARE)))
            else:
                # prescribing day unknown, or no visit of this patient on or
                # before it: the old rule (visit after the log date) stands
                floor = log_date if not COUNT_LOG_DATE_VISIT_AS_RETURN \
                        else log_date - timedelta(days=1)
                start = None
        else:
            start = due_date - timedelta(days=30)

        matched_visit = None
        matched_vid   = ""
        if uid and uid in visit_map:
            for vd, vid in visit_map[uid]:
                if floor is not None and not (vd > floor):
                    continue
                if start is not None and vd < start:
                    continue
                matched_visit, matched_vid = vd, vid
                break

        if matched_visit:
            delay = (matched_visit - due_date).days
            fu_ledger.at[idx, "Matched_Return_Visit_Date"] = date_to_str(matched_visit)
            fu_ledger.at[idx, "Matched_Visit_ID"]          = matched_vid
            fu_ledger.at[idx, "Return_Delay_Days"]         = str(delay)
            fu_ledger.at[idx, "Days_Overdue"]              = ""
            if delay < 0:
                status = "Returned Early"
            elif delay <= 2:
                status = "Returned On Time"
            else:
                status = "Returned Late"
            fu_ledger.at[idx, "Followup_Status"]  = status
            fu_ledger.at[idx, "Suggested_Action"] = "—"
        else:
            days_overdue = (today - due_date).days
            fu_ledger.at[idx, "Days_Overdue"]              = str(days_overdue)
            fu_ledger.at[idx, "Matched_Return_Visit_Date"] = ""
            fu_ledger.at[idx, "Matched_Visit_ID"]          = ""
            fu_ledger.at[idx, "Return_Delay_Days"]         = ""

            if days_overdue < 0:
                status = "Not Due"
                action = "—"
            elif days_overdue == 0:
                status = "Due Today"
                action = "WhatsApp reminder"
            elif days_overdue <= 3:
                status = "Grace Period"
                action = "WhatsApp reminder"
            elif days_overdue <= 10:
                status = "Actionable Missed Follow-Up"
                action = "Call / WhatsApp"
            elif days_overdue <= EXPIRY_DAYS:
                status = "Probable Dropout"
                action = "Call and mark outcome"
            else:
                status = "Expired Unresolved"
                action = "Archived (>%d days)" % EXPIRY_DAYS
            fu_ledger.at[idx, "Followup_Status"]  = status
            fu_ledger.at[idx, "Suggested_Action"] = action

        fu_ledger.at[idx, "Last_Status_Update"] = processed_on

    return fu_ledger

