<?php
// I18N support information here
$language = 'ja_JP.utf8';

putenv('LC_ALL=' . $language);
setlocale(LC_ALL, $language);

// Set the text domain as 'messages'
$domain = 'messages';
$localedir = dirname(__FILE__) . '/locale';
echo $localedir . ': ';
bindtextdomain($domain, $localedir);
textdomain($domain);

echo gettext('hello-world') . '<br/>';
?>
