<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Http\Session;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;

/**
 * The default session strategy implementation.
 *
 * Supports the following strategies:
 * NONE: the session is not changed
 * MIGRATE: the session id is updated, attributes are kept
 * INVALIDATE: the session id is updated, attributes are lost
 *
 * @author Johannes M. Schmitt <schmittjoh@gmail.com>
 */
class SessionAuthenticationStrategy implements SessionAuthenticationStrategyInterface
{
    public const NONE = 'none';
    public const MIGRATE = 'migrate';
    public const INVALIDATE = 'invalidate';

    private $strategy;

    public function __construct(string $strategy)
    {
        $this->strategy = $strategy;
    }

    /**
     * {@inheritdoc}
     */
    public function onAuthentication(Request $request, TokenInterface $token)
    {
        switch ($this->strategy) {
            case self::NONE:
                return;

            case self::MIGRATE:
                // Note: this logic is duplicated in several authentication listeners
                // until Symfony 5.0 due to a security fix with BC compat
                $request->getSession()->migrate(true);

                return;

            case self::INVALIDATE:
                $request->getSession()->invalidate();

                return;

            default:
                throw new \RuntimeException(sprintf('Invalid session authentication strategy "%s".', $this->strategy));
        }
    }
}
