<h2>Users</h2>

<!-- link to add new users page -->
<div class='upper-right-opt'>
	<?php echo $this->Html->link( '+ New User', array( 'action' => 'add' ) ); ?>
</div>

<table style='padding:5px;'>
	<!-- table heading -->
	<tr style='background-color:#fff;'>
		<th>ID</th>
		<th>Firstname</th>
		<th>Lastname</th>
		<th>Username</th>
		<th>Email</th>
		<th>Actions</th>
	</tr>
	
<?php

	
	//loop to show all retrieved records
	foreach( $users as $user ){
	
		echo "<tr>";
			echo "<td>{$user['User']['id']}</td>";
			echo "<td>{$user['User']['firstname']}</td>";
			echo "<td>{$user['User']['lastname']}</td>";
			echo "<td>{$user['User']['username']}</td>";
			echo "<td>{$user['User']['email']}</td>";
			
			//here are the links to edit and delete actions
			echo "<td class='actions'>";
				echo $this->Html->link( 'Edit', array('action' => 'edit', $user['User']['id']) );
				
				//in cakephp 2.0, we won't use get request for deleting records
				//we use post request (for security purposes)
				echo $this->Form->postLink( 'Delete', array(
						'action' => 'delete', 
						$user['User']['id']), array(
							'confirm'=>'Are you sure you want to delete that user?' ) );
			echo "</td>";
		echo "</tr>";
	}
?>
	
</table>