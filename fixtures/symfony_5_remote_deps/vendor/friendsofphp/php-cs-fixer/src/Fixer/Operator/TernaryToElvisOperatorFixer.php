<?php

/*
 * This file is part of PHP CS Fixer.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *     Dariusz Rumiński <dariusz.ruminski@gmail.com>
 *
 * This source file is subject to the MIT license that is bundled
 * with this source code in the file LICENSE.
 */

namespace PhpCsFixer\Fixer\Operator;

use PhpCsFixer\AbstractFixer;
use PhpCsFixer\FixerDefinition\CodeSample;
use PhpCsFixer\FixerDefinition\FixerDefinition;
use PhpCsFixer\Tokenizer\CT;
use PhpCsFixer\Tokenizer\Tokens;

/**
 * @author SpacePossum
 */
final class TernaryToElvisOperatorFixer extends AbstractFixer
{
    /**
     * @internal
     *
     * Lower precedence and other valid preceding tokens.
     *
     * Ordered by most common types first.
     *
     * @var array
     */
    const VALID_BEFORE_ENDTYPES = [
        '=',
        [T_OPEN_TAG],
        [T_OPEN_TAG_WITH_ECHO],
        '(',
        ',',
        ';',
        '[',
        '{',
        '}',
        [CT::T_ARRAY_INDEX_CURLY_BRACE_OPEN],
        [T_AND_EQUAL],    // &=
        [T_CONCAT_EQUAL], // .=
        [T_DIV_EQUAL],    // /=
        [T_MINUS_EQUAL],  // -=
        [T_MOD_EQUAL],    // %=
        [T_MUL_EQUAL],    // *=
        [T_OR_EQUAL],     // |=
        [T_PLUS_EQUAL],   // +=
        [T_POW_EQUAL],    // **=
        [T_SL_EQUAL],     // <<=
        [T_SR_EQUAL],     // >>=
        [T_XOR_EQUAL],    // ^=
    ];

    /**
     * {@inheritdoc}
     */
    public function getDefinition()
    {
        return new FixerDefinition(
            'Use the Elvis operator `?:` where possible.',
            [
                new CodeSample(
                    "<?php\n\$foo = \$foo ? \$foo : 1;\n"
                ),
                new CodeSample(
                    "<?php \$foo = \$bar[a()] ? \$bar[a()] : 1; # \"risky\" sample, \"a()\" only gets called once after fixing\n"
                ),
            ],
            null,
            'Risky when relying on functions called on both sides of the `?` operator.'
        );
    }

    /**
     * {@inheritdoc}
     *
     * Must run before NoTrailingWhitespaceFixer, TernaryOperatorSpacesFixer.
     */
    public function getPriority()
    {
        return 1;
    }

    /**
     * {@inheritdoc}
     */
    public function isCandidate(Tokens $tokens)
    {
        return $tokens->isTokenKindFound('?');
    }

    /**
     * {@inheritdoc}
     */
    public function isRisky()
    {
        return true;
    }

    /**
     * {@inheritdoc}
     */
    protected function applyFix(\SplFileInfo $file, Tokens $tokens)
    {
        $blockEdgeDefinitions = Tokens::getBlockEdgeDefinitions();

        for ($index = \count($tokens) - 5; $index > 1; --$index) {
            if (!$tokens[$index]->equals('?')) {
                continue;
            }

            $nextIndex = $tokens->getNextMeaningfulToken($index);

            if ($tokens[$nextIndex]->equals(':')) {
                continue; // Elvis is alive!
            }

            // get and check what is before the `?` operator

            $beforeOperator = $this->getBeforeOperator($tokens, $index, $blockEdgeDefinitions);

            if (null === $beforeOperator) {
                continue; // contains something we cannot fix because of priorities
            }

            // get what is after the `?` token

            $afterOperator = $this->getAfterOperator($tokens, $index);

            // if before and after the `?` operator are the same (in meaningful matter), clear after

            if ($this->rangeEqualsRange($tokens, $beforeOperator, $afterOperator)) {
                $this->clearMeaningfulFromRange($tokens, $afterOperator);
            }
        }
    }

