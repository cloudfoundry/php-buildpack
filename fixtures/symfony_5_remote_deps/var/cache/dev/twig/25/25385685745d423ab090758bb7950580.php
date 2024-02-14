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

/* @WebProfiler/Icon/redirect.svg */
class __TwigTemplate_1c71fa92bc65024358e89d238ad61536 extends Template
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
        $__internal_5a27a8ba21ca79b61932376b2fa922d2 = $this->extensions["Symfony\\Bundle\\WebProfilerBundle\\Twig\\WebProfilerExtension"];
        $__internal_5a27a8ba21ca79b61932376b2fa922d2->enter($__internal_5a27a8ba21ca79b61932376b2fa922d2_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "@WebProfiler/Icon/redirect.svg"));

        $__internal_6f47bbe9983af81f1e7450e9a3e3768f = $this->extensions["Symfony\\Bridge\\Twig\\Extension\\ProfilerExtension"];
        $__internal_6f47bbe9983af81f1e7450e9a3e3768f->enter($__internal_6f47bbe9983af81f1e7450e9a3e3768f_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "@WebProfiler/Icon/redirect.svg"));

        // line 1
        echo "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\"><path fill=\"#aaa\" d=\"M23 7.8L14 .4a1.3 1.3 0 0 0-2 .9V4a13.6 13.6 0 0 1-2.2.6l-1.3.5c-.5.1-1 .4-1.4.6l-.7.4-.7.4a10.6 10.6 0 0 0-1.4 1A13.2 13.2 0 0 0 3 8.8a15.3 15.3 0 0 0-1.1 1.5 17.6 17.6 0 0 0-.9 1.6l-.5 1.7c-.2.5 0 1.2 0 1.7a10.2 10.2 0 0 0 0 1.5A5.7 5.7 0 0 0 1 18l.4 1.2 1 2 1 1.4 1 1c.2.2.4.1.3-.2l-.3-1.2-.3-1.6-.1-1.9v-1a3.4 3.4 0 0 1 .2-1 6.4 6.4 0 0 1 .3-.8l.4-.8.6-.6.6-.6.7-.4a7.5 7.5 0 0 1 .8-.2 4.5 4.5 0 0 1 .8-.2h2.5a3.8 3.8 0 0 1 1.2.3v3.1a1.3 1.3 0 0 0 2 1l9-7.5a1.5 1.5 0 0 0 0-2.3z\"/></svg>
";
        
        $__internal_5a27a8ba21ca79b61932376b2fa922d2->leave($__internal_5a27a8ba21ca79b61932376b2fa922d2_prof);

        
        $__internal_6f47bbe9983af81f1e7450e9a3e3768f->leave($__internal_6f47bbe9983af81f1e7450e9a3e3768f_prof);

    }

    /**
     * @codeCoverageIgnore
     */
    public function getTemplateName()
    {
        return "@WebProfiler/Icon/redirect.svg";
    }

    /**
     * @codeCoverageIgnore
     */
    public function getDebugInfo()
    {
        return array (  43 => 1,);
    }

    public function getSourceContext()
    {
        return new Source("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\"><path fill=\"#aaa\" d=\"M23 7.8L14 .4a1.3 1.3 0 0 0-2 .9V4a13.6 13.6 0 0 1-2.2.6l-1.3.5c-.5.1-1 .4-1.4.6l-.7.4-.7.4a10.6 10.6 0 0 0-1.4 1A13.2 13.2 0 0 0 3 8.8a15.3 15.3 0 0 0-1.1 1.5 17.6 17.6 0 0 0-.9 1.6l-.5 1.7c-.2.5 0 1.2 0 1.7a10.2 10.2 0 0 0 0 1.5A5.7 5.7 0 0 0 1 18l.4 1.2 1 2 1 1.4 1 1c.2.2.4.1.3-.2l-.3-1.2-.3-1.6-.1-1.9v-1a3.4 3.4 0 0 1 .2-1 6.4 6.4 0 0 1 .3-.8l.4-.8.6-.6.6-.6.7-.4a7.5 7.5 0 0 1 .8-.2 4.5 4.5 0 0 1 .8-.2h2.5a3.8 3.8 0 0 1 1.2.3v3.1a1.3 1.3 0 0 0 2 1l9-7.5a1.5 1.5 0 0 0 0-2.3z\"/></svg>
", "@WebProfiler/Icon/redirect.svg", "/php-buildpack/fixtures/symfony_5_remote_deps/vendor/symfony/web-profiler-bundle/Resources/views/Icon/redirect.svg");
    }
}
