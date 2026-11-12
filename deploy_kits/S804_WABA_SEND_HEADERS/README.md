# S804_WABA_SEND_HEADERS — the older approve-and-send page's sender reaches MyOperator the way the Inbox now does (F-1294)

**What was shown on 12-Nov-2026 (S802, 15:35 IST, MyOperator's live gateway, nothing sent):** their authorizer answers HTTP 500
when the company header arrives named `X-Myop-Company-Id` and answers properly when it arrives as `X-MYOP-COMPANY-ID`. Python's
urllib re-cases header names on the wire; `http.client` sends them as written. S802 moved the Inbox (`portal_inbox.py`) and the
portal's template sender (`portal_wa.py`). **`/root/wa/waba.py` was left on urllib** — it is the send arm behind the older
approve-and-send page (`wa_approve.py`, service `wa-approve`, port 8101) and is imported by `waba_diag.py`,
`waba_certainty.py` and `plan_followups_from_xlsx.py`.

**The change — one request per try, nothing else:**
- `/root/wa/waba.py` 031b4642 → 82f3503b — `send_template`: the request goes through `http.client`, header names as written.
  The same result dict (`ok, status_code, message_id, conversation_id, code, message, raw`), the same stop codes
  (`WabaFatalError` on an empty wallet and the three "disabled" codes), the same ONE retry after 3 seconds on a 5xx or on no
  answer **only when the request could not be connected or sent** (what urllib raised as `URLError`). **Once the request has
  gone out it is never sent again by this function**: a late answer, a dropped connection or a cut-short body is raised to the
  caller after ONE request, exactly as before (MyOperator may already have accepted it — a retry there would be a second
  message to a patient; the cold review caught the first build doing that). One small difference: a 3xx answer is reported,
  not followed.
- Not changed, and noted for the sending build: when such an exception stops the approve page's batch, the page writes its
  log rows only at the end of the batch — rows already sent are then not on its log.

**Proved before it is placed** — `prove_s804.py`, nothing sent. Every request uses a **fresh made-up key** (its proper answer is
401/403): the old road, `http.client` as written, `http.client` with the company header named as urllib sends it; then the
changed `send_template` with fresh made-up keys, and once with the real key and an EMPTY number and EMPTY text (the request
S802 made on this box; the proper answer is 400). Placed only on **PROVEN**. NOT-SHOWN or FAILED → nothing is changed.
After placing, the installed sender is checked once more (real key, empty number → 400), else the file goes back.
The account's settings are read by key from the box's own `/root/wa/.env`, inside the program; nothing of it is printed.

**The approve page's door is read before anything is placed** (its answer without a key) and must answer the same after the
restart of `wa-approve`; if the service is not running it is left so.

**The kit carries no copy of `waba.py`** (its opening notes hold the account's IDs — F-185, F-1293): the installer makes it on
the box with `make_s804.py` from the live bytes (the replaced block checked by its md5) and checks the result against the pin.

**Walk** 32/32 against a stand-in gateway on the same machine that behaves as the live one did in S802's proof; the CONTROL
red on the live file (12 of 30). The installer rehearsed on a stand-in root: DRY · the old road not refused → NOT-SHOWN,
nothing changed · everything refused → FAILED, nothing changed · install · ALREADY · undo byte-identical · red journal after
placing → the file back · the door answering differently after the restart → the file back · the installed sender refused
after placing (three tries) → the file back · a kit file altered → stopped · a live file not the pinned one → stopped · the service not
running → placed, not restarted · another install running → stopped.

**Nothing is sent to any patient by this kit, and it switches no sending on.** The `wa-approve` service is restarted: do not
run the install while a send from the approve page is going on.

**Cold review (a second reader, S439):** NOT SAFE on the first build — one must-fix (the retry after the request had gone out),
built; its should-fixes built (the stand-in checks the path and the body; the installed check tries three times; the restart
note) and its nits (the scratch folder checked; `WABA_DEBUG` cleared in the proof; a query string kept).

**Install** (after the publish), one line on the server:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s804kit && cp -rp /root/deploy/repo/deploy_kits/S804_WABA_SEND_HEADERS /tmp/s804kit && bash /tmp/s804kit/install_S804_WABA_SEND_HEADERS.sh
```
Undo: `bash /tmp/s804kit/install_S804_WABA_SEND_HEADERS.sh --undo`.
