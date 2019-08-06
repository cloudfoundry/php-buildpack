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

use Cake\Collection\Collection;
use Cake\ORM\TableRegistry;
use Phinx\Db\Table as BaseTable;

class Table extends BaseTable
{

    /**
     * Primary key for this table.
     * Can either be a string or an array in case of composite
     * primary key.
     *
     * @var string|array
     */
    protected $primaryKey;

    /**
     * Add a primary key to a database table.
     *
     * @param string|array $columns Table Column(s)
     * @return Table
     */
    public function addPrimaryKey($columns)
    {
        $this->primaryKey = $columns;

        return $this;
    }

    /**
     * You can pass `autoIncrement` as an option and it will be converted
     * to the correct option for phinx to create the column with an
     * auto increment attribute
     *
     * {@inheritdoc}
     */
    public function addColumn($columnName, $type = null, $options = [])
    {
        $options = $this->convertedAutoIncrement($options);

        return parent::addColumn($columnName, $type, $options);
    }

    /**
     * You can pass `autoIncrement` as an option and it will be converted
     * to the correct option for phinx to create the column with an
     * auto increment attribute
     *
     * {@inheritdoc}
     */
    public function changeColumn($columnName, $type, array $options = [])
    {
        $options = $this->convertedAutoIncrement($options);

        return parent::changeColumn($columnName, $type, $options);
    }

    /**
     * Convert the `autoIncrement` option to the correct options for phinx.
     *
     * @param array $options Options
     * @return array Converted options
     */
    protected function convertedAutoIncrement($options)
    {
        if (isset($options['autoIncrement']) && $options['autoIncrement'] === true) {
            $options['identity'] = true;
            unset($options['autoIncrement']);
        }

        return $options;
    }

    /**
     * {@inheritdoc}
     *
     * If using MySQL and no collation information has been given to the table options, a request to the information
     * schema will be made to get the default database collation and apply it to the database. This is to prevent
     * phinx default mechanism to put the collation to a default of "utf8_general_ci".
     */
    public function create()
    {
        $options = $this->getTable()->getOptions();
        if ((!isset($options['id']) || $options['id'] === false) && !empty($this->primaryKey)) {
            $options['primary_key'] = $this->primaryKey;
            $this->filterPrimaryKey();
        }

        if ($this->getAdapter()->getAdapterType() === 'mysql' && empty($options['collation'])) {
            $encodingRequest = 'SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
                FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = "%s"';

            $cakeConnection = $this->getAdapter()->getCakeConnection();
            $connectionConfig = $cakeConnection->config();
            $encodingRequest = sprintf($encodingRequest, $connectionConfig['database']);

            $defaultEncoding = $cakeConnection->execute($encodingRequest)->fetch('assoc');
            if (!empty($defaultEncoding['DEFAULT_COLLATION_NAME'])) {
                $options['collation'] = $defaultEncoding['DEFAULT_COLLATION_NAME'];
            }
        }

        $this->getTable()->setOptions($options);

        parent::create();
    }

    /**
     * {@inheritdoc}
     *
     * After a table update, the TableRegistry should be cleared in order to prevent issues with
     * table schema stored in Table objects having columns that might have been renamed or removed during
     * the update process.
     */
    public function update()
    {
        parent::update();
        TableRegistry::clear();
    }

    /**
     * {@inheritDoc}
     *
     * We disable foreign key deletion for the SQLite adapter as SQLite does not support the feature natively and the
     * process implemented by Phinx has serious side-effects (for instance it rename FK references in existing tables
     * which breaks the database schema cohesion).
     */
    public function dropForeignKey($columns, $constraint = null)
    {
        if ($this->getAdapter()->getAdapterType() == 'sqlite') {
            return $this;
        }

        return parent::dropForeignKey($columns, $constraint);
    }

    /**
     * This method is called in case a primary key was defined using the addPrimaryKey() method.
     * It currently does something only if using SQLite.
     * If a column is an auto-increment key in SQLite, it has to be a primary key and it has to defined
     * when defining the column. Phinx takes care of that so we have to make sure columns defined as autoincrement were
     * not added with the addPrimaryKey method, otherwise, SQL queries will be wrong.
     *
     * @return void
     */
    protected function filterPrimaryKey()
    {
        $options = $this->getTable()->getOptions();
        if ($this->getAdapter()->getAdapterType() !== 'sqlite' || empty($options['primary_key'])) {
            return;
        }

        $primaryKey = $options['primary_key'];
        if (!is_array($primaryKey)) {
            $primaryKey = [$primaryKey];
        }
        $primaryKey = array_flip($primaryKey);

        $columnsCollection = (new Collection($this->actions->getActions()))
            ->filter(function ($action) {
                return $action instanceof \Phinx\Db\Action\AddColumn;
            })
            ->map(function ($action) {
                return $action->getColumn();
            });
        $primaryKeyColumns = $columnsCollection->filter(function ($columnDef, $key) use ($primaryKey) {
            return isset($primaryKey[$columnDef->getName()]);
        })->toArray();

        if (empty($primaryKeyColumns)) {
            return;
        }

        foreach ($primaryKeyColumns as $primaryKeyColumn) {
            if ($primaryKeyColumn->isIdentity()) {
                unset($primaryKey[$primaryKeyColumn->getName()]);
            }
        }

        $primaryKey = array_flip($primaryKey);

        if (!empty($primaryKey)) {
            $options['primary_key'] = $primaryKey;
        } else {
            unset($options['primary_key']);
        }

        $this->getTable()->setOptions($options);
    }
}
