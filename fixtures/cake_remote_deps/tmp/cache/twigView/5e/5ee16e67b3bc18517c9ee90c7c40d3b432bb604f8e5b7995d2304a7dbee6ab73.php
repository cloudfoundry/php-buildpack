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

/* /Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//tests/fixture.twig */
class __TwigTemplate_31d640f9fa288959cb27b9fc846a87ccae9113ae9c36136a9bace3f51d01d6e5 extends \Twig\Template
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
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->enter($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//tests/fixture.twig"));

        // line 20
        echo "<?php
namespace ";
        // line 21
        echo twig_escape_filter($this->env, ($context["namespace"] ?? null), "html", null, true);
        echo "\\Test\\Fixture;

use Cake\\TestSuite\\Fixture\\TestFixture;

/**
 * ";
        // line 26
        echo twig_escape_filter($this->env, ($context["name"] ?? null), "html", null, true);
        echo "Fixture
 */
class ";
        // line 28
        echo twig_escape_filter($this->env, ($context["name"] ?? null), "html", null, true);
        echo "Fixture extends TestFixture
{
";
        // line 30
        if (($context["table"] ?? null)) {
            // line 31
            echo "    /**
     * Table name
     *
     * @var string
     */
    public \$table = '";
            // line 36
            echo ($context["table"] ?? null);
            echo "';
";
        }
        // line 39
        if (($context["import"] ?? null)) {
            // line 40
            echo "    /**
     * Import
     *
     * @var array
     */
    public \$import = ";
            // line 45
            echo ($context["import"] ?? null);
            echo ";

";
        }
        // line 49
        if (($context["schema"] ?? null)) {
            // line 50
            echo "    /**
     * Fields
     *
     * @var array
     */
    // @codingStandardsIgnoreStart
    public \$fields = ";
            // line 56
            echo ($context["schema"] ?? null);
            echo ";
    // @codingStandardsIgnoreEnd
";
        }
        // line 60
        if (($context["records"] ?? null)) {
            // line 61
            echo "    /**
     * Init method
     *
     * @return void
     */
    public function init()
    {
        \$this->records = ";
            // line 68
            echo ($context["records"] ?? null);
            echo ";
        parent::init();
    }
";
        }
        // line 72
        echo "}
";
        
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->leave($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof);

    }

    public function getTemplateName()
    {
        return "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//tests/fixture.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  117 => 72,  110 => 68,  101 => 61,  99 => 60,  93 => 56,  85 => 50,  83 => 49,  77 => 45,  70 => 40,  68 => 39,  63 => 36,  56 => 31,  54 => 30,  49 => 28,  44 => 26,  36 => 21,  33 => 20,);
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
 * Fixture Template file
 *
 * Fixture Template used when baking fixtures with bake
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
namespace {{ namespace }}\\Test\\Fixture;

use Cake\\TestSuite\\Fixture\\TestFixture;

/**
 * {{ name }}Fixture
 */
class {{ name }}Fixture extends TestFixture
{
{% if table %}
    /**
     * Table name
     *
     * @var string
     */
    public \$table = '{{ table|raw }}';
{% endif %}

{%- if import %}
    /**
     * Import
     *
     * @var array
     */
    public \$import = {{ import|raw }};

{% endif %}

{%- if schema %}
    /**
     * Fields
     *
     * @var array
     */
    // @codingStandardsIgnoreStart
    public \$fields = {{ schema|raw }};
    // @codingStandardsIgnoreEnd
{% endif %}

{%- if records %}
    /**
     * Init method
     *
     * @return void
     */
    public function init()
    {
        \$this->records = {{ records|raw }};
        parent::init();
    }
{% endif %}
}
", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//tests/fixture.twig", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake//tests/fixture.twig");
    }
}
