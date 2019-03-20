#!/bin/bash
set -euo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )/.."
source .envrc

if [ ! -f .bin/ginkgo ]; then
  go install github.com/onsi/ginkgo/ginkgo
fi

export BUNDLE_GEMFILE=cf.Gemfile
bundle install
