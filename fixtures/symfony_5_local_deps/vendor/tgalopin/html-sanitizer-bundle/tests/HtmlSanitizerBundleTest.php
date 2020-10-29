<?php

/*
 * This file is part of the HTML sanitizer project.
 *
 * (c) Titouan Galopin <galopintitouan@gmail.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Tests\HtmlSanitizer\Bundle;

use PHPUnit\Framework\TestCase;
use Symfony\Component\HttpKernel\Kernel;
use Tests\HtmlSanitizer\Bundle\Kernel\EmptyAppKernel;
use Tests\HtmlSanitizer\Bundle\Kernel\FrameworkBundleAppKernel;
use Tests\HtmlSanitizer\Bundle\Kernel\TwigBundleAppKernel;

/**
 * @internal
 */
class HtmlSanitizerBundleTest extends TestCase
{
    public function provideKernels()
    {
        yield 'empty' => [new EmptyAppKernel('test', true)];
        yield 'framework' => [new FrameworkBundleAppKernel('test', true)];
        yield 'twig' => [new TwigBundleAppKernel('test', true)];
    }

    /**
     * @dataProvider provideKernels
     */
    public function testBootKernel(Kernel $kernel)
    {
        $kernel->boot();
        $this->assertArrayHasKey('HtmlSanitizerBundle', $kernel->getBundles());
    }
}
