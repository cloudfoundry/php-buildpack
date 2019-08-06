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

/* /Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/delete.twig */
class __TwigTemplate_66cf76be29629e070b9eb473670f2b596de249505a4de0dd9a31ec90ad34ed7e extends \Twig\Template
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
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->enter($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof = new \Twig\Profiler\Profile($this->getTemplateName(), "template", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/delete.twig"));

        // line 16
        echo "    /**
     * Delete method
     *
     * @param string|null \$id ";
        // line 19
        echo twig_escape_filter($this->env, ($context["singularHumanName"] ?? null), "html", null, true);
        echo " id.
     * @return \\Cake\\Http\\Response|null Redirects to index.
     * @throws \\Cake\\Datasource\\Exception\\RecordNotFoundException When record not found.
     */
    public function delete(\$id = null)
    {
        \$this->request->allowMethod(['post', 'delete']);
        \$";
        // line 26
        echo twig_escape_filter($this->env, ($context["singularName"] ?? null), "html", null, true);
        echo " = \$this->";
        echo twig_escape_filter($this->env, ($context["currentModelName"] ?? null), "html", null, true);
        echo "->get(\$id);
        if (\$this->";
        // line 27
        echo twig_escape_filter($this->env, ($context["currentModelName"] ?? null), "html", null, true);
        echo "->delete(\$";
        echo twig_escape_filter($this->env, ($context["singularName"] ?? null), "html", null, true);
        echo ")) {
            \$this->Flash->success(__('The ";
        // line 28
        echo twig_escape_filter($this->env, twig_lower_filter($this->env, ($context["singularHumanName"] ?? null)), "html", null, true);
        echo " has been deleted.'));
        } else {
            \$this->Flash->error(__('The ";
        // line 30
        echo twig_escape_filter($this->env, twig_lower_filter($this->env, ($context["singularHumanName"] ?? null)), "html", null, true);
        echo " could not be deleted. Please, try again.'));
        }

        return \$this->redirect(['action' => 'index']);
    }
";
        
        $__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa->leave($__internal_770edd655cdeb606afc443e4edb1f19b4248a91788cb82e88bf8b9495a7c5cfa_prof);

    }

    public function getTemplateName()
    {
        return "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/delete.twig";
    }

    public function isTraitable()
    {
        return false;
    }

    public function getDebugInfo()
    {
        return array (  65 => 30,  60 => 28,  54 => 27,  48 => 26,  38 => 19,  33 => 16,);
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
    /**
     * Delete method
     *
     * @param string|null \$id {{ singularHumanName }} id.
     * @return \\Cake\\Http\\Response|null Redirects to index.
     * @throws \\Cake\\Datasource\\Exception\\RecordNotFoundException When record not found.
     */
    public function delete(\$id = null)
    {
        \$this->request->allowMethod(['post', 'delete']);
        \${{ singularName }} = \$this->{{ currentModelName }}->get(\$id);
        if (\$this->{{ currentModelName }}->delete(\${{ singularName }})) {
            \$this->Flash->success(__('The {{ singularHumanName|lower }} has been deleted.'));
        } else {
            \$this->Flash->error(__('The {{ singularHumanName|lower }} could not be deleted. Please, try again.'));
        }

        return \$this->redirect(['action' => 'index']);
    }
", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/delete.twig", "/Users/pivotal/workspace/php-buildpack/fixtures/new-cake-test/vendor/cakephp/bake/src/Template/Bake/Element/Controller/delete.twig");
    }
}
