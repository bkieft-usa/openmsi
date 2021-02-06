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
        echo "   -d, --dev           backup development instance instead of production"
        exit 0
        ;;
    *)echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done

# mount points of the persistant volumes
BACKUP_MNT=/backups
DATA_MNT=/data

TIMESTAMP=$(date +%Y%m%d%H%M)
DEST_DIR="${BACKUP_MNT}/${TIMESTAMP}"

if [[ $DEV -eq 1 ]]; then
  RANCHER_ENVIRONMENT=dev-cattle
  DATA_VOL=api.openmsi-dev-nersc
  SQLITE_GZ="${DEST_DIR}/openmsi-dev_sqlite_${TIMESTAMP}.gz"
  # pod names in rancher
  APP="openmsi-dev-nersc/web"
  SQLITE_BACKUP="openmsi-dev-nersc/backup"
else
  RANCHER_ENVIRONMENT=prod-cattle
  DATA_VOL=api.openmsi-nersc
  SQLITE_GZ="${DEST_DIR}/openmsi_sqlite_${TIMESTAMP}.gz"
  # pod names in rancher
  APP="openmsi-nersc/web"
  SQLITE_BACKUP="openmsi-nersc/backup"
fi

SQLITE_FILE=${DATA_MNT}/db/openmsi.sqlite

module load spin

rancher stop "${APP}"

echo 'starting ubuntu container'
ID=$(rancher run \
        --name "${SQLITE_BACKUP}" \
        --cap-drop ALL \
        --volume "${DATA_VOL}:${DATA_MNT}" \
        "ubuntu:20.04" \
        tail -f /dev/null)

echo 'waiting for ubuntu container'
rancher wait "${ID}"

echo 'changeing file permissions on sqlite db file'
rancher exec -it "${SQLITE_BACKUP}" \
       /bin/bash -c "chmod +r ${SQLITE_FILE}"

echo 'stoping ubuntu container'
rancher stop "${SQLITE_BACKUP}"

echo 'removing ubuntu container'
rancher rm "${SQLITE_BACKUP}"

echo 'starting 2nd ubuntu container'
ID=$(rancher run \
        --name "${SQLITE_BACKUP}" \
        --user 94014:94014 \
        --cap-drop ALL \
        --volume "${DATA_VOL}:${DATA_MNT}" \
        --volume "/global/cfs/cdirs/openmsi/omsi_db/backups:${BACKUP_MNT}" \
        "ubuntu:20.04" \
        tail -f /dev/null)

echo 'waiting for ubuntu container'
rancher wait "${ID}"

echo 'starting copy sqlite database to global file system'
rancher exec -it "${SQLITE_BACKUP}" \
       /bin/bash -c "mkdir -p ${DEST_DIR} && gzip --stdout ${SQLITE_FILE} > ${SQLITE_GZ} && chmod 660 ${SQLITE_GZ}"

echo 'stoping ubuntu container'
rancher stop "${SQLITE_BACKUP}"

echo 'removing ubuntu container'
rancher rm "${SQLITE_BACKUP}"


