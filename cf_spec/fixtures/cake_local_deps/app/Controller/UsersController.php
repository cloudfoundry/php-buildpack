<?php
class UsersController extends AppController {

	public $name = 'Users';
    
	public function index() {
		//to retrieve all users, need just one line
		$this->set('users', $this->User->find('all'));
	}
	
	public function add(){
	
		//check if it is a post request
		//this way, we won't have to do if(!empty($this->request->data))
		if ($this->request->is('post')){
			//save new user
			if ($this->User->save($this->request->data)){
			
				//set flash to user screen
				$this->Session->setFlash('User was added.');
				//redirect to user list
				$this->redirect(array('action' => 'index'));
				
			}else{
				//if save failed
				$this->Session->setFlash('Unable to add user. Please, try again.');
				
			}
		}
	}

	public function edit() {
		//get the id of the user to be edited
		$id = $this->request->params['pass'][0];
		
		//set the user id
		$this->User->id = $id;
		
		//check if a user with this id really exists
		if( $this->User->exists() ){
		
			if( $this->request->is( 'post' ) || $this->request->is( 'put' ) ){
				//save user
				if( $this->User->save( $this->request->data ) ){
				
					//set to user's screen
					$this->Session->setFlash('User was edited.');
					
					//redirect to user's list
					$this->redirect(array('action' => 'index'));
					
				}else{
					$this->Session->setFlash('Unable to edit user. Please, try again.');
				}
				
			}else{
			
				//we will read the user data
				//so it will fill up our html form automatically
				$this->request->data = $this->User->read();
			}
			
		}else{
			//if not found, we will tell the user that user does not exist
			$this->Session->setFlash('The user you are trying to edit does not exist.');
			$this->redirect(array('action' => 'index'));
				
			//or, since it we are using php5, we can throw an exception
			//it looks like this
			//throw new NotFoundException('The user you are trying to edit does not exist.');
		}
		

	}

	public function delete() {
		$id = $this->request->params['pass'][0];
		
		//the request must be a post request 
		//that's why we use postLink method on our view for deleting user
		if( $this->request->is('get') ){
		
			$this->Session->setFlash('Delete method is not allowed.');
			$this->redirect(array('action' => 'index'));
			
			//since we are using php5, we can also throw an exception like:
			//throw new MethodNotAllowedException();
		}else{
		
			if( !$id ) {
				$this->Session->setFlash('Invalid id for user');
				$this->redirect(array('action'=>'index'));
				
			}else{
				//delete user
				if( $this->User->delete( $id ) ){
					//set to screen
					$this->Session->setFlash('User was deleted.');
					//redirect to users's list
					$this->redirect(array('action'=>'index'));
					
				}else{	
					//if unable to delete
					$this->Session->setFlash('Unable to delete user.');
					$this->redirect(array('action' => 'index'));
				}
			}
		}
	}
}
?>
