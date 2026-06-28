# app.py PATCH — Revenue Upload + Review Queue + Last-Uploaded Banner
**Dr. Manoj Agarwal Clinic · Follow-Up Tracker · Session 15**

This patch adds the periodic external-revenue ingest (Labmate/Marg → patient ledger)
to the live tracker, with a **preview→confirm** flow, a **held queue** for the
remainder (fed only after your manual check), and a **last-uploaded banner**.

It touches your 1,808-line `app.py` **only by ADDING** — no existing line is edited.
The heavy logic lives in the standalone, already-proven `revenue_ingest.py`.

---

## STEP 0 — files into the tracker folder

Put **`revenue_ingest.py`** in the same folder as `app.py` / `revenue.py`
(`…/followup_tracker/`). Nothing else moves.

## STEP 1 — verify before touching app.py

In the tracker folder (the "black window"):
```
python3 -c "import revenue_ingest; print('revenue_ingest OK')"
```
Expect `revenue_ingest OK`. (If it errors, stop — do not edit app.py yet.)

## STEP 2 — paste BLOCK A  (the routes + screens)

Open `app.py`. Scroll to the **very bottom**. Find this line (near line 1802):
```python
if __name__ == "__main__":
```
**Paste BLOCK A on the empty line JUST ABOVE it** (so the new code sits above
`if __name__`, at the same left margin — no indentation).

## STEP 3 — paste BLOCK B  (the home-page banner + menu link)  — OPTIONAL but recommended

This shows the "Revenue data as of __" banner on the home page and adds a menu link.
Two tiny insertions, described inside BLOCK B. If you skip this, the feature still
works — you'd just reach it by typing `/revenue/upload`.

## STEP 4 — verify + restart
```
python3 -m py_compile app.py        # must print nothing (no error)
```
Then restart the tracker the usual way (close + `2_START_TRACKER.bat`, or your
service restart). Visit `/revenue/upload` (logged in as admin).

---

# ════════════════════════ BLOCK A ════════════════════════
# Paste everything between the lines, just ABOVE `if __name__ == "__main__":`

