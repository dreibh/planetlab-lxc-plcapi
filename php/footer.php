}

global $adm;

$adm = new PLCAPI(array('AuthMethod' => "capability",
			'Username' => PLC_API_MAINTENANCE_USER,
			'AuthString' => PLC_API_MAINTENANCE_PASSWORD));

?>
