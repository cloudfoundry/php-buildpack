<?php

namespace App\Model\Entity;

use Cake\ORM\Entity;

class User extends Entity
{
    protected $_accessible = [
        "name" => true,
        "email" => true,
        "phone_no" => true
    ];
}