```python
# ─────────────────────────────────────────────────────────────────────────────
# REVENUE INGEST — periodic external-revenue upload (Labmate / Marg) + review queue
# Added Session 15. Heavy logic is in revenue_ingest.py (proven offline).
# Policy: only confidently-MATCHED bills hit the live ledger (so /finance counts
# them now); REVIEW + UNCLASSIFIED are HELD in revenue_pending_review.csv and only
# enter the ledger when the doctor PROMOTES them after manual checking.
# ─────────────────────────────────────────────────────────────────────────────
import revenue_ingest

# preview payloads are stashed server-side between the upload and the confirm click,
# keyed by a short token (avoids putting big row-lists in the browser form).
_REVENUE_PREVIEWS = {}

def _revenue_status():
    """Banner data for the home page + upload page (mirrors _diagnosis_status)."""
    try:
        return revenue_ingest.meta_status()
    except Exception:
        return {}


@app.route("/revenue/upload", methods=["GET"])
@admin_required
def revenue_upload_page():
    return render_template_string(REVENUE_UPLOAD_HTML, role=current_role(),
                                  rev=_revenue_status())


@app.route("/revenue/preview", methods=["POST"])
@admin_required
def revenue_preview():
    import uuid as _uuid
    f = request.files.get("revenue_file")
    if not f or not f.filename:
        flash("Please choose a Labmate (.xlsx) or Marg (.xls) file.", "error")
        return redirect(url_for("revenue_upload_page"))
    if not f.filename.lower().endswith((".xlsx", ".xls")):
        flash("Only Excel files (.xlsx / .xls) are accepted.", "error")
        return redirect(url_for("revenue_upload_page"))
    save_path = str(UPLOAD_DIR / secure_filename(f.filename))
    f.save(save_path)
    try:
        prev = revenue_ingest.preview(save_path)
    except Exception as e:
        import traceback; traceback.print_exc()
        flash(f"Could not read that file: {e}", "error")
        return redirect(url_for("revenue_upload_page"))
    token = _uuid.uuid4().hex[:12]
    _REVENUE_PREVIEWS[token] = prev
    # keep the stash small — drop anything but the last few
    if len(_REVENUE_PREVIEWS) > 8:
        for k in list(_REVENUE_PREVIEWS)[:-8]:
            _REVENUE_PREVIEWS.pop(k, None)
    return render_template_string(REVENUE_PREVIEW_HTML, role=current_role(),
                                  p=prev, token=token)


@app.route("/revenue/commit", methods=["POST"])
@admin_required
def revenue_commit():
    token = request.form.get("token", "")
    prev = _REVENUE_PREVIEWS.pop(token, None)
    if not prev:
        flash("That preview expired. Please upload the file again.", "error")
        return redirect(url_for("revenue_upload_page"))
    try:
        res = revenue_ingest.commit(prev)
        flash(f"✅ Added to /finance: {res['matched_written']} matched bills. "
              f"Held for your review: {res['held_written']} "
              f"(skipped {res['matched_skipped_dup']} already-loaded).", "success")
    except Exception as e:
        import traceback; traceback.print_exc()
        flash(f"Error writing: {e}", "error")
    return redirect(url_for("revenue_review_page"))


@app.route("/revenue/review", methods=["GET"])
@admin_required
def revenue_review_page():
    pend = revenue_ingest.load_pending()
    rows = []
    for _, r in pend.iterrows():
        cand_uids = [x for x in str(r.get("Cand_UIDs", "")).split(";") if x]
        cand_cids = [x for x in str(r.get("Cand_Clinic_Ids", "")).split(";") if x]
        cand_nms  = [x for x in str(r.get("Cand_Names", "")).split(";") if x]
        cands = []
        for i in range(len(cand_uids)):
            cands.append({"uid": cand_uids[i],
                          "clinic_id": cand_cids[i] if i < len(cand_cids) else "",
                          "name": cand_nms[i] if i < len(cand_nms) else ""})
        rows.append({
            "rid": r["Revenue_ID"], "date": r["Date"], "net": r["Net"],
            "source": r["Source"], "status": r.get("Match_Status", ""),
            "bill_name": r.get("Bill_Name", ""), "bill_mobile": r.get("Bill_Mobile", ""),
            "bill_cid": r.get("Bill_Clinic_Id", ""), "cands": cands,
        })
    return render_template_string(REVENUE_REVIEW_HTML, role=current_role(), rows=rows)


@app.route("/revenue/promote", methods=["POST"])
@admin_required
def revenue_promote():
    rid = request.form.get("rid", "").strip()
    uid = request.form.get("uid", "").strip()
    clinic_id = request.form.get("clinic_id", "").strip()
    name = request.form.get("name", "").strip()
    mobile = request.form.get("mobile", "").strip()
    if not rid or not uid:
        flash("Pick a patient to attribute this bill to.", "error")
        return redirect(url_for("revenue_review_page"))
    try:
        res = revenue_ingest.promote(rid, uid, clinic_id, name, mobile)
        if res.get("ok"):
            flash(f"✅ ₹{res['net']:.0f} attributed to {res['name']} and added to /finance.", "success")
        else:
            flash(res.get("message", "Could not promote."), "error")
    except Exception as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("revenue_review_page"))


@app.route("/revenue/lookup")
@admin_required
def revenue_lookup():
    """For the review screen's manual search (when none of the candidates is right)."""
    from flask import jsonify
    import revenue as _rev
    hit = _rev.lookup_patient(request.args.get("q", ""))
    if hit and hit.get("uid"):
        return jsonify({"found": True, "uid": hit["uid"], "clinic_id": hit["clinic_id"],
                        "name": hit["name"], "mobile": hit["mobile"]})
    msg = hit.get("ambiguous") if hit else "No patient found."
    return jsonify({"found": False, "message": msg or "No patient found."})


REVENUE_UPLOAD_HTML = """
<!DOCTYPE html><html><head><title>Revenue Upload</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">Dr. Manoj Agarwal Clinic <small>External Revenue — Pharmacy &amp; Lab Upload</small></div>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}<div class="alert alert-{{ cat }}">{{ msg }}</div>{% endfor %}
  {% endwith %}

  {% if rev.as_of_date or rev.ingested_on %}
  <div class="card">
    <h2>📊 Last Revenue Upload</h2>
    <div style="background:{{ '#FEF3C7' if rev.stale else '#ECFDF5' }};
      border:1px solid {{ '#F59E0B' if rev.stale else '#A7F3D0' }};
      border-radius:8px; padding:12px 14px; font-size:13px;">
      <div style="font-size:15px; font-weight:700; color:{{ '#92400E' if rev.stale else '#065F46' }};">
        Revenue data as of: {{ rev.as_of_label }}
        {% if rev.stale %}&nbsp;·&nbsp;⚠️ {{ rev.age_days }} days old — time for a fresh export{% endif %}
      </div>
      <div style="color:#4B5563; margin-top:5px;">
        Last absorbed {{ rev.ingested_on or '—' }} from <strong>{{ rev.source_file }}</strong>
        ({{ rev.kind }}).<br>
        ₹{{ '{:,.0f}'.format(rev.matched_net) }} matched into /finance ·
        ₹{{ '{:,.0f}'.format(rev.held_net) }} held that run.<br>
        <strong>{{ rev.pending_count }}</strong> bills (₹{{ '{:,.0f}'.format(rev.pending_net) }})
        currently waiting in <a href="/revenue/review">Review &amp; Promote</a>.
      </div>
    </div>
  </div>
  {% endif %}

  <div class="card">
    <h2>⬆️ Upload a revenue file</h2>
    <p class="hint" style="margin-bottom:14px;">
      Accepts the <strong>Labmate</strong> pathology export (.xlsx) or the
      <strong>Marg</strong> pharmacy export (.xls). You'll see a <em>preview</em>
      first — nothing is saved until you confirm. Only confident matches go into
      Finance; the rest wait for your check.
    </p>
    <form method="POST" action="/revenue/preview" enctype="multipart/form-data">
      <label>Revenue file (.xlsx / .xls)</label>
      <input type="file" name="revenue_file" accept=".xlsx,.xls" required
        style="width:100%; padding:9px; border:1.5px solid #D1D5DB; border-radius:7px;
        margin-bottom:16px; background:#fafafa;">
      <button class="btn" type="submit">Preview match</button>
    </form>
  </div>

  <div class="nav-links"><a href="/">← Home</a> <a href="/revenue/review">🔎 Review &amp; Promote</a> <a href="/finance">💰 Finance</a></div>
</div></body></html>
"""

REVENUE_PREVIEW_HTML = """
<!DOCTYPE html><html><head><title>Revenue Preview</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">Dr. Manoj Agarwal Clinic <small>Revenue Upload — Preview</small></div>
<div class="container">
  <div class="card">
    <h2>🔍 Preview — {{ p.source_file }}</h2>
    <p class="hint">{{ p.kind }} · as of {{ p.as_of }} · window ±{{ p.window_days }} days ·
      {{ p.bills_in }} bills · total ₹{{ '{:,.0f}'.format(p.net_in) }}</p>

    <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:8px; padding:12px 14px; margin:10px 0;">
      <div style="font-weight:700; color:#065F46; font-size:15px;">
        ✅ Will be ADDED to Finance now:
        {{ p.new_matched_count }} bills · ₹{{ '{:,.0f}'.format(p.new_matched_net) }}
      </div>
      {% if p.already_in_ledger %}<div style="color:#4B5563; font-size:12px;">({{ p.already_in_ledger }} matched bills already in the ledger — will be skipped.)</div>{% endif %}
    </div>

    <div style="background:#FEF3C7; border:1px solid #F59E0B; border-radius:8px; padding:12px 14px; margin:10px 0;">
      <div style="font-weight:700; color:#92400E; font-size:15px;">
        ⏸️ HELD for your review (NOT counted yet):
        {{ p.buckets.review.count + p.buckets.unclassified.count }} bills ·
        ₹{{ '{:,.0f}'.format(p.buckets.review.net + p.buckets.unclassified.net) }}
      </div>
      <div style="color:#4B5563; font-size:12px;">
        {{ p.buckets.review.count }} ambiguous (2+ patients) ·
        {{ p.buckets.unclassified.count }} no-match. You promote these after checking.
      </div>
    </div>

    <table style="width:100%; border-collapse:collapse; font-size:13px; margin-top:8px;">
      <tr style="text-align:left; color:#6B7280;"><th>Match type</th><th>Bills</th><th style="text-align:right;">₹</th></tr>
      {% for k, v in p.by_breakdown.items() %}
      <tr style="border-top:1px solid #f1f1f1;"><td>{{ k }}</td><td>{{ v.count }}</td>
        <td style="text-align:right;">₹{{ '{:,.0f}'.format(v.net) }}</td></tr>
      {% endfor %}
    </table>

    <form method="POST" action="/revenue/commit" style="margin-top:16px;">
      <input type="hidden" name="token" value="{{ token }}">
      <button class="btn btn-green" type="submit">Confirm &amp; append matched to Finance</button>
    </form>
    <p class="hint" style="margin-top:8px;">No rupee is dropped: ₹{{ '{:,.0f}'.format(p.net_in) }} in =
      matched + held. Confirm only writes matched to /finance; held money waits in Review.</p>
  </div>
  <div class="nav-links"><a href="/revenue/upload">← Upload another</a> <a href="/">Home</a></div>
</div></body></html>
"""

REVENUE_REVIEW_HTML = """
<!DOCTYPE html><html><head><title>Revenue Review</title>
""" + BASE_STYLE + """
</head><body>
<div class="header">Dr. Manoj Agarwal Clinic <small>Revenue — Review &amp; Promote held bills</small></div>
<div class="container">
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% for cat, msg in messages %}<div class="alert alert-{{ cat }}">{{ msg }}</div>{% endfor %}
  {% endwith %}

  <div class="card">
    <h2>🔎 Held bills awaiting your decision</h2>
    <p class="hint">These were NOT auto-attributed (ambiguous name, or no patient found).
      They are NOT in /finance yet. Pick the right patient and promote — that adds the
      money to Finance under that patient. Nothing here is counted until you do.</p>
    {% if not rows %}
      <p style="color:#065F46; font-weight:600; padding:10px 0;">✅ Nothing pending. All clear.</p>
    {% endif %}
  </div>

  {% for r in rows %}
  <div class="card">
    <div style="display:flex; justify-content:space-between; align-items:baseline;">
      <div><strong>{{ r.bill_name or '(no name)' }}</strong>
        <span style="color:#9aa; font-size:12px;">· {{ r.date }} ·
        {{ r.source }}{% if r.status=='unclassified' %} · no match found{% endif %}</span></div>
      <div style="font-weight:700; color:#166534;">₹{{ r.net }}</div>
    </div>
    {% if r.bill_mobile or r.bill_cid %}<div class="hint">on bill: mobile {{ r.bill_mobile or '—' }} · Clinic ID {{ r.bill_cid or '—' }}</div>{% endif %}

    {% if r.cands %}
    <div style="margin-top:8px; font-size:13px; color:#6B7280;">Candidates:</div>
    {% for c in r.cands %}
    <form method="POST" action="/revenue/promote" style="display:flex; gap:8px; align-items:center;
      padding:6px 0; border-bottom:1px solid #f3f3f3;">
      <input type="hidden" name="rid" value="{{ r.rid }}">
      <input type="hidden" name="uid" value="{{ c.uid }}">
      <input type="hidden" name="clinic_id" value="{{ c.clinic_id }}">
      <input type="hidden" name="name" value="{{ c.name }}">
      <span style="flex:1;">{{ c.name }} <span style="color:#9aa;">(Clinic ID {{ c.clinic_id }})</span></span>
      <button class="btn btn-green" style="width:auto; padding:7px 14px;" type="submit">Promote ₹{{ r.net }} → this patient</button>
    </form>
    {% endfor %}
    {% endif %}

    <div style="margin-top:10px; font-size:13px;">
      <span style="color:#6B7280;">None of these? Search by Clinic ID / mobile:</span>
      <div style="display:flex; gap:6px; margin-top:4px;">
        <input type="text" id="q_{{ r.rid }}" placeholder="Clinic ID or mobile" style="flex:1;">
        <button class="btn" style="width:auto; padding:7px 12px;" onclick="findFor('{{ r.rid }}','{{ r.net }}')">Find</button>
      </div>
      <form method="POST" action="/revenue/promote" id="mf_{{ r.rid }}" style="display:none; margin-top:6px;">
        <input type="hidden" name="rid" value="{{ r.rid }}">
        <input type="hidden" name="uid" id="muid_{{ r.rid }}">
        <input type="hidden" name="clinic_id" id="mcid_{{ r.rid }}">
        <input type="hidden" name="name" id="mname_{{ r.rid }}">
        <input type="hidden" name="mobile" id="mmob_{{ r.rid }}">
        <button class="btn btn-green" type="submit" id="mbtn_{{ r.rid }}"></button>
      </form>
      <div id="msg_{{ r.rid }}" class="hint"></div>
    </div>
  </div>
  {% endfor %}

  <div class="nav-links"><a href="/revenue/upload">← Upload</a> <a href="/finance">💰 Finance</a> <a href="/">Home</a></div>
</div>
<script>
async function findFor(rid, net){
  var q = document.getElementById('q_'+rid).value.trim();
  var msg = document.getElementById('msg_'+rid);
  if(!q){ msg.textContent='Enter a Clinic ID or mobile.'; return; }
  msg.style.color='#6B7280'; msg.textContent='Searching…';
  try{
    var res = await fetch('/revenue/lookup?q='+encodeURIComponent(q));
    var d = await res.json();
    if(d.found){
      document.getElementById('muid_'+rid).value=d.uid;
      document.getElementById('mcid_'+rid).value=d.clinic_id;
      document.getElementById('mname_'+rid).value=d.name;
      document.getElementById('mmob_'+rid).value=d.mobile;
      document.getElementById('mbtn_'+rid).textContent='Promote ₹'+net+' → '+d.name;
      document.getElementById('mf_'+rid).style.display='block';
      msg.style.color='#065F46'; msg.textContent='Found: '+d.name;
    } else { msg.style.color='#B91C1C'; msg.textContent=d.message||'Not found.'; }
  }catch(e){ msg.style.color='#B91C1C'; msg.textContent='Lookup failed.'; }
}
</script>
</body></html>
"""
```

