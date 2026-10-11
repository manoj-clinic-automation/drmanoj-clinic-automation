<?php
/* save/index.php -- kit S529 (session 305, 11-Oct-2026). The clinic's "save contact" page, opened by
   https://save.dr-manoj.in (a GoDaddy forward to https://drmanojagarwal.com/save/).
   ONE TAP: on Android the button opens the phone's own new-contact form, already filled in (name and numbers);
   on iPhone it opens the contact card itself ("Create New Contact"). ?card=1 serves the card (text/vcard).
   The card is clinic.vcf beside this file, placed by the installer from the card the clinic's contact page
   already uses. THIS FILE HOLDS NO NUMBER: the numbers are read from that card when the page is opened.
   No input is stored, no cookie is set, nothing is logged here. */
$card_file = __DIR__ . '/clinic.vcf';
$vcf = @file_get_contents($card_file);
if ($vcf === false || strpos($vcf, 'BEGIN:VCARD') === false) {
    header('Location: https://contact.dr-manoj.in', true, 302);   // the clinic's contact page still works
    exit;
}
if (isset($_GET['card'])) {
    header('Content-Type: text/vcard; charset=utf-8');
    header('Content-Disposition: inline; filename="DrManojAgarwalClinic.vcf"');
    header('Cache-Control: no-cache');
    echo $vcf;
    exit;
}
// unfold folded vCard lines (RFC 6350: a line starting with a space continues the one before)
$text = preg_replace("/\r?\n[ \t]/", '', $vcf);
$name = 'Dr Manoj Agarwal Clinic';
$tels = array();
foreach (preg_split("/\r?\n/", $text) as $line) {
    if (preg_match('/^(?:item\d+\.)?FN[^:]*:(.+)$/i', $line, $m)) { $name = trim($m[1]); }
    if (preg_match('/^(?:item\d+\.)?TEL[^:]*:(.+)$/i', $line, $m)) {
        $t = preg_replace('/[^0-9+]/', '', $m[1]);
        if ($t !== '' && !in_array($t, $tels, true)) { $tels[] = $t; }
    }
}
$ua = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : '';
$android = (stripos($ua, 'Android') !== false);
$card_url = 'https://drmanojagarwal.com/save/?card=1';
$intent = 'intent:#Intent;action=android.intent.action.INSERT;type=vnd.android.cursor.dir/contact'
        . ';S.name=' . rawurlencode($name)
        . (isset($tels[0]) ? ';S.phone=' . rawurlencode($tels[0]) . ';i.phone_type=3' : '')
        . (isset($tels[1]) ? ';S.secondary_phone=' . rawurlencode($tels[1]) . ';i.secondary_phone_type=3' : '')
        . ';S.browser_fallback_url=' . rawurlencode($card_url) . ';end';
$href = $android ? $intent : $card_url;
$h = function ($s) { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); };
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-cache');
header('X-LiteSpeed-Cache-Control: no-cache');   // the page differs by phone: never cached by the web server
header('Vary: User-Agent');
?><!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Save <?= $h($name) ?></title>
<style>
body{margin:0;font:17px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#f4f1ea;color:#1d2a33}
.w{max-width:440px;margin:0 auto;padding:28px 18px 40px;text-align:center}
h1{font-size:22px;margin:6px 0 4px}.s{color:#5b6670;margin:0 0 22px}
.b{display:block;background:#1f6b4a;color:#fff;text-decoration:none;font-size:20px;font-weight:650;padding:18px 14px;border-radius:14px}
.n{margin:22px 0 0;font-size:16px}.n a{color:#1f6b4a;font-weight:600;text-decoration:none;display:inline-block;margin:4px 8px}
.f{margin-top:26px;font-size:14px;color:#6b747c}.f a{color:#6b747c}
</style></head><body><div class="w">
<h1><?= $h($name) ?></h1>
<p class="s">Bareilly &middot; Advanced Orthopaedic Surgery Centre</p>
<a class="b" href="<?= $h($href) ?>">Save to my contacts</a>
<p class="n"><?php foreach ($tels as $t): ?><a href="tel:<?= $h($t) ?>">Call <?= $h($t) ?></a><?php endforeach; ?></p>
<p class="f"><a href="<?= $h($card_url) ?>">Download the contact card</a> &middot; <a href="https://contact.dr-manoj.in">All clinic links</a></p>
</div></body></html>
