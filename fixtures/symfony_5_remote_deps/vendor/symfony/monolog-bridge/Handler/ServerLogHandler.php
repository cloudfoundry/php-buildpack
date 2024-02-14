<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Bridge\Monolog\Handler;

use Monolog\Formatter\FormatterInterface;
use Monolog\Handler\AbstractProcessingHandler;
use Monolog\Handler\FormattableHandlerTrait;
use Monolog\Logger;
use Symfony\Bridge\Monolog\Formatter\VarDumperFormatter;

if (trait_exists(FormattableHandlerTrait::class)) {
    class ServerLogHandler extends AbstractProcessingHandler
    {
        use ServerLogHandlerTrait;

        /**
         * {@inheritdoc}
         */
        protected function getDefaultFormatter(): FormatterInterface
        {
            return new VarDumperFormatter();
        }
    }
} else {
    class ServerLogHandler extends AbstractProcessingHandler
    {
        use ServerLogHandlerTrait;

        /**
         * {@inheritdoc}
         */
        protected function getDefaultFormatter()
        {
            return new VarDumperFormatter();
        }
    }
}

/**
 * @author Grégoire Pineau <lyrixx@lyrixx.info>
 */
trait ServerLogHandlerTrait
{
    private $host;
    private $context;
    private $socket;

    /**
     * @param string|int $level The minimum logging level at which this handler will be triggered
     */
    public function __construct(string $host, $level = Logger::DEBUG, bool $bubble = true, array $context = [])
    {
        parent::__construct($level, $bubble);

        if (false === strpos($host, '://')) {
            $host = 'tcp://'.$host;
        }

        $this->host = $host;
        $this->context = stream_context_create($context);
    }

    /**
     * {@inheritdoc}
     */
    public function handle(array $record): bool
    {
        if (!$this->isHandling($record)) {
            return false;
        }

        set_error_handler(self::class.'::nullErrorHandler');

        try {
            if (!$this->socket = $this->socket ?: $this->createSocket()) {
                return false === $this->bubble;
            }
        } finally {
            restore_error_handler();
        }

        return parent::handle($record);
    }

    protected function write(array $record): void
    {
        $recordFormatted = $this->formatRecord($record);

        set_error_handler(self::class.'::nullErrorHandler');

        try {
            if (-1 === stream_socket_sendto($this->socket, $recordFormatted)) {
                stream_socket_shutdown($this->socket, \STREAM_SHUT_RDWR);

                // Let's retry: the persistent connection might just be stale
                if ($this->socket = $this->createSocket()) {
                    stream_socket_sendto($this->socket, $recordFormatted);
                }
            }
        } finally {
            restore_error_handler();
        }
    }

    /**
     * {@inheritdoc}
     */
    protected function getDefaultFormatter(): FormatterInterface
    {
        return new VarDumperFormatter();
    }

    private static function nullErrorHandler()
    {
    }

    private function createSocket()
    {
        $socket = stream_socket_client($this->host, $errno, $errstr, 0, \STREAM_CLIENT_CONNECT | \STREAM_CLIENT_ASYNC_CONNECT | \STREAM_CLIENT_PERSISTENT, $this->context);

        if ($socket) {
            stream_set_blocking($socket, false);
        }

        return $socket;
    }

    private function formatRecord(array $record): string
    {
        $recordFormatted = $record['formatted'];

        foreach (['log_uuid', 'uuid', 'uid'] as $key) {
            if (isset($record['extra'][$key])) {
                $recordFormatted['log_id'] = $record['extra'][$key];
                break;
            }
        }

        return base64_encode(serialize($recordFormatted))."\n";
    }
}
