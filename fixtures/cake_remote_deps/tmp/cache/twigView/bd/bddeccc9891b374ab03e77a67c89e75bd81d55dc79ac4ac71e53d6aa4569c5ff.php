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

/* /Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Template/view.twig */
class __TwigTemplate_ba139a6d8cb14ca92b35df2da32328e60992a8f61a689676d87f47c02599f52a extends \Twig\Template
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
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->enter($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Template/view.twig"));

        // line 16
        echo "<?php
/**
 * @var \\";
        // line 18
        echo twig_escape_filter($this->env, ($context["namespace"] ?? null), "html", null, true);
        echo "\\View\\AppView \$this
 * @var \\";
        // line 19
        echo twig_escape_filter($this->env, ($context["entityClass"] ?? null), "html", null, true);
        echo " \$";
        echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
        echo "
 */
?>
";
        // line 22
        $context["associations"] = twig_array_merge(["BelongsTo" => [], "HasOne" => [], "HasMany" => [], "BelongsToMany" => []], ($context["associations"] ?? null));
        // line 23
        $context["fieldsData"] = $this->getAttribute(($context["Bake"] ?? null), "getViewFieldsData", [0 => ($context["fields"] ?? null), 1 => ($context["schema"] ?? null), 2 => ($context["associations"] ?? null)], "method");
        // line 24
        $context["associationFields"] = $this->getAttribute(($context["fieldsData"] ?? null), "associationFields", []);
        // line 25
        $context["groupedFields"] = $this->getAttribute(($context["fieldsData"] ?? null), "groupedFields", []);
        // line 26
        $context["pK"] = ((("\$" . ($context["singularVar"] ?? null)) . "->") . $this->getAttribute(($context["primaryKey"] ?? null), 0, [], "array"));
        // line 27
        echo "<nav class=\"large-3 medium-4 columns\" id=\"actions-sidebar\">
    <ul class=\"side-nav\">
        <li class=\"heading\"><?= __('Actions') ?></li>
        <li><?= \$this->Html->link(__('Edit ";
        // line 30
        echo twig_escape_filter($this->env, ($context["singularHumanName"] ?? null), "html", null, true);
        echo "'), ['action' => 'edit', ";
        echo ($context["pK"] ?? null);
        echo "]) ?> </li>
        <li><?= \$this->Form->postLink(__('Delete ";
        // line 31
        echo twig_escape_filter($this->env, ($context["singularHumanName"] ?? null), "html", null, true);
        echo "'), ['action' => 'delete', ";
        echo ($context["pK"] ?? null);
        echo "], ['confirm' => __('Are you sure you want to delete # {0}?', ";
        echo ($context["pK"] ?? null);
        echo ")]) ?> </li>
        <li><?= \$this->Html->link(__('List ";
        // line 32
        echo twig_escape_filter($this->env, ($context["pluralHumanName"] ?? null), "html", null, true);
        echo "'), ['action' => 'index']) ?> </li>
        <li><?= \$this->Html->link(__('New ";
        // line 33
        echo twig_escape_filter($this->env, ($context["singularHumanName"] ?? null), "html", null, true);
        echo "'), ['action' => 'add']) ?> </li>
";
        // line 34
        $context["done"] = [];
        // line 35
        $context['_parent'] = $context;
        $context['_seq'] = twig_ensure_traversable(($context["associations"] ?? null));
        foreach ($context['_seq'] as $context["type"] => $context["data"]) {
            // line 36
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($context["data"]);
            foreach ($context['_seq'] as $context["alias"] => $context["details"]) {
                // line 37
                if (( !($this->getAttribute($context["details"], "controller", []) === $this->getAttribute(($context["_view"] ?? null), "name", [])) && !twig_in_filter($this->getAttribute($context["details"], "controller", []), ($context["done"] ?? null)))) {
                    // line 38
                    echo "        <li><?= \$this->Html->link(__('List ";
                    echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize(Cake\Utility\Inflector::underscore($context["alias"])), "html", null, true);
                    echo "'), ['controller' => '";
                    echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "controller", []), "html", null, true);
                    echo "', 'action' => 'index']) ?> </li>
        <li><?= \$this->Html->link(__('New ";
                    // line 39
                    echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize(Cake\Utility\Inflector::singularize(Cake\Utility\Inflector::underscore($context["alias"]))), "html", null, true);
                    echo "'), ['controller' => '";
                    echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "controller", []), "html", null, true);
                    echo "', 'action' => 'add']) ?> </li>
";
                    // line 40
                    $context["done"] = twig_array_merge(($context["done"] ?? null), [0 => "controller"]);
                }
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['alias'], $context['details'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['type'], $context['data'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 44
        echo "    </ul>
</nav>
<div class=\"";
        // line 46
        echo twig_escape_filter($this->env, ($context["pluralVar"] ?? null), "html", null, true);
        echo " view large-9 medium-8 columns content\">
    <h3><?= h(\$";
        // line 47
        echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
        echo "->";
        echo twig_escape_filter($this->env, ($context["displayField"] ?? null), "html", null, true);
        echo ") ?></h3>
    <table class=\"vertical-table\">
";
        // line 49
        if ($this->getAttribute(($context["groupedFields"] ?? null), "string", [], "array")) {
            // line 50
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute(($context["groupedFields"] ?? null), "string", [], "array"));
            foreach ($context['_seq'] as $context["_key"] => $context["field"]) {
                // line 51
                if ($this->getAttribute(($context["associationFields"] ?? null), $context["field"], [], "array")) {
                    // line 52
                    $context["details"] = $this->getAttribute(($context["associationFields"] ?? null), $context["field"], [], "array");
                    // line 53
                    echo "        <tr>
            <th scope=\"row\"><?= __('";
                    // line 54
                    echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize($this->getAttribute(($context["details"] ?? null), "property", [])), "html", null, true);
                    echo "') ?></th>
            <td><?= \$";
                    // line 55
                    echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                    echo "->has('";
                    echo twig_escape_filter($this->env, $this->getAttribute(($context["details"] ?? null), "property", []), "html", null, true);
                    echo "') ? \$this->Html->link(\$";
                    echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                    echo "->";
                    echo twig_escape_filter($this->env, $this->getAttribute(($context["details"] ?? null), "property", []), "html", null, true);
                    echo "->";
                    echo twig_escape_filter($this->env, $this->getAttribute(($context["details"] ?? null), "displayField", []), "html", null, true);
                    echo ", ['controller' => '";
                    echo twig_escape_filter($this->env, $this->getAttribute(($context["details"] ?? null), "controller", []), "html", null, true);
                    echo "', 'action' => 'view', \$";
                    echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                    echo "->";
                    echo twig_escape_filter($this->env, $this->getAttribute(($context["details"] ?? null), "property", []), "html", null, true);
                    echo "->";
                    echo twig_escape_filter($this->env, $this->getAttribute($this->getAttribute(($context["details"] ?? null), "primaryKey", []), 0, [], "array"), "html", null, true);
                    echo "]) : '' ?></td>
        </tr>
";
                } else {
                    // line 58
                    echo "        <tr>
            <th scope=\"row\"><?= __('";
                    // line 59
                    echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize($context["field"]), "html", null, true);
                    echo "') ?></th>
            <td><?= h(\$";
                    // line 60
                    echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                    echo "->";
                    echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                    echo ") ?></td>
        </tr>
";
                }
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['_key'], $context['field'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        // line 65
        if ($this->getAttribute(($context["associations"] ?? null), "HasOne", [])) {
            // line 66
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute(($context["associations"] ?? null), "HasOne", []));
            foreach ($context['_seq'] as $context["alias"] => $context["details"]) {
                // line 67
                echo "        <tr>
            <th scope=\"row\"><?= __('";
                // line 68
                echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize(Cake\Utility\Inflector::singularize(Cake\Utility\Inflector::underscore($context["alias"]))), "html", null, true);
                echo "') ?></th>
            <td><?= \$";
                // line 69
                echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                echo "->has('";
                echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "property", []), "html", null, true);
                echo "') ? \$this->Html->link(\$";
                echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "property", []), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "displayField", []), "html", null, true);
                echo ", ['controller' => '";
                echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "controller", []), "html", null, true);
                echo "', 'action' => 'view', \$";
                echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "property", []), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $this->getAttribute($this->getAttribute($context["details"], "primaryKey", []), 0, [], "array"), "html", null, true);
                echo "]) : '' ?></td>
        </tr>
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['alias'], $context['details'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        // line 73
        if ($this->getAttribute(($context["groupedFields"] ?? null), "number", [])) {
            // line 74
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute(($context["groupedFields"] ?? null), "number", []));
            foreach ($context['_seq'] as $context["_key"] => $context["field"]) {
                // line 75
                echo "        <tr>
            <th scope=\"row\"><?= __('";
                // line 76
                echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize($context["field"]), "html", null, true);
                echo "') ?></th>
            <td><?= \$this->Number->format(\$";
                // line 77
                echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                echo ") ?></td>
        </tr>
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['_key'], $context['field'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        // line 81
        if ($this->getAttribute(($context["groupedFields"] ?? null), "date", [])) {
            // line 82
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute(($context["groupedFields"] ?? null), "date", []));
            foreach ($context['_seq'] as $context["_key"] => $context["field"]) {
                // line 83
                echo "        <tr>
            <th scope=\"row\"><?= __('";
                // line 84
                echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize($context["field"]), "html", null, true);
                echo "') ?></th>
            <td><?= h(\$";
                // line 85
                echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                echo ") ?></td>
        </tr>
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['_key'], $context['field'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        // line 89
        if ($this->getAttribute(($context["groupedFields"] ?? null), "boolean", [])) {
            // line 90
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute(($context["groupedFields"] ?? null), "boolean", []));
            foreach ($context['_seq'] as $context["_key"] => $context["field"]) {
                // line 91
                echo "        <tr>
            <th scope=\"row\"><?= __('";
                // line 92
                echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize($context["field"]), "html", null, true);
                echo "') ?></th>
            <td><?= \$";
                // line 93
                echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                echo " ? __('Yes') : __('No'); ?></td>
        </tr>
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['_key'], $context['field'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        // line 97
        echo "    </table>
";
        // line 98
        if ($this->getAttribute(($context["groupedFields"] ?? null), "text", [])) {
            // line 99
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute(($context["groupedFields"] ?? null), "text", []));
            foreach ($context['_seq'] as $context["_key"] => $context["field"]) {
                // line 100
                echo "    <div class=\"row\">
        <h4><?= __('";
                // line 101
                echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize($context["field"]), "html", null, true);
                echo "') ?></h4>
        <?= \$this->Text->autoParagraph(h(\$";
                // line 102
                echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                echo ")); ?>
    </div>
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['_key'], $context['field'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        // line 106
        $context["relations"] = twig_array_merge($this->getAttribute(($context["associations"] ?? null), "BelongsToMany", []), $this->getAttribute(($context["associations"] ?? null), "HasMany", []));
        // line 107
        $context['_parent'] = $context;
        $context['_seq'] = twig_ensure_traversable(($context["relations"] ?? null));
        foreach ($context['_seq'] as $context["alias"] => $context["details"]) {
            // line 108
            $context["otherSingularVar"] = Cake\Utility\Inflector::variable($context["alias"]);
            // line 109
            $context["otherPluralHumanName"] = Cake\Utility\Inflector::humanize(Cake\Utility\Inflector::underscore($this->getAttribute($context["details"], "controller", [])));
            // line 110
            echo "    <div class=\"related\">
        <h4><?= __('Related ";
            // line 111
            echo twig_escape_filter($this->env, ($context["otherPluralHumanName"] ?? null), "html", null, true);
            echo "') ?></h4>
        <?php if (!empty(\$";
            // line 112
            echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
            echo "->";
            echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "property", []), "html", null, true);
            echo ")): ?>
        <table cellpadding=\"0\" cellspacing=\"0\">
            <tr>
";
            // line 115
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute($context["details"], "fields", []));
            foreach ($context['_seq'] as $context["_key"] => $context["field"]) {
                // line 116
                echo "                <th scope=\"col\"><?= __('";
                echo twig_escape_filter($this->env, Cake\Utility\Inflector::humanize($context["field"]), "html", null, true);
                echo "') ?></th>
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['_key'], $context['field'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
            // line 118
            echo "                <th scope=\"col\" class=\"actions\"><?= __('Actions') ?></th>
            </tr>
            <?php foreach (\$";
            // line 120
            echo twig_escape_filter($this->env, ($context["singularVar"] ?? null), "html", null, true);
            echo "->";
            echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "property", []), "html", null, true);
            echo " as \$";
            echo twig_escape_filter($this->env, ($context["otherSingularVar"] ?? null), "html", null, true);
            echo "): ?>
            <tr>
";
            // line 122
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($this->getAttribute($context["details"], "fields", []));
            foreach ($context['_seq'] as $context["_key"] => $context["field"]) {
                // line 123
                echo "                <td><?= h(\$";
                echo twig_escape_filter($this->env, ($context["otherSingularVar"] ?? null), "html", null, true);
                echo "->";
                echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                echo ") ?></td>
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['_key'], $context['field'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
            // line 125
            $context["otherPk"] = ((("\$" . ($context["otherSingularVar"] ?? null)) . "->") . $this->getAttribute($this->getAttribute($context["details"], "primaryKey", []), 0, [], "array"));
            // line 126
            echo "                <td class=\"actions\">
                    <?= \$this->Html->link(__('View'), ['controller' => '";
            // line 127
            echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "controller", []), "html", null, true);
            echo "', 'action' => 'view', ";
            echo ($context["otherPk"] ?? null);
            echo "]) ?>
                    <?= \$this->Html->link(__('Edit'), ['controller' => '";
            // line 128
            echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "controller", []), "html", null, true);
            echo "', 'action' => 'edit', ";
            echo ($context["otherPk"] ?? null);
            echo "]) ?>
                    <?= \$this->Form->postLink(__('Delete'), ['controller' => '";
            // line 129
            echo twig_escape_filter($this->env, $this->getAttribute($context["details"], "controller", []), "html", null, true);
            echo "', 'action' => 'delete', ";
            echo ($context["otherPk"] ?? null);
            echo "], ['confirm' => __('Are you sure you want to delete # {0}?', ";
            echo ($context["otherPk"] ?? null);
            echo ")]) ?>
                </td>
            </tr>
            <?php endforeach; ?>
        </table>
        <?php endif; ?>
    </div>
";
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['alias'], $context['details'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 137
        echo "</div>
";
        
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->leave($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof);

    }

    public function getTemplateName()
    {
        return "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Template/view.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  439 => 137,  421 => 129,  415 => 128,  409 => 127,  406 => 126,  404 => 125,  393 => 123,  389 => 122,  380 => 120,  376 => 118,  367 => 116,  363 => 115,  355 => 112,  351 => 111,  348 => 110,  346 => 109,  344 => 108,  340 => 107,  338 => 106,  326 => 102,  322 => 101,  319 => 100,  315 => 99,  313 => 98,  310 => 97,  298 => 93,  294 => 92,  291 => 91,  287 => 90,  285 => 89,  273 => 85,  269 => 84,  266 => 83,  262 => 82,  260 => 81,  248 => 77,  244 => 76,  241 => 75,  237 => 74,  235 => 73,  209 => 69,  205 => 68,  202 => 67,  198 => 66,  196 => 65,  183 => 60,  179 => 59,  176 => 58,  154 => 55,  150 => 54,  147 => 53,  145 => 52,  143 => 51,  139 => 50,  137 => 49,  130 => 47,  126 => 46,  122 => 44,  111 => 40,  105 => 39,  98 => 38,  96 => 37,  92 => 36,  88 => 35,  86 => 34,  82 => 33,  78 => 32,  70 => 31,  64 => 30,  59 => 27,  57 => 26,  55 => 25,  53 => 24,  51 => 23,  49 => 22,  41 => 19,  37 => 18,  33 => 16,);
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
<?php
/**
 * @var \\{{ namespace }}\\View\\AppView \$this
 * @var \\{{ entityClass }} \${{ singularVar }}
 */
?>
{% set associations = {'BelongsTo': [], 'HasOne': [], 'HasMany': [], 'BelongsToMany': []}|merge(associations) %}
{% set fieldsData = Bake.getViewFieldsData(fields, schema, associations) %}
{% set associationFields = fieldsData.associationFields %}
{% set groupedFields = fieldsData.groupedFields %}
{% set pK = '\$' ~ singularVar ~ '->' ~ primaryKey[0] %}
<nav class=\"large-3 medium-4 columns\" id=\"actions-sidebar\">
    <ul class=\"side-nav\">
        <li class=\"heading\"><?= __('Actions') ?></li>
        <li><?= \$this->Html->link(__('Edit {{ singularHumanName }}'), ['action' => 'edit', {{ pK|raw }}]) ?> </li>
        <li><?= \$this->Form->postLink(__('Delete {{ singularHumanName }}'), ['action' => 'delete', {{ pK|raw }}], ['confirm' => __('Are you sure you want to delete # {0}?', {{ pK|raw }})]) ?> </li>
        <li><?= \$this->Html->link(__('List {{ pluralHumanName }}'), ['action' => 'index']) ?> </li>
        <li><?= \$this->Html->link(__('New {{ singularHumanName }}'), ['action' => 'add']) ?> </li>
{% set done = [] %}
{% for type, data in associations %}
{% for alias, details in data %}
{% if details.controller is not same as(_view.name) and details.controller not in done %}
        <li><?= \$this->Html->link(__('List {{ alias|underscore|humanize }}'), ['controller' => '{{ details.controller }}', 'action' => 'index']) ?> </li>
        <li><?= \$this->Html->link(__('New {{ alias|underscore|singularize|humanize }}'), ['controller' => '{{ details.controller }}', 'action' => 'add']) ?> </li>
{% set done = done|merge(['controller']) %}
{% endif %}
{% endfor %}
{% endfor %}
    </ul>
</nav>
<div class=\"{{ pluralVar }} view large-9 medium-8 columns content\">
    <h3><?= h(\${{ singularVar }}->{{ displayField }}) ?></h3>
    <table class=\"vertical-table\">
{% if groupedFields['string'] %}
{% for field in groupedFields['string'] %}
{% if associationFields[field] %}
{% set details = associationFields[field] %}
        <tr>
            <th scope=\"row\"><?= __('{{ details.property|humanize }}') ?></th>
            <td><?= \${{ singularVar }}->has('{{ details.property }}') ? \$this->Html->link(\${{ singularVar }}->{{ details.property }}->{{ details.displayField }}, ['controller' => '{{ details.controller }}', 'action' => 'view', \${{ singularVar }}->{{ details.property }}->{{ details.primaryKey[0] }}]) : '' ?></td>
        </tr>
{% else %}
        <tr>
            <th scope=\"row\"><?= __('{{ field|humanize }}') ?></th>
            <td><?= h(\${{ singularVar }}->{{ field }}) ?></td>
        </tr>
{% endif %}
{% endfor %}
{% endif %}
{% if associations.HasOne %}
{% for alias, details in associations.HasOne %}
        <tr>
            <th scope=\"row\"><?= __('{{ alias|underscore|singularize|humanize }}') ?></th>
            <td><?= \${{ singularVar }}->has('{{ details.property }}') ? \$this->Html->link(\${{ singularVar }}->{{ details.property }}->{{ details.displayField }}, ['controller' => '{{ details.controller }}', 'action' => 'view', \${{ singularVar }}->{{ details.property }}->{{ details.primaryKey[0] }}]) : '' ?></td>
        </tr>
{% endfor %}
{% endif %}
{% if groupedFields.number %}
{% for field in groupedFields.number %}
        <tr>
            <th scope=\"row\"><?= __('{{ field|humanize }}') ?></th>
            <td><?= \$this->Number->format(\${{ singularVar }}->{{ field }}) ?></td>
        </tr>
{% endfor %}
{% endif %}
{% if groupedFields.date %}
{% for field in groupedFields.date %}
        <tr>
            <th scope=\"row\"><?= __('{{ field|humanize }}') ?></th>
            <td><?= h(\${{ singularVar }}->{{ field }}) ?></td>
        </tr>
{% endfor %}
{% endif %}
{% if groupedFields.boolean %}
{% for field in groupedFields.boolean %}
        <tr>
            <th scope=\"row\"><?= __('{{ field|humanize }}') ?></th>
            <td><?= \${{ singularVar }}->{{ field }} ? __('Yes') : __('No'); ?></td>
        </tr>
{% endfor %}
{% endif %}
    </table>
{% if groupedFields.text %}
{% for field in groupedFields.text %}
    <div class=\"row\">
        <h4><?= __('{{ field|humanize }}') ?></h4>
        <?= \$this->Text->autoParagraph(h(\${{ singularVar }}->{{ field }})); ?>
    </div>
{% endfor %}
{% endif %}
{% set relations = associations.BelongsToMany|merge(associations.HasMany) %}
{% for alias, details in relations %}
{% set otherSingularVar = alias|variable %}
{% set otherPluralHumanName = details.controller|underscore|humanize %}
    <div class=\"related\">
        <h4><?= __('Related {{ otherPluralHumanName }}') ?></h4>
        <?php if (!empty(\${{ singularVar }}->{{ details.property }})): ?>
        <table cellpadding=\"0\" cellspacing=\"0\">
            <tr>
{% for field in details.fields %}
                <th scope=\"col\"><?= __('{{ field|humanize }}') ?></th>
{% endfor %}
                <th scope=\"col\" class=\"actions\"><?= __('Actions') ?></th>
            </tr>
            <?php foreach (\${{ singularVar }}->{{ details.property }} as \${{ otherSingularVar }}): ?>
            <tr>
{% for field in details.fields %}
                <td><?= h(\${{ otherSingularVar }}->{{ field }}) ?></td>
{% endfor %}
{% set otherPk = '\$' ~ otherSingularVar ~ '->' ~ details.primaryKey[0] %}
                <td class=\"actions\">
                    <?= \$this->Html->link(__('View'), ['controller' => '{{ details.controller }}', 'action' => 'view', {{ otherPk|raw }}]) ?>
                    <?= \$this->Html->link(__('Edit'), ['controller' => '{{ details.controller }}', 'action' => 'edit', {{ otherPk|raw }}]) ?>
                    <?= \$this->Form->postLink(__('Delete'), ['controller' => '{{ details.controller }}', 'action' => 'delete', {{ otherPk|raw }}], ['confirm' => __('Are you sure you want to delete # {0}?', {{ otherPk|raw }})]) ?>
                </td>
            </tr>
            <?php endforeach; ?>
        </table>
        <?php endif; ?>
    </div>
{% endfor %}
</div>
", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Template/view.twig", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Template/view.twig");
    }
}
