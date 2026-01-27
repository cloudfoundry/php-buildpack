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

function usage() {
  cat <<-USAGE
integration.sh --github-token <token> [OPTIONS]
Runs the integration tests.
OPTIONS
  --help                  -h  prints the command usage
  --github-token <token>      GitHub token to use when making API requests
  --platform <cf|docker>      Switchblade platform to execute the tests against
  --keep-failed-containers    Preserve failed test containers for debugging (default: false)
USAGE
}

function main() {
  local src stack platform token cached parallel keep_failed
  src="$(find "${ROOTDIR}/src" -mindepth 1 -maxdepth 1 -type d )"
  stack="${CF_STACK:-$(jq -r -S .stack "${ROOTDIR}/config.json")}"
  platform="cf"
  keep_failed="false"

  while [[ "${#}" != 0 ]]; do
    case "${1}" in
      --platform)
        platform="${2}"
        shift 2
        ;;

      --github-token)
        token="${2}"
        shift 2
        ;;

      --cached)
        cached="${2}"
        shift 2
        ;;

      --parallel)
        parallel="${2}"
        shift 2
        ;;

      --keep-failed-containers)
        keep_failed="true"
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

  if [[ -z "${token:-}" ]]; then
    util::print::error "Missing required github token. This is used as COMPOSER_GITHUB_OAUTH_TOKEN for the build"
  fi
  util::print::info "The provided github token is also being used as COMPOSER_GITHUB_OAUTH_TOKEN for the build"

  if [[ "${platform}" == "docker" ]]; then
    if [[ "$(jq -r -S .integration.harness "${ROOTDIR}/config.json")" != "switchblade" ]]; then
      util::print::warn "NOTICE: This integration suite does not support Docker."
    fi
  fi

  declare -a matrix
  if [[ "${cached:-}" != "" && "${parallel:-}" != "" ]]; then
    matrix+=("{\"cached\":${cached},\"parallel\":${parallel}}")
  else
    IFS=$'\n' read -r -d '' -a matrix < <(
      jq -r -S -c .integration.matrix[] "${ROOTDIR}/config.json" \
        && printf "\0"
    )
  fi

  util::tools::buildpack-packager::install --directory "${ROOTDIR}/.bin"
  util::tools::cf::install --directory "${ROOTDIR}/.bin"

  for row in "${matrix[@]}"; do
    local cached parallel
    cached="$(jq -r -S .cached <<<"${row}")"
    parallel="$(jq -r -S .parallel <<<"${row}")"

    echo "Running integration suite (cached: ${cached}, parallel: ${parallel})"

    specs::run "${cached}" "${parallel}" "${stack}" "${platform}" "${token:-}" "${keep_failed}"
  done
}

function specs::run() {
  local cached parallel stack platform token keep_failed
  cached="${1}"
  parallel="${2}"
  stack="${3}"
  platform="${4}"
  token="${5}"
  keep_failed="${6}"

  local nodes cached_flag serial_flag platform_flag stack_flag token_flag keep_failed_flag
  cached_flag="--cached=${cached}"
  serial_flag="--serial=true"
  platform_flag="--platform=${platform}"
  stack_flag="--stack=${stack}"
  token_flag="--github-token=${token}"
  keep_failed_flag="--keep-failed-containers=${keep_failed}"
  nodes=1

  if [[ "${parallel}" == "true" ]]; then
    nodes=3
    serial_flag=""
  fi

  local buildpack_file version
  version="$(cat "${ROOTDIR}/VERSION")"
  buildpack_file="$(buildpack::package "${version}" "${cached}" "${stack}")"

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
         ${cached_flag} \
         ${platform_flag} \
         ${token_flag} \
         ${stack_flag} \
         ${serial_flag} \
         ${keep_failed_flag}
}

function buildpack::package() {
  local version cached
  version="${1}"
  cached="${2}"
  stack="${3}"

  local cached_flag
  cached_flag=""
  if [[ "${cached}" == "true" ]]; then
    cached_flag="--cached"
  fi

  bash "${ROOTDIR}/scripts/package.sh" \
    --stack "${stack}" \
    "${cached_flag}" > /dev/null

  # this is the default output location of the package.sh script
  echo "${ROOTDIR}/build/buildpack.zip"
}

main "${@:-}"
