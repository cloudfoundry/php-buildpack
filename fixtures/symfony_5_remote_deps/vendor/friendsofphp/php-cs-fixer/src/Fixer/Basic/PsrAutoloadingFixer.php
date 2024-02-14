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

namespace PhpCsFixer\Fixer\Basic;

use PhpCsFixer\AbstractFixer;
use PhpCsFixer\Fixer\ConfigurableFixerInterface;
use PhpCsFixer\FixerConfiguration\FixerConfigurationResolver;
use PhpCsFixer\FixerConfiguration\FixerOptionBuilder;
use PhpCsFixer\FixerDefinition\FileSpecificCodeSample;
use PhpCsFixer\FixerDefinition\FixerDefinition;
use PhpCsFixer\Preg;
use PhpCsFixer\StdinFileInfo;
use PhpCsFixer\Tokenizer\Token;
use PhpCsFixer\Tokenizer\Tokens;

/**
 * @author Jordi Boggiano <j.boggiano@seld.be>
 * @author Dariusz Rumiński <dariusz.ruminski@gmail.com>
 * @author Bram Gotink <bram@gotink.me>
 * @author Graham Campbell <graham@alt-three.com>
 * @author Kuba Werłos <werlos@gmail.com>
 */
final class PsrAutoloadingFixer extends AbstractFixer implements ConfigurableFixerInterface
{
    /**
     * {@inheritdoc}
     */
    public function getDefinition()
    {
        return new FixerDefinition(
            'Classes must be in a path that matches their namespace, be at least one namespace deep and the class name should match the file name.',
            [
                new FileSpecificCodeSample(
                    '<?php
namespace PhpCsFixer\FIXER\Basic;
class InvalidName {}
',
                    new \SplFileInfo(__FILE__)
                ),
                new FileSpecificCodeSample(
                    '<?php
namespace PhpCsFixer\FIXER\Basic;
class InvalidName {}
',
                    new \SplFileInfo(__FILE__),
                    ['dir' => './src']
                ),
            ],
            null,
            'This fixer may change your class name, which will break the code that depends on the old name.'
        );
    }

    /**
     * {@inheritdoc}
     */
    public function isCandidate(Tokens $tokens)
    {
        return $tokens->isAnyTokenKindsFound(Token::getClassyTokenKinds());
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
    public function getPriority()
    {
        return -10;
    }

    /**
     * {@inheritdoc}
     */
    public function supports(\SplFileInfo $file)
    {
        if ($file instanceof StdinFileInfo) {
            return false;
        }

        if (
            // ignore file with extension other than php
            ('php' !== $file->getExtension())
            // ignore file with name that cannot be a class name
            || 0 === Preg::match('/^[a-zA-Z_\x7f-\xff][a-zA-Z0-9_\x7f-\xff]*$/', $file->getBasename('.php'))
        ) {
            return false;
        }

        try {
            $tokens = Tokens::fromCode(sprintf('<?php class %s {}', $file->getBasename('.php')));

            if ($tokens[3]->isKeyword() || $tokens[3]->isMagicConstant()) {
                // name can not be a class name - detected by PHP 5.x
                return false;
            }
        } catch (\ParseError $e) {
            // name can not be a class name - detected by PHP 7.x
            return false;
        }

        // ignore stubs/fixtures, since they are typically containing invalid files for various reasons
        return !Preg::match('{[/\\\\](stub|fixture)s?[/\\\\]}i', $file->getRealPath());
    }

    /**
     * {@inheritdoc}
     */
    protected function createConfigurationDefinition()
    {
        return new FixerConfigurationResolver([
            (new FixerOptionBuilder('dir', 'If provided, the directory where the project code is placed.'))
                ->setAllowedTypes(['null', 'string'])
                ->setDefault(null)
                ->getOption(),
        ]);
    }

    /**
     * {@inheritdoc}
     */
    protected function applyFix(\SplFileInfo $file, Tokens $tokens)
    {
        $namespace = null;
        $namespaceStartIndex = null;
        $namespaceEndIndex = null;

        $classyName = null;
        $classyIndex = null;

        foreach ($tokens as $index => $token) {
            if ($token->isGivenKind(T_NAMESPACE)) {
                if (null !== $namespace) {
                    return;
                }

                $namespaceStartIndex = $tokens->getNextMeaningfulToken($index);
                $namespaceEndIndex = $tokens->getNextTokenOfKind($namespaceStartIndex, [';']);

                $namespace = trim($tokens->generatePartialCode($namespaceStartIndex, $namespaceEndIndex - 1));
            } elseif ($token->isClassy()) {
                if ($tokens[$tokens->getPrevMeaningfulToken($index)]->isGivenKind(T_NEW)) {
                    continue;
                }

                if (null !== $classyName) {
                    return;
                }

                $classyIndex = $tokens->getNextMeaningfulToken($index);
                $classyName = $tokens[$classyIndex]->getContent();
            }
        }

        if (null === $classyName) {
            return;
        }

        if (null === $namespace) {
            $expectedClassyName = substr(str_replace('/', '_', $file->getRealPath()), -\strlen($classyName) - 4, -4);
        } else {
            $expectedClassyName = $file->getBasename('.php');
        }

        if ($classyName !== $expectedClassyName) {
            $tokens[$classyIndex] = new Token([T_STRING, $expectedClassyName]);
        }

        if (null === $this->configuration['dir'] || null === $namespace) {
            return;
        }

        if (!is_dir($this->configuration['dir'])) {
            return;
        }

        $configuredDir = realpath($this->configuration['dir']);
        $fileDir = \dirname($file->getRealPath());
        if (\strlen($configuredDir) >= \strlen($fileDir)) {
            return;
        }

        $newNamespace = substr(str_replace('/', '\\', $fileDir), \strlen($configuredDir) + 1);
        $originalNamespace = substr($namespace, -\strlen($newNamespace));

        if ($originalNamespace !== $newNamespace && strtolower($originalNamespace) === strtolower($newNamespace)) {
            $tokens->clearRange($namespaceStartIndex, $namespaceEndIndex);
            $namespace = substr($namespace, 0, -\strlen($newNamespace)).$newNamespace;

            $newNamespace = Tokens::fromCode('<?php namespace '.$namespace.';');
            $newNamespace->clearRange(0, 2);
            $newNamespace->clearEmptyTokens();

            $tokens->insertAt($namespaceStartIndex, $newNamespace);
        }
    }
}