# ════════════════════════ END BLOCK A ════════════════════════

---

# ════════════════════════ BLOCK B (optional) ════════════════════════
# Home-page banner + menu link. Two tiny ADD-ONLY insertions in INDEX_HTML.

## B1 — menu link
Find this line in `app.py` (around line 675, inside INDEX_HTML's menu):
```html
    {% if role == 'admin' %}<a href="/finance">💰 Finance Dashboard</a>{% endif %}
```
**Add this line right after it:**
```html
    {% if role == 'admin' %}<a href="/revenue/upload">📊 Revenue Upload</a>{% endif %}
```

## B2 — home banner (optional)
If you want the "Revenue data as of __" box on the home page too, you'd pass `rev`
into the index render. Simplest: it already shows on `/revenue/upload`. Skip B2
unless you specifically want it on the home screen — the upload page banner covers it.

# ════════════════════════ END BLOCK B ════════════════════════

---

## What you get

- **`/revenue/upload`** — upload a Labmate/Marg file → **preview** (matched vs held, ₹)
  → **Confirm** appends only matched to the live ledger `/finance` reads.
- **`/revenue/review`** — the held queue: each bill with its candidate patients and a
  one-tap **Promote** (or search any patient). Promoting adds that bill's money to
  Finance under the chosen patient and removes it from the queue.
- **Last-uploaded banner** — green/amber "Revenue data as of __", source file, ₹ matched,
  ₹ held, and how many bills are still pending review.
- **Safe re-uploads** — the same file won't double-count (de-duped).
- **The backlog is just your first upload** through this path. Future months: same button.

## Proven before delivery
`revenue_ingest.py` was tested inside a copy of your tracker against the real ledger:
matched ₹2,58,560 landed in `/finance`, held ₹91,570 stayed out, re-upload added 0,
and a promote correctly moved one held bill into Finance. The real ledger was untouched.
