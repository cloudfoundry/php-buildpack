<?php

/*
 * This file is part of the HTML sanitizer project.
 *
 * (c) Titouan Galopin <galopintitouan@gmail.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Tests\HtmlSanitizer\Bundle\Extension;

use HtmlSanitizer\SanitizerBuilder;
use HtmlSanitizer\SanitizerInterface;
use PHPUnit\Framework\TestCase;

/**
 * @internal
 */
class CustomExtensionTest extends TestCase
{
    public function testExtensionLoaded()
    {
        $kernel = new CustomExtensionAppKernel('test', true);
        $kernel->boot();

        /** @var SanitizerBuilder $builder */
        $builder = $kernel->getContainer()->get('test.html_sanitizer.builder');

        // This shouldn't fail as the extension should be loaded
        $sanitizer = $builder->build(['extensions' => ['custom']]);
        $this->assertInstanceOf(SanitizerInterface::class, $sanitizer);
    }
}
