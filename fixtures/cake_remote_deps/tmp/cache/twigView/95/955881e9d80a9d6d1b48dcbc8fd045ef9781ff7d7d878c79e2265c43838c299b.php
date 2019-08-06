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

/* /Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Controller/controller.twig */
class __TwigTemplate_8ab1f92cc6e538e1504ba2f1180eb65fad0b3e3b0d5bdc1e185e1a243178c9c4 extends \Twig\Template
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
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->enter($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Controller/controller.twig"));

        // line 20
        echo "<?php
namespace ";
        // line 21
        echo twig_escape_filter($this->env, ($context["namespace"] ?? null), "html", null, true);
        echo "\\Controller";
        echo twig_escape_filter($this->env, ($context["prefix"] ?? null), "html", null, true);
        echo ";

use ";
        // line 23
        echo twig_escape_filter($this->env, ($context["namespace"] ?? null), "html", null, true);
        echo "\\Controller\\AppController;

/**
 * ";
        // line 26
        echo twig_escape_filter($this->env, ($context["name"] ?? null), "html", null, true);
        echo " Controller
 *
";
        // line 28
        if (($context["defaultModel"] ?? null)) {
            // line 29
            echo " * @property \\";
            echo twig_escape_filter($this->env, ($context["defaultModel"] ?? null), "html", null, true);
            echo " \$";
            echo twig_escape_filter($this->env, ($context["name"] ?? null), "html", null, true);
            echo "
";
        }
        // line 32
        $context['_parent'] = $context;
        $context['_seq'] = twig_ensure_traversable(($context["components"] ?? null));
        foreach ($context['_seq'] as $context["_key"] => $context["component"]) {
            // line 33
            $context["classInfo"] = $this->getAttribute(($context["Bake"] ?? null), "classInfo", [0 => $context["component"], 1 => "Controller/Component", 2 => "Component"], "method");
            // line 34
            echo " * @property ";
            echo twig_escape_filter($this->env, $this->getAttribute(($context["classInfo"] ?? null), "fqn", []), "html", null, true);
            echo " \$";
            echo twig_escape_filter($this->env, $this->getAttribute(($context["classInfo"] ?? null), "name", []), "html", null, true);
            echo "
";
        }
        $_parent = $context['_parent'];
        unset($context['_seq'], $context['_iterated'], $context['_key'], $context['component'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 37
        if (twig_in_filter("index", ($context["actions"] ?? null))) {
            // line 38
            echo " *
 * @method \\";
            // line 39
            echo twig_escape_filter($this->env, ($context["namespace"] ?? null), "html", null, true);
            echo "\\Model\\Entity\\";
            echo twig_escape_filter($this->env, ($context["entityClassName"] ?? null), "html", null, true);
            echo "[]|\\Cake\\Datasource\\ResultSetInterface paginate(\$object = null, array \$settings = [])
";
        }
        // line 41
        echo " */
class ";
        // line 42
        echo twig_escape_filter($this->env, ($context["name"] ?? null), "html", null, true);
        echo "Controller extends AppController
{
";
        // line 44
        $context["helpers"] = $this->getAttribute(($context["Bake"] ?? null), "arrayProperty", [0 => "helpers", 1 => ($context["helpers"] ?? null), 2 => ["indent" => false]], "method");
        // line 45
        if (twig_trim_filter(($context["helpers"] ?? null))) {
            // line 46
            echo ($context["helpers"] ?? null);
            echo "
";
            // line 47
            if (($context["components"] ?? null)) {
                // line 48
                echo "
";
            }
        }
        // line 51
        $context["components"] = $this->getAttribute(($context["Bake"] ?? null), "arrayProperty", [0 => "components", 1 => ($context["components"] ?? null), 2 => ["indent" => false]], "method");
        // line 52
        if (twig_trim_filter(($context["components"] ?? null))) {
            // line 53
            echo ($context["components"] ?? null);
            echo "
";
            // line 54
            if (($context["actions"] ?? null)) {
                // line 55
                echo "
";
            }
        }
        // line 58
        $context['_parent'] = $context;
        $context['_seq'] = twig_ensure_traversable(($context["actions"] ?? null));
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
        foreach ($context['_seq'] as $context["_key"] => $context["action"]) {
            // line 59
            if (($this->getAttribute($context["loop"], "index", []) > 1)) {
                // line 60
                echo "
";
            }
            // line 62
echo $context['_view']->element(("Controller/" . $context["action"]),[],[]);
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
        unset($context['_seq'], $context['_iterated'], $context['_key'], $context['action'], $context['_parent'], $context['loop']);
        $context = array_intersect_key($context, $_parent) + $_parent;
        // line 64
        echo "}
";
        
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->leave($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof);

    }

    public function getTemplateName()
    {
        return "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Controller/controller.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  168 => 64,  154 => 62,  150 => 60,  148 => 59,  131 => 58,  126 => 55,  124 => 54,  120 => 53,  118 => 52,  116 => 51,  111 => 48,  109 => 47,  105 => 46,  103 => 45,  101 => 44,  96 => 42,  93 => 41,  86 => 39,  83 => 38,  81 => 37,  70 => 34,  68 => 33,  64 => 32,  56 => 29,  54 => 28,  49 => 26,  43 => 23,  36 => 21,  33 => 20,);
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
 * Controller bake template file
 *
 * Allows templating of Controllers generated from bake.
 *
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
namespace {{ namespace }}\\Controller{{ prefix }};

use {{ namespace }}\\Controller\\AppController;

/**
 * {{ name }} Controller
 *
{% if defaultModel %}
 * @property \\{{ defaultModel }} \${{ name }}
{% endif %}

{%- for component in components %}
{% set classInfo = Bake.classInfo(component, 'Controller/Component', 'Component') %}
 * @property {{ classInfo.fqn }} \${{ classInfo.name }}
{% endfor %}

{%- if 'index' in actions %}
 *
 * @method \\{{ namespace }}\\Model\\Entity\\{{ entityClassName }}[]|\\Cake\\Datasource\\ResultSetInterface paginate(\$object = null, array \$settings = [])
{% endif %}
 */
class {{ name }}Controller extends AppController
{
{% set helpers = Bake.arrayProperty('helpers', helpers, {'indent': false})|raw %}
{% if helpers|trim %}
    {{- helpers|raw }}
{% if components %}

{% endif %}
{% endif %}
{%- set components = Bake.arrayProperty('components', components, {'indent': false})|raw %}
{% if components|trim %}
    {{- components|raw }}
{% if actions %}

{% endif %}
{% endif %}
{%- for action in actions %}
{% if loop.index > 1 %}

{% endif %}
    {%- element 'Controller/' ~ action %}
{% endfor %}
}
", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Controller/controller.twig", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//Controller/controller.twig");
    }
}
