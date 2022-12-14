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
        $users = $this->Users->find()->toList();
        $this->set("title", "List Users");
        $this->set(compact("users"));
    }
}
