<p>Avail: <?php echo geoip_db_avail(GEOIP_COUNTRY_EDITION); ?></p>
<p>Info: <?php echo geoip_database_info(); ?></p>

<?php
$country = geoip_country_code_by_name('www.cs.rochester.edu');
echo '<p>Country: ' . $country . '</p>';
?>
