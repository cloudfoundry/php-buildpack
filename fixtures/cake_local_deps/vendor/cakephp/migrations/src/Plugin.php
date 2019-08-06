<?php
/**
 * Copyright (c) Cake Software Foundation, Inc. (http://cakefoundation.org)
 *
 * Licensed under The MIT License
 * Redistributions of files must retain the above copyright notice.
 *
 * @copyright     Copyright (c) Cake Software Foundation, Inc. (http://cakefoundation.org)
 * @link          http://cakephp.org CakePHP(tm) Project
 * @license       http://www.opensource.org/licenses/mit-license.php MIT License
 */
namespace Migrations;

use Cake\Core\BasePlugin;

/**
 * Plugin class for migrations
 */
class Plugin extends BasePlugin
{
    /**
     * Plugin name.
     *
     * @var string
     */
    protected $name = 'Migrations';

    /**
     * Don't try to load routes.
     *
     * @var bool
     */
    protected $routesEnabled = false;
}
