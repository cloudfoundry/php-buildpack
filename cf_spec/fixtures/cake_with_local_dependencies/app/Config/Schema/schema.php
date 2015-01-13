<?php 
class AppSchema extends CakeSchema {

	public function before($event = array()) {
		return true;
	}

	public function after($event = array()) {
	}

	public $users = array(
		'id' => array('type' => 'string', 'null' => false, 'key' => 'primary'),
		'firstname' => array('type' => 'text', 'null' => false, 'length' => 1073741824),
		'lastname' => array('type' => 'text', 'null' => false, 'length' => 1073741824),
		'email' => array('type' => 'text', 'null' => false, 'length' => 1073741824),
		'username' => array('type' => 'text', 'null' => false, 'length' => 1073741824),
		'password' => array('type' => 'text', 'null' => false, 'length' => 1073741824),
		'indexes' => array(
			'PRIMARY' => array('unique' => true, 'column' => 'id')
		),
		'tableParameters' => array()
	);

}
