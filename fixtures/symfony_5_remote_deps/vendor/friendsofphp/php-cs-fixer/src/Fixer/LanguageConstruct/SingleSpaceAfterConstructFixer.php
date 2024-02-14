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

namespace PhpCsFixer\Fixer\LanguageConstruct;

use PhpCsFixer\AbstractFixer;
use PhpCsFixer\Fixer\ConfigurableFixerInterface;
use PhpCsFixer\FixerConfiguration\AllowedValueSubset;
use PhpCsFixer\FixerConfiguration\FixerConfigurationResolver;
use PhpCsFixer\FixerConfiguration\FixerOptionBuilder;
use PhpCsFixer\FixerDefinition\CodeSample;
use PhpCsFixer\FixerDefinition\FixerDefinition;
use PhpCsFixer\FixerDefinition\VersionSpecification;
use PhpCsFixer\FixerDefinition\VersionSpecificCodeSample;
use PhpCsFixer\Preg;
use PhpCsFixer\Tokenizer\CT;
use PhpCsFixer\Tokenizer\Token;
use PhpCsFixer\Tokenizer\Tokens;

/**
 * @author Andreas Möller <am@localheinz.com>
 */
final class SingleSpaceAfterConstructFixer extends AbstractFixer implements ConfigurableFixerInterface
{
    /**
     * @var array<string, null|int>
     */
    private static $tokenMap = [
        'abstract' => T_ABSTRACT,
        'as' => T_AS,
        'break' => T_BREAK,
        'case' => T_CASE,
        'catch' => T_CATCH,
        'class' => T_CLASS,
        'clone' => T_CLONE,
        'const' => T_CONST,
        'const_import' => CT::T_CONST_IMPORT,
        'continue' => T_CONTINUE,
        'do' => T_DO,
        'echo' => T_ECHO,
        'else' => T_ELSE,
        'elseif' => T_ELSEIF,
        'extends' => T_EXTENDS,
        'final' => T_FINAL,
        'finally' => T_FINALLY,
        'for' => T_FOR,
        'foreach' => T_FOREACH,
        'function' => T_FUNCTION,
        'function_import' => CT::T_FUNCTION_IMPORT,
        'global' => T_GLOBAL,
        'goto' => T_GOTO,
        'if' => T_IF,
        'implements' => T_IMPLEMENTS,
        'include' => T_INCLUDE,
        'include_once' => T_INCLUDE_ONCE,
        'instanceof' => T_INSTANCEOF,
        'insteadof' => T_INSTEADOF,
        'interface' => T_INTERFACE,
        'new' => T_NEW,
        'open_tag_with_echo' => T_OPEN_TAG_WITH_ECHO,
        'php_open' => T_OPEN_TAG,
        'print' => T_PRINT,
        'private' => T_PRIVATE,
        'protected' => T_PROTECTED,
        'public' => T_PUBLIC,
        'require' => T_REQUIRE,
        'require_once' => T_REQUIRE_ONCE,
        'return' => T_RETURN,
        'static' => T_STATIC,
        'throw' => T_THROW,
        'trait' => T_TRAIT,
        'try' => T_TRY,
        'use' => T_USE,
        'use_lambda' => CT::T_USE_LAMBDA,
        'use_trait' => CT::T_USE_TRAIT,
        'var' => T_VAR,
        'while' => T_WHILE,
        'yield' => T_YIELD,
        'yield_from' => null,
    ];

    /**
     * @var array<string, int>
     */
    private $fixTokenMap = [];

    /**
     * {@inheritdoc}
     */
    public function configure(array $configuration = null)
    {
        parent::configure($configuration);

        if (70000 <= \PHP_VERSION_ID) {
            self::$tokenMap['yield_from'] = T_YIELD_FROM;
        }

        $this->fixTokenMap = [];

        foreach ($this->configuration['constructs'] as $key) {
            $this->fixTokenMap[$key] = self::$tokenMap[$key];
        }
    }

