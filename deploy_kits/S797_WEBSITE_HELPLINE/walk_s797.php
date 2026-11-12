<?php
/* walk_s797.php -- kit S797_WEBSITE_HELPLINE.
 *   php walk_s797.php <kit dir>                              the walk on made-up pages (made-up numbers); last line WALK OK n/n | WALK RED k of n
 *   php walk_s797.php <dir without the template> --control   must end 'CONTROL: red ...'
 *   php walk_s797.php --apply <built plugin> <in.html> <out.html>   one real page through the built plugin; prints counts only
 */
error_reporting(E_ALL);
define('ABSPATH', '/nowhere/');
$a = $argv;
if (isset($a[1]) && $a[1] === '--apply') {
    require $a[2];
    $in = file_get_contents($a[3]);
    $out = s797_helpline_html($in);
    file_put_contents($a[4], $out);
    $c = function ($re, $s) { return preg_match_all($re, $s); };
    $o = preg_quote(S797_OLD, '~'); $n = preg_quote(S797_NEW, '~');
    printf("APPLY call links to the old number %d -> %d ; call links to the helpline %d -> %d ; places the helpline is shown %d -> %d ; WhatsApp links %d -> %d ; bytes %d -> %d\n",
        $c('~href\s*=\s*["\']tel:[^"\']*' . $o . '~i', $in), $c('~href\s*=\s*["\']tel:[^"\']*' . $o . '~i', $out),
        $c('~href\s*=\s*["\']tel:\+91' . $n . '["\']~i', $in), $c('~href\s*=\s*["\']tel:\+91' . $n . '["\']~i', $out),
        $c('~>[^<]*' . $n . '[^<]*<~', $in), $c('~>[^<]*' . $n . '[^<]*<~', $out),
        $c('~(?:whatsapp\.com/send\?phone=|wa\.me/)[0-9+]*' . $o . '~i', $in), $c('~(?:whatsapp\.com/send\?phone=|wa\.me/)[0-9+]*' . $o . '~i', $out),
        strlen($in), strlen($out));
    exit(0);
}
$kit = isset($a[1]) ? $a[1] : '.';
$control = in_array('--control', $a, true);
$tpl = $kit . '/clinic-helpline-number.php.tpl';
if (!is_readable($tpl)) {
    echo $control ? "CONTROL: red (no template) -- the walk cannot pass without the file\n" : "WALK RED: the template is not there\n";
    exit($control ? 0 : 1);
}
if ($control) { echo "CONTROL: NOT red -- the template was found where none should be\n"; exit(1); }
$OLD = str_repeat('9', 10); $NEW = str_repeat('8', 10);          // made-up: no real number in the kit
$src = str_replace(array('@@OLD@@', '@@NEW@@'), array($OLD, $NEW), file_get_contents($tpl));
$tmp = tempnam(sys_get_temp_dir(), 's797') . '.php';
file_put_contents($tmp, $src);
require $tmp;
unlink($tmp);
$res = array();
function chk($name, $ok, $got = null) { global $res; $res[] = $ok; echo ($ok ? 'ok  ' : 'BAD ') . $name . ($ok ? '' : '  -> ' . var_export($got, true)) . "\n"; }
$f = 's797_helpline_html';
$T = 'tel:+91' . $NEW; $S = $NEW . ', ' . $OLD;

$h = '<header><a href="tel:+91-' . $OLD . '">+91-' . $OLD . '</a></header>';
chk('the header link dials the helpline and shows both', $f($h) === '<header><a href="' . $T . '">' . $S . '</a></header>', $f($h));
$h = '<a class="btn" href="tel:+91-' . $OLD . '"><span class="t">+91-' . $OLD . '</span></a>';
chk('a button with the number inside a span', $f($h) === '<a class="btn" href="' . $T . '"><span class="t">' . $S . '</span></a>', $f($h));
$h = '<a href="tel:+91-' . $OLD . '"><i class="ic"></i> Call Us</a>';
chk('Call Us: the link changes, the label stays', $f($h) === '<a href="' . $T . '"><i class="ic"></i> Call Us</a>', $f($h));
foreach (array('tel:' . $OLD, 'tel:+91' . $OLD, 'tel:0' . $OLD, 'tel:91' . $OLD, 'tel: +91 ' . $OLD) as $v) {
    $h = "<a href='" . $v . "'>Call</a>";
    chk('call link written as ' . str_replace($OLD, 'N', $v), $f($h) === "<a href='" . $T . "'>Call</a>", $f($h));
}
$w = '<a href="https://api.whatsapp.com/send?phone=' . $OLD . '">Whatsapp</a><a href="https://wa.me/91' . $OLD . '">WhatsApp ' . $OLD . '</a>';
chk('WhatsApp links and a WhatsApp label are untouched', $f($w) === $w, $f($w));
$j = '<script type="application/ld+json">{"telephone":"+91-' . $OLD . '","a":"<b>' . $OLD . '</b>"}</script>';
chk('a script block (page data for Google) is untouched', $f($j) === $j, $f($j));
$s = '<style>.x:after{content:"' . $OLD . '"}</style>';
chk('a style block is untouched', $f($s) === $s, $f($s));
$h = '<p title="Call +91-' . $OLD . '">Phone: ' . $OLD . '</p>';
chk('an attribute is untouched, the shown text changes', $f($h) === '<p title="Call +91-' . $OLD . '">Phone: ' . $S . '</p>', $f($h));
$h = '<p>1' . $OLD . ' and ' . $OLD . '1</p>';
chk('a longer run of digits that only contains the number is untouched', $f($h) === $h, $f($h));
$h = '<div>no number here</div>';
chk('a page without the number comes back identical', $f($h) === $h);
$page = '<html><head><title>x</title>' . $j . $s . '</head><body><header><a href="tel:+91-' . $OLD . '">+91-' . $OLD . '</a></header>text ' . $OLD . '<script>var a="' . str_repeat('x<y>', 90000) . $OLD . '";</script><footer>' . $w . '<a href="tel:+91-' . $OLD . '">Call Us</a></footer></body></html>';
$o = $f($page);
chk('a whole page: 2 call links to the helpline', substr_count($o, 'href="' . $T . '"') === 2, substr_count($o, 'href="' . $T . '"'));
chk('a whole page: the big script and the page data are byte-identical', strpos($o, 'var a="' . str_repeat('x<y>', 90000) . $OLD . '";') !== false && strpos($o, $j) !== false);
chk('a whole page: text straight before a script is changed too', strpos($o, 'text ' . $S . '<script>') !== false);
chk('a whole page: WhatsApp part identical', strpos($o, $w) !== false);
chk('twice is the same as once', $f($o) === $o);
chk('not a string comes back as it was', $f(null) === null && $f('') === '' && $f(array(1)) === array(1));
$h = '<a href="tel:+91-' . $OLD . '">x</a><script>unclosed ' . $OLD;
chk('an unclosed script does not lose the page', $f($h) === '<a href="' . $T . '">x</a><script>unclosed ' . $OLD, $f($h));
chk('the template carries no real number', !preg_match('~[6-9][0-9]{9}~', file_get_contents($tpl)));
$bad = count(array_filter($res, function ($x) { return !$x; }));
echo $bad ? "WALK RED $bad of " . count($res) . "\n" : 'WALK OK ' . count($res) . '/' . count($res) . "\n";
exit($bad ? 1 : 0);
