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

/* @WebProfiler/Icon/request.svg */
class __TwigTemplate_c497a7134894cc8fd69d96f816f57a61 extends Template
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
        $__internal_5a27a8ba21ca79b61932376b2fa922d2->enter($__internal_5a27a8ba21ca79b61932376b2fa922d2_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "@WebProfiler/Icon/request.svg"));

        $__internal_6f47bbe9983af81f1e7450e9a3e3768f = $this->extensions["Symfony\\Bridge\\Twig\\Extension\\ProfilerExtension"];
        $__internal_6f47bbe9983af81f1e7450e9a3e3768f->enter($__internal_6f47bbe9983af81f1e7450e9a3e3768f_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "@WebProfiler/Icon/request.svg"));

        // line 1
        echo "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\"><path fill=\"#AAA\" d=\"M15.8 6.4h-1.1s-.1.1-.1 0l.8-.7c.5-.5.5-1.3 0-1.9L14 2.4c-.5-.5-1.4-.5-1.9 0l-.6.8c-.1 0 0 0 0-.1v-1c0-.8-1-1.4-1.8-1.4h-2c-.8 0-1.9.6-1.9 1.4v1.1l.1.1-.8-.8c-.5-.5-1.3-.5-1.9 0L1.8 3.9c-.5.5-.5 1.4 0 1.9l.8.6c0 .1 0 0-.1 0H1.4C.7 6.4 0 7.5 0 8.2v2C0 11 .7 12 1.4 12h1.2l.1-.1-.8.7c-.5.5-.5 1.3 0 1.9L3.3 16c.5.5 1.4.5 1.9 0l.6-.8-.1.1v1.2c0 .8 1.1 1.4 1.9 1.4h2c.8 0 1.8-.6 1.8-1.4v-1.2s-.1-.1 0-.1l.7.8c.5.5 1.3.5 1.9 0l1.4-1.4c.5-.5.5-1.4 0-1.9l-.8-.7.1.1h1.1c.8 0 1.3-1.1 1.3-1.8v-2c0-.8-.6-1.9-1.3-1.9zM8.6 13a3.8 3.8 0 1 1 3.8-3.8A4 4 0 0 1 8.6 13zm13.7 2.6l-.6.2s0 .1 0 0l.3-.5c.2-.4 0-.8-.4-1l-1-.4c-.4-.2-.8 0-1 .4l-.1.5-.2-.6c-.2-.4-.8-.5-1.2-.3l-1.1.4c-.4.2-.8.7-.7 1.1l.2.6h.1l-.5-.3c-.4-.2-.8 0-1 .4l-.4 1c-.2.4 0 .8.4 1l.5.1-.6.2c-.4.2-.5.8-.4 1.2l.4 1.1c.2.4.7.8 1.1.7l.6-.2s0-.1 0 0l-.3.5c-.2.4 0 .8.4 1l1 .4c.4.2.8 0 1-.4l.1-.5.2.6c.2.4.9.5 1.2.3l1.1-.4c.4-.2.8-.7.6-1.1l-.2-.6s-.1 0 0 0l.5.3c.4.2.8 0 1-.4l.4-1c.2-.4 0-.8-.4-1l-.5-.1.6-.2c.4-.2.5-.8.3-1.2l-.4-1.1c-.1-.4-.6-.8-1-.7zm-2.4 4.9a2 2 0 0 1-2.7-1.2 2 2 0 0 1 1.2-2.7 2 2 0 0 1 2.7 1.2 2 2 0 0 1-1.2 2.7z\"/></svg>
";
        
        $__internal_5a27a8ba21ca79b61932376b2fa922d2->leave($__internal_5a27a8ba21ca79b61932376b2fa922d2_prof);

        
        $__internal_6f47bbe9983af81f1e7450e9a3e3768f->leave($__internal_6f47bbe9983af81f1e7450e9a3e3768f_prof);

    }

    /**
     * @codeCoverageIgnore
     */
    public function getTemplateName()
    {
        return "@WebProfiler/Icon/request.svg";
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
        return new Source("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\"><path fill=\"#AAA\" d=\"M15.8 6.4h-1.1s-.1.1-.1 0l.8-.7c.5-.5.5-1.3 0-1.9L14 2.4c-.5-.5-1.4-.5-1.9 0l-.6.8c-.1 0 0 0 0-.1v-1c0-.8-1-1.4-1.8-1.4h-2c-.8 0-1.9.6-1.9 1.4v1.1l.1.1-.8-.8c-.5-.5-1.3-.5-1.9 0L1.8 3.9c-.5.5-.5 1.4 0 1.9l.8.6c0 .1 0 0-.1 0H1.4C.7 6.4 0 7.5 0 8.2v2C0 11 .7 12 1.4 12h1.2l.1-.1-.8.7c-.5.5-.5 1.3 0 1.9L3.3 16c.5.5 1.4.5 1.9 0l.6-.8-.1.1v1.2c0 .8 1.1 1.4 1.9 1.4h2c.8 0 1.8-.6 1.8-1.4v-1.2s-.1-.1 0-.1l.7.8c.5.5 1.3.5 1.9 0l1.4-1.4c.5-.5.5-1.4 0-1.9l-.8-.7.1.1h1.1c.8 0 1.3-1.1 1.3-1.8v-2c0-.8-.6-1.9-1.3-1.9zM8.6 13a3.8 3.8 0 1 1 3.8-3.8A4 4 0 0 1 8.6 13zm13.7 2.6l-.6.2s0 .1 0 0l.3-.5c.2-.4 0-.8-.4-1l-1-.4c-.4-.2-.8 0-1 .4l-.1.5-.2-.6c-.2-.4-.8-.5-1.2-.3l-1.1.4c-.4.2-.8.7-.7 1.1l.2.6h.1l-.5-.3c-.4-.2-.8 0-1 .4l-.4 1c-.2.4 0 .8.4 1l.5.1-.6.2c-.4.2-.5.8-.4 1.2l.4 1.1c.2.4.7.8 1.1.7l.6-.2s0-.1 0 0l-.3.5c-.2.4 0 .8.4 1l1 .4c.4.2.8 0 1-.4l.1-.5.2.6c.2.4.9.5 1.2.3l1.1-.4c.4-.2.8-.7.6-1.1l-.2-.6s-.1 0 0 0l.5.3c.4.2.8 0 1-.4l.4-1c.2-.4 0-.8-.4-1l-.5-.1.6-.2c.4-.2.5-.8.3-1.2l-.4-1.1c-.1-.4-.6-.8-1-.7zm-2.4 4.9a2 2 0 0 1-2.7-1.2 2 2 0 0 1 1.2-2.7 2 2 0 0 1 2.7 1.2 2 2 0 0 1-1.2 2.7z\"/></svg>
", "@WebProfiler/Icon/request.svg", "/php-buildpack/fixtures/symfony_5_remote_deps/vendor/symfony/web-profiler-bundle/Resources/views/Icon/request.svg");
    }
}
