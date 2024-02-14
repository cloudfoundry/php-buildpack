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

use Symfony\Component\Intl\Countries;
use Symfony\Component\Validator\Constraint;
use Symfony\Component\Validator\Exception\LogicException;

/**
 * @Annotation
 * @Target({"PROPERTY", "METHOD", "ANNOTATION"})
 *
 * @author Bernhard Schussek <bschussek@gmail.com>
 */
class Country extends Constraint
{
    public const NO_SUCH_COUNTRY_ERROR = '8f900c12-61bd-455d-9398-996cd040f7f0';

    protected static $errorNames = [
        self::NO_SUCH_COUNTRY_ERROR => 'NO_SUCH_COUNTRY_ERROR',
    ];

    public $message = 'This value is not a valid country.';
    public $alpha3 = false;

    public function __construct($options = null)
    {
        if (!class_exists(Countries::class)) {
            throw new LogicException('The Intl component is required to use the Country constraint. Try running "composer require symfony/intl".');
        }

        parent::__construct($options);
    }
}
