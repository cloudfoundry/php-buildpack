<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Form\Extension\Core\EventListener;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\Form\FormError;
use Symfony\Component\Form\FormEvent;
use Symfony\Component\Form\FormEvents;
use Symfony\Contracts\Translation\TranslatorInterface;

/**
 * @author Christian Flothmann <christian.flothmann@sensiolabs.de>
 */
class TransformationFailureListener implements EventSubscriberInterface
{
    private $translator;

    public function __construct(TranslatorInterface $translator = null)
    {
        $this->translator = $translator;
    }

    public static function getSubscribedEvents()
    {
        return [
            FormEvents::POST_SUBMIT => ['convertTransformationFailureToFormError', -1024],
        ];
    }

    public function convertTransformationFailureToFormError(FormEvent $event)
    {
        $form = $event->getForm();

        if (null === $form->getTransformationFailure() || !$form->isValid()) {
            return;
        }

        foreach ($form as $child) {
            if (!$child->isSynchronized()) {
                return;
            }
        }

        $clientDataAsString = is_scalar($form->getViewData()) ? (string) $form->getViewData() : get_debug_type($form->getViewData());
        $messageTemplate = 'The value {{ value }} is not valid.';

        if (null !== $this->translator) {
            $message = $this->translator->trans($messageTemplate, ['{{ value }}' => $clientDataAsString]);
        } else {
            $message = strtr($messageTemplate, ['{{ value }}' => $clientDataAsString]);
        }

        $form->addError(new FormError($message, $messageTemplate, ['{{ value }}' => $clientDataAsString], null, $form->getTransformationFailure()));
    }
}
