<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Sensio\Bundle\FrameworkExtraBundle\Configuration;

/**
 * Base configuration annotation.
 *
 * @author Johannes M. Schmitt <schmittjoh@gmail.com>
 */
abstract class ConfigurationAnnotation implements ConfigurationInterface
{
    public function __construct(array $values)
    {
        foreach ($values as $k => $v) {
            if (!method_exists($this, $name = 'set'.$k)) {
                throw new \RuntimeException(sprintf('Unknown key "%s" for annotation "@%s".', $k, static::class));
            }

            $this->$name($v);
        }
    }
}
