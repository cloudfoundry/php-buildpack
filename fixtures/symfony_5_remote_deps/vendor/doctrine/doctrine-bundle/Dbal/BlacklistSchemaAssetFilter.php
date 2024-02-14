<?php

namespace Doctrine\Bundle\DoctrineBundle\Dbal;

use Doctrine\DBAL\Schema\AbstractAsset;
use function in_array;

class BlacklistSchemaAssetFilter
{
    /** @var string[] */
    private $blacklist;

    /**
     * @param string[] $blacklist
     */
    public function __construct(array $blacklist)
    {
        $this->blacklist = $blacklist;
    }

    public function __invoke($assetName) : bool
    {
        if ($assetName instanceof AbstractAsset) {
            $assetName = $assetName->getName();
        }

        return ! in_array($assetName, $this->blacklist, true);
    }
}
