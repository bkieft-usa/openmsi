#!/bin/bash

set -euf -o pipefail

NAMESPACE='openmsi'
SPIN_MODULE="spin/2.0"
RANCHER_MAJOR_VERSION_REQUIRED=2

# default options to pass to kubectl
FLAGS="--namespace=${NAMESPACE}"

# location of backup directories on global file system (cori)
ROOT_BACKUP_DIR="/global/cfs/cdirs/openmsi/omsi_db/backups/"
BACKUP_PREFIX="openmsi_sqlite_"

# initialize variables to avoid errors
OMSI_IMAGE=""
BACKUP_IMAGE=""
DEV=0
#export NON_ROOT_UID='104741' #bkieft uid at nersc
#export NON_ROOT_UID='55710' #bpb uid at nersc
export NON_ROOT_UID='97932'  # msdata user on NERSC
#export NON_ROOT_GID='60734'  # metatlas group on NERSC
export NON_ROOT_GID='55809'  # openmsi group on NERSC

# mount points of the persistant volumes
BACKUP_MNT=/backups
DB_MNT=/sqlite

TIMESTAMP=

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -b|--backup) export BACKUP_IMAGE="$2"; shift ;;
    -d|--dev) DEV=1 ;;
    -w|--webserver) export OMSI_IMAGE="$2"; shift ;;
    -t|--timestamp) TIMESTAMP="$2"; shift ;;
    -h|--help)
        echo -e "$0 [options]"
        echo ""
        echo "   -h, --help          show this command refernce"
	echo "   -b, --backup        source of backup docker image (required)"
	echo "   -d, --dev           deploy development instance instead of production"
	echo "   -w, --webserver     source of openmsi webserver docker image (required)"
	echo "   -t, --timestamp     timestamp of the backup to use (defaults to most recent)"
        exit 0
        ;;
    *)echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

function k8s_version() {
  rancher kubectl version \
  | grep '^Server Version:' \
  | tr -d ' v'  \
  | cut -d: -f2
}

function required_flag_or_error() {
  if [[ -z  "$1" ]]; then
    >&2 echo "ERROR: ${2}"
    exit 1
  fi
}

function file_exists_readable_not_empty_or_error () {
  if [[ ! -e "$1" ]]; then
    >&2 echo "ERROR: file ${1} does not exist."
    exit 2 
  fi
  if [[ ! -r "$1" ]]; then
    >&2 echo "ERROR: file ${1} is not readable."
    exit 2 
  fi
  if [[ ! -s "$1" ]]; then
    >&2 echo "ERROR: file ${1} is empty."
    exit 2 
  fi
  return 0
}

function file_safe_secret_or_error() {
  if [ $(stat -c %a "$1") != 600 ] && [ $(stat -c %a "$1") != 660 ]; then
    >&2 echo "ERROR: ${1} must have file permissions 600 or 660."
    exit 3 
  fi
  return 0
}

# default to the most recent directory with a timestamp for a name
if [[ $TIMESTAMP == '' ]]; then
  if [[ $DEV -eq 0 ]]; then
    BACKUP_PREFIX="openmsi_sqlite_"
  else
    BACKUP_PREFIX="openmsi-dev_sqlite_"
  fi
  TIMESTAMP=$(basename $(dirname $(find /global/cfs/cdirs/openmsi/omsi_db/backups -name "${BACKUP_PREFIX}*.gz" | \
	                           sort -r | head -1)))
fi

required_flag_or_error "$OMSI_IMAGE" "You are required to supply a source for the openmsi docker image via -w or --webserver."
required_flag_or_error "$BACKUP_IMAGE" "You are required to supply a source for the backup docker image via -b or --backup."
required_flag_or_error "$TIMESTAMP" "You are required to supply a backup timestamp via -t or --timestamp."

# relative to the global filesystem:
DB_BACKUP="${ROOT_BACKUP_DIR}/${TIMESTAMP}/${BACKUP_PREFIX}${TIMESTAMP}.gz"
echo "Using backup: ${DB_BACKUP}"

# directory containing this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Get dependency mo
MO_EXE="${SCRIPT_DIR}/lib/mo"
if [[ ! -x "${MO_EXE}" ]]; then
  mkdir -p "$(dirname "$MO_EXE")"
  curl -sSL https://git.io/get-mo -o "${MO_EXE}"
  chmod +x "${MO_EXE}"
fi

# Get dependency kubeconform
KUBEVAL_EXE="${SCRIPT_DIR}/lib/kubeconform"
if [[ ! -x "${KUBEVAL_EXE}" ]]; then
  mkdir -p "$(dirname "$KUBEVAL_EXE")"
  pushd "$(dirname "$KUBEVAL_EXE")"
  curl -sL https://github.com/yannh/kubeconform/releases/latest/download/kubeconform-linux-amd64.tar.gz \
  | tar xvz "$(basename "$KUBEVAL_EXE")"
  popd
fi

if [[ $DEV -eq 1 ]]; then
  PROJECT="c-fwj56:p-lswtz" # development:m2650
  export LB_FQDN="lb.openmsi.development.svc.spin.nersc.org"
  export OPENMSI_FQDN="openmsi-dev.nersc.gov"
  export PREFIX="openmsi-dev_sqlite_"
  export API_ROOT="https://openmsi-dev.nersc.gov/"
  CERT_FILE="${SCRIPT_DIR}/.tls.openmsi-dev.nersc.gov.cert"
  KEY_FILE="${SCRIPT_DIR}/.tls.openmsi-dev.nersc.gov.key"
