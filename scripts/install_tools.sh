#!/bin/bash
set -euo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )/.."
source .envrc

if [ ! -f .bin/ginkgo ]; then
  pushd /tmp > /dev/null || return
    GOBIN="${OLDPWD}/.bin" \
      go get \
        -u \
        github.com/onsi/ginkgo/ginkgo@latest
  popd > /dev/null || return
fi

export BUNDLE_GEMFILE=cf.Gemfile
bundle install
