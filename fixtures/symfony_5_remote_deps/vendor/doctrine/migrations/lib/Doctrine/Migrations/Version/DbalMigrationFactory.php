<?php

declare(strict_types=1);

namespace Doctrine\Migrations\Version;

use Doctrine\DBAL\Connection;
use Doctrine\Migrations\AbstractMigration;
use Psr\Log\LoggerInterface;

/**
 * The DbalMigrationFactory class is responsible for creating instances of a migration class name for a DBAL connection.
 *
 * @var internal
 */
final class DbalMigrationFactory implements MigrationFactory
{
    /** @var Connection */
    private $connection;

    /** @var LoggerInterface */
    private $logger;

    public function __construct(Connection $connection, LoggerInterface $logger)
    {
        $this->connection = $connection;
        $this->logger     = $logger;
    }

    public function createVersion(string $migrationClassName) : AbstractMigration
    {
        return new $migrationClassName(
            $this->connection,
            $this->logger
        );
    }
}
