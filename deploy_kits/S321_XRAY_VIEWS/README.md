# S321_XRAY_VIEWS — the buttons, the views, and the prices

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S321_XRAY_VIEWS/install_S321_XRAY_VIEWS.sh
```

## 1 · Why Approve said "page not accessible"

Every form on the page carries a **relative** action — `action="status"`, `action="rename"`,
`action="price"`, `action="add"`. The page is served at `/finance/clinic/sheets` **without a trailing
slash** (which is what the portal tile links to), and a browser resolves a relative action against the
*directory* of the current URL — so it drops the last segment:

```
page  /finance/clinic/sheets   +  action "status"   ->   POST /finance/clinic/status   (404)
```

With a trailing slash it would have worked, which is exactly why the S316 walk missed it: **the walk
posted to the routes by their full URLs and never did what a browser does.**

The fix is one line — `<base href="/finance/clinic/sheets/">`, taken from the blueprint's own
`url_prefix` so the two cannot disagree. It repairs every form at once, including any added later.

## 2 · The names and the prices, from his own message

Every X-ray now carries its views, and **chest becomes two studies** because he described two:

| his rule | rows |
|---|---|
| two views — 500 | knee, LS, K/S, ankle, foot, C-spine, shoulder, elbow, leg, hand, toes, D-spine, thumb, forearm, dorsolumbar |
| single view — 300 | clavicle · **Chest AP view** · **Chest PA view** |
| single view on 11 x 14 — 400 | pelvis both hips |
| three views on 11 x 14 — 800 | wrist (AP, lateral & oblique) |

He edits any of them on the page. **A row he has already changed himself is never overwritten** — the
update only touches rows still marked as the seed's own, so his work always wins. Nothing is deleted,
no procedure row is touched, and the whole table is dumped to
`owner_service_before_S321_<stamp>.sql` before a single row changes.

The page also now states the rule itself, so he need not hold it in his head while editing.

## 3 · Proof

`walk_s321.py` — **23 checks** on a copy of the live module and a scratch database. It **renders the
real page through Flask**, reads every `<form action>` out of the HTML, resolves each one the way a
browser does (against the page URL and its `<base>` tag), and then **POSTs to the address that comes
out**: no 404, no 405, Approve redirects back, and the row really is approved afterwards.

Three negative controls, all on the **unpatched** module: no base tag, Approve resolving to
`/finance/clinic/status`, and that address returning **404 — the owner's own error, reproduced.**

Plus: every price and name asserted, chest proved to be two rows, the procedure row untouched, a
second run says ALREADY, and a row edited by hand survives the update.
