<?php
/*
 * wpdb_s592.php -- kit S592_CONTACT_FORM_VIA_WPCLI (session S329, 18-Oct-2026) · D742.
 *
 * Run ONLY by fix_s592.py, as:  wp eval-file wpdb_s592.php --path=<site> --allow-root --skip-plugins --skip-themes
 * It runs ONE statement through WordPress's own database connection ($wpdb) -- the road S589 proved works
 * (WordPress connects; the mysql program with the wp-config login was refused, F-938).
 * The statement is read from the root-only file named in S592_SQL_FILE. Nothing is printed but the rows,
 * between two marker lines, so a PHP notice on the page can never be mistaken for data.
 */
global $wpdb;
$f = getenv('S592_SQL_FILE');
$sql = ($f && is_readable($f)) ? trim(file_get_contents($f)) : '';
$sql = rtrim($sql, "; \n\r\t");
if ($sql === '') {
    fwrite(STDERR, "@@S592ERR no statement given\n");
    exit(3);
}
$wpdb->hide_errors();
$wpdb->suppress_errors(true);
$is_read = preg_match('/^\s*(SELECT|SHOW)\b/i', $sql) === 1;
if ($is_read) {
    $rows = $wpdb->get_results($sql, ARRAY_N);
} else {
    $rows = array();
    $wpdb->query($sql);
}
if ($wpdb->last_error !== '') {
    fwrite(STDERR, "@@S592ERR " . substr(str_replace(array("\n", "\r"), ' ', $wpdb->last_error), 0, 160) . "\n");
    exit(4);
}
if ($is_read && !is_array($rows)) {
    fwrite(STDERR, "@@S592ERR the read returned nothing usable\n");
    exit(5);
}
echo "@@S592BEGIN\n";
foreach ($rows as $r) {
    $out = array();
    foreach ($r as $v) {
        $out[] = ($v === null) ? 'NULL' : str_replace(array("\\", "\t", "\n", "\r"), array("\\\\", "\\t", "\\n", "\\r"), (string)$v);
    }
    echo implode("\t", $out) . "\n";
}
echo "@@S592END\n";
