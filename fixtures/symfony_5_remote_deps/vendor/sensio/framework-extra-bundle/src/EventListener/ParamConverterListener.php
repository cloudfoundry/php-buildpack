<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Sensio\Bundle\FrameworkExtraBundle\EventListener;

use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Sensio\Bundle\FrameworkExtraBundle\Request\ParamConverter\ParamConverterManager;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpKernel\Event\KernelEvent;
use Symfony\Component\HttpKernel\KernelEvents;

/**
 * The ParamConverterListener handles the ParamConverter annotation.
 *
 * @author Fabien Potencier <fabien@symfony.com>
 */
class ParamConverterListener implements EventSubscriberInterface
{
    /**
     * @var ParamConverterManager
     */
    private $manager;

    private $autoConvert;

    /**
     * @param bool $autoConvert Auto convert non-configured objects
     */
    public function __construct(ParamConverterManager $manager, $autoConvert = true)
    {
        $this->manager = $manager;
        $this->autoConvert = $autoConvert;
    }

    /**
     * Modifies the ParamConverterManager instance.
     */
    public function onKernelController(KernelEvent $event)
    {
        $controller = $event->getController();
        $request = $event->getRequest();
        $configurations = [];

        if ($configuration = $request->attributes->get('_converters')) {
            foreach (\is_array($configuration) ? $configuration : [$configuration] as $configuration) {
                $configurations[$configuration->getName()] = $configuration;
            }
        }

        if (\is_array($controller)) {
            $r = new \ReflectionMethod($controller[0], $controller[1]);
        } elseif (\is_object($controller) && \is_callable([$controller, '__invoke'])) {
            $r = new \ReflectionMethod($controller, '__invoke');
        } else {
            $r = new \ReflectionFunction($controller);
        }

        // automatically apply conversion for non-configured objects
        if ($this->autoConvert) {
            $configurations = $this->autoConfigure($r, $request, $configurations);
        }

        $this->manager->apply($request, $configurations);
    }

    private function autoConfigure(\ReflectionFunctionAbstract $r, Request $request, $configurations)
    {
        foreach ($r->getParameters() as $param) {
            $type = $param->getType();
            $class = null !== $type && !$type->isBuiltin() ? $type->getName() : null;
            if (null !== $class && $request instanceof $class) {
                continue;
            }

            $name = $param->getName();

            if ($type) {
                if (!isset($configurations[$name])) {
                    $configuration = new ParamConverter([]);
                    $configuration->setName($name);

                    $configurations[$name] = $configuration;
                }

                if (null !== $class && null === $configurations[$name]->getClass()) {
                    $configurations[$name]->setClass($class);
                }
            }

            if (isset($configurations[$name])) {
                $configurations[$name]->setIsOptional($param->isOptional() || $param->isDefaultValueAvailable() || ($type && $type->allowsNull()));
            }
        }

        return $configurations;
    }

    /**
     * {@inheritdoc}
     */
    public static function getSubscribedEvents()
    {
        return [
            KernelEvents::CONTROLLER => 'onKernelController',
        ];
    }
}
