<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Form\Extension\Core\DataTransformer;

use Symfony\Component\Form\DataTransformerInterface;
use Symfony\Component\Form\Exception\TransformationFailedException;

/**
 * Transforms between a timezone identifier string and a DateTimeZone object.
 *
 * @author Roland Franssen <franssen.roland@gmail.com>
 */
class DateTimeZoneToStringTransformer implements DataTransformerInterface
{
    private $multiple;

    public function __construct(bool $multiple = false)
    {
        $this->multiple = $multiple;
    }

    /**
     * {@inheritdoc}
     */
    public function transform($dateTimeZone)
    {
        if (null === $dateTimeZone) {
            return null;
        }

        if ($this->multiple) {
            if (!\is_array($dateTimeZone)) {
                throw new TransformationFailedException('Expected an array of \DateTimeZone objects.');
            }

            return array_map([new self(), 'transform'], $dateTimeZone);
        }

        if (!$dateTimeZone instanceof \DateTimeZone) {
            throw new TransformationFailedException('Expected a \DateTimeZone object.');
        }

        return $dateTimeZone->getName();
    }

    /**
     * {@inheritdoc}
     */
    public function reverseTransform($value)
    {
        if (null === $value) {
            return null;
        }

        if ($this->multiple) {
            if (!\is_array($value)) {
                throw new TransformationFailedException('Expected an array of timezone identifier strings.');
            }

            return array_map([new self(), 'reverseTransform'], $value);
        }

        if (!\is_string($value)) {
            throw new TransformationFailedException('Expected a timezone identifier string.');
        }

        try {
            return new \DateTimeZone($value);
        } catch (\Exception $e) {
            throw new TransformationFailedException($e->getMessage(), $e->getCode(), $e);
        }
    }
}