else
  PROJECT="c-tmq7p:p-gqfz8" # production cluster for m2650. Run 'rancher context switch' to get other values.
  export LB_FQDN="lb.openmsi.production.svc.spin.nersc.org"
  export OPENMSI_FQDN="openmsi.nersc.gov"
  export PREFIX="openmsi_sqlite_"
  export API_ROOT="https://openmsi.nersc.gov/"
  CERT_FILE="${SCRIPT_DIR}/.tls.openmsi.nersc.gov.cert"
  KEY_FILE="${SCRIPT_DIR}/.tls.openmsi.nersc.gov.key"
fi

# backup file locations within the backup_restore container:
DB_BACKUP_INTERNAL="${BACKUP_MNT}/${TIMESTAMP}/$(basename $DB_BACKUP)"
DB_BACKUP_TEMP="$(dirname $DB_BACKUP_INTERNAL)/$(basename $DB_BACKUP)"

file_exists_readable_not_empty_or_error "$DB_BACKUP"
file_exists_readable_not_empty_or_error "$CERT_FILE"
file_exists_readable_not_empty_or_error "$KEY_FILE"

file_safe_secret_or_error "${KEY_FILE}"

DEPLOY_TMP="${SCRIPT_DIR}/deploy_tmp"
mkdir -p "$DEPLOY_TMP"
rm -rf "$DEPLOY_TMP/*"

#if declare -F module; then
#  module unload spin/1.0 &> /dev/null || true
#  module load "${SPIN_MODULE}"
#fi

if ! which rancher; then
  >&2 echo "ERROR: Required program 'rancher' not found."
  exit 6
fi

RANCHER_VERSION=$(rancher --version | sed -e 's/rancher version v\([0-9.]\+\)/\1/')
RANCHER_MAJOR_VERSION="${RANCHER_VERSION%%.*}"

if [[ "${RANCHER_MAJOR_VERSION}" -ne "${RANCHER_MAJOR_VERSION_REQUIRED}" ]]; then
  >&2 echo "ERROR: rancher v${RANCHER_MAJOR_VERSION_REQUIRED}.x required, version v${RANCHER_VERSION} found."
  exit 7
fi

if ! rancher project; then
  >&2 echo "ERROR: No rancher authentication token is present."
  exit 8 
fi

rancher context switch "${PROJECT}"

if ! rancher inspect --type namespace "${NAMESPACE}"; then
  rancher namespace create "${NAMESPACE}"
fi

for TEMPLATE in $(find "${SCRIPT_DIR}/spin2/" -name '*.yaml.template'); do
  REPLACED_FILE="${DEPLOY_TMP}/$(basename ${TEMPLATE%.*})"
  # does replacement of **exported** environment variables enclosed in double braces
  # such as {{API_ROOT}}
  "${MO_EXE}" -u "${TEMPLATE}" > "${REPLACED_FILE}"
  # lint kubernetes configruation file
  "${KUBEVAL_EXE}" -kubernetes-version "$(k8s_version)" "${REPLACED_FILE}"
done

# clean up any existing resources to make this script re-runable 
rancher kubectl delete deployments,statefulsets,cronjobs,services,pods,ingresses --all $FLAGS
rancher kubectl delete secret openmsi-cert $FLAGS

# start building up the new instance
rancher kubectl create secret tls openmsi-cert $FLAGS \
	"--cert=${CERT_FILE}" \
	"--key=${KEY_FILE}"

## Create persistant volumes - this isn't working from the CLI
# rancher kubectl apply $FLAGS -f "${DEPLOY_TMP}/sqlite.yaml"

# Restore sqlite database
# The container that copies the archive from global filesystem to the
# persistant volume cannot be running as root and therefore cannot
# correctly set the ownership of the unarchived files. Therefore
# a second pod (restore-root) does not mount the global filesystem
# and can set the correct ownership.

## Create restore pods
rancher kubectl apply $FLAGS -f "${DEPLOY_TMP}/restore.yaml"
rancher kubectl apply $FLAGS -f "${DEPLOY_TMP}/restore-root.yaml"

## Restore openmsi database
rancher kubectl wait $FLAGS deployment.apps/restore --for=condition=available --timeout=60s
rancher kubectl exec deployment.apps/restore $FLAGS -- /bin/bash -c "gunzip -c ${DB_BACKUP_INTERNAL} > ${DB_MNT}/openmsi.sqlite"
rancher kubectl scale $FLAGS --replicas=0 deployment.app/restore

rancher kubectl wait $FLAGS deployment.apps/restore-root --for=condition=available --timeout=60s
rancher kubectl exec deployment.apps/restore-root $FLAGS -- chown "${NON_ROOT_UID}:${NON_ROOT_GID}" "${DB_MNT}/openmsi.sqlite"
rancher kubectl scale $FLAGS --replicas=0 deployment.app/restore-root

## Create openmsi pod
rancher kubectl apply $FLAGS -f "${DEPLOY_TMP}/webserver.yaml"

## Create load balancer
rancher kubectl apply $FLAGS -f "${DEPLOY_TMP}/lb.yaml"

## Create cron job to backup sqlite DB to /global filesystem
rancher kubectl apply $FLAGS -f "${DEPLOY_TMP}/backup.yaml"

rm -rf "${DEPLOY_TMP}"
