#!/usr/bin/env bash
set -euo pipefail

ROOTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOTDIR

source .envrc

# shellcheck source=SCRIPTDIR/.util/tools.sh
source "${ROOTDIR}/scripts/.util/tools.sh"

util::tools::ginkgo::install --directory "${ROOTDIR}/.bin"

cd src/*/integration/..
export CF_STACK=${CF_STACK:-cflinuxfs3}
ginkgo -r -skipPackage=brats,integration
