#!/bin/bash

set -euf -o pipefail

DEV=0
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -d|--dev) DEV=1 ;;
    -h|--help)
        echo -e "$0 [options]"
        echo ""
        echo "   -h, --help          show this command refernce"
        echo "   -d, --dev           shutdown development instance instead of production"
        exit 0
        ;;
    *)echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

if [[ $DEV -eq 0 ]]; then
  RANCHER_ENVIRONMENT=prod-cattle
  POD_PREFIX="openmsi-nersc"
  POD_SUFFIXES="web-redirect web app kv"
else
  RANCHER_ENVIRONMENT=dev-cattle
  POD_PREFIX="openmsi-dev-nersc"
  POD_SUFFIXES="setup admin web app kv"
fi


PODS=""
for SUF in $POD_SUFFIXES; do
  PODS="${PODS} ${POD_PREFIX}/${SUF}"
done

echo $PODS

module load spin

for P in $PODS; do
  rancher stop "${P}" || true
done

