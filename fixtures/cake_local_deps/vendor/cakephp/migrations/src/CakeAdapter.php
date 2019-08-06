<?php
/**
 * Copyright (c) Cake Software Foundation, Inc. (http://cakefoundation.org)
 *
 * Licensed under The MIT License
 * Redistributions of files must retain the above copyright notice.
 *
 * @copyright     Copyright (c) Cake Software Foundation, Inc. (http://cakefoundation.org)
 * @link          http://cakephp.org CakePHP(tm) Project
 * @license       http://www.opensource.org/licenses/mit-license.php MIT License
 */
namespace Migrations;

use Cake\Database\Connection;
use Cake\Database\Driver\Postgres;
use PDO;
use Phinx\Db\Adapter\AdapterInterface;
use Phinx\Db\Adapter\AdapterWrapper;
use Phinx\Db\Table as PhinxTable;
use Phinx\Db\Table\Column;
use Phinx\Db\Table\ForeignKey;
use Phinx\Db\Table\Index;
use Phinx\Migration\MigrationInterface;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

/**
 * Decorates an AdapterInterface in order to proxy some method to the actual
 * connection object.
 */
class CakeAdapter extends AdapterWrapper
{

    /**
     * Database connection
     *
     * @var \Cake\Database\Connection
     */
    protected $connection;

    /**
     * Constructor
     *
     * @param \Phinx\Db\Adapter\AdapterInterface $adapter The original adapter to decorate.
     * @param \Cake\Database\Connection|null $connection The connection to actually use.
     */
    public function __construct(AdapterInterface $adapter, Connection $connection = null)
    {
        if ($connection === null) {
            throw new \InvalidArgumentException("The cake connection cannot be null");
        }

        parent::__construct($adapter);

        $this->connection = $connection;
        $pdo = $adapter->getConnection();

        if ($pdo->getAttribute(PDO::ATTR_ERRMODE) !== PDO::ERRMODE_EXCEPTION) {
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        }
        $connection->cacheMetadata(false);

        if ($connection->getDriver() instanceof Postgres) {
            $config = $connection->config();
            $schema = empty($config['schema']) ? 'public' : $config['schema'];
            $pdo->exec('SET search_path TO ' . $schema);
        }
        $connection->getDriver()->setConnection($pdo);
    }

    /**
     * Gets the CakePHP Connection object.
     *
     * @return \Cake\Database\Connection
     */
    public function getCakeConnection()
    {
        return $this->connection;
    }

    /**
     * Returns a new Query object
     *
     * @return \Cake\Database\Query
     */
    public function getQueryBuilder()
    {
        return $this->getCakeConnection()->newQuery();
    }

    /**
     * Returns the adapter type name, for example mysql
     *
     * @return string
     */
    public function getAdapterType()
    {
        return $this->getAdapter()->getAdapterType();
    }
}
