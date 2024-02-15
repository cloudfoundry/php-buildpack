<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Bridge\Doctrine\DataCollector;

use Doctrine\DBAL\Logging\DebugStack;
use Doctrine\DBAL\Types\ConversionException;
use Doctrine\DBAL\Types\Type;
use Doctrine\Persistence\ManagerRegistry;
use Symfony\Bridge\Doctrine\Middleware\Debug\DebugDataHolder;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\DataCollector\DataCollector;
use Symfony\Component\VarDumper\Caster\Caster;
use Symfony\Component\VarDumper\Cloner\Stub;

/**
 * DoctrineDataCollector.
 *
 * @author Fabien Potencier <fabien@symfony.com>
 */
class DoctrineDataCollector extends DataCollector
{
    private array $connections;
    private array $managers;

    /**
     * @var array<string, DebugStack>
     */
    private array $loggers = [];

    public function __construct(
        private ManagerRegistry $registry,
        private ?DebugDataHolder $debugDataHolder = null,
    ) {
        $this->connections = $registry->getConnectionNames();
        $this->managers = $registry->getManagerNames();

        if (null === $debugDataHolder) {
            trigger_deprecation('symfony/doctrine-bridge', '6.4', 'Not passing an instance of "%s" as "$debugDataHolder" to "%s()" is deprecated.', DebugDataHolder::class, __METHOD__);
        }
    }

    /**
     * Adds the stack logger for a connection.
     *
     * @return void
     *
     * @deprecated since Symfony 6.4, use a DebugDataHolder instead.
     */
    public function addLogger(string $name, DebugStack $logger)
    {
        trigger_deprecation('symfony/doctrine-bridge', '6.4', '"%s()" is deprecated. Pass an instance of "%s" to the constructor instead.', __METHOD__, DebugDataHolder::class);

        $this->loggers[$name] = $logger;
    }

    /**
     * @return void
     */
    public function collect(Request $request, Response $response, ?\Throwable $exception = null)
    {
        $this->data = [
            'queries' => $this->collectQueries(),
            'connections' => $this->connections,
            'managers' => $this->managers,
        ];
    }

    private function collectQueries(): array
    {
        $queries = [];

        if (null !== $this->debugDataHolder) {
            foreach ($this->debugDataHolder->getData() as $name => $data) {
                $queries[$name] = $this->sanitizeQueries($name, $data);
            }

            return $queries;
        }

        foreach ($this->loggers as $name => $logger) {
            $queries[$name] = $this->sanitizeQueries($name, $logger->queries);
        }

        return $queries;
    }

    /**
     * @return void
     */
    public function reset()
    {
        $this->data = [];

        if (null !== $this->debugDataHolder) {
            $this->debugDataHolder->reset();

            return;
        }

        foreach ($this->loggers as $logger) {
            $logger->queries = [];
            $logger->currentQuery = 0;
        }
    }

    /**
     * @return array
     */
    public function getManagers()
    {
        return $this->data['managers'];
    }

    /**
     * @return array
     */
    public function getConnections()
    {
        return $this->data['connections'];
    }

    /**
     * @return int
     */
    public function getQueryCount()
    {
        return array_sum(array_map('count', $this->data['queries']));
    }

    /**
     * @return array
     */
    public function getQueries()
    {
        return $this->data['queries'];
    }

    /**
     * @return float
     */
    public function getTime()
    {
        $time = 0;
        foreach ($this->data['queries'] as $queries) {
            foreach ($queries as $query) {
                $time += $query['executionMS'];
            }
        }

        return $time;
    }

    public function getName(): string
    {
        return 'db';
    }

    protected function getCasters(): array
    {
        return parent::getCasters() + [
            ObjectParameter::class => static function (ObjectParameter $o, array $a, Stub $s): array {
                $s->class = $o->getClass();
                $s->value = $o->getObject();

                $r = new \ReflectionClass($o->getClass());
                if ($f = $r->getFileName()) {
                    $s->attr['file'] = $f;
                    $s->attr['line'] = $r->getStartLine();
                } else {
                    unset($s->attr['file']);
                    unset($s->attr['line']);
                }

                if ($error = $o->getError()) {
                    return [Caster::PREFIX_VIRTUAL.'⚠' => $error->getMessage()];
                }

                if ($o->isStringable()) {
                    return [Caster::PREFIX_VIRTUAL.'__toString()' => (string) $o->getObject()];
                }

                return [Caster::PREFIX_VIRTUAL.'⚠' => sprintf('Object of class "%s" could not be converted to string.', $o->getClass())];
            },
        ];
    }

    private function sanitizeQueries(string $connectionName, array $queries): array
    {
        foreach ($queries as $i => $query) {
            $queries[$i] = $this->sanitizeQuery($connectionName, $query);
        }

        return $queries;
    }

    private function sanitizeQuery(string $connectionName, array $query): array
    {
        $query['explainable'] = true;
        $query['runnable'] = true;
        $query['params'] ??= [];
        if (!\is_array($query['params'])) {
            $query['params'] = [$query['params']];
        }
        if (!\is_array($query['types'])) {
            $query['types'] = [];
        }
        foreach ($query['params'] as $j => $param) {
            $e = null;
            if (isset($query['types'][$j])) {
                // Transform the param according to the type
                $type = $query['types'][$j];
                if (\is_string($type)) {
                    $type = Type::getType($type);
                }
                if ($type instanceof Type) {
                    $query['types'][$j] = $type->getBindingType();
                    try {
                        $param = $type->convertToDatabaseValue($param, $this->registry->getConnection($connectionName)->getDatabasePlatform());
                    } catch (\TypeError $e) {
                    } catch (ConversionException $e) {
                    }
                }
            }

            [$query['params'][$j], $explainable, $runnable] = $this->sanitizeParam($param, $e);
            if (!$explainable) {
                $query['explainable'] = false;
            }

            if (!$runnable) {
                $query['runnable'] = false;
            }
        }

        $query['params'] = $this->cloneVar($query['params']);

        return $query;
    }

    /**
     * Sanitizes a param.
     *
     * The return value is an array with the sanitized value and a boolean
     * indicating if the original value was kept (allowing to use the sanitized
     * value to explain the query).
     */
    private function sanitizeParam(mixed $var, ?\Throwable $error): array
    {
        if (\is_object($var)) {
            return [$o = new ObjectParameter($var, $error), false, $o->isStringable() && !$error];
        }

        if ($error) {
            return ['⚠ '.$error->getMessage(), false, false];
        }

        if (\is_array($var)) {
            $a = [];
            $explainable = $runnable = true;
            foreach ($var as $k => $v) {
                [$value, $e, $r] = $this->sanitizeParam($v, null);
                $explainable = $explainable && $e;
                $runnable = $runnable && $r;
                $a[$k] = $value;
            }

            return [$a, $explainable, $runnable];
        }

        if (\is_resource($var)) {
            return [sprintf('/* Resource(%s) */', get_resource_type($var)), false, false];
        }

        return [$var, true, true];
    }
}
