<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Validator\Constraints;

use Symfony\Component\Validator\Constraint;
use Symfony\Component\Validator\ConstraintValidator;
use Symfony\Component\Validator\Exception\UnexpectedTypeException;

/**
 * @author Przemysław Bogusz <przemyslaw.bogusz@tubotax.pl>
 */
class AtLeastOneOfValidator extends ConstraintValidator
{
    /**
     * {@inheritdoc}
     */
    public function validate($value, Constraint $constraint)
    {
        if (!$constraint instanceof AtLeastOneOf) {
            throw new UnexpectedTypeException($constraint, AtLeastOneOf::class);
        }

        $validator = $this->context->getValidator();

        $messages = [$constraint->message];

        foreach ($constraint->constraints as $key => $item) {
            $executionContext = clone $this->context;
            $executionContext->setNode($value, $this->context->getObject(), $this->context->getMetadata(), $this->context->getPropertyPath());
            $violations = $validator->inContext($executionContext)->validate($value, $item, $this->context->getGroup())->getViolations();

            if (\count($this->context->getViolations()) === \count($violations)) {
                return;
            }

            if ($constraint->includeInternalMessages) {
                $message = ' ['.($key + 1).'] ';

                if ($item instanceof All || $item instanceof Collection) {
                    $message .= $constraint->messageCollection;
                } else {
                    $message .= $violations->get(0)->getMessage();
                }

                $messages[] = $message;
            }
        }

        $this->context->buildViolation(implode('', $messages))
            ->setCode(AtLeastOneOf::AT_LEAST_ONE_OF_ERROR)
            ->addViolation()
        ;
    }
}
