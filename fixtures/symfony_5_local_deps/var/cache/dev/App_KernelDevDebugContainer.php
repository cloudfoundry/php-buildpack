<?php

// This file has been auto-generated by the Symfony Dependency Injection Component for internal use.

if (\class_exists(\Container0GjhWRH\App_KernelDevDebugContainer::class, false)) {
    // no-op
} elseif (!include __DIR__.'/Container0GjhWRH/App_KernelDevDebugContainer.php') {
    touch(__DIR__.'/Container0GjhWRH.legacy');

    return;
}

if (!\class_exists(App_KernelDevDebugContainer::class, false)) {
    \class_alias(\Container0GjhWRH\App_KernelDevDebugContainer::class, App_KernelDevDebugContainer::class, false);
}

return new \Container0GjhWRH\App_KernelDevDebugContainer([
    'container.build_hash' => '0GjhWRH',
    'container.build_id' => 'a239a24f',
    'container.build_time' => 1708034881,
    'container.runtime_mode' => \in_array(\PHP_SAPI, ['cli', 'phpdbg', 'embed'], true) ? 'web=0' : 'web=1',
], __DIR__.\DIRECTORY_SEPARATOR.'Container0GjhWRH');
