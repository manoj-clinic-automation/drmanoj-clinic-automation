# S353_XRAY_FILMS — films per study, the owner's ruling

**The owner, 20-Sep-2026:** *"Usually the AP and lateral are done on a single film … The knee studies is a unique
x-ray where both knee AP standing is taken and both knee lateral view is taken. So that is two films. Record that as
an exception."* Asked because the X-ray test page (after S351) read a Knee-studies patient's two photos as
*"2 files, 1 X-ray on the slip — numbered, not guessed"*.

So: a two-view study is **one film, one photo**; **Knee studies (K/S)** is **two films** — film 1 both knees AP
standing, film 2 both knees lateral. `study_films()` expands a study into its films (`TWO_FILM_STUDIES`, one
entry, one line to widen if he ever names another) and the day list counts films. That patient's two photos now
read MATCHED, named *… — AP standing* and *… — Lateral*. Read-only test page; nothing filed, renamed or moved.

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S353_XRAY_FILMS/install_S353_XRAY_FILMS.sh
```

Pins: `records.py` `4c2f38b9…` (S351) → `07ec9b41cb5bbded215dcd1b1916e3d0` (full file; `make_s353.py` = the one
anchored edit) · `finance_app.py` `29819879…` (S349) checked, unchanged. Walk: 40 checks (S351's 32 re-proven +
the films rule), own rows only (F-581), the LIVE S351 `records.py` as the negative control. Restarts clinic-finance.
Touches no Sanjeevni file, none of `finance_app.py` / `portal.py` / `tile_grants.json`.
