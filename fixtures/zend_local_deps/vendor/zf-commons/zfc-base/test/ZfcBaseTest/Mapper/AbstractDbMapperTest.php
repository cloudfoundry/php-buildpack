<?php
namespace ZfcBaseTest\Mapper;

use PHPUnit_Framework_TestCase;
use Zend\Db\Adapter\Adapter;
use ZfcBase\Db\Adapter\MasterSlaveAdapter;
use ZfcBaseTest\Mapper\TestAsset\TestMapper;

class AbstractDbMapperTest extends PHPUnit_Framework_TestCase
{
    public function setup()
    {
        $this->mockDriver = $this->getMock('Zend\Db\Adapter\Driver\DriverInterface');
        $this->mockConnection = $this->getMock('Zend\Db\Adapter\Driver\ConnectionInterface');
        $this->mockDriver->expects($this->any())->method('checkEnvironment')->will($this->returnValue(true));
        $this->mockDriver->expects($this->any())->method('getConnection')->will($this->returnValue($this->mockConnection));
        $this->mockPlatform = $this->getMock('Zend\Db\Adapter\Platform\PlatformInterface');
        $this->mockStatement = $this->getMock('Zend\Db\Adapter\Driver\StatementInterface');
        $this->mockDriver->expects($this->any())->method('createStatement')->will($this->returnValue($this->mockStatement));

        $this->adapter = new Adapter($this->mockDriver, $this->mockPlatform);
        $this->masterSlaveAdapter = new MasterSlaveAdapter($this->adapter, $this->mockDriver, $this->mockPlatform);
    }

    public function testSetMasterAndSlaveDbAdapterSettersAndGettersWorksAsExpected()
    {
        $this->mapper = new TestMapper;
        $this->mapper->setDbAdapter($this->adapter);
        $this->assertSame($this->adapter, $this->mapper->getDbAdapter());
        $this->assertSame($this->adapter, $this->mapper->getDbSlaveAdapter());
        $newAdapter = new Adapter($this->mockDriver, $this->mockPlatform);
        $this->mapper->setDbSlaveAdapter($newAdapter);
        $this->assertSame($newAdapter, $this->mapper->getDbSlaveAdapter());
        unset($this->mapper);
    }

    public function testSetMasterSlaveDbAdapterSetterAndGettersAlsoWorksAsExpected()
    {
        $this->mapper = new TestMapper;
        $this->mapper->setDbAdapter($this->masterSlaveAdapter);
        $this->assertSame($this->masterSlaveAdapter, $this->mapper->getDbAdapter());
        $this->assertSame($this->adapter, $this->mapper->getDbSlaveAdapter());
        $newAdapter = new Adapter($this->mockDriver, $this->mockPlatform);
        $this->mapper->setDbSlaveAdapter($newAdapter);
        $this->assertSame($newAdapter, $this->mapper->getDbSlaveAdapter());
        unset($this->mapper);
    }
}