    /**
     * @param int $index
     *
     * @return null|array null if contains ++/-- operator
     */
    private function getBeforeOperator(Tokens $tokens, $index, array $blockEdgeDefinitions)
    {
        $index = $tokens->getPrevMeaningfulToken($index);
        $before = ['end' => $index];

        while (!$tokens[$index]->equalsAny(self::VALID_BEFORE_ENDTYPES)) {
            if ($tokens[$index]->isGivenKind([T_INC, T_DEC])) {
                return null;
            }

            $blockType = Tokens::detectBlockType($tokens[$index]);

            if (null === $blockType || $blockType['isStart']) {
                $before['start'] = $index;
                $index = $tokens->getPrevMeaningfulToken($index);

                continue;
            }

            $blockType = $blockEdgeDefinitions[$blockType['type']];
            $openCount = 1;

            do {
                $index = $tokens->getPrevMeaningfulToken($index);

                if ($tokens[$index]->isGivenKind([T_INC, T_DEC])) {
                    return null;
                }

                if ($tokens[$index]->equals($blockType['start'])) {
                    ++$openCount;

                    continue;
                }

                if ($tokens[$index]->equals($blockType['end'])) {
                    --$openCount;
                }
            } while (1 >= $openCount);

            $before['start'] = $index;
            $index = $tokens->getPrevMeaningfulToken($index);
        }

        if (!isset($before['start'])) {
            return null;
        }

        return $before;
    }

    /**
     * @param int $index
     *
     * @return array
     */
    private function getAfterOperator(Tokens $tokens, $index)
    {
        $index = $tokens->getNextMeaningfulToken($index);
        $after = ['start' => $index];

        while (!$tokens[$index]->equals(':')) {
            $blockType = Tokens::detectBlockType($tokens[$index]);

            if (null !== $blockType) {
                $index = $tokens->findBlockEnd($blockType['type'], $index);
            }

            $after['end'] = $index;
            $index = $tokens->getNextMeaningfulToken($index);
        }

        return $after;
    }

    /**
     * Meaningful compare of tokens within ranges.
     *
     * @return bool
     */
    private function rangeEqualsRange(Tokens $tokens, array $range1, array $range2)
    {
        $leftStart = $range1['start'];
        $leftEnd = $range1['end'];

        while ($tokens[$leftStart]->equals('(') && $tokens[$leftEnd]->equals(')')) {
            $leftStart = $tokens->getNextMeaningfulToken($leftStart);
            $leftEnd = $tokens->getPrevMeaningfulToken($leftEnd);
        }

        $rightStart = $range2['start'];
        $rightEnd = $range2['end'];

        while ($tokens[$rightStart]->equals('(') && $tokens[$rightEnd]->equals(')')) {
            $rightStart = $tokens->getNextMeaningfulToken($rightStart);
            $rightEnd = $tokens->getPrevMeaningfulToken($rightEnd);
        }

        while ($leftStart <= $leftEnd && $rightStart <= $rightEnd) {
            if (
                !$tokens[$leftStart]->equals($tokens[$rightStart])
                && !($tokens[$leftStart]->equalsAny(['[', [CT::T_ARRAY_INDEX_CURLY_BRACE_OPEN]]) && $tokens[$rightStart]->equalsAny(['[', [CT::T_ARRAY_INDEX_CURLY_BRACE_OPEN]]))
                && !($tokens[$leftStart]->equalsAny([']', [CT::T_ARRAY_INDEX_CURLY_BRACE_CLOSE]]) && $tokens[$rightStart]->equalsAny([']', [CT::T_ARRAY_INDEX_CURLY_BRACE_CLOSE]]))
            ) {
                return false;
            }

            $leftStart = $tokens->getNextMeaningfulToken($leftStart);
            $rightStart = $tokens->getNextMeaningfulToken($rightStart);
        }

        return $leftStart > $leftEnd && $rightStart > $rightEnd;
    }

    private function clearMeaningfulFromRange(Tokens $tokens, array $range)
    {
        // $range['end'] must be meaningful!
        for ($i = $range['end']; $i >= $range['start']; $i = $tokens->getPrevMeaningfulToken($i)) {
            $tokens->clearTokenAndMergeSurroundingWhitespace($i);
        }
    }
}
