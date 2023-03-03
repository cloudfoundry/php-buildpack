#!/usr/bin/env bash

set -e
set -u
set -o pipefail

ROOTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOTDIR

## shellcheck source=SCRIPTDIR/.util/tools.sh
#source "${ROOTDIR}/scripts/.util/tools.sh"
#
# shellcheck source=SCRIPTDIR/.util/print.sh
source "${ROOTDIR}/scripts/.util/print.sh"

function main() {
  local stack cached
  stack="any"
  cached="false"

  while [[ "${#}" != 0 ]]; do
    case "${1}" in
      --stack)
        stack="${2}"
        shift 2
        ;;

      --cached)
        cached="true"
        shift 1
        ;;

      --uncached)
        cached="false"
        shift 1
        ;;

      --help|-h)
        shift 1
        usage
        exit 0
        ;;

      "")
        # skip if the argument is empty
        shift 1
        ;;

      *)
        util::print::error "unknown argument \"${1}\""
    esac
  done

  package::buildpack "${cached}" "${stack}"
}


function usage() {
  cat <<-USAGE
package.sh [OPTIONS]
Packages the buildpack into a .zip file.
OPTIONS
  --help               -h            prints the command usage
  --cached            packages the buildpack as a cached buildpack
  --uncached          packages the buildpack as an uncached buildpack (default)
  --stack             the stack to package the buildpack for (default: any)
USAGE
}

function package::buildpack() {
  local cached stack
  cached="${1}"
  stack="${2}"


  local stack_flag
  stack_flag="--any-stack"
  if [[ "${stack}" != "any" ]]; then
    stack_flag="--stack=${stack}"
  fi

  local cached_flag
  cached_flag="--uncached"
  if [[ "${cached}" == "true" ]]; then
    cached_flag="--cached"
  fi

  pushd "${ROOTDIR}" &> /dev/null
    cat <<EOF > Dockerfile
FROM ruby:3.0
RUN apt-get update && apt-get install -y zip
ADD cf.Gemfile .
ADD cf.Gemfile.lock .
ENV BUNDLE_GEMFILE=cf.Gemfile
RUN bundle install
ENTRYPOINT ["bundle", "exec", "buildpack-packager"]
EOF
    docker build -t buildpack-packager . &> /dev/null

    docker run --rm -v "${ROOTDIR}":/buildpack -w /buildpack buildpack-packager "${stack_flag}" ${cached_flag} &> /dev/null
    util::print::success "Buildpack packaged successfully"

  popd &> /dev/null

  rm -f "${ROOTDIR}/Dockerfile"
}

main "${@:-}"
