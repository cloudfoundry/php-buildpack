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

/* @WebProfiler/Icon/http-client.svg */
class __TwigTemplate_278327201cb3073fb1285de9f8c9e80c7e7fdea5708208f34629a190c27dc7f4 extends Template
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
        $__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e->enter($__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "@WebProfiler/Icon/http-client.svg"));

        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02 = $this->extensions["Symfony\\Bridge\\Twig\\Extension\\ProfilerExtension"];
        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02->enter($__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "@WebProfiler/Icon/http-client.svg"));

        // line 1
        echo "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\"><path fill=\"#AAA\" d=\"M20.4 12c-1 0-1.8.6-2.2 1.4l-2.6-.9c.1-.3.1-.5.1-.8 0-1.2-.6-2.2-1.5-2.9l1.5-2.6c.3.1.6.2 1 .2 1.4 0 2.5-1.1 2.5-2.5s-1.1-2.5-2.5-2.5-2.5 1.1-2.5 2.5c0 .8.4 1.5.9 1.9l-1.5 2.6c-.5-.3-1-.4-1.6-.4-.9 0-1.7.3-2.3.9L7.4 6.6c.3-.4.5-.9.5-1.5 0-1.4-1.1-2.5-2.5-2.5S2.7 3.7 2.7 5.1s1.1 2.5 2.5 2.5c.6 0 1.1-.2 1.5-.5L9 9.4c-.5.6-.8 1.4-.8 2.3 0 .7.2 1.4.6 2l-3.9 3.8c-.4-.3-.9-.5-1.5-.5C2 17 .9 18.1.9 19.5S2.2 22 3.6 22s2.5-1.1 2.5-2.5c0-.5-.2-1-.5-1.5l3.8-3.7c.7.7 1.6 1.1 2.6 1.1h.2l.4 2.4c-1 .3-1.7 1.3-1.7 2.4 0 1.4 1.1 2.5 2.5 2.5s2.5-1.1 2.5-2.5-1.1-2.5-2.5-2.5l-.4-2.5c1-.3 1.9-1 2.3-2l2.6.9v.4c0 1.4 1.1 2.5 2.5 2.5s2.5-1.1 2.5-2.5c.1-1.4-1.1-2.5-2.5-2.5z\"/></svg>
";
        
        $__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e->leave($__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e_prof);

        
        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02->leave($__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02_prof);

    }

    public function getTemplateName()
    {
        return "@WebProfiler/Icon/http-client.svg";
    }

    public function getDebugInfo()
    {
        return array (  43 => 1,);
    }

    public function getSourceContext()
    {
        return new Source("<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\"><path fill=\"#AAA\" d=\"M20.4 12c-1 0-1.8.6-2.2 1.4l-2.6-.9c.1-.3.1-.5.1-.8 0-1.2-.6-2.2-1.5-2.9l1.5-2.6c.3.1.6.2 1 .2 1.4 0 2.5-1.1 2.5-2.5s-1.1-2.5-2.5-2.5-2.5 1.1-2.5 2.5c0 .8.4 1.5.9 1.9l-1.5 2.6c-.5-.3-1-.4-1.6-.4-.9 0-1.7.3-2.3.9L7.4 6.6c.3-.4.5-.9.5-1.5 0-1.4-1.1-2.5-2.5-2.5S2.7 3.7 2.7 5.1s1.1 2.5 2.5 2.5c.6 0 1.1-.2 1.5-.5L9 9.4c-.5.6-.8 1.4-.8 2.3 0 .7.2 1.4.6 2l-3.9 3.8c-.4-.3-.9-.5-1.5-.5C2 17 .9 18.1.9 19.5S2.2 22 3.6 22s2.5-1.1 2.5-2.5c0-.5-.2-1-.5-1.5l3.8-3.7c.7.7 1.6 1.1 2.6 1.1h.2l.4 2.4c-1 .3-1.7 1.3-1.7 2.4 0 1.4 1.1 2.5 2.5 2.5s2.5-1.1 2.5-2.5-1.1-2.5-2.5-2.5l-.4-2.5c1-.3 1.9-1 2.3-2l2.6.9v.4c0 1.4 1.1 2.5 2.5 2.5s2.5-1.1 2.5-2.5c.1-1.4-1.1-2.5-2.5-2.5z\"/></svg>
", "@WebProfiler/Icon/http-client.svg", "/home/ubuntu/workspace/cloudfoundry/php-buildpack/fixtures/symfony_5_local_deps/vendor/symfony/web-profiler-bundle/Resources/views/Icon/http-client.svg");
    }
}
