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
use Monolog\Formatter\LogstashFormatter;
use Monolog\Handler\AbstractHandler;
use Monolog\Handler\FormattableHandlerTrait;
use Monolog\Handler\ProcessableHandlerTrait;
use Monolog\Level;
use Monolog\Logger;
use Monolog\LogRecord;
use Symfony\Component\HttpClient\HttpClient;
use Symfony\Contracts\HttpClient\Exception\ExceptionInterface;
use Symfony\Contracts\HttpClient\HttpClientInterface;
use Symfony\Contracts\HttpClient\ResponseInterface;

/**
 * Push logs directly to Elasticsearch and format them according to Logstash specification.
 *
 * This handler dials directly with the HTTP interface of Elasticsearch. This
 * means it will slow down your application if Elasticsearch takes times to
 * answer. Even if all HTTP calls are done asynchronously.
 *
 * In a development environment, it's fine to keep the default configuration:
 * for each log, an HTTP request will be made to push the log to Elasticsearch.
 *
 * In a production environment, it's highly recommended to wrap this handler
 * in a handler with buffering capabilities (like the FingersCrossedHandler, or
 * BufferHandler) in order to call Elasticsearch only once with a bulk push. For
 * even better performance and fault tolerance, a proper ELK (https://www.elastic.co/what-is/elk-stack)
 * stack is recommended.
 *
 * @author Grégoire Pineau <lyrixx@lyrixx.info>
 *
 * @final since Symfony 6.1
 */
class ElasticsearchLogstashHandler extends AbstractHandler
{
    use CompatibilityHandler;

    use FormattableHandlerTrait;
    use ProcessableHandlerTrait;

    private string $endpoint;
    private string $index;
    private HttpClientInterface $client;
    private string $elasticsearchVersion;

    /**
     * @var \SplObjectStorage<ResponseInterface, null>
     */
    private \SplObjectStorage $responses;

    public function __construct(string $endpoint = 'http://127.0.0.1:9200', string $index = 'monolog', ?HttpClientInterface $client = null, string|int|Level $level = Logger::DEBUG, bool $bubble = true, string $elasticsearchVersion = '1.0.0')
    {
        if (!interface_exists(HttpClientInterface::class)) {
            throw new \LogicException(sprintf('The "%s" handler needs an HTTP client. Try running "composer require symfony/http-client".', __CLASS__));
        }

        parent::__construct($level, $bubble);
        $this->endpoint = $endpoint;
        $this->index = $index;
        $this->client = $client ?: HttpClient::create(['timeout' => 1]);
        $this->responses = new \SplObjectStorage();
        $this->elasticsearchVersion = $elasticsearchVersion;
    }

    private function doHandle(array|LogRecord $record): bool
    {
        if (!$this->isHandling($record)) {
            return false;
        }

        $this->sendToElasticsearch([$record]);

        return !$this->bubble;
    }

    public function handleBatch(array $records): void
    {
        $records = array_filter($records, $this->isHandling(...));

        if ($records) {
            $this->sendToElasticsearch($records);
        }
    }

    protected function getDefaultFormatter(): FormatterInterface
    {
        // Monolog 1.X
        if (\defined(LogstashFormatter::class.'::V1')) {
            return new LogstashFormatter('application', null, null, 'ctxt_', LogstashFormatter::V1);
        }

        // Monolog 2.X
        return new LogstashFormatter('application');
    }

    private function sendToElasticsearch(array $records): void
    {
        $formatter = $this->getFormatter();

        if (version_compare($this->elasticsearchVersion, '7', '>=')) {
            $headers = json_encode([
                'index' => [
                    '_index' => $this->index,
                ],
            ]);
        } else {
            $headers = json_encode([
                'index' => [
                    '_index' => $this->index,
                    '_type' => '_doc',
                ],
            ]);
        }

        $body = '';
        foreach ($records as $record) {
            foreach ($this->processors as $processor) {
                $record = $processor($record);
            }

            $body .= $headers;
            $body .= "\n";
            $body .= $formatter->format($record);
            $body .= "\n";
        }

        $response = $this->client->request('POST', $this->endpoint.'/_bulk', [
            'body' => $body,
            'headers' => [
                'Content-Type' => 'application/json',
            ],
        ]);

        $this->responses->attach($response);

        $this->wait(false);
    }

    public function __sleep(): array
    {
        throw new \BadMethodCallException('Cannot serialize '.__CLASS__);
    }

    /**
     * @return void
     */
    public function __wakeup()
    {
        throw new \BadMethodCallException('Cannot unserialize '.__CLASS__);
    }

    public function __destruct()
    {
        $this->wait(true);
    }

    private function wait(bool $blocking): void
    {
        foreach ($this->client->stream($this->responses, $blocking ? null : 0.0) as $response => $chunk) {
            try {
                if ($chunk->isTimeout() && !$blocking) {
                    continue;
                }
                if (!$chunk->isFirst() && !$chunk->isLast()) {
                    continue;
                }
                if ($chunk->isLast()) {
                    $this->responses->detach($response);
                }
            } catch (ExceptionInterface $e) {
                $this->responses->detach($response);
                error_log(sprintf("Could not push logs to Elasticsearch:\n%s", (string) $e));
            }
        }
    }
}
