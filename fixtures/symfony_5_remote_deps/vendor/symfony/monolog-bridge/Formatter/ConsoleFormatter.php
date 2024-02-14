<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Bridge\Monolog\Formatter;

use Monolog\Formatter\FormatterInterface;
use Monolog\Logger;
use Symfony\Component\Console\Formatter\OutputFormatter;
use Symfony\Component\VarDumper\Cloner\Data;
use Symfony\Component\VarDumper\Cloner\Stub;
use Symfony\Component\VarDumper\Cloner\VarCloner;
use Symfony\Component\VarDumper\Dumper\CliDumper;

/**
 * Formats incoming records for console output by coloring them depending on log level.
 *
 * @author Tobias Schultze <http://tobion.de>
 * @author Grégoire Pineau <lyrixx@lyrixx.info>
 */
class ConsoleFormatter implements FormatterInterface
{
    public const SIMPLE_FORMAT = "%datetime% %start_tag%%level_name%%end_tag% <comment>[%channel%]</> %message%%context%%extra%\n";
    public const SIMPLE_DATE = 'H:i:s';

    private const LEVEL_COLOR_MAP = [
        Logger::DEBUG => 'fg=white',
        Logger::INFO => 'fg=green',
        Logger::NOTICE => 'fg=blue',
        Logger::WARNING => 'fg=cyan',
        Logger::ERROR => 'fg=yellow',
        Logger::CRITICAL => 'fg=red',
        Logger::ALERT => 'fg=red',
        Logger::EMERGENCY => 'fg=white;bg=red',
    ];

    private $options;
    private $cloner;
    private $outputBuffer;
    private $dumper;

    /**
     * Available options:
     *   * format: The format of the outputted log string. The following placeholders are supported: %datetime%, %start_tag%, %level_name%, %end_tag%, %channel%, %message%, %context%, %extra%;
     *   * date_format: The format of the outputted date string;
     *   * colors: If true, the log string contains ANSI code to add color;
     *   * multiline: If false, "context" and "extra" are dumped on one line.
     */
    public function __construct(array $options = [])
    {
        $this->options = array_replace([
            'format' => self::SIMPLE_FORMAT,
            'date_format' => self::SIMPLE_DATE,
            'colors' => true,
            'multiline' => false,
            'level_name_format' => '%-9s',
            'ignore_empty_context_and_extra' => true,
        ], $options);

        if (class_exists(VarCloner::class)) {
            $this->cloner = new VarCloner();
            $this->cloner->addCasters([
                '*' => [$this, 'castObject'],
            ]);

            $this->outputBuffer = fopen('php://memory', 'r+');
            if ($this->options['multiline']) {
                $output = $this->outputBuffer;
            } else {
                $output = [$this, 'echoLine'];
            }

            $this->dumper = new CliDumper($output, null, CliDumper::DUMP_LIGHT_ARRAY | CliDumper::DUMP_COMMA_SEPARATOR);
        }
    }

    /**
     * {@inheritdoc}
     *
     * @return mixed
     */
    public function formatBatch(array $records)
    {
        foreach ($records as $key => $record) {
            $records[$key] = $this->format($record);
        }

        return $records;
    }

    /**
     * {@inheritdoc}
     *
     * @return mixed
     */
    public function format(array $record)
    {
        $record = $this->replacePlaceHolder($record);

        if (!$this->options['ignore_empty_context_and_extra'] || !empty($record['context'])) {
            $context = ($this->options['multiline'] ? "\n" : ' ').$this->dumpData($record['context']);
        } else {
            $context = '';
        }

        if (!$this->options['ignore_empty_context_and_extra'] || !empty($record['extra'])) {
            $extra = ($this->options['multiline'] ? "\n" : ' ').$this->dumpData($record['extra']);
        } else {
            $extra = '';
        }

        $formatted = strtr($this->options['format'], [
            '%datetime%' => $record['datetime'] instanceof \DateTimeInterface
                ? $record['datetime']->format($this->options['date_format'])
                : $record['datetime'],
            '%start_tag%' => sprintf('<%s>', self::LEVEL_COLOR_MAP[$record['level']]),
            '%level_name%' => sprintf($this->options['level_name_format'], $record['level_name']),
            '%end_tag%' => '</>',
            '%channel%' => $record['channel'],
            '%message%' => $this->replacePlaceHolder($record)['message'],
            '%context%' => $context,
            '%extra%' => $extra,
        ]);

        return $formatted;
    }

    /**
     * @internal
     */
    public function echoLine(string $line, int $depth, string $indentPad)
    {
        if (-1 !== $depth) {
            fwrite($this->outputBuffer, $line);
        }
    }

    /**
     * @internal
     */
    public function castObject($v, array $a, Stub $s, bool $isNested): array
    {
        if ($this->options['multiline']) {
            return $a;
        }

        if ($isNested && !$v instanceof \DateTimeInterface) {
            $s->cut = -1;
            $a = [];
        }

        return $a;
    }

    private function replacePlaceHolder(array $record): array
    {
        $message = $record['message'];

        if (false === strpos($message, '{')) {
            return $record;
        }

        $context = $record['context'];

        $replacements = [];
        foreach ($context as $k => $v) {
            // Remove quotes added by the dumper around string.
            $v = trim($this->dumpData($v, false), '"');
            $v = OutputFormatter::escape($v);
            $replacements['{'.$k.'}'] = sprintf('<comment>%s</>', $v);
        }

        $record['message'] = strtr($message, $replacements);

        return $record;
    }

    private function dumpData($data, bool $colors = null): string
    {
        if (null === $this->dumper) {
            return '';
        }

        if (null === $colors) {
            $this->dumper->setColors($this->options['colors']);
        } else {
            $this->dumper->setColors($colors);
        }

        if (!$data instanceof Data) {
            $data = $this->cloner->cloneVar($data);
        }
        $data = $data->withRefHandles(false);
        $this->dumper->dump($data);

        $dump = stream_get_contents($this->outputBuffer, -1, 0);
        rewind($this->outputBuffer);
        ftruncate($this->outputBuffer, 0);

        return rtrim($dump);
    }
}
