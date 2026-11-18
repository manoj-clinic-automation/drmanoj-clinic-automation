# S874_HUB_SHORT_MOBILE_CALL — the day's own short · full mobiles · Call (18-Nov-2026, Sanjeevni session 482)

His words 13:41 after S869/S872: "you do need to do that correction [the 17-Oct short had to be found from the Cash card]. And also, I need full mobile numbers everywhere. Also tell me if I make these numbers tappable for calling them through the my operator IVR."

**What changes on his Hub (checker's page only; no staff screen):**
1. A day panel names its OWN short — "₹504 short — less left the drawer than came in" — with **Accept (write off)** (two-tap, as S872) and **Add an entry** (opens the S869 form). Shown once the day is approved/locked or Darpan's page has its handover; beyond the tolerance; gone once accepted (then "written off" as before) or once entries explain it.
2. Every bill and return carries the patient's **full mobile**: the patient record's, else the Call Console's patient mirror (`/root/wa/console.db`, `patients(phone10, clinic_id)`, read-only, 5-s timeout, fail-soft to the last four as before — the same read as the parent's "not in Docterz" list). The number is a `tel:` link for a phone.
3. A **📞 Call** button beside each full mobile → the portal's own click-to-call door `POST /portal/console/api/call {phone10}` (your MyOperator agent rings first, then the patient; one call per number per minute, as on the Call Console). Needs the portal sign-in in the same browser: on 401/403/redirect the page says so with the portal link. The door is the parent's, read only — nothing of the portal changes.

**Files** (this project's): `/root/finance/sanjeevni_day.py` 4359d048 → db30da9f (v1.4, whole) · `/root/finance/finance_ui/finance_approvals.html` 1f594b5f → 254c0bbf (4 anchors, `make_s874.py`). Nothing written to any table.

**Proof:** `synth_s874.py` 10/10 on the 18-Nov copy (a MADE-UP mirror — no real number; without a mirror no full number invented; 17-Oct short 504 with Accept, written off once accepted; 14-Nov no short once its entries explain it) — control on the live files red (3/5). S869's own proof 47/47 on the new files. Rehearsal 9/9 on a stand. Number gate clean.

**Install (his publish, then one line on the server):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s874kit && cp -rp /root/deploy/repo/deploy_kits/S874_HUB_SHORT_MOBILE_CALL /tmp/s874kit && bash /tmp/s874kit/install_S874_HUB_SHORT_MOBILE_CALL.sh
```
**Undo:** `bash /root/deploy/repo/deploy_kits/S874_HUB_SHORT_MOBILE_CALL/undo_s874.sh`