    /**
     * {@inheritdoc}
     */
    public function getDefinition()
    {
        return new FixerDefinition(
            'Ensures a single space after language constructs.',
            [
                new CodeSample(
                    '<?php

throw  new  \Exception();
'
                ),
                new CodeSample(
                    '<?php

echo  "Hello!";
',
                    [
                        'constructs' => [
                            'echo',
                        ],
                    ]
                ),
                new VersionSpecificCodeSample(
                    '<?php

yield  from  baz();
',
                    new VersionSpecification(70000),
                    [
                        'constructs' => [
                            'yield_from',
                        ],
                    ]
                ),
            ]
        );
    }

    /**
     * {@inheritdoc}
     */
    public function isCandidate(Tokens $tokens)
    {
        return $tokens->isAnyTokenKindsFound(array_values($this->fixTokenMap)) && !$tokens->hasAlternativeSyntax();
    }

    /**
     * {@inheritdoc}
     */
    protected function applyFix(\SplFileInfo $file, Tokens $tokens)
    {
        $tokenKinds = array_values($this->fixTokenMap);

        for ($index = $tokens->count() - 2; $index >= 0; --$index) {
            $token = $tokens[$index];

            if (!$token->isGivenKind($tokenKinds)) {
                continue;
            }

            $whitespaceTokenIndex = $index + 1;

            if (';' === $tokens[$whitespaceTokenIndex]->getContent()) {
                continue;
            }

            if (
                $token->isGivenKind(T_STATIC)
                && !$tokens[$tokens->getNextMeaningfulToken($index)]->isGivenKind([T_FUNCTION, T_VARIABLE])
            ) {
                continue;
            }

            if ($token->isGivenKind(T_OPEN_TAG)) {
                if ($tokens[$whitespaceTokenIndex]->equals([T_WHITESPACE]) && false === strpos($token->getContent(), "\n")) {
                    $tokens->clearAt($whitespaceTokenIndex);
                }

                continue;
            }

            if ($token->isGivenKind(T_CLASS) && $tokens[$tokens->getNextMeaningfulToken($index)]->equals('(')) {
                continue;
            }

            if ($token->isGivenKind(T_RETURN) && $this->isMultiLineReturn($tokens, $index)) {
                continue;
            }

            if (!$tokens[$whitespaceTokenIndex]->equals([T_WHITESPACE])) {
                $tokens->insertAt($whitespaceTokenIndex, new Token([T_WHITESPACE, ' ']));
            } elseif (' ' !== $tokens[$whitespaceTokenIndex]->getContent()) {
                $tokens[$whitespaceTokenIndex] = new Token([T_WHITESPACE, ' ']);
            }

            if (
                70000 <= \PHP_VERSION_ID
                && $token->isGivenKind(T_YIELD_FROM)
                && 'yield from' !== strtolower($token->getContent())
            ) {
                $tokens[$index] = new Token([T_YIELD_FROM, Preg::replace(
                    '/\s+/',
                    ' ',
                    $token->getContent()
                )]);
            }
        }
    }

    protected function createConfigurationDefinition()
    {
        return new FixerConfigurationResolver([
            (new FixerOptionBuilder('constructs', 'List of constructs which must be followed by a single space.'))
                ->setAllowedTypes(['array'])
                ->setAllowedValues([new AllowedValueSubset(array_keys(self::$tokenMap))])
                ->setDefault(array_keys(self::$tokenMap))
                ->getOption(),
        ]);
    }

    /**
     * @param int $index
     *
     * @return bool
     */
    private function isMultiLineReturn(Tokens $tokens, $index)
    {
        ++$index;
        $tokenFollowingReturn = $tokens[$index];

        if (
            !$tokenFollowingReturn->isGivenKind(T_WHITESPACE)
            || false === strpos($tokenFollowingReturn->getContent(), "\n")
        ) {
            return false;
        }

        $nestedCount = 0;

        for ($indexEnd = \count($tokens) - 1, ++$index; $index < $indexEnd; ++$index) {
            if (false !== strpos($tokens[$index]->getContent(), "\n")) {
                return true;
            }

            if ($tokens[$index]->equals('{')) {
                ++$nestedCount;
            } elseif ($tokens[$index]->equals('}')) {
                --$nestedCount;
            } elseif (0 === $nestedCount && $tokens[$index]->equalsAny([';', [T_CLOSE_TAG]])) {
                break;
            }
        }

        return false;
    }
}
