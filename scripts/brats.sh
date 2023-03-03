#!/usr/bin/env bash
set -euo pipefail

ROOTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOTDIR

# shellcheck source=SCRIPTDIR/.util/print.sh
source "${ROOTDIR}/scripts/.util/print.sh"

# shellcheck source=SCRIPTDIR/.util/tools.sh
source "${ROOTDIR}/scripts/.util/tools.sh"

function main() {
  cd "$( dirname "${BASH_SOURCE[0]}" )/.."
  source .envrc

  # shellcheck source=SCRIPTDIR/.util/tools.sh
  source "${ROOTDIR}/scripts/.util/tools.sh"

  util::tools::ginkgo::install --directory "${ROOTDIR}/.bin"

  # set up buildpack-packager
  # apt-get install ruby
  gem install bundler
  export BUNDLE_GEMFILE=cf.Gemfile
  bundle install


  GINKGO_NODES=${GINKGO_NODES:-3}
  GINKGO_ATTEMPTS=${GINKGO_ATTEMPTS:-1}
  export CF_STACK=${CF_STACK:-cflinuxfs3}

  cd src/*/brats

  util::print::title "Run Buildpack Runtime Acceptance Tests"

  ginkgo -r --flakeAttempts="$GINKGO_ATTEMPTS" -nodes "$GINKGO_NODES"
}

main "${@:-}"
