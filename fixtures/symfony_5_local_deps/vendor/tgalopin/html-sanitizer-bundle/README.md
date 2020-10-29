# html-sanitizer-bundle

[![Build Status](https://travis-ci.org/tgalopin/html-sanitizer-bundle.svg?branch=master)](https://travis-ci.org/tgalopin/html-sanitizer-bundle)

[![SymfonyInsight](https://insight.symfony.com/projects/760ca691-4f3a-4cd6-9b3e-bf131ffc07c7/big.svg)](https://insight.symfony.com/projects/760ca691-4f3a-4cd6-9b3e-bf131ffc07c7)

[html-sanitizer](https://github.com/tgalopin/html-sanitizer)
is a library aiming at handling, cleaning and sanitizing HTML sent by external users
(who you cannot trust), allowing you to store it and display it safely. It has sensible defaults
to provide a great developer experience while still being entierely configurable.

This repository is a Symfony bundle integrating the [html-sanitizer](https://github.com/tgalopin/html-sanitizer)
library into Symfony applications. It provides helpful tools on top of the sanitizer to easily use it in Symfony.

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage in services](#usage-in-services)
- [Usage in forms](#usage-in-forms)
- [Usage in Twig](#usage-in-twig)
- [Registering an extension](#registering-an-extension)
- [Security issues](#security-issues)
- [Backward Compatibility promise](#backward-compatibility-promise)

## Installation

html-sanitizer-bundle requires PHP 7.1+ and Symfony 3.4+.

You can install the bundle using Symfony Flex:

```
composer require tgalopin/html-sanitizer-bundle
```

## Configuration

You can configure the bundle using the `html_sanitizer` configuration section:

```yaml
# config/packages/html_sanitizer.yaml

html_sanitizer:
    default_sanitizer: 'default'
    sanitizers:
        default:
            extensions: ['basic', 'image', 'list']
            tags:
                img:
                    allowed_hosts: ['127.0.0.1', 'mywebsite.com', 'youtube.com']
                    force_https: true
        admin_content:
            extensions: ['basic', 'image', 'list']
```

As you see, you can have multiple sanitizers available at the same time in your application.
Have a look at the [library documentation](https://github.com/tgalopin/html-sanitizer) to learn all the available
configuration options for the sanitizers themselves.

## Usage in services

This bundle provides the configured sanitizer for autowiring using the interface 
`HtmlSanitizer\SanitizerInterface`. This autowiring will target the default sanitizer defined
in the bundle configuration.
 
This means that if you are using autowiring, you can simply typehint `SanitizerInterface` in any
of your services to get the default sanitizer:

```php
use HtmlSanitizer\SanitizerInterface;

class MyService
{
    private $sanitizer;
    
    public function __construct(SanitizerInterface $sanitizer)
    {
        $this->sanitizer = $sanitizer;
    }
    
    // ...
}
```

The same goes for controllers:

```php
use HtmlSanitizer\SanitizerInterface;

class MyController
{
    public function index(SanitizerInterface $sanitizer)
    {
        // ...
    }
}
```

If you are not using autowiring, you can inject the `html_sanitizer` service into your services
manually to get the default sanitizer.

If you need to access other sanitizers than the default one in your services, you can either:

1. inject a specific sanitizer by injecting it with your services configuration as
  `html_sanitizer.<santizer-name>` (for instance, `html_sanitizer.admin_content`) ;

2. use the sanitizers registry by injecting it with your services configuration as 
   `html_sanitizer.registry`. It is a service locator mapping all the sanitizers available:
  
```php
use Psr\Container\ContainerInterface;

class MyService
{
    public function __construct(ContainerInterface $sanitizers)
    {
        // $sanitizers->get('admin_content') ...
    }
}
```

## Usage in forms

> This applies only if you have installed the Symfony Form component. 

The main usage of the html-sanitizer is in combination with forms. This bundle provides a TextType extension
which allows you to automatically sanitize HTML of any text field or any field based on the TextType
(TextareaType, SearchType, etc.). 

To use it in any of your forms, you can use the `sanitize_html` option:

```php
class MyFormType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('content', TextareaType::class, ['sanitize_html' => true])
        ;
    }
}
```

To use a different sanitizer than the default one, use the `sanitizer` option:

```php
class MyFormType extends AbstractType
{
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('content', TextareaType::class, ['sanitize_html' => true, 'sanitizer' => 'admin_content'])
        ;
    }
}
```

## Usage in Twig

> This applies only if you have installed the Twig bundle.

A `sanitize_html` Twig filter is provided through an extension, letting you filter HTML inside your views.

```twig
<div>
    {{ html|sanitize_html }}
</div>
```

To use a different sanitizer than the default one, add an argument to the filter:

```php
<div>
    {{ html|sanitize_html('admin_content') }}
</div>
```

## Registering an extension

If you use autoconfiguration, classes implementing the `HtmlSanitizer\Extension\ExtensionInterface` interface
will be automatically registered and you can use them in your sanitizer configuration:

```yaml
html_sanitizer:
    default_sanitizer: 'default'
    sanitizers:
        default:
            extensions: ['basic', 'my-extension']
```

If you don't use autoconfiguration, you need to register your extension as a service tagged `html_sanitizer.extension`:

```yaml
services:
    app.sanitizer.my_extension:
        class: 'App\Sanitizer\MyExtension'
        tags: [{ name: 'html_sanitizer.extension' }]
```

## Security Issues

If you discover a security vulnerability within the sanitizer bundle or library, please follow
[our disclosure procedure](https://github.com/tgalopin/html-sanitizer/blob/master/docs/A-security-disclosure-procedure.md).

## Backward Compatibility promise

This library follows the same Backward Compatibility promise as the Symfony framework:
[https://symfony.com/doc/current/contributing/code/bc.html](https://symfony.com/doc/current/contributing/code/bc.html)

> *Note*: many classes in this library are either marked `@final` or `@internal`.
> `@internal` classes are excluded from any Backward Compatiblity promise (you should not use them in your code)
> whereas `@final` classes can be used but should not be extended (use composition instead).
