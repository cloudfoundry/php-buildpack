<?php

use Twig\Environment;
use Twig\Error\LoaderError;
use Twig\Error\RuntimeError;
use Twig\Extension\SandboxExtension;
use Twig\Markup;
use Twig\Sandbox\SecurityError;
use Twig\Sandbox\SecurityNotAllowedTagError;
use Twig\Sandbox\SecurityNotAllowedFilterError;
use Twig\Sandbox\SecurityNotAllowedFunctionError;
use Twig\Source;
use Twig\Template;

/* debug/source_code.html.twig */
class __TwigTemplate_9353d74410869e594ed28b36827ad9b4664b2daca7ca9353e8f47d72f07829c6 extends Template
{
    private $source;
    private $macros = [];

    public function __construct(Environment $env)
    {
        parent::__construct($env);

        $this->source = $this->getSourceContext();

        $this->parent = false;

        $this->blocks = [
        ];
    }

    protected function doDisplay(array $context, array $blocks = [])
    {
        $macros = $this->macros;
        $__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e = $this->extensions["Symfony\\Bundle\\WebProfilerBundle\\Twig\\WebProfilerExtension"];
        $__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e->enter($__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "debug/source_code.html.twig"));

        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02 = $this->extensions["Symfony\\Bridge\\Twig\\Extension\\ProfilerExtension"];
        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02->enter($__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "debug/source_code.html.twig"));

        // line 1
        echo "<div class=\"section source-code\">
    <p>
        ";
        // line 3
        echo $this->extensions['Symfony\Bridge\Twig\Extension\TranslationExtension']->trans("help.show_code");
        echo "
    </p>

    <button type=\"button\" class=\"btn btn-default btn-lg btn-block\" data-toggle=\"modal\" data-target=\"#sourceCodeModal\">
      <i class=\"fa fa-cogs\" aria-hidden=\"true\"></i> ";
        // line 7
        echo twig_escape_filter($this->env, $this->extensions['Symfony\Bridge\Twig\Extension\TranslationExtension']->trans("action.show_code"), "html", null, true);
        echo "
    </button>

    <div class=\"modal fade\" id=\"sourceCodeModal\" tabindex=\"-1\">
        <div class=\"modal-dialog modal-lg\">
            <div class=\"modal-content\">
                <div class=\"modal-header\">
                    <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"";
        // line 14
        echo twig_escape_filter($this->env, $this->extensions['Symfony\Bridge\Twig\Extension\TranslationExtension']->trans("action.close"), "html", null, true);
        echo "\">
                        <span aria-hidden=\"true\">&times;</span>
                    </button>
                    <h4 class=\"modal-title\"><i class=\"fa fa-code\" aria-hidden=\"true\"></i> ";
        // line 17
        echo twig_escape_filter($this->env, $this->extensions['Symfony\Bridge\Twig\Extension\TranslationExtension']->trans("title.source_code"), "html", null, true);
        echo "</h4>
                </div>

                <div class=\"modal-body\">
                    ";
        // line 21
        if ((isset($context["controller"]) || array_key_exists("controller", $context) ? $context["controller"] : (function () { throw new RuntimeError('Variable "controller" does not exist.', 21, $this->source); })())) {
            // line 22
            echo "                        <h3><a href=\"https://symfony.com/doc/current/controller.html\" target=\"_blank\">";
            echo twig_escape_filter($this->env, $this->extensions['Symfony\Bridge\Twig\Extension\TranslationExtension']->trans("title.controller_code"), "html", null, true);
            echo "</a><small class=\"pull-right\">";
            echo $this->extensions['Symfony\Bridge\Twig\Extension\CodeExtension']->formatFile(twig_get_attribute($this->env, $this->source, (isset($context["controller"]) || array_key_exists("controller", $context) ? $context["controller"] : (function () { throw new RuntimeError('Variable "controller" does not exist.', 22, $this->source); })()), "file_path", [], "any", false, false, false, 22), twig_get_attribute($this->env, $this->source, (isset($context["controller"]) || array_key_exists("controller", $context) ? $context["controller"] : (function () { throw new RuntimeError('Variable "controller" does not exist.', 22, $this->source); })()), "starting_line", [], "any", false, false, false, 22));
            echo "</small></h3>
                        <pre><code class=\"php\">";
            // line 23
            echo twig_escape_filter($this->env, twig_get_attribute($this->env, $this->source, (isset($context["controller"]) || array_key_exists("controller", $context) ? $context["controller"] : (function () { throw new RuntimeError('Variable "controller" does not exist.', 23, $this->source); })()), "source_code", [], "any", false, false, false, 23), "html", null, true);
            echo "</code></pre>
                    ";
        } else {
            // line 25
            echo "                        <h3><a href=\"https://symfony.com/doc/current/controller.html\">";
            echo twig_escape_filter($this->env, $this->extensions['Symfony\Bridge\Twig\Extension\TranslationExtension']->trans("title.controller_code"), "html", null, true);
            echo "</a></h3>
                        <pre><code>";
            // line 26
            echo twig_escape_filter($this->env, $this->extensions['Symfony\Bridge\Twig\Extension\TranslationExtension']->trans("not_available"), "html", null, true);
            echo "</code></pre>
                    ";
        }
        // line 28
        echo "
                    <h3><a href=\"https://symfony.com/doc/current/templates.html\" target=\"_blank\">";
        // line 29
        echo twig_escape_filter($this->env, $this->extensions['Symfony\Bridge\Twig\Extension\TranslationExtension']->trans("title.twig_template_code"), "html", null, true);
        echo "</a><small class=\"pull-right\">";
        echo $this->extensions['Symfony\Bridge\Twig\Extension\CodeExtension']->formatFile(twig_get_attribute($this->env, $this->source, (isset($context["template"]) || array_key_exists("template", $context) ? $context["template"] : (function () { throw new RuntimeError('Variable "template" does not exist.', 29, $this->source); })()), "file_path", [], "any", false, false, false, 29), twig_get_attribute($this->env, $this->source, (isset($context["template"]) || array_key_exists("template", $context) ? $context["template"] : (function () { throw new RuntimeError('Variable "template" does not exist.', 29, $this->source); })()), "starting_line", [], "any", false, false, false, 29));
        echo "</small></h3>
                    <pre><code class=\"twig\">";
        // line 30
        echo twig_escape_filter($this->env, twig_get_attribute($this->env, $this->source, (isset($context["template"]) || array_key_exists("template", $context) ? $context["template"] : (function () { throw new RuntimeError('Variable "template" does not exist.', 30, $this->source); })()), "source_code", [], "any", false, false, false, 30), "html", null, true);
        echo "</code></pre>
                </div>
            </div>
        </div>
    </div>
