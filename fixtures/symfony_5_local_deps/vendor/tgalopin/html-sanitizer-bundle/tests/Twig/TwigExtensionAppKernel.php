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

use HtmlSanitizer\Bundle\HtmlSanitizerBundle;
use Symfony\Bundle\FrameworkBundle\FrameworkBundle;
use Symfony\Bundle\TwigBundle\TwigBundle;
use Symfony\Component\Config\Loader\LoaderInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\HttpKernel\Kernel;
use Tests\HtmlSanitizer\Bundle\Kernel\KernelTestTrait;

/**
 * @internal
 */
class TwigExtensionAppKernel extends Kernel
{
    use KernelTestTrait;

    public function registerBundles()
    {
        return [new FrameworkBundle(), new TwigBundle(), new HtmlSanitizerBundle()];
    }

    public function registerContainerConfiguration(LoaderInterface $loader)
    {
        $loader->load(function (ContainerBuilder $container) {
            $container->loadFromExtension('framework', ['secret' => '$ecret']);
            $container->loadFromExtension('twig', ['paths' => [__DIR__.'/templates']]);

            $container->loadFromExtension('html_sanitizer', [
                'default_sanitizer' => 'default',
                'sanitizers' => [
                    'default' => [
                        'extensions' => ['basic', 'image'],
                        'tags' => ['img' => ['allowed_hosts' => ['trusted.com']]],
                    ],
                    'basic' => [
                        'extensions' => ['basic'],
                    ],
                ],
            ]);
        });
    }
}
