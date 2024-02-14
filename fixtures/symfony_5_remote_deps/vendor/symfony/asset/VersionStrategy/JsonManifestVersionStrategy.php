<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Asset\VersionStrategy;

/**
 * Reads the versioned path of an asset from a JSON manifest file.
 *
 * For example, the manifest file might look like this:
 *     {
 *         "main.js": "main.abc123.js",
 *         "css/styles.css": "css/styles.555abc.css"
 *     }
 *
 * You could then ask for the version of "main.js" or "css/styles.css".
 */
class JsonManifestVersionStrategy implements VersionStrategyInterface
{
    private $manifestPath;
    private $manifestData;

    /**
     * @param string $manifestPath Absolute path to the manifest file
     */
    public function __construct(string $manifestPath)
    {
        $this->manifestPath = $manifestPath;
    }

    /**
     * With a manifest, we don't really know or care about what
     * the version is. Instead, this returns the path to the
     * versioned file.
     */
    public function getVersion(string $path)
    {
        return $this->applyVersion($path);
    }

    public function applyVersion(string $path)
    {
        return $this->getManifestPath($path) ?: $path;
    }

    private function getManifestPath(string $path): ?string
    {
        if (null === $this->manifestData) {
            if (!is_file($this->manifestPath)) {
                throw new \RuntimeException(sprintf('Asset manifest file "%s" does not exist.', $this->manifestPath));
            }

            $this->manifestData = json_decode(file_get_contents($this->manifestPath), true);
            if (0 < json_last_error()) {
                throw new \RuntimeException(sprintf('Error parsing JSON from asset manifest file "%s": ', $this->manifestPath).json_last_error_msg());
            }
        }

        return $this->manifestData[$path] ?? null;
    }
}
