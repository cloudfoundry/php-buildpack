<h2>Edit User</h2>

<!-- link to add new users page -->
<div class='upper-right-opt'>
	<?php echo $this->Html->link( 'List Users', array( 'action' => 'index' ) ); ?>
</div>

<?php 
//this is our edit form, name the fields same as database column names
echo $this->Form->create('User');

	echo $this->Form->input('firstname');
	echo $this->Form->input('lastname');
	echo $this->Form->input('email');
	echo $this->Form->input('username');
	echo $this->Form->input('password', array('type'=>'password'));
	
echo $this->Form->end('Submit');
?>

