<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Http\RememberMe;

use Symfony\Component\HttpFoundation\Cookie;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Exception\AuthenticationException;
use Symfony\Component\Security\Core\User\UserInterface;

/**
 * Concrete implementation of the RememberMeServicesInterface providing
 * remember-me capabilities without requiring a TokenProvider.
 *
 * @author Johannes M. Schmitt <schmittjoh@gmail.com>
 */
class TokenBasedRememberMeServices extends AbstractRememberMeServices
{
    /**
     * {@inheritdoc}
     */
    protected function processAutoLoginCookie(array $cookieParts, Request $request)
    {
        if (4 !== \count($cookieParts)) {
            throw new AuthenticationException('The cookie is invalid.');
        }

        [$class, $username, $expires, $hash] = $cookieParts;
        if (false === $username = base64_decode($username, true)) {
            throw new AuthenticationException('$username contains a character from outside the base64 alphabet.');
        }
        try {
            $user = $this->getUserProvider($class)->loadUserByUsername($username);
        } catch (\Exception $e) {
            if (!$e instanceof AuthenticationException) {
                $e = new AuthenticationException($e->getMessage(), $e->getCode(), $e);
            }

            throw $e;
        }

        if (!$user instanceof UserInterface) {
            throw new \RuntimeException(sprintf('The UserProviderInterface implementation must return an instance of UserInterface, but returned "%s".', get_debug_type($user)));
        }

        if (true !== hash_equals($this->generateCookieHash($class, $username, $expires, $user->getPassword()), $hash)) {
            throw new AuthenticationException('The cookie\'s hash is invalid.');
        }

        if ($expires < time()) {
            throw new AuthenticationException('The cookie has expired.');
        }

        return $user;
    }

    /**
     * {@inheritdoc}
     */
    protected function onLoginSuccess(Request $request, Response $response, TokenInterface $token)
    {
        $user = $token->getUser();
        $expires = time() + $this->options['lifetime'];
        $value = $this->generateCookieValue(\get_class($user), $user->getUsername(), $expires, $user->getPassword());

        $response->headers->setCookie(
            new Cookie(
                $this->options['name'],
                $value,
                $expires,
                $this->options['path'],
                $this->options['domain'],
                $this->options['secure'] ?? $request->isSecure(),
                $this->options['httponly'],
                false,
                $this->options['samesite']
            )
        );
    }

    /**
     * Generates the cookie value.
     *
     * @param int         $expires  The Unix timestamp when the cookie expires
     * @param string|null $password The encoded password
     *
     * @return string
     */
    protected function generateCookieValue(string $class, string $username, int $expires, ?string $password)
    {
        // $username is encoded because it might contain COOKIE_DELIMITER,
        // we assume other values don't
        return $this->encodeCookie([
            $class,
            base64_encode($username),
            $expires,
            $this->generateCookieHash($class, $username, $expires, $password),
        ]);
    }

    /**
     * Generates a hash for the cookie to ensure it is not being tampered with.
     *
     * @param int         $expires  The Unix timestamp when the cookie expires
     * @param string|null $password The encoded password
     *
     * @return string
     */
    protected function generateCookieHash(string $class, string $username, int $expires, ?string $password)
    {
        return hash_hmac('sha256', $class.self::COOKIE_DELIMITER.$username.self::COOKIE_DELIMITER.$expires.self::COOKIE_DELIMITER.$password, $this->getSecret());
    }
}
