<?php

/*
 * This file is part of the HTML sanitizer project.
 *
 * (c) Titouan Galopin <galopintitouan@gmail.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Tests\HtmlSanitizer\Bundle\Twig;

use PHPUnit\Framework\TestCase;

/**
 * @internal
 */
class TwigExtensionTest extends TestCase
{
    public function testUseTwigExtension()
    {
        $kernel = new TwigExtensionAppKernel('test', true);
        $kernel->boot();

        $container = $kernel->getContainer();

        $this->assertTrue($container->has('twig'));

        $this->assertSame(
            trim(file_get_contents(__DIR__.'/templates/output.html')),
            trim($container->get('twig')->render('input.html.twig'))
        );
    }
}
