#!/bin/sh

rm -rf $HOME/.composer/cache/*
rm -Rf ./vendor/

composer config -g github-oauth.github.com "$COMPOSER_GITHUB_OAUTH_TOKEN"

composer install --no-interaction
