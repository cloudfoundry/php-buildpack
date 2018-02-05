<?php

namespace ZfcBase\Module;

use InvalidArgumentException;
use Zend\EventManager\EventInterface as Event;
use Zend\EventManager\StaticEventManager;
use Zend\ModuleManager\Feature\AutoloaderProviderInterface;
use Zend\ModuleManager\Feature\LocatorRegisteredInterface;
use Zend\ModuleManager\ModuleManager;
use Zend\Mvc\ApplicationInterface;

abstract class AbstractModule implements
    AutoloaderProviderInterface,
    LocatorRegisteredInterface
{
    protected $mergedConfig;

    abstract public function getDir();
    abstract public function getNamespace();

    public function init(ModuleManager $moduleManager)
    {
        $sharedManager = $moduleManager->getEventManager()->getSharedManager();
        $instance = $this;//TODO this will no be needed in PHP 5.4
        $sharedManager->attach('Zend\Mvc\Application', 'bootstrap', function($e) use ($instance, $moduleManager) {
            $app = $e->getParam('application');
            $instance->setMergedConfig($app->getConfig());
            $instance->bootstrap($moduleManager, $app);
        });
    }

    public function bootstrap(ModuleManager $moduleManager, ApplicationInterface $app)
    {
    }

    public function getAutoloaderConfig()
    {
        return array(
            'Zend\Loader\ClassMapAutoloader' => array(
                $this->getDir() . '/autoload_classmap.php',
            ),
            'Zend\Loader\StandardAutoloader' => array(
                'namespaces' => array(
                    $this->getNamespace() => $this->getDir() . '/src/' . $this->getNamespace(),
                ),
            ),
        );
    }

    public function getConfig()
    {
        return include $this->getDir() . '/config/module.config.php';
    }

    public function getMergedConfig()
    {
        return $this->mergedConfig;
    }

    public function setMergedConfig($mergedConfig)
    {
        $this->mergedConfig = $mergedConfig;
    }

    public function getOptions($namespace = 'options')
    {
        $config = $this->getMergedConfig();
        if(empty($config[$this->getNamespace()][$namespace])) {
            return array();
        }

        if (is_array($config[$this->getNamespace()][$namespace])) {
            return $config[$this->getNamespace()][$namespace];
        } else {
            return $config[$this->getNamespace()][$namespace]->toArray();
        }
    }

    /**
     * Returns module option value.
     * Dot character is used to separate sub arrays.
     *
     * Example:
     * array(
     *      'option1' => 'this is my option 1'
     *      'option2' => array(
     *          'key1' => 'sub key1',
     *          'key2' => 'sub key2',
     *      )
     * )
     *
     * $module->getOption('option1');
     * Returns: (string) "This is my option 1"
     *
     * $module->getOption('option2');
     * Returns: array(
     *          'key1' => 'sub key1',
     *          'key2' => 'sub key2',
     *      )
     *
     * $module->getOption('option2.key1');
     * Returns: (string) "sub key1"
     *
     * @param string $option
     * @param mixed $default
     * @return mixed
     */
    public function getOption($option, $default = null, $namespace = 'options')
    {
        $options = $this->getOptions($namespace);
        $optionArr = explode('.', $option);

        $option = $this->getOptionFromArray($options, $optionArr, $default, $option);
        return $option;
    }

    private function getOptionFromArray($options, array $option, $default, $origOption)
    {
        $currOption = array_shift($option);
        //we need this fix to accept both array/ZendConfig -- there is know problem with offsetExists() in PHP
        //if(array_key_exists($currOption, $options)) {
        if(array_key_exists($currOption, $options) || ($options instanceof \Zend\Config\Config && $options->offsetExists($currOption))) {
            if(count($option) >= 1) {
                return $this->getOptionFromArray($options[$currOption], $option, $default, $origOption);
            }

            return $options[$currOption];
        }

        if($default !== null) {
            return $default;
        }

        throw new InvalidArgumentException("Option '$origOption' is not set");
    }

}
