<?php

/*
 * This file is part of the HTML sanitizer project.
 *
 * (c) Titouan Galopin <galopintitouan@gmail.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace HtmlSanitizer\Bundle\Twig;

use Psr\Container\ContainerInterface;
use Twig\Extension\AbstractExtension;
use Twig\TwigFilter;

/**
 * @final
 */
class TwigExtension extends AbstractExtension
{
    private $sanitizers;
    private $default;

    public function __construct(ContainerInterface $sanitizers, string $default)
    {
        $this->sanitizers = $sanitizers;
        $this->default = $default;
    }

    public function getFilters(): array
    {
        return [
            new TwigFilter('sanitize_html', [$this, 'sanitize'], ['is_safe' => ['html']]),
        ];
    }

    public function sanitize(string $html, string $sanitizer = null): string
    {
        return $this->sanitizers->get($sanitizer ?: $this->default)->sanitize($html);
    }
}
