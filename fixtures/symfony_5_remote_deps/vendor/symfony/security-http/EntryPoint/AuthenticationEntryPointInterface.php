<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Http\EntryPoint;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Core\Exception\AuthenticationException;

/**
 * Implement this interface for any classes that will be called to "start"
 * the authentication process (see method for more details).
 *
 * @author Fabien Potencier <fabien@symfony.com>
 */
interface AuthenticationEntryPointInterface
{
    /**
     * Returns a response that directs the user to authenticate.
     *
     * This is called when an anonymous request accesses a resource that
     * requires authentication. The job of this method is to return some
     * response that "helps" the user start into the authentication process.
     *
     * Examples:
     *
     * - For a form login, you might redirect to the login page
     *
     *     return new RedirectResponse('/login');
     *
     * - For an API token authentication system, you return a 401 response
     *
     *     return new Response('Auth header required', 401);
     *
     * @return Response
     */
    public function start(Request $request, AuthenticationException $authException = null);
}
