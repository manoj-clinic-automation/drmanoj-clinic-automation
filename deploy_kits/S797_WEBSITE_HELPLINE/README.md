# S797_WEBSITE_HELPLINE — the helpline number first on the website (the parent, S435, 12-Nov-2026)

The owner, 12-Nov 08:08 / 08:21 IST: the helpline (IVR) number is to be made known everywhere so that patients recognise the clinic's calls, with the old number beside it — "Do 2 and 3".

ONE new file on the website, made at install from `clinic-helpline-number.php.tpl`: `wp-content/mu-plugins/clinic-helpline-number.php` (a must-use plugin: WordPress loads it by itself). On every public page: each call link (`tel:`) to the old number dials the helpline; the old number as shown reads "helpline, old number"; WhatsApp links, scripts, styles and attributes are untouched; admin, feeds, REST, AJAX and the Elementor editor are left alone. Nothing in the website's database is changed; no theme or plugin file is edited. Undo = the file is moved out.

The two numbers are given on the server line (HELPLINE=… OLD=…) — no number is kept in the repository (F-185); the walk uses made-up digits.

The installer: SUMS · the numbers' shape · PHP's own check of the made file · the walk (22 checks) and its control · today's home page fetched and put through the file (counts printed; DRY=1 stops here) · the file placed with the website's own ownership · the live home page fetched again — status 200, no call link to the old number left, the helpline there, WhatsApp links as before, size sane — or the file is taken out again.

Found on 12-Nov (read in the browser): theme gerow (header phone), Elementor page 131 (two call widgets), footer template 111 (icon list, WhatsApp), the bottom menu's "Call Us"; 5 call links on the home page, the helpline nowhere.
