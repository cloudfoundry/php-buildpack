#!/usr/bin/env bash
set -euo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )/.."
source .envrc

cd src/*/integration/..
export CF_STACK=${CF_STACK:-cflinuxfs3}
ginkgo -r -skipPackage=brats,integration
