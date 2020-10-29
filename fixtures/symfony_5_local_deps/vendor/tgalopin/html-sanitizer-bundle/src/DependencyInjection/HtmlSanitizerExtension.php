<?php

/*
 * This file is part of the HTML sanitizer project.
 *
 * (c) Titouan Galopin <galopintitouan@gmail.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace HtmlSanitizer\Bundle\DependencyInjection;

use HtmlSanitizer\Bundle\Form\TextTypeExtension;
use HtmlSanitizer\Bundle\Twig\TwigExtension;
use HtmlSanitizer\Extension\ExtensionInterface;
use HtmlSanitizer\SanitizerInterface;
use Symfony\Component\Config\FileLocator;
use Symfony\Component\DependencyInjection\Argument\ServiceClosureArgument;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Definition;
use Symfony\Component\DependencyInjection\Loader\XmlFileLoader;
use Symfony\Component\DependencyInjection\Reference;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\HttpKernel\DependencyInjection\Extension;
use Twig\Environment;

/**
 * @author Titouan Galopin <galopintitouan@gmail.com>
 *
 * @final
 */
class HtmlSanitizerExtension extends Extension
{
    public function load(array $configs, ContainerBuilder $container)
    {
        $configuration = new Configuration();
        $config = $this->processConfiguration($configuration, $configs);

        $loader = new XmlFileLoader($container, new FileLocator(__DIR__.'/../Resources/config'));
        $loader->load('services.xml');

        $container->registerForAutoconfiguration(ExtensionInterface::class)->addTag('html_sanitizer.extension');

        $this->registerSanitizers($container, $config['sanitizers'], $config['default_sanitizer']);

        if (class_exists(TextType::class)) {
            $this->registerFormExtension($container, $config['default_sanitizer']);
        }

        if (class_exists(Environment::class)) {
            $this->registerTwigExtension($container, $config['default_sanitizer']);
        }
    }

    private function registerSanitizers(ContainerBuilder $container, array $sanitizers, string $default)
    {
        if (!array_key_exists($default, $sanitizers)) {
            throw new \InvalidArgumentException(sprintf(
                'You have configured a non-existent default sanitizer "%s" (available sanitizers: %s)',
                $default,
                implode(', ', array_keys($sanitizers))
            ));
        }

        $refMap = [];
        foreach ($sanitizers as $name => $config) {
            $definition = new Definition(SanitizerInterface::class, [$config]);
            $definition->setFactory([new Reference('html_sanitizer.builder'), 'build']);

            $container->setDefinition('html_sanitizer.'.$name, $definition);

            if ($name === $default) {
                $container->setAlias(SanitizerInterface::class, 'html_sanitizer.'.$name);
                $container->setAlias('html_sanitizer', 'html_sanitizer.'.$name);
            }

            $refMap[$name] = new ServiceClosureArgument(new Reference('html_sanitizer.'.$name));
        }

        $registry = $container->getDefinition('html_sanitizer.registry');
        $registry->setArgument(0, $refMap);
    }

    private function registerFormExtension(ContainerBuilder $container, string $default)
    {
        $extension = new Definition(TextTypeExtension::class, [new Reference('html_sanitizer.registry'), $default]);
        $extension->addTag('form.type_extension', ['extended_type' => TextType::class]);

        $container->setDefinition('html_sanitizer.form.text_type_extension', $extension);
    }

    private function registerTwigExtension(ContainerBuilder $container, string $default)
    {
        $extension = new Definition(TwigExtension::class, [new Reference('html_sanitizer.registry'), $default]);
        $extension->addTag('twig.extension');

        $container->setDefinition('html_sanitizer.twig_extension', $extension);
    }
}
