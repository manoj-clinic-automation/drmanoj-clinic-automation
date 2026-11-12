<?php
/**
 * Plugin Name: Clinic helpline number (kit S797)
 * Description: Shows the clinic's helpline number first wherever the public pages show the old call number: every call link dials the helpline, and the number shown reads "helpline, old number". WhatsApp links are left as they are. Nothing in the database is changed. To undo, remove this one file.
 * Version: S797.1
 *
 * Made on the server by install_S797_WEBSITE_HELPLINE.sh from the kit's template; the two numbers were given on the server line
 * (no number is kept in the repository). The owner, 12-Nov-2026: the helpline number is to be made known everywhere, with the old
 * number beside it.
 */
if (!defined('ABSPATH')) {
    exit;
}
if (!defined('S797_OLD')) {
    define('S797_OLD', '@@OLD@@');
}
if (!defined('S797_NEW')) {
    define('S797_NEW', '@@NEW@@');
}

if (!function_exists('s797_text_nodes')) {
    /** The number as SHOWN (text between tags) in one piece of markup that holds no script or style block. */
    function s797_text_nodes($chunk)
    {
        if ($chunk === '' || strpos($chunk, S797_OLD) === false) {
            return $chunk;
        }
        $r = preg_replace_callback('~>([^<]+)<~', function ($m) {
            $t = $m[1];
            if (strpos($t, S797_OLD) === false || strpos($t, S797_NEW) !== false || stripos($t, 'whatsapp') !== false) {
                return $m[0];
            }
            $n = preg_replace('~(?<![0-9])(?:\+?91[-\s]?)?' . S797_OLD . '(?![0-9])~', S797_NEW . ', ' . S797_OLD, $t);
            return '>' . ($n === null ? $t : $n) . '<';
        }, '>' . $chunk . '<');
        return $r === null ? $chunk : substr($r, 1, -1);
    }
}

if (!function_exists('s797_helpline_html')) {
    /** One whole page of HTML in, the same page out with the helpline first. Any doubt returns the page untouched. */
    function s797_helpline_html($html)
    {
        if (!is_string($html) || $html === '' || strpos($html, S797_OLD) === false) {
            return $html;
        }
        $num = '(?<![0-9])(?:\+?91[-\s]?|0)?' . S797_OLD . '(?![0-9])';
        $out = preg_replace('~(href\s*=\s*["\'])tel:\s*' . $num . '\s*(["\'])~i', '${1}tel:+91' . S797_NEW . '${2}', $html);
        if ($out === null) {
            return $html;
        }
        $res = '';
        $pos = 0;
        $len = strlen($out);
        while ($pos < $len) {
            $s1 = stripos($out, '<script', $pos);
            $s2 = stripos($out, '<style', $pos);
            if ($s1 === false && $s2 === false) {
                $res .= s797_text_nodes(substr($out, $pos));
                break;
            }
            if ($s2 === false || ($s1 !== false && $s1 < $s2)) {
                $start = $s1;
                $close = '</script';
            } else {
                $start = $s2;
                $close = '</style';
            }
            $res .= s797_text_nodes(substr($out, $pos, $start - $pos));
            $end = stripos($out, $close, $start);
            if ($end === false) {
                $res .= substr($out, $start);
                break;
            }
            $gt = strpos($out, '>', $end);
            $end = ($gt === false) ? $len : $gt + 1;
            $res .= substr($out, $start, $end - $start);
            $pos = $end;
        }
        return $res;
    }
}

if (function_exists('add_action')) {
    add_action('template_redirect', function () {
        if (is_admin() || is_feed() || (function_exists('is_customize_preview') && is_customize_preview())
            || (defined('REST_REQUEST') && REST_REQUEST) || (defined('DOING_AJAX') && DOING_AJAX)
            || isset($_GET['elementor-preview']) || isset($_GET['elementor_library'])) {
            return;
        }
        ob_start(function ($buffer) {
            return s797_helpline_html($buffer);
        });
    }, 0);
}
