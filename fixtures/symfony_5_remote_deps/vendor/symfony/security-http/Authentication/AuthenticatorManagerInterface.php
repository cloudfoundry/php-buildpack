<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Http\Authentication;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Http\Firewall\AbstractListener;

/**
 * @author Wouter de Jong <wouter@wouterj.nl>
 * @author Ryan Weaver <ryan@symfonycasts.com>
 *
 * @experimental in Symfony 5.1
 */
interface AuthenticatorManagerInterface
{
    /**
     * Called to see if authentication should be attempted on this request.
     *
     * @see AbstractListener::supports()
     */
    public function supports(Request $request): ?bool;

    /**
     * Tries to authenticate the request and returns a response - if any authenticator set one.
     */
    public function authenticateRequest(Request $request): ?Response;
}
