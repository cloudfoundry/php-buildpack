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

/* /Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Model/table.twig */
class __TwigTemplate_a3ffb3d82a336caaf209b42e2bc4df8c59f0a59480d834c3d02c44999d4a8220 extends \Twig\Template
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
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->enter($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Model/table.twig"));

        // line 16
        $context["annotations"] = $this->getAttribute(($context["DocBlock"] ?? null), "buildTableAnnotations", [0 => ($context["associations"] ?? null), 1 => ($context["associationInfo"] ?? null), 2 => ($context["behaviors"] ?? null), 3 => ($context["entity"] ?? null), 4 => ($context["namespace"] ?? null)], "method");
        // line 17
        echo "<?php
namespace ";
        // line 18
        echo twig_escape_filter($this->env, ($context["namespace"] ?? null), "html", null, true);
        echo "\\Model\\Table;

";
        // line 20
        $context["uses"] = [0 => "use Cake\\ORM\\Query;", 1 => "use Cake\\ORM\\RulesChecker;", 2 => "use Cake\\ORM\\Table;", 3 => "use Cake\\Validation\\Validator;"];
        // line 21
        echo twig_join_filter(($context["uses"] ?? null), "
");
        echo "

";
        // line 23
        echo $this->getAttribute(($context["DocBlock"] ?? null), "classDescription", [0 => ($context["name"] ?? null), 1 => "Model", 2 => ($context["annotations"] ?? null)], "method");
        echo "
class ";
        // line 24
        echo twig_escape_filter($this->env, ($context["name"] ?? null), "html", null, true);
        echo "Table extends Table
{
    /**
     * Initialize method
     *
     * @param array \$config The configuration for the Table.
     * @return void
     */
    public function initialize(array \$config)
    {
        parent::initialize(\$config);

";
        // line 36
        if (($context["table"] ?? null)) {
            // line 37
            echo "        \$this->setTable('";
            echo twig_escape_filter($this->env, ($context["table"] ?? null), "html", null, true);
            echo "');
";
        }
        // line 40
        if (($context["displayField"] ?? null)) {
            // line 41
            echo "        \$this->setDisplayField('";
            echo twig_escape_filter($this->env, ($context["displayField"] ?? null), "html", null, true);
            echo "');
";
        }
        // line 44
        if (($context["primaryKey"] ?? null)) {
            // line 45
            if ((twig_test_iterable(($context["primaryKey"] ?? null)) && (twig_length_filter($this->env, ($context["primaryKey"] ?? null)) > 1))) {
                // line 46
                echo "        \$this->setPrimaryKey([";
                echo $this->getAttribute(($context["Bake"] ?? null), "stringifyList", [0 => ($context["primaryKey"] ?? null), 1 => ["indent" => false]], "method");
                echo "]);";
                // line 47
                echo "
";
            } else {
                // line 49
                echo "        \$this->setPrimaryKey('";
                echo twig_escape_filter($this->env, twig_first($this->env, $this->env->getExtension('Jasny\Twig\ArrayExtension')->asArray(($context["primaryKey"] ?? null))), "html", null, true);
                echo "');";
                // line 50
                echo "
";
            }
        }
        // line 54
        if (($context["behaviors"] ?? null)) {
            // line 55
            echo "
";
        }
        // line 58
        $context['_parent'] = $context;
        $context['_seq'] = twig_ensure_traversable(($context["behaviors"] ?? null));
        foreach ($context['_seq'] as $context["behavior"] => $context["behaviorData"]) {
            // line 59
            echo "        \$this->addBehavior('";
            echo twig_escape_filter($this->env, $context["behavior"], "html", null, true);
            echo "'";
            echo (($context["behaviorData"]) ? (((", [" . $this->getAttribute(($context["Bake"] ?? null), "stringifyList", [0 => $context["behaviorData"], 1 => ["indent" => 3, "quotes" => false]], "method")) . "]")) : (""));
            echo ");
";
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['behavior'], $context['behaviorData'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 62
        if ((($this->getAttribute(($context["associations"] ?? null), "belongsTo", []) || $this->getAttribute(($context["associations"] ?? null), "hasMany", [])) || $this->getAttribute(($context["associations"] ?? null), "belongsToMany", []))) {
            // line 63
            echo "
";
        }
        // line 66
        $context['_parent'] = $context;
        $context['_seq'] = twig_ensure_traversable(($context["associations"] ?? null));
        foreach ($context['_seq'] as $context["type"] => $context["assocs"]) {
            // line 67
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable($context["assocs"]);
            foreach ($context['_seq'] as $context["_key"] => $context["assoc"]) {
                // line 68
                $context["assocData"] = [];
                // line 69
                $context['_parent'] = $context;
                $context['_seq'] = twig_ensure_traversable($context["assoc"]);
                foreach ($context['_seq'] as $context["key"] => $context["val"]) {
                    if ( !($context["key"] === "alias")) {
                        // line 70
                        $context["assocData"] = twig_array_merge(($context["assocData"] ?? null), [$context["key"] => $context["val"]]);
                    }
                }
                $_parent = $context['_parent'];
                unset($context['_seq'], $context['_iterated'], $context['key'], $context['val'], $context['_parent'], $context['loop']);
                $context = array_intersect_key($context, $_parent) + $_parent;
                // line 72
                echo "        \$this->";
                echo twig_escape_filter($this->env, $context["type"], "html", null, true);
                echo "('";
                echo twig_escape_filter($this->env, $this->getAttribute($context["assoc"], "alias", []), "html", null, true);
                echo "', [";
                echo $this->getAttribute(($context["Bake"] ?? null), "stringifyList", [0 => ($context["assocData"] ?? null), 1 => ["indent" => 3]], "method");
                echo "]);";
                // line 73
                echo "
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['_key'], $context['assoc'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['type'], $context['assocs'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 76
        echo "    }";
        // line 77
        echo "
";
        // line 79
        if (($context["validation"] ?? null)) {
            // line 80
            echo "
    /**
     * Default validation rules.
     *
     * @param \\Cake\\Validation\\Validator \$validator Validator instance.
     * @return \\Cake\\Validation\\Validator
     */
    public function validationDefault(Validator \$validator)
    {
";
            // line 89
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable(($context["validation"] ?? null));
            foreach ($context['_seq'] as $context["field"] => $context["rules"]) {
                // line 90
                $context["validationMethods"] = $this->getAttribute(($context["Bake"] ?? null), "getValidationMethods", [0 => $context["field"], 1 => $context["rules"]], "method");
                // line 91
                if (($context["validationMethods"] ?? null)) {
                    // line 92
                    echo "        \$validator
";
                    // line 93
                    $context['_parent'] = $context;
                    $context['_seq'] = twig_ensure_traversable(($context["validationMethods"] ?? null));
                    $context['loop'] = [
                      'parent' => $context['_parent'],
                      'index0' => 0,
                      'index'  => 1,
                      'first'  => true,
                    ];
                    if (is_array($context['_seq']) || (is_object($context['_seq']) && $context['_seq'] instanceof \Countable)) {
                        $length = count($context['_seq']);
                        $context['loop']['revindex0'] = $length - 1;
                        $context['loop']['revindex'] = $length;
                        $context['loop']['length'] = $length;
                        $context['loop']['last'] = 1 === $length;
                    }
                    foreach ($context['_seq'] as $context["_key"] => $context["validationMethod"]) {
                        // line 94
                        if ($this->getAttribute($context["loop"], "last", [])) {
                            // line 95
                            $context["validationMethod"] = ($context["validationMethod"] . ";");
                        }
                        // line 97
                        echo "            ";
                        echo $context["validationMethod"];
                        echo "
";
                        ++$context['loop']['index0'];
                        ++$context['loop']['index'];
                        $context['loop']['first'] = false;
                        if (isset($context['loop']['length'])) {
                            --$context['loop']['revindex0'];
                            --$context['loop']['revindex'];
                            $context['loop']['last'] = 0 === $context['loop']['revindex0'];
                        }
                    }
                    $_parent = $context['_parent'];
                    unset($context['_seq'], $context['_iterated'], $context['_key'], $context['validationMethod'], $context['_parent'], $context['loop']);
                    $context = array_intersect_key($context, $_parent) + $_parent;
                    // line 99
                    echo "
";
                }
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['field'], $context['rules'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
            // line 102
            echo "        return \$validator;
    }
";
        }
        // line 106
        if (($context["rulesChecker"] ?? null)) {
            // line 107
            echo "
    /**
     * Returns a rules checker object that will be used for validating
     * application integrity.
     *
     * @param \\Cake\\ORM\\RulesChecker \$rules The rules object to be modified.
     * @return \\Cake\\ORM\\RulesChecker
     */
    public function buildRules(RulesChecker \$rules)
    {
";
            // line 117
            $context['_parent'] = $context;
            $context['_seq'] = twig_ensure_traversable(($context["rulesChecker"] ?? null));
            foreach ($context['_seq'] as $context["field"] => $context["rule"]) {
                // line 118
                echo "        \$rules->add(\$rules->";
                echo twig_escape_filter($this->env, $this->getAttribute($context["rule"], "name", []), "html", null, true);
                echo "(['";
                echo twig_escape_filter($this->env, $context["field"], "html", null, true);
                echo "']";
                echo ((($this->getAttribute($context["rule"], "extra", [], "any", true, true) && $this->getAttribute($context["rule"], "extra", []))) ? (((", '" . $this->getAttribute($context["rule"], "extra", [])) . "'")) : (""));
                echo "));
";
            }
            $_parent = $context['_parent'];
            unset($context['_seq'], $context['_iterated'], $context['field'], $context['rule'], $context['_parent'], $context['loop']);
            $context = array_intersect_key($context, $_parent) + $_parent;
            // line 120
            echo "
        return \$rules;
    }
";
        }
        // line 125
        if ( !(($context["connection"] ?? null) === "default")) {
            // line 126
            echo "
    /**
     * Returns the database connection name to use by default.
     *
     * @return string
     */
    public static function defaultConnectionName()
    {
        return '";
            // line 134
            echo twig_escape_filter($this->env, ($context["connection"] ?? null), "html", null, true);
            echo "';
    }
";
        }
        // line 137
        echo "}
";
        
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->leave($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof);

    }

    public function getTemplateName()
    {
        return "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Model/table.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  311 => 137,  305 => 134,  295 => 126,  293 => 125,  287 => 120,  274 => 118,  270 => 117,  258 => 107,  256 => 106,  251 => 102,  243 => 99,  226 => 97,  223 => 95,  221 => 94,  204 => 93,  201 => 92,  199 => 91,  197 => 90,  193 => 89,  182 => 80,  180 => 79,  177 => 77,  175 => 76,  164 => 73,  156 => 72,  149 => 70,  144 => 69,  142 => 68,  138 => 67,  134 => 66,  130 => 63,  128 => 62,  117 => 59,  113 => 58,  109 => 55,  107 => 54,  102 => 50,  98 => 49,  94 => 47,  90 => 46,  88 => 45,  86 => 44,  80 => 41,  78 => 40,  72 => 37,  70 => 36,  55 => 24,  51 => 23,  45 => 21,  43 => 20,  38 => 18,  35 => 17,  33 => 16,);
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
{% set annotations = DocBlock.buildTableAnnotations(associations, associationInfo, behaviors, entity, namespace) %}
<?php
namespace {{ namespace }}\\Model\\Table;

{% set uses = ['use Cake\\\\ORM\\\\Query;', 'use Cake\\\\ORM\\\\RulesChecker;', 'use Cake\\\\ORM\\\\Table;', 'use Cake\\\\Validation\\\\Validator;'] %}
{{ uses|join('\\n')|raw }}

{{ DocBlock.classDescription(name, 'Model', annotations)|raw }}
class {{ name }}Table extends Table
{
    /**
     * Initialize method
     *
     * @param array \$config The configuration for the Table.
     * @return void
     */
    public function initialize(array \$config)
    {
        parent::initialize(\$config);

{% if table %}
        \$this->setTable('{{ table }}');
{% endif %}

{%- if displayField %}
        \$this->setDisplayField('{{ displayField }}');
{% endif %}

{%- if primaryKey %}
    {%- if primaryKey is iterable and primaryKey|length > 1 %}
        \$this->setPrimaryKey([{{ Bake.stringifyList(primaryKey, {'indent': false})|raw }}]);
        {{- \"\\n\" }}
    {%- else %}
        \$this->setPrimaryKey('{{ primaryKey|as_array|first }}');
        {{- \"\\n\" }}
    {%- endif %}
{% endif %}

{%- if behaviors %}

{% endif %}

{%- for behavior, behaviorData in behaviors %}
        \$this->addBehavior('{{ behavior }}'{{ (behaviorData ? (\", [\" ~ Bake.stringifyList(behaviorData, {'indent': 3, 'quotes': false})|raw ~ ']') : '')|raw }});
{% endfor %}

{%- if associations.belongsTo or associations.hasMany or associations.belongsToMany %}

{% endif %}

{%- for type, assocs in associations %}
    {%- for assoc in assocs %}
        {%- set assocData = [] %}
        {%- for key, val in assoc if key is not same as('alias') %}
            {%- set assocData = assocData|merge({(key): val}) %}
        {%- endfor %}
        \$this->{{ type }}('{{ assoc.alias }}', [{{ Bake.stringifyList(assocData, {'indent': 3})|raw }}]);
        {{- \"\\n\" }}
    {%- endfor %}
{% endfor %}
    }
{{- \"\\n\" }}

{%- if validation %}

    /**
     * Default validation rules.
     *
     * @param \\Cake\\Validation\\Validator \$validator Validator instance.
     * @return \\Cake\\Validation\\Validator
     */
    public function validationDefault(Validator \$validator)
    {
{% for field, rules in validation %}
{% set validationMethods = Bake.getValidationMethods(field, rules) %}
{% if validationMethods %}
        \$validator
{% for validationMethod in validationMethods %}
{% if loop.last %}
{% set validationMethod = validationMethod ~ ';' %}
{% endif %}
            {{ validationMethod|raw }}
{% endfor %}

{% endif %}
{% endfor %}
        return \$validator;
    }
{% endif %}

{%- if rulesChecker %}

    /**
     * Returns a rules checker object that will be used for validating
     * application integrity.
     *
     * @param \\Cake\\ORM\\RulesChecker \$rules The rules object to be modified.
     * @return \\Cake\\ORM\\RulesChecker
     */
    public function buildRules(RulesChecker \$rules)
    {
{% for field, rule in rulesChecker %}
        \$rules->add(\$rules->{{ rule.name }}(['{{ field }}']{{ (rule.extra is defined and rule.extra ? (\", '#{rule.extra}'\") : '')|raw }}));
{% endfor %}

        return \$rules;
    }
{% endif %}

{%- if connection is not same as('default') %}

    /**
     * Returns the database connection name to use by default.
     *
     * @return string
     */
    public static function defaultConnectionName()
    {
        return '{{ connection }}';
    }
{% endif %}
}
", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Model/table.twig", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Model/table.twig");
    }
}
