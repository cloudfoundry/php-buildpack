#!/usr/bin/env bash
set -euo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )/.."
source .envrc
./scripts/install_tools.sh

cd src/*/integration/..
export CF_STACK=${CF_STACK:-cflinuxfs2}
ginkgo -r -skipPackage=brats,integration
