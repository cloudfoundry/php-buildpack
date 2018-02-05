# ZfcBase

Version 0.0.1 Created by Evan Coury and the ZF-Commons team

[![Build Status](https://secure.travis-ci.org/ZF-Commons/ZfcBase.png?branch=master)](http://travis-ci.org/ZF-Commons/ZfcBase)

## Introduction

ZfcBase provides a suite of common classes used across several ZF2 modules.
You probably don't need to install this module unless either A) you are
installing a module that depends on ZfcBase, or B) you are building a module
that depends on ZfcBase.

## Requirements

* Zend Framework 2

## Installation

Simply clone this project into your `./vendor/` directory and enable it in your
`./config/application.config.php` file.

Provided Classes
----------------

* `ZfcBase\Mapper\AbstractDbMapper` - An abstract mapper for Zend\Db that makes
  using hydrators and custom entities very simple.
* `ZfcBase\Form\ProvidesEventsForm` - Extends Zend\Form and provides the
  functionality of `ZfcBase\EventManager\EventProvider` (basically it's a
  crutch since we can't use traits yet).
* `ZfcBase\EventManager\EventProvider` - Abstract class that gives extending
  classes an event manager and related methods.
