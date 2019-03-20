#!/bin/bash
set -euo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )/.."
source .envrc

go install github.com/onsi/ginkgo/ginkgo

export BUNDLE_GEMFILE=cf.Gemfile
bundle install
