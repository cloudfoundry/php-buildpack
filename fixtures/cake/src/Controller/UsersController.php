<?php

namespace App\Controller;

use App\Controller\AppController;

class UsersController extends AppController
{
    public function initialize(): void
    {
        parent::initialize();

        $this->loadModel("Users");
    }

    public function listUsers()
    {
        $users = $this->Users->find()->all()->toList();
        $this->set("title", "List Users");
        $this->set(compact("users"));
    }

    public function addUser()
    {
        $user = $this->Users->newEmptyEntity();
        if ($this->request->is('post')) {
            $user = $this->Users->patchEntity($user, $this->request->getData());
            if ($this->Users->save($user)) {
                $this->Flash->success(__('The user has been created.'));
                return $this->redirect(['action' => 'listUsers']);
            }
            $this->Flash->error(__('Failed to create user. Please, try again.'));
        }
        $this->set("title", "Add User");
        $this->set(compact("user"));
    }
}
