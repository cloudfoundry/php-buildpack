<?php

/*
 * This file is part of the HTML sanitizer project.
 *
 * (c) Titouan Galopin <galopintitouan@gmail.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace HtmlSanitizer\Bundle;

use HtmlSanitizer\Bundle\DependencyInjection\CompilerPass\RegisterUserExtensionsCompilerPass;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\HttpKernel\Bundle\Bundle;

/**
 * @author Titouan Galopin <galopintitouan@gmail.com>
 *
 * @final
 */
class HtmlSanitizerBundle extends Bundle
{
    public function build(ContainerBuilder $container)
    {
        parent::build($container);

        $container->addCompilerPass(new RegisterUserExtensionsCompilerPass());
    }
}
