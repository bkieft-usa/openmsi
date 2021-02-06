#!/bin/bash

# catch some common errors, terminate if a command returns non-zero exit code
set -euf -o pipefail

SPIN_USER="$USER"
PROJECT="openmsi"
REGISTRY="registry.spin.nersc.gov"
DOCKER="docker"
VERSION=`date "+%Y-%m-%d-%H-%M"`

# next line from https://stackoverflow.com/questions/59895/
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
IMAGE_NAME="openmsi"

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -d|--docker) DOCKER="$2"; shift ;;
    -r|--registry) REGISTRY="$2"; shift ;;
    -p|--project) PROJECT="$2"; shift ;;
    -u|--user) SPIN_USER="$2"; shift ;;
    -h|--help)
        echo -e "$0 [options]"
        echo ""
        echo "   -h, --help              show this command reference"
	echo "   -d, --docker            name of docker command (default ${DOCKER})"
        echo "   -p, --project string    project name within the registry (default ${PROJECT})"
        echo "   -r, --registry string   FQDN of container registry to push to"
        echo "                           use 'NONE' to not push (default ${REGISTRY})"
        echo "   -u, --user string       username for ${REGISTRY} (default ${USER})"
        exit 0
        ;;
    *)echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

SHORT_TAG="${IMAGE_NAME}:${VERSION}"
LONG_TAG="${REGISTRY}/${PROJECT}/${SHORT_TAG}"

DOCKERFILE_DIR="${SCRIPT_DIR}"

if [[ ! -r "${DOCKERFILE_DIR}/Dockerfile" ]]; then
  >&2 echo "ERROR: Could not find readable Dockerfile in ${DOCKERFILE_DIR}."
  exit 1
fi

${DOCKER} image build --tag "${SHORT_TAG}" "${DOCKERFILE_DIR}"

if [[ "$REGISTRY" != "NONE" ]]; then
  if [[ $(basename $(readlink -f $(which ${DOCKER}))) == 'podman' ]]; then
    PUSH_FLAGS="--format=docker"
  fi
  ${DOCKER} image tag "${SHORT_TAG}" "${LONG_TAG}"
  ${DOCKER} image push ${PUSH_FLAGS:-} "${LONG_TAG}" "docker://${LONG_TAG}"
  TAG="${LONG_TAG}"
else
  TAG="${SHORT_TAG}"
fi

