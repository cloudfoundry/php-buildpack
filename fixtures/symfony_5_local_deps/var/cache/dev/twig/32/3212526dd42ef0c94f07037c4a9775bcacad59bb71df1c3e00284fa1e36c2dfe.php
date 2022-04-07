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

/* @DoctrineMigrations/Collector/icon.svg */
class __TwigTemplate_5f205d16862b92fab31a6fb733323247bbbe629f1fba6fe4662dbf3813e17e0f extends Template
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
        $__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e->enter($__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "@DoctrineMigrations/Collector/icon.svg"));

        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02 = $this->extensions["Symfony\\Bridge\\Twig\\Extension\\ProfilerExtension"];
        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02->enter($__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "@DoctrineMigrations/Collector/icon.svg"));

        // line 1
        echo "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\" width=\"24\" height=\"24\">
    <polygon fill=\"#AAA\" points=\"0 0 24 0 24 7 17.5 7 16.5 3 15.5 7 11 7 12 3 3 3 4 7 0 7\" />
    <polygon fill=\"#AAA\" points=\"0 8.5 4.5 8.5 6 15.5 0 15.5\" />
    <polygon fill=\"#AAA\" points=\"10.5 8.5 15 8.5 13.5 15.5 9 15.5\" />
    <polygon fill=\"#AAA\" points=\"18 8.5 24 8.5 24 15.5 19.5 15.5\" />
    <polygon fill=\"#AAA\" points=\"0 17 6.5 17 7.5 21 8.5 17 13 17 12 21 21 21 20 17 24 17 24 24 0 24\" />
</svg>
";
        
        $__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e->leave($__internal_085b0142806202599c7fe3b329164a92397d8978207a37e79d70b8c52599e33e_prof);

        
        $__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02->leave($__internal_319393461309892924ff6e74d6d6e64287df64b63545b994e100d4ab223aed02_prof);

    }

    public function getTemplateName()
    {
        return "@DoctrineMigrations/Collector/icon.svg";
    }

    public function getDebugInfo()
    {
        return array (  43 => 1,);
    }

    public function getSourceContext()
    {
        return new Source("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 24 24\" width=\"24\" height=\"24\">
    <polygon fill=\"#AAA\" points=\"0 0 24 0 24 7 17.5 7 16.5 3 15.5 7 11 7 12 3 3 3 4 7 0 7\" />
    <polygon fill=\"#AAA\" points=\"0 8.5 4.5 8.5 6 15.5 0 15.5\" />
    <polygon fill=\"#AAA\" points=\"10.5 8.5 15 8.5 13.5 15.5 9 15.5\" />
    <polygon fill=\"#AAA\" points=\"18 8.5 24 8.5 24 15.5 19.5 15.5\" />
    <polygon fill=\"#AAA\" points=\"0 17 6.5 17 7.5 21 8.5 17 13 17 12 21 21 21 20 17 24 17 24 24 0 24\" />
</svg>
", "@DoctrineMigrations/Collector/icon.svg", "/test/fixtures/symfony_5_local_deps/vendor/doctrine/doctrine-migrations-bundle/Resources/views/Collector/icon.svg");
    }
}
