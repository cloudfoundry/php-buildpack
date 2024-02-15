<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Http\Authenticator\Passport\Credentials;

use Symfony\Component\Security\Core\Exception\LogicException;

/**
 * Implements password credentials.
 *
 * These plaintext passwords are checked by the UserPasswordHasher during
 * authentication.
 *
 * @author Wouter de Jong <wouter@wouterj.nl>
 *
 * @final
 */
class PasswordCredentials implements CredentialsInterface
{
    private ?string $password = null;
    private bool $resolved = false;

    public function __construct(#[\SensitiveParameter] string $password)
    {
        $this->password = $password;
    }

    public function getPassword(): string
    {
        if (null === $this->password) {
            throw new LogicException('The credentials are erased as another listener already verified these credentials.');
        }

        return $this->password;
    }

    /**
     * @internal
     */
    public function markResolved(): void
    {
        $this->resolved = true;
        $this->password = null;
    }

    public function isResolved(): bool
    {
        return $this->resolved;
    }
}
