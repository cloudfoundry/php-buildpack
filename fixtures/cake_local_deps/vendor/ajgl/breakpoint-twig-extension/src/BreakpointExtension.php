<?php

/*
 * AJGL Breakpoint Twig Extension Component
 *
 * Copyright (C) Antonio J. García Lagar <aj@garcialagar.es>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Ajgl\Twig\Extension;

use Twig\Environment;
use Twig\Extension\AbstractExtension;
use Twig\TwigFunction;

/**
 * @author Antonio J. García Lagar <aj@garcialagar.es>
 */
class BreakpointExtension extends AbstractExtension
{
    public function getName()
    {
        return 'breakpoint';
    }

    public function getFunctions()
    {
        return [
            new TwigFunction('breakpoint', [$this, 'setBreakpoint'], ['needs_environment' => true, 'needs_context' => true]),
        ];
    }

    /**
     * If Xdebug is detected, makes the debugger break.
     *
     * @param Environment $environment the environment instance
     * @param mixed       $context     variables from the Twig template
     */
    public function setBreakpoint(Environment $environment, $context)
    {
        if (function_exists('xdebug_break')) {
            $arguments = func_get_args();
            $arguments = array_slice($arguments, 2);
            xdebug_break();
        }
    }
}
