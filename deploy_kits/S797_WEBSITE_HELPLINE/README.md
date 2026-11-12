# S797_WEBSITE_HELPLINE — the helpline number first on the website (the parent, S435, 12-Nov-2026)

The owner, 12-Nov 08:08 / 08:21 IST: the helpline (IVR) number is to be made known everywhere so that patients recognise the clinic's calls, with the old number beside it — "Do 2 and 3".

ONE new file on the website, made at install from `clinic-helpline-number.php.tpl`: `wp-content/mu-plugins/clinic-helpline-number.php` (a must-use plugin: WordPress loads it by itself). On every public page: each call link (`tel:`) to the old number dials the helpline; the old number as shown reads "helpline, old number"; WhatsApp links, scripts, styles and attributes are untouched; admin, feeds, REST, AJAX and the Elementor editor are left alone. Nothing in the website's database is changed; no theme or plugin file is edited. Undo = the file is moved out.

The two numbers are given on the server line (HELPLINE=… OLD=…) — no number is kept in the repository (F-185); the walk uses made-up digits.

The installer: SUMS · the numbers' shape · PHP's own check of the made file · the walk (23 checks) and its control · today's home page fetched and put through the file (counts printed; DRY=1 stops here) · the file placed with the website's own ownership · the live home page fetched again — status 200, no call link to the old number left, the helpline there, WhatsApp links as before, size sane — or the file is taken out again.

Found on 12-Nov (read in the browser): theme gerow (header phone), Elementor page 131 (two call widgets), footer template 111 (icon list, WhatsApp), the bottom menu's "Call Us"; 5 call links on the home page, the helpline nowhere.

v2 (09:1x IST 12-Nov): no `php -l` — the server's PHP crashed on it; every candidate PHP runs with -n and counts only if it runs the whole walk; with none, the live check alone decides.
v3 (09:2x IST): the web server (LiteSpeed) keeps a cached copy of every page for 7 days and went on serving the old one to visitors — the file now answers a one-off key (made at install, kept only in the file on the server) with the server's own purge header; the installer sends it, also tries the cache plugin's own command, then reads the home page the way every visitor gets it and says which it found. A run over the earlier file replaces it (the earlier copy kept in /root/s797_prev_*.txt).
