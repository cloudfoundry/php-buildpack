<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Http;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\RequestMatcherInterface;
use Symfony\Component\Security\Http\Firewall\ExceptionListener;
use Symfony\Component\Security\Http\Firewall\LogoutListener;

/**
 * FirewallMap allows configuration of different firewalls for specific parts
 * of the website.
 *
 * @author Fabien Potencier <fabien@symfony.com>
 */
class FirewallMap implements FirewallMapInterface
{
    private $map = [];

    public function add(RequestMatcherInterface $requestMatcher = null, array $listeners = [], ExceptionListener $exceptionListener = null, LogoutListener $logoutListener = null)
    {
        $this->map[] = [$requestMatcher, $listeners, $exceptionListener, $logoutListener];
    }

    /**
     * {@inheritdoc}
     */
    public function getListeners(Request $request)
    {
        foreach ($this->map as $elements) {
            if (null === $elements[0] || $elements[0]->matches($request)) {
                return [$elements[1], $elements[2], $elements[3]];
            }
        }

        return [[], null, null];
    }
}
