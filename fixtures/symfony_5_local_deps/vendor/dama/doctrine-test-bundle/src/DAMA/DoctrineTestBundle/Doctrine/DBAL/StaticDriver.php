<?php

namespace DAMA\DoctrineTestBundle\Doctrine\DBAL;

use Doctrine\DBAL\Connection\StaticServerVersionProvider;
use Doctrine\DBAL\Driver;
use Doctrine\DBAL\Driver\Connection;
use Doctrine\DBAL\Platforms\AbstractPlatform;

class StaticDriver extends Driver\Middleware\AbstractDriverMiddleware
{
    /**
     * @var Connection[]
     */
    private static $connections = [];

    /**
     * @var bool
     */
    private static $keepStaticConnections = false;

    public function connect(array $params): Connection
    {
        if (!self::isKeepStaticConnections()
            || !isset($params['dama.keep_static'])
            || !$params['dama.keep_static']
        ) {
            return parent::connect($params);
        }

        $key = sha1(json_encode($params));

        if (!isset(self::$connections[$key])) {
            self::$connections[$key] = parent::connect($params);
            self::$connections[$key]->beginTransaction();
        }

        $connection = self::$connections[$key];

        $platform = $this->getPlatform($connection, $params);

        if (!$platform->supportsSavepoints()) {
            throw new \RuntimeException('This bundle only works for database platforms that support savepoints.');
        }

        return new StaticConnection($connection, $platform);
    }

    public static function setKeepStaticConnections(bool $keepStaticConnections): void
    {
        self::$keepStaticConnections = $keepStaticConnections;
    }

    public static function isKeepStaticConnections(): bool
    {
        return self::$keepStaticConnections;
    }

    public static function beginTransaction(): void
    {
        foreach (self::$connections as $connection) {
            $connection->beginTransaction();
        }
    }

    public static function rollBack(): void
    {
        foreach (self::$connections as $connection) {
            $connection->rollBack();
        }
    }

    public static function commit(): void
    {
        foreach (self::$connections as $connection) {
            $connection->commit();
        }
    }

    private function getPlatform(Connection $connection, array $params): AbstractPlatform
    {
        if (isset($params['platform'])) {
            return $params['platform'];
        }

        // DBAL 3
        if (method_exists($this, 'createDatabasePlatformForVersion')) {
            if (isset($params['serverVersion'])) {
                return $this->createDatabasePlatformForVersion($params['serverVersion']);
            }

            return $this->getDatabasePlatform();
        }

        // DBAL 4
        return $this->getDatabasePlatform(
            isset($params['serverVersion'])
                ? new StaticServerVersionProvider($params['serverVersion'])
                : $connection,
        );
    }
}
