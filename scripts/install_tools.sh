#!/bin/bash
set -euo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )/.."
source .envrc

(cd src/*/vendor/github.com/onsi/ginkgo/ginkgo/ && go install)
(cd src/*/vendor/github.com/cloudfoundry/libbuildpack/packager/buildpack-packager && go install)
# (cd src/*/vendor/github.com/GeertJohan/go.rice/rice && go install)
