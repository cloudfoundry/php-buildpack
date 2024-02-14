<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Bridge\Monolog;

use Monolog\Logger as BaseLogger;
use Monolog\ResettableInterface;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpKernel\Log\DebugLoggerInterface;
use Symfony\Contracts\Service\ResetInterface;

/**
 * @author Fabien Potencier <fabien@symfony.com>
 */
class Logger extends BaseLogger implements DebugLoggerInterface, ResetInterface
{
    /**
     * {@inheritdoc}
     */
    public function getLogs(Request $request = null)
    {
        if ($logger = $this->getDebugLogger()) {
            return $logger->getLogs($request);
        }

        return [];
    }

    /**
     * {@inheritdoc}
     */
    public function countErrors(Request $request = null)
    {
        if ($logger = $this->getDebugLogger()) {
            return $logger->countErrors($request);
        }

        return 0;
    }

    /**
     * {@inheritdoc}
     */
    public function clear()
    {
        if ($logger = $this->getDebugLogger()) {
            $logger->clear();
        }
    }

    /**
     * {@inheritdoc}
     */
    public function reset(): void
    {
        $this->clear();

        if ($this instanceof ResettableInterface) {
            parent::reset();
        }
    }

    public function removeDebugLogger()
    {
        foreach ($this->processors as $k => $processor) {
            if ($processor instanceof DebugLoggerInterface) {
                unset($this->processors[$k]);
            }
        }

        foreach ($this->handlers as $k => $handler) {
            if ($handler instanceof DebugLoggerInterface) {
                unset($this->handlers[$k]);
            }
        }
    }

    /**
     * Returns a DebugLoggerInterface instance if one is registered with this logger.
     */
    private function getDebugLogger(): ?DebugLoggerInterface
    {
        foreach ($this->processors as $processor) {
            if ($processor instanceof DebugLoggerInterface) {
                return $processor;
            }
        }

        foreach ($this->handlers as $handler) {
            if ($handler instanceof DebugLoggerInterface) {
                return $handler;
            }
        }

        return null;
    }
}
