<?php

/*
 * This file is part of the HTML sanitizer project.
 *
 * (c) Titouan Galopin <galopintitouan@gmail.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace HtmlSanitizer\Bundle\Form;

use Psr\Container\ContainerInterface;
use Symfony\Component\Form\AbstractTypeExtension;
use Symfony\Component\Form\Extension\Core\Type\TextType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\Form\FormEvent;
use Symfony\Component\Form\FormEvents;
use Symfony\Component\OptionsResolver\OptionsResolver;

/**
 * @final
 */
class TextTypeExtension extends AbstractTypeExtension
{
    private $sanitizers;
    private $default;

    public function __construct(ContainerInterface $sanitizers, string $default)
    {
        $this->sanitizers = $sanitizers;
        $this->default = $default;
    }

    // needed for BC reasons
    public function getExtendedType()
    {
        foreach (static::getExtendedTypes() as $extendedType) {
            return $extendedType;
        }
    }

    public static function getExtendedTypes(): iterable
    {
        return [TextType::class];
    }

    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver
            ->setDefaults(['sanitize_html' => false, 'sanitizer' => null])
            ->setAllowedTypes('sanitize_html', 'bool')
            ->setAllowedTypes('sanitizer', ['string', 'null'])
        ;
    }

    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        if ($options['sanitize_html']) {
            $builder->addEventListener(
                FormEvents::PRE_SUBMIT,
                $this->createSanitizeListener($options['sanitizer']),
                999999 /* as soon as possible */
            );
        }
    }

    public function createSanitizeListener(?string $sanitizer)
    {
        $registry = $this->sanitizers;
        $default = $this->default;

        return function (FormEvent $event) use ($registry, $default, $sanitizer) {
            if (!is_scalar($data = $event->getData())) {
                return;
            }

            if (0 === mb_strlen($html = trim($data))) {
                return;
            }

            $event->setData($registry->get($sanitizer ?: $default)->sanitize($html));
        };
    }
}
