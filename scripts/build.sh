#!/usr/bin/env bash
set -exuo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )/.."
source .envrc

(cd src/*/vendor/github.com/GeertJohan/go.rice/rice && go install)
(cd src/php/supply && rice embed-go)

GOOS=linux go build -ldflags="-s -w" -o bin/varify php/varify
GOOS=linux go build -ldflags="-s -w" -o bin/procfiled php/procfiled
GOOS=linux go build -ldflags="-s -w" -o bin/supply php/supply/cli
GOOS=linux go build -ldflags="-s -w" -o bin/finalize php/finalize/cli
