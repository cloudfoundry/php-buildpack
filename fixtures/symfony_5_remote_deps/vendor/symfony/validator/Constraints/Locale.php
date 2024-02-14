<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Validator\Constraints;

use Symfony\Component\Intl\Locales;
use Symfony\Component\Validator\Constraint;
use Symfony\Component\Validator\Exception\LogicException;

/**
 * @Annotation
 * @Target({"PROPERTY", "METHOD", "ANNOTATION"})
 *
 * @author Bernhard Schussek <bschussek@gmail.com>
 */
class Locale extends Constraint
{
    public const NO_SUCH_LOCALE_ERROR = 'a0af4293-1f1a-4a1c-a328-979cba6182a2';

    protected static $errorNames = [
        self::NO_SUCH_LOCALE_ERROR => 'NO_SUCH_LOCALE_ERROR',
    ];

    public $message = 'This value is not a valid locale.';
    public $canonicalize = true;

    public function __construct($options = null)
    {
        if (!class_exists(Locales::class)) {
            throw new LogicException('The Intl component is required to use the Locale constraint. Try running "composer require symfony/intl".');
        }

        parent::__construct($options);
    }
}
