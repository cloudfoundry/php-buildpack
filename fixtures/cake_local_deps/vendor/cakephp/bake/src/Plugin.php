<?php
/**
 * CakePHP(tm) : Rapid Development Framework (http://cakephp.org)
 * Copyright (c) Cake Software Foundation, Inc. (http://cakefoundation.org)
 *
 * Licensed under The MIT License
 * For full copyright and license information, please see the LICENSE.txt
 * Redistributions of files must retain the above copyright notice.
 *
 * @copyright     Copyright (c) Cake Software Foundation, Inc. (http://cakefoundation.org)
 * @link          http://cakephp.org CakePHP(tm) Project
 * @since         1.7.2
 * @license       http://www.opensource.org/licenses/mit-license.php MIT License
 */
namespace Bake;

use Cake\Core\BasePlugin;
use Cake\Core\PluginApplicationInterface;

/**
 * Plugin class for bake
 */
class Plugin extends BasePlugin
{
    /**
     * Plugin name.
     *
     * @var string
     */
    protected $name = 'Bake';

    /**
     * Override to do nothing.
     *
     * @param \Cake\Routing\RouteBuilder $routes The route builder to update.
     * @return void
     */
    public function routes($routes)
    {
    }

    /**
     * load WyriHaximus/TwigView plugin.
     *
     * @param \Cake\Core\PluginApplicationInterface $app The host application
     * @return void
     */
    public function bootstrap(PluginApplicationInterface $app)
    {
        $app->addPlugin('WyriHaximus/TwigView');
    }
}
