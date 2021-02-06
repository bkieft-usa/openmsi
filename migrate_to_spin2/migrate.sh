#!/bin/bash

set -euf -o pipefail

# initialize variables to avoid errors
DEV=0
OMSI_IMAGE=""
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -d|--dev) DEV=1 ;;
    -i|--image) OMSI_IMAGE="$2"; shift ;;
    -h|--help)
        echo -e "$0 [options]"
        echo ""
        echo "   -h, --help          show this command refernce"
	echo "   -d, --dev           migrate development instance instead of production"
	echo "   -i, --image         source of openmsi docker image (required)"
        exit 0
        ;;
    *)echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

function required_flag_or_error() {
  if [[ -z  "$1" ]]; then
    >&2 echo "ERROR: ${2}"
    exit 1
  fi
}

required_flag_or_error "$OMSI_IMAGE" "You are required to supply a source for the openmsi docker image via -i or --image."

# directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [[ $DEV -eq 1 ]]; then
  API_ROOT='https://openmsi-dev.nersc.gov/'
  FLAGS="--dev"
else
  API_ROOT='https://openmsi.nersc.gov/'
  FLAGS=
fi

${SCRIPT_DIR}/backup-spin1.sh $FLAGS
${SCRIPT_DIR}/shutdown-spin1.sh $FLAGS
${SCRIPT_DIR}/../deploy.sh --image "$OMSI_IMAGE" --api "$API_ROOT" $FLAGS

