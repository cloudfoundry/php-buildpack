<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Http\EventListener;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\Security\Core\User\UserCheckerInterface;
use Symfony\Component\Security\Http\Authenticator\Passport\Badge\PreAuthenticatedUserBadge;
use Symfony\Component\Security\Http\Authenticator\Passport\UserPassportInterface;
use Symfony\Component\Security\Http\Event\CheckPassportEvent;
use Symfony\Component\Security\Http\Event\LoginSuccessEvent;

/**
 * @author Wouter de Jong <wouter@wouterj.nl>
 *
 * @final
 * @experimental in 5.1
 */
class UserCheckerListener implements EventSubscriberInterface
{
    private $userChecker;

    public function __construct(UserCheckerInterface $userChecker)
    {
        $this->userChecker = $userChecker;
    }

    public function preCheckCredentials(CheckPassportEvent $event): void
    {
        $passport = $event->getPassport();
        if (!$passport instanceof UserPassportInterface || $passport->hasBadge(PreAuthenticatedUserBadge::class)) {
            return;
        }

        $this->userChecker->checkPreAuth($passport->getUser());
    }

    public function postCheckCredentials(LoginSuccessEvent $event): void
    {
        $passport = $event->getPassport();
        if (!$passport instanceof UserPassportInterface || null === $passport->getUser()) {
            return;
        }

        $this->userChecker->checkPostAuth($passport->getUser());
    }

    public static function getSubscribedEvents(): array
    {
        return [
            CheckPassportEvent::class => ['preCheckCredentials', 256],
            LoginSuccessEvent::class => ['postCheckCredentials', 256],
        ];
    }
}