</div>
";
        
        $__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e->leave($__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e_prof);

        
        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02->leave($__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02_prof);

    }

    public function getTemplateName()
    {
        return "debug/source_code.html.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  110 => 30,  104 => 29,  101 => 28,  96 => 26,  91 => 25,  86 => 23,  79 => 22,  77 => 21,  70 => 17,  64 => 14,  54 => 7,  47 => 3,  43 => 1,);
    }

    public function getSourceContext()
    {
        return new Source("<div class=\"section source-code\">
    <p>
        {{ 'help.show_code'|trans|raw }}
    </p>

    <button type=\"button\" class=\"btn btn-default btn-lg btn-block\" data-toggle=\"modal\" data-target=\"#sourceCodeModal\">
      <i class=\"fa fa-cogs\" aria-hidden=\"true\"></i> {{ 'action.show_code'|trans }}
    </button>

    <div class=\"modal fade\" id=\"sourceCodeModal\" tabindex=\"-1\">
        <div class=\"modal-dialog modal-lg\">
            <div class=\"modal-content\">
                <div class=\"modal-header\">
                    <button type=\"button\" class=\"close\" data-dismiss=\"modal\" aria-label=\"{{ 'action.close'|trans }}\">
                        <span aria-hidden=\"true\">&times;</span>
                    </button>
                    <h4 class=\"modal-title\"><i class=\"fa fa-code\" aria-hidden=\"true\"></i> {{ 'title.source_code'|trans }}</h4>
                </div>

                <div class=\"modal-body\">
                    {% if controller %}
                        <h3><a href=\"https://symfony.com/doc/current/controller.html\" target=\"_blank\">{{ 'title.controller_code'|trans }}</a><small class=\"pull-right\">{{ controller.file_path|format_file(controller.starting_line) }}</small></h3>
                        <pre><code class=\"php\">{{ controller.source_code }}</code></pre>
                    {% else %}
                        <h3><a href=\"https://symfony.com/doc/current/controller.html\">{{ 'title.controller_code'|trans }}</a></h3>
                        <pre><code>{{ 'not_available'|trans }}</code></pre>
                    {% endif %}

                    <h3><a href=\"https://symfony.com/doc/current/templates.html\" target=\"_blank\">{{ 'title.twig_template_code'|trans }}</a><small class=\"pull-right\">{{ template.file_path|format_file(template.starting_line) }}</small></h3>
                    <pre><code class=\"twig\">{{ template.source_code }}</code></pre>
                </div>
            </div>
        </div>
    </div>
</div>
", "debug/source_code.html.twig", "/home/ubuntu/workspace/cloudfoundry/php-buildpack/fixtures/symfony_5_local_deps/templates/debug/source_code.html.twig");
    }
}
