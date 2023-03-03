#!/usr/bin/env bash

set -e
set -u
set -o pipefail

ROOTDIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly ROOTDIR

# shellcheck source=SCRIPTDIR/.util/print.sh
source "${ROOTDIR}/scripts/.util/print.sh"

# shellcheck source=SCRIPTDIR/.util/tools.sh
source "${ROOTDIR}/scripts/.util/tools.sh"

function main() {
  local src stack token

  if [[ -z "${COMPOSER_GITHUB_OAUTH_TOKEN:-}" ]]; then
    echo "Missing required environment variable: COMPOSER_GITHUB_OAUTH_TOKEN"
    exit 1
  else
    token="${COMPOSER_GITHUB_OAUTH_TOKEN}"
  fi

  src="$(find "${ROOTDIR}/src" -mindepth 1 -maxdepth 1 -type d )"
  stack="${CF_STACK:-$(jq -r -S .stack "${ROOTDIR}/config.json")}"

  util::tools::cf::install --directory "${ROOTDIR}/.bin"

  # Run uncached tests
  specs::run "false" "${stack}" "${token}"

  # Run cached tests
  specs::run "true" "${stack}" "${token}"
}

function specs::run() {
  local cached stack token
  cached="${1}"
  stack="${2}"
  token="${3}"

  local nodes cached_flag stack_flag
  cached_flag="--cached=${cached}"
  stack_flag="--stack=${stack}"
  nodes=1

  local buildpack_file
  buildpack::package "${cached}" "${stack}"
  version="$(cat "${ROOTDIR}/VERSION")"
  if [[ "${cached}" == "true" ]]; then
    buildpack_file="${ROOTDIR}/php_buildpack-cached-${stack}-v${version}.zip"
  else
    buildpack_file="${ROOTDIR}/php_buildpack-${stack}-v${version}.zip"
  fi

  util::print::title "Running integration tests (cached=${cached}, stack=${stack})"

  CF_STACK="${stack}" \
  COMPOSER_GITHUB_OAUTH_TOKEN="${token}" \
  BUILDPACK_FILE="${BUILDPACK_FILE:-"${buildpack_file}"}" \
  GOMAXPROCS="${GOMAXPROCS:-"${nodes}"}" \
    go test \
      -count=1 \
      -timeout=0 \
      -mod vendor \
      -v \
        "${src}/integration" \
         "${cached_flag}" \
         "${stack_flag}"
}

function buildpack::package() {
  local version cached
  cached="${1}"
  stack="${2}"

  local cached_flag
  cached_flag=""
  if [[ "${cached}" == "true" ]]; then
    cached_flag="--cached"
  else
    cached_flag="--uncached"
  fi

  bash "${ROOTDIR}/scripts/package.sh" \
    --stack "${stack}" \
    "${cached_flag}" &> /dev/null
}

main "${@:-}"
