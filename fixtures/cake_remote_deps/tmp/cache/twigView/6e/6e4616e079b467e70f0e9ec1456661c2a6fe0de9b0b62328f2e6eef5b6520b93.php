<?php

use Twig\Environment;
use Twig\Error\LoaderError;
use Twig\Error\RuntimeError;
use Twig\Markup;
use Twig\Sandbox\SecurityError;
use Twig\Sandbox\SecurityNotAllowedTagError;
use Twig\Sandbox\SecurityNotAllowedFilterError;
use Twig\Sandbox\SecurityNotAllowedFunctionError;
use Twig\Source;
use Twig\Template;

/* /Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/form.twig */
class __TwigTemplate_866271069bf606af3f323f7a819eea22f4908324be789a075b38464c3f51e26b extends \Twig\Template
{
    public function __construct(Environment $env)
    {
        parent::__construct($env);

        $this->parent = false;

        $this->blocks = [
        ];
    }

    protected function doDisplay(array $context, array $blocks = [])
    {
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa = $this->env->getExtension("WyriHaximus\\TwigView\\Lib\\Twig\\Extension\\Profiler");
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->enter($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/form.twig"));

        // line 16
        $context["fields"] = $this->getAttribute(($context["Bake"] ?? null), "filterFields", [0 => ($context["fields"] ?? null), 1 => ($context["schema"] ?? null), 2 => ($context["modelObject"] ?? null)], "method");
        // line 17
        echo "<nav class=\"large-3 medium-4 columns\" id=\"actions-sidebar\">
    <ul class=\"side-nav\">
        <li class=\"heading\"><?= __('Actions') ?></li>
";
        // line 20
        if ((strpos(($context["action"] ?? null), "add") === false)) {
            // line 21
            echo "        <li><?= \$this->Form->postLink(
                __('Delete'),
                ['action' => 'delete', \$";
            // line 23
            echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
            echo "->";
            echo twig_escape_filter($this->env, $this->getAttribute(($context["primaryKey"] ?? null), 0, [], "array"), "html", null, true);
            echo "],
                ['confirm' => __('Are you sure you want to delete # {0}?', \$";
            // line 24
            echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
            echo "->";
            echo twig_escape_filter($this->env, $this->getAttribute(($context["primaryKey"] ?? null), 0, [], "array"), "html", null, true);
            echo ")]
            )
        ?></li>
";
        }
        // line 28
        echo "        <li><?= \$this->Html->link(__('List ";
        echo twig_escape_filter($this->env, ($context["pluralHumanName"] ?? null), "html", null, true);
        echo "'), ['action' => 'index']) ?></li>";
        // line 29
        echo "
";
        // line 30
        $context["done"] = [];
        // line 31
        $context['_parent'] = $context;
        $context['_seq'] = twig_ensure_traversable(($context["associations"] ?? null));
        foreach ($context['_seq'] as $context["type"] => $context["data"]) {
            // line 32
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($context["data"]);
            foreach ($context['_seq'] as $context["alias"] => $context["details"]) {
                // line 33
                if (( !($this->getAttribute($context["details"], "controller", []) === $this->getAttribute(($context["_view"] ?? null), "name", [])) && !twig_in_filter($this->getAttribute($context["details"], "controller", []), ($context["done"] ?? null)))) {
                    // line 34
                    echo "        <li><?= \$this->Html->link(__('List ";
                    echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize(Cake\Utility\Inflector::underscore($context["alias"])), "html", null, true);
                    echo "'), ['controller' => '";
                    echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "controller", []), "html", null, true);
                    echo "', 'action' => 'index']) ?></li>
        <li><?= \$this->Html->link(__('New ";
                    // line 35
                    echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize(Cake\Utility\Inflector::underscore(Cake\Utility\Inflector::singularize($context["alias"]))), "html", null, true);
                    echo "'), ['controller' => '";
                    echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "controller", []), "html", null, true);
                    echo "', 'action' => 'add']) ?></li>";
                    // line 36
                    echo "
";
                    // line 37
                    $context["done"] = twig_array_merge(($context["done"] ?? null), [0 => $this->getAttribute($context["details"], "controller", [])]);
                }
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['alias'], $context['details'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['type'], $context['data'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 41
        echo "    </ul>
</nav>
<div class=\"";
        // line 43
        echo twig_escape_filter($this->env, ($context["pluralVar"] ?? null), "html", null, true);
        echo " form large-9 medium-8 columns content\">
    <?= \$this->Form->create(\$";
        // line 44
        echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
        echo ") ?>
    <fieldset>
        <legend><?= __('";
        // line 46
        echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize(($context["action"] ?? null)), "html", null, true);
        echo " ";
        echo twig_escape_filter($this->env, ($context["singularHumanName"] ?? null), "html", null, true);
        echo "') ?></legend>
        <?php
";
        // line 48
        $context['_parent'] = $context;
        $context['_seq'] = twig_ensure_traversable(($context["fields"] ?? null));
        foreach ($context['_seq'] as $context["_key"] => $context["field"]) {
            if (!twig_in_filter($context["field"], ($context["primaryKey"] ?? null))) {
                // line 49
                if ($this->getAttribute(($context["keyFields"] ?? null), $context["field"], [], "array")) {
                    // line 50
                    $context["fieldData"] = $this->getAttribute(($context["Bake"] ?? null), "columnData", [0 => $context["field"], 1 => ($context["schema"] ?? null)], "method");
                    // line 51
                    if ($this->getAttribute(($context["fieldData"] ?? null), "null", [])) {
                        // line 52
                        echo "            echo \$this->Form->control('";
                        echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                        echo "', ['options' => \$";
                        echo twig_escape_filter($this->env, $this->getAttribute(($context["keyFields"] ?? null), $context["field"], [], "array"), "html", null, true);
                        echo ", 'empty' => true]);";
                        // line 53
                        echo "
";
                    } else {
                        // line 55
                        echo "            echo \$this->Form->control('";
                        echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                        echo "', ['options' => \$";
                        echo twig_escape_filter($this->env, $this->getAttribute(($context["keyFields"] ?? null), $context["field"], [], "array"), "html", null, true);
                        echo "]);";
                        // line 56
                        echo "
";
                    }
                } elseif (!twig_in_filter(                // line 58
$context["field"], [0 => "created", 1 => "modified", 2 => "updated"])) {
                    // line 59
                    $context["fieldData"] = $this->getAttribute(($context["Bake"] ?? null), "columnData", [0 => $context["field"], 1 => ($context["schema"] ?? null)], "method");
                    // line 60
                    if ((twig_in_filter($this->getAttribute(($context["fieldData"] ?? null), "type", []), [0 => "date", 1 => "datetime", 2 => "time"]) && $this->getAttribute(($context["fieldData"] ?? null), "null", []))) {
                        // line 61
                        echo "            echo \$this->Form->control('";
                        echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                        echo "', ['empty' => true]);";
                        // line 62
                        echo "
";
                    } else {
                        // line 64
                        echo "            echo \$this->Form->control('";
                        echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                        echo "');";
                        // line 65
                        echo "
";
                    }
                }
            }
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['_key'], $context['field'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 70
        if ($this->getAttribute(($context["associations"] ?? null), "BelongsToMany", [])) {
            // line 71
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute(($context["associations"] ?? null), "BelongsToMany", []));
            foreach ($context['_seq'] as $context["assocName"] => $context["assocData"]) {
                // line 72
                echo "            echo \$this->Form->control('";
                echo twig_escape_filter($this->env, $this->getAttribute($context["assocData"], "property", []), "html", null, true);
                echo "._ids', ['options' => \$";
                echo twig_escape_filter($this->env, $this->getAttribute($context["assocData"], "variable", []), "html", null, true);
                echo "]);";
                // line 73
                echo "
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['assocName'], $context['assocData'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        // line 76
        echo "        ?>
    </fieldset>
    <?= \$this->Form->button(__('Submit')) ?>
    <?= \$this->Form->end() ?>
</div>
";
        
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->leave($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof);

    }

    public function getTemplateName()
    {
        return "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/form.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  205 => 76,  197 => 73,  191 => 72,  187 => 71,  185 => 70,  175 => 65,  171 => 64,  167 => 62,  163 => 61,  161 => 60,  159 => 59,  157 => 58,  153 => 56,  147 => 55,  143 => 53,  137 => 52,  135 => 51,  133 => 50,  131 => 49,  126 => 48,  119 => 46,  114 => 44,  110 => 43,  106 => 41,  95 => 37,  92 => 36,  87 => 35,  80 => 34,  78 => 33,  74 => 32,  70 => 31,  68 => 30,  65 => 29,  61 => 28,  52 => 24,  46 => 23,  42 => 21,  40 => 20,  35 => 17,  33 => 16,);
    }

    /** @deprecated since 1.27 (to be removed in 2.0). Use getSourceContext() instead */
    public function getSource()
    {
        @trigger_error('The '.__METHOD__.' method is deprecated since version 1.27 and will be removed in 2.0. Use getSourceContext() instead.', E_USER_DEPRECATED);

        return $this->getSourceContext()->getCode();
    }

    public function getSourceContext()
    {
        return new Source("{#
/**
 * CakePHP(tm) : Rapid Development Framework (http://cakephp.org)
 * Copyright (c) Cake Software Foundation, Inc. (http://cakefoundation.org)
 *
 * Licensed under The MIT License
 * For full copyright and license information, please see the LICENSE.txt
 * Redistributions of files must retain the above copyright notice.
 *
 * @copyright     Copyright (c) Cake Software Foundation, Inc. (http://cakefoundation.org)
 * @link          http://cakephp.org CakePHP(tm) Project
 * @since         2.0.0
 * @license       http://www.opensource.org/licenses/mit-license.php MIT License
 */
#}
{% set fields = Bake.filterFields(fields, schema, modelObject) %}
<nav class=\"large-3 medium-4 columns\" id=\"actions-sidebar\">
    <ul class=\"side-nav\">
        <li class=\"heading\"><?= __('Actions') ?></li>
{% if strpos(action, 'add') is same as(false) %}
        <li><?= \$this->Form->postLink(
                __('Delete'),
                ['action' => 'delete', \${{ singularVar }}->{{ primaryKey[0] }}],
                ['confirm' => __('Are you sure you want to delete # {0}?', \${{ singularVar }}->{{ primaryKey[0] }})]
            )
        ?></li>
{% endif %}
        <li><?= \$this->Html->link(__('List {{ pluralHumanName }}'), ['action' => 'index']) ?></li>
        {{- \"\\n\" }}
{%- set done = [] %}
{% for type, data in associations %}
    {%- for alias, details in data %}
        {%- if details.controller is not same as(_view.name) and details.controller not in done %}
        <li><?= \$this->Html->link(__('List {{ alias|underscore|humanize }}'), ['controller' => '{{ details.controller }}', 'action' => 'index']) ?></li>
        <li><?= \$this->Html->link(__('New {{ alias|singularize|underscore|humanize }}'), ['controller' => '{{ details.controller }}', 'action' => 'add']) ?></li>
        {{- \"\\n\" }}
        {%- set done = done|merge([details.controller]) %}
        {%- endif %}
    {%- endfor %}
{% endfor %}
    </ul>
</nav>
<div class=\"{{ pluralVar }} form large-9 medium-8 columns content\">
    <?= \$this->Form->create(\${{ singularVar }}) ?>
    <fieldset>
        <legend><?= __('{{ action|humanize }} {{ singularHumanName }}') ?></legend>
        <?php
{% for field in fields if field not in primaryKey %}
    {%- if keyFields[field] %}
        {%- set fieldData = Bake.columnData(field, schema) %}
        {%- if fieldData.null %}
            echo \$this->Form->control('{{ field }}', ['options' => \${{ keyFields[field] }}, 'empty' => true]);
            {{- \"\\n\" }}
        {%- else %}
            echo \$this->Form->control('{{ field }}', ['options' => \${{ keyFields[field] }}]);
            {{- \"\\n\" }}
        {%- endif %}
    {%- elseif field not in ['created', 'modified', 'updated'] %}
        {%- set fieldData = Bake.columnData(field, schema) %}
        {%- if fieldData.type in ['date', 'datetime', 'time'] and fieldData.null %}
            echo \$this->Form->control('{{ field }}', ['empty' => true]);
            {{- \"\\n\" }}
        {%- else %}
            echo \$this->Form->control('{{ field }}');
    {{- \"\\n\" }}
        {%- endif %}
    {%- endif %}
{%- endfor %}

{%- if associations.BelongsToMany %}
    {%- for assocName, assocData in associations.BelongsToMany %}
            echo \$this->Form->control('{{ assocData.property }}._ids', ['options' => \${{ assocData.variable }}]);
    {{- \"\\n\" }}
    {%- endfor %}
{% endif %}
        ?>
    </fieldset>
    <?= \$this->Form->button(__('Submit')) ?>
    <?= \$this->Form->end() ?>
</div>
", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/form.twig", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/form.twig");
    }
}
