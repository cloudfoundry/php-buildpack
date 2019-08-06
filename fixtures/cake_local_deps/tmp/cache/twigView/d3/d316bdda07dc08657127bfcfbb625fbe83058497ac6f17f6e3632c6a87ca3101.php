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

/* /Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/view.twig */
class __TwigTemplate_98746630eba67ef3c5bfe7d93b5d04e1ead1efc8ef6c330b5e22388ceefe47ad extends \Twig\Template
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
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->enter($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/view.twig"));

        // line 16
        $context["allAssociations"] = $this->getAttribute(($context["Bake"] ?? null), "aliasExtractor", [0 => ($context["modelObj"] ?? null), 1 => "BelongsTo"], "method");
        // line 17
        $context["allAssociations"] = twig_array_merge(($context["allAssociations"] ?? null), $this->getAttribute(($context["Bake"] ?? null), "aliasExtractor", [0 => ($context["modelObj"] ?? null), 1 => "BelongsToMany"], "method"));
        // line 18
        $context["allAssociations"] = twig_array_merge(($context["allAssociations"] ?? null), $this->getAttribute(($context["Bake"] ?? null), "aliasExtractor", [0 => ($context["modelObj"] ?? null), 1 => "HasOne"], "method"));
        // line 19
        $context["allAssociations"] = twig_array_merge(($context["allAssociations"] ?? null), $this->getAttribute(($context["Bake"] ?? null), "aliasExtractor", [0 => ($context["modelObj"] ?? null), 1 => "HasMany"], "method"));
        // line 20
        echo "    /**
     * View method
     *
     * @param string|null \$id ";
        // line 23
        echo twig_escape_filter($this->env, ($context["singularHumanName"] ?? null), "html", null, true);
        echo " id.
     * @return \\Cake\\Http\\Response|null
     * @throws \\Cake\\Datasource\\Exception\\RecordNotFoundException When record not found.
     */
    public function view(\$id = null)
    {
        \$";
        // line 29
        echo twig_escape_filter($this->env, ($context["singularName"] ?? null), "html", null, true);
        echo " = \$this->";
        echo twig_escape_filter($this->env, ($context["currentModelName"] ?? null), "html", null, true);
        echo "->get(\$id, [
            'contain' => [";
        // line 30
        echo $this->getAttribute(($context["Bake"] ?? null), "stringifyList", [0 => ($context["allAssociations"] ?? null), 1 => ["indent" => false]], "method");
        echo "]
        ]);

        \$this->set('";
        // line 33
        echo twig_escape_filter($this->env, ($context["singularName"] ?? null), "html", null, true);
        echo "', \$";
        echo twig_escape_filter($this->env, ($context["singularName"] ?? null), "html", null, true);
        echo ");
    }
";
        
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->leave($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof);

    }

    public function getTemplateName()
    {
        return "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/view.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  67 => 33,  61 => 30,  55 => 29,  46 => 23,  41 => 20,  39 => 19,  37 => 18,  35 => 17,  33 => 16,);
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
{% set allAssociations = Bake.aliasExtractor(modelObj, 'BelongsTo') %}
{% set allAssociations = allAssociations|merge(Bake.aliasExtractor(modelObj, 'BelongsToMany')) %}
{% set allAssociations = allAssociations|merge(Bake.aliasExtractor(modelObj, 'HasOne')) %}
{% set allAssociations = allAssociations|merge(Bake.aliasExtractor(modelObj, 'HasMany')) %}
    /**
     * View method
     *
     * @param string|null \$id {{ singularHumanName }} id.
     * @return \\Cake\\Http\\Response|null
     * @throws \\Cake\\Datasource\\Exception\\RecordNotFoundException When record not found.
     */
    public function view(\$id = null)
    {
        \${{ singularName }} = \$this->{{ currentModelName }}->get(\$id, [
            'contain' => [{{ Bake.stringifyList(allAssociations, {'indent': false})|raw }}]
        ]);

        \$this->set('{{ singularName }}', \${{ singularName }});
    }
", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/view.twig", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/view.twig");
    }
}
