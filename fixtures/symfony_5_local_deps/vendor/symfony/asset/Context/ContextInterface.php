<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Asset\Context;

/**
 * Holds information about the current request.
 *
 * @author Fabien Potencier <fabien@symfony.com>
 */
interface ContextInterface
{
    /**
     * Gets the base path.
     */
    public function getBasePath(): string;

    /**
     * Checks whether the request is secure or not.
     */
    public function isSecure(): bool;
}
